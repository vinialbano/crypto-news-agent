import uuid
from typing import Any
from datetime import datetime

from sqlmodel import Session, select, col

from app.core.security import get_password_hash, verify_password
from app.models import (
    Item,
    ItemCreate,
    User,
    UserCreate,
    UserUpdate,
    NewsSource,
    NewsArticle,
)


def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    db_user = get_user_by_email(session=session, email=email)
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user


def create_item(*, session: Session, item_in: ItemCreate, owner_id: uuid.UUID) -> Item:
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


# NewsSource CRUD Operations
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


# NewsArticle CRUD Operations
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
    from sqlalchemy import func

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
