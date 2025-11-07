"""News feature database operations (repository pattern)."""

from datetime import datetime

from sqlmodel import Session, col, select

from app.core.config import settings
from app.models import NewsArticle


class NewsRepository:
    """Repository for news-related database operations."""

    def __init__(self, session: Session):
        """Initialize repository."""
        self.session = session

    # NewsSource operations (now config-based)
    def get_active_news_sources(self) -> list[dict[str, str]]:
        """Get all configured news sources from settings."""
        return settings.news_sources

    def get_source_by_name(self, source_name: str) -> dict[str, str] | None:
        """Get a news source by name.

        Args:
            source_name: The name of the source to retrieve

        Returns:
            Source dict if found, None otherwise
        """
        for source in settings.news_sources:
            if source["name"] == source_name:
                return source
        return None

    # NewsArticle operations
    def create_news_article(
        self,
        *,
        title: str,
        url: str,
        content: str,
        source_name: str,
        published_at: datetime | None,
        embedding: list[float],
    ) -> NewsArticle:
        """Create a new news article with embedding."""
        content_hash = NewsArticle.compute_content_hash(title, url)

        article = NewsArticle(
            content_hash=content_hash,
            title=title,
            url=url,
            content=content,
            source_name=source_name,
            published_at=published_at,
            embedding=embedding,
        )

        self.session.add(article)
        self.session.flush()  # Make ID available without committing
        self.session.refresh(article)
        return article

    def get_article_by_hash(self, content_hash: str) -> NewsArticle | None:
        """Get article by content hash."""
        statement = select(NewsArticle).where(NewsArticle.content_hash == content_hash)
        return self.session.exec(statement).first()

    def get_recent_articles(
        self, limit: int = 50, source_name: str | None = None
    ) -> list[NewsArticle]:
        """Get recent articles, optionally filtered by source."""
        statement = select(NewsArticle).order_by(col(NewsArticle.ingested_at).desc())

        if source_name:
            statement = statement.where(NewsArticle.source_name == source_name)

        statement = statement.limit(limit)

        return list(self.session.exec(statement).all())

    def semantic_search(
        self, query_embedding: list[float], limit: int = 5
    ) -> list[tuple[NewsArticle, float]]:
        """Perform semantic search using vector similarity.

        Returns list of (article, distance) tuples sorted by similarity.
        Lower distance = more similar.
        """
        # This requires PostgreSQL with pgvector extension
        # Using cosine distance operator
        statement = (
            select(
                NewsArticle,
                NewsArticle.embedding.cosine_distance(query_embedding).label(
                    "distance"
                ),
            )
            .order_by("distance")
            .limit(limit)
        )

        results = self.session.exec(statement).all()
        return [(article, distance) for article, distance in results]

    def delete_old_articles(self, cutoff_date: datetime) -> int:
        """Delete articles older than specified date."""
        from sqlmodel import delete

        statement = delete(NewsArticle).where(NewsArticle.ingested_at < cutoff_date)
        result = self.session.exec(statement)
        deleted_count = result.rowcount  # type: ignore

        return deleted_count
