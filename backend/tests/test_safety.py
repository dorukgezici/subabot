import socket
from unittest.mock import AsyncMock

import pytest

from subabot.config import Settings
from subabot.crawler import fetch_feed
from subabot.safety import PublicResolver, public_ip, safe_url


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/",
        "http://localhost/",
        "http://0.0.0.0/",
        "http://10.1.2.3/",
        "http://172.16.1.1/",
        "http://192.168.1.1/",
        "http://169.254.169.254/",
        "http://[::1]/",
        "http://[::ffff:127.0.0.1]/",
        "http://[fc00::1]/",
        "http://user:password@example.com/",
        "http://example.com:8000/",
        "ftp://example.com/",
        "http://service.internal/",
        "http://thing.local/",
        "http://example.com\\@127.0.0.1",
        "http://example.com/\r\nx:yes",
    ],
)
def test_private_and_unsafe_urls_rejected(url):
    with pytest.raises(ValueError):
        safe_url(url)


def test_valid_public_addresses():
    assert safe_url("https://example.com/feed#section") == "https://example.com/feed"
    assert public_ip("1.1.1.1")
    assert not public_ip("224.0.0.1")


async def test_connection_resolver_rejects_any_private_result():
    resolver = PublicResolver()
    resolver.resolver.resolve = AsyncMock(return_value=[{"host": "1.1.1.1"}, {"host": "127.0.0.1"}])
    with pytest.raises(OSError, match="private"):
        await resolver.resolve("example.com", 443, socket.AF_UNSPEC)
    await resolver.close()


class FakeContent:
    def __init__(self, body):
        self.body = body

    async def iter_chunked(self, size):
        for index in range(0, len(self.body), size):
            yield self.body[index : index + size]


class FakeResponse:
    def __init__(self, status=200, body=b"", headers=None, length=None):
        self.status = status
        self.headers = headers or {}
        self.content = FakeContent(body)
        self.content_length = length

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False


class FakeSession:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.urls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    def get(self, url, **kwargs):
        assert kwargs["allow_redirects"] is False
        self.urls.append(url)
        return next(self.responses)


def fake_http(monkeypatch, responses):
    client = FakeSession(responses)
    monkeypatch.setattr("subabot.crawler.aiohttp.ClientSession", lambda **kwargs: client)
    monkeypatch.setattr("subabot.crawler.aiohttp.TCPConnector", lambda **kwargs: None)
    return client


async def test_redirect_to_private_address_is_never_requested(monkeypatch):
    client = fake_http(monkeypatch, [FakeResponse(302, headers={"Location": "http://169.254.169.254/latest"})])
    with pytest.raises(ValueError, match="Private"):
        await fetch_feed("https://example.com/feed", Settings())
    assert client.urls == ["https://example.com/feed"]


async def test_real_feed_parser_and_relative_redirect(monkeypatch):
    rss = (
        b'<?xml version="1.0"?><rss version="2.0"><channel><title>Example</title>'
        b"<link>https://example.com</link><description>News</description><item><title>AI launch</title>"
        b"<link>https://example.com/story</link><description>Hello</description></item></channel></rss>"
    )
    client = fake_http(monkeypatch, [FakeResponse(301, headers={"Location": "/rss"}), FakeResponse(body=rss)])
    feed = await fetch_feed("https://example.com/feed", Settings())
    assert feed["source"] == "Example" and feed["entries"][0]["title"] == "AI launch"
    assert client.urls == ["https://example.com/feed", "https://example.com/rss"]


async def test_non_feed_and_large_body_rejected(monkeypatch):
    fake_http(monkeypatch, [FakeResponse(body=b"<html><body>Not a feed</body></html>")])
    with pytest.raises(ValueError, match="valid RSS"):
        await fetch_feed("https://example.com/feed", Settings())
    fake_http(monkeypatch, [FakeResponse(body=b"x" * 1001)])
    with pytest.raises(ValueError, match="size limit"):
        await fetch_feed("https://example.com/feed", Settings(max_feed_bytes=1000))


async def test_compressed_responses_cannot_expand_past_size_limit(monkeypatch):
    fake_http(monkeypatch, [FakeResponse(body=b"ignored", headers={"Content-Encoding": "gzip"})])
    with pytest.raises(ValueError, match="uncompressed"):
        await fetch_feed("https://example.com/feed", Settings())
    fake_http(monkeypatch, [FakeResponse(body=b"\x1f\x8bmalicious-compression")])
    with pytest.raises(ValueError, match="compressed data"):
        await fetch_feed("https://example.com/feed", Settings())
