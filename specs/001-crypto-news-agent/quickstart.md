# Quickstart: Crypto News Agent

**Feature**: 001-crypto-news-agent
**Audience**: Developers setting up the project for the first time
**Time to Complete**: ~30 minutes

This guide walks through setting up the complete Crypto News Agent development environment from a fresh clone.

---

## Prerequisites

Ensure you have the following installed:

- **Docker & Docker Compose**: Version 20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- **Python**: Version 3.11+ ([Install Python](https://www.python.org/downloads/))
- **Node.js**: Version 18+ ([Install Node.js](https://nodejs.org/))
- **uv**: Python package manager ([Install uv](https://github.com/astral-sh/uv#installation))
- **Ollama**: For local LLM inference ([Install Ollama](https://ollama.com/download))
- **Git**: For version control

**System Requirements**:
- 8GB+ RAM (Ollama LLMs require memory)
- 10GB+ free disk space (for Docker images and models)
- macOS, Linux, or WSL2 on Windows

---

## Step 1: Clone and Configure

### 1.1 Clone Repository

```bash
git clone https://github.com/your-org/crypto-news-agent.git
cd crypto-news-agent
git checkout 001-crypto-news-agent
```

### 1.2 Environment Configuration

Copy the example environment file and configure:

```bash
cp .env.example .env
```

Edit `.env` and set the following:

```bash
# Project Configuration
PROJECT_NAME=Crypto News Agent
ENVIRONMENT=development

# Database
POSTGRES_SERVER=db
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=changethis123  # ⚠️ Change in production!
POSTGRES_DB=crypto_news

# Security
SECRET_KEY=your-secret-key-here  # Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"

# Ollama Configuration
OLLAMA_HOST=http://ollama:11434
OLLAMA_CHAT_MODEL=llama3.1:8b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# News Sources (RSS URLs)
RSS_DL_NEWS=https://www.dlnews.com/arc/outboundfeeds/rss/
RSS_THE_DEFIANT=https://thedefiant.io/api/feed
RSS_COINTELEGRAPH=https://cointelegraph.com/rss

# Ingestion Schedule (cron format)
INGESTION_INTERVAL_MINUTES=30

# Frontend
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws/ask

# Optional: Superuser for Admin Access
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=changethis
```

---

## Step 2: Pull Ollama Models

Ollama models must be downloaded before starting the app. This can take 5-10 minutes depending on your internet speed.

### 2.1 Start Ollama Service

If you installed Ollama locally:

```bash
# macOS/Linux
ollama serve
```

Or if using Docker (recommended):

```bash
docker compose up ollama -d
```

### 2.2 Pull Required Models

```bash
# Chat model (llama3.1:8b ~ 4.7GB)
ollama pull llama3.1:8b

# Embedding model (nomic-embed-text ~ 274MB)
ollama pull nomic-embed-text
```

**Verify models are installed**:

```bash
ollama list
```

You should see:
```
NAME                    ID              SIZE      MODIFIED
llama3.1:8b             abc123def456    4.7 GB    2 minutes ago
nomic-embed-text        xyz789uvw012    274 MB    1 minute ago
```

---

## Step 3: Start Backend Services

### 3.1 Start Database and Ollama

```bash
docker compose up db ollama -d
```

**Verify services are running**:

```bash
docker compose ps
```

Expected output:
```
NAME                    STATUS          PORTS
crypto-news-agent-db-1      Up 30 seconds   0.0.0.0:5432->5432/tcp
crypto-news-agent-ollama-1  Up 30 seconds   0.0.0.0:11434->11434/tcp
```

### 3.2 Install Backend Dependencies

```bash
cd backend
uv sync
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3.3 Run Database Migrations

```bash
# Enable pgvector extension and create tables
alembic upgrade head
```

Expected output:
```
INFO  [alembic.runtime.migration] Running upgrade -> abc123, enable pgvector
INFO  [alembic.runtime.migration] Running upgrade abc123 -> def456, create news tables
```

### 3.4 Seed News Sources

```bash
# Seed the 3 configured news sources
python -m app.scripts.seed_sources
```

Expected output:
```
Created news source: DL News
Created news source: The Defiant
Created news source: Cointelegraph
✓ 3 sources seeded successfully
```

### 3.5 Run Initial News Ingestion

```bash
# Fetch first batch of articles (this may take 2-3 minutes)
python -m app.services.ingestion
```

Expected output:
```
Fetching articles from DL News...
  - Ingested 15 new articles
Fetching articles from The Defiant...
  - Ingested 12 new articles
Fetching articles from Cointelegraph...
  - Ingested 18 new articles
✓ Total: 45 articles ingested
```

### 3.6 Start Backend Server

```bash
# From backend/ directory
fastapi dev app/main.py
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Application startup complete
```

**Verify backend is running**:
- Visit http://localhost:8000/docs (Swagger UI)
- Check http://localhost:8000/api/health (should return `{"status": "healthy"}`)

---

## Step 4: Start Frontend

### 4.1 Clean Up Template (First Time Only)

The FastAPI template comes with Chakra UI and authentication components. We need to remove these first:

```bash
cd frontend

# Uninstall Chakra UI
npm uninstall @chakra-ui/react @emotion/react

# Delete Chakra UI component files
rm -rf src/components/ui/  # Old Chakra components
rm src/theme.tsx           # Chakra theme

# Delete authentication routes (not needed for MVP)
rm src/routes/login.tsx
rm src/routes/signup.tsx
rm src/routes/recover-password.tsx
rm src/routes/reset-password.tsx

# Delete template demo components
rm -rf src/routes/_layout/
rm -rf src/components/Admin/
rm -rf src/components/Items/
rm -rf src/components/UserSettings/
```

### 4.2 Install Shadcn UI

```bash
# From frontend/ directory
npx shadcn@latest init
```

You'll be prompted with configuration questions:

```
✔ Preflight checks
✔ Verifying framework. Found Vite
✔ Validating Tailwind CSS

● Where is your tailwind.config located? › tailwind.config.js
● Where is your global CSS file? › src/index.css
● Would you like to use CSS variables for theming? › yes
● Where is your components directory? › src/components/ui
● Configure import alias: › @
● Run install command? › yes
```

This installs:
- Tailwind CSS
- Radix UI primitives
- class-variance-authority (for component variants)
- clsx & tailwind-merge (for className utilities)

### 4.3 Add Required Shadcn Components

```bash
# From frontend/ directory
npx shadcn@latest add button
npx shadcn@latest add input
npx shadcn@latest add card
npx shadcn@latest add skeleton
npx shadcn@latest add alert
```

Components are copied to `src/components/ui/` and fully customizable.

### 4.4 Install Additional Dependencies

```bash
npm install zod  # For WebSocket message validation
npm install
```

### 4.5 Generate API Client

```bash
# From project root, generate TypeScript client from OpenAPI schema
./scripts/generate-client.sh
```

Expected output:
```
Generating TypeScript client from OpenAPI schema...
✓ Client generated at frontend/src/client/
```

### 4.6 Start Frontend Dev Server

```bash
# From frontend/ directory
npm run dev
```

Expected output:
```
  VITE v5.x.x  ready in 543 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

---

## Step 5: Verify Everything Works

### 5.1 Test News Browsing

1. Open http://localhost:5173 in your browser
2. Navigate to "News" page (or `/news` route)
3. You should see a list of ~45 cryptocurrency articles

### 5.2 Test Question Answering

1. On the home page, type a question: "What happened to Bitcoin today?"
2. Click "Ask" or press Enter
3. You should see:
   - WebSocket connection established
   - "Using 3 sources" message appears
   - Answer streams word-by-word
   - Complete answer displayed within ~5 seconds

### 5.3 Test Error Handling

1. Ask an unrelated question: "What is the weather like?"
2. You should see:
   - "I don't have enough information about that topic in recent news."

---

## Step 6: Run Tests

### 6.1 Backend Tests

```bash
cd backend
bash ./scripts/test.sh
```

Expected output:
```
============================= test session starts ==============================
collected 45 items

tests/unit/test_ingestion.py ............                                [ 26%]
tests/unit/test_embeddings.py .......                                    [ 42%]
tests/integration/test_rag_workflow.py .......                           [ 57%]
tests/integration/test_websocket.py ..........                           [ 80%]
tests/e2e/test_question_flow.py .........                                [100%]

============================== 45 passed in 12.34s ==============================
```

### 6.2 Frontend E2E Tests

```bash
cd frontend
npx playwright test
```

Expected output:
```
Running 8 tests using 4 workers

  ✓  [chromium] › question-answer.spec.ts:6:1 › should stream answer to question (2.3s)
  ✓  [chromium] › news-browsing.spec.ts:6:1 › should display list of news articles (1.1s)
  ✓  [firefox] › question-answer.spec.ts:6:1 › should stream answer to question (2.5s)
  ✓  [firefox] › news-browsing.spec.ts:6:1 › should display list of news articles (1.2s)

  8 passed (6.8s)
```

---

## Common Issues & Troubleshooting

### Issue: Ollama Models Not Found

**Symptoms**: Backend throws error "Model llama3.1:8b not found"

**Solution**:
```bash
# Verify models are installed
ollama list

# If missing, pull again
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

### Issue: Database Connection Failed

**Symptoms**: Backend logs show "Connection to database failed"

**Solution**:
```bash
# Check if database container is running
docker compose ps

# Restart database
docker compose restart db

# Check logs
docker compose logs db
```

### Issue: WebSocket Connection Refused

**Symptoms**: Frontend shows "WebSocket connection failed"

**Solution**:
1. Verify backend is running on port 8000
2. Check CORS settings in `backend/app/core/config.py`
3. Ensure `VITE_WS_URL` in `.env` matches backend WebSocket endpoint

### Issue: No Articles Appear in News List

**Symptoms**: News page shows empty list

**Solution**:
```bash
# Run ingestion manually
cd backend
source .venv/bin/activate
python -m app.services.ingestion

# Check database
docker compose exec db psql -U postgres -d crypto_news -c "SELECT COUNT(*) FROM news_articles;"
```

### Issue: Slow Answer Generation

**Symptoms**: WebSocket streaming takes >10 seconds to start

**Solution**:
- Check Ollama has sufficient resources (min 4GB RAM allocated)
- Use smaller model: `OLLAMA_CHAT_MODEL=llama3.2:3b` in `.env`
- Verify semantic search is fast: Test `GET /api/news` response time

---

## Development Workflow

### Start All Services with Docker Compose

For convenience, you can run everything in Docker:

```bash
docker compose watch
```

This starts all services with live-reload:
- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:5173
- **Database**: localhost:5432
- **Ollama**: http://localhost:11434
- **Adminer** (DB UI): http://localhost:8080

### Stop All Services

```bash
docker compose down
```

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f db
```

### Trigger Manual News Ingestion

```bash
# From backend with virtual env activated
python -m app.services.ingestion
```

Or via API:

```bash
curl -X POST http://localhost:8000/api/admin/ingest
```

---

## Next Steps

Now that your development environment is set up:

1. **Review the codebase structure** in [plan.md](./plan.md)
2. **Explore API contracts** in [contracts/](./contracts/)
3. **Read the data model** in [data-model.md](./data-model.md)
4. **Review research findings** in [research.md](./research.md)
5. **Check tasks for implementation** in `tasks.md` (generated via `/speckit.tasks`)

### Recommended First Tasks

- Add more news sources (edit `.env` and seed_sources.py)
- Customize LLM prompt template (edit `backend/app/services/rag.py`)
- Improve UI styling (edit `frontend/src/components/`)
- Add pagination to news list (update REST API and frontend)

---

## Docker Compose Services Reference

| Service | Port | Purpose |
|---------|------|---------|
| `db` | 5432 | PostgreSQL 15 with pgvector |
| `ollama` | 11434 | Ollama LLM server |
| `backend` | 8000 | FastAPI application |
| `frontend` | 5173 | Vite dev server |
| `adminer` | 8080 | Database admin UI |

---

## Useful Commands Cheat Sheet

```bash
# Backend
cd backend && uv sync                    # Install dependencies
alembic upgrade head                     # Run migrations
alembic revision --autogenerate -m "..." # Create migration
fastapi dev app/main.py                  # Start dev server
bash ./scripts/test.sh                   # Run tests
bash ./scripts/lint.sh                   # Lint code
bash ./scripts/format.sh                 # Format code

# Frontend
cd frontend && npm install               # Install dependencies
npm run dev                              # Start dev server
npx playwright test                      # Run E2E tests
npm run lint                             # Lint & format

# Docker
docker compose up -d                     # Start all services
docker compose watch                     # Start with live-reload
docker compose down                      # Stop all services
docker compose logs -f backend           # View backend logs
docker compose exec backend bash         # Shell into backend container
docker compose exec db psql -U postgres  # PostgreSQL shell

# Ollama
ollama list                              # List installed models
ollama pull <model>                      # Download model
ollama run llama3.1:8b                   # Test model interactively
```

---

**Quickstart Phase Status**: ✅ COMPLETE

Complete setup guide from clone to working application, with common issues and development workflow.
