<!--
Sync Impact Report:
- Version change: 1.1.0 → 1.2.0
- Modified principles:
  * Code Review Requirements updated to verify principle VII compliance
- Added sections:
  * VII. Documentation-First Development and AI Agent Discipline (new principle)
- Removed sections: N/A
- Templates requiring updates:
  ✅ plan-template.md (reviewed - no changes needed, documentation research aligns with Phase 0)
  ✅ spec-template.md (reviewed - no changes needed)
  ✅ tasks-template.md (reviewed - no changes needed, documentation lookup can be part of research tasks)
- Follow-up TODOs: None
-->

# Crypto News Agent Constitution

## Core Principles

### I. Code Quality and Structure

All code MUST adhere to industry-standard practices for maintainability and scalability:

- **Type Safety**: Python code MUST use type hints (Pydantic, SQLModel); TypeScript MUST use strict mode
- **Modularity**: Features MUST be organized as self-contained modules with clear boundaries and single responsibilities
- **Separation of Concerns**: Business logic (services), data access (models), API interfaces (routers), and presentation (frontend components) MUST remain separate
- **Code Reusability**: Shared functionality MUST be extracted into utilities/libraries rather than duplicated
- **Documentation**: All public APIs, complex functions, and business logic MUST include docstrings/JSDoc comments explaining purpose, parameters, return values, and edge cases
- **Consistency**: Follow existing patterns and conventions in the codebase; when introducing new patterns, document the rationale

**Rationale**: Clean architecture enables parallel development, reduces bugs, simplifies testing, and makes the codebase accessible to new contributors.

### II. End-to-End Functionality

Every feature MUST deliver complete, working user journeys from frontend to backend:

- **Vertical Slices**: Features MUST be implemented as full vertical slices (UI → API → Service → Database) rather than horizontal layers
- **API-First Design**: Backend endpoints MUST be designed and documented (OpenAPI) before frontend integration
- **Contract Testing**: API contracts MUST be validated with tests before integration work begins
- **Integration Validation**: Every feature MUST include at least one end-to-end test proving the complete user journey works
- **No Orphaned Code**: Frontend components without backend support or backend endpoints without UI consumers MUST NOT be merged

**Rationale**: Vertical integration ensures features deliver user value immediately, reduces integration surprises, and enables incremental delivery of working software.

### III. User Experience and Responsiveness

Applications MUST provide fast, intuitive, and reliable user experiences:

- **Performance Budgets**: API responses MUST complete within 200ms (p95) for standard operations; UI interactions MUST provide feedback within 100ms
- **Loading States**: All asynchronous operations MUST display loading indicators; optimistic updates SHOULD be used where appropriate
- **Error Feedback**: User-facing errors MUST be actionable and friendly (no raw stack traces); include specific guidance on resolution when possible
- **Responsive Design**: Frontend MUST be fully functional on mobile (375px), tablet (768px), and desktop (1440px+) viewports
- **Accessibility**: UI MUST meet WCAG 2.1 Level AA standards (semantic HTML, keyboard navigation, ARIA labels, color contrast)
- **Progressive Enhancement**: Core functionality MUST work with JavaScript disabled or slow connections; enhanced features can progressively load

**Rationale**: User experience directly impacts adoption and satisfaction. Performance and accessibility are non-negotiable baseline quality attributes.

### IV. Testing Standards

Tests MUST be comprehensive, automated, and maintained alongside production code:

- **Test Pyramid**:
  - Unit tests MUST cover all business logic and utilities (>80% coverage)
  - Integration tests MUST validate service-to-service and database interactions
  - Contract tests MUST verify API endpoint contracts match frontend expectations
  - End-to-end tests MUST prove critical user journeys work (focus on happy paths + key edge cases)
- **Test-First Approach**: For new features, write failing tests BEFORE implementation; verify tests fail for the right reasons
- **Test Independence**: Tests MUST NOT depend on execution order or external state; use fixtures/factories for test data
- **Test Maintenance**: Broken tests MUST be fixed immediately or temporarily skipped with tracked issues; no permanently ignored tests
- **Performance Testing**: Critical paths (authentication, data fetching) MUST have performance benchmarks that fail when thresholds are exceeded
- **Continuous Testing**: All tests MUST run in CI on every pull request; PRs with failing tests MUST NOT be merged

**Rationale**: Comprehensive testing enables confident refactoring, catches regressions early, serves as living documentation, and maintains delivery velocity.

### V. Error Handling and Scalability

Systems MUST handle failures gracefully and scale reliably:

- **Graceful Degradation**: Failed dependencies MUST NOT crash the application; provide fallback behavior or clear error states
- **Structured Logging**: All errors MUST be logged with structured context (user ID, request ID, timestamp, stack trace)
- **Error Monitoring**: Production errors MUST be tracked with alerting (Sentry, CloudWatch, etc.); critical errors trigger immediate notifications
- **Retry Logic**: Transient failures (network, rate limits) MUST be retried with exponential backoff and circuit breakers
- **Rate Limiting**: API endpoints MUST implement rate limiting to prevent abuse and protect infrastructure
- **Resource Management**: Database connections, file handles, and external API clients MUST use connection pooling and proper cleanup
- **Horizontal Scalability**: Backend services MUST be stateless to enable horizontal scaling; shared state MUST be externalized (database, cache, message queue)
- **Database Optimization**: Queries MUST use appropriate indexes; N+1 queries MUST be eliminated; query performance MUST be monitored
- **Caching Strategy**: Frequently accessed, rarely changing data MUST be cached; cache invalidation strategy MUST be explicit

**Rationale**: Robust error handling ensures reliability under real-world conditions. Scalability design prevents costly rewrites as usage grows.

### VI. Version Control and Commit Discipline

Version control MUST be used as a development enabler, not an afterthought:

- **Conventional Commits**: All commits MUST follow the Conventional Commits specification:
  - Format: `<type>(<scope>): <description>` (e.g., `feat(auth): add password reset endpoint`)
  - Types: `feat` (new feature), `fix` (bug fix), `docs` (documentation), `style` (formatting), `refactor` (code restructuring), `test` (tests), `chore` (maintenance)
  - Scope is optional but recommended (e.g., `auth`, `api`, `ui`, `db`)
  - Description MUST be lowercase, imperative mood ("add" not "added"), no period at end
  - Body and footer are optional but encouraged for breaking changes and issue references
- **Small, Atomic Commits**: Each commit MUST represent a single logical change that can be understood and reviewed independently
  - Commit after completing each discrete unit of work (e.g., one model, one endpoint, one test)
  - Avoid commits that mix unrelated changes (e.g., feature + refactor + formatting)
  - If a commit message needs "and" to describe what it does, it should be split
- **Feature Branch Workflow**: Every feature, fix, or enhancement MUST be developed in a dedicated branch:
  - Branch naming: `<type>/<issue-number>-<brief-description>` (e.g., `feat/123-user-authentication`, `fix/456-api-timeout`)
  - Branch from `main` for new work; keep branches short-lived (prefer <3 days)
  - Rebase or merge from `main` regularly to avoid large merge conflicts
- **Pull Request Discipline**: Every branch MUST have a dedicated pull request before merging to `main`:
  - PR title MUST follow Conventional Commits format
  - PR description MUST include: what changed, why, testing performed, screenshots (if UI), related issues
  - PRs MUST be kept up-to-date as new commits are pushed to the branch
  - Commit history in PR MUST tell a clear story of feature development
  - Force-push (`git push --force-with-lease`) is allowed on feature branches to clean up history before merge
- **Commit Message Quality**: Commit messages MUST explain the "why" not just the "what":
  - Bad: `fix bug` or `update code`
  - Good: `fix(auth): prevent race condition in token refresh`
  - Body should explain motivation and context when not obvious from diff
- **Work-in-Progress Commits**: WIP commits are acceptable on feature branches but MUST be squashed or amended before PR approval:
  - Use `feat(scope): wip - <description>` for incomplete work
  - Clean up WIP commits with interactive rebase (`git rebase -i`) before requesting review

**Rationale**: Disciplined version control creates an auditable history, simplifies debugging through git bisect, enables atomic reverts, facilitates code review, and allows teams to understand system evolution. Conventional commits enable automated changelog generation and semantic versioning.

### VII. Documentation-First Development and AI Agent Discipline

When AI agents or developers work with external libraries and UI frameworks, current documentation MUST take precedence over training data or assumptions:

- **No Assumptions About External Libraries**: AI agents and developers MUST NEVER assume library behavior, APIs, or syntax based on training data or memory
  - External library ecosystems evolve rapidly; training data becomes outdated quickly
  - Incorrect assumptions lead to bugs, deprecated API usage, and wasted debugging time
- **Mandatory Documentation Lookup via Context7**: Before using any external library or framework (Python packages, npm packages, APIs), agents MUST use the Context7 MCP server to fetch current official documentation
  - Context7 provides real-time access to official docs, changelogs, and migration guides
  - Query Context7 for: installation instructions, API signatures, usage examples, breaking changes, best practices
  - Applies to all external dependencies: FastAPI, SQLModel, Pydantic, React, TanStack Query, etc.
- **UI Component Standards via Shadcn UI**: When creating user interface components, agents MUST use the Shadcn UI MCP server to generate components
  - Shadcn UI ensures consistent design system adherence and accessibility standards
  - Components generated via Shadcn UI are pre-tested, accessible, and follow React best practices
  - Do NOT manually create components that Shadcn UI provides (Button, Input, Dialog, Table, etc.)
  - Agents MAY customize Shadcn components after generation but MUST preserve accessibility attributes
- **Documentation-Driven Implementation**: Implementation MUST follow official documentation patterns and examples
  - If documentation shows a specific pattern (e.g., FastAPI dependency injection), use that pattern
  - If documentation deprecates an API, do NOT use the deprecated approach
  - When documentation conflicts with training data, documentation wins
- **Version-Specific Documentation**: When using Context7, specify package versions to ensure correct documentation
  - Example: Query "FastAPI 0.104.1 dependency injection" not just "FastAPI dependency injection"
  - Check package.json (frontend) or pyproject.toml (backend) for installed versions
- **Documentation Before Code**: For complex integrations or unfamiliar libraries, agents MUST retrieve and review documentation BEFORE writing implementation code
  - Reduces trial-and-error cycles
  - Prevents using deprecated or incorrect APIs
  - Ensures best practices from the start

**Rationale**: AI training data has knowledge cutoffs and cannot track real-time library updates, deprecations, or breaking changes. Relying on assumptions leads to bugs, security vulnerabilities, and technical debt. Mandatory documentation lookup ensures code uses current, supported APIs and patterns. Shadcn UI standardizes component quality and accessibility.

## Development Workflow

### Git Workflow

**Branch Strategy**:
- `main` branch is the production-ready branch; MUST always be deployable
- Feature branches are created from and merged back to `main`
- Hot fixes MAY use `hotfix/*` branches for urgent production issues
- Release branches (`release/*`) MAY be used for release preparation if needed

**Development Cycle**:
1. Create feature branch from latest `main`
2. Make small, atomic commits following Conventional Commits
3. Push commits to remote feature branch regularly (at least daily)
4. Open pull request early (mark as draft if not ready for review)
5. Update PR as you commit new changes; keep PR description current
6. Request review when feature is complete and tests pass
7. Address review feedback with new commits (do not force-push after review starts unless explicitly cleaning up)
8. Squash or merge PR to `main` after approval

**Merge Strategy**:
- Prefer squash merging for feature branches with many small commits
- Use regular merge for feature branches with clean, meaningful commit history worth preserving
- Rebase small, single-commit fixes directly onto `main`
- Delete feature branch after successful merge

### Code Review Requirements

- All code MUST be reviewed by at least one other developer before merging
- Reviews MUST verify constitution compliance (principles I-VII)
- Reviewers MUST validate test coverage and quality
- Reviewers MUST verify commits follow Conventional Commits standard
- Reviewers MUST check that external library usage follows current documentation (not deprecated patterns)
- Reviewers MUST verify UI components use Shadcn UI where applicable
- Security-sensitive changes (authentication, data access, permissions) MUST have additional security-focused review
- Reviewers SHOULD verify commit messages explain the "why" behind changes

### Continuous Integration

- CI pipelines MUST run linting, type checking, unit tests, integration tests, and security scans
- CI MUST validate commit message format against Conventional Commits specification
- PR merge MUST be blocked if CI fails
- Code coverage MUST NOT decrease without explicit justification

### Deployment Process

- Production deployments MUST follow the documented deployment guide
- Database migrations MUST be tested in staging before production
- Rollback procedures MUST be documented and tested
- Deployment automation SHOULD use conventional commit types to determine version bumps

## Governance

### Amendment Procedure

- Constitution amendments require discussion in team meeting or RFC document
- Amendments MUST include rationale, impact analysis, and migration plan for existing code
- All dependent templates (plan, spec, tasks) MUST be updated to reflect changes

### Versioning Policy

- Version follows semantic versioning (MAJOR.MINOR.PATCH)
- MAJOR: Backward incompatible principle removals or redefinitions
- MINOR: New principles added or materially expanded guidance
- PATCH: Clarifications, wording improvements, non-semantic refinements

### Compliance Review

- All PRs MUST self-certify constitution compliance in PR description
- Quarterly constitution review MUST assess alignment with project evolution
- Violations requiring justification MUST be documented in plan.md Complexity Tracking table

### Enforcement

- Constitution supersedes all other practices and guidelines
- Complexity additions (new projects, architectural patterns) MUST be justified against simpler alternatives
- Unjustified constitution violations MUST be refactored before feature completion

**Version**: 1.2.0 | **Ratified**: 2025-11-05 | **Last Amended**: 2025-11-05
