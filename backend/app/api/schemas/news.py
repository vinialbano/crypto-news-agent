"""News API response schemas (pure Pydantic models for HTTP layer)."""

from datetime import datetime

from pydantic import BaseModel


class NewsSourcePublic(BaseModel):
    """Public schema for news source API responses."""

    id: int
    name: str
    rss_url: str
    is_active: bool
    last_ingestion_at: datetime | None
    last_error: str | None
    ingestion_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class NewsArticlePublic(BaseModel):
    """Public schema for news article API responses."""

    id: int
    title: str
    url: str
    source_name: str
    published_at: datetime | None
    ingested_at: datetime
    content: str  # Full article content for display
    # Note: embedding not exposed in public API

    model_config = {"from_attributes": True}


class NewsListResponse(BaseModel):
    """Response model for news article list endpoint."""

    articles: list[NewsArticlePublic]
    count: int
