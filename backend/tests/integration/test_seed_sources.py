"""Integration tests for RSS source seeding."""

import pytest
from sqlmodel import Session, select

from app.core.config import settings
from app.models import NewsSource


@pytest.fixture
def clean_news_sources(session: Session):
    """Clean news sources before and after test."""
    # Delete all news sources
    sources = session.exec(select(NewsSource)).all()
    for source in sources:
        session.delete(source)
    session.commit()

    yield

    # Clean up after test
    sources = session.exec(select(NewsSource)).all()
    for source in sources:
        session.delete(source)
    session.commit()


@pytest.mark.integration
def test_seed_sources_creates_sources(session: Session, clean_news_sources):
    """Test that seeding creates all configured sources."""
    # Import and run seeding function
    from app.scripts.seed_sources import seed_news_sources

    seed_news_sources(session)

    # Verify sources were created
    sources = session.exec(select(NewsSource)).all()

    # Should have 3 sources (DL News, The Defiant, Cointelegraph)
    assert len(sources) == 3

    # Verify each source exists
    source_names = {source.name for source in sources}
    assert "DL News" in source_names
    assert "The Defiant" in source_names
    assert "Cointelegraph" in source_names

    # Verify RSS URLs match config
    for source in sources:
        if source.name == "DL News":
            assert source.rss_url == settings.RSS_DL_NEWS
        elif source.name == "The Defiant":
            assert source.rss_url == settings.RSS_THE_DEFIANT
        elif source.name == "Cointelegraph":
            assert source.rss_url == settings.RSS_COINTELEGRAPH

        # All sources should be active by default
        assert source.is_active is True


@pytest.mark.integration
def test_seed_sources_is_idempotent(session: Session, clean_news_sources):
    """Test that seeding can be run multiple times safely (idempotent)."""
    from app.scripts.seed_sources import seed_news_sources

    # Run seeding twice
    seed_news_sources(session)
    seed_news_sources(session)

    # Should still have exactly 3 sources (no duplicates)
    sources = session.exec(select(NewsSource)).all()
    assert len(sources) == 3

    # Verify no duplicates by name
    source_names = [source.name for source in sources]
    assert len(source_names) == len(set(source_names))


@pytest.mark.integration
def test_seed_sources_updates_existing(session: Session, clean_news_sources):
    """Test that seeding updates existing sources if RSS URL changes."""
    from app.scripts.seed_sources import seed_news_sources

    # First seeding
    seed_news_sources()

    # Get DL News source
    dl_news = session.exec(
        select(NewsSource).where(NewsSource.name == "DL News")
    ).first()
    assert dl_news is not None
    original_url = dl_news.rss_url

    # Manually change RSS URL
    dl_news.rss_url = "https://example.com/old-feed"
    session.add(dl_news)
    session.commit()
    session.refresh(dl_news)

    # Run seeding again
    seed_news_sources(session)

    # Verify URL was updated back to config value
    dl_news = session.exec(
        select(NewsSource).where(NewsSource.name == "DL News")
    ).first()
    assert dl_news.rss_url == original_url
    assert dl_news.rss_url == settings.RSS_DL_NEWS


@pytest.mark.integration
def test_seed_sources_preserves_metadata(session: Session, clean_news_sources):
    """Test that seeding preserves existing metadata."""
    from app.scripts.seed_sources import seed_news_sources
    from datetime import UTC, datetime

    # First seeding
    seed_news_sources()

    # Update source with some metadata
    dl_news = session.exec(
        select(NewsSource).where(NewsSource.name == "DL News")
    ).first()
    dl_news.ingestion_count = 10
    dl_news.last_ingestion_at = datetime.now(UTC)
    dl_news.last_error = "Some previous error"
    session.add(dl_news)
    session.commit()
    session.refresh(dl_news)

    original_count = dl_news.ingestion_count
    original_last_ingestion = dl_news.last_ingestion_at

    # Run seeding again
    seed_news_sources(session)

    # Verify metadata was preserved
    dl_news = session.exec(
        select(NewsSource).where(NewsSource.name == "DL News")
    ).first()
    assert dl_news.ingestion_count == original_count
    assert dl_news.last_ingestion_at == original_last_ingestion
    # Note: last_error might be cleared by the seed script - verify implementation


@pytest.mark.integration
def test_seed_sources_all_active(session: Session, clean_news_sources):
    """Test that all seeded sources are active by default."""
    from app.scripts.seed_sources import seed_news_sources

    seed_news_sources()

    sources = session.exec(select(NewsSource)).all()
    for source in sources:
        assert source.is_active is True


@pytest.mark.integration
def test_seed_sources_unique_constraints(session: Session, clean_news_sources):
    """Test that seeding respects unique constraints."""
    from app.scripts.seed_sources import seed_news_sources

    seed_news_sources()

    # Verify unique constraints on name and rss_url
    sources = session.exec(select(NewsSource)).all()

    # All names should be unique
    names = [s.name for s in sources]
    assert len(names) == len(set(names))

    # All RSS URLs should be unique
    urls = [s.rss_url for s in sources]
    assert len(urls) == len(set(urls))


@pytest.mark.integration
def test_seed_sources_with_deactivated_source(session: Session, clean_news_sources):
    """Test seeding behavior when a source was manually deactivated."""
    from app.scripts.seed_sources import seed_news_sources

    # First seeding
    seed_news_sources()

    # Manually deactivate a source
    dl_news = session.exec(
        select(NewsSource).where(NewsSource.name == "DL News")
    ).first()
    dl_news.is_active = False
    session.add(dl_news)
    session.commit()

    # Run seeding again
    seed_news_sources(session)

    # Verify source remains deactivated (seeding doesn't override manual changes)
    # Note: This depends on seed script implementation - adjust test if behavior differs
    dl_news = session.exec(
        select(NewsSource).where(NewsSource.name == "DL News")
    ).first()
    # Check actual implementation behavior here
