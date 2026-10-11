import pytest
from fastapi.testclient import TestClient

from subabot.api import create_app
from subabot.config import Settings


@pytest.fixture
def client(tmp_path):
    app = create_app(
        Settings(database_url=f"sqlite:///{tmp_path / 'test.db'}", scheduler_enabled=False, scan_cooldown_seconds=0)
    )
    with TestClient(app) as client:
        yield client


@pytest.fixture
def headers(client):
    result = client.post("/api/workspaces", json={"name": "Test studio"})
    assert result.status_code == 201, result.text
    return {"Authorization": f"Bearer {result.json()['token']}"}


@pytest.fixture
def monitor_data():
    return {"name": "AI radar", "keywords": ["AI", "OpenAI"], "feed_urls": ["https://example.com/feed.xml"]}


@pytest.fixture
def feed():
    return {
        "source": "Example News",
        "url": "https://example.com/feed.xml",
        "entries": [
            {
                "title": "OpenAI releases a new model",
                "link": "https://example.com/ai-story?utm_source=rss",
                "summary": "<p>Useful AI news.</p><script>alert('bad')</script>",
            },
            {"title": "A paid holiday", "link": "https://example.com/holiday", "summary": "No relevant keyword."},
            {"title": "AI bad link", "link": "javascript:alert(1)", "summary": "AI"},
        ],
    }
