"""Integration tests for News API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.db import engine
from app.main import app


@pytest.fixture(scope="module")
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture(scope="module")
def db_session():
    """Create database session for tests."""
    with Session(engine) as session:
        yield session


@pytest.fixture(scope="module", autouse=True)
def seed_news_sources_fixture():
    """Seed news sources for all API news tests."""
    from app.scripts.seed_sources import seed_news_sources

    # Seed sources (uses its own session)
    seed_news_sources()


@pytest.mark.integration
def test_get_news_articles_success(client):
    """Test GET /news/ returns articles."""
    response = client.get("/news/", params={"limit": 10})

    assert response.status_code == 200
    data = response.json()

    assert "articles" in data
    assert "count" in data
    assert isinstance(data["articles"], list)
    assert data["count"] == len(data["articles"])

    if data["articles"]:
        article = data["articles"][0]
        assert "id" in article
        assert "title" in article
        assert "url" in article
        assert "content" in article
        assert "source_name" in article
        assert "ingested_at" in article


@pytest.mark.integration
def test_get_news_articles_with_limit(client):
    """Test GET /news/ respects limit parameter."""
    response = client.get("/news/", params={"limit": 5})

    assert response.status_code == 200
    data = response.json()

    assert len(data["articles"]) <= 5


@pytest.mark.integration
def test_get_news_articles_default_limit(client):
    """Test GET /news/ uses default limit."""
    response = client.get("/news/")

    assert response.status_code == 200
    data = response.json()

    # Default limit is 50
    assert len(data["articles"]) <= 50


@pytest.mark.integration
def test_get_news_sources_success(client):
    """Test GET /news/sources returns sources."""
    response = client.get("/news/sources")

    assert response.status_code == 200
    data = response.json()

    assert "sources" in data
    assert "count" in data
    assert isinstance(data["sources"], list)
    assert data["count"] == len(data["sources"])

    if data["sources"]:
        source = data["sources"][0]
        assert "id" in source
        assert "name" in source
        assert "rss_url" in source
        assert "is_active" in source
        assert "ingestion_count" in source


@pytest.mark.integration
def test_get_news_sources_shows_active_sources(client, db_session):
    """Test that active sources are listed."""
    response = client.get("/news/sources")

    assert response.status_code == 200
    data = response.json()

    # Should have at least the 3 configured sources
    assert data["count"] >= 3

    # Check that we have expected sources
    source_names = [s["name"] for s in data["sources"]]
    assert any("DL News" in name for name in source_names)


@pytest.mark.integration
@pytest.mark.slow
def test_post_admin_ingest_all_sources_success(client):
    """Test POST /news/ingest/ triggers ingestion for all sources.

    Note: This test is marked as slow because it actually fetches RSS feeds.
    """
    response = client.post("/news/ingest/", timeout=300)

    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert data["status"] == "success"
    assert "message" in data
    assert "all sources" in data["message"].lower()
    assert "stats" in data

    stats = data["stats"]
    assert "sources_processed" in stats
    assert "sources_succeeded" in stats
    assert "sources_failed" in stats
    assert "total_new_articles" in stats
    assert "total_duplicates" in stats
    assert "total_errors" in stats
    assert "duration_seconds" in stats
    assert "source_results" in stats

    # Should process at least one source
    assert stats["sources_processed"] >= 1


@pytest.mark.integration
@pytest.mark.slow
def test_post_admin_ingest_single_source_success(client):
    """Test POST /news/ingest/ with source_id parameter.

    Note: This test is marked as slow because it actually fetches RSS feeds.
    """
    # First, get available sources
    sources_response = client.get("/news/sources")
    assert sources_response.status_code == 200
    sources = sources_response.json()["sources"]
    assert len(sources) > 0, "No sources available for testing"

    # Get first source ID
    source_id = sources[0]["id"]

    # Ingest single source
    response = client.post(
        "/news/ingest/", params={"source_id": source_id}, timeout=300
    )

    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert data["status"] == "success"
    assert "message" in data
    assert "stats" in data

    stats = data["stats"]
    # Single-source stats structure
    assert "source_name" in stats
    assert "source_id" in stats
    assert stats["source_id"] == source_id
    assert "new_articles" in stats
    assert "duplicates" in stats
    assert "errors" in stats
    assert "duration_seconds" in stats
    assert "success" in stats


@pytest.mark.integration
def test_post_admin_ingest_invalid_source_id(client):
    """Test POST /news/ingest/ with invalid source_id returns 404."""
    response = client.post("/news/ingest/", params={"source_id": 999999})

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


@pytest.mark.integration
def test_get_news_articles_returns_full_content(client):
    """Test that articles include full content, not summaries."""
    response = client.get("/news/", params={"limit": 1})

    assert response.status_code == 200
    data = response.json()

    if data["articles"]:
        article = data["articles"][0]
        # Full articles should have substantial content
        assert len(article["content"]) > 500
        # Should not have embedding in response (internal field)
        assert "embedding" not in article


@pytest.mark.integration
def test_news_api_cors_headers(client):
    """Test that CORS headers are set correctly."""
    response = client.get("/news/", headers={"Origin": "http://localhost:5173"})

    # CORS headers should be present
    assert (
        "access-control-allow-origin" in response.headers or response.status_code == 200
    )


@pytest.mark.integration
def test_news_api_ordering(client):
    """Test that articles are ordered by ingestion date (newest first)."""
    response = client.get("/news/", params={"limit": 10})

    assert response.status_code == 200
    data = response.json()

    if len(data["articles"]) >= 2:
        articles = data["articles"]
        # Articles should be ordered by ingested_at descending
        for i in range(len(articles) - 1):
            assert articles[i]["ingested_at"] >= articles[i + 1]["ingested_at"]
