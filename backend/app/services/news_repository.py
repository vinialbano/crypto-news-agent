"""News feature database operations (repository pattern)."""

from datetime import UTC, datetime

from sqlmodel import Session, col, select

from app.models import NewsArticle, NewsSource


class NewsRepository:
    """Repository for news-related database operations."""

    def __init__(self, session: Session):
        """Initialize repository."""
        self.session = session

    # NewsSource operations
    def create_news_source(
        self, *, name: str, rss_url: str, is_active: bool = True
    ) -> NewsSource:
        """Create a new news source."""
        source = NewsSource(name=name, rss_url=rss_url, is_active=is_active)
        self.session.add(source)
        self.session.flush()  # Make ID available without committing
        self.session.refresh(source)
        return source

    def get_active_news_sources(self) -> list[NewsSource]:
        """Get all active news sources."""
        statement = select(NewsSource).where(NewsSource.is_active == True)
        return list(self.session.exec(statement).all())

    def get_source_by_id(self, source_id: int) -> NewsSource | None:
        """Get a news source by ID.

        Args:
            source_id: The ID of the source to retrieve

        Returns:
            NewsSource if found, None otherwise
        """
        statement = select(NewsSource).where(NewsSource.id == source_id)
        return self.session.exec(statement).first()

    def update_ingestion_status(
        self,
        *,
        source_id: int,
        success: bool,
        error_message: str | None = None,
    ) -> None:
        """Update ingestion status for a news source."""
        statement = select(NewsSource).where(NewsSource.id == source_id)
        source = self.session.exec(statement).first()

        if source:
            if success:
                source.ingestion_count += 1
                source.last_ingestion_at = datetime.now(UTC)
                source.last_error = None
            else:
                source.last_error = error_message

            self.session.add(source)
            self.session.flush()  # Make changes visible for subsequent operations

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
