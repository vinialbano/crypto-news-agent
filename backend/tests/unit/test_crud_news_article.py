"""Unit tests for NewsArticle CRUD operations."""

from datetime import datetime, timedelta

import numpy as np
import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.features.news.repository import NewsRepository


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
    embedding = np.random.rand(768).tolist()
    repo = NewsRepository(session)

    article = repo.create_news_article(
        title="Bitcoin Surges to New High",
        url="https://example.com/bitcoin-surges",
        content="Bitcoin reached a new all-time high today, surpassing $100,000 for the first time in history.",
        source_name="DL News",
        published_at=datetime.utcnow(),
        embedding=embedding,
    )

    assert article.id is not None
    assert article.title == "Bitcoin Surges to New High"
    assert article.url == "https://example.com/bitcoin-surges"
    assert article.source_name == "DL News"
    assert article.content_hash is not None
    assert len(article.content_hash) == 64
    assert article.ingested_at is not None


def test_get_by_hash_existing(session: Session):
    embedding = np.random.rand(768).tolist()
    repo = NewsRepository(session)

    article = repo.create_news_article(
        title="Bitcoin Surges to New High",
        url="https://example.com/bitcoin-surges",
        content="Bitcoin reached a new all-time high today.",
        source_name="DL News",
        published_at=datetime.utcnow(),
        embedding=embedding,
    )

    found_article = repo.get_article_by_hash(content_hash=article.content_hash)

    assert found_article is not None
    assert found_article.id == article.id
    assert found_article.title == article.title


def test_get_by_hash_nonexistent(session: Session):
    repo = NewsRepository(session)
    found_article = repo.get_article_by_hash(content_hash="0" * 64)

    assert found_article is None


def test_duplicate_detection_same_title_and_url(session: Session):
    embedding = np.random.rand(768).tolist()
    repo = NewsRepository(session)

    repo.create_news_article(
        title="Bitcoin Surges to New High",
        url="https://example.com/bitcoin-surges",
        content="Content version 1",
        source_name="DL News",
        published_at=datetime.utcnow(),
        embedding=embedding,
    )

    with pytest.raises(Exception):
        repo.create_news_article(
            title="Bitcoin Surges to New High",
            url="https://example.com/bitcoin-surges",
            content="Content version 2",
            source_name="DL News",
            published_at=datetime.utcnow(),
            embedding=embedding,
        )


def test_get_recent_articles(session: Session):
    embedding = np.random.rand(768).tolist()
    repo = NewsRepository(session)

    for i in range(5):
        repo.create_news_article(
            title=f"Article {i}",
            url=f"https://example.com/article-{i}",
            content=f"Content for article {i}",
            source_name="DL News",
            published_at=datetime.utcnow() - timedelta(hours=i),
            embedding=embedding,
        )

    recent = repo.get_recent_articles(limit=3)

    assert len(recent) == 3
    assert "Article 4" in recent[0].title


def test_get_recent_articles_with_source_filter(session: Session):
    embedding = np.random.rand(768).tolist()
    repo = NewsRepository(session)

    repo.create_news_article(
        title="Article from DL News",
        url="https://example.com/dl-1",
        content="Content 1",
        source_name="DL News",
        published_at=datetime.utcnow(),
        embedding=embedding,
    )

    repo.create_news_article(
        title="Article from The Defiant",
        url="https://example.com/defiant-1",
        content="Content 2",
        source_name="The Defiant",
        published_at=datetime.utcnow(),
        embedding=embedding,
    )

    repo.create_news_article(
        title="Another from DL News",
        url="https://example.com/dl-2",
        content="Content 3",
        source_name="DL News",
        published_at=datetime.utcnow(),
        embedding=embedding,
    )

    dl_articles = repo.get_recent_articles(source_name="DL News", limit=10)

    assert len(dl_articles) == 2
    assert all(article.source_name == "DL News" for article in dl_articles)


@pytest.mark.skip(reason="Requires PostgreSQL with pgvector extension")
def test_semantic_search():
    """Test semantic search with vector similarity.

    This test requires PostgreSQL with pgvector extension.
    It will be implemented in integration tests.
    """
    pass
