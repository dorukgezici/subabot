import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func
from sqlmodel import Session, select

from subabot.api import create_app
from subabot.config import Settings
from subabot.models import Workspace

PROXY_SECRET = "test-server-only-proxy-secret"
PROXY_HEADERS = {"x-subabot-proxy-secret": PROXY_SECRET}


@pytest.fixture
def protected_client(tmp_path):
    app = create_app(
        Settings(
            database_url=f"sqlite:///{tmp_path / 'protected.db'}",
            scheduler_enabled=False,
            trust_proxy_client_ip=True,
            proxy_shared_secret=PROXY_SECRET,
        )
    )
    with TestClient(app) as client:
        yield client


def test_empty_proxy_secret_preserves_direct_local_access(client):
    assert client.get("/api/templates").status_code == 200
    assert client.post("/api/workspaces").status_code == 201


@pytest.mark.parametrize("supplied_secret", [None, "incorrect-secret"])
def test_protected_api_rejects_before_creating_workspaces(protected_client, supplied_secret):
    headers = {"x-subabot-client-address": "198.51.100.1"}
    if supplied_secret is not None:
        headers["x-subabot-proxy-secret"] = supplied_secret
    response = protected_client.post("/api/workspaces", headers=headers, json={"name": "Rejected"})
    assert response.status_code == 401
    assert PROXY_SECRET not in response.text
    assert response.headers["cache-control"] == "no-store"
    with Session(protected_client.app.state.engine) as session:
        assert session.exec(select(func.count()).select_from(Workspace)).one() == 0
    assert protected_client.get("/api/templates", headers=headers).status_code == 401


def test_health_probe_remains_public_with_proxy_protection(protected_client):
    assert protected_client.get("/api/health").json()["status"] == "ok"
    assert protected_client.get("/api/health", headers={"x-subabot-proxy-secret": "wrong"}).status_code == 200


def test_proxy_secret_does_not_replace_workspace_authorization(protected_client):
    result = protected_client.post("/api/workspaces", headers=PROXY_HEADERS, json={"name": "Original"})
    assert result.status_code == 201
    workspace_headers = {"Authorization": f"Bearer {result.json()['token']}"}
    assert protected_client.get("/api/workspace", headers=PROXY_HEADERS).status_code == 401
    response = protected_client.patch("/api/workspace", headers=workspace_headers, json={"name": "Spoofed"})
    assert response.status_code == 401
    authorized_headers = {**PROXY_HEADERS, **workspace_headers}
    assert protected_client.get("/api/workspace", headers=authorized_headers).json()["workspace"]["name"] == "Original"
    assert (
        protected_client.patch("/api/workspace", headers=authorized_headers, json={"name": "Updated"}).status_code
        == 200
    )
    assert protected_client.get("/api/workspace", headers=authorized_headers).json()["workspace"]["name"] == "Updated"


def test_spoofed_client_addresses_cannot_bypass_or_poison_rate_limits(protected_client):
    for index in range(25):
        assert (
            protected_client.post(
                "/api/workspaces", headers={"x-subabot-client-address": f"198.51.100.{index}"}
            ).status_code
            == 401
        )
    trusted_client = {**PROXY_HEADERS, "x-subabot-client-address": "198.51.100.1"}
    for _ in range(20):
        assert protected_client.post("/api/workspaces", headers=trusted_client).status_code == 201
    assert protected_client.post("/api/workspaces", headers=trusted_client).status_code == 429
    another_client = {**PROXY_HEADERS, "x-subabot-client-address": "198.51.100.2"}
    assert protected_client.post("/api/workspaces", headers=another_client).status_code == 201


def test_proxy_secret_is_redacted_from_settings_repr_and_serialization():
    settings = Settings(proxy_shared_secret=PROXY_SECRET)
    assert PROXY_SECRET not in repr(settings)
    assert PROXY_SECRET not in settings.model_dump_json()
