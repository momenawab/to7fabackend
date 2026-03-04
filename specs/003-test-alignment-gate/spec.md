# Feature Specification: Spec 002 Test Alignment & Gate Stabilization

**Feature Branch**: `003-test-alignment-gate`
**Created**: 2026-02-07
**Status**: Draft
**Input**: User description: "Spec 003 – Spec 002 Test Alignment & Gate Stabilization"

## Clarifications

### Session 2026-02-07

- Q: How should test classification be performed? → A: Manual review - Developer manually reviews each test and applies classification with documented rationale

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Test Classification and Alignment (Priority: P1)

Development team needs to categorize all Spec 002 tests into critical (gate-blocking) and non-critical categories, then align the tests to match the actual production implementation without modifying business logic.

**Why this priority**: This is the foundation for establishing a reliable quality gate. Without proper classification and alignment, the team cannot distinguish between real defects and test implementation issues, blocking release decisions.

**Independent Test**: Can be fully tested by running the updated test suite and verifying that critical business logic tests pass while non-critical tests are either fixed or documented as deferred debt.

**Acceptance Scenarios**:

1. **Given** 114 Spec 002 tests exist, **When** developer manually reviews each test and categorizes it, **Then** each test is marked as critical or non-critical with clear rationale documented
2. **Given** tests classified as non-critical due to implementation mismatches, **When** tests are aligned to actual implementation, **Then** previously failing tests now pass without code changes
3. **Given** tests requiring Cart ORM usage, **When** direct JSON assignment is replaced with Cart.add_item() or CartItem ORM, **Then** cart-related tests pass
4. **Given** cancellation tests using POST method, **When** updated to use PUT /orders/{id}/cancel/, **Then** cancellation endpoint tests pass
5. **Given** wallet transaction tests expecting WalletTransaction model, **When** updated to use Transaction model, **Then** wallet tests pass or fail for valid business reasons only

---

### User Story 2 - Critical Business Logic Validation (Priority: P2)

Quality assurance team needs to verify that all critical business invariants and state machine behaviors pass tests, confirming Spec 002 production implementation is functionally correct.

**Why this priority**: This validates the core business logic that cannot fail. State transitions, atomicity, and idempotency are fundamental to order and payment correctness.

**Independent Test**: Can be fully tested by running the critical test suite and confirming 100% pass rate on order lifecycle, state transitions, and business invariants.

**Acceptance Scenarios**:

1. **Given** OrderStateMachine implementation, **When** all lifecycle tests execute, **Then** all 35 state transition tests pass (currently passing)
2. **Given** order creation with atomic transaction, **When** creation fails mid-transaction, **Then** no partial order is created and stock is not reserved
3. **Given** order cancellation with refund, **When** cancellation completes, **Then** stock is released, wallet is refunded, and order state is CANCELLED
4. **Given** duplicate order request with same idempotency key, **When** second request is processed, **Then** existing order is returned without creating duplicates
5. **Given** multi-seller order, **When** order is created, **Then** orders are correctly aggregated by seller with appropriate stock reservations

---

### User Story 3 - Deferred Test Debt Documentation (Priority: P3)

Development team needs to document all tests that cannot be aligned without modifying production code or implementing missing infrastructure, creating a clear record of technical debt for future resolution.

**Why this priority**: This prevents endless debugging of test failures that are out of scope for the current gate, while ensuring important issues are tracked for future work.

**Independent Test**: Can be fully tested by reviewing the deferred test documentation and confirming each deferred test has a clear rationale and classification (infrastructure missing, implementation choice, or future work).

**Acceptance Scenarios**:

1. **Given** failing tests requiring external infrastructure, **When** infrastructure is unavailable (Redis, Celery runtime), **Then** tests are marked as deferred with infrastructure dependency noted
2. **Given** API endpoint tests returning 403 or 405, **When** investigation shows implementation differs from spec, **Then** tests are deferred with note about implementation vs spec discrepancy
3. **Given** internal coordinator function tests with signature mismatches, **When** refactoring would change production code (out of scope), **Then** tests are deferred as implementation detail debt
4. **Given** all deferred tests documented, **When** gate review occurs, **Then** no deferred test blocks Spec 002 stabilization

---

### Edge Cases

- What happens when test alignment reveals legitimate production bugs vs implementation choices?
  - **Resolution**: Document legitimate bugs separately from implementation choices; bugs may block gate, implementation choices do not
- How should tests handle ambiguous spec requirements where production made a reasonable choice?
  - **Resolution**: Align tests to production implementation and document the choice; spec may be updated in future iterations
- What if critical tests cannot be made to pass without modifying production code?
  - **Resolution**: This is a gate-blocking condition that must be escalated; spec definition states code alone is insufficient
- How should the team handle tests that pass but test the wrong thing?
  - **Resolution**: These should be identified during classification, marked as non-critical, and either fixed or deferred

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST classify each of the 114 Spec 002 tests as either critical (gate-blocking) or non-critical (non-blocking) with documented rationale via manual review by developer
- **FR-002**: System MUST align all non-critical tests to actual production implementation boundaries (Cart ORM, HTTP methods, model names)
- **FR-003**: System MUST ensure all critical business logic tests pass before Spec 002 can be marked as STABLE
- **FR-004**: System MUST document all deferred test debt with clear categorization (infrastructure missing, implementation choice, future work)
- **FR-005**: System MUST verify OrderStateMachine transitions and invariants through passing tests (35/35 lifecycle tests)
- **FR-006**: System MUST verify atomicity guarantees for order creation and cancellation through passing tests
- **FR-007**: System MUST verify idempotency enforcement prevents duplicate orders and duplicate payments
- **FR-008**: System MUST verify multi-seller aggregation logic correctly splits orders by seller
- **FR-009**: System MUST create a categorized test list showing gate-critical, aligned, and deferred tests
- **FR-010**: System MUST generate a gate verdict document for Spec 002 with pass/fail status and justification

### Key Entities

- **Test Case**: A single test method with classification (critical/non-critical), alignment status, and pass/fail result
- **Test Suite**: A collection of related test files (lifecycle, cancellation, order creation, payment, idempotency, inventory)
- **Gate Criteria**: The conditions that must be met for Spec 002 to be considered STABLE (all critical tests pass, no business rule violations, remaining failures documented as deferred debt)
- **Deferred Debt**: A test that cannot pass without out-of-scope changes (new infrastructure, production code modifications, model refactoring)
- **Alignment Rule**: A specific mapping between test expectations and actual implementation (e.g., PUT for cancellation, Transaction model name, Cart.add_item() method)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 35 OrderStateMachine lifecycle tests pass (100% pass rate for state transitions and invariants)
- **SC-002**: At least 10/13 idempotency tests pass, verifying core atomicity and business invariants
- **SC-003**: All critical tests identified and classified with documented rationale (target: 50-60 critical tests out of 114 total)
- **SC-004**: Test classification document categorizes all 114 tests into gate-critical, aligned, or deferred with clear criteria
- **SC-005**: No failing critical test indicates a violation of core business rules (atomicity, consistency, correctness)
- **SC-006**: All non-critical test failures are explicitly documented as deferred debt with infrastructure, implementation, or future-work categorization
- **SC-007**: Gate verdict document produced with clear PASS/CONDITIONAL PASS/FAIL decision and justification
- **SC-008**: Development team can run test suite and distinguish between business logic failures (must fix) and test alignment issues (defer or fix tests)

## Assumptions

1. **Production Implementation is Correct**: The spec assumes that production code implementation choices (e.g., allowing cancellation in PROCESSING state) are intentional and should drive test alignment, not the other way around
2. **No Production Code Changes**: Test alignment must not modify production business logic, models, or API endpoints—only tests are updated
3. **Infrastructure Gaps are Known**: Missing external infrastructure (Redis, Celery runtime, payment providers) is accepted as out-of-scope and tests depending on these will be deferred
4. **Existing Alignment Report**: The SPEC002_TEST_ALIGNMENT_REPORT.md (2026-02-07) provides baseline data showing 54/114 tests passing before this alignment work
5. **Critical Path Definition**: Core business logic is defined as state machine, atomicity, idempotency, and multi-seller aggregation—API endpoint specifics are secondary
6. **Test Debt is Temporary**: Deferred tests represent technical debt that will be addressed in future specs but should not block the current gate

## Constraints

- **No New Features**: This spec cannot add new endpoints, modify business logic, or implement missing infrastructure
- **No Model Refactoring**: Changes to domain models (Order, Wallet, Transaction) are out of scope
- **Gate-Blocking Criteria**: Spec 002 cannot be marked STABLE until all critical tests pass
- **Manual Classification Process**: Test classification requires manual developer review of each test with documented rationale (not automated)
- **Time Bound**: Test alignment should be completed efficiently to avoid extended gate delays
- **Backward Compatibility**: Aligned tests must continue to validate the intended business behaviors

## Dependencies

- **Spec 002 Implementation**: All tasks from spec-002/tasks.md must be implemented in production code (already complete)
- **Existing Test Suite**: 114 tests across 6 test files must exist and be runnable
- **Alignment Report**: SPEC002_TEST_ALIGNMENT_REPORT.md provides baseline failure analysis
- **Coverage Report**: COVERAGE_REPORT.md documents current test coverage and pass rates
- **Test Infrastructure**: pytest, Django test framework, and test fixtures must be functional

## Out of Scope

- Adding new API endpoints or modifying existing endpoint behavior
- Implementing missing external infrastructure (Redis, Celery runtime, payment providers)
- Refactoring domain models or changing database schema
- Modifying production business logic or state machine rules
- Performance testing or load testing
- Security testing or penetration testing
- End-to-end integration testing with external services
