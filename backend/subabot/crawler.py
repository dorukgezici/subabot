import asyncio
import calendar
import hashlib
import logging
import re
from datetime import UTC, datetime
from html.parser import HTMLParser
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

import aiohttp
import feedparser
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from subabot.config import Settings
from subabot.models import Monitor, Signal, Workspace, now
from subabot.safety import PublicResolver, safe_url

logger = logging.getLogger(__name__)


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.hidden += 1
        elif tag in {"p", "br", "div", "li"}:
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.hidden = max(0, self.hidden - 1)
        else:
            self.parts.append(" ")

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def plain_text(value: str, limit=600) -> str:
    parser = TextExtractor()
    parser.feed(str(value)[:100_000])
    return " ".join("".join(parser.parts).split())[:limit]


def canonical_url(value: str) -> str:
    parsed = urlsplit(safe_url(value))
    query = [(k, v) for k, v in parse_qsl(parsed.query) if not k.lower().startswith("utm_") and k != "fbclid"]
    return urlunsplit((parsed.scheme, parsed.netloc.lower(), parsed.path, urlencode(query), ""))


def matching_keywords(text: str, monitor: Monitor) -> list[str]:
    text = text.casefold()

    def contains(keyword):
        # Word boundaries keep "AI" from matching "paid"; phrases and punctuation still work.
        return bool(re.search(r"(?<!\w)" + re.escape(keyword.casefold()) + r"(?!\w)", text))

    if any(contains(word) for word in monitor.exclude_keywords):
        return []
    matches = [word for word in monitor.keywords if contains(word)]
    return [] if monitor.match_mode == "all" and len(matches) != len(monitor.keywords) else matches


async def fetch_feed(url: str, settings: Settings) -> dict:
    connector = aiohttp.TCPConnector(resolver=PublicResolver(), use_dns_cache=False, limit=6)
    timeout = aiohttp.ClientTimeout(total=settings.feed_timeout_seconds, connect=5)
    async with aiohttp.ClientSession(
        connector=connector,
        timeout=timeout,
        trust_env=False,
        auto_decompress=False,
        headers={
            "User-Agent": "Subabot/1.0 (+https://github.com/dorukgezici/subabot)",
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml",
            "Accept-Encoding": "identity",
        },
    ) as client:
        async with asyncio.timeout(settings.feed_timeout_seconds):
            current = safe_url(url)
            for _ in range(4):
                async with client.get(current, allow_redirects=False) as response:
                    if response.status in {301, 302, 303, 307, 308}:
                        location = response.headers.get("Location")
                        if not location:
                            raise ValueError("Feed returned a redirect without a destination.")
                        current = safe_url(urljoin(current, location))
                        continue
                    if response.status != 200:
                        raise ValueError(f"Feed returned HTTP {response.status}.")
                    if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                        raise ValueError("Feed ignored the request for an uncompressed response.")
                    if response.content_length and response.content_length > settings.max_feed_bytes:
                        raise ValueError("Feed exceeds the size limit.")
                    data = bytearray()
                    async for chunk in response.content.iter_chunked(16_384):
                        data.extend(chunk)
                        if len(data) > settings.max_feed_bytes:
                            raise ValueError("Feed exceeds the size limit.")
                    if data[:2] == b"\x1f\x8b":
                        raise ValueError("Feed returned compressed data without the correct response headers.")
                    parsed = await asyncio.to_thread(feedparser.parse, bytes(data))
                    if not parsed.get("version"):
                        raise ValueError("This URL does not contain a valid RSS or Atom feed.")
                    return {
                        "source": plain_text(parsed.feed.get("title", urlsplit(current).hostname), 100),
                        "entries": parsed.entries[:100],
                        "url": current,
                    }
            raise ValueError("Feed has too many redirects.")


async def deliver_signal(webhook: str, signal: Signal, monitor_name: str) -> bool:
    # Plain text blocks prevent feed content from triggering Slack mentions or markup.
    payload = {
        "text": "A new Subabot signal is ready.",
        "blocks": [
            {"type": "section", "text": {"type": "plain_text", "text": signal.title[:2500]}},
            {"type": "section", "text": {"type": "plain_text", "text": (signal.summary or signal.source)[:2500]}},
            {
                "type": "context",
                "elements": [{"type": "plain_text", "text": f"{monitor_name} | {signal.source} | via Subabot"[:2000]}],
            },
            {
                "type": "actions",
                "elements": [
                    {"type": "button", "text": {"type": "plain_text", "text": "Read story"}, "url": signal.url}
                ],
            },
        ],
        "unfurl_links": False,
        "unfurl_media": False,
    }
    connector = aiohttp.TCPConnector(resolver=PublicResolver(), use_dns_cache=False)
    async with aiohttp.ClientSession(
        connector=connector, timeout=aiohttp.ClientTimeout(total=8), trust_env=False
    ) as client:
        async with client.post(webhook, json=payload, allow_redirects=False) as response:
            return response.status == 200 and (await response.content.read(100)).strip() == b"ok"


def entry_signal(entry, feed, monitor: Monitor, workspace: Workspace) -> Signal | None:
    title = plain_text(entry.get("title", "Untitled story"), 300)
    content = entry.get("summary", "")
    if not content and entry.get("content"):
        content = entry["content"][0].get("value", "")
    text = plain_text(content, 10_000)
    matches = matching_keywords(f"{title} {text}", monitor)
    if not matches or not entry.get("link"):
        return None
    try:
        url = canonical_url(urljoin(feed["url"], entry["link"]))
    except ValueError:
        return None
    published_at = now()
    timestamp = entry.get("published_parsed") or entry.get("updated_parsed")
    if timestamp:
        try:
            published_at = datetime.fromtimestamp(calendar.timegm(timestamp), UTC)
            if published_at > now():
                published_at = now()
        except OverflowError, ValueError, TypeError:
            pass
    return Signal(
        workspace_id=workspace.id,
        monitor_id=monitor.id,
        title=title,
        url=url,
        fingerprint=hashlib.sha256(url.encode()).hexdigest(),
        summary=text[:600],
        source=feed["source"],
        published_at=published_at,
        matched_keywords=matches,
        delivery_pending=bool(workspace.webhook_url),
    )


async def scan_workspace(engine, workspace_id: str, settings: Settings) -> dict:
    result = {"checked": 0, "new_signals": 0, "errors": [], "slack_sent": 0}
    with Session(engine) as session:
        workspace = session.get(Workspace, workspace_id)
        if not workspace:
            return result
        monitors = list(
            session.exec(select(Monitor).where(Monitor.workspace_id == workspace_id, Monitor.enabled)).all()
        )
        urls = list(dict.fromkeys(url for monitor in monitors for url in monitor.feed_urls))
        semaphore = asyncio.Semaphore(6)

        async def fetch(url):
            async with semaphore:
                try:
                    return await fetch_feed(url, settings)
                except (ValueError, OSError, aiohttp.ClientError, TimeoutError) as exc:
                    # Exception strings from the HTTP client can contain sensitive query strings.
                    message = str(exc) if isinstance(exc, ValueError) else "Could not reach this feed. Try again later."
                    result["errors"].append({"feed_url": url, "message": message})
                    return None

        feeds = dict(zip(urls, await asyncio.gather(*(fetch(url) for url in urls)), strict=True))
        result["checked"] = len(urls)
        for monitor in monitors:
            # This session does not hold a write transaction while waiting for network I/O.
            session.refresh(monitor)
            if not monitor.enabled:
                continue
            for url in monitor.feed_urls:
                if not (feed := feeds.get(url)):
                    continue
                for entry in feed["entries"]:
                    signal = entry_signal(entry, feed, monitor, workspace)
                    if signal is None:
                        continue
                    exists = session.exec(
                        select(Signal.id).where(
                            Signal.monitor_id == monitor.id, Signal.fingerprint == signal.fingerprint
                        )
                    ).first()
                    if exists:
                        continue
                    try:
                        session.add(signal)
                        session.commit()
                        result["new_signals"] += 1
                    except IntegrityError:
                        session.rollback()
            monitor.last_checked_at = now()
            failures = sum(feeds.get(url) is None for url in monitor.feed_urls)
            monitor.last_error = (
                f"{failures} of {len(monitor.feed_urls)} feeds could not be checked." if failures else None
            )
            session.add(monitor)
        session.commit()
        if workspace.webhook_url:
            enabled_ids = [monitor.id for monitor in monitors if monitor.enabled]
            pending = session.exec(
                select(Signal)
                .where(Signal.workspace_id == workspace_id, Signal.delivery_pending, Signal.monitor_id.in_(enabled_ids))
                .order_by(Signal.created_at)
                .limit(20)
            ).all()
            monitor_names = {monitor.id: monitor.name for monitor in monitors}
            for index, signal in enumerate(pending):
                if index:
                    # Incoming webhooks allow roughly one message per second per channel.
                    await asyncio.sleep(1.05)
                try:
                    delivered = await deliver_signal(
                        workspace.webhook_url, signal, monitor_names.get(signal.monitor_id, "Your monitor")
                    )
                except aiohttp.ClientError, OSError, TimeoutError:
                    delivered = False
                if not delivered:
                    result["errors"].append(
                        {
                            "feed_url": "Slack",
                            "message": "Slack delivery failed. Saved signals will retry on the next scan.",
                        }
                    )
                    break
                signal.delivery_pending = False
                signal.delivered_at = now()
                session.add(signal)
                session.commit()
                result["slack_sent"] += 1
    return result
