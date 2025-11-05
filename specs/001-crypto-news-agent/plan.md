# Implementation Plan: Crypto News Agent

**Branch**: `001-crypto-news-agent` | **Date**: 2025-11-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-crypto-news-agent/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build an LLM-powered web application that ingests cryptocurrency news from RSS feeds, stores article vectors in PostgreSQL with pgvector, and provides real-time AI-generated answers to user questions via WebSocket streaming. The system uses FastAPI for the backend API with WebSocket support, LangChain for document processing and RAG workflows, Ollama for local LLM inference, PostgreSQL with pgvector for semantic search, and a React frontend with TanStack Query for real-time streaming responses.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5.x (frontend)
**Primary Dependencies**: FastAPI, LangChain, Ollama, langchain-ollama, langchain-community, pgvector-python, SQLModel, Alembic, React, TanStack Query, Shadcn UI, Tailwind CSS, Vite, Zod
**Storage**: PostgreSQL 15+ with pgvector extension for vector embeddings and semantic search
**Testing**: pytest (backend unit/integration), Playwright (E2E frontend)
**Target Platform**: Linux/macOS server (Docker), modern web browsers
**Project Type**: Web application (backend + frontend)
**Performance Goals**: <5s answer streaming initiation, handle 100 concurrent WebSocket connections, ingest news every 15-30 minutes
**Constraints**: <200ms p95 for semantic search queries, streaming word-by-word with no perceived delays, 95% successful news ingestion rate
**Scale/Scope**: 3 news sources, ~1000 articles stored (30-day retention), support 100 concurrent users, semantic search over vector embeddings

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Code Quality and Structure
- ✅ **Type Safety**: Python with Pydantic/SQLModel type hints; TypeScript strict mode
- ✅ **Modularity**: Services separated (news ingestion, vector storage, LLM query, WebSocket streaming)
- ✅ **Separation of Concerns**: API routes, CRUD operations, LangChain workflows, React components properly separated
- ✅ **Documentation**: All public APIs and LLM workflows will be documented

### Principle II: End-to-End Functionality
- ✅ **Vertical Slices**: Each user story (question answering, news browsing, ingestion) implemented end-to-end
- ✅ **API-First Design**: WebSocket endpoints and REST APIs defined before frontend integration
- ✅ **Integration Validation**: E2E tests for complete question → answer → streaming flow

### Principle III: User Experience and Responsiveness
- ✅ **Performance Budgets**: <5s for answer streaming, <200ms for semantic search (p95)
- ✅ **Loading States**: WebSocket connection states, streaming indicators, news ingestion status
- ✅ **Error Feedback**: User-friendly messages for no results, failed ingestion, LLM unavailability
- ✅ **Responsive Design**: Shadcn UI components (built on Radix UI + Tailwind CSS) support mobile/tablet/desktop viewports

### Principle IV: Testing Standards
- ✅ **Test Pyramid**: Unit tests for CRUD/ingestion logic, integration tests for LangChain workflows, E2E for streaming
- ✅ **Test-First Approach**: Write tests for semantic search, embedding generation, WebSocket streaming before implementation
- ✅ **Performance Testing**: Benchmark vector search queries and concurrent WebSocket connections

### Principle V: Error Handling and Scalability
- ✅ **Graceful Degradation**: Failed news sources don't crash ingestion, LLM timeout returns friendly message
- ✅ **Structured Logging**: All ingestion attempts, LLM queries, and errors logged with context
- ✅ **Retry Logic**: RSS feed fetching retries with exponential backoff
- ✅ **Horizontal Scalability**: Stateless FastAPI backend enables horizontal scaling
- ✅ **Database Optimization**: pgvector HNSW indexes for fast similarity search

### Principle VI: Version Control and Commit Discipline
- ✅ **Conventional Commits**: All commits follow format (e.g., `feat(ingestion): add RSS feed parser`)
- ✅ **Feature Branch Workflow**: Development on `001-crypto-news-agent` branch
- ✅ **Pull Request Discipline**: PR will include description, testing notes, constitution compliance

### Principle VII: Documentation-First Development
- ✅ **Context7 Usage**: All external library documentation fetched via Context7 MCP (FastAPI WebSockets, LangChain, Ollama, pgvector, TanStack Query)
- ✅ **Shadcn UI**: UI components (Input, Button, Card, WebSocket indicators) generated from Shadcn UI MCP server (copy-paste approach, full customization)
- ✅ **Version-Specific Docs**: Used specific library IDs for current API patterns

**Gate Status**: ✅ PASSED - All principles addressed, no violations requiring justification

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── news.py           # News article endpoints (GET /api/news)
│   │   │   ├── questions.py      # WebSocket endpoint (/ws/ask)
│   │   │   ├── history.py        # Chat history endpoints (GET /api/history)
│   │   │   └── health.py         # Health check endpoint
│   │   ├── deps.py               # FastAPI dependencies (DB session, auth)
│   │   └── main.py               # API router registration
│   ├── core/
│   │   ├── config.py             # Settings (Pydantic Settings)
│   │   └── security.py           # Security utilities
│   ├── models.py                 # SQLModel models (NewsArticle, NewsSource, Question, Answer, AnswerSourceArticle)
│   ├── crud.py                   # Database operations
│   ├── services/
│   │   ├── ingestion.py          # RSS feed ingestion service
│   │   ├── embeddings.py         # Ollama embeddings generation
│   │   ├── rag.py                # LangChain RAG workflow
│   │   ├── chat_history.py       # Chat history persistence during streaming
│   │   └── scheduler.py          # Background task scheduler (ingestion)
│   ├── alembic/
│   │   └── versions/             # Database migrations (pgvector extension)
│   └── main.py                   # FastAPI app initialization
├── tests/
│   ├── unit/
│   │   ├── test_ingestion.py
│   │   ├── test_embeddings.py
│   │   └── test_crud.py
│   ├── integration/
│   │   ├── test_rag_workflow.py
│   │   └── test_websocket.py
│   └── e2e/
│       └── test_question_flow.py
└── scripts/
    ├── prestart.sh               # Run migrations, check Ollama connectivity
    └── test.sh

frontend/
├── src/
│   ├── routes/                   # TanStack Router file-based routing
│   │   ├── __root.tsx
│   │   ├── index.tsx             # Home page (question input)
│   │   ├── news.tsx              # News browsing page
│   │   └── history.tsx           # Chat history page
│   ├── components/
│   │   ├── ui/                   # Shadcn UI components
│   │   ├── QuestionInput.tsx    # Question form with WebSocket
│   │   ├── StreamingAnswer.tsx  # Displays streaming LLM response
│   │   ├── NewsList.tsx         # News article list
│   │   ├── HistoryList.tsx      # Chat history list
│   │   └── HistoryCard.tsx      # Individual Q&A display card
│   ├── hooks/
│   │   ├── useWebSocketQuery.ts # TanStack Query hook for WebSocket
│   │   ├── useNews.ts           # Fetch news articles
│   │   └── useHistory.ts        # Fetch chat history
│   ├── client/                   # Auto-generated OpenAPI client
│   ├── lib/
│   │   └── websocket.ts         # WebSocket connection utilities
│   └── main.tsx                  # App entry point
├── tests/
│   └── e2e/
│       ├── question-answer.spec.ts
│       └── news-browsing.spec.ts
└── package.json

.env                              # Environment variables (Ollama host, DB credentials)
docker-compose.yml                # PostgreSQL + pgvector, Ollama service
```

**Structure Decision**: Web application structure (Option 2) selected. Backend follows existing FastAPI template layout with additions for: (1) services/ directory for ingestion, embeddings, RAG workflows; (2) WebSocket route for streaming; (3) LangChain integration. Frontend follows existing React + TanStack template but **removes Chakra UI** in favor of **Shadcn UI** (Tailwind CSS + Radix UI primitives). Authentication and Items CRUD removed as not needed for MVP. See `template-cleanup-analysis.md` for detailed migration plan.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
