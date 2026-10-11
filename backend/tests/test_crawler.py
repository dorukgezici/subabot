from unittest.mock import AsyncMock

import pytest
from sqlmodel import Session, select

from subabot.crawler import matching_keywords, plain_text
from subabot.models import Monitor, Signal


def test_scan_deduplicates_and_signal_actions(client, headers, monitor_data, feed, monkeypatch):
    fetch = AsyncMock(return_value=feed)
    monkeypatch.setattr("subabot.crawler.fetch_feed", fetch)
    monitor = client.post("/api/monitors", headers=headers, json=monitor_data).json()
    first = client.post("/api/scan", headers=headers)
    assert first.status_code == 200, first.text
    assert first.json() == {"checked": 1, "new_signals": 1, "errors": [], "slack_sent": 0}
    assert client.post("/api/scan", headers=headers).json()["new_signals"] == 0
    signals = client.get("/api/signals", headers=headers).json()
    assert len(signals) == 1
    signal = signals[0]
    assert signal["summary"] == "Useful AI news."
    assert signal["url"] == "https://example.com/ai-story"
    assert signal["matched_keywords"] == ["ai", "openai"]
    assert client.get("/api/workspace", headers=headers).json()["stats"]["unread"] == 1
    changed = client.patch(
        f"/api/signals/{signal['id']}", headers=headers, json={"is_read": True, "is_bookmarked": True}
    ).json()
    assert changed["is_read"] is True and changed["is_bookmarked"] is True
    assert len(client.get("/api/signals", headers=headers, params={"bookmarked": True, "search": "model"}).json()) == 1
    assert client.get("/api/signals", headers=headers, params={"search": "%"}).json() == []
    other = client.post("/api/workspaces").json()["token"]
    assert (
        client.patch(
            f"/api/signals/{signal['id']}", headers={"Authorization": f"Bearer {other}"}, json={"is_read": False}
        ).status_code
        == 404
    )
    checked = client.get("/api/monitors", headers=headers).json()[0]["last_checked_at"]
    assert checked and checked.endswith("Z")
    client.delete(f"/api/monitors/{monitor['id']}", headers=headers)
    assert client.get("/api/signals", headers=headers).json() == []


def test_feed_failure_is_partial_and_paused_monitors_are_skipped(client, headers, monitor_data, feed, monkeypatch):
    async def fetch(url, settings):
        if "broken" in url:
            raise ValueError("This URL does not contain a valid RSS or Atom feed.")
        return feed

    monkeypatch.setattr("subabot.crawler.fetch_feed", fetch)
    monitor = client.post(
        "/api/monitors",
        headers=headers,
        json={**monitor_data, "feed_urls": [*monitor_data["feed_urls"], "https://broken.example.com/feed"]},
    ).json()
    response = client.post("/api/scan", headers=headers).json()
    assert response["checked"] == 2 and response["new_signals"] == 1 and len(response["errors"]) == 1
    client.patch(f"/api/monitors/{monitor['id']}", headers=headers, json={"enabled": False})
    assert client.post("/api/scan", headers=headers).json()["checked"] == 0


def test_slack_retries_pending_without_duplicate_ingestion(client, headers, monitor_data, feed, monkeypatch):
    monkeypatch.setattr("subabot.crawler.fetch_feed", AsyncMock(return_value=feed))
    delivery = AsyncMock(side_effect=[False, True])
    monkeypatch.setattr("subabot.crawler.deliver_signal", delivery)
    client.post("/api/monitors", headers=headers, json=monitor_data)
    client.post(
        "/api/integrations/slack", headers=headers, json={"webhook_url": "https://hooks.slack.com/services/T/B/fake"}
    )
    first = client.post("/api/scan", headers=headers).json()
    assert first["new_signals"] == 1 and first["slack_sent"] == 0 and first["errors"]
    second = client.post("/api/scan", headers=headers).json()
    assert second["new_signals"] == 0 and second["slack_sent"] == 1
    third = client.post("/api/scan", headers=headers).json()
    assert third["slack_sent"] == 0
    assert delivery.await_count == 2
    with Session(client.app.state.engine) as session:
        signal = session.exec(select(Signal)).one()
        assert signal.delivery_pending is False and signal.delivered_at is not None


def test_connecting_slack_does_not_send_old_signals(client, headers, monitor_data, feed, monkeypatch):
    monkeypatch.setattr("subabot.crawler.fetch_feed", AsyncMock(return_value=feed))
    delivery = AsyncMock(return_value=True)
    monkeypatch.setattr("subabot.crawler.deliver_signal", delivery)
    client.post("/api/monitors", headers=headers, json=monitor_data)
    client.post("/api/scan", headers=headers)
    client.post(
        "/api/integrations/slack", headers=headers, json={"webhook_url": "https://hooks.slack.com/services/T/B/fake"}
    )
    client.post("/api/scan", headers=headers)
    delivery.assert_not_awaited()


@pytest.mark.parametrize(
    "text,mode,excluded,expected",
    [
        ("A paid day", "any", [], []),
        ("AI and OpenAI", "all", [], ["ai", "openai"]),
        ("AI alone", "all", [], []),
        ("AI and OpenAI sponsored", "any", ["sponsored"], []),
        ("AI-assisted design", "any", [], ["ai"]),
    ],
)
def test_keyword_matching(text, mode, excluded, expected):
    monitor = Monitor(
        workspace_id="test", name="test", keywords=["ai", "openai"], match_mode=mode, exclude_keywords=excluded
    )
    assert matching_keywords(text, monitor) == expected


def test_html_text_is_safe():
    assert (
        plain_text("<p>Hello &amp; goodbye</p><style>bad</style><script>evil</script><p>World</p>")
        == "Hello & goodbye World"
    )
