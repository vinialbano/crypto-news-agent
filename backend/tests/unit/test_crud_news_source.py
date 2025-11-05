"""Unit tests for NewsSource CRUD operations."""
import pytest
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool
from datetime import datetime

from app.models import NewsSource
from app import crud


@pytest.fixture(name="session")
def session_fixture():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_create_news_source(session: Session):
    """Test creating a news source."""
    source = crud.create_news_source(
        session=session,
        name="DL News",
        rss_url="https://www.dlnews.com/arc/outboundfeeds/rss/",
        is_active=True
    )

    assert source.id is not None
    assert source.name == "DL News"
    assert source.rss_url == "https://www.dlnews.com/arc/outboundfeeds/rss/"
    assert source.is_active is True
    assert source.ingestion_count == 0
    assert source.last_ingestion_at is None
    assert source.last_error is None


def test_get_active_news_sources(session: Session):
    """Test retrieving only active news sources."""
    # Create active and inactive sources
    crud.create_news_source(
        session=session,
        name="DL News",
        rss_url="https://www.dlnews.com/arc/outboundfeeds/rss/",
        is_active=True
    )
    crud.create_news_source(
        session=session,
        name="The Defiant",
        rss_url="https://thedefiant.io/api/feed",
        is_active=True
    )
    crud.create_news_source(
        session=session,
        name="Inactive Source",
        rss_url="https://example.com/rss",
        is_active=False
    )

    active_sources = crud.get_active_news_sources(session)

    assert len(active_sources) == 2
    assert all(source.is_active for source in active_sources)
    assert "Inactive Source" not in [s.name for s in active_sources]


def test_update_ingestion_status_success(session: Session):
    """Test updating ingestion status after successful ingestion."""
    source = crud.create_news_source(
        session=session,
        name="DL News",
        rss_url="https://www.dlnews.com/arc/outboundfeeds/rss/",
        is_active=True
    )

    crud.update_ingestion_status(
        session=session,
        source_id=source.id,
        success=True,
        error_message=None
    )

    session.refresh(source)

    assert source.ingestion_count == 1
    assert source.last_ingestion_at is not None
    assert source.last_error is None


def test_update_ingestion_status_failure(session: Session):
    """Test updating ingestion status after failed ingestion."""
    source = crud.create_news_source(
        session=session,
        name="DL News",
        rss_url="https://www.dlnews.com/arc/outboundfeeds/rss/",
        is_active=True
    )

    error_msg = "Failed to fetch RSS feed: Connection timeout"

    crud.update_ingestion_status(
        session=session,
        source_id=source.id,
        success=False,
        error_message=error_msg
    )

    session.refresh(source)

    assert source.ingestion_count == 0  # Count not incremented on failure
    assert source.last_error == error_msg
    assert source.last_ingestion_at is None  # Not updated on failure


def test_update_ingestion_status_multiple_times(session: Session):
    """Test ingestion count increments correctly over multiple successes."""
    source = crud.create_news_source(
        session=session,
        name="DL News",
        rss_url="https://www.dlnews.com/arc/outboundfeeds/rss/",
        is_active=True
    )

    # Simulate 3 successful ingestions
    for _ in range(3):
        crud.update_ingestion_status(
            session=session,
            source_id=source.id,
            success=True,
            error_message=None
        )
        session.refresh(source)

    assert source.ingestion_count == 3
