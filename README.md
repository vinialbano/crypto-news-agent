# Crypto News Agent

A RAG-powered crypto news aggregator with intelligent question answering using local LLMs. The system automatically ingests news from multiple crypto sources and enables natural language queries about recent developments in the crypto space.

## The Challenge

This project was built as a technical assessment with the following requirements:

**Core Objective**: Build an LLM-powered web application that understands user questions and provides real-time, accurate answers based on the latest cryptocurrency news.

**Key Requirements**:
- Ingest live crypto news from multiple sources
- Semantic search for relevant articles
- LLM-powered answer generation with context
- Real-time streaming responses (word-by-word)
- Handle concurrent requests and edge cases
- Basic content moderation for offensive input

**Constraints**:
- Backend: Any language
- Frontend: React
- News sources: DL News, The Defiant, Cointelegraph

## Solution Approach

My approach was to build a complete **RAG (Retrieval-Augmented Generation) pipeline**:

1. **Ingestion**: RSS feeds → Parse with LangChain → Extract full-text with newspaper3k
2. **Vectorization**: Generate embeddings with Ollama (nomic-embed-text)
3. **Storage**: PostgreSQL with pgvector extension for semantic search
4. **Retrieval**: Query embedding → Cosine similarity search → Top-K articles
5. **Generation**: Feed context to LLM (llama3.2:3b) → Stream response token-by-token

**Technology Choices**:
- **Backend**: FastAPI + Python (rich ETL/vectorization ecosystem)
- **LangChain**: RSSFeedLoader for easy XML parsing and content extraction
- **WebSocket**: Bi-directional streaming (simpler than SSE for back-and-forth)
- **Shadcn UI**: Rapid prototyping with composable components + MCP server
- **FastAPI Template**: Jump-started with full-stack template, then cleaned

## Features

- **Automated News Ingestion**: Fetches and processes articles from leading crypto news sources (DL News, The Defiant, Cointelegraph)
- **RAG Question Answering**: Ask questions about recent crypto news and get AI-powered answers with source citations
- **Real-Time Streaming**: WebSocket-based streaming responses for immediate feedback
- **Content Moderation**: Built-in filtering for profanity, spam, and prompt injection attacks
- **Semantic Search**: Vector-based similarity search powered by pgvector for relevant article retrieval
- **Automatic Deduplication**: Smart content hashing prevents duplicate articles
- **Background Jobs**: Scheduled ingestion every 30 minutes and automatic cleanup of old articles
- **Local LLM**: Runs entirely on Ollama - no external API costs or data sharing

## Technology Stack

### Backend
- **FastAPI** - Modern async Python web framework (chosen for quick development + automatic OpenAPI docs)
- **SQLModel** - Type-safe ORM (Pydantic + SQLAlchemy) for database operations
- **PostgreSQL + pgvector** - Single database solution for both relational data and vector similarity search
- **Ollama** - Local LLM server (nomic-embed-text for embeddings, llama3.2:3b for chat)
- **LangChain** - Framework for RAG applications (RSSFeedLoader, document processing)
- **APScheduler** - Background job scheduling for automatic ingestion

### Frontend
- **React + TypeScript** - Modern frontend with type safety
- **TanStack Query & Router** - Data fetching/caching and file-based routing
- **Shadcn UI + Tailwind CSS** - Composable component library with dark mode support
- **Playwright** - End-to-end testing framework

### Infrastructure
- **Docker Compose** - Local development environment with all services
- **pytest** - Comprehensive test suite (unit tests, integration tests, E2E tests)

## Architecture Overview

The system follows a clean, service-oriented architecture:

```
Frontend (React)
    ↓ WebSocket /ask
Backend API (FastAPI)
    ├─ News Ingestion Service
    │   ├─ RSS Fetcher (LangChain + newspaper3k)
    │   └─ Article Processor (embeddings + deduplication)
    ├─ RAG Service
    │   ├─ Semantic Search (pgvector)
    │   └─ LLM Response Generation (Ollama)
    └─ Content Moderation
    ↓
PostgreSQL + pgvector
Ollama (Local LLM)
```

**Design Pattern**: Service-oriented architecture with dependency injection for testability. All external dependencies injected via FastAPI's `Depends()` pattern, centralized in `deps.py`.

For detailed technical documentation, see:
- Backend: [backend/README.md](./backend/README.md)
- Frontend: [frontend/README.md](./frontend/README.md)

## Quick Start

### Prerequisites

- [Docker](https://www.docker.com/) and Docker Compose
- [uv](https://docs.astral.sh/uv/) for Python development (optional, for local development)

### 1. Clone and Configure

Clone the repository:

```bash
git clone https://github.com/vinialbano/crypto-news-agent.git
cd crypto-news-agent
```

Configure environment variables in `.env`:

```bash
# Generate secure keys
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Update .env with secure values
POSTGRES_PASSWORD=<strong-password>
```

### 2. Start the Stack

Start all services with Docker Compose:

```bash
docker compose watch
```

This will start:
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:5173
- **Database**: PostgreSQL with pgvector on port 5432
- **Ollama**: Local LLM server on port 11434

### 3. Access the Application

**Frontend**: Open http://localhost:5173

### 4. Ask Questions About Crypto News

Once articles are ingested (happens automatically every 30 minutes, or trigger manually via API):

1. Navigate to the chat page in the frontend
2. Ask natural language questions like:
   - "What are the latest developments in Bitcoin?"
   - "Tell me about recent Ethereum updates"
   - "What happened with DeFi this week?"
3. Get streaming AI responses with source citations

## Key Design Decisions

### 1. FastAPI Template → Radical Simplification

**Decision**: Started with FastAPI full-stack template, then removed some thousands of lines of production code.

**Rationale**:
- Quick start with batteries included (Docker, migrations, testing setup)
- Template included production complexity not needed for this project
- Removed: GitHub Actions, Traefik reverse proxy, email services, deployment scripts

**Trade-off**: Spent time cleaning vs building from scratch, but gained solid foundation.

**Result**: Focused codebase for learning while maintaining test infrastructure (pytest, Playwright, coverage).

### 2. Config-Based News Sources (No Database CRUD)

**Decision**: News sources defined in environment variables, not in database.

**Rationale**:
- Simpler: No admin UI needed to manage sources
- Version controlled: Sources tracked in `.env` file
- Deployment-friendly: Change sources without database migration

**Trade-off**: Less dynamic (requires code deploy to add sources), but acceptable for this use case.

**Implementation**: See `backend/app/core/config.py` - `news_sources` computed field.

### 3. PostgreSQL + pgvector (No Separate Vector Database)

**Decision**: Use pgvector extension in PostgreSQL instead of dedicated vector database (Qdrant, Weaviate, Pinecone).

**Rationale**:
- Single database: Relational data + vectors in one place
- ACID compliance: Transactions work across all data
- Familiar tooling: Standard PostgreSQL tools and backups
- Lower complexity: One fewer service to deploy/manage

**Trade-off**: Fewer vector search features vs specialized DBs, but sufficient for this scale.

**Technical detail**: HNSW index for approximate nearest neighbor search (<0.5 cosine distance threshold).

### 4. WebSocket for Streaming (Not SSE)

**Decision**: WebSocket protocol for question answering instead of Server-Sent Events.

**Rationale**:
- Bi-directional: Can send metadata and receive responses in same connection
- Simpler protocol: Less HTTP overhead for streaming
- Built-in backpressure: Client can control flow

**Implementation**: Rate limiting (10 questions/minute), timeout protection (3 minutes), structured protocol:
```json
{"type": "sources", "articles": [...]}
{"type": "chunk", "content": "Bitcoin..."}
{"type": "done"}
```

### 5. Strict Dependency Injection Pattern

**Decision**: ALL dependency factories must live in `backend/app/deps.py`.

**Rationale**:
- Testability: Easy to mock dependencies in unit tests
- Consistency: Same dependency graph everywhere (API, scheduler, CLI)
- Single Responsibility: Services never instantiate their own dependencies

**Impact**: unit tests using dependency mocking, instead of monkey patching.

### 6. LangChain RSSFeedLoader + newspaper3k

**Decision**: Use LangChain's RSSFeedLoader with newspaper3k for full-text extraction.

**Rationale**:
- LangChain integration: Fits naturally into RAG pipeline
- Full-text extraction: newspaper3k gets complete article content (not just RSS summary)
- Mature libraries: Battle-tested for content extraction

**Challenge**: newspaper3k HTML parsing can fail on some sites → Implemented graceful fallback.

### 7. Content Hash Deduplication

**Decision**: SHA-256 hash of (title + URL) with unique database constraint.

**Rationale**:
- RSS feeds often republish same articles
- Database-level enforcement prevents duplicates automatically
- Fast lookup: Hash indexed for O(1) duplicate detection

**Implementation**: See `backend/app/models.py` - `content_hash` field with unique constraint.

## Technical Challenges Solved

### Challenge 1: Ollama Startup Race Condition

**Problem**: Backend starts before Ollama finishes loading models → connection failures.

**Solution**:
- Health check script with retry logic: `backend/scripts/prestart.sh`
- Docker healthchecks: Wait for Ollama ready state
- Graceful degradation: Log errors but continue startup

**Code**: See `backend/app/core/config.py` - Ollama connection with timeout handling.

### Challenge 2: Duplicate Article Detection with URL Normalization

**Problem**: RSS feeds republish articles with different tracking parameters (utm_*, fbclid, timestamps), causing the same article to be stored multiple times.

**Example**: These URLs point to the same article but have different query parameters:
```
https://example.com/article?utm_source=rss&timestamp=123
https://example.com/article?utm_source=twitter&fbclid=xyz
https://example.com/article?gclid=abc&utm_medium=cpc
```

**Solution**:
- **URL normalization**: Strip query parameters, fragments, trailing slashes before hashing
- **Lowercase normalization**: Convert scheme, domain, and path to lowercase
- **Content hash**: `SHA-256(title + normalized_url)` as unique identifier
- **Database unique constraint**: Automatic duplicate rejection
- **Fast lookup**: O(1) hash-based duplicate detection

**Implementation**:
- `backend/app/services/url_utils.py` - URL normalization utility
- `backend/app/services/article_processor.py` - Uses normalized URLs for hashing
- Comprehensive test suite with real-world URLs

**Result**: Zero duplicate articles in database, even with tracking parameters and overlapping RSS feeds.

### Challenge 3: Real-Time Streaming UX

**Problem**: LLM responses take several seconds → need to show progress to user.

**Solution**:
- WebSocket streaming: Token-by-token response delivery
- Structured protocol: Send sources first, then stream content, then done signal
- Frontend handling: Update UI as each token arrives

**UX Impact**: Immediate feedback vs waiting for complete response (2-5 seconds vs 10-15 seconds perceived time).

## Known Issues

### RSS Feed Date Parsing Inconsistencies

**Problem**: Some RSS feeds return `null` for publication dates even when `<pubDate>` exists in the RSS XML.

**Details**:
- LangChain's `RSSFeedLoader` fails to parse dates from certain feeds (e.g., Cointelegraph)
- Raw RSS XML contains valid `<pubDate>` tags: `<pubDate>Fri, 07 Nov 2025 23:51:58 +0000</pubDate>`
- The `publish_date` field in document metadata is consistently `None` for these feeds
- Other feeds (e.g., The Defiant) work correctly and return valid datetime objects

**Impact**:
- Articles from affected feeds have `published_at: null` in the database
- Semantic search and chat features still work (dates are optional)
- Articles can still be ingested and deduplicated correctly

**Potential Solutions** (not implemented):
- Use `feedparser` library as a fallback to parse dates directly from RSS XML
- Parse dates from article content using NLP
- Switch to alternative RSS feeds for affected sources
- File issue with LangChain/newspaper3k projects

**Current Status**: Accepted limitation. Articles are stored without dates for some sources.

## Trade-offs & Limitations

### What I Sacrificed for Simplicity

1. **Config-based sources vs Admin UI**
   - Pro: Simpler code, version controlled
   - Con: Can't add sources without deployment
   - Decision: Config is sufficient for 3-5 sources

2. **Local LLM vs Cloud APIs (OpenAI/Anthropic)**
   - Pro: Zero API costs, complete privacy, learning experience
   - Con: Slower inference (3-5 sec vs 1-2 sec), requires GPU for best performance
   - Decision: Acceptable for demo, worth the learning

3. **Single PostgreSQL vs Specialized Vector DB**
   - Pro: Simpler deployment, familiar tooling, ACID compliance
   - Con: Fewer vector search features (no filtering, clustering, etc.)
   - Decision: pgvector sufficient for semantic search needs

4. **Regex-based moderation vs ML model**
   - Pro: Fast, predictable, no extra dependencies
   - Con: Can be bypassed with creative spelling
   - Decision: Good enough for profanity/spam, not production-grade

5. **No authentication on /ask endpoint**
   - Pro: Simpler demo, faster development
   - Con: Open to abuse (rate limited per IP only)
   - Decision: Fine for assessment, would add auth for production

## What I'd Do Differently

### If Starting Over:

1. **Start with simpler template**
   - FastAPI full-stack was overkill for this project
   - Would use another template or build from scratch
   - Saved time on setup, lost time on cleanup

2. **Consider Qdrant/Weaviate for vectors**
   - pgvector works, but specialized DBs have better features
   - Filtering, hybrid search, clustering would be useful
   - Trade-off: One more service to manage

5. **Implement better error boundaries**
   - Current error handling is basic (try/catch + logging)
   - Structured errors with retry logic would be more robust
   - Integration with an observability tool for production monitoring

### Known Limitations:

- **Embedding quality**: nomic-embed-text is good but not SOTA (768-dim vs 1536-dim OpenAI)
- **No article ranking**: Just cosine distance, no relevance feedback or re-ranking
- **No conversation memory**: Each question is independent (no follow-ups)
- **Basic content moderation**: Regex-based, can be bypassed
- **No caching**: Embeddings generated fresh each time (could cache query embeddings)

## Development

For detailed development instructions, see:

- **Backend**: [backend/README.md](./backend/README.md) - API development, testing, migrations
- **Frontend**: [frontend/README.md](./frontend/README.md) - React development, E2E testing, API client generation

**Quick Commands**:

```bash
# Start all services with hot-reload
docker compose watch

# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Run backend tests
cd backend && bash scripts/test-all.sh

# Run frontend E2E tests
cd frontend && npx playwright test

# Generate API client (after backend changes)
bash scripts/generate-client.sh
```

## Project Structure

```
crypto-news-agent/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── main.py      # Application entry point
│   │   ├── routes.py    # API endpoints (REST + WebSocket)
│   │   ├── models.py    # Database models (NewsArticle)
│   │   ├── services/    # Business logic (ingestion, RAG, embeddings)
│   │   ├── core/        # Configuration & database
│   │   └── alembic/     # Database migrations
│   ├── scripts/         # Development & test scripts
│   ├── tests/           # Unit, integration, E2E tests
│   └── README.md        # Backend documentation
├── frontend/            # React frontend
│   ├── src/
│   │   ├── routes/      # Page components (TanStack Router)
│   │   ├── components/  # Reusable UI components
│   │   └── client/      # Auto-generated API client
│   └── README.md        # Frontend documentation
├── docker-compose.yml   # Docker services configuration
├── .env                 # Environment configuration
└── README.md           # This file
```

## Credits

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [React](https://react.dev/) - UI library
- [Ollama](https://ollama.ai/) - Local LLM server
- [LangChain](https://www.langchain.com/) - LLM application framework
- [pgvector](https://github.com/pgvector/pgvector) - Vector similarity search for PostgreSQL

Based on [FastAPI Full Stack Template](https://github.com/fastapi/full-stack-fastapi-template) by Sebastián Ramírez.
