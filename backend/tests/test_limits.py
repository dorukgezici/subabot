from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from subabot.api import create_app
from subabot.config import Settings


def test_proxy_client_ip_is_ignored_unless_explicitly_trusted(client):
    for index in range(20):
        assert client.post("/api/workspaces", headers={"x-subabot-client-address": f"1.1.1.{index}"}).status_code == 201
    assert client.post("/api/workspaces", headers={"x-subabot-client-address": "2.2.2.2"}).status_code == 429


def test_trusted_proxy_separates_client_rate_limits(tmp_path):
    app = create_app(
        Settings(database_url=f"sqlite:///{tmp_path / 'proxy.db'}", scheduler_enabled=False, trust_proxy_client_ip=True)
    )
    with TestClient(app) as client:
        for _ in range(20):
            assert client.post("/api/workspaces", headers={"x-subabot-client-address": "1.1.1.1"}).status_code == 201
        assert client.post("/api/workspaces", headers={"x-subabot-client-address": "1.1.1.1"}).status_code == 429
        assert client.post("/api/workspaces", headers={"x-subabot-client-address": "2.2.2.2"}).status_code == 201


def test_scan_errors_are_persisted_then_cleared(client, headers, monitor_data, feed, monkeypatch):
    client.post("/api/monitors", headers=headers, json=monitor_data)
    monkeypatch.setattr("subabot.crawler.fetch_feed", AsyncMock(side_effect=ValueError("Invalid feed")))
    client.post("/api/scan", headers=headers)
    assert client.get("/api/monitors", headers=headers).json()[0]["last_error"] == "1 of 1 feeds could not be checked."
    monkeypatch.setattr("subabot.crawler.fetch_feed", AsyncMock(return_value=feed))
    client.post("/api/scan", headers=headers)
    assert client.get("/api/monitors", headers=headers).json()[0]["last_error"] is None
    assert len(client.get("/api/signals?unread=true", headers=headers).json()) == 1
    assert len(client.get("/api/signals?unread=false", headers=headers).json()) == 0
