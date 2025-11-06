"""Integration tests for RSS fetcher with real feeds.

These tests fetch from real RSS feeds and are marked as integration tests.
Run with: pytest tests/integration/test_rss_fetcher_integration.py -v -s
"""

import pytest
from sqlmodel import Session

from app.core.db import engine
from app.features.news.models import NewsSource
from app.features.news.rss_fetcher import RSSFetcher


@pytest.fixture(scope="module")
def rss_fetcher():
    """Create RSS fetcher instance."""
    return RSSFetcher()


@pytest.fixture(scope="module")
def db_session():
    """Create database session for integration tests."""
    with Session(engine) as session:
        yield session


@pytest.mark.integration
def test_fetch_dl_news(rss_fetcher, db_session):
    """Test fetching from DL News RSS feed.

    Note: This test may be skipped if the external RSS feed is
    temporarily unavailable or returns non-XML responses.
    """
    source = NewsSource(
        id=999,  # Temporary ID for testing
        name="DL News (Integration Test)",
        rss_url="https://www.dlnews.com/arc/outboundfeeds/rss/",
        is_active=True,
    )

    stats = rss_fetcher.fetch_feed(db_session, source)

    # Verify we got some articles
    print(f"\nDL News stats: {stats}")

    # If the feed failed completely (returns HTML instead of XML), skip test
    if (
        stats["errors"] > 0
        and stats["new_articles"] == 0
        and stats["duplicate_articles"] == 0
    ):
        pytest.skip(
            "DL News feed is temporarily unavailable or returning non-XML content"
        )

    assert stats["new_articles"] >= 0  # May have duplicates if run multiple times

    # Note: new_articles may be 0 if articles already exist in DB
    total_processed = stats["new_articles"] + stats["duplicate_articles"]
    assert total_processed > 0, "Should have processed at least 1 article"


@pytest.mark.integration
def test_fetch_the_defiant(rss_fetcher, db_session):
    """Test fetching from The Defiant RSS feed."""
    source = NewsSource(
        id=998,  # Temporary ID for testing
        name="The Defiant (Integration Test)",
        rss_url="https://thedefiant.io/api/feed",
        is_active=True,
    )

    stats = rss_fetcher.fetch_feed(db_session, source)

    # Verify we got some articles
    print(f"\nThe Defiant stats: {stats}")
    assert stats["new_articles"] >= 0
    assert stats["errors"] == 0

    total_processed = stats["new_articles"] + stats["duplicate_articles"]
    assert total_processed > 0, "Should have processed at least 1 article"


@pytest.mark.integration
def test_fetch_cointelegraph(rss_fetcher, db_session):
    """Test fetching from Cointelegraph RSS feed."""
    source = NewsSource(
        id=997,  # Temporary ID for testing
        name="Cointelegraph (Integration Test)",
        rss_url="https://cointelegraph.com/rss",
        is_active=True,
    )

    stats = rss_fetcher.fetch_feed(db_session, source)

    # Verify we got some articles
    print(f"\nCointelegraph stats: {stats}")
    assert stats["new_articles"] >= 0
    assert stats["errors"] == 0

    total_processed = stats["new_articles"] + stats["duplicate_articles"]
    assert total_processed > 0, "Should have processed at least 1 article"


@pytest.mark.integration
def test_article_content_quality(rss_fetcher, db_session):
    """Test that fetched articles have full content, not just summaries."""
    from app.features.news.repository import NewsRepository

    source = NewsSource(
        id=996,  # Temporary ID for testing
        name="Content Quality Test",
        rss_url="https://www.dlnews.com/arc/outboundfeeds/rss/",
        is_active=True,
    )

    # Fetch articles
    stats = rss_fetcher.fetch_feed(db_session, source)

    # Get one of the recently fetched articles
    repo = NewsRepository(db_session)
    articles = repo.get_recent_articles(limit=1)

    if articles:
        article = articles[0]
        print("\nSample article:")
        print(f"Title: {article.title}")
        print(f"Content length: {len(article.content)} characters")
        print(f"Content preview: {article.content[:200]}...")

        # Verify content is substantial (full article, not just summary)
        assert len(article.content) > 100, "Article should have substantial content"

        # Verify we have embeddings
        assert article.embedding is not None, "Article should have embeddings"
        assert len(article.embedding) == 768, (
            "Embedding should be 768 dimensions (nomic-embed-text)"
        )


@pytest.mark.integration
def test_duplicate_prevention(rss_fetcher, db_session):
    """Test that fetching the same feed twice prevents duplicates."""
    source = NewsSource(
        id=995,  # Temporary ID for testing
        name="Duplicate Prevention Test",
        rss_url="https://www.dlnews.com/arc/outboundfeeds/rss/",
        is_active=True,
    )

    # First fetch
    stats1 = rss_fetcher.fetch_feed(db_session, source)
    print(f"\nFirst fetch stats: {stats1}")

    # Second fetch (should detect duplicates)
    stats2 = rss_fetcher.fetch_feed(db_session, source)
    print(f"Second fetch stats: {stats2}")

    # On second fetch, we should have mostly duplicates
    assert stats2["duplicate_articles"] >= stats2["new_articles"], (
        "Second fetch should have more duplicates than new articles"
    )
