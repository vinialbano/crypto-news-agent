# Template Cleanup Analysis: FastAPI Full Stack Template

**Feature**: 001-crypto-news-agent
**Date**: 2025-11-05
**Purpose**: Identify components to keep, remove, or modify from the FastAPI full stack template

---

## Executive Summary

The current repository is forked from the FastAPI full stack template, which includes user authentication, CRUD operations for "items", and a complete admin interface. For the Crypto News Agent application, we need to:

1. **Remove**: User management, Items CRUD, authentication (for MVP)
2. **Keep**: Core infrastructure (DB, migrations, API structure)
3. **Add**: News ingestion, vector search, WebSocket streaming, LangChain integration

---

## Backend Analysis

### ✅ Components to KEEP

#### Core Infrastructure
- **`backend/app/core/db.py`** - Database connection and session management
- **`backend/app/core/config.py`** - Pydantic Settings (extend for Ollama, RSS URLs)
- **`backend/app/api/deps.py`** - Dependency injection patterns (SessionDep)
- **`backend/app/api/main.py`** - API router registration
- **`backend/app/alembic/`** - Migration framework (will add pgvector migration)
- **`backend/app/main.py`** - FastAPI app initialization
- **`backend/app/backend_pre_start.py`** - Pre-start checks (adapt for Ollama)

#### Utilities
- **`backend/app/utils.py`** - Generic utilities (if needed)
- **`backend/scripts/test.sh`** - Test execution script
- **`backend/scripts/format.sh`** - Code formatting
- **`backend/scripts/lint.sh`** - Linting

---

### ❌ Components to REMOVE

#### User Management (Not needed for MVP)
- **`backend/app/models.py`** - User, UserCreate, UserUpdate, UserPublic models
  - **Action**: Delete User models, keep Message model, remove Item models

- **`backend/app/api/routes/users.py`** - User CRUD endpoints
  - **Action**: Delete entire file

- **`backend/app/api/routes/login.py`** - Authentication endpoints
  - **Action**: Delete entire file (no auth for MVP)

- **`backend/app/core/security.py`** - Password hashing, JWT tokens
  - **Action**: Delete entire file (no auth for MVP)

#### Items Management (Template demo feature)
- **`backend/app/api/routes/items.py`** - Items CRUD endpoints
  - **Action**: Delete entire file

- **Item models in `backend/app/models.py`**
  - **Action**: Remove ItemBase, ItemCreate, ItemUpdate, Item, ItemPublic, ItemsPublic

#### Admin/Private Routes
- **`backend/app/api/routes/private.py`** - Admin-only endpoints
  - **Action**: Delete entire file

#### Initial Data Seeding
- **`backend/app/initial_data.py`** - Creates first superuser
  - **Action**: Replace with news source seeding script

---

### 🔧 Components to MODIFY

#### Models (`backend/app/models.py`)
**Current**: User, Item models
**New**: NewsArticle, NewsSource models

```python
# REMOVE: User, UserCreate, UserUpdate, Item, etc.
# KEEP: Message, Token (if adding auth later)
# ADD: NewsArticle, NewsSource, StreamMessage (Pydantic models)
```

#### Configuration (`backend/app/core/config.py`)
**Add fields**:
```python
class Settings(BaseSettings):
    # Existing fields (keep DATABASE_URI, BACKEND_CORS_ORIGINS, etc.)

    # Add new fields for Crypto News Agent
    OLLAMA_HOST: str = "http://ollama:11434"
    OLLAMA_CHAT_MODEL: str = "llama3.1:8b"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"

    RSS_DL_NEWS: str = "https://www.dlnews.com/arc/outboundfeeds/rss/"
    RSS_THE_DEFIANT: str = "https://thedefiant.io/api/feed"
    RSS_COINTELEGRAPH: str = "https://cointelegraph.com/rss"

    INGESTION_INTERVAL_MINUTES: int = 30
    SEMANTIC_SEARCH_THRESHOLD: float = 0.5

    # Remove: FIRST_SUPERUSER, FIRST_SUPERUSER_PASSWORD (no auth)
```

#### API Routes (`backend/app/api/main.py`)
**Current**:
```python
api_router.include_router(login.router, tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(items.router, prefix="/items", tags=["items"])
api_router.include_router(utils.router, prefix="/utils", tags=["utils"])
```

**New**:
```python
api_router.include_router(news.router, prefix="/news", tags=["news"])
api_router.include_router(sources.router, prefix="/sources", tags=["sources"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
# WebSocket registered directly in main.py
```

#### Pre-start Script (`backend/app/backend_pre_start.py`)
**Add**: Check Ollama connectivity, verify models exist

---

### ➕ Components to ADD

#### Services Directory (`backend/app/services/`)
```
services/
├── __init__.py
├── ingestion.py          # RSS feed fetching and parsing
├── embeddings.py         # Ollama embeddings generation
├── rag.py                # LangChain RAG workflow
└── scheduler.py          # APScheduler for periodic ingestion
```

#### WebSocket Route (`backend/app/api/routes/questions.py`)
- WebSocket endpoint `/ws/ask`
- Streaming LLM responses

#### CRUD Operations (`backend/app/crud.py`)
**Replace existing**: User/Item CRUD
**Add new**: NewsArticle, NewsSource CRUD with vector search

#### Alembic Migration
**Add**: Enable pgvector extension, create news_articles and news_sources tables

---

## Frontend Analysis

### ✅ Components to KEEP

#### Core Infrastructure
- **`frontend/src/main.tsx`** - App entry point
- **`frontend/src/routes/__root.tsx`** - Root layout
- **`frontend/src/client/`** - Generated OpenAPI client (will regenerate)
- **`frontend/vite.config.ts`** - Vite configuration
- **`frontend/tsconfig.json`** - TypeScript configuration

#### Common Components (if reusable)
- **`frontend/src/components/Common/Navbar.tsx`** - May adapt for news app branding
- **`frontend/src/components/Common/NotFound.tsx`** - 404 page

---

### ❌ Components to REMOVE

#### Chakra UI Components (Switching to Shadcn UI)
- **`frontend/src/components/ui/`** - ALL Chakra UI wrapper components
  - `button.tsx`, `dialog.tsx`, `field.tsx`, `input-group.tsx`, etc.
  - **Action**: Delete entire `ui/` directory, replace with Shadcn UI components

- **`frontend/src/theme.tsx`** - Chakra UI theme configuration
  - **Action**: Delete (Shadcn UI uses Tailwind CSS + CSS variables)

- **`frontend/src/components/ui/provider.tsx`** - Chakra UI provider
  - **Action**: Delete (Shadcn doesn't need a provider, uses standard React components)

#### User Management UI
- **`frontend/src/routes/login.tsx`** - Login page
- **`frontend/src/routes/signup.tsx`** - Signup page
- **`frontend/src/routes/recover-password.tsx`** - Password recovery
- **`frontend/src/routes/reset-password.tsx`** - Password reset
- **`frontend/src/components/UserSettings/`** - User profile settings
- **`frontend/src/components/Admin/`** - Admin user management
  - **Action**: Delete all authentication-related routes and components

#### Items Management UI
- **`frontend/src/routes/_layout/items.tsx`** - Items list page
- **`frontend/src/components/Items/`** - AddItem, EditItem, DeleteItem components
  - **Action**: Delete all items-related components

#### Layout Components (Auth-dependent)
- **`frontend/src/routes/_layout.tsx`** - Protected layout with auth
- **`frontend/src/routes/_layout/`** - Protected pages (settings, admin, items)
  - **Action**: Delete protected layout, simplify to public-only routes

---

### 🔧 Components to MODIFY

#### Package.json
**Remove dependencies**:
```json
{
  "dependencies": {
    // REMOVE:
    "@chakra-ui/react": "^3.27.0",
    "@emotion/react": "^11.14.0",

    // KEEP:
    "@tanstack/react-query": "^5.90.2",
    "@tanstack/react-router": "^1.131.50",
    "axios": "1.12.2",
    "react": "^19.1.1",
    "react-dom": "^19.2.0",
    "react-hook-form": "7.62.0",

    // ADD:
    "zod": "^3.23.8"  // For WebSocket message validation
  }
}
```

**Add Shadcn UI dependencies**:
```bash
npx shadcn@latest init
# This will add:
# - tailwindcss
# - class-variance-authority
# - clsx
# - tailwind-merge
# - @radix-ui/* components as needed
```

#### Root Layout (`frontend/src/routes/__root.tsx`)
**Current**: Wraps with Chakra UI Provider
**New**: Remove Chakra Provider, add Shadcn/Tailwind setup

---

### ➕ Components to ADD

#### Routes (`frontend/src/routes/`)
```
routes/
├── __root.tsx            # Modify: Remove Chakra, add Shadcn
├── index.tsx             # NEW: Home page with question input
└── news.tsx              # NEW: News browsing page
```

#### Components (`frontend/src/components/`)
```
components/
├── QuestionInput.tsx     # NEW: Question form with WebSocket
├── StreamingAnswer.tsx   # NEW: Displays streaming LLM response
├── NewsList.tsx          # NEW: News article list
└── ui/                   # NEW: Shadcn UI components (generated via CLI)
    ├── button.tsx
    ├── input.tsx
    ├── card.tsx
    └── ... (as needed)
```

#### Hooks (`frontend/src/hooks/`)
```
hooks/
├── useWebSocketQuery.ts  # NEW: TanStack Query hook for WebSocket
└── useNews.ts            # NEW: Fetch news articles
```

#### Lib (`frontend/src/lib/`)
```
lib/
├── utils.ts              # NEW: cn() helper for Tailwind classes
└── websocket.ts          # NEW: WebSocket connection utilities
```

---

## Dependency Changes Summary

### Backend - REMOVE
```bash
# No specific removals needed, template dependencies are minimal
# Just don't install any auth-related extras
```

### Backend - ADD
```bash
uv add langchain langchain-community langchain-ollama
uv add pgvector
uv add feedparser  # For RSS parsing if not using WebBaseLoader
uv add apscheduler  # For scheduled ingestion
```

### Frontend - REMOVE
```bash
npm uninstall @chakra-ui/react @emotion/react
```

### Frontend - ADD
```bash
# Shadcn UI init (includes Tailwind, Radix UI primitives)
npx shadcn@latest init

# Additional dependencies
npm install zod  # WebSocket message validation
```

---

## Migration Checklist

### Phase 1: Backend Cleanup
- [ ] Delete `backend/app/api/routes/users.py`
- [ ] Delete `backend/app/api/routes/login.py`
- [ ] Delete `backend/app/api/routes/items.py`
- [ ] Delete `backend/app/api/routes/private.py`
- [ ] Delete `backend/app/core/security.py`
- [ ] Clean up `backend/app/models.py` (remove User, Item models)
- [ ] Update `backend/app/api/main.py` (remove old routers)
- [ ] Update `backend/app/core/config.py` (add Ollama, RSS config)

### Phase 2: Backend Additions
- [ ] Create `backend/app/services/` directory with new services
- [ ] Add NewsArticle, NewsSource models to `backend/app/models.py`
- [ ] Create Alembic migration for pgvector + new tables
- [ ] Add news, sources, health API routes
- [ ] Add WebSocket route for questions
- [ ] Update `backend/app/backend_pre_start.py` for Ollama checks

### Phase 3: Frontend Cleanup
- [ ] Delete `frontend/src/components/ui/` (all Chakra components)
- [ ] Delete `frontend/src/theme.tsx`
- [ ] Delete `frontend/src/routes/login.tsx`, `signup.tsx`, etc.
- [ ] Delete `frontend/src/routes/_layout.tsx` and `_layout/` directory
- [ ] Delete `frontend/src/components/Admin/`
- [ ] Delete `frontend/src/components/Items/`
- [ ] Delete `frontend/src/components/UserSettings/`
- [ ] Uninstall Chakra UI from `package.json`

### Phase 4: Frontend Additions
- [ ] Run `npx shadcn@latest init` to setup Shadcn UI
- [ ] Add Shadcn components as needed (button, input, card, etc.)
- [ ] Create new routes: `index.tsx`, `news.tsx`
- [ ] Create new components: QuestionInput, StreamingAnswer, NewsList
- [ ] Create hooks: useWebSocketQuery, useNews
- [ ] Add Zod schemas for validation
- [ ] Update `__root.tsx` to remove Chakra Provider

---

## File Count Summary

### Backend
- **Files to Delete**: 5 (users.py, login.py, items.py, private.py, security.py)
- **Files to Modify**: 4 (models.py, main.py, config.py, backend_pre_start.py)
- **Files to Add**: ~10 (services/, new routes, CRUD, migrations)

### Frontend
- **Files to Delete**: ~35 (all Chakra UI components, all auth routes/components, items components)
- **Files to Modify**: 3 (__root.tsx, package.json, vite.config.ts)
- **Files to Add**: ~15 (new routes, components, hooks, Shadcn UI components)

---

## Risk Assessment

### Low Risk
- ✅ Deleting unused routes/components (no dependencies on them for new features)
- ✅ Switching from Chakra to Shadcn (both are component libraries, no architectural change)
- ✅ Removing authentication (not needed for MVP, can add later)

### Medium Risk
- ⚠️ Modifying `models.py` - ensure migrations are clean
- ⚠️ Updating `config.py` - ensure all new env vars have defaults

### High Risk
- ❌ None identified (template is clean starting point)

---

## Shadcn UI vs Chakra UI

### Why Shadcn UI?

| Feature | Chakra UI | Shadcn UI |
|---------|-----------|-----------|
| **Philosophy** | Component library (runtime) | Copy-paste components (build-time) |
| **Bundle Size** | Larger (runtime JS) | Smaller (only what you use) |
| **Customization** | Theme tokens | Direct code editing |
| **Dependencies** | @chakra-ui/react + Emotion | Tailwind + Radix UI primitives |
| **Performance** | Good | Excellent (no runtime overhead) |
| **TypeScript** | Good | Excellent (full control) |
| **Accessibility** | Built-in | Built-in (via Radix UI) |

**Decision**: Shadcn UI is more modern, gives full control over components, and aligns with the lightweight approach. No provider needed, just import components.

---

## Next Steps

1. **Execute cleanup**: Follow migration checklist phases 1-4
2. **Test baseline**: Ensure app starts with minimal template after cleanup
3. **Add features**: Implement news ingestion, vector search, WebSocket streaming
4. **Integrate Shadcn UI**: Add components as needed during feature development

---

**Template Cleanup Analysis Status**: ✅ COMPLETE

Comprehensive analysis of what to keep, remove, and modify from the FastAPI full stack template for the Crypto News Agent application.
