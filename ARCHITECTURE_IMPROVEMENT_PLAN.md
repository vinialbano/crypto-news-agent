# Backend Architecture Improvement Plan

**Date**: 2025-11-06
**Status**: Planning
**Priority**: High

---

## 📊 Executive Summary

The codebase follows a solid **Vertical Slice Architecture** with good separation between `news` and `questions` domains. However, there are critical violations in session management, dependency injection for scheduled jobs, and some misplaced components that blur architectural boundaries.

**Current Architecture Quality: 6.75/10**
**Target Architecture Quality: 8.5/10**

---

## 🎯 Core Issues Identified

### Critical Problems (Must Fix)

1. **Session Management Chaos**
   - Repositories auto-commit (removes transaction control from callers)
   - Services call `repository.session.rollback()` (violates encapsulation)
   - No clear transaction boundaries
   - **Impact**: Cannot compose multi-repository transactions, tight coupling, unpredictable behavior

2. **Broken Scheduler Dependency Injection**
   - `create_ingestion_service()` and `create_rag_service()` use `Depends()` outside FastAPI context
   - Manual DB lifecycle management with generator gymnastics
   - Unused session variables
   - **Impact**: Pattern doesn't actually work as intended, confusing for developers, fragile

3. **Embeddings Misplaced as a "Feature"**
   - Located in `features/embeddings/` but it's infrastructure, not a domain
   - No business logic, no data model, no routes
   - Both `news` and `questions` domains depend on it
   - **Impact**: Confusing mental model, violates vertical slice principles

4. **Leaky Abstractions**
   - Services directly access `repository.session.rollback()`
   - Breaks encapsulation and separation of concerns
   - **Impact**: Tight coupling, hard to test, violates Open/Closed Principle

5. **Dead Code**
   - Empty `features/questions/models.py` placeholder
   - Duplicate test fixtures
   - **Impact**: Confusing for developers, suggests incomplete implementation

---

## 📋 Refactoring Plan (Priority Order)

### Phase 1: Fix Critical Architecture Violations (HIGH PRIORITY)

#### 1.1 Move Embeddings to Shared Infrastructure

**Current Structure:**
```
features/embeddings/
  └── service.py  # EmbeddingsService
```

**Target Structure:**
```
shared/
  └── embeddings.py  # EmbeddingsService
```

**Changes Required:**
- Move `features/embeddings/service.py` → `shared/embeddings.py`
- Update imports in:
  - `features/news/article_processor.py`
  - `features/questions/rag_service.py`
  - `shared/deps.py`
  - All test files
- Remove now-empty `features/embeddings/` directory

**Rationale:** Embeddings is infrastructure (thin wrapper around Ollama), not a business domain. Both domains depend on it, making it a shared service.

---

#### 1.2 Fix Repository Session Management

**Current Anti-Pattern:**
```python
# In NewsRepository.create_news_source()
def create_news_source(...) -> NewsSource:
    source = NewsSource(...)
    self.session.add(source)
    self.session.commit()  # ❌ Repository shouldn't auto-commit
    self.session.refresh(source)
    return source
```

**Target Pattern:**
```python
# Repository is transaction-agnostic
def create_news_source(...) -> NewsSource:
    source = NewsSource(...)
    self.session.add(source)
    self.session.flush()  # Make ID available without committing
    self.session.refresh(source)
    return source
```

**Changes Required:**
- Remove `session.commit()` from ALL repository methods:
  - `create_news_source()`
  - `create_news_article()`
  - `update_ingestion_status()`
- Replace `commit()` with `flush()` where needed (to get generated IDs)
- Move commit to router/service boundary (see 1.3)

**Rationale:** Transaction control should be at the service/router layer, not repository. This allows composing multiple repository operations in a single transaction.

---

#### 1.3 Remove Service Access to Sessions

**Current Anti-Pattern:**
```python
# In ArticleProcessor.process_article()
except Exception as e:
    logger.error(f"Error processing article '{title}': {e}")
    self.repository.session.rollback()  # ❌ WRONG LAYER
    raise

# In IngestionService.run_ingestion()
except Exception as e:
    self.repository.session.rollback()  # ❌ WRONG LAYER
```

**Target Pattern:**
```python
# Service just raises exceptions
except Exception as e:
    logger.error(f"Error processing article '{title}': {e}")
    raise  # Let caller handle transaction

# Router/entry point handles transaction
@router.post("/manual-ingestion")
def manual_ingestion(service: IngestionServiceDep, session: SessionDep):
    try:
        result = service.run_ingestion()
        session.commit()
        return result
    except Exception as e:
        session.rollback()
        raise
```

**Changes Required:**
- Remove `self.repository.session.rollback()` from:
  - `features/news/article_processor.py` line 72
  - `features/news/ingestion_service.py` line 116
- Add transaction management at router level:
  - `features/news/router.py`
- Update service constructors to NOT need session access

**Rationale:** Services should not know about repository internals. Transaction management is infrastructure concern, not business logic.

---

#### 1.4 Fix Scheduler Dependency Injection

**Current Broken Pattern:**
```python
# In shared/deps.py
def create_ingestion_service(
    repository: NewsRepository = Depends(get_news_repository),  # ❌ WRONG
    ...
) -> IngestionService:
    return IngestionService(...)

# In shared/scheduler.py
def run_scheduled_ingestion() -> None:
    from app.shared.deps import create_ingestion_service, get_db

    db_gen = get_db()
    session = next(db_gen)  # ❌ Manual lifecycle management
    try:
        service = create_ingestion_service()  # ❌ Depends() doesn't work here
        service.run_ingestion()
    finally:
        try:
            db_gen.close()
        except StopIteration:
            pass
```

**Target Pattern:**
```python
# In shared/deps.py - NEW factory for scheduler
def create_ingestion_service_for_scheduler() -> IngestionService:
    """Factory for scheduled jobs (not FastAPI context)."""
    embeddings = get_ollama_embeddings()
    embeddings_service = EmbeddingsService(embeddings)
    rss_fetcher = RSSFetcher()

    with Session(engine) as session:
        repository = NewsRepository(session)
        processor = ArticleProcessor(embeddings_service, repository)
        service = IngestionService(rss_fetcher, processor, repository)

        try:
            service.run_ingestion()
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Scheduled ingestion failed: {e}")
            raise

# In shared/scheduler.py
def run_scheduled_ingestion() -> None:
    from app.shared.deps import create_ingestion_service_for_scheduler
    create_ingestion_service_for_scheduler()
```

**Changes Required:**
- Remove `create_ingestion_service()` and `create_rag_service()` from `shared/deps.py`
- Add proper factory functions that handle their own session lifecycle:
  - `create_ingestion_service_for_scheduler()`
  - `create_rag_service_for_scheduler()`
- Update `shared/scheduler.py` to use new factories
- Remove manual DB lifecycle management

**Rationale:** `Depends()` only works in FastAPI request context. Scheduled jobs need explicit dependency construction with proper resource management.

---

#### 1.5 Clean Up Dead Code

**Files to Delete:**
- `features/questions/models.py` (empty placeholder)

**Test Fixtures to Consolidate:**
- Remove duplicate `db_session` fixture in `tests/integration/test_api_news.py`
- Standardize on `db` fixture from `tests/conftest.py`

**Rationale:** Dead code confuses developers and suggests incomplete implementation.

---

### Phase 2: Standardize Patterns (MEDIUM PRIORITY)

#### 2.1 Implement Explicit Transaction Boundaries

**Goal:** Make it clear where transactions start and end

**Pattern to Implement:**
```python
# Router level - transaction boundary
@router.post("/articles")
def create_article(
    article_data: ArticleCreate,
    service: IngestionServiceDep,
    session: SessionDep
) -> ArticlePublic:
    try:
        article = service.process_article(article_data)
        session.commit()
        return article
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
```

**Changes Required:**
- Add transaction management to all routes in `features/news/router.py`
- Add transaction management to WebSocket lifecycle in `features/questions/router.py`
- Document pattern in docstrings
- Update tests to verify commit/rollback behavior

**Rationale:** Explicit is better than implicit. Clear boundaries prevent bugs.

---

#### 2.2 Extract Configuration Values

**Current Hardcoded Values:**
```python
# In rag_service.py
DISTANCE_THRESHOLD = 0.5
TOP_K_ARTICLES = 5
article.content[:500]  # Truncation

# In ingestion_service.py
days=30  # Cleanup threshold
```

**Target Configuration:**
```python
# In core/config.py
class Settings(BaseSettings):
    # Existing settings...

    # RAG Configuration
    RAG_DISTANCE_THRESHOLD: float = 0.5
    RAG_TOP_K_ARTICLES: int = 5
    RAG_CONTEXT_PREVIEW_LENGTH: int = 500

    # Article Management
    ARTICLE_CLEANUP_DAYS: int = 30
    INGESTION_INTERVAL_MINUTES: int = 30
    CLEANUP_SCHEDULE_HOUR: int = 2  # UTC
```

**Changes Required:**
- Add new config fields to `core/config.py`
- Update `features/questions/rag_service.py` to use config
- Update `features/news/ingestion_service.py` to use config
- Update `shared/scheduler.py` to use config for schedules
- Add environment variables to `.env` template

**Rationale:** Configuration should be centralized and environment-variable driven, not scattered as magic numbers.

---

#### 2.3 Standardize Error Handling

**Current Issues:**
- Bare `except:` catches everything (too broad)
- Mix of error logging styles
- No custom business exceptions

**Target Pattern:**
```python
# New file: shared/exceptions.py
class CryptoNewsAgentError(Exception):
    """Base exception for application errors."""
    pass

class DuplicateArticleError(CryptoNewsAgentError):
    """Article already exists in database."""
    pass

class EmbeddingGenerationError(CryptoNewsAgentError):
    """Failed to generate embeddings."""
    pass

class RSSFetchError(CryptoNewsAgentError):
    """Failed to fetch RSS feed."""
    pass

# Usage in services
try:
    embedding = self.embeddings_service.embed_documents([combined])
except Exception as e:
    raise EmbeddingGenerationError(f"Failed to generate embedding: {e}")
```

**Changes Required:**
- Create `shared/exceptions.py` with custom exception hierarchy
- Replace bare `except:` with specific exception types
- Update error handling in:
  - `features/news/article_processor.py`
  - `features/news/ingestion_service.py`
  - `features/questions/rag_service.py`
  - `features/questions/router.py`
- Document error handling strategy in CLAUDE.md

**Rationale:** Specific exceptions make errors traceable and allow targeted handling. Bare `except:` can mask bugs.

---

#### 2.4 Add WebSocket Security

**Current Issues:**
- No authentication on `/ws/ask` endpoint
- No rate limiting (DoS vector)
- No connection timeout
- Any client can connect and ask questions

**Target Implementation:**
```python
# In features/questions/router.py
from fastapi import WebSocket, Depends, status
from app.api.deps import get_current_user  # Reuse existing auth

@router.websocket("/ws/ask")
async def websocket_ask(
    websocket: WebSocket,
    current_user: User = Depends(get_current_user),  # ✅ Authentication
    rag_service: RAGServiceDep = Depends(get_rag_service_dep),
):
    await websocket.accept()

    # Rate limiting: max 10 questions per minute per user
    rate_limiter = RateLimiter(max_requests=10, window_seconds=60)

    # Connection timeout: 5 minutes idle
    timeout_seconds = 300

    try:
        while True:
            data = await asyncio.wait_for(
                websocket.receive_json(),
                timeout=timeout_seconds
            )

            if not rate_limiter.allow(current_user.id):
                await websocket.send_json({
                    "type": "error",
                    "content": "Rate limit exceeded"
                })
                continue

            # Process question...
    except asyncio.TimeoutError:
        await websocket.close(code=status.WS_1000_NORMAL_CLOSURE)
```

**Changes Required:**
- Add authentication dependency to WebSocket endpoint
- Implement rate limiter (simple in-memory for MVP)
- Add connection timeout
- Add error codes for rate limit/auth failures
- Update frontend to handle auth errors

**Rationale:** Security fundamentals - authentication, rate limiting, and timeouts prevent abuse.

---

### Phase 3: Optional Improvements (LOW PRIORITY - YAGNI)

#### 3.1 Consider Simplifying RSSFetcher

**Current:**
```python
class RSSFetcher:
    def __init__(self):
        pass

    def fetch_feed(self, source: NewsSource) -> list[dict[str, Any]]:
        loader = RSSFeedLoader(urls=[source.rss_url], ...)
        return loader.load()
```

**Alternative (simpler):**
```python
# Could be a simple function
def fetch_rss_feed(source: NewsSource) -> list[dict[str, Any]]:
    loader = RSSFeedLoader(urls=[source.rss_url], ...)
    return loader.load()
```

**Decision:** Keep as-is unless team prefers function over class. Current abstraction is acceptable for testing purposes.

---

#### 3.2 Add Retry Logic (Only if failures observed)

**Potential Addition:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

class ArticleProcessor:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _generate_embedding(self, text: str) -> list[float]:
        return self.embeddings_service.embed_documents([text])[0]
```

**Decision:** Only implement if embedding failures become a real problem. Don't optimize prematurely.

---

#### 3.3 Batch Embedding Generation (Only if performance bottleneck)

**Potential Optimization:**
```python
# Process 10 articles at once
batch_texts = [combine_text(art) for art in articles[:10]]
batch_embeddings = embeddings_service.embed_documents(batch_texts)

for article, embedding in zip(articles[:10], batch_embeddings):
    # Save article with embedding
```

**Decision:** Current one-at-a-time approach works fine. Batch processing adds complexity. Only optimize if profiling shows this is a bottleneck.

---

## 🏗️ Target Architecture

### Domain Structure (After Phase 1)

```
backend/app/
├── core/                           # Infrastructure Configuration
│   ├── config.py                   # ✅ Settings (+ new RAG/cleanup config)
│   └── db.py                       # ✅ Database engine
│
├── shared/                         # Cross-Cutting Concerns
│   ├── deps.py                     # ✅ DI factories (fixed scheduler factories)
│   ├── embeddings.py               # ⬅️ MOVED from features/
│   ├── exceptions.py               # ✨ NEW: Custom exceptions
│   ├── models.py                   # ✅ Shared response models
│   ├── scheduler.py                # ✅ Background jobs (using fixed factories)
│   └── check_ollama.py             # ✅ Startup check
│
├── features/                       # Business Domains (Vertical Slices)
│   ├── news/                       # News Ingestion & Storage
│   │   ├── models.py               # ✅ NewsSource, NewsArticle
│   │   ├── schemas.py              # ✅ API schemas
│   │   ├── repository.py           # ✅ NO auto-commit, transaction-agnostic
│   │   ├── rss_fetcher.py          # ✅ Fetch RSS feeds
│   │   ├── article_processor.py    # ✅ NO session.rollback()
│   │   ├── ingestion_service.py    # ✅ NO session.rollback()
│   │   ├── router.py               # ✅ Transaction boundaries at router level
│   │   └── scripts/seed_sources.py # ✅ Seed data
│   │
│   └── questions/                  # Q&A / RAG Domain
│       ├── rag_service.py          # ✅ Use config values
│       └── router.py               # ✅ Auth + rate limiting + timeouts
│
├── api/
│   └── main.py                     # ✅ Central router
│
└── main.py                         # ✅ FastAPI app initialization
```

---

## 🎯 Key Principles Enforced

### SOLID Principles

1. **Single Responsibility Principle (SRP)**
   - ✅ Repositories only handle data access (no transaction management)
   - ✅ Services only handle business logic (no session management)
   - ✅ Routers handle HTTP/WebSocket concerns + transaction boundaries

2. **Open/Closed Principle (OCP)**
   - ✅ Services don't depend on repository internals (session)
   - ✅ Can swap repository implementations without changing services

3. **Liskov Substitution Principle (LSP)**
   - ✅ Repository methods have consistent return types
   - ✅ All repositories follow same transaction-agnostic pattern

4. **Interface Segregation Principle (ISP)**
   - ✅ Services only depend on methods they use
   - ✅ No fat interfaces

5. **Dependency Inversion Principle (DIP)**
   - ✅ Services depend on abstractions (injected dependencies)
   - ✅ High-level modules (services) don't depend on low-level modules (DB sessions)

### Clean Architecture Layers

```
┌─────────────────────────────────────┐
│  Presentation Layer (Routers)       │  ← Transaction boundaries
│  - HTTP endpoints                   │
│  - WebSocket handlers                │
│  - Request/response validation      │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Application Layer (Services)       │  ← Business logic
│  - IngestionService                 │
│  - RAGService                        │
│  - Orchestration                    │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Domain Layer (Models)               │  ← Core entities
│  - NewsSource                       │
│  - NewsArticle                      │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  Infrastructure Layer                │  ← Technical details
│  - Repositories (data access)       │
│  - EmbeddingsService (Ollama)       │
│  - RSSFetcher (external feeds)      │
│  - Database (PostgreSQL)            │
└─────────────────────────────────────┘
```

### Vertical Slice Architecture

Each feature slice contains all layers needed for that feature:
- **News**: Models → Repository → Services → Router
- **Questions**: Service → Router (reuses News models)

Horizontal concerns (auth, logging, config) live in `shared/`

---

## ✅ Success Criteria

### Phase 1 Completion Checklist

- [ ] `EmbeddingsService` moved to `shared/embeddings.py`
- [ ] All imports updated (news, questions, deps, tests)
- [ ] No `session.commit()` in any repository method
- [ ] No `repository.session.rollback()` in any service
- [ ] Transaction management added to all routers
- [ ] Scheduler factories refactored (no broken `Depends()`)
- [ ] `features/questions/models.py` deleted
- [ ] Duplicate test fixtures removed
- [ ] All tests pass (unit + integration + e2e)
- [ ] Docker Compose stack runs successfully

### Phase 2 Completion Checklist

- [ ] Configuration values extracted to `core/config.py`
- [ ] `.env` template updated with new variables
- [ ] Custom exceptions defined in `shared/exceptions.py`
- [ ] All bare `except:` replaced with specific types
- [ ] WebSocket authentication implemented
- [ ] Rate limiting added to WebSocket
- [ ] Connection timeouts configured
- [ ] All tests pass

### Architecture Quality Metrics

| Metric | Before | Target | How to Measure |
|--------|--------|--------|----------------|
| **Separation of Concerns** | 7/10 | 9/10 | No cross-layer violations |
| **Dependency Injection** | 6/10 | 9/10 | No manual lifecycle mgmt |
| **SOLID Compliance** | 7/10 | 9/10 | No session leaks |
| **YAGNI Compliance** | 6/10 | 8/10 | No premature abstractions |
| **Database Patterns** | 5/10 | 9/10 | Explicit transactions |
| **Error Handling** | 7/10 | 9/10 | Specific exception types |
| **Overall Score** | 6.75/10 | 8.5/10 | Weighted average |

---

## 🚫 What We're NOT Doing (YAGNI)

These are things that COULD be done but provide no current value:

- ❌ **Conversation History**: Questions are independent, no user requirement
- ❌ **Async/Await Refactor**: Current synchronous code performs adequately
- ❌ **Batch Embedding Optimization**: No observed performance bottleneck
- ❌ **Complex Caching**: Premature optimization without metrics
- ❌ **Event Sourcing**: No audit trail requirement
- ❌ **CQRS Pattern**: Read/write patterns are simple enough
- ❌ **Microservices Split**: Monolith is appropriate for this scale
- ❌ **GraphQL**: REST + WebSocket meet all current needs
- ❌ **Removing All Thin Wrappers**: Current abstractions aid testing

**Principle:** Only add complexity when there's a clear problem to solve. The architecture is fundamentally sound.

---

## 📊 Risk Assessment

### Low Risk Changes
- Moving embeddings to shared (no logic changes)
- Extracting configuration values (backward compatible)
- Adding custom exceptions (additive)
- Cleaning up dead code (no impact)

### Medium Risk Changes
- Removing repository auto-commit (requires careful testing)
- Refactoring scheduler DI (must verify background jobs work)
- Adding transaction boundaries (must ensure all paths covered)

### High Risk Changes
- None in this plan (all changes are refactoring, not feature changes)

### Mitigation Strategies
1. **Comprehensive Testing**: Run full test suite after each phase
2. **Incremental Rollout**: Complete Phase 1 before starting Phase 2
3. **Feature Flags**: Not needed (no user-facing changes)
4. **Rollback Plan**: Git branches for each phase
5. **Monitoring**: Watch logs for session leaks or transaction errors

---

## 📚 Reference Documentation

### Architecture Decision Records (ADRs)

**ADR-001: Move Embeddings to Shared Infrastructure**
- **Context**: Embeddings was in `features/` but has no business logic
- **Decision**: Move to `shared/` to clarify it's infrastructure
- **Consequences**: Clearer separation of domains vs. infrastructure

**ADR-002: Remove Repository Auto-Commit**
- **Context**: Repositories auto-commit, preventing transaction composition
- **Decision**: Repositories are transaction-agnostic, commit at router level
- **Consequences**: More control over transactions, can compose operations

**ADR-003: Explicit Transaction Boundaries**
- **Context**: Unclear where transactions start/end
- **Decision**: Routers manage transactions, services are transaction-agnostic
- **Consequences**: Explicit is better than implicit, easier to reason about

**ADR-004: Custom Exception Hierarchy**
- **Context**: Generic exceptions make debugging hard
- **Decision**: Domain-specific exceptions with clear names
- **Consequences**: Better error tracking, targeted error handling

**ADR-005: WebSocket Authentication**
- **Context**: Unauthenticated WebSocket endpoint is security risk
- **Decision**: Add JWT-based auth to WebSocket handshake
- **Consequences**: Secure by default, can track usage per user

---

## 🔗 Related Documents

- [CLAUDE.md](./CLAUDE.md) - Project overview and development guidelines
- [Constitution](./.specify/memory/constitution.md) - Coding standards and principles
- [Spec](./specs/001-crypto-news-agent/spec.md) - Feature specification
- [Plan](./specs/001-crypto-news-agent/plan.md) - Implementation plan

---

## 📅 Implementation Timeline (Estimated)

### Phase 1: Critical Fixes
- **Duration**: 1-2 days
- **Effort**: 8-12 hours
- **Complexity**: Medium

### Phase 2: Standardization
- **Duration**: 1-2 days
- **Effort**: 6-10 hours
- **Complexity**: Medium

### Phase 3: Optional Improvements
- **Duration**: As needed
- **Effort**: Variable
- **Complexity**: Low-Medium

**Total Estimated Effort**: 14-22 hours over 2-4 days

---

## 💡 Key Insights from Analysis

### What's Working Well
1. ✅ Clean vertical slice architecture (news vs. questions)
2. ✅ Good use of FastAPI dependency injection for routes
3. ✅ Proper vector embeddings with pgvector
4. ✅ Clean API contracts (schemas separated from models)
5. ✅ Background jobs correctly scheduled
6. ✅ WebSocket streaming for good UX

### What Needs Improvement
1. ❌ Session management patterns are confused
2. ❌ Scheduler DI uses broken pattern (`Depends()` outside FastAPI)
3. ❌ Some architectural boundaries are blurred (embeddings placement)
4. ❌ Services know too much about repository internals
5. ❌ Configuration scattered as magic numbers
6. ❌ WebSocket lacks basic security

### Key Takeaway
**The foundation is solid. This is polish, not reconstruction.**

We're not rebuilding the architecture - we're cleaning up technical debt that accumulated during rapid development. The core vertical slice structure and domain separation are excellent.

---

## 🎓 Learning Opportunities

This refactoring demonstrates:
1. **Transaction Management**: Where commit/rollback should live
2. **Dependency Injection**: FastAPI vs. non-FastAPI contexts
3. **Layer Separation**: What each layer should (and shouldn't) know
4. **SOLID Principles**: Practical application in real codebase
5. **YAGNI**: Resisting premature optimization and over-engineering

These patterns will inform future feature development.

---

**Last Updated**: 2025-11-06
**Author**: Architecture Analysis (Claude Code)
**Status**: Ready for Review → Implementation
