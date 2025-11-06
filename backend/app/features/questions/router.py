"""Questions feature API router with WebSocket support."""

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.shared.deps import RAGServiceDep

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/ask")
async def ask_question_websocket(
    websocket: WebSocket,
    rag_service: RAGServiceDep,
):
    """WebSocket endpoint for streaming question answering.

    Args:
        websocket: WebSocket connection
        rag_service: RAG service injected via dependency injection

    Protocol:
    1. Client sends: {"question": "What happened to Bitcoin today?"}
    2. Server streams:
       - {"type": "sources", "count": 3} - Number of articles used
       - {"type": "chunk", "content": "Bitcoin "} - Text chunks
       - {"type": "chunk", "content": "surged..."} - More chunks
       - {"type": "done"} - Streaming complete
       - {"type": "error", "content": "message"} - On error
    """
    await websocket.accept()
    logger.info("WebSocket connection established")

    try:
        while True:
            # Receive question from client
            data = await websocket.receive_text()
            message = json.loads(data)
            question = message.get("question", "").strip()

            if not question:
                await websocket.send_json(
                    {
                        "type": "error",
                        "content": "Question cannot be empty",
                    }
                )
                continue

            logger.info(f"Received question via WebSocket: {question[:100]}")

            # Stream answer back to client (repository is already injected in RAG service)
            async for message_chunk in rag_service.stream_answer(question):
                await websocket.send_json(message_chunk)

            logger.info("Answer streaming completed")

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON received: {e}")
        await websocket.send_json(
            {
                "type": "error",
                "content": "Invalid message format",
            }
        )
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
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
