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
    source_id: int | None = None,
) -> Any:
    """Manually trigger news ingestion.

    Args:
        source_id: Optional source ID. If provided, ingests only that source.
                   If omitted, ingests all active sources.

    Returns:
        Success response with ingestion statistics

    Raises:
        HTTPException: 404 if source_id not found, 500 if ingestion fails
    """
    try:
        if source_id is not None:
            # Single source ingestion
            try:
                stats = service.ingest_source(source_id)
            except ValueError as ve:
                # Source not found
                raise HTTPException(status_code=404, detail=str(ve)) from ve

            session.commit()
            return {
                "status": "success",
                "message": f"Ingestion completed for source: {stats['source_name']}",
                "stats": stats,
            }
        else:
            # All sources ingestion
            stats = service.ingest_all_sources()
            session.commit()
            return {
                "status": "success",
                "message": "News ingestion completed for all sources",
                "stats": stats,
            }
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
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
