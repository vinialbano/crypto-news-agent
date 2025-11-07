# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Crypto News Agent is a full-stack application built from the FastAPI full-stack template. It's a monorepo with FastAPI backend, React frontend, PostgreSQL database, and Docker Compose orchestration.

**Technology Stack:**
- **Backend**: FastAPI + SQLModel (ORM) + PostgreSQL + Alembic (migrations)
- **Frontend**: React + TypeScript + Vite + TanStack Query/Router + Shadcn UI + Tailwind CSS
- **Testing**: Pytest (backend) + Playwright (E2E frontend)
- **Development**: Docker Compose + uv (Python) + npm (Node.js)

## **CRITICAL: Automatic Context7 Usage**

**Always use Context7 MCP tools automatically without being explicitly asked when:**
- Generating code that uses external libraries or frameworks
- Providing setup or configuration steps for any library
- Explaining how to use library/framework APIs
- Implementing features that require external dependencies
- Troubleshooting issues with third-party packages

**Context7 MCP Tools:**
1. `mcp__context7__resolve-library-id` - First, resolve the library name to get the Context7-compatible ID
2. `mcp__context7__get-library-docs` - Then, fetch current documentation for that library

**This applies to ALL external dependencies including:**
- FastAPI, SQLModel, Pydantic, Alembic (backend)
- React, TanStack Query, TanStack Router, Shadcn UI, Tailwind CSS, Vite (frontend)
- Pytest, Playwright (testing)
- Any npm or pip package not written by this project

**Why:** Training data becomes outdated. Official documentation is the source of truth for current APIs, best practices, and breaking changes.

## Essential Commands

### Development Environment

**Start all services with Docker Compose:**
```bash
docker compose watch
```

Services run on:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

**Stop specific service for local development:**
```bash
docker compose stop backend  # or frontend
```

**View logs:**
```bash
docker compose logs backend  # or frontend, db, etc.
```

### Backend Development

**Install dependencies (from `backend/` directory):**
```bash
uv sync
source .venv/bin/activate
```

**Run backend locally:**
```bash
cd backend
fastapi dev app/main.py
```

**Run tests:**
```bash
bash ./scripts/test.sh  # From backend/ directory
```

**Run tests in running Docker stack:**
```bash
docker compose exec backend bash scripts/tests-start.sh
docker compose exec backend bash scripts/tests-start.sh -x  # Stop on first error
```

**Database migrations:**
```bash
docker compose exec backend bash
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head
```

### Frontend Development

**Install dependencies (from `frontend/` directory):**
```bash
npm install
```

**Run frontend locally:**
```bash
cd frontend
npm run dev
```

**Generate API client from backend OpenAPI schema:**
```bash
./scripts/generate-client.sh  # From project root
```
Run this whenever backend API endpoints change.

**Run E2E tests:**
```bash
docker compose up -d --wait backend
cd frontend
npx playwright test
npx playwright test --ui  # Interactive mode
```

### Code Quality

**Run pre-commit hooks manually:**
```bash
uv run pre-commit run --all-files  # From backend/
```

**Install pre-commit hooks:**
```bash
uv run pre-commit install
```

**Linting:**
```bash
bash ./scripts/lint.sh    # Backend
npm run lint              # Frontend
```

**Format code:**
```bash
bash ./scripts/format.sh  # Backend
npm run lint              # Frontend (also formats)
```

## Architecture & Code Structure

### Request Flow Architecture

```
User Request
  ↓
Frontend (React) → TanStack Query
  ↓
Generated Client (OpenAPI)
  ↓
Backend API Router (app/api/routes/)
  ↓
CRUD Layer (app/crud.py) → Business Logic
  ↓
SQLModel Models (app/models.py)
  ↓
PostgreSQL Database
```

### Backend Architecture

**Entry Point**: `backend/app/main.py`
- FastAPI app initialization
- CORS middleware configuration
- Router registration via `app.api.main.api_router`

**API Structure**: `backend/app/api/`
- `main.py`: Central router that includes all route modules
- `routes/`: Feature-based route modules (login, users, items, utils)
- `deps.py`: FastAPI dependencies (auth, DB sessions)

**Key Patterns:**
- **Dependency Injection (CRITICAL)**:
  - **ALWAYS** use FastAPI's `Depends()` for ALL external services (DB sessions, embeddings, LLM services, etc.)
  - **NEVER** instantiate services directly in route handlers or other services
  - **ALL** dependency factory functions MUST be placed in `backend/app/shared/deps.py` to prevent scope pollution
  - Keeps code clean, testable, and follows single responsibility principle
  - Example: Use `EmbeddingsServiceDep`, `IngestionServiceDep`, `RAGServiceDep` from `app.shared.deps`
- **SQLModel**: Models in `app/models.py` serve as both Pydantic schemas and SQLAlchemy tables
- **CRUD Utilities**: Database operations abstracted in `app/crud.py`
- **Configuration**: `app/core/config.py` uses Pydantic Settings; reads from `../.env`

**Database Access:**
- SQLModel provides type-safe ORM
- Sessions injected via `SessionDep` dependency
- Migrations managed by Alembic in `app/alembic/versions/`

### Frontend Architecture

**Entry Point**: `frontend/src/main.tsx`
- React app with TanStack Router
- Theme provider (next-themes)

**Structure**:
- `src/routes/`: File-based routing with TanStack Router
- `src/components/`: Reusable UI components (Shadcn UI)
- `src/client/`: Auto-generated OpenAPI client (DO NOT EDIT MANUALLY)
- `src/hooks/`: Custom React hooks

**Key Patterns:**
- **API Integration**: Use generated client from `src/client/` with TanStack Query
- **State Management**: TanStack Query for server state, React Context for UI state
- **Routing**: TanStack Router with file-based conventions
- **Styling**: Tailwind CSS with Shadcn UI components

### Configuration Management

**Primary Config**: `.env` at project root
- Contains secrets (POSTGRES_PASSWORD)
- Used by both backend and Docker Compose
- Backend reads via `backend/app/core/config.py`
- Frontend can use `VITE_*` variables

**Important Variables:**
- `PROJECT_NAME`: Displayed in UI and API docs
- `POSTGRES_PASSWORD`: Database password

## Development Workflow & Principles

This project follows the **Crypto News Agent Constitution** (see `.specify/memory/constitution.md`). Key principles:

### Principle VII: Documentation-First Development (CRITICAL)

**Automatic Context7 Usage - NO EXCEPTIONS:**

Always use Context7 MCP tools proactively when code generation, setup/configuration steps, or library documentation is needed. Do NOT wait for the user to explicitly request documentation lookup.

**Workflow:**
1. User requests feature/fix involving external library
2. **Immediately** call `mcp__context7__resolve-library-id` to get library ID
3. **Immediately** call `mcp__context7__get-library-docs` with that ID
4. Use retrieved documentation to write correct, current implementation
5. Proceed with code generation using official API patterns

**Example Scenario:**
- User: "Add pagination to the items list endpoint"
- Claude: *Automatically queries Context7 for SQLModel and FastAPI pagination docs before responding*
- Claude: Provides implementation using current, documented patterns

**Use Shadcn UI MCP server for UI components:**
- Do NOT manually create Button, Input, Dialog, Table, etc.
- Shadcn ensures consistency and accessibility
- Customize after generation if needed

### Other Key Principles

**Vertical Slice Development**: Implement features end-to-end (UI → API → DB) before moving to next feature

**Conventional Commits**: Use format `<type>(<scope>): <description>`
- Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
- Example: `feat(auth): add password reset endpoint`

**Test Standards**:
- Unit tests: >80% coverage
- Integration tests for service interactions
- E2E tests for critical user journeys
- Write tests before implementation (TDD)

**Error Handling**:
- Structured logging with context
- Graceful degradation (don't crash on failed dependencies)
- User-friendly error messages (no raw stack traces)

## Important Notes

### API Client Generation

The frontend API client (`frontend/src/client/`) is auto-generated. After backend API changes:
1. Ensure backend Docker service is running
2. Run `./scripts/generate-client.sh`
3. Commit generated files

### Database Migrations

Always create migrations for model changes:
```bash
docker compose exec backend bash
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

Migrations run automatically on container startup via `scripts/prestart.sh`.

### Docker Development Workflow

`docker-compose.override.yml` enables live-reload:
- Backend: Source code mounted, `fastapi run --reload` enabled
- Frontend: Source mounted, Vite HMR works
- This is ONLY for development; production uses built images

### VS Code Integration

Configurations exist for:
- Backend debugger with breakpoints
- Python tests via Test Explorer
- Editor uses correct virtual environment (`.venv/bin/python`)

### GitHub Spec Kit Integration

This project uses GitHub Spec Kit for specification-driven development. See `.specify/` directory:
- Constitution defines coding standards and principles
- Spec templates guide feature specifications
- Plan templates structure implementation planning

When creating features, follow the spec workflow defined in constitution and templates.

## Active Technologies
- Python 3.11+ (backend), TypeScript 5.x (frontend)
- FastAPI, LangChain, Ollama, langchain-ollama, langchain-community, pgvector-python, SQLModel, Alembic
- React, TanStack Query, TanStack Router, Shadcn UI, Tailwind CSS, Vite
- PostgreSQL 15+ with pgvector extension for vector embeddings and semantic search

## Recent Changes
- Removed production infrastructure (Sentry, unused environment variables)
- Simplified Docker configuration for local development only
- Cleaned up frontend dependencies and styling system
- Always use npm to install javascript dependencies. Never edit the package.json file directly
