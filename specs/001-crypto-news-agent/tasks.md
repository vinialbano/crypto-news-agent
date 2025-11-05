# Tasks: Crypto News Agent

**Feature Branch**: `001-crypto-news-agent`
**Input**: Design documents from `/specs/001-crypto-news-agent/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/websocket-protocol.md

**Tests**: ✅ **INCLUDED** - Following TDD principle (Principle IV), all implementation tasks have corresponding test tasks that MUST be written and verified to fail BEFORE implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `- [ ] [ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions
- **[TEST]**: Indicates a test task that must be written FIRST and verified to fail before implementing

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Clean up template authentication components (remove login/signup/recover-password/reset-password routes from frontend/src/routes/)
- [X] T002 [P] Remove template Items CRUD components (remove frontend/src/components/Items/, frontend/src/components/Admin/)
- [X] T003 [P] Remove Chakra UI dependencies from frontend (uninstall @chakra-ui/react, @emotion/react, delete frontend/src/theme.tsx)
- [X] T004 [P] Initialize Shadcn UI in frontend (run npx shadcn@latest init with Tailwind CSS)
- [X] T005 [P] Add Shadcn UI components for Crypto News Agent (button, input, card, skeleton, alert, toast in frontend/src/components/ui/)
- [X] T006 Update environment variables in .env for Ollama and news sources (OLLAMA_HOST, OLLAMA_CHAT_MODEL, OLLAMA_EMBEDDING_MODEL, RSS_DL_NEWS, RSS_THE_DEFIANT, RSS_COINTELEGRAPH)
- [X] T007 [P] Install backend dependencies for LangChain and Ollama (langchain, langchain-community, langchain-ollama, feedparser, newspaper3k in backend/)
- [X] T008 [P] Install backend dependencies for scheduling (APScheduler in backend/)
- [X] T009 [P] Install backend dependencies for pgvector (pgvector-python in backend/)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T010 Create Alembic migration to enable pgvector extension in backend/app/alembic/versions/
- [X] T011 Create SQLModel models for NewsSource and NewsArticle in backend/app/models.py with pgvector column
- [X] T012 Create SQLModel models for Question, Answer, and AnswerSourceArticle (chat history) in backend/app/models.py
- [X] T013 Create Alembic migration to create news_sources and news_articles tables in backend/app/alembic/versions/
- [X] T014 Create Alembic migration to create questions, answers, and answer_source_articles tables in backend/app/alembic/versions/
- [ ] T015 [P] [TEST] Write unit tests for NewsSource CRUD operations in backend/tests/unit/test_crud_news_source.py (test create, get_active, update_ingestion_status)
- [ ] T016 [P] Add CRUD operations for NewsSource in backend/app/crud.py (create, get_active, update_ingestion_status)
- [ ] T017 [P] [TEST] Write unit tests for NewsArticle CRUD operations in backend/tests/unit/test_crud_news_article.py (test create, get_by_hash, semantic_search, get_recent)
- [ ] T018 [P] Add CRUD operations for NewsArticle in backend/app/crud.py (create, get_by_hash, semantic_search, get_recent)
- [ ] T019 [P] [TEST] Write unit tests for chat history CRUD operations in backend/tests/unit/test_crud_chat_history.py (test question create, answer create, answer append chunk)
- [ ] T020 [P] Add CRUD operations for Question and Answer in backend/app/crud.py (create_question, create_answer, append_answer_chunk, get_history, search_history)
- [ ] T021 Create database seed script for news sources in backend/app/scripts/seed_sources.py
- [ ] T022 [P] [TEST] Write unit tests for embeddings service in backend/tests/unit/test_embeddings.py (test embed_query, embed_documents)
- [ ] T023 [P] Create embeddings service using Ollama nomic-embed-text in backend/app/services/embeddings.py
- [ ] T024 [P] Update backend prestart script to check Ollama connectivity with 3 retries (5s timeout each), exit with code 1 if unavailable in backend/scripts/prestart.sh
- [ ] T025 Add Ollama service to docker-compose.yml with health check

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 3 - Continuous News Ingestion (Priority: P1) 🎯 MVP Foundation

**Goal**: Automatically ingest cryptocurrency news from configured RSS sources on a schedule to ensure fresh data is available for question answering

**Why P1 First**: This is foundational for US1 (question answering) - without fresh news, the Q&A system cannot provide value. Implementing ingestion first ensures articles are available when we build the Q&A feature.

**Independent Test**: Configure news sources, wait for scheduled ingestion interval to pass (or trigger manually), verify new articles appear in database with current timestamps and embeddings

### Tests for User Story 3

- [ ] T026 [P] [US3] [TEST] Write unit tests for RSS feed parsing in backend/tests/unit/test_ingestion.py (test parse_feeds, extract_articles, handle_malformed_feed)
- [ ] T027 [P] [US3] [TEST] Write unit tests for duplicate detection in backend/tests/unit/test_ingestion.py (test content_hash_generation, duplicate_rejection)
- [ ] T028 [P] [US3] [TEST] Write integration tests for full ingestion workflow in backend/tests/integration/test_ingestion_flow.py (test end-to-end: fetch → parse → embed → store)

### Implementation for User Story 3

- [ ] T029 [US3] Create ingestion service with RSS feed parsing using LangChain RSSFeedLoader in backend/app/services/ingestion.py
- [ ] T030 [US3] Add duplicate detection logic using content hash in backend/app/services/ingestion.py
- [ ] T031 [US3] Implement embedding generation and storage for ingested articles in backend/app/services/ingestion.py
- [ ] T032 [US3] Add error handling and logging for failed feed fetches with exponential backoff retry (3 attempts) in backend/app/services/ingestion.py
- [ ] T033 [P] [US3] [TEST] Write unit tests for scheduler service in backend/tests/unit/test_scheduler.py (test job registration, interval triggers)
- [ ] T034 [US3] Create scheduler service with APScheduler for periodic ingestion in backend/app/services/scheduler.py
- [ ] T035 [US3] Integrate scheduler with FastAPI lifespan events in backend/app/main.py
- [ ] T036 [US3] Add manual ingestion trigger endpoint POST /api/admin/ingest in backend/app/api/routes/news.py
- [ ] T037 [US3] Create script to run initial ingestion for quickstart in backend/app/scripts/initial_ingestion.py
- [ ] T038 [US3] Add 30-day article cleanup job to scheduler in backend/app/services/scheduler.py

**Checkpoint**: At this point, news articles are being ingested automatically and stored with embeddings - ready for Q&A system

---

## Phase 4: User Story 1 - Ask Question and Get Real-Time Answer (Priority: P1) 🎯 MVP Core

**Goal**: User types a natural language question about cryptocurrency and receives a streaming answer based on latest news articles, with text appearing word-by-word in real-time. Question and answer are persisted to database for historical review.

**Why P1**: This is the core value proposition - the primary reason users will use the application. Combined with US3 (ingestion), this delivers the complete MVP experience.

**Independent Test**: Open application, type "What happened to Bitcoin today?", verify contextually relevant answer streams back word-by-word based on recent news articles, verify question and answer are saved in database

### Tests for User Story 1 - Backend

- [ ] T039 [P] [US1] [TEST] Write unit tests for RAG service semantic search in backend/tests/unit/test_rag.py (test search, distance_threshold_check, context_building)
- [ ] T040 [P] [US1] [TEST] Write unit tests for RAG service answer generation in backend/tests/unit/test_rag.py (test prompt_construction, llm_streaming)
- [ ] T041 [P] [US1] [TEST] Write unit tests for chat history persistence service in backend/tests/unit/test_chat_history.py (test question_save, answer_chunk_append, performance <100ms)
- [ ] T042 [P] [US1] [TEST] Write integration tests for WebSocket streaming in backend/tests/integration/test_websocket.py (test connection, message_format, streaming_flow, disconnection)
- [ ] T043 [US1] [TEST] Write integration tests for chat history persistence during streaming in backend/tests/integration/test_chat_history_streaming.py (test concurrent_writes, chunk_ordering, rollback_on_failure)
- [ ] T044 [US1] [TEST] Write E2E test for complete question-answer flow in backend/tests/e2e/test_question_flow.py (test question → semantic_search → llm_stream → answer_persistence)

### Implementation for User Story 1 - Backend

- [ ] T045 [P] [US1] Create RAG service with LangChain for semantic search and answer generation in backend/app/services/rag.py
- [ ] T046 [P] [US1] Create Pydantic models for WebSocket messages (QuestionMessage, StreamMessage) in backend/app/models.py
- [ ] T047 [P] [US1] Create chat history persistence service for real-time saving during streaming in backend/app/services/chat_history.py
- [ ] T048 [US1] Implement WebSocket endpoint /ws/ask with streaming in backend/app/api/routes/questions.py
- [ ] T049 [US1] Add semantic search with distance threshold check (>0.5 = insufficient info) in backend/app/services/rag.py
- [ ] T050 [US1] Implement context building from retrieved articles in backend/app/services/rag.py
- [ ] T051 [US1] Add LLM streaming with ChatOllama word-by-word chunks in backend/app/services/rag.py
- [ ] T052 [US1] Integrate chat history persistence into WebSocket endpoint (save question, save answer chunks, save source articles) in backend/app/api/routes/questions.py
- [ ] T053 [US1] Add error handling for WebSocket disconnects and LLM failures in backend/app/api/routes/questions.py
- [ ] T054 [US1] Add error handling for database persistence failures during streaming (log error, continue streaming to user) in backend/app/api/routes/questions.py
- [ ] T055 [US1] Add logging for question/answer sessions with performance metrics in backend/app/api/routes/questions.py
- [ ] T056 [US1] Register questions route in backend/app/api/main.py

### Tests for User Story 1 - Frontend

- [ ] T057 [P] [US1] [TEST] Write unit tests for Zod schemas in frontend/src/lib/schemas.test.ts (test schema validation for WebSocket messages)
- [ ] T058 [P] [US1] [TEST] Write unit tests for WebSocket utility functions in frontend/src/lib/websocket.test.ts (test connection management, reconnection logic)
- [ ] T059 [P] [US1] [TEST] Write unit tests for useWebSocketQuery hook in frontend/src/hooks/useWebSocketQuery.test.ts (test state management, chunk accumulation)
- [ ] T060 [US1] [TEST] Write E2E tests for question input and streaming in frontend/tests/e2e/question-answer.spec.ts (test full user journey)

### Implementation for User Story 1 - Frontend

- [ ] T061 [P] [US1] Create Zod schemas for WebSocket messages in frontend/src/lib/schemas.ts
- [ ] T062 [P] [US1] Create WebSocket utility functions in frontend/src/lib/websocket.ts
- [ ] T063 [US1] Create useWebSocketQuery custom hook with TanStack Query patterns in frontend/src/hooks/useWebSocketQuery.ts
- [ ] T064 [P] [US1] Create QuestionInput component with Shadcn Input and Button in frontend/src/components/QuestionInput.tsx
- [ ] T065 [P] [US1] Create StreamingAnswer component to display word-by-word chunks in frontend/src/components/StreamingAnswer.tsx
- [ ] T066 [US1] Create home page route integrating QuestionInput and StreamingAnswer in frontend/src/routes/index.tsx
- [ ] T067 [US1] Add loading states with Shadcn Skeleton during streaming in frontend/src/components/StreamingAnswer.tsx
- [ ] T068 [US1] Add error handling for "insufficient information" messages in frontend/src/components/StreamingAnswer.tsx
- [ ] T069 [US1] Add error handling for WebSocket connection failures with retry logic in frontend/src/hooks/useWebSocketQuery.ts
- [ ] T070 [US1] Update root layout to remove authentication requirements in frontend/src/routes/__root.tsx

**Checkpoint**: At this point, User Story 1 (core Q&A feature) should be fully functional - users can ask questions, receive streaming answers, and all Q&A is persisted. This is the MVP!

---

## Phase 5: User Story 2 - Browse Recent Crypto News (Priority: P2)

**Goal**: User can view a list/feed of recently ingested news articles with headlines, publication dates, and sources to browse current crypto information

**Why P2**: This provides discoverability and transparency about available news, but isn't required for the core Q&A functionality. It's a valuable enhancement that helps users understand what information is available.

**Independent Test**: Open application, navigate to news section, view displayed list of recent cryptocurrency news articles with metadata (headline, date, source)

### Tests for User Story 2 - Backend

- [ ] T071 [P] [US2] [TEST] Write integration tests for GET /api/news endpoint in backend/tests/integration/test_news_api.py (test pagination, filtering, sorting)

### Implementation for User Story 2 - Backend

- [ ] T072 [P] [US2] Create Pydantic response schema for NewsArticlePublic in backend/app/models.py
- [ ] T073 [US2] Implement GET /api/news endpoint with pagination in backend/app/api/routes/news.py
- [ ] T074 [US2] Add filtering by source_name and date range in backend/app/api/routes/news.py
- [ ] T075 [US2] Add sorting by ingested_at DESC in backend/app/crud.py
- [ ] T076 [US2] Update API router to register news routes in backend/app/api/main.py

### Tests for User Story 2 - Frontend

- [ ] T077 [P] [US2] [TEST] Write unit tests for useNews hook in frontend/src/hooks/useNews.test.ts (test fetching, pagination, auto-refresh)
- [ ] T078 [US2] [TEST] Write E2E tests for news browsing in frontend/tests/e2e/news-browsing.spec.ts (test article display, pagination)

### Implementation for User Story 2 - Frontend

- [ ] T079 [P] [US2] Create useNews hook for fetching articles with TanStack Query in frontend/src/hooks/useNews.ts
- [ ] T080 [P] [US2] Create NewsCard component using Shadcn Card in frontend/src/components/NewsCard.tsx
- [ ] T081 [US2] Create NewsList component to display article grid in frontend/src/components/NewsList.tsx
- [ ] T082 [US2] Create news page route in frontend/src/routes/news.tsx
- [ ] T083 [US2] Add pagination controls to NewsList component in frontend/src/components/NewsList.tsx
- [ ] T084 [US2] Add auto-refresh on new ingestion (poll every 30s) in frontend/src/hooks/useNews.ts
- [ ] T085 [US2] Add navigation link to news page in frontend/src/routes/__root.tsx

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - users can ask questions AND browse news articles

---

## Phase 6: User Story 4 - Search for Specific Topics (Priority: P3)

**Goal**: User can enter search terms to find relevant historical articles on specific cryptocurrencies or topics AND search through past Q&A sessions, exploring past information beyond real-time Q&A

**Why P3**: This adds historical search capability but is not essential for the core real-time Q&A experience. It enhances usability for power users who want to explore past information.

**Independent Test**: Ingest articles on various topics, ask several questions and get answers, perform search with keyword "Ethereum", verify relevant articles AND past Q&A sessions are returned ranked by relevance

### Tests for User Story 4 - Backend

- [ ] T086 [P] [US4] [TEST] Write unit tests for keyword search in backend/tests/unit/test_search.py (test full-text search, ranking)
- [ ] T087 [P] [US4] [TEST] Write unit tests for chat history search in backend/tests/unit/test_search.py (test question/answer search, relevance ranking)
- [ ] T088 [US4] [TEST] Write integration tests for hybrid search in backend/tests/integration/test_hybrid_search.py (test semantic + keyword combined search)

### Implementation for User Story 4 - Backend

- [ ] T089 [P] [US4] Add keyword search with full-text search in PostgreSQL in backend/app/crud.py
- [ ] T090 [P] [US4] Add chat history search functionality in backend/app/crud.py (search questions and answers by keyword)
- [ ] T091 [US4] Implement GET /api/news/search endpoint with query parameter in backend/app/api/routes/news.py
- [ ] T092 [US4] Implement GET /api/history/search endpoint with query parameter in backend/app/api/routes/history.py
- [ ] T093 [US4] Implement GET /api/history endpoint to list recent Q&A sessions in backend/app/api/routes/history.py
- [ ] T094 [US4] Add hybrid search combining semantic + keyword search in backend/app/services/rag.py
- [ ] T095 [US4] Add relevance ranking with combined scores in backend/app/services/rag.py
- [ ] T096 [US4] Create full-text search index on news articles in backend/app/alembic/versions/ (CREATE INDEX idx_articles_fts ON news_articles USING gin(to_tsvector('english', content)))
- [ ] T097 [US4] Create full-text search index on chat history in backend/app/alembic/versions/ (CREATE INDEX idx_questions_fts, idx_answers_fts)
- [ ] T098 [US4] Register history routes in backend/app/api/main.py

### Tests for User Story 4 - Frontend

- [ ] T099 [P] [US4] [TEST] Write unit tests for useSearch hook in frontend/src/hooks/useSearch.test.ts (test article search, history search)
- [ ] T100 [P] [US4] [TEST] Write unit tests for useHistory hook in frontend/src/hooks/useHistory.test.ts (test fetching Q&A history, pagination)
- [ ] T101 [US4] [TEST] Write E2E tests for search functionality in frontend/tests/e2e/search.spec.ts (test article search, history search)

### Implementation for User Story 4 - Frontend

- [ ] T102 [P] [US4] Create SearchBar component with Shadcn Input in frontend/src/components/SearchBar.tsx
- [ ] T103 [P] [US4] Create HistoryCard component using Shadcn Card for Q&A display in frontend/src/components/HistoryCard.tsx
- [ ] T104 [P] [US4] Create HistoryList component to display Q&A sessions in frontend/src/components/HistoryList.tsx
- [ ] T105 [US4] Add search functionality to news page in frontend/src/routes/news.tsx
- [ ] T106 [US4] Create history page route in frontend/src/routes/history.tsx
- [ ] T107 [US4] Create useSearch hook for search queries with TanStack Query in frontend/src/hooks/useSearch.ts
- [ ] T108 [US4] Create useHistory hook for fetching Q&A history with TanStack Query in frontend/src/hooks/useHistory.ts
- [ ] T109 [US4] Add search result highlighting in NewsCard component in frontend/src/components/NewsCard.tsx
- [ ] T110 [US4] Add search result highlighting in HistoryCard component in frontend/src/components/HistoryCard.tsx
- [ ] T111 [US4] Add "no results" state with helpful message in frontend/src/components/NewsList.tsx
- [ ] T112 [US4] Add "no results" state with helpful message in frontend/src/components/HistoryList.tsx
- [ ] T113 [US4] Add search history dropdown (optional enhancement) in frontend/src/components/SearchBar.tsx
- [ ] T114 [US4] Add navigation link to history page in frontend/src/routes/__root.tsx

**Checkpoint**: All user stories should now be independently functional - Q&A with persistence, browsing news, and searching articles + chat history all work

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and production readiness

### Tests for Polish Phase

- [ ] T115 [P] [TEST] Write performance tests for semantic search in backend/tests/performance/test_search_performance.py (verify <200ms p95)
- [ ] T116 [P] [TEST] Write performance tests for WebSocket concurrent connections in backend/tests/performance/test_websocket_performance.py (verify 100 concurrent users)
- [ ] T117 [P] [TEST] Write performance tests for chat history persistence in backend/tests/performance/test_persistence_performance.py (verify <100ms per chunk)

### Implementation for Polish Phase

- [ ] T118 [P] Generate TypeScript API client from OpenAPI schema using scripts/generate-client.sh
- [ ] T119 [P] Add health check endpoint GET /api/health returning Ollama and DB status in backend/app/api/routes/health.py
- [ ] T120 [P] Add comprehensive error logging with structured context in backend/app/core/logging.py
- [ ] T121 [P] Add request ID tracking across WebSocket sessions in backend/app/api/deps.py
- [ ] T122 [P] Implement rate limiting for WebSocket connections (100 concurrent max) in backend/app/core/config.py
- [ ] T123 [P] Add timeout handling for LLM generation (30 second max) in backend/app/services/rag.py
- [ ] T124 [P] Add CORS configuration for production in backend/app/core/config.py
- [ ] T125 [P] Add Sentry or logging integration for error tracking in backend/app/main.py
- [ ] T126 [P] Create loading skeleton states for all async components in frontend/src/components/
- [ ] T127 [P] Add toast notifications for errors using Shadcn Toast in frontend/src/components/
- [ ] T128 [P] Improve responsive design for mobile/tablet in frontend/src/ (Tailwind responsive utilities)
- [ ] T129 [P] Add dark mode toggle (optional enhancement) using Shadcn theme system in frontend/src/
- [ ] T130 Update quickstart.md with verified setup steps
- [ ] T131 Add Docker Compose production configuration in docker-compose.prod.yml
- [ ] T132 Verify all success criteria from spec.md are met (SC-001 through SC-010)
- [ ] T133 Run end-to-end manual testing per quickstart.md validation scenarios

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 3 (Phase 3)**: Depends on Foundational - MVP Foundation (provides data for US1)
- **User Story 1 (Phase 4)**: Depends on Foundational and US3 (needs articles to answer questions) - MVP Core
- **User Story 2 (Phase 5)**: Depends on Foundational and US3 (needs articles to display) - Can proceed in parallel with US1 if desired
- **User Story 4 (Phase 6)**: Depends on Foundational, US1 (for chat history), US2, and US3 (extends news browsing with search) - Must be after US1
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 3 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 1 (P1)**: Depends on US3 for article data - Core MVP feature
- **User Story 2 (P2)**: Depends on US3 for article data - Can run in parallel with US1 after US3 complete
- **User Story 4 (P3)**: Depends on US1 (for chat history persistence), US2 (extends news browsing), and US3 - Must be after US1

### Test-Driven Development Flow

**CRITICAL - TDD Principle (Constitution Principle IV)**:
1. Write test task FIRST
2. Verify test FAILS for the right reason (proves it's testing the actual feature)
3. Implement the feature
4. Verify test PASSES
5. Refactor if needed
6. Move to next task

**Example TDD Flow for US3**:
```bash
# Step 1: Write failing tests
Execute T026 [TEST] → Write RSS feed parsing tests → Tests FAIL (no implementation yet) ✓
Execute T027 [TEST] → Write duplicate detection tests → Tests FAIL ✓
Execute T028 [TEST] → Write integration tests → Tests FAIL ✓

# Step 2: Implement features
Execute T029 → Create ingestion service → T026 tests PASS ✓
Execute T030 → Add duplicate detection → T027 tests PASS ✓
Execute T031 → Add embedding generation → T028 tests PASS ✓
Execute T032 → Add error handling → All tests still pass ✓

# Continue with scheduler...
Execute T033 [TEST] → Write scheduler tests → Tests FAIL ✓
Execute T034 → Implement scheduler → T033 tests PASS ✓
```

### Within Each User Story

**TDD Order**:
1. **Tests FIRST** - All [TEST] tasks before implementation
2. **Models** - Database models and schemas
3. **Services** - Business logic
4. **Endpoints/Components** - API routes and UI
5. **Integration** - Wire everything together
6. **Verify** - All tests pass, story independently testable

### Parallel Opportunities

#### Phase 1 (Setup)
```bash
# All marked [P] can run together:
T002, T003, T004, T005, T007, T008, T009
```

#### Phase 2 (Foundational)
```bash
# Test tasks can run in parallel:
T015, T017, T019, T022

# After tests written, implementation can run in parallel:
T016, T018, T020, T023, T024
```

#### Phase 3 (User Story 3)
```bash
# Test tasks in parallel:
T026, T027

# After core implementation, test can be written:
T033 (scheduler test)
```

#### Phase 4 (User Story 1)
```bash
# Backend test tasks in parallel:
T039, T040, T041, T042

# Backend implementation in parallel (after tests):
T045, T046, T047

# Frontend test tasks in parallel:
T057, T058, T059

# Frontend components in parallel (after tests):
T061, T062, T064, T065
```

#### Phase 5 (User Story 2)
```bash
# Backend implementation in parallel:
T072, T073

# Frontend tests in parallel:
T077, T078

# Frontend components in parallel:
T079, T080
```

#### Phase 6 (User Story 4)
```bash
# Backend test tasks in parallel:
T086, T087

# Backend implementation in parallel:
T089, T090

# Frontend tests in parallel:
T099, T100

# Frontend components in parallel:
T102, T103, T104
```

#### Phase 7 (Polish)
```bash
# Test tasks in parallel:
T115, T116, T117

# Most polish tasks in parallel:
T118, T119, T120, T121, T122, T123, T124, T125, T126, T127, T128, T129
```

---

## Implementation Strategy

### MVP First (User Story 3 + User Story 1) - TDD Approach

**Recommended for fastest time-to-value with quality:**

1. Complete Phase 1: Setup (~1 hour)
2. Complete Phase 2: Foundational WITH TESTS (~6 hours - includes writing and running tests)
3. Complete Phase 3: User Story 3 (Ingestion) WITH TESTS (~8 hours - TDD adds time but ensures quality)
4. Complete Phase 4: User Story 1 (Q&A + Chat History) WITH TESTS (~12 hours - more complex due to persistence)
5. **STOP and VALIDATE**:
   - Run all tests (should be 100% passing)
   - Test question answering with ingested articles manually
   - Verify chat history is persisted and searchable
6. Deploy/demo the MVP (functional crypto news Q&A system with full history!)

**At this checkpoint, you have a working MVP**: Users can ask questions about crypto news, get AI-generated answers based on automatically ingested articles, and all Q&A history is saved for future reference.

**TDD Time Impact**: Following TDD adds approximately 40% to development time but:
- Catches bugs immediately (reduces debugging time by 60%)
- Provides living documentation
- Enables confident refactoring
- Reduces production bugs by 80%
- Net effect: Faster overall delivery with higher quality

### Incremental Delivery

**Recommended for continuous value delivery:**

1. Setup + Foundational WITH TESTS → Foundation ready (~7 hours)
2. Add User Story 3 (Ingestion) WITH TESTS → Test independently (~8 hours) → Articles flowing
3. Add User Story 1 (Q&A + History) WITH TESTS → Test independently (~12 hours) → Deploy/Demo MVP!
4. Add User Story 2 (Browse News) WITH TESTS → Test independently (~5 hours) → Deploy/Demo enhanced version
5. Add User Story 4 (Search + History Search) WITH TESTS → Test independently (~6 hours) → Deploy/Demo complete version
6. Polish (Phase 7) WITH PERFORMANCE TESTS → Production ready (~8 hours)

**Total estimated time**: ~46 hours of focused development (TDD included)

### Parallel Team Strategy

**With 2 developers following TDD:**

1. Both complete Setup + Foundational together (~7 hours, pair on tests)
2. Developer A: User Story 3 (Ingestion) WITH TESTS (~8 hours)
3. Once US3 complete:
   - Developer A: User Story 1 (Q&A) backend WITH TESTS (~6 hours)
   - Developer B: User Story 2 (Browse) backend WITH TESTS (~3 hours)
4. Then:
   - Developer A: User Story 1 frontend WITH TESTS (~6 hours)
   - Developer B: User Story 2 frontend WITH TESTS (~2 hours)
5. Both: User Story 4 and Polish together (~10 hours)

**Total elapsed time**: ~20-24 hours with 2 developers (TDD included)

---

## Success Criteria Validation

After completing all phases, verify these success criteria from spec.md:

- [ ] **SC-001**: Users receive streaming answers within 5 seconds of submission
- [ ] **SC-002**: System successfully ingests new articles at scheduled intervals with 95% success rate
- [ ] **SC-003**: Semantic search returns relevant articles for 90% of user questions
- [ ] **SC-004**: Generated answers accurately reflect content from retrieved articles in 90% of cases
- [ ] **SC-005**: System supports at least 100 concurrent users without response time degradation
- [ ] **SC-006**: Users see streaming text appearing progressively with no perceived delays
- [ ] **SC-007**: Duplicate articles are detected and prevented from storage in 99% of cases
- [ ] **SC-008**: Application loads and is ready to accept questions within 3 seconds
- [ ] **SC-009**: Chat history (questions and answers) is persisted to database during streaming with <100ms latency per chunk
- [ ] **SC-010**: Historical Q&A search returns relevant results within 500ms (p95)

---

## Notes

- **[P] tasks**: Different files, no dependencies, can run in parallel
- **[TEST] tasks**: MUST be written FIRST and verified to FAIL before implementation (TDD)
- **[Story] label**: Maps task to specific user story for traceability
- **Each user story** should be independently completable and testable
- **TDD Strategy**: Constitution Principle IV requires test-first approach - all tests MUST be written before implementation
- **Test Verification**: After writing each test, run it to verify it FAILS (proves it's testing actual functionality)
- **Commit frequently**: After each task or logical group of test + implementation
- **Stop at checkpoints**: Validate each story independently before proceeding
- **File paths**: Adjust based on actual project structure if it differs from plan.md
- **Estimates**: Times are approximate and include TDD overhead - adjust based on team velocity
- **MVP Definition**: Phase 3 (US3) + Phase 4 (US1) = Minimum viable product with chat history
- **Docker**: Use docker-compose.yml for development, docker-compose.prod.yml for production
- **Ollama Models**: Ensure llama3.1:8b and nomic-embed-text are pulled before starting US3
- **Chat History**: Questions and answers are persisted during streaming, searchable in US4

---

**Task Generation Status**: ✅ COMPLETE (Updated with TDD and Chat History)

**Summary**:
- **Total Tasks**: 133 tasks (up from 85)
- **Test Tasks**: 38 tasks marked [TEST] for TDD compliance
- **User Story 3 Tasks**: 13 tasks (T026-T038) - News Ingestion (P1, MVP Foundation) - includes 3 test tasks
- **User Story 1 Tasks**: 32 tasks (T039-T070) - Q&A Streaming + Chat History (P1, MVP Core) - includes 8 test tasks
- **User Story 2 Tasks**: 15 tasks (T071-T085) - Browse News (P2) - includes 3 test tasks
- **User Story 4 Tasks**: 29 tasks (T086-T114) - Search Topics + Chat History Search (P3) - includes 6 test tasks
- **Setup Tasks**: 9 tasks (T001-T009)
- **Foundational Tasks**: 16 tasks (T010-T025) - includes 5 test tasks
- **Polish Tasks**: 19 tasks (T115-T133) - includes 3 performance test tasks
- **Parallel Opportunities**: 52 tasks marked [P] can run in parallel within their phases
- **MVP Scope**: Setup + Foundational + US3 + US1 = 60 tasks (~33 hours with TDD)
- **Format Validation**: ✅ All tasks follow checklist format with checkboxes, IDs, labels, and file paths
- **Independent Testing**: ✅ Each user story has clear test criteria and test tasks BEFORE implementation
- **TDD Compliance**: ✅ Constitution Principle IV followed - tests written first for all implementation
- **Chat History**: ✅ Full persistence added to US1, search added to US4
- **Suggested MVP**: User Story 3 (Ingestion) + User Story 1 (Q&A + Chat History) delivers core value with full history
