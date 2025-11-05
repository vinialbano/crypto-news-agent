"""Unit tests for NewsArticle CRUD operations."""
import pytest
from sqlmodel import Session, create_engine, SQLModel, text
from sqlmodel.pool import StaticPool
from datetime import datetime, timedelta
from pgvector.sqlalchemy import Vector
import numpy as np

from app.models import NewsArticle
from app import crud


@pytest.fixture(name="session")
def session_fixture():
    """Create an in-memory SQLite database for testing.

    Note: SQLite doesn't support pgvector, so semantic_search tests will be skipped.
    Integration tests should use PostgreSQL with pgvector.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_create_news_article(session: Session):
    """Test creating a news article with embedding."""
    embedding = np.random.rand(768).tolist()

    article = crud.create_news_article(
        session=session,
        title="Bitcoin Surges to New High",
        url="https://example.com/bitcoin-surges",
        content="Bitcoin reached a new all-time high today, surpassing $100,000 for the first time in history.",
        source_name="DL News",
        published_at=datetime.utcnow(),
        embedding=embedding
    )

    assert article.id is not None
    assert article.title == "Bitcoin Surges to New High"
    assert article.url == "https://example.com/bitcoin-surges"
    assert article.source_name == "DL News"
    assert article.content_hash is not None
    assert len(article.content_hash) == 64  # SHA-256 hex string
    assert article.ingested_at is not None


def test_get_by_hash_existing(session: Session):
    """Test retrieving article by content hash."""
    embedding = np.random.rand(768).tolist()

    article = crud.create_news_article(
        session=session,
        title="Bitcoin Surges to New High",
        url="https://example.com/bitcoin-surges",
        content="Bitcoin reached a new all-time high today.",
        source_name="DL News",
        published_at=datetime.utcnow(),
        embedding=embedding
    )

    # Try to find the article by hash
    found_article = crud.get_article_by_hash(
        session=session,
        content_hash=article.content_hash
    )

    assert found_article is not None
    assert found_article.id == article.id
    assert found_article.title == article.title


def test_get_by_hash_nonexistent(session: Session):
    """Test retrieving non-existent article returns None."""
    found_article = crud.get_article_by_hash(
        session=session,
        content_hash="0" * 64  # Non-existent hash
    )

    assert found_article is None


def test_duplicate_detection_same_title_and_url(session: Session):
    """Test that duplicate articles (same title + URL) are detected."""
    embedding = np.random.rand(768).tolist()

    # Create first article
    article1 = crud.create_news_article(
        session=session,
        title="Bitcoin Surges to New High",
        url="https://example.com/bitcoin-surges",
        content="Content version 1",
        source_name="DL News",
        published_at=datetime.utcnow(),
        embedding=embedding
    )

    # Try to create duplicate (same title + URL, different content)
    # Should raise IntegrityError due to unique content_hash
    with pytest.raises(Exception):  # SQLAlchemy IntegrityError
        crud.create_news_article(
            session=session,
            title="Bitcoin Surges to New High",
            url="https://example.com/bitcoin-surges",
            content="Content version 2",  # Different content
            source_name="DL News",
            published_at=datetime.utcnow(),
            embedding=embedding
        )


def test_get_recent_articles(session: Session):
    """Test retrieving recent articles sorted by ingestion time."""
    embedding = np.random.rand(768).tolist()

    # Create 5 articles with different ingestion times
    for i in range(5):
        crud.create_news_article(
            session=session,
            title=f"Article {i}",
            url=f"https://example.com/article-{i}",
            content=f"Content for article {i}",
            source_name="DL News",
            published_at=datetime.utcnow() - timedelta(hours=i),
            embedding=embedding
        )

    # Get 3 most recent articles
    recent = crud.get_recent_articles(session=session, limit=3)

    assert len(recent) == 3
    # Should be sorted by ingested_at DESC (most recent first)
    # Since we created them in sequence, Article 4 should be first
    assert "Article 4" in recent[0].title


def test_get_recent_articles_with_source_filter(session: Session):
    """Test retrieving recent articles filtered by source."""
    embedding = np.random.rand(768).tolist()

    # Create articles from different sources
    crud.create_news_article(
        session=session,
        title="Article from DL News",
        url="https://example.com/dl-1",
        content="Content 1",
        source_name="DL News",
        published_at=datetime.utcnow(),
        embedding=embedding
    )

    crud.create_news_article(
        session=session,
        title="Article from The Defiant",
        url="https://example.com/defiant-1",
        content="Content 2",
        source_name="The Defiant",
        published_at=datetime.utcnow(),
        embedding=embedding
    )

    crud.create_news_article(
        session=session,
        title="Another from DL News",
        url="https://example.com/dl-2",
        content="Content 3",
        source_name="DL News",
        published_at=datetime.utcnow(),
        embedding=embedding
    )

    # Filter by source
    dl_articles = crud.get_recent_articles(
        session=session,
        source_name="DL News",
        limit=10
    )

    assert len(dl_articles) == 2
    assert all(article.source_name == "DL News" for article in dl_articles)


@pytest.mark.skip(reason="Requires PostgreSQL with pgvector extension")
def test_semantic_search():
    """Test semantic search with vector similarity.

    This test requires PostgreSQL with pgvector extension.
    It will be implemented in integration tests.
    """
    pass
