# Crypto News Agent

A RAG-powered crypto news aggregator with intelligent question answering using local LLMs. The system automatically ingests news from multiple crypto sources and enables natural language queries about recent developments in the crypto space.

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
- **FastAPI** - Modern async Python web framework
- **SQLModel** - Type-safe ORM (Pydantic + SQLAlchemy)
- **PostgreSQL + pgvector** - Database with vector similarity search
- **Ollama** - Local LLM server (nomic-embed-text for embeddings, qwen2.5 for chat)
- **LangChain** - Framework for RAG and LLM applications
- **APScheduler** - Background job scheduling

### Frontend
- **React + TypeScript** - Modern frontend with hooks and Vite
- **TanStack Query & Router** - Data fetching and routing
- **Chakra UI** - Component library with dark mode
- **Playwright** - End-to-end testing

### Infrastructure
- **Docker Compose** - Development and production deployment
- **Traefik** - Reverse proxy with automatic HTTPS
- **pytest** - Comprehensive test suite (unit, integration, E2E)

## Architecture Overview

The system follows a clean, service-oriented architecture:

```
Frontend (React)
    ↓
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

For detailed architecture documentation, see [backend/README.md](./backend/README.md).

## Quick Start

### Prerequisites

- [Docker](https://www.docker.com/) and Docker Compose
- [uv](https://docs.astral.sh/uv/) for Python development (optional, for local development)

### 1. Clone and Configure

Clone the repository:

```bash
git clone git@github.com:vinialbano/crypto-news-agent
cd crypto-news-agent
```

Configure environment variables in `.env`:

```bash
# Generate secure keys
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Update .env with secure values
SECRET_KEY=<generated-key>
FIRST_SUPERUSER_PASSWORD=<strong-password>
POSTGRES_PASSWORD=<strong-password>

# News source RSS URLs (pre-configured)
RSS_DL_NEWS=https://www.dlnews.com/arc/outboundfeeds/rss/
RSS_THE_DEFIANT=https://thedefiant.io/api/feed
RSS_COINTELEGRAPH=https://cointelegraph.com/rss
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
- **Adminer**: Database UI on port 8080

### 3. Access the Application

**Frontend**: Open http://localhost:5173

**API Documentation**: http://localhost:8000/docs

**Default Login**:
- Email: `admin@example.com` (configurable via `FIRST_SUPERUSER`)
- Password: Set in `.env` as `FIRST_SUPERUSER_PASSWORD`

### 4. Ask Questions About Crypto News

Once articles are ingested (happens automatically every 30 minutes, or trigger manually via API), you can:

1. Navigate to the questions page in the frontend
2. Ask natural language questions like:
   - "What are the latest developments in Bitcoin?"
   - "Tell me about recent Ethereum updates"
   - "What happened with DeFi this week?"
3. Get streaming AI responses with source citations

## Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Security
SECRET_KEY=changethis                    # Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=changethis

# Database
POSTGRES_SERVER=db
POSTGRES_USER=app_user
POSTGRES_PASSWORD=changethis
POSTGRES_DB=app

# Ollama LLM
OLLAMA_HOST=http://ollama:11434
OLLAMA_CHAT_MODEL=qwen2.5:latest
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# News Sources (RSS URLs)
RSS_DL_NEWS=https://www.dlnews.com/arc/outboundfeeds/rss/
RSS_THE_DEFIANT=https://thedefiant.io/api/feed
RSS_COINTELEGRAPH=https://cointelegraph.com/rss

# Ingestion Settings
INGESTION_INTERVAL_MINUTES=30            # How often to fetch news
ARTICLE_CLEANUP_DAYS=90                  # Delete articles older than N days

# RAG Settings
RAG_DISTANCE_THRESHOLD=0.5               # Relevance threshold for semantic search
RAG_TOP_K_ARTICLES=5                     # Number of articles to use as context
RAG_MAX_CONTEXT_LENGTH=8000              # Max characters in LLM context

# WebSocket Settings
WS_MAX_QUESTIONS_PER_MINUTE=10          # Rate limit per client
WS_TIMEOUT_SECONDS=180                   # Connection timeout
```

### Adding New News Sources

To add a new RSS feed:

1. Add the RSS URL to `.env`:
   ```bash
   RSS_NEW_SOURCE=https://newssite.com/rss
   ```

2. Update `backend/app/core/config.py` to include the new source in the `news_sources` computed field

3. Restart the backend service

## Development

### Backend Development

Backend is built with FastAPI + SQLModel + Ollama.

**Documentation**: [backend/README.md](./backend/README.md)

**Key directories**:
- `backend/app/models.py` - Database models
- `backend/app/routes.py` - API endpoints
- `backend/app/services/` - Business logic (ingestion, RAG, embeddings)
- `backend/app/deps.py` - Dependency injection
- `backend/tests/` - Unit, integration, and E2E tests

**Run tests**:
```bash
cd backend
bash ./scripts/test.sh
```

### Frontend Development

Frontend is built with React + TypeScript + Chakra UI.

**Documentation**: [frontend/README.md](./frontend/README.md)

**Key directories**:
- `frontend/src/routes/` - File-based routing (TanStack Router)
- `frontend/src/components/` - Reusable UI components
- `frontend/src/client/` - Auto-generated API client (DO NOT EDIT)

**Generate API client** (after backend changes):
```bash
./scripts/generate-client.sh
```

### Docker Compose Development

The `docker-compose.override.yml` file enables hot-reloading for local development:
- Backend: `fastapi run --reload` auto-restarts on code changes
- Frontend: Vite HMR provides instant updates
- Database: Data persists in Docker volume

**View logs**:
```bash
docker compose logs -f backend    # Backend logs
docker compose logs -f frontend   # Frontend logs
docker compose logs -f ollama     # LLM server logs
```

**Restart services**:
```bash
docker compose restart backend
docker compose restart frontend
```

## Services

### Available Services

- **backend** - FastAPI application (port 8000)
- **frontend** - React application (port 5173)
- **db** - PostgreSQL with pgvector (port 5432)
- **ollama** - Local LLM server (port 11434)
- **adminer** - Database management UI (port 8080)
- **mailcatcher** - Email testing UI (port 1080)
- **proxy** - Traefik reverse proxy (port 80, 8090)

### Checking Service Status

```bash
docker compose ps                  # List all services
docker compose logs <service>      # View logs
docker compose exec <service> bash # Enter service container
```

## Testing

### Run All Tests

```bash
# Backend tests (unit + integration)
cd backend
bash ./scripts/test.sh

# Frontend E2E tests
cd frontend
npx playwright test
```

### Test in Running Stack

```bash
# Backend tests in Docker
docker compose exec backend bash scripts/tests-start.sh

# Stop on first error
docker compose exec backend bash scripts/tests-start.sh -x

# Run specific test
docker compose exec backend pytest tests/unit/test_rag_service.py -v
```

### Test Coverage

After running tests, view coverage reports:
- Backend: `backend/htmlcov/index.html`
- Frontend: `frontend/coverage/index.html`

## API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Key endpoints:
- `GET /news/` - List recent articles
- `POST /news/ingest/` - Trigger manual ingestion
- `GET /news/sources` - List configured news sources
- `WebSocket /ask` - Real-time question answering

## Deployment

For production deployment instructions, see [deployment.md](./deployment.md).

Key steps:
1. Remove `docker-compose.override.yml` (development only)
2. Set secure `SECRET_KEY`, `POSTGRES_PASSWORD`, and `FIRST_SUPERUSER_PASSWORD`
3. Configure `SENTRY_DSN` for error tracking (optional)
4. Use `fastapi run` instead of `fastapi run --reload`
5. Set up reverse proxy with HTTPS (Traefik included)
6. Configure backup strategy for PostgreSQL + pgvector data

## Troubleshooting

### Ollama Models Not Found

If you see "model not found" errors:

```bash
# Check available models
docker compose exec ollama ollama list

# Pull required models
docker compose exec ollama ollama pull nomic-embed-text
docker compose exec ollama ollama pull qwen2.5:latest
```

### Database Connection Issues

```bash
# Check database is running
docker compose ps db

# View database logs
docker compose logs db

# Connect to database
docker compose exec db psql -U app_user -d app
```

### Backend Won't Start

```bash
# View backend logs
docker compose logs backend

# Common issues:
# 1. Check Ollama is running: docker compose ps ollama
# 2. Check database is healthy: docker compose ps db
# 3. Verify .env configuration
# 4. Rebuild if dependencies changed: docker compose build backend
```

### Frontend Can't Connect to Backend

- Ensure backend is running: `docker compose ps backend`
- Check backend health: `curl http://localhost:8000/docs`
- Regenerate API client if backend changed: `./scripts/generate-client.sh`

## Project Structure

```
crypto-news-agent/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── main.py      # Application entry point
│   │   ├── routes.py    # API endpoints
│   │   ├── models.py    # Database models
│   │   ├── services/    # Business logic
│   │   ├── core/        # Configuration & database
│   │   └── alembic/     # Database migrations
│   ├── tests/           # Unit, integration, E2E tests
│   └── README.md        # Backend documentation
├── frontend/            # React frontend
│   ├── src/
│   │   ├── routes/      # Page components
│   │   ├── components/  # Reusable UI components
│   │   └── client/      # Auto-generated API client
│   └── README.md        # Frontend documentation
├── docker-compose.yml   # Production Docker config
├── docker-compose.override.yml  # Development overrides
├── .env                 # Environment configuration
└── README.md           # This file
```

## Contributing

When contributing:

1. Follow existing code patterns and architecture
2. Write tests for new features (unit + integration)
3. Update documentation for significant changes
4. Run linters before committing:
   ```bash
   # Backend
   cd backend
   bash ./scripts/lint.sh

   # Frontend
   cd frontend
   npm run lint
   ```
5. Ensure all tests pass:
   ```bash
   cd backend && bash ./scripts/test.sh
   cd frontend && npx playwright test
   ```

## License

The Full Stack FastAPI Template (which this project is based on) is licensed under the terms of the MIT license.

## Credits

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [React](https://react.dev/) - UI library
- [Ollama](https://ollama.ai/) - Local LLM server
- [LangChain](https://www.langchain.com/) - LLM application framework
- [pgvector](https://github.com/pgvector/pgvector) - Vector similarity search for PostgreSQL

Based on [FastAPI Full Stack Template](https://github.com/fastapi/full-stack-fastapi-template) by Sebastián Ramírez.
