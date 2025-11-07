# FastAPI Backend - Crypto News Agent

A production-ready FastAPI backend for crypto news ingestion and RAG-powered question answering using local LLMs via Ollama.

## Requirements

* [Docker](https://www.docker.com/)
* [uv](https://docs.astral.sh/uv/) for Python package and environment management

## Architecture Overview

The backend follows a **clean, service-oriented architecture** with clear separation of concerns:

```
API Layer (routes.py)
    ↓
Service Layer (services/)
    ↓
Repository Layer (news_repository.py)
    ↓
Database Models (models.py)
    ↓
PostgreSQL + pgvector
```

**Key Architectural Patterns:**
- **Service Layer Pattern**: Business logic encapsulated in dedicated services
- **Repository Pattern**: Database operations abstracted in `NewsRepository`
- **Dependency Injection**: All external dependencies injected via FastAPI's `Depends()`
- **Config-Based Sources**: News sources managed via environment variables (no database table)

### Recent Architecture Changes

The backend recently migrated from database-driven news sources to **config-based management**:
- News sources now defined in environment variables (`.env` file)
- No `news_sources` table required
- Simpler configuration and version control
- See migration `4ce808250de3_drop_news_sources_table.py`

## Project Structure

```
backend/app/
├── main.py                      # FastAPI app + lifespan management
├── routes.py                    # All API endpoints (REST + WebSocket)
├── models.py                    # Database models (NewsArticle)
├── deps.py                      # Dependency injection factories
├── exceptions.py                # Custom exception hierarchy
├── scheduler.py                 # Background job scheduler
├── core/
│   ├── config.py               # Pydantic Settings + news sources
│   └── db.py                   # Database engine setup
├── services/                    # Business logic layer
│   ├── ingestion.py            # News ingestion orchestration
│   ├── rss_fetcher.py          # RSS feed fetching (LangChain)
│   ├── article_processor.py   # Article processing + embeddings
│   ├── embeddings.py           # Ollama embeddings service
│   ├── rag.py                  # RAG question answering
│   ├── content_moderation.py  # Input validation & security
│   └── news_repository.py      # Database operations
├── alembic/                     # Database migrations
│   └── versions/               # Migration files
└── scripts/                     # Startup & utility scripts
    ├── backend_pre_start.py    # DB + Ollama health checks
    └── prestart.sh             # Docker entrypoint script
```

## Core Components

### 1. API Layer (`routes.py`)

All API endpoints in a single file with clean dependency injection.

**News Endpoints:**
- `GET /news/` - List recent articles with optional source filtering
- `POST /news/ingest/` - Manually trigger ingestion (single source or all)
- `GET /news/sources` - List configured news sources

**Questions Endpoint:**
- `WebSocket /ask` - Real-time streaming question answering
  - Rate limiting: 10 questions per minute per client
  - Content moderation: Profanity/spam/injection detection
  - Streaming protocol: `{"type": "sources"}` → `{"type": "chunk", "content": "..."}` → `{"type": "done"}`

### 2. Database Models (`models.py`)

**NewsArticle Model:**
```python
class NewsArticle(SQLModel, table=True):
    id: int                      # Primary key
    content_hash: str            # SHA-256(title + URL) for deduplication
    title: str                   # Article title
    url: str                     # Article URL
    content: str                 # Full article text
    source_name: str             # Source identifier (e.g., "DL News")
    published_at: datetime | None # Publication timestamp
    ingested_at: datetime        # When added to database
    embedding: list[float]       # 768-dimensional vector (pgvector)
```

**Features:**
- SQLModel combines Pydantic validation + SQLAlchemy ORM
- Built-in deduplication via `content_hash` unique constraint
- pgvector integration for semantic search
- HNSW index on embeddings for fast similarity queries

### 3. Services Layer

#### **IngestionService** (`ingestion.py`)
Orchestrates the news ingestion pipeline: RSS fetching → processing → persistence.

**Methods:**
- `ingest_source(name: str)` - Ingest from single source
- `ingest_all_sources()` - Ingest from all configured sources
- `cleanup_old_articles(days: int)` - Delete articles older than N days

**Returns:** Detailed statistics (new articles, duplicates, errors, duration)

#### **RSSFetcher** (`rss_fetcher.py`)
Fetches and parses RSS feeds using LangChain's `RSSFeedLoader` with `newspaper3k` for full-text extraction.

**Features:**
- Extracts full article content (not just RSS summaries)
- Handles publish date parsing with fallback
- Filters out short content (< 100 chars)
- Graceful error handling per article

#### **ArticleProcessor** (`article_processor.py`)
Processes articles with duplicate detection and embedding generation.

**Workflow:**
1. Check for duplicates via content hash
2. Generate embedding via `EmbeddingsService`
3. Persist to database via `NewsRepository`
4. Track statistics (new/duplicates/errors)

#### **EmbeddingsService** (`embeddings.py`)
Wraps Ollama embeddings using `nomic-embed-text` model.

**Methods:**
- `embed_query(text)` - Generate embedding for single text (sync)
- `aembed_query(text)` - Generate embedding (async)
- `embed_documents(texts)` - Generate embeddings for batch (sync)
- `aembed_documents(texts)` - Generate embeddings for batch (async)

#### **RAGService** (`rag.py`)
Question answering using Retrieval Augmented Generation.

**Workflow:**
1. Generate query embedding via `EmbeddingsService`
2. Semantic search for top-K relevant articles via `NewsRepository`
3. Check relevance threshold (pgvector cosine distance)
4. Build context from retrieved articles
5. Stream LLM response with source citations via `ChatOllama`

**Features:**
- Streaming responses for real-time UX
- Source attribution in answers
- Configurable relevance threshold and top-K

#### **ContentModerationService** (`content_moderation.py`)
Multi-layer input validation and security.

**Checks:**
- Profanity filtering (regex patterns)
- Prompt injection detection (common attack patterns)
- Spam detection (repetitive patterns)
- Length validation (max 500 chars)

**Returns:** `ModerationResult(is_valid, reason, filtered_text)`

#### **NewsRepository** (`news_repository.py`)
Database operations abstraction using repository pattern.

**News Sources:**
- `get_active_news_sources()` - Returns sources from config (not DB)
- `get_source_by_name(name)` - Lookup source by name

**Article Operations:**
- `create_news_article()` - Insert with duplicate detection
- `get_recent_articles()` - Paginated list with filtering
- `semantic_search()` - Vector similarity search via pgvector
- `delete_old_articles()` - Cleanup by date

### 4. Configuration (`core/config.py`)

**Pydantic Settings** with environment variables:

```python
class Settings(BaseSettings):
    # Database
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    # Ollama
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_CHAT_MODEL: str = "llama3.2:3b"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"

    # News Sources (environment variables)
    RSS_DL_NEWS: str
    RSS_THE_DEFIANT: str
    RSS_COINTELEGRAPH: str

    @computed_field
    @property
    def news_sources(self) -> list[dict[str, str]]:
        """Aggregate news sources from environment variables."""
        return [
            {"name": "DL News", "rss_url": self.RSS_DL_NEWS},
            {"name": "The Defiant", "rss_url": self.RSS_THE_DEFIANT},
            {"name": "Cointelegraph", "rss_url": self.RSS_COINTELEGRAPH},
        ]

    # Ingestion
    INGESTION_INTERVAL_MINUTES: int = 30
    ARTICLE_CLEANUP_DAYS: int = 90

    # RAG
    RAG_DISTANCE_THRESHOLD: float = 0.5
    RAG_TOP_K_ARTICLES: int = 5
    RAG_MAX_CONTEXT_LENGTH: int = 8000

    # WebSocket
    WS_MAX_QUESTIONS_PER_MINUTE: int = 10
    WS_TIMEOUT_SECONDS: int = 180
```

### 5. Dependency Injection (`deps.py`)

**Critical Design Decision:** ALL dependency factories centralized in one file.

**Benefits:**
- Testability: Easy to mock dependencies in tests
- Consistency: Same dependency graph everywhere (API, scheduler, CLI)
- Single Responsibility: Services never instantiate their own dependencies

**Example Factory:**
```python
def create_ingestion_service(session: Session) -> IngestionService:
    """Factory for IngestionService with all dependencies."""
    return IngestionService(
        rss_fetcher=RSSFetcher(),
        article_processor=ArticleProcessor(
            embeddings_service=get_embeddings_service(),
            repository=NewsRepository(session),
        ),
        repository=NewsRepository(session),
    )
```

### 6. Background Scheduler (`scheduler.py`)

**APScheduler** (AsyncIOScheduler) manages background jobs:

**Jobs:**
1. **News Ingestion** - Every 30 minutes (configurable)
   - Calls `ingest_all_sources()`
   - Max instances: 1 (prevents overlapping runs)

2. **Article Cleanup** - Daily at 2 AM UTC
   - Deletes articles older than 90 days (configurable)

**Lifecycle:** Started in `main.py` lifespan, stopped on shutdown.

## Key Features

### News Ingestion System
- Automatic RSS feed fetching with full-text extraction
- Deduplication via content hashing (SHA-256)
- Batch processing with detailed statistics
- Scheduled background ingestion (every 30 minutes)
- Manual triggering via API endpoint
- Automatic cleanup of old articles (daily)

### RAG Question Answering
- Semantic search using pgvector embeddings (768-dim nomic-embed-text)
- LLM response generation via Ollama (llama3.2:3b)
- Streaming responses for real-time user experience
- Source citation in answers
- Relevance threshold filtering (cosine distance < 0.5)
- WebSocket protocol for bi-directional communication

### Content Moderation
- Rate limiting: 10 questions per minute per client
- Profanity filtering
- Prompt injection prevention
- Spam detection
- Connection timeout protection (3 minutes)

### Database Features
- PostgreSQL with pgvector extension for vector similarity
- HNSW index for fast approximate nearest neighbor search
- Alembic migrations for schema versioning
- SQLModel for type-safe ORM operations

## Technology Stack

**Core Framework:**
- **FastAPI** - Modern async web framework with automatic OpenAPI docs
- **SQLModel** - Type-safe ORM (Pydantic + SQLAlchemy)
- **Pydantic** - Data validation and settings management
- **Alembic** - Database migration tool

**Database:**
- **PostgreSQL 15+** - Primary database
- **pgvector** - Vector similarity search extension
- **psycopg[binary]** - PostgreSQL adapter

**AI/LLM Stack:**
- **LangChain** - Framework for LLM applications
- **langchain-ollama** - Ollama integration (chat + embeddings)
- **langchain-community** - Community tools (RSSFeedLoader)
- **Ollama** - Local LLM server
  - `nomic-embed-text` - 768-dim embeddings
  - `llama3.2:3b` - Chat model for question answering

**News Ingestion:**
- **feedparser** - RSS feed parsing
- **newspaper3k** - Full-text article extraction
- **python-dateutil** - Flexible date parsing
- **lxml-html-clean** - HTML sanitization

**Background Jobs:**
- **APScheduler** - Cron-like job scheduling

**Testing:**
- **pytest** - Testing framework
- **pytest-asyncio** - Async test support
- **coverage** - Code coverage reporting

**Code Quality:**
- **ruff** - Fast Python linter/formatter
- **mypy** - Static type checking
- **pre-commit** - Git hooks for quality checks

## Data Flow Architecture

### News Ingestion Flow

```
Scheduler/Manual API Call
    ↓
IngestionService.ingest_all_sources()
    ↓
For each configured source:
  ├─ RSSFetcher.fetch_feed()
  │   ├─ LangChain RSSFeedLoader
  │   └─ newspaper3k (full-text extraction)
  ↓
  ├─ ArticleProcessor.process_batch()
  │   ├─ Check duplicates (content hash lookup)
  │   ├─ EmbeddingsService.embed_query()
  │   │   └─ Ollama (nomic-embed-text → 768-dim vector)
  │   └─ NewsRepository.create_news_article()
  │       └─ PostgreSQL INSERT with pgvector
  ↓
Return statistics (new/duplicates/errors)
```

### Question Answering Flow (WebSocket)

```
Client → WebSocket /ask
    ↓
{"question": "What is Bitcoin?"}
    ↓
Rate Limiting Check (in-memory tracker)
    ↓
ContentModerationService
    ├─ Profanity filter
    ├─ Prompt injection detection
    └─ Spam detection
    ↓
RAGService.stream_answer()
    ↓
1. Generate Query Embedding
   EmbeddingsService.aembed_query()
   └─ Ollama → 768-dim vector
    ↓
2. Semantic Search
   NewsRepository.semantic_search()
   └─ pgvector cosine distance query
   └─ Returns top-5 articles
    ↓
3. Check Relevance Threshold
   Filter articles with distance < 0.5
    ↓
4. Build Context
   Combine article content (max 8000 chars)
    ↓
5. Stream LLM Response
   ChatOllama.astream()
   └─ Stream: {"type": "sources", ...}
   └─ Stream: {"type": "chunk", "content": "..."}*
   └─ Stream: {"type": "done"}
```

## Docker Compose

Start the local development environment with Docker Compose following the guide in [../development.md](../development.md).

## General Workflow

By default, the dependencies are managed with [uv](https://docs.astral.sh/uv/), go there and install it.

From `./backend/` you can install all the dependencies with:

```console
$ uv sync
```

Then you can activate the virtual environment with:

```console
$ source .venv/bin/activate
```

Make sure your editor is using the correct Python virtual environment, with the interpreter at `backend/.venv/bin/python`.

### Code Organization

Modify or add:
- **SQLModel models** in `./backend/app/models.py`
- **API endpoints** in `./backend/app/routes.py`
- **Business logic** in `./backend/app/services/`
- **Database operations** in `./backend/app/services/news_repository.py`

**Important:** All dependency injection factories must be in `./backend/app/deps.py` to maintain consistency.

## VS Code

There are already configurations in place to run the backend through the VS Code debugger, so that you can use breakpoints, pause and explore variables, etc.

The setup is also already configured so you can run the tests through the VS Code Python tests tab.

## Docker Compose Override

During development, you can change Docker Compose settings that will only affect the local development environment in the file `docker-compose.override.yml`.

The changes to that file only affect the local development environment, not the production environment. So, you can add "temporary" changes that help the development workflow.

For example, the directory with the backend code is synchronized in the Docker container, copying the code you change live to the directory inside the container. That allows you to test your changes right away, without having to build the Docker image again. It should only be done during development, for production, you should build the Docker image with a recent version of the backend code. But during development, it allows you to iterate very fast.

There is also a command override that runs `fastapi run --reload` instead of the default `fastapi run`. It starts a single server process (instead of multiple, as would be for production) and reloads the process whenever the code changes. Have in mind that if you have a syntax error and save the Python file, it will break and exit, and the container will stop. After that, you can restart the container by fixing the error and running again:

```console
$ docker compose watch
```

There is also a commented out `command` override, you can uncomment it and comment the default one. It makes the backend container run a process that does "nothing", but keeps the container alive. That allows you to get inside your running container and execute commands inside, for example a Python interpreter to test installed dependencies, or start the development server that reloads when it detects changes.

To get inside the container with a `bash` session you can start the stack with:

```console
$ docker compose watch
```

and then in another terminal, `exec` inside the running container:

```console
$ docker compose exec backend bash
```

You should see an output like:

```console
root@7f2607af31c3:/app#
```

that means that you are in a `bash` session inside your container, as a `root` user, under the `/app` directory, this directory has another directory called "app" inside, that's where your code lives inside the container: `/app/app`.

There you can use the `fastapi run --reload` command to run the debug live reloading server.

```console
$ fastapi run --reload app/main.py
```

...it will look like:

```console
root@7f2607af31c3:/app# fastapi run --reload app/main.py
```

and then hit enter. That runs the live reloading server that auto reloads when it detects code changes.

Nevertheless, if it doesn't detect a change but a syntax error, it will just stop with an error. But as the container is still alive and you are in a Bash session, you can quickly restart it after fixing the error, running the same command ("up arrow" and "Enter").

...this previous detail is what makes it useful to have the container alive doing nothing and then, in a Bash session, make it run the live reload server.

## Backend Tests

To test the backend run:

```console
$ bash ./scripts/test.sh
```

The tests run with Pytest, modify and add tests to `./backend/tests/`.

If you use GitHub Actions the tests will run automatically.

### Test Organization

Tests are organized by type:
- **Unit Tests** (`tests/unit/`) - Isolated component testing with mocks
- **Integration Tests** (`tests/integration/`) - API endpoints with real database
- **Scripts Tests** (`tests/scripts/`) - Startup and utility scripts

Mark integration tests with:
```python
@pytest.mark.integration
def test_something():
    ...
```

### Test Running Stack

If your stack is already up and you just want to run the tests, you can use:

```bash
docker compose exec backend bash scripts/tests-start.sh
```

That `/app/scripts/tests-start.sh` script just calls `pytest` after making sure that the rest of the stack is running. If you need to pass extra arguments to `pytest`, you can pass them to that command and they will be forwarded.

For example, to stop on first error:

```bash
docker compose exec backend bash scripts/tests-start.sh -x
```

### Test Coverage

When the tests are run, a file `htmlcov/index.html` is generated, you can open it in your browser to see the coverage of the tests.

## Migrations

As during local development your app directory is mounted as a volume inside the container, you can also run the migrations with `alembic` commands inside the container and the migration code will be in your app directory (instead of being only inside the container). So you can add it to your git repository.

Make sure you create a "revision" of your models and that you "upgrade" your database with that revision every time you change them. As this is what will update the tables in your database. Otherwise, your application will have errors.

* Start an interactive session in the backend container:

```console
$ docker compose exec backend bash
```

* Alembic is already configured to import your SQLModel models from `./backend/app/models.py`.

* After changing a model (for example, adding a column), inside the container, create a revision, e.g.:

```console
$ alembic revision --autogenerate -m "Add column last_name to User model"
```

* Commit to the git repository the files generated in the alembic directory.

* After creating the revision, run the migration in the database (this is what will actually change the database):

```console
$ alembic upgrade head
```

### Important Notes on Migrations

**Model Imports:**
When creating migrations, ensure all models are imported in `./backend/app/alembic/env.py`:

```python
# Import all models so Alembic can detect them for autogenerate
from app.models import NewsArticle  # Add new models here
```

**Vector Indexes:**
When adding pgvector indexes, note that `CREATE INDEX CONCURRENTLY` requires running outside a transaction. For initial migrations on empty tables, omit the `postgresql_concurrently=True` parameter. See `7b5594e385cc_add_hnsw_index_to_news_articles.py` for reference.

If you don't want to use migrations at all, uncomment the lines in the file at `./backend/app/core/db.py` that end in:

```python
SQLModel.metadata.create_all(engine)
```

and comment the line in the file `scripts/prestart.sh` that contains:

```console
$ alembic upgrade head
```

If you don't want to start with the default models and want to remove them / modify them, from the beginning, without having any previous revision, you can remove the revision files (`.py` Python files) under `./backend/app/alembic/versions/`. And then create a first migration as described above.

## Dependency Injection Best Practices

**Critical Rule:** ALL dependency factories must be in `app/deps.py`.

**Why?**
- Testability: Easy to mock dependencies in unit tests
- Consistency: Same dependency graph in API routes, background scheduler, CLI scripts, and tests
- Single Responsibility: Services never instantiate their own dependencies

**Example:**

```python
# ❌ WRONG - Don't instantiate dependencies inside services
class MyService:
    def __init__(self):
        self.embeddings = EmbeddingsService()  # BAD!

# ✅ CORRECT - Inject dependencies via constructor
class MyService:
    def __init__(self, embeddings_service: EmbeddingsService):
        self.embeddings = embeddings_service

# In deps.py:
def get_my_service(
    embeddings_service: Annotated[EmbeddingsService, Depends(get_embeddings_service)]
) -> MyService:
    return MyService(embeddings_service=embeddings_service)
```

## News Source Configuration

News sources are configured via environment variables in `.env`:

```bash
RSS_DL_NEWS=https://www.dlnews.com/arc/outboundfeeds/rss/
RSS_THE_DEFIANT=https://thedefiant.io/api/feed
RSS_COINTELEGRAPH=https://cointelegraph.com/rss
```

To add a new source:
1. Add RSS URL to `.env`
2. Update `Settings.news_sources` computed field in `app/core/config.py`
3. Source will be automatically picked up by ingestion service

**Note:** This replaced the old database-driven approach (see migration `4ce808250de3`).

## Background Jobs

Background jobs are managed by APScheduler in `app/scheduler.py`:

**Ingestion Job:**
- Interval: `INGESTION_INTERVAL_MINUTES` (default: 30 minutes)
- Calls: `IngestionService.ingest_all_sources()`
- Max instances: 1 (prevents overlapping runs)

**Cleanup Job:**
- Schedule: Daily at 2 AM UTC
- Calls: `IngestionService.cleanup_old_articles()`
- Retention: `ARTICLE_CLEANUP_DAYS` (default: 90 days)

Jobs are started automatically in `main.py` lifespan context.

## API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

The OpenAPI schema includes all REST endpoints and WebSocket connections.

## Troubleshooting

### Ollama Connection Errors

If the backend fails to start with Ollama connection errors, ensure:
1. Ollama service is running: `docker compose ps ollama`
2. Check Ollama logs: `docker compose logs ollama`
3. Verify model is pulled: `docker compose exec ollama ollama list`
4. Pull required models if missing:
   ```bash
   docker compose exec ollama ollama pull nomic-embed-text
   docker compose exec ollama ollama pull llama3.2:3b
   ```

### Database Migration Errors

If migrations fail:
1. Check database connection: `docker compose ps db`
2. Ensure all models are imported in `alembic/env.py`
3. For pgvector issues, verify extension is installed: `docker compose exec db psql -U app_user -d app -c "CREATE EXTENSION IF NOT EXISTS vector;"`

### Import Errors

If you see `ModuleNotFoundError`:
1. Ensure virtual environment is activated: `source .venv/bin/activate`
2. Re-run dependency installation: `uv sync`
3. Check Python version (requires 3.10+)

## Contributing

When contributing to the backend:

1. Follow existing architectural patterns (Service Layer, Repository, DI)
2. Add all dependency factories to `deps.py`
3. Write unit tests with mocked dependencies
4. Write integration tests for API endpoints
5. Update this README if adding new features or services
6. Run code quality checks: `bash ./scripts/lint.sh`
7. Ensure all tests pass: `bash ./scripts/test.sh`

## License

See the project root for license information.
