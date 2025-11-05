# WebSocket Protocol: Question Answering Stream

**Endpoint**: `ws://localhost:8000/ws/ask`
**Purpose**: Stream LLM-generated answers to user questions about cryptocurrency news in real-time

---

## Connection Lifecycle

### 1. Connection Establishment

**Client Initiates**:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/ask')

ws.onopen = () => {
  console.log('WebSocket connected')
  // Connection ready to send questions
}
```

**Server Accepts**:
- Server accepts WebSocket connection
- No authentication required (for MVP; add auth in future)
- Connection remains open until client closes or error occurs

---

### 2. Sending Questions

**Client → Server**:
```json
{
  "question": "What happened to Bitcoin today?"
}
```

**Message Format (Client to Server)**:
```typescript
interface QuestionMessage {
  question: string // User's natural language question (1-1000 chars)
}
```

**Validation**:
- `question` must be non-empty string
- Maximum 1000 characters
- Server responds with error if invalid

---

### 3. Receiving Answers (Streaming)

Server sends multiple messages in sequence to stream the answer word-by-word.

#### 3.1 Source Metadata (First Message)

Sent before streaming begins to indicate how many news articles were used as context.

**Server → Client**:
```json
{
  "type": "sources",
  "content": "",
  "metadata": {
    "source_count": 3,
    "distance_threshold": 0.5
  }
}
```

#### 3.2 Text Chunks (Streaming)

Sent continuously as LLM generates the answer. Each chunk contains a portion of the response.

**Server → Client** (multiple messages):
```json
{"type": "chunk", "content": "Bitcoin "}
{"type": "chunk", "content": "surged "}
{"type": "chunk", "content": "to "}
{"type": "chunk", "content": "a "}
{"type": "chunk", "content": "new "}
{"type": "chunk", "content": "all-time "}
{"type": "chunk", "content": "high "}
{"type": "chunk", "content": "today. "}
```

#### 3.3 Completion Signal

Sent when LLM finishes generating the answer.

**Server → Client**:
```json
{
  "type": "done",
  "content": ""
}
```

---

### 4. Error Handling

#### 4.1 Insufficient Information

If semantic search finds no relevant articles (distance > threshold), server sends error instead of hallucinating.

**Server → Client**:
```json
{
  "type": "error",
  "content": "I don't have enough information about that topic in recent news.",
  "metadata": {
    "min_distance": 0.72,
    "threshold": 0.5
  }
}
```

#### 4.2 LLM Unavailable

If Ollama service is down or unresponsive:

**Server → Client**:
```json
{
  "type": "error",
  "content": "The answer generation service is temporarily unavailable. Please try again later."
}
```

#### 4.3 Invalid Question Format

If client sends malformed JSON or violates validation:

**Server → Client**:
```json
{
  "type": "error",
  "content": "Invalid question format. Question must be 1-1000 characters."
}
```

---

### 5. Connection Closure

#### Normal Closure

**Client Closes**:
```javascript
ws.close(1000, "User navigated away")
```

**Server Closes** (after sending 'done'):
- Server MAY close connection after sending 'done' message
- OR keep connection open for next question (depends on implementation)

#### Abnormal Closure

**Network Error**:
```javascript
ws.onerror = (error) => {
  console.error('WebSocket error:', error)
}

ws.onclose = (event) => {
  if (event.code !== 1000) {
    console.error('Abnormal closure:', event.code, event.reason)
  }
}
```

**Server Timeout**:
- If client doesn't send question within 60 seconds of connection, server MAY close
- If answer generation exceeds 30 seconds, server sends error and closes

---

## Complete Message Type Definitions

### TypeScript (Client-Side)

```typescript
import { z } from 'zod'

// Client → Server
export const QuestionMessageSchema = z.object({
  question: z.string().trim().min(1).max(1000)
})

// Server → Client
export const StreamMessageSchema = z.object({
  type: z.enum(['sources', 'chunk', 'done', 'error']),
  content: z.string(),
  metadata: z.object({
    source_count: z.number().int().nonnegative().optional(),
    distance_threshold: z.number().optional(),
    min_distance: z.number().optional(),
  }).optional()
})

export type QuestionMessage = z.infer<typeof QuestionMessageSchema>
export type StreamMessage = z.infer<typeof StreamMessageSchema>
```

### Python (Server-Side)

```python
from pydantic import BaseModel, Field
from typing import Literal, Optional

# Client → Server
class QuestionMessage(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)

# Server → Client
class StreamMetadata(BaseModel):
    source_count: Optional[int] = None
    distance_threshold: Optional[float] = None
    min_distance: Optional[float] = None

class StreamMessage(BaseModel):
    type: Literal["sources", "chunk", "done", "error"]
    content: str
    metadata: Optional[StreamMetadata] = None
```

---

## Example Client Implementation (React)

```typescript
import { useEffect, useState } from 'react'
import { StreamMessageSchema, type StreamMessage } from './types'

export function useQuestionStream(question: string | null) {
  const [chunks, setChunks] = useState<string[]>([])
  const [sourceCount, setSourceCount] = useState<number | null>(null)
  const [status, setStatus] = useState<'idle' | 'streaming' | 'complete' | 'error'>('idle')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  useEffect(() => {
    if (!question) return

    const ws = new WebSocket('ws://localhost:8000/ws/ask')

    ws.onopen = () => {
      setStatus('streaming')
      setChunks([])
      setSourceCount(null)
      setErrorMessage(null)
      ws.send(JSON.stringify({ question }))
    }

    ws.onmessage = (event) => {
      try {
        const message: StreamMessage = StreamMessageSchema.parse(JSON.parse(event.data))

        switch (message.type) {
          case 'sources':
            setSourceCount(message.metadata?.source_count ?? null)
            break
          case 'chunk':
            setChunks(prev => [...prev, message.content])
            break
          case 'done':
            setStatus('complete')
            ws.close()
            break
          case 'error':
            setStatus('error')
            setErrorMessage(message.content)
            ws.close()
            break
        }
      } catch (err) {
        console.error('Invalid message format:', err)
        setStatus('error')
        setErrorMessage('Received invalid message from server')
      }
    }

    ws.onerror = () => {
      setStatus('error')
      setErrorMessage('Connection error occurred')
    }

    return () => {
      ws.close()
    }
  }, [question])

  return {
    chunks,
    fullText: chunks.join(''),
    sourceCount,
    status,
    errorMessage
  }
}
```

---

## Example Server Implementation (FastAPI)

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from langchain_ollama import ChatOllama
import json
import logging

app = FastAPI()
logger = logging.getLogger(__name__)

@app.websocket("/ws/ask")
async def ask_question(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection established")

    try:
        # Receive question
        data = await websocket.receive_text()
        question_msg = QuestionMessage.model_validate_json(data)
        question = question_msg.question

        logger.info(f"Received question: {question[:50]}...")

        # Semantic search for relevant articles
        results = await semantic_search(question)

        # Check if sufficient context exists
        if not results or results[0]['distance'] > 0.5:
            await websocket.send_text(json.dumps({
                "type": "error",
                "content": "I don't have enough information about that topic in recent news.",
                "metadata": {
                    "min_distance": results[0]['distance'] if results else None,
                    "threshold": 0.5
                }
            }))
            await websocket.close()
            return

        # Send source metadata
        await websocket.send_text(json.dumps({
            "type": "sources",
            "content": "",
            "metadata": {
                "source_count": len(results),
                "distance_threshold": 0.5
            }
        }))

        # Build context from articles
        context = "\n\n".join([doc['content'] for doc in results])

        # Stream LLM response
        chat = ChatOllama(model="llama3.1:8b", temperature=0)
        prompt = build_rag_prompt(context, question)

        async for chunk in chat.astream(prompt):
            await websocket.send_text(json.dumps({
                "type": "chunk",
                "content": chunk.content
            }))

        # Send completion signal
        await websocket.send_text(json.dumps({
            "type": "done",
            "content": ""
        }))

    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Error processing question: {e}", exc_info=True)
        await websocket.send_text(json.dumps({
            "type": "error",
            "content": "An error occurred while processing your question."
        }))
    finally:
        await websocket.close()
```

---

## Performance Considerations

### Server-Side
- **Timeout**: Implement 30-second timeout for LLM response generation
- **Rate Limiting**: Limit concurrent WebSocket connections per IP (100 max)
- **Backpressure**: If client is slow to receive, buffer up to 100 chunks then close connection

### Client-Side
- **Reconnection**: Implement exponential backoff if connection fails
- **Message Queue**: Buffer incoming chunks in case of React re-render delays
- **Cleanup**: Always close WebSocket in useEffect cleanup function

---

## Security Notes

### Current (MVP)
- ❌ No authentication required
- ❌ No rate limiting per user
- ⚠️ Input validation only (question length)

### Future Improvements
- ✅ Require JWT token in WebSocket connection URL or headers
- ✅ Rate limit per authenticated user (10 questions per minute)
- ✅ Sanitize question input for SQL injection / XSS attempts
- ✅ Monitor for abusive patterns (repeated identical questions)

---

## Testing Scenarios

### Happy Path
1. Client connects to `/ws/ask`
2. Client sends valid question
3. Server sends 'sources' message
4. Server streams 5-10 'chunk' messages
5. Server sends 'done' message
6. Connection closes gracefully

### Error Cases
1. **Invalid Question**: Send empty string → Expect 'error' message
2. **No Context**: Send question about unrelated topic → Expect 'error' with "insufficient information"
3. **Ollama Down**: Stop Ollama service → Expect 'error' with "service unavailable"
4. **Client Disconnect**: Close connection mid-stream → Server logs disconnect, no crash
5. **Timeout**: Mock slow LLM → Expect 'error' after 30 seconds

---

**WebSocket Protocol Phase Status**: ✅ COMPLETE

Complete protocol specification with message formats, error handling, client/server examples, and testing scenarios.
