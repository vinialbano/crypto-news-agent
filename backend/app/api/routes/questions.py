"""Questions feature API router with WebSocket support."""

import asyncio
import json
import logging
from collections import defaultdict
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.config import settings
from app.shared.deps import ContentModerationDep, RAGServiceDep
from app.shared.exceptions import InvalidQuestionError

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


@router.websocket("/ws/ask")
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
