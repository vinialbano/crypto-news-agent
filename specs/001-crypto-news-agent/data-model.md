# Data Model: Crypto News Agent

**Feature**: 001-crypto-news-agent
**Date**: 2025-11-05
**Phase**: 1 (Design & Contracts)

This document defines all entities, relationships, validation rules, and state transitions for the Crypto News Agent system.

---

## Entity Definitions

### 1. NewsArticle

**Purpose**: Represents a single cryptocurrency news article ingested from an RSS feed.

**Fields**:
- `id` (int, primary key): Auto-incrementing unique identifier
- `content_hash` (str, unique, indexed): SHA-256 hash of title + URL for duplicate detection
- `title` (str, max 500 chars, required): Article headline
- `url` (str, max 2048 chars, required): Original article URL
- `content` (text, required): Full article text content
- `source_name` (str, max 100 chars, required): News source name (e.g., "DL News", "The Defiant", "Cointelegraph")
- `published_at` (datetime, nullable): Article publication timestamp (from RSS feed)
- `ingested_at` (datetime, required): Timestamp when article was ingested into system
- `embedding` (vector(768), required): Article content embedding for semantic search (nomic-embed-text dimension)

**Validation Rules**:
- `title`: Must not be empty, max 500 characters
- `url`: Must be valid URL format, max 2048 characters
- `content`: Must not be empty, min 100 characters (avoid empty/malformed articles)
- `source_name`: Must be one of configured sources
- `content_hash`: Auto-computed as SHA-256(title + "|" + url), enforced unique
- `embedding`: Must be 768-dimensional vector, all values floats

**Indexes**:
- Primary key on `id`
- Unique index on `content_hash`
- HNSW index on `embedding` with cosine similarity operator for fast vector search
- Index on `ingested_at` for chronological queries
- Index on `source_name` for filtering by source

**Relationships**:
- None (articles are independent entities)

**State Transitions**:
- Created → ingestion process fetches RSS, generates embedding, inserts row
- No updates (articles are immutable after ingestion)
- Deleted → periodic cleanup removes articles older than 30 days

---

### 2. NewsSource

**Purpose**: Represents a configured RSS feed source for cryptocurrency news.

**Fields**:
- `id` (int, primary key): Auto-incrementing unique identifier
- `name` (str, max 100 chars, unique, required): Display name (e.g., "DL News")
- `rss_url` (str, max 2048 chars, unique, required): RSS feed URL
- `is_active` (bool, default True): Whether source should be ingested
- `last_ingestion_at` (datetime, nullable): Timestamp of last successful ingestion
- `last_error` (str, nullable): Last error message if ingestion failed
- `ingestion_count` (int, default 0): Total number of successful ingestions

**Validation Rules**:
- `name`: Must not be empty, max 100 characters, unique
- `rss_url`: Must be valid URL format, max 2048 characters, unique
- `is_active`: Boolean only
- `last_error`: Max 1000 characters

**Indexes**:
- Primary key on `id`
- Unique index on `name`
- Unique index on `rss_url`
- Index on `is_active` for filtering active sources

**Relationships**:
- Conceptually linked to `NewsArticle` via `source_name`, but no foreign key constraint (to allow source deletion without cascade)

**State Transitions**:
- Created → admin or seed script adds new source
- Active → `is_active=True`, included in scheduled ingestion
- Inactive → `is_active=False`, skipped during ingestion
- Updated → `last_ingestion_at` updated after successful ingestion, `last_error` set on failure

---

### 3. Question (Frontend only, not persisted)

**Purpose**: Represents a user's natural language query submitted via the UI.

**Fields**:
- `text` (str, max 1000 chars, required): User's question
- `submitted_at` (datetime): Client-side timestamp

**Validation Rules** (Frontend - Zod schema):
- `text`: Non-empty, trimmed, max 1000 characters
- No special characters or script injection attempts

**State Transitions**:
- Created → user types question and submits form
- Transmitted → sent via WebSocket to backend
- Not persisted in database (ephemeral)

---

### 4. Answer (Frontend only, not persisted)

**Purpose**: Represents the streaming LLM-generated response to a user's question.

**Fields**:
- `chunks` (array of strings): Individual text chunks received via WebSocket
- `full_text` (str): Concatenated full answer
- `source_count` (int): Number of news articles used as context
- `status` (enum): 'streaming' | 'complete' | 'error'
- `error_message` (str, nullable): Error message if status='error'

**Validation Rules** (Frontend - Zod schema):
- `status`: Must be one of the enum values
- `chunks`: Array of non-empty strings
- `source_count`: Non-negative integer

**State Transitions**:
- Streaming → receiving chunks from WebSocket, status='streaming'
- Complete → received final chunk, status='complete'
- Error → WebSocket error or "insufficient information" message, status='error'

---

### 5. StreamMessage (WebSocket protocol)

**Purpose**: Represents a single message sent from backend to frontend via WebSocket during answer streaming.

**Fields**:
- `type` (enum): 'chunk' | 'sources' | 'done' | 'error'
- `content` (str): Text chunk (if type='chunk'), error message (if type='error'), or empty
- `metadata` (object, optional):
  - `source_count` (int): Number of articles used (sent with type='sources')
  - `distance_threshold` (float): Semantic search threshold used

**Validation Rules** (Zod schema):
- `type`: Must be one of enum values
- `content`: String, required for 'chunk' and 'error', optional otherwise
- `metadata.source_count`: Non-negative integer if present

**Example Messages**:
```json
// First message: metadata about sources
{"type": "sources", "content": "", "metadata": {"source_count": 3}}

// Subsequent messages: text chunks
{"type": "chunk", "content": "Bitcoin "}
{"type": "chunk", "content": "surged "}
{"type": "chunk", "content": "today..."}

// Final message
{"type": "done", "content": ""}

// Error case
{"type": "error", "content": "I don't have enough information about that topic in recent news."}
```

---

## Database Schema (PostgreSQL + pgvector)

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- News sources table
CREATE TABLE news_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    rss_url VARCHAR(2048) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    last_ingestion_at TIMESTAMP,
    last_error VARCHAR(1000),
    ingestion_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- News articles table
CREATE TABLE news_articles (
    id SERIAL PRIMARY KEY,
    content_hash CHAR(64) UNIQUE NOT NULL,  -- SHA-256 hex string
    title VARCHAR(500) NOT NULL,
    url VARCHAR(2048) NOT NULL,
    content TEXT NOT NULL,
    source_name VARCHAR(100) NOT NULL,
    published_at TIMESTAMP,
    ingested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    embedding vector(768) NOT NULL,  -- nomic-embed-text dimension

    CONSTRAINT content_min_length CHECK (LENGTH(content) >= 100)
);

-- Indexes for performance
CREATE INDEX idx_news_articles_ingested_at ON news_articles(ingested_at DESC);
CREATE INDEX idx_news_articles_source_name ON news_articles(source_name);
CREATE INDEX idx_news_sources_active ON news_sources(is_active) WHERE is_active = TRUE;

-- HNSW index for fast vector similarity search (cosine distance)
CREATE INDEX idx_news_articles_embedding ON news_articles
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
```

---

## SQLModel Models (Python)

```python
from sqlmodel import SQLModel, Field, Column
from pgvector.sqlalchemy import Vector
from datetime import datetime
from typing import Optional

class NewsSource(SQLModel, table=True):
    __tablename__ = "news_sources"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True, index=True)
    rss_url: str = Field(max_length=2048, unique=True)
    is_active: bool = Field(default=True, index=True)
    last_ingestion_at: Optional[datetime] = None
    last_error: Optional[str] = Field(default=None, max_length=1000)
    ingestion_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class NewsArticle(SQLModel, table=True):
    __tablename__ = "news_articles"

    id: Optional[int] = Field(default=None, primary_key=True)
    content_hash: str = Field(max_length=64, unique=True, index=True)
    title: str = Field(max_length=500)
    url: str = Field(max_length=2048)
    content: str
    source_name: str = Field(max_length=100, index=True)
    published_at: Optional[datetime] = None
    ingested_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    embedding: list[float] = Field(sa_column=Column(Vector(768)))

    @classmethod
    def compute_content_hash(cls, title: str, url: str) -> str:
        import hashlib
        content = f"{title}|{url}"
        return hashlib.sha256(content.encode()).hexdigest()
```

---

## TypeScript Types (Frontend)

```typescript
// Zod schemas for runtime validation
import { z } from 'zod'

export const NewsArticleSchema = z.object({
  id: z.number(),
  title: z.string(),
  url: z.string().url(),
  source_name: z.string(),
  published_at: z.string().datetime().nullable(),
  ingested_at: z.string().datetime(),
  content: z.string(),
})

export const StreamMessageSchema = z.object({
  type: z.enum(['chunk', 'sources', 'done', 'error']),
  content: z.string(),
  metadata: z.object({
    source_count: z.number().int().nonnegative().optional(),
    distance_threshold: z.number().optional(),
  }).optional(),
})

export const QuestionSchema = z.object({
  text: z.string().trim().min(1).max(1000),
})

// Inferred types
export type NewsArticle = z.infer<typeof NewsArticleSchema>
export type StreamMessage = z.infer<typeof StreamMessageSchema>
export type Question = z.infer<typeof QuestionSchema>

// Answer state (managed in React)
export interface AnswerState {
  chunks: string[]
  fullText: string
  sourceCount: number | null
  status: 'idle' | 'streaming' | 'complete' | 'error'
  errorMessage: string | null
}
```

---

## Data Flow Diagrams

### Ingestion Flow

```
┌─────────────────┐
│ APScheduler     │
│ (every 30 min)  │
└────────┬────────┘
         │
         v
┌─────────────────────────────┐
│ IngestionService.run()      │
│ - Fetch active sources      │
└────────┬────────────────────┘
         │
         v
┌─────────────────────────────┐
│ For each NewsSource:        │
│ - WebBaseLoader(rss_url)    │
│ - Parse documents           │
└────────┬────────────────────┘
         │
         v
┌─────────────────────────────┐
│ For each document:          │
│ - Compute content_hash      │
│ - Check if exists (hash)    │
│ - If new: generate embedding│
│ - Insert NewsArticle        │
└────────┬────────────────────┘
         │
         v
┌─────────────────────────────┐
│ Update NewsSource:          │
│ - last_ingestion_at         │
│ - ingestion_count++         │
│ - Clear last_error          │
└─────────────────────────────┘
```

### Question Answering Flow

```
┌─────────────────┐
│ User submits    │
│ question via UI │
└────────┬────────┘
         │
         v
┌─────────────────────────────┐
│ WebSocket connection        │
│ /ws/ask                     │
│ - Receive question text     │
└────────┬────────────────────┘
         │
         v
┌─────────────────────────────┐
│ EmbeddingsService:          │
│ - Generate query embedding  │
└────────┬────────────────────┘
         │
         v
┌─────────────────────────────┐
│ SemanticSearch:             │
│ - Query pgvector            │
│ - ORDER BY cosine_distance  │
│ - LIMIT 5                   │
└────────┬────────────────────┘
         │
         v
┌─────────────────────────────┐
│ Distance check:             │
│ - If min_distance > 0.5:    │
│   Send error message        │
│ - Else: continue to RAG     │
└────────┬────────────────────┘
         │
         v
┌─────────────────────────────┐
│ RAG Service:                │
│ - Format context from docs  │
│ - Build prompt with context │
│ - Stream from ChatOllama    │
└────────┬────────────────────┘
         │
         v (stream)
┌─────────────────────────────┐
│ WebSocket send:             │
│ - Send source_count         │
│ - For each chunk: send JSON │
│ - Send 'done' when complete │
└────────┬────────────────────┘
         │
         v
┌─────────────────────────────┐
│ Frontend accumulates chunks │
│ - Display word-by-word      │
│ - Mark complete when 'done' │
└─────────────────────────────┘
```

---

## Validation Rules Summary

### Backend (Pydantic/SQLModel)
- All required fields enforced at model level
- String length constraints via `Field(max_length=...)`
- URL format validation via Pydantic's HttpUrl type
- Embedding dimension check (must be 768 floats)
- Content minimum length (100 chars) enforced via CHECK constraint

### Frontend (Zod)
- Question text: 1-1000 chars, trimmed
- WebSocket messages: type enum validation, content required for certain types
- News article list: validate API response structure before rendering

### Database (PostgreSQL)
- UNIQUE constraints on content_hash, source name, source URL
- NOT NULL constraints on all required fields
- CHECK constraint for minimum content length
- Foreign key integrity (if NewsSource → NewsArticle relationship enforced)

---

## Cleanup and Retention

### 30-Day Article Retention
- Background job runs daily at 2 AM UTC
- Deletes articles where `ingested_at < NOW() - INTERVAL '30 days'`
- Logs number of articles deleted for monitoring

```sql
-- Cleanup query (executed by scheduled job)
DELETE FROM news_articles
WHERE ingested_at < CURRENT_TIMESTAMP - INTERVAL '30 days';
```

### Source Management
- Inactive sources (`is_active=FALSE`) remain in database but skipped during ingestion
- No automatic deletion of sources
- Admin can manually delete sources (articles from that source remain with `source_name` preserved as string)

---

**Data Model Phase Status**: ✅ COMPLETE

All entities defined with fields, validation rules, relationships, and state transitions. Database schema and ORM models specified. Ready for contract generation.
