from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from subabot.api import create_app
from subabot.config import Settings
from subabot.models import Workspace


def test_health_templates_and_openapi(client):
    assert client.get("/api/health").json()["status"] == "ok"
    templates = client.get("/api/templates").json()
    assert len(templates) == 6
    assert all(template["feed_urls"] and template["keywords"] for template in templates)
    assert client.get("/openapi.json").status_code == 200


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/api/workspace"),
        ("get", "/api/monitors"),
        ("get", "/api/signals"),
        ("post", "/api/scan"),
        ("delete", "/api/workspace"),
        ("delete", "/api/integrations/slack"),
    ],
)
def test_private_routes_need_token(client, method, path):
    assert getattr(client, method)(path).status_code == 401
    assert getattr(client, method)(path, headers={"Authorization": "Bearer fake"}).status_code == 401


def test_workspace_key_is_hashed_and_private(client, headers):
    result = client.get("/api/workspace", headers=headers)
    assert result.status_code == 200
    assert result.json()["workspace"]["name"] == "Test studio"
    assert result.json()["slack"] == {"connected": False}
    assert "token" not in result.text and "webhook" not in result.text
    with Session(client.app.state.engine) as session:
        workspace = session.exec(select(Workspace)).first()
        assert workspace.token_hash != headers["Authorization"].split()[1]
        assert len(workspace.token_hash) == 64
    changed = client.patch("/api/workspace", headers=headers, json={"name": "My company"})
    assert changed.json()["name"] == "My company"


def test_monitor_crud_and_isolation(client, headers, monitor_data):
    created = client.post("/api/monitors", headers=headers, json=monitor_data)
    assert created.status_code == 201, created.text
    monitor = created.json()
    assert monitor["keywords"] == ["ai", "openai"]
    assert monitor["created_at"].endswith("Z")
    assert monitor["color"] == "#357a57"
    assert monitor["public"] is False
    assert len(client.get("/api/monitors", headers=headers).json()) == 1
    other = client.post("/api/workspaces", json={"name": "Other"}).json()
    other_headers = {"Authorization": f"Bearer {other['token']}"}
    path = f"/api/monitors/{monitor['id']}"
    assert client.patch(path, headers=other_headers, json={"name": "Stolen"}).status_code == 404
    assert client.delete(path, headers=other_headers).status_code == 404
    assert client.get("/api/signals", headers=other_headers, params={"monitor_id": monitor["id"]}).status_code == 404
    assert client.get("/api/monitors", headers=other_headers).json() == []
    changed = client.patch(path, headers=headers, json={"enabled": False, "name": "Paused"})
    assert changed.status_code == 200
    assert changed.json()["enabled"] is False
    assert client.patch(path, headers=headers, json={"keywords": []}).status_code == 422
    assert client.patch(path, headers=headers, json={"name": None}).status_code == 422
    assert client.delete(path, headers=headers).status_code == 204
    assert client.get("/api/monitors", headers=headers).json() == []


@pytest.mark.parametrize(
    "changes",
    [
        {"keywords": []},
        {"keywords": [""]},
        {"keywords": ["a" * 81]},
        {"feed_urls": []},
        {"feed_urls": ["http://127.0.0.1/feed"]},
        {"feed_urls": ["file:///etc/passwd"]},
        {"feed_urls": ["https://example.com:8000/feed"]},
        {"feed_urls": ["http://169.254.169.254/latest"]},
        {"name": " "},
        {"match_mode": "invalid"},
        {"color": "url(javascript:bad)"},
        {"workspace_id": "another"},
    ],
)
def test_monitor_validation(client, headers, monitor_data, changes):
    assert client.post("/api/monitors", headers=headers, json={**monitor_data, **changes}).status_code == 422


def test_public_board_explicit_publishing_and_revocation(client, headers, monitor_data, feed, monkeypatch):
    monkeypatch.setattr("subabot.crawler.fetch_feed", AsyncMock(return_value=feed))
    monitor = client.post("/api/monitors", headers=headers, json=monitor_data).json()
    assert monitor["share_slug"] is None
    client.post("/api/scan", headers=headers)
    published = client.post(f"/api/monitors/{monitor['id']}/publish", headers=headers).json()
    slug = published["share_slug"]
    board = client.get(f"/api/public/{slug}")
    assert board.status_code == 200
    assert board.json()["monitor"]["feed_urls"] == monitor_data["feed_urls"]
    assert len(board.json()["signals"]) == 1
    for private in ["workspace_id", "token", "webhook", "is_read", "is_bookmarked", "delivery_pending"]:
        assert private not in board.text
    client.patch(f"/api/monitors/{monitor['id']}", headers=headers, json={"public": False})
    assert client.get(f"/api/public/{slug}").status_code == 404
    republished = client.post(f"/api/monitors/{monitor['id']}/publish", headers=headers).json()
    assert republished["share_slug"] != slug


def test_templates_and_limits(client, headers):
    result = client.post("/api/monitors/from-template/ai-radar", headers=headers)
    assert result.status_code == 201, result.text
    assert result.json()["name"] == "AI radar"
    assert client.post("/api/monitors/from-template/nope", headers=headers).status_code == 404
    client.app.state.settings.max_monitors = 1
    assert client.post("/api/monitors/from-template/ai-radar", headers=headers).status_code == 409


def test_delete_workspace_removes_all_data(client, headers, monitor_data, feed, monkeypatch):
    monkeypatch.setattr("subabot.crawler.fetch_feed", AsyncMock(return_value=feed))
    monitor = client.post("/api/monitors", headers=headers, json={**monitor_data, "public": True}).json()
    client.post("/api/scan", headers=headers)
    assert client.delete("/api/workspace", headers=headers).status_code == 204
    assert client.get("/api/workspace", headers=headers).status_code == 401
    assert client.get(f"/api/public/{monitor['share_slug']}").status_code == 404


def test_slack_validation_never_echoes_secret(client, headers):
    secret = "very-secret-key"
    response = client.post(
        "/api/integrations/slack", headers=headers, json={"webhook_url": f"http://evil.com/{secret}"}
    )
    assert response.status_code == 422
    assert secret not in response.text
    for url in ["https://hooks.slack.com.evil.com/services/T/B/X", "https://hooks.slack.com/services/T/B/X?secret=1"]:
        assert client.post("/api/integrations/slack", headers=headers, json={"webhook_url": url}).status_code == 422
    response = client.post(
        "/api/integrations/slack", headers=headers, json={"webhook_url": "https://hooks.slack.com/services/T/B/secret"}
    )
    assert response.json() == {"connected": True}
    assert client.get("/api/workspace", headers=headers).json()["slack"]["connected"] is True
    assert client.delete("/api/integrations/slack", headers=headers).status_code == 204
    assert client.get("/api/workspace", headers=headers).json()["slack"]["connected"] is False


def test_workspace_persists_across_restart(tmp_path):
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'persist.db'}", scheduler_enabled=False)
    with TestClient(create_app(settings)) as client:
        token = client.post("/api/workspaces", json={"name": "Keep me"}).json()["token"]
    with TestClient(create_app(settings)) as client:
        assert (
            client.get("/api/workspace", headers={"Authorization": f"Bearer {token}"}).json()["workspace"]["name"]
            == "Keep me"
        )


def test_create_workspace_rate_limit(client):
    for _ in range(20):
        assert client.post("/api/workspaces").status_code == 201
    assert client.post("/api/workspaces").status_code == 429


def test_request_body_limits_and_invalid_length(client):
    assert client.post("/api/workspaces", content=b"x" * 32_769).status_code == 413
    response = client.post(
        "/api/workspaces",
        content=b'{"name":"Okay"}',
        headers={"Content-Type": "application/json", "Content-Length": "invalid"},
    )
    assert response.status_code == 201
    response = client.post("/api/workspaces", content=iter([b"x" * 20_000, b"x" * 20_000]))
    assert response.status_code == 413
