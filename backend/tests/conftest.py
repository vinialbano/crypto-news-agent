"""Test configuration and fixtures."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.db import engine
from app.main import app
from app.shared.deps import get_embeddings_service_dep
from app.shared.embeddings import EmbeddingsService


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    """Initialize database for tests.

    Database schema is created with Alembic migrations.
    """
    with Session(engine) as session:
        yield session
        # Cleanup handled by test database


@pytest.fixture(scope="function")
def session() -> Generator[Session, None, None]:
    """Provide a database session for tests.

    Each test gets a fresh session with transaction rollback for isolation.
    """
    with Session(engine) as session:
        yield session
        session.rollback()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """Create test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def mock_embeddings_service() -> Generator[EmbeddingsService, None, None]:
    """Provide a mock embeddings service for WebSocket tests.

    This fixture mocks the async embedding methods to avoid calling real Ollama,
    which prevents event loop closure issues in sync TestClient WebSocket tests.
    """
    mock_service = MagicMock(spec=EmbeddingsService)

    # Create a fake embedding vector (768 dimensions for nomic-embed-text)
    fake_embedding = [0.1] * 768

    # Mock async methods
    mock_service.aembed_query = AsyncMock(return_value=fake_embedding)
    mock_service.aembed_documents = AsyncMock(return_value=[fake_embedding])

    # Mock sync methods (for completeness)
    mock_service.embed_query = MagicMock(return_value=fake_embedding)
    mock_service.embed_documents = MagicMock(return_value=[fake_embedding])

    # Override the FastAPI dependency
    app.dependency_overrides[get_embeddings_service_dep] = lambda: mock_service

    yield mock_service

    # Clean up dependency override
    app.dependency_overrides.pop(get_embeddings_service_dep, None)


def create_fake_embedding() -> list[float]:
    """Create a fake 768-dimensional embedding vector for tests.

    Returns a deterministic embedding vector for consistent test behavior.
    Real embeddings come from Ollama nomic-embed-text model.
    """
    return [0.1] * 768


@pytest.fixture
def create_article(session: Session):
    """Factory fixture to create test articles on-demand.

    Returns a function that creates articles with sensible defaults.
    Useful for tests that need one or more articles with specific properties.

    Example:
        def test_something(create_article):
            article1 = create_article(title="Bitcoin News")
            article2 = create_article(title="Ethereum Update", source_name="The Defiant")
    """
    from datetime import UTC, datetime

    from app.features.news.repository import NewsRepository

    def _create_article(
        title: str = "Test Bitcoin Article",
        url: str | None = None,
        content: str = (
            "Bitcoin has reached new heights with substantial market activity. "
            "Traders are closely monitoring the price movements as institutional "
            "investors continue to show strong interest in cryptocurrency markets. " * 5
        ),
        source_name: str = "DL News",
        published_at: datetime | None = None,
    ):
        if url is None:
            # Generate unique URL based on title hash
            url = f"https://example.com/article-{abs(hash(title)) % 100000}"
        if published_at is None:
            published_at = datetime.now(UTC)

        repo = NewsRepository(session)
        return repo.create_news_article(
            title=title,
            url=url,
            content=content,
            source_name=source_name,
            published_at=published_at,
            embedding=create_fake_embedding(),
        )

    return _create_article


@pytest.fixture
def seed_test_articles(session: Session, create_article):
    """Seed database with test articles for integration tests.

    Creates 5 diverse articles with different sources and content.
    Automatically commits to database for use in integration tests.

    Returns list of created NewsArticle instances.

    Note: Uses function scope so each test gets fresh articles.
    Session rollback at test end will clean up articles.
    """
    import random

    articles = []
    topics = [
        ("Bitcoin Reaches All-Time High", "Bitcoin price surge analysis"),
        ("Ethereum 2.0 Upgrade Complete", "Details on Ethereum upgrade"),
        ("DeFi Protocols See Record Growth", "DeFi market expansion report"),
        ("NFT Market Shows Strong Recovery", "NFT trading volume increase"),
        ("Crypto Regulation Updates", "New regulatory framework details"),
    ]

    # Add randomness to ensure unique content_hash across tests
    test_id = random.randint(1000, 9999)

    for i, (title, topic) in enumerate(topics):
        content = (
            f"{topic}. The cryptocurrency market continues to evolve with "
            f"significant developments across multiple sectors. Industry experts "
            f"are analyzing the long-term implications of these changes. "
            f"Test ID: {test_id}. " * 10
        )

        article = create_article(
            title=f"Test Article {test_id}-{i}: {title}",
            url=f"https://example.com/test-article-{test_id}-{i}",
            content=content,
            source_name="DL News" if i % 2 == 0 else "The Defiant",
        )
        articles.append(article)

    session.commit()
    return articles
