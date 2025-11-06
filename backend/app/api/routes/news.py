"""News feature API router."""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.schemas.news import NewsListResponse
from app.shared.deps import IngestionServiceDep, NewsRepositoryDep, SessionDep

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=NewsListResponse)
def get_news_articles(
    *,
    repository: NewsRepositoryDep,
    limit: int = 50,
    source_name: str | None = None,
) -> Any:
    """Get recent news articles with optional source filtering."""
    articles = repository.get_recent_articles(limit=limit, source_name=source_name)

    return {"articles": articles, "count": len(articles)}


@router.post("/admin/ingest")
def trigger_manual_ingestion(
    service: IngestionServiceDep,
    session: SessionDep,
) -> Any:
    """Manually trigger news ingestion."""
    try:
        stats = service.run_ingestion()
        session.commit()  # Commit all changes from the ingestion
        return {
            "status": "success",
            "message": "News ingestion completed",
            "stats": stats,
        }
    except Exception as e:
        session.rollback()  # Rollback on error
        logger.error(f"Manual ingestion failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Ingestion failed: {str(e)}"
        ) from e


@router.get("/sources")
def get_news_sources(
    *,
    repository: NewsRepositoryDep,
) -> Any:
    """Get all active news sources."""
    sources = repository.get_active_news_sources()
    return {"sources": sources, "count": len(sources)}
