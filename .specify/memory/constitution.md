<!--
================================================================================
SYNC IMPACT REPORT
================================================================================
Version Change: 0.0.0 → 1.0.0
Bump Rationale: MAJOR - Initial constitution creation with 4 core principles

Added Sections:
  - Principle I: Code Quality
  - Principle II: Testing Standards
  - Principle III: User Experience Consistency
  - Principle IV: Performance Requirements
  - Development Workflow
  - Quality Gates

Templates Status:
  ✅ plan-template.md - Constitution Check section available for gates
  ✅ spec-template.md - Requirements align with UX consistency principle
  ✅ tasks-template.md - Test phases align with Testing Standards principle

Follow-up TODOs: None
================================================================================
-->

# To7fa Backend Constitution

## Core Principles

### I. Code Quality

All code MUST adhere to maintainable, readable, and well-structured standards. This principle is NON-NEGOTIABLE.

**Mandatory Rules:**

- **Single Responsibility**: Every module, class, and function MUST have exactly one clear purpose. If a component cannot be explained in one paragraph, it MUST be split.
- **File Size Limit**: No single file SHALL exceed 300 lines of code (excluding comments and blank lines). Files approaching this limit MUST trigger refactoring.
- **Naming Conventions**: All identifiers MUST be descriptive and self-documenting. Abbreviations are prohibited unless universally understood (e.g., `id`, `url`, `api`).
- **No Dead Code**: Unused imports, commented-out code blocks, and unreachable code MUST be removed before merge.
- **Linting Enforcement**: All code MUST pass configured linting rules (flake8/pylint for Python, ESLint for JavaScript). Zero warnings in production code.
- **Documentation**: All public APIs, modules, and complex logic MUST have docstrings/comments explaining the "why", not just the "what".

**Rationale**: Code is read far more often than it is written. Poor code quality compounds into technical debt that slows development and introduces bugs.

---

### II. Testing Standards

All features MUST have corresponding tests. Testing is NOT optional; it is a first-class development activity.

**Mandatory Rules:**

- **Test Coverage Threshold**: Critical paths MUST have minimum 80% line coverage. New code contributions MUST maintain or improve coverage.
- **Test Types Required**:
  - **Unit Tests**: For all business logic and utility functions. MUST run in isolation without external dependencies.
  - **Integration Tests**: For API endpoints, database operations, and service interactions.
  - **Contract Tests**: For all external API boundaries.
- **Test-First for Bug Fixes**: Every bug fix MUST have a reproducing test written BEFORE the fix is implemented.
- **Test Naming**: Test functions MUST follow the pattern `test_<action>_<condition>_<expected_result>` (e.g., `test_login_with_invalid_password_returns_401`).
- **No Flaky Tests**: Tests MUST be deterministic. Any test that fails intermittently MUST be fixed or quarantined immediately.
- **CI Enforcement**: All tests MUST pass in CI before any merge to main/staging branches.

**Rationale**: Tests are executable documentation and the primary defense against regressions. Without reliable tests, refactoring becomes dangerous and velocity decreases over time.

---

### III. User Experience Consistency

The API and all user-facing interactions MUST provide a predictable, consistent experience.

**Mandatory Rules:**

- **Error Response Format**: All error responses MUST follow a consistent JSON schema:
  ```json
  {
    "error": "<error_code>",
    "message": "<human_readable_message>",
    "details": {}
  }
  ```
- **Status Codes**: HTTP status codes MUST be used correctly and consistently (400 for client errors, 500 for server errors, 401 for auth failures, 403 for forbidden, 404 for not found).
- **Pagination**: All list endpoints returning more than 20 items MUST support pagination with consistent `page`, `page_size`, `total`, and `next`/`previous` fields.
- **Response Structure**: Successful responses MUST include the resource in a `data` field for single resources or `results` for collections.
- **Validation Messages**: Input validation errors MUST specify which field failed and why, in a machine-readable format.
- **API Versioning**: Breaking changes MUST be versioned (e.g., `/api/v1/`, `/api/v2/`). Existing versions MUST remain stable.
- **Deprecation Policy**: Deprecated endpoints MUST include deprecation headers and documentation with migration paths for at least one release cycle.

**Rationale**: Consistent APIs reduce integration friction, minimize support burden, and build trust with API consumers.

---

### IV. Performance Requirements

The system MUST meet defined performance thresholds. Performance is a feature, not an afterthought.

**Mandatory Rules:**

- **Response Time Targets**:
  - API endpoints MUST respond within 200ms (p50) and 500ms (p95) under normal load.
  - Database queries MUST NOT exceed 100ms individually. Queries exceeding this MUST be optimized or cached.
- **Query Optimization**: N+1 query patterns are PROHIBITED. All database interactions MUST use appropriate prefetching/joins.
- **Caching Strategy**: Frequently accessed, rarely changed data MUST be cached. Cache invalidation strategy MUST be documented.
- **Payload Size**: API responses MUST NOT exceed 1MB without explicit pagination or streaming. Large responses MUST support field selection or filtering.
- **Background Processing**: Long-running operations (>3 seconds) MUST be moved to background tasks with progress tracking.
- **Database Indexing**: All fields used in WHERE clauses or ORDER BY operations with significant table sizes MUST have appropriate indexes.
- **Monitoring**: All production endpoints MUST have performance metrics (response time, throughput, error rate) collected and monitored.

**Rationale**: Poor performance directly impacts user experience and system reliability. Performance issues are often discovered late and expensive to fix.

---

## Development Workflow

All development MUST follow a structured workflow ensuring quality and traceability.

**Process Requirements:**

1. **Branch Strategy**: Feature branches MUST follow naming convention `<type>/<issue-number>-<description>` (e.g., `feature/123-add-payment-gateway`).
2. **Commit Messages**: All commits MUST follow conventional commits format: `<type>(<scope>): <description>`. Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`.
3. **Code Review**: All changes MUST be reviewed by at least one team member before merge. Reviewers MUST verify:
   - Code quality principles are followed
   - Tests are present and meaningful
   - Performance implications are considered
4. **No Direct Pushes**: Direct pushes to `main` and `staging` branches are PROHIBITED. All changes MUST go through pull requests.
5. **Issue Tracking**: All work MUST be linked to an issue. No orphan commits.

---

## Quality Gates

All changes MUST pass these gates before deployment.

| Gate | Criteria | Enforcement |
|------|----------|-------------|
| **Linting** | Zero errors, zero warnings | CI automated |
| **Unit Tests** | 100% pass rate | CI automated |
| **Integration Tests** | 100% pass rate | CI automated |
| **Coverage** | ≥80% on critical paths | CI automated |
| **Security Scan** | No high/critical vulnerabilities | CI automated |
| **Code Review** | ≥1 approval | GitHub/GitLab enforced |
| **Performance** | No regression >10% | Manual review (pre-release) |

---

## Governance

This Constitution supersedes all other development practices and conventions within the To7fa Backend project.

**Amendment Process:**

1. **Proposal**: Any team member MAY propose amendments through a documented RFC (Request for Comments).
2. **Discussion**: Proposals MUST be discussed for a minimum of 48 hours.
3. **Approval**: Amendments require consensus from core maintainers.
4. **Documentation**: All amendments MUST be documented with:
   - Rationale for change
   - Migration plan for existing code
   - Updated version number

**Compliance:**

- All pull requests MUST verify compliance with these principles.
- Violations MUST be justified in writing and approved by a maintainer.
- Repeated violations SHOULD trigger process review.

**Guidance**: For runtime development guidance and implementation patterns, refer to project documentation and the spec-kit workflow artifacts.

**Version**: 1.0.0 | **Ratified**: 2026-01-15 | **Last Amended**: 2026-01-15
