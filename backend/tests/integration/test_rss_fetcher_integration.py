"""Integration tests for RSS fetcher with real feeds.

These tests fetch from real RSS feeds and are marked as integration tests.
Run with: pytest tests/integration/test_rss_fetcher_integration.py -v -s
"""

import pytest

from app.services.rss_fetcher import RSSFetcher


@pytest.fixture(scope="module")
def rss_fetcher():
    """Create RSS fetcher instance."""
    return RSSFetcher()


@pytest.mark.integration
def test_fetch_dl_news(rss_fetcher):
    """Test fetching from DL News RSS feed.

    Note: This test may be skipped if the external RSS feed is
    temporarily unavailable or returns non-XML responses.
    """
    source = {
        "name": "DL News (Integration Test)",
        "rss_url": "https://www.dlnews.com/arc/outboundfeeds/rss/",
    }

    articles = rss_fetcher.fetch_feed(source)

    # Verify we got some articles
    print(f"\nDL News: Fetched {len(articles)} articles")

    # If the feed failed completely, skip test
    if len(articles) == 0:
        pytest.skip(
            "DL News feed is temporarily unavailable or returning no articles"
        )

    assert len(articles) > 0, "Should have fetched at least 1 article"

    # Verify article structure
    article = articles[0]
    assert "title" in article
    assert "url" in article
    assert "content" in article
    assert "published_at" in article
    assert len(article["content"]) > 100, "Article should have substantial content"


@pytest.mark.integration
def test_fetch_the_defiant(rss_fetcher):
    """Test fetching from The Defiant RSS feed."""
    source = {
        "name": "The Defiant (Integration Test)",
        "rss_url": "https://thedefiant.io/api/feed",
    }

    articles = rss_fetcher.fetch_feed(source)

    # Verify we got some articles
    print(f"\nThe Defiant: Fetched {len(articles)} articles")
    assert len(articles) > 0, "Should have fetched at least 1 article"

    # Verify article structure
    article = articles[0]
    assert "title" in article
    assert "url" in article
    assert "content" in article


@pytest.mark.integration
def test_fetch_cointelegraph(rss_fetcher):
    """Test fetching from Cointelegraph RSS feed."""
    source = {
        "name": "Cointelegraph (Integration Test)",
        "rss_url": "https://cointelegraph.com/rss",
    }

    articles = rss_fetcher.fetch_feed(source)

    # Verify we got some articles
    print(f"\nCointelegraph: Fetched {len(articles)} articles")
    assert len(articles) > 0, "Should have fetched at least 1 article"

    # Verify article structure
    article = articles[0]
    assert "title" in article
    assert "url" in article
    assert "content" in article


@pytest.mark.integration
def test_article_content_quality(rss_fetcher):
    """Test that fetched articles have full content, not just summaries."""
    source = {
        "name": "Content Quality Test",
        "rss_url": "https://www.dlnews.com/arc/outboundfeeds/rss/",
    }

    # Fetch articles
    articles = rss_fetcher.fetch_feed(source)

    if not articles:
        pytest.skip("No articles fetched to test content quality")

    # Test first article
    article = articles[0]
    print("\nSample article:")
    print(f"Title: {article['title']}")
    print(f"Content length: {len(article['content'])} characters")
    print(f"Content preview: {article['content'][:200]}...")

    # Verify content is substantial (full article, not just summary)
    assert len(article["content"]) > 100, "Article should have substantial content"


@pytest.mark.integration
def test_duplicate_prevention(rss_fetcher):
    """Test that fetching the same feed twice returns same articles.

    Note: This test verifies that the fetcher returns consistent results.
    Actual duplicate detection is handled by IngestionService.
    """
    import time

    source = {
        "name": "Duplicate Prevention Test",
        "rss_url": "https://www.dlnews.com/arc/outboundfeeds/rss/",
    }

    # First fetch
    articles1 = rss_fetcher.fetch_feed(source)
    print(f"\nFirst fetch: {len(articles1)} articles")

    # Wait to avoid rate limiting (429 errors)
    time.sleep(5)

    # Second fetch (should return same articles from feed)
    articles2 = rss_fetcher.fetch_feed(source)
    print(f"Second fetch: {len(articles2)} articles")

    # If EITHER fetch was rate limited or failed, skip test
    # External RSS feeds are unreliable and may fail at any time
    if len(articles1) == 0 or len(articles2) == 0:
        pytest.skip(
            f"One or both fetches failed (first: {len(articles1)}, second: {len(articles2)}). "
            "External RSS API is unreliable during testing."
        )

    # Both fetches should return the same number of articles
    # (RSS feeds typically return the same items)
    assert len(articles1) == len(articles2), (
        "Fetching same feed twice should return same number of articles"
    )

    # URLs should match (same articles)
    urls1 = {article["url"] for article in articles1}
    urls2 = {article["url"] for article in articles2}
    assert urls1 == urls2, "Should fetch same article URLs"
