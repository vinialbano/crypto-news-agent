"""API routes for the application."""

import asyncio
import json
import logging
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from app.core.config import settings
from app.schemas import NewsListResponse
from app.deps import (
    ContentModerationDep,
    IngestionServiceDep,
    NewsRepositoryDep,
    RAGServiceDep,
    SessionDep,
)
from app.exceptions import InvalidQuestionError

logger = logging.getLogger(__name__)

router = APIRouter()

# Rate limiting: Track question count per client (in-memory)
# Key: client_id (IP or connection ID), Value: list of timestamps
_rate_limit_tracker: dict[str, list[datetime]] = defaultdict(list)


def _check_rate_limit(client_id: str) -> bool:
    """Check if client has exceeded rate limit.

    Args:
        client_id: Unique client identifier

    Returns:
        True if within rate limit, False if exceeded
    """
    now = datetime.now(UTC)
    cutoff = now - timedelta(minutes=1)

    # Clean up old timestamps
    _rate_limit_tracker[client_id] = [
        ts for ts in _rate_limit_tracker[client_id] if ts > cutoff
    ]

    # Check rate limit
    if len(_rate_limit_tracker[client_id]) >= settings.WEBSOCKET_MAX_QUESTIONS_PER_MINUTE:
        return False

    # Add current timestamp
    _rate_limit_tracker[client_id].append(now)
    return True


# News routes
@router.get("/news/", response_model=NewsListResponse, tags=["news"])
def get_news_articles(
    *,
    repository: NewsRepositoryDep,
    limit: int = 50,
    source_name: str | None = None,
) -> Any:
    """Get recent news articles with optional source filtering."""
    articles = repository.get_recent_articles(limit=limit, source_name=source_name)

    return {"articles": articles, "count": len(articles)}


@router.post("/news/ingest/", tags=["news"])
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


@router.get("/news/sources", tags=["news"])
def get_news_sources(
    *,
    repository: NewsRepositoryDep,
) -> Any:
    """Get all active news sources."""
    sources = repository.get_active_news_sources()
    return {"sources": sources, "count": len(sources)}


# Questions route (WebSocket)
@router.websocket("/ask")
async def ask_question_websocket(
    websocket: WebSocket,
    rag_service: RAGServiceDep,
    content_moderation: ContentModerationDep,
):
    """WebSocket endpoint for streaming question answering.

    Args:
        websocket: WebSocket connection
        rag_service: RAG service injected via dependency injection
        content_moderation: Content moderation service for input validation

    Protocol:
    1. Client sends: {"question": "What happened to Bitcoin today?"}
    2. Server streams:
       - {"type": "sources", "count": 3} - Number of articles used
       - {"type": "chunk", "content": "Bitcoin "} - Text chunks
       - {"type": "chunk", "content": "surged..."} - More chunks
       - {"type": "done"} - Streaming complete
       - {"type": "error", "content": "message"} - On error

    Security features (in order):
    - Rate limiting: Max questions per minute per client (checked first)
    - Content moderation: Filters profanity, prompt injection, spam
    - Connection timeout: Auto-disconnect after configured timeout
    """
    await websocket.accept()

    # Generate client ID from websocket client (use IP if available)
    client_id = f"{websocket.client.host}:{websocket.client.port}" if websocket.client else id(websocket)
    logger.info(f"WebSocket connection established: {client_id}")

    try:
        # Set connection timeout
        async with asyncio.timeout(settings.WEBSOCKET_CONNECTION_TIMEOUT_SECONDS):
            while True:
                # Receive question from client
                data = await websocket.receive_text()
                message = json.loads(data)
                question = message.get("question", "").strip()

                # Check rate limit FIRST (before any processing)
                # This prevents abuse via content validation probing
                if not _check_rate_limit(client_id):
                    logger.warning(f"Rate limit exceeded for client: {client_id}")
                    await websocket.send_json(
                        {
                            "type": "error",
                            "content": "Rate limit exceeded. Please wait before sending more questions.",
                        }
                    )
                    continue

                # Basic validation (empty check)
                if not question:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "content": "Question cannot be empty",
                        }
                    )
                    continue

                # Content moderation (after rate limit)
                try:
                    content_moderation.validate_or_raise(question)
                except InvalidQuestionError as e:
                    logger.warning(
                        f"Content moderation rejected question from {client_id}: {e}"
                    )
                    await websocket.send_json(
                        {
                            "type": "error",
                            "content": str(e),
                        }
                    )
                    continue

                logger.info(f"Received question via WebSocket: {question[:100]}")

                # Stream answer back to client (repository is already injected in RAG service)
                async for message_chunk in rag_service.stream_answer(question):
                    await websocket.send_json(message_chunk)

                logger.info("Answer streaming completed")

    except TimeoutError:
        logger.warning(f"WebSocket connection timeout for client: {client_id}")
        try:
            await websocket.send_json(
                {
                    "type": "error",
                    "content": "Connection timeout. Please reconnect.",
                }
            )
            await websocket.close()
        except:
            pass
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected: {client_id}")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON received from {client_id}: {e}")
        try:
            await websocket.send_json(
                {
                    "type": "error",
                    "content": "Invalid message format",
                }
            )
        except:
            pass
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}", exc_info=True)
        try:
            await websocket.send_json(
                {
                    "type": "error",
                    "content": f"Server error: {str(e)}",
                }
            )
        except:
            # Connection might be closed already
            pass
    finally:
        # Clean up rate limit tracker for this client
        if client_id in _rate_limit_tracker:
            del _rate_limit_tracker[client_id]
        logger.info(f"WebSocket connection closed: {client_id}")
