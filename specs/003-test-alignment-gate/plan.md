# Implementation Plan: Spec 002 Test Alignment & Gate Stabilization

**Branch**: `003-test-alignment-gate` | **Date**: 2026-02-07 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-test-alignment-gate/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Classify all 114 Spec 002 tests into critical (gate-blocking) and non-critical categories through **manual developer review**, align non-critical tests to actual production implementation boundaries, and document deferred test debt. The goal is to establish a reliable quality gate where all critical business logic tests (state machine, atomicity, idempotency) pass while non-critical test failures are explicitly documented. Technical approach: manual test review and classification, followed by targeted test code modifications (not production code) to match implementation reality.

## Technical Context

**Language/Version**: Python 3.14.2
**Primary Dependencies**: Django 4.2.13, Django REST Framework 3.16.0, pytest-django 4.5.2
**Storage**: MySQL (via mysqlclient 2.2.7)
**Testing**: pytest with pytest-django, Django test framework
**Target Platform**: Linux server (Django backend)
**Project Type**: Web application (backend API)
**Performance Goals**: Test suite execution time <5 minutes for full Spec 002 suite
**Constraints**: No production code changes, no model refactoring, no new infrastructure, manual classification process (not automated)
**Scale/Scope**: 114 tests across 6 test files (lifecycle, cancellation, order creation, payment, idempotency, inventory)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Code Quality
✅ **PASS** - This feature modifies test code only, not production code. Test modifications will follow single responsibility principle, use descriptive naming, and include clear docstrings explaining alignment rationale.

### Principle II: Testing Standards
✅ **PASS** - This feature IS about testing standards. All aligned tests will:
- Follow naming convention: `test_<action>_<condition>_<expected_result>`
- Be deterministic (no flaky tests)
- Run in isolation where possible
- Maintain minimum 80% coverage on critical business logic paths

### Principle III: User Experience Consistency
✅ **PASS** - Not directly applicable (test-only changes), but test fixtures will use consistent error response formats matching production API standards.

### Principle IV: Performance Requirements
✅ **PASS** - Test suite execution will remain under 5 minutes. No test will introduce N+1 query patterns in test fixtures. Background processing tests will mock Celery/Redis appropriately.

### Development Workflow
✅ **PASS** - Branch naming convention followed: `003-test-alignment-gate`. All commits will follow conventional commits format with `test` or `docs` scope. Changes will be documented in test alignment report.

### Quality Gates
✅ **PASS** - All modified tests must pass CI (100% pass rate). No reduction in coverage. No new security vulnerabilities introduced.

## Project Structure

### Documentation (this feature)

```text
specs/003-test-alignment-gate/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output (test classification research)
├── data-model.md        # Phase 1 output (test metadata model)
├── quickstart.md        # Phase 1 output (test alignment guide)
├── contracts/           # Phase 1 output (gate criteria contract)
└── tasks.md             # Phase 2 output (implementation tasks)
```

### Source Code (repository root)

```text
# Django backend application
orders/
├── tests/
│   ├── test_spec002_lifecycle.py        # 35 tests - state machine
│   ├── test_spec002_cancellation.py     # 19 tests - cancellation API
│   ├── test_spec002_order_creation.py   # 13 tests - order creation API
│   ├── test_spec002_payment.py          # 11 tests - wallet/payment
│   ├── test_spec002_idempotency.py      # 13 tests - business invariants
│   └── test_spec002_inventory.py        # 34 tests - stock management
wallet/
└── tests/
    └── test_spec002_wallet.py           # Wallet transaction tests

# Documentation (existing)
docs/
├── SPEC002_TEST_ALIGNMENT_REPORT.md     # Baseline alignment data
└── COVERAGE_REPORT.md                    # Current test coverage

# Test infrastructure
pytest.ini                                # pytest configuration
conftest.py                               # Shared test fixtures
```

**Structure Decision**: Standard Django multi-app structure. Tests are co-located with the code they test (orders/tests, wallet/tests). Documentation lives in docs/ for existing reports and specs/ for spec-kit artifacts.

## Complexity Tracking

> **No violations to justify** - All constitutional gates passed. This feature is test-only, maintains existing code quality standards, and does not introduce complexity.

## Phase 0: Research & Test Classification

### Research Tasks

1. **Test Classification Criteria Research**
   - Objective: Define clear criteria for critical vs non-critical tests
   - Context: 114 tests need classification; current baseline is 54 passing
   - Decision needed: What makes a test "gate-blocking"?

2. **Production Implementation Survey**
   - Objective: Catalog actual API endpoints, model names, method signatures
   - Context: Tests expect PUT /orders/{id}/cancel/, Transaction model, Cart.add_item()
   - Sources: orders/views.py, orders/models.py, cart/models.py, wallet/models.py

3. **Failure Pattern Analysis**
   - Objective: Categorize failure types from SPEC002_TEST_ALIGNMENT_REPORT.md
   - Context: 60 failing tests with known patterns (403/405 errors, signature mismatches)
   - Sources: docs/SPEC002_TEST_ALIGNMENT_REPORT.md

4. **Infrastructure Dependency Mapping**
   - Objective: Identify tests requiring unavailable infrastructure
   - Context: Redis, Celery runtime, payment providers not available
   - Decision needed: Which infrastructure gaps justify deferring tests?

### Research Output

All findings consolidated in `research.md` with:
- **Decision**: Classification criteria chosen (critical = business logic, non-critical = API contract)
- **Rationale**: Manual review ensures thoughtful classification
- **Alternatives considered**: Automated classification (rejected as overkill for one-time effort)

## Phase 1: Design Artifacts

### data-model.md
Define test metadata model:
- TestClassification entity (critical/non-critical/deferred)
- AlignmentRule entity (implementation mapping)
- GateCriteria entity (pass conditions)

### contracts/
Define gate verdict contract:
- Input: Test results, classification, alignment status
- Output: PASS/CONDITIONAL_PASS/FAIL with justification
- Format: JSON schema for automated gate checking

### quickstart.md
Developer guide for test alignment:
- How to manually classify a test (step-by-step process)
- Common alignment patterns (Cart ORM, HTTP methods, model names)
- How to document deferred debt
- Troubleshooting guide

## Phase 2: Implementation (tasks.md)

**NOTE**: tasks.md will be generated by `/speckit.tasks` command, not by this plan.

Expected task categories:
1. **Manual test classification** (developer reviews each of 114 tests)
2. **Test code alignment** (Cart ORM, HTTP methods, model names)
3. **Deferred debt documentation** (infrastructure, implementation choices)
4. **Gate verdict generation** (produce final decision document)
5. **Test suite validation** (run tests, verify critical tests pass)

## Success Metrics

- **SC-001**: All 35 lifecycle tests pass (100%)
- **SC-002**: 10/13 idempotency tests pass (77%+)
- **SC-003**: 50-60 tests classified as critical with documented rationale
- **SC-004**: All 114 tests categorized (critical/aligned/deferred)
- **SC-005**: No failing critical test indicates business rule violation
- **SC-006**: All non-critical failures documented as deferred debt
- **SC-007**: Gate verdict document produced
- **SC-008**: Team can distinguish bugs from alignment issues

## Clarifications Applied

From spec clarification session (2026-02-07):
- **Classification Method**: Manual review by developer (not automated)
  - Rationale: One-time stabilization effort; automation overkill
  - Impact: FR-001 updated, constraint added, US1 acceptance scenario updated
