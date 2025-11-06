"""News feature database models."""
import hashlib
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlmodel import Column, Field, SQLModel


class NewsSource(SQLModel, table=True):
    """News source (RSS feed) model."""

    __tablename__ = "news_sources"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True, index=True)
    rss_url: str = Field(max_length=2048, unique=True)
    is_active: bool = Field(default=True, index=True)
    last_ingestion_at: datetime | None = None
    last_error: str | None = Field(default=None, max_length=1000)
    ingestion_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class NewsArticle(SQLModel, table=True):
    """News article with vector embedding for semantic search."""

    __tablename__ = "news_articles"

    id: int | None = Field(default=None, primary_key=True)
    content_hash: str = Field(max_length=64, unique=True, index=True)
    title: str = Field(max_length=500)
    url: str = Field(max_length=2048)
    content: str
    source_name: str = Field(max_length=100, index=True)
    published_at: datetime | None = None
    ingested_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    embedding: list[float] = Field(sa_column=Column(Vector(768)))

    @classmethod
    def compute_content_hash(cls, title: str, url: str) -> str:
        """Compute SHA-256 hash of title + URL for duplicate detection."""
        content = f"{title}|{url}"
        return hashlib.sha256(content.encode()).hexdigest()
