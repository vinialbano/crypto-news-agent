"""News feature API schemas (request/response models)."""
from datetime import datetime

from sqlmodel import SQLModel


class NewsSourcePublic(SQLModel):
    """Public schema for news source API responses."""

    id: int
    name: str
    rss_url: str
    is_active: bool
    last_ingestion_at: datetime | None
    last_error: str | None
    ingestion_count: int
    created_at: datetime


class NewsArticlePublic(SQLModel):
    """Public schema for news article API responses."""

    id: int
    title: str
    url: str
    source_name: str
    published_at: datetime | None
    ingested_at: datetime
    # Note: embedding not exposed in public API
