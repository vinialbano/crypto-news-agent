"""News feature database operations (repository pattern)."""
from datetime import datetime

from sqlmodel import Session, select, col

from app.features.news.models import NewsSource, NewsArticle


# NewsSource repository functions
def create_news_source(
    *, session: Session, name: str, rss_url: str, is_active: bool = True
) -> NewsSource:
    """Create a new news source."""
    source = NewsSource(name=name, rss_url=rss_url, is_active=is_active)
    session.add(source)
    session.commit()
    session.refresh(source)
    return source


def get_active_news_sources(session: Session) -> list[NewsSource]:
    """Get all active news sources."""
    statement = select(NewsSource).where(NewsSource.is_active == True)
    return list(session.exec(statement).all())


def update_ingestion_status(
    *,
    session: Session,
    source_id: int,
    success: bool,
    error_message: str | None = None,
) -> None:
    """Update ingestion status for a news source."""
    statement = select(NewsSource).where(NewsSource.id == source_id)
    source = session.exec(statement).first()

    if source:
        if success:
            source.ingestion_count += 1
            source.last_ingestion_at = datetime.utcnow()
            source.last_error = None
        else:
            source.last_error = error_message

        session.add(source)
        session.commit()


# NewsArticle repository functions
def create_news_article(
    *,
    session: Session,
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

    session.add(article)
    session.commit()
    session.refresh(article)
    return article


def get_article_by_hash(session: Session, content_hash: str) -> NewsArticle | None:
    """Get article by content hash."""
    statement = select(NewsArticle).where(NewsArticle.content_hash == content_hash)
    return session.exec(statement).first()


def get_recent_articles(
    session: Session, limit: int = 50, source_name: str | None = None
) -> list[NewsArticle]:
    """Get recent articles, optionally filtered by source."""
    statement = select(NewsArticle).order_by(col(NewsArticle.ingested_at).desc())

    if source_name:
        statement = statement.where(NewsArticle.source_name == source_name)

    statement = statement.limit(limit)

    return list(session.exec(statement).all())


def semantic_search(
    session: Session, query_embedding: list[float], limit: int = 5
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
            NewsArticle.embedding.cosine_distance(query_embedding).label("distance"),
        )
        .order_by("distance")
        .limit(limit)
    )

    results = session.exec(statement).all()
    return [(article, distance) for article, distance in results]
