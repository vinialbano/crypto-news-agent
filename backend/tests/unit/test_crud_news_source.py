"""Unit tests for NewsSource CRUD operations."""


import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.features.news.repository import NewsRepository


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_create_news_source(session: Session):
    repo = NewsRepository(session)
    source = repo.create_news_source(
        name="DL News",
        rss_url="https://www.dlnews.com/arc/outboundfeeds/rss/",
        is_active=True,
    )

    assert source.id is not None
    assert source.name == "DL News"
    assert source.rss_url == "https://www.dlnews.com/arc/outboundfeeds/rss/"
    assert source.is_active is True
    assert source.ingestion_count == 0
    assert source.last_ingestion_at is None
    assert source.last_error is None


def test_get_active_news_sources(session: Session):
    repo = NewsRepository(session)
    repo.create_news_source(
        name="DL News",
        rss_url="https://www.dlnews.com/arc/outboundfeeds/rss/",
        is_active=True,
    )
    repo.create_news_source(
        name="The Defiant",
        rss_url="https://thedefiant.io/api/feed",
        is_active=True,
    )
    repo.create_news_source(
        name="Inactive Source",
        rss_url="https://example.com/rss",
        is_active=False,
    )

    active_sources = repo.get_active_news_sources()

    assert len(active_sources) == 2
    assert all(source.is_active for source in active_sources)
    assert "Inactive Source" not in [s.name for s in active_sources]


def test_update_ingestion_status_success(session: Session):
    repo = NewsRepository(session)
    source = repo.create_news_source(
        name="DL News",
        rss_url="https://www.dlnews.com/arc/outboundfeeds/rss/",
        is_active=True,
    )

    repo.update_ingestion_status(source_id=source.id, success=True, error_message=None)

    session.refresh(source)

    assert source.ingestion_count == 1
    assert source.last_ingestion_at is not None
    assert source.last_error is None


def test_update_ingestion_status_failure(session: Session):
    repo = NewsRepository(session)
    source = repo.create_news_source(
        name="DL News",
        rss_url="https://www.dlnews.com/arc/outboundfeeds/rss/",
        is_active=True,
    )

    error_msg = "Failed to fetch RSS feed: Connection timeout"

    repo.update_ingestion_status(
        source_id=source.id, success=False, error_message=error_msg
    )

    session.refresh(source)

    assert source.ingestion_count == 0
    assert source.last_error == error_msg
    assert source.last_ingestion_at is None


def test_update_ingestion_status_multiple_times(session: Session):
    repo = NewsRepository(session)
    source = repo.create_news_source(
        name="DL News",
        rss_url="https://www.dlnews.com/arc/outboundfeeds/rss/",
        is_active=True,
    )

    for _ in range(3):
        repo.update_ingestion_status(
            source_id=source.id, success=True, error_message=None
        )
        session.refresh(source)

    assert source.ingestion_count == 3
