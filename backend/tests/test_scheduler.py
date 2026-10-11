import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from subabot.api import create_app
from subabot.config import Settings


def test_lifespan_scheduler_collects_signals(tmp_path, monitor_data, feed, monkeypatch):
    monkeypatch.setattr("subabot.crawler.fetch_feed", AsyncMock(return_value=feed))
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'scheduled.db'}",
        scan_cooldown_seconds=0,
        scheduler_enabled=True,
    )
    # Shorten only the test clock; production validation requires at least 60 seconds.
    settings.scan_interval_seconds = 0.02
    with TestClient(create_app(settings)) as client:
        token = client.post("/api/workspaces").json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        client.post("/api/monitors", headers=headers, json=monitor_data)
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            signals = client.get("/api/signals", headers=headers).json()
            if signals:
                break
            time.sleep(0.01)
        assert len(signals) == 1


def test_overlapping_scans_and_deletes_are_rejected(client, headers, monitor_data, feed, monkeypatch):
    started = threading.Event()
    finish = threading.Event()

    async def delayed_feed(*args):
        started.set()
        while not finish.is_set():
            await asyncio.sleep(0.001)
        return feed

    monkeypatch.setattr("subabot.crawler.fetch_feed", delayed_feed)
    monitor = client.post("/api/monitors", headers=headers, json=monitor_data).json()
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(client.post, "/api/scan", headers=headers)
        try:
            assert started.wait(timeout=3)
            assert client.post("/api/scan", headers=headers).status_code == 409
            assert client.delete("/api/workspace", headers=headers).status_code == 409
            assert client.delete(f"/api/monitors/{monitor['id']}", headers=headers).status_code == 409
            # Pausing while a fetch is running must prevent ingestion from its stale snapshot.
            assert (
                client.patch(f"/api/monitors/{monitor['id']}", headers=headers, json={"enabled": False}).status_code
                == 200
            )
        finally:
            finish.set()
        assert future.result(timeout=3).json()["new_signals"] == 0
    assert client.get("/api/signals", headers=headers).json() == []
