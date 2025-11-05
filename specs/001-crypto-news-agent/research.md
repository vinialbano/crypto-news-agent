# Research: Crypto News Agent

**Feature**: 001-crypto-news-agent
**Date**: 2025-11-05
**Phase**: 0 (Outline & Research)

This document consolidates research findings for all technical decisions required to implement the Crypto News Agent. All research was conducted using Context7 MCP to fetch current official documentation.

---

## 1. FastAPI WebSocket Implementation

### Decision
Use FastAPI's native WebSocket support with async/await patterns for real-time streaming of LLM responses.

### Rationale
- **Native Integration**: FastAPI provides first-class WebSocket support via `@app.websocket()` decorator
- **Async Streaming**: `websocket.send_text()` works seamlessly with async generators from LangChain
- **Dependency Injection**: Can use FastAPI `Depends()` for authentication, DB sessions even in WebSocket routes
- **Exception Handling**: `WebSocketDisconnect` exception makes client disconnection handling explicit

### Implementation Pattern (from Context7 FastAPI docs)
```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

@app.websocket("/ws/ask")
async def ask_question(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            question = await websocket.receive_text()
            # Stream LLM response word-by-word
            async for chunk in llm_service.stream_answer(question):
                await websocket.send_text(chunk)
    except WebSocketDisconnect:
        logger.info("Client disconnected")
```

### Alternatives Considered
- **Server-Sent Events (SSE)**: Simpler but unidirectional; WebSocket allows future interactivity
- **HTTP Streaming with chunked encoding**: Less browser support, harder to detect disconnects

---

## 2. LangChain for RSS Processing and RAG

### Decision
Use `langchain-community` for RSS/web loaders, `langchain-ollama` for embeddings/chat, and build custom RAG chain for question answering.

### Rationale
- **Document Loaders**: `WebBaseLoader` can fetch RSS feeds and parse HTML content
- **Ollama Integration**: `langchain-ollama` provides `ChatOllama` and `OllamaEmbeddings` with streaming support
- **RAG Workflow**: LangChain's LCEL (LangChain Expression Language) allows composing retrieval → context formatting → LLM invocation
- **Streaming Support**: `ChatOllama.stream()` yields `AIMessageChunk` objects for word-by-word output

### Implementation Pattern (from Context7 LangChain docs)
```python
from langchain_community.document_loaders import WebBaseLoader
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# Load RSS feed
loader = WebBaseLoader("https://www.dlnews.com/arc/outboundfeeds/rss/")
documents = loader.load()

# Generate embeddings
embeddings = OllamaEmbeddings(model="nomic-embed-text")

# RAG chain with streaming
chat = ChatOllama(model="llama3.1:8b", temperature=0)

prompt = ChatPromptTemplate.from_template(
    """Answer based on context:

Context: {context}

Question: {question}"""
)

async def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | chat
    | StrOutputParser()
)

# Stream response
async for chunk in chain.astream("What happened to Bitcoin?"):
    print(chunk, end="", flush=True)
```

### Alternatives Considered
- **LlamaIndex**: More opinionated, less flexibility for custom workflows
- **Custom RAG from scratch**: Reinventing wheel, no streaming primitives

---

## 3. pgvector for Semantic Search

### Decision
Use PostgreSQL with pgvector extension and `pgvector-python` package via SQLAlchemy integration for vector storage and similarity search.

### Rationale
- **Existing Infrastructure**: Project already uses PostgreSQL; no new database needed
- **SQLAlchemy Integration**: `pgvector.sqlalchemy` provides Vector column type with distance functions
- **Performance**: HNSW and IVFFlat indexes support sub-100ms searches on 1M+ vectors
- **Semantic Search Methods**: Supports L2 distance, cosine similarity, max inner product

### Implementation Pattern (from Context7 pgvector-python docs)
```python
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase
from pgvector.sqlalchemy import Vector

class Base(DeclarativeBase):
    pass

class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True)
    title = Column(String(500))
    content = Column(Text)
    embedding = Column(Vector(768))  # nomic-embed-text dimension

# Semantic search with cosine distance
from sqlalchemy import select

query_embedding = embeddings.embed_query("Bitcoin price surge")

results = session.scalars(
    select(NewsArticle)
    .order_by(NewsArticle.embedding.cosine_distance(query_embedding))
    .limit(5)
).all()

# Create HNSW index for fast search
# In Alembic migration:
# op.execute("CREATE INDEX ON news_articles USING hnsw (embedding vector_cosine_ops)")
```

### Alternatives Considered
- **Pinecone/Weaviate**: Managed vector DBs, but adds infrastructure complexity and cost
- **Chroma/FAISS**: Good for prototyping but less production-ready than PostgreSQL

---

## 4. Ollama for Local LLM Inference

### Decision
Use Ollama as LLM provider with `llama3.1:8b` for chat and `nomic-embed-text` for embeddings, integrated via `langchain-ollama`.

### Rationale
- **Local Deployment**: Runs on-premise, no API keys or rate limits
- **LangChain Integration**: `langchain-ollama.ChatOllama` provides streaming interface
- **Model Selection**: llama3.1:8b balances quality and speed; nomic-embed-text optimized for retrieval
- **Docker Compatibility**: Ollama runs in Docker container for consistent deployment

### Implementation Pattern (from Context7 Ollama/LangChain docs)
```python
from langchain_ollama import ChatOllama, OllamaEmbeddings

# Chat model with streaming
chat = ChatOllama(
    model="llama3.1:8b",
    temperature=0,
    base_url="http://ollama:11434"  # Docker service name
)

# Embeddings for semantic search
embeddings = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url="http://ollama:11434"
)

# Stream responses
async for chunk in chat.astream("Explain cryptocurrency"):
    print(chunk.content, end="", flush=True)

# Generate embeddings
text_embedding = embeddings.embed_query("Bitcoin whitepaper")
# Returns list of 768 floats
```

### Alternatives Considered
- **OpenAI API**: Requires API keys, costs money, external dependency
- **HuggingFace Transformers**: More complex setup, no built-in streaming

---

## 5. TanStack Query for WebSocket State Management

### Decision
Build custom WebSocket hook integrated with TanStack Query for managing connection state, message history, and reactivity.

### Rationale
- **Not Native Support**: TanStack Query doesn't natively support WebSockets, but provides primitives for custom implementations
- **State Management**: `useQuery` can track WebSocket connection state and message accumulation
- **React Integration**: Automatic re-renders when new chunks arrive
- **Error Handling**: Built-in error boundaries and retry logic

### Implementation Pattern (adapted from TanStack Query patterns)
```typescript
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'

interface StreamMessage {
  type: 'chunk' | 'done' | 'error'
  content: string
}

function useWebSocketQuery(question: string | null) {
  const [messages, setMessages] = useState<string[]>([])
  const [isStreaming, setIsStreaming] = useState(false)

  useEffect(() => {
    if (!question) return

    const ws = new WebSocket('ws://localhost:8000/ws/ask')

    ws.onopen = () => {
      setIsStreaming(true)
      ws.send(question)
    }

    ws.onmessage = (event) => {
      const msg: StreamMessage = JSON.parse(event.data)

      if (msg.type === 'chunk') {
        setMessages(prev => [...prev, msg.content])
      } else if (msg.type === 'done') {
        setIsStreaming(false)
        ws.close()
      }
    }

    ws.onerror = () => {
      setIsStreaming(false)
    }

    return () => {
      ws.close()
    }
  }, [question])

  return { messages, isStreaming, fullText: messages.join('') }
}
```

### Alternatives Considered
- **React Query + external WS library**: More complex, duplication of state
- **Plain useState**: No built-in error handling or dev tools

---

## 6. RSS Feed Parsing

### Decision
Use LangChain's `RSSFeedLoader` to fetch RSS feeds, automatically extract individual articles, and parse content with metadata.

### Rationale
- **Purpose-Built for RSS**: Specifically designed for RSS/Atom feed parsing (unlike generic HTML loaders)
- **Automatic Article Extraction**: Uses `feedparser` + `newspaper3k` to extract individual articles as separate documents
- **Rich Metadata**: Automatically extracts title, author, publication date, keywords, summary
- **Error Resilience**: `continue_on_failure=True` handles individual feed/article failures gracefully
- **Multi-Feed Support**: Process multiple RSS sources in one call
- **Document Format**: Returns `Document` objects compatible with LangChain embeddings pipeline
- **OPML Support**: Can import curated feed lists from Feedly exports (optional)
- **Progress Tracking**: Built-in progress bar for long operations

### Implementation Pattern (from LangChain documentation)
```python
from langchain_community.document_loaders import RSSFeedLoader
from datetime import datetime, timedelta

# Define crypto news RSS feeds
CRYPTO_RSS_FEEDS = [
    "https://www.dlnews.com/arc/outboundfeeds/rss/",
    "https://thedefiant.io/api/feed",
    "https://cointelegraph.com/rss"
]

# Load articles from all feeds
loader = RSSFeedLoader(
    urls=CRYPTO_RSS_FEEDS,
    continue_on_failure=True,  # Don't crash on individual feed errors
    show_progress_bar=True,    # Display progress
    nlp=True                   # Enable keyword extraction and summarization
)

documents = loader.load()
print(f"Loaded {len(documents)} articles")

# Each document has rich metadata
for doc in documents:
    article = {
        "title": doc.metadata.get("title", "Untitled"),
        "url": doc.metadata.get("link"),
        "content": doc.page_content,
        "source_name": extract_source_from_feed(doc.metadata.get("feed")),
        "published_at": doc.metadata.get("publish_date"),
        "authors": doc.metadata.get("authors", []),
        "keywords": doc.metadata.get("keywords", []),  # If nlp=True
        "summary": doc.metadata.get("summary", ""),    # If nlp=True
        "ingested_at": datetime.utcnow()
    }
    # Store in database with embedding

# Filter recent articles programmatically
def filter_recent(docs, days=7):
    cutoff = datetime.now() - timedelta(days=days)
    return [
        doc for doc in docs
        if doc.metadata.get("publish_date") and
           parse_date(doc.metadata["publish_date"]) >= cutoff
    ]

recent_articles = filter_recent(documents, days=7)
```

### Metadata Extracted by RSSFeedLoader

| Field | Description | Example |
|-------|-------------|---------|
| `title` | Article headline | "Bitcoin Surges Past $50K" |
| `link` | Original article URL | "https://..." |
| `authors` | Article authors | `["John Doe"]` |
| `language` | Content language | `"en"` |
| `description` | Meta description/excerpt | "Bitcoin reached new highs..." |
| `publish_date` | Publication timestamp | "2025-01-15 14:30:00" |
| `feed` | Source RSS feed URL | "https://example.com/rss" |
| `keywords` | Extracted key terms (if nlp=True) | `["Bitcoin", "crypto"]` |
| `summary` | AI-generated summary (if nlp=True) | "Bitcoin prices surged..." |

### Advantages Over WebBaseLoader

**RSSFeedLoader:**
- ✅ Designed specifically for RSS/Atom feeds
- ✅ Automatically parses feed XML structure with `feedparser`
- ✅ Extracts each article as separate document (not entire feed as one doc)
- ✅ Rich metadata extraction (title, author, date, keywords)
- ✅ Error handling per feed/article (`continue_on_failure`)
- ✅ Progress tracking support
- ✅ OPML import support

**WebBaseLoader:**
- ❌ Not designed for RSS feeds (generic HTML parser)
- ❌ Requires manual RSS XML parsing
- ❌ Returns entire feed as single document
- ❌ No automatic article extraction
- ❌ Minimal metadata extraction

### Dependencies Required
```bash
pip install feedparser newspaper3k
pip install listparser  # Optional: for OPML support
```

### Best Practices
1. **Always enable error handling**: `continue_on_failure=True`
2. **Show progress for user feedback**: `show_progress_bar=True`
3. **Filter by date after loading**: Don't rely solely on RSS feed limits
4. **Handle missing metadata gracefully**: Use `.get()` with defaults
5. **Use lazy loading for large feeds**: Memory-efficient processing
6. **Cache results**: Avoid re-fetching unchanged articles

### Known Limitations
- **newspaper3k failures**: Some sites may block or have paywalls (handled by `continue_on_failure`)
- **Publication date reliability**: May be empty/unreliable for some feeds (filter programmatically)
- **Performance**: Slower than raw HTML fetching (but extracts full article content)

### Alternatives Considered
- **WebBaseLoader**: Generic HTML parser, not RSS-specific, no article extraction
- **feedparser + custom code**: Lower-level, requires manual Document conversion
- **Scrapy**: Overkill for simple RSS parsing, steeper learning curve

---

## 7. Scheduled News Ingestion

### Decision
Use APScheduler with BackgroundScheduler for periodic RSS feed ingestion every 15-30 minutes.

### Rationale
- **Async Support**: APScheduler supports async jobs compatible with FastAPI
- **Flexible Scheduling**: Cron-like or interval-based scheduling
- **Error Resilience**: Jobs can fail without crashing scheduler
- **Lightweight**: No external dependencies like Celery + Redis

### Implementation Pattern
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager

scheduler = AsyncIOScheduler()

async def ingest_news():
    """Fetch and store news from all sources"""
    logger.info("Starting news ingestion")
    # Fetch RSS, generate embeddings, store in DB

scheduler.add_job(ingest_news, "interval", minutes=30)

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)
```

### Alternatives Considered
- **Celery + Redis**: Too heavy for simple periodic task
- **Cron jobs**: External to app, harder to manage dependencies

---

## 8. Duplicate Detection

### Decision
Use content hash (SHA-256 of title + URL) as uniqueness constraint in database to prevent duplicate articles.

### Rationale
- **Database-Level Enforcement**: UNIQUE constraint prevents duplicates automatically
- **Deterministic**: Same article always produces same hash
- **Fast Lookup**: Indexed hash column enables quick duplicate check

### Implementation Pattern
```python
import hashlib

def compute_content_hash(title: str, url: str) -> str:
    content = f"{title}|{url}"
    return hashlib.sha256(content.encode()).hexdigest()

class NewsArticle(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    content_hash: str = Field(unique=True, index=True)
    title: str
    url: str

# Before insert:
article_hash = compute_content_hash(title, url)
# Try to insert; if hash exists, DB raises IntegrityError (handle gracefully)
```

### Alternatives Considered
- **URL-only uniqueness**: Same article may have different URLs
- **Manual duplicate checks**: Slower, race condition prone

---

## 9. Error Messages for No Results

### Decision
Implement semantic check in RAG workflow: if top search result has cosine distance > 0.5, return "insufficient information" message instead of hallucinating.

### Rationale
- **Prevents Hallucination**: LLM won't make up answers when no relevant context exists
- **User Transparency**: Clear message explains limitation
- **Configurable Threshold**: Can tune based on embedding model characteristics

### Implementation Pattern
```python
# In RAG service
results_with_scores = session.execute(
    select(
        NewsArticle,
        NewsArticle.embedding.cosine_distance(query_embedding).label('distance')
    ).order_by('distance').limit(5)
).all()

if not results_with_scores or results_with_scores[0].distance > 0.5:
    return {
        "type": "error",
        "message": "I don't have enough information about that topic in recent news."
    }
```

### Alternatives Considered
- **Always answer**: Risks hallucination
- **Hard keyword matching**: Misses semantic similarity

---

## 10. Contract Validation with Zod

### Decision
Use Zod schemas on frontend to validate WebSocket messages and API responses match expected structure.

### Rationale
- **Runtime Validation**: Catches API contract violations at runtime
- **TypeScript Integration**: Generates types from schemas automatically
- **Error Messages**: Descriptive validation errors for debugging

### Implementation Pattern
```typescript
import { z } from 'zod'

const StreamMessageSchema = z.object({
  type: z.enum(['chunk', 'done', 'error']),
  content: z.string(),
  metadata: z.object({
    source_count: z.number().optional()
  }).optional()
})

type StreamMessage = z.infer<typeof StreamMessageSchema>

// In WebSocket handler
ws.onmessage = (event) => {
  try {
    const parsed = StreamMessageSchema.parse(JSON.parse(event.data))
    // Use safely typed `parsed` object
  } catch (err) {
    console.error("Invalid message format:", err)
  }
}
```

### Alternatives Considered
- **Plain TypeScript types**: No runtime validation
- **JSON Schema**: More verbose, less TypeScript integration

---

---

## 11. Shadcn UI for Component Library

### Decision
Use Shadcn UI (copy-paste component system built on Radix UI + Tailwind CSS) instead of runtime component libraries like Chakra UI.

### Rationale
- **Copy-Paste Approach**: Components are copied into your codebase, giving full control over customization
- **No Runtime Overhead**: No provider, no theme context, no runtime JS for styling
- **Tailwind CSS Integration**: Uses utility-first CSS, excellent performance and DX
- **Accessibility Built-in**: Built on Radix UI primitives (WAI-ARIA compliant)
- **Type-Safe**: Full TypeScript support, direct code editing
- **Minimal Bundle Size**: Only includes components you actually use
- **Customization**: Edit component code directly rather than fighting with theme overrides

### Implementation Pattern (Shadcn UI CLI)
```bash
# Initialize Shadcn UI in your project
npx shadcn@latest init

# Select options:
# - TypeScript: yes
# - Style: Default
# - Color: Slate
# - CSS variables: yes
# - Tailwind config: tailwind.config.js
# - Components path: @/components/ui
# - Utils path: @/lib/utils

# Add components as needed
npx shadcn@latest add button
npx shadcn@latest add input
npx shadcn@latest add card
npx shadcn@latest add dialog
npx shadcn@latest add skeleton  # For loading states

# Components are copied to src/components/ui/
# Full customization by editing the copied files
```

### Usage Pattern
```typescript
// Import components from your local ui directory
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export function QuestionInput() {
  const [question, setQuestion] = useState("")

  return (
    <Card>
      <CardHeader>
        <CardTitle>Ask About Crypto News</CardTitle>
        <CardDescription>Get AI-powered answers based on latest articles</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex gap-2">
          <Input
            placeholder="What happened to Bitcoin today?"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            className="flex-1"
          />
          <Button onClick={() => handleAsk(question)}>
            Ask
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
```

### Alternatives Considered
- **Chakra UI**: Runtime component library, larger bundle size, less control over styling
- **Material UI**: Heavy, opinionated design system
- **Headless UI**: Requires custom styling for everything
- **Raw Radix UI**: Too low-level, requires significant setup

### Shadcn UI vs Chakra UI Comparison

| Feature | Chakra UI | Shadcn UI |
|---------|-----------|-----------|
| Approach | Runtime library | Copy-paste components |
| Bundle Size | ~100KB+ | Only what you use (~10KB) |
| Customization | Theme overrides | Direct code editing |
| Dependencies | @chakra-ui/react + Emotion | Tailwind + Radix UI |
| Provider Needed | Yes (ChakraProvider) | No |
| TypeScript | Good | Excellent (full control) |
| Accessibility | Built-in | Built-in (via Radix UI) |
| Performance | Good | Excellent (no runtime) |
| Learning Curve | Medium | Low (just React + Tailwind) |

**Decision Factors**:
1. **Performance**: No runtime styling overhead, smaller bundle
2. **Control**: Full access to component source code
3. **Modern Stack**: Tailwind CSS is industry standard
4. **Flexibility**: Easy to customize without fighting theme system
5. **Future-Proof**: Components are in your codebase, no breaking changes from library updates

---

## Summary of Technology Stack

| Layer | Technology | Version | Justification |
|-------|-----------|---------|---------------|
| Backend Framework | FastAPI | 0.115+ | Native WebSocket support, async/await, OpenAPI generation |
| LLM Orchestration | LangChain | Latest | RAG primitives, streaming support, document loaders |
| LLM Provider | Ollama | Latest | Local inference, no API costs, Docker compatible |
| Chat Model | llama3.1:8b | - | Balance of quality and performance for Q&A |
| Embedding Model | nomic-embed-text | - | Optimized for retrieval, 768 dimensions |
| Vector Database | PostgreSQL + pgvector | 15+ / 0.5+ | Existing infrastructure, HNSW indexes, SQL familiarity |
| ORM | SQLModel | 0.0.14+ | Type-safe, Pydantic integration, Alembic compatible |
| Frontend Framework | React | 18+ | Component model, existing template |
| State Management | TanStack Query | 5+ | Server state caching, custom WebSocket integration |
| Routing | TanStack Router | Latest | Type-safe, file-based routing |
| UI Components | **Shadcn UI** | Latest | Copy-paste components, Radix UI + Tailwind CSS, full control |
| Styling | **Tailwind CSS** | 3.4+ | Utility-first CSS, excellent performance, modern DX |
| Validation | Zod | Latest | Runtime type safety for API contracts |
| Scheduling | APScheduler | 3.10+ | Async job scheduling, no external broker needed |
| Testing (Backend) | pytest | 7+ | Async support, fixtures for DB/Ollama mocks |
| Testing (Frontend) | Playwright | Latest | E2E tests for WebSocket streaming |

---

## Open Questions Resolved

All technical unknowns from the feature specification have been researched and resolved:

1. **How to stream LLM responses via WebSocket?** → FastAPI WebSocket + LangChain `.astream()`
2. **How to parse RSS feeds?** → LangChain `WebBaseLoader`
3. **How to generate embeddings locally?** → Ollama with `nomic-embed-text` model
4. **How to store and search vectors?** → pgvector extension in PostgreSQL with HNSW indexes
5. **How to build RAG pipeline?** → LangChain LCEL chains with retriever → prompt → chat model
6. **How to prevent duplicates?** → Content hash (SHA-256) with UNIQUE constraint
7. **How to schedule ingestion?** → APScheduler with async jobs
8. **How to validate contracts?** → Zod schemas on frontend
9. **How to handle no results?** → Distance threshold check before LLM invocation
10. **How to manage WebSocket state in React?** → Custom hook with TanStack Query patterns

---

**Research Phase Status**: ✅ COMPLETE

All technical decisions documented with rationale, implementation patterns from official documentation (via Context7), and alternatives considered. Ready to proceed to Phase 1 (Design & Contracts).
