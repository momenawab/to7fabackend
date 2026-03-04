# Tasks: Spec 002 Test Alignment & Gate Stabilization

**Input**: Design documents from `/specs/003-test-alignment-gate/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: This feature IS about test alignment - no separate test tasks needed. Each task validates tests themselves.

**Organization**: Tasks are grouped by user story to enable independent implementation and validation of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Test files: `orders/tests/`, `wallet/tests/`
- Documentation: `specs/003-test-alignment-gate/`, `docs/`
- Contracts: `specs/003-test-alignment-gate/contracts/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create documentation structure and classification templates

- [x] T001 Create test-classification.md template in specs/003-test-alignment-gate/ with columns for test_id, classification, rationale, alignment_status, current_status
- [x] T002 Create deferred-test-debt.md template in specs/003-test-alignment-gate/ with sections for infrastructure, implementation_choice, and future_work tests
- [x] T003 [P] Create gate-verdict.md template in specs/003-test-alignment-gate/ matching the JSON schema from contracts/gate-verdict-schema.json
- [x] T004 [P] Review pytest.ini configuration in pytest.ini to ensure all Spec 002 test files are included in test discovery
- [x] T005 [P] Verify conftest.py in conftest.py has necessary fixtures for Spec 002 tests (user, cart, order, wallet fixtures)

**Checkpoint**: ✅ Documentation templates ready, test infrastructure verified

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Understand current test state and alignment baseline

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 Run full Spec 002 test suite and capture baseline results: `pytest orders/tests/test_spec002_*.py wallet/tests/test_spec002_*.py -v > specs/003-test-alignment-gate/baseline-test-results.txt`
- [x] T007 Review docs/SPEC002_TEST_ALIGNMENT_REPORT.md to understand known failure patterns and alignment issues from 2026-02-07
- [x] T008 Review docs/COVERAGE_REPORT.md to understand current test coverage and pass rates by feature area
- [x] T009 Create test-file-inventory.md in specs/003-test-alignment-gate/ listing all 114 tests with their file locations and current status
- [x] T010 Verify alignment rules from research.md are documented: rule_001 (cancellation HTTP), rule_002 (Cart ORM), rule_003 (Transaction model), rule_004 (status codes)

**Checkpoint**: ✅ Current test state fully documented, alignment rules confirmed

---

## Phase 3: User Story 1 - Test Classification and Alignment (Priority: P1) 🎯 MVP

**Goal**: Manually classify all 114 tests and align non-critical tests to production implementation

**Independent Test**: Run test suite and verify critical business logic tests pass while non-critical tests are either passing or documented as deferred

### Classification for User Story 1

- [x] T011 [P] [US1] Manually review and classify all 35 tests in orders/tests/test_spec002_lifecycle.py using criteria from research.md (state machine tests = critical)
- [x] T012 [P] [US1] Manually review and classify all 19 tests in orders/tests/test_spec002_cancellation.py using criteria from research.md (API contract tests = non-critical)
- [x] T013 [P] [US1] Manually review and classify all 13 tests in orders/tests/test_spec002_order_creation.py using criteria from research.md (API contract tests = non-critical)
- [x] T014 [P] [US1] Manually review and classify all 11 tests in orders/tests/test_spec002_payment.py using criteria from research.md (implementation detail tests = non-critical)
- [x] T015 [P] [US1] Manually review and classify all 13 tests in orders/tests/test_spec002_idempotency.py using criteria from research.md (invariant tests = critical)
- [x] T016 [P] [US1] Manually review and classify all 34 tests in orders/tests/test_spec002_inventory.py using criteria from research.md (infrastructure-dependent = deferred)
- [x] T017 [P] [US1] Manually review and classify all tests in wallet/tests/test_spec002_wallet.py using criteria from research.md (implementation detail tests = non-critical)
- [x] T018 [US1] Document all classification decisions in specs/003-test-alignment-gate/test-classification.md with rationale for each test
- [x] T019 [US1] Count and verify critical test count is 50-60 tests as required by SC-003

### Alignment for User Story 1

- [x] T020 [P] [US1] Apply @pytest.mark.critical decorator to all critical tests in orders/tests/test_spec002_lifecycle.py
- [x] T021 [P] [US1] Apply @pytest.mark.critical decorator to all critical tests in orders/tests/test_spec002_idempotency.py
- [x] T022 [P] [US1] Apply @pytest.mark.non_critical decorator to all non-critical tests in orders/tests/test_spec002_cancellation.py
- [x] T023 [P] [US1] Apply @pytest.mark.non_critical decorator to all non-critical tests in orders/tests/test_spec002_order_creation.py
- [x] T024 [P] [US1] Apply @pytest.mark.non_critical decorator to all non-critical tests in orders/tests/test_spec002_payment.py
- [x] T025 [P] [US1] Apply @pytest.mark.deferred decorator to all deferred tests in orders/tests/test_spec002_inventory.py with @pytest.mark.skip(reason="infrastructure: Redis/Celery not available")
- [x] T026 [P] [US1] Align cancellation tests in orders/tests/test_spec002_cancellation.py: change POST to PUT per rule_001
- [x] T027 [P] [US1] Align cart tests in orders/tests/test_spec002_order_creation.py: replace direct cart.items assignment with cart.add_item() per rule_002
- [x] T028 [P] [US1] Align wallet tests in orders/tests/test_spec002_payment.py and wallet/tests/test_spec002_wallet.py: replace WalletTransaction with Transaction per rule_003
- [x] T029 [P] [US1] Align status code assertions in orders/tests/test_spec002_cancellation.py: accept 200/201/403 per rule_004
- [x] T030 [US1] Update test-classification.md with alignment_status (aligned/needs_alignment/deferred) for each test

### Validation for User Story 1

- [x] T031 [US1] Run aligned test suite: `pytest orders/tests/test_spec002_*.py wallet/tests/test_spec002_*.py -v`
- [x] T032 [US1] Verify all 35 lifecycle tests pass (100% per SC-001)
- [x] T033 [US1] Verify at least 10/13 idempotency tests pass (77%+ per SC-002)
- [x] T034 [US1] Verify test classification document categorizes all 114 tests per SC-004
- [x] T035 [US1] Create before/after comparison in specs/003-test-alignment-gate/alignment-results.md showing pass rate improvement

**Checkpoint**: ✅ User Story 1 complete - all tests classified, pytest marks applied, alignment results documented

---

## Phase 4: User Story 2 - Critical Business Logic Validation (Priority: P2)

**Goal**: Verify all critical business logic tests pass, confirming Spec 002 implementation is functionally correct

**Independent Test**: Run critical test suite only and confirm 100% pass rate on order lifecycle and business invariants

### Validation for User Story 2

- [x] T036 [US2] Run critical tests only: `pytest -m critical orders/tests/test_spec002_*.py wallet/tests/test_spec002_*.py -v`
- [x] T037 [US2] Verify OrderStateMachine transitions: all 35 lifecycle tests passing
- [x] T038 [US2] Verify atomicity guarantees: order creation and cancellation tests passing
- [x] T039 [US2] Verify idempotency enforcement: duplicate prevention tests passing
- [x] T040 [US2] Verify multi-seller aggregation: order splitting by seller tests passing
- [x] T041 [US2] Document any critical test failures in specs/003-test-alignment-gate/critical-test-failures.md with failure analysis
- [x] T042 [US2] If any critical test fails, investigate and determine if it's a bug vs test alignment issue
- [x] T043 [US2] For critical test bugs: document as gate-blocking in critical-test-failures.md
- [x] T044 [US2] For critical test alignment issues: align test and re-run
- [x] T045 [US2] Verify SC-005: no failing critical test indicates business rule violation

**Checkpoint**: ✅ User Story 2 complete - all critical business logic validated, no rule violations

---

## Phase 5: User Story 3 - Deferred Test Debt Documentation (Priority: P3)

**Goal**: Document all tests that cannot be aligned without production changes or missing infrastructure

**Independent Test**: Review deferred test documentation and confirm each deferred test has clear rationale and classification

### Documentation for User Story 3

- [x] T046 [P] [US3] Document infrastructure-deferred tests in specs/003-test-alignment-gate/deferred-test-debt.md with Redis/Celery/payment provider dependencies
- [x] T047 [P] [US3] Document implementation-choice-deferred tests in specs/003-test-alignment-gate/deferred-test-debt.md with production vs spec differences
- [x] T048 [P] [US3] Document future-work-deferred tests in specs/003-test-alignment-gate/deferred-test-debt.md with implementation detail debt items
- [x] T049 [US3] Add @pytest.mark.deferred decorator to all infrastructure-dependent tests with @pytest.mark.skip(reason="...")
- [x] T050 [US3] Add @pytest.mark.deferred decorator to all implementation-choice tests with explanation
- [x] T051 [US3] Add @pytest.mark.deferred decorator to all future-work tests with explanation
- [x] T052 [US3] Count total deferred tests and document in deferred-test-debt.md
- [x] T053 [US3] Verify SC-006: all non-critical failures explicitly documented as deferred debt
- [x] T054 [US3] Verify no deferred test blocks Spec 002 stabilization per acceptance scenario 4

**Checkpoint**: ✅ User Story 3 complete - all deferred tests documented with clear rationale

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Generate gate verdict and finalize documentation

- [x] T055 [P] Generate gate-verdict.json in specs/003-test-alignment-gate/ using contracts/gate-verdict-schema.json with PASS/CONDITIONAL_PASS/FAIL decision
- [x] T056 [P] Create final alignment report in docs/SPEC002_FINAL_ALIGNMENT_REPORT.md summarizing before/after state
- [x] T057 [P] Update docs/COVERAGE_REPORT.md with final pass rates and coverage metrics
- [x] T058 [P] Add quickstart.md reference to specs/003-test-alignment-gate/quickstart.md for future team members
- [x] T059 [P] Create follow-up recommendations in specs/003-test-alignment-gate/recommendations.md for deferred debt resolution
- [x] T060 Run final test suite validation: `pytest orders/tests/test_spec002_*.py wallet/tests/test_spec002_*.py --cov=orders --cov=wallet`
- [x] T061 Verify all success criteria SC-001 through SC-008 are met
- [x] T062 Create gate verdict summary in specs/003-test-alignment-gate/gate-verdict.md with justification and next steps

**Checkpoint**: ✅ Phase 6 complete - All documentation finalized, gate verdict delivered

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational phase completion
- **User Story 2 (Phase 4)**: Depends on User Story 1 completion (needs classification data)
- **User Story 3 (Phase 5)**: Depends on User Story 1 completion (needs alignment data)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on User Story 1 - requires classification data from T011-T019
- **User Story 3 (P3)**: Depends on User Story 1 - requires alignment data from T020-T030

### Within Each User Story

- **User Story 1**: Classification tasks (T011-T017) can run in parallel [P], then T018 consolidates, then alignment tasks (T020-T029) can run in parallel [P], then T030 consolidates, then validation (T031-T035) runs sequentially
- **User Story 2**: Must run sequentially (validation depends on test results)
- **User Story 3**: Documentation tasks (T046-T048) can run in parallel [P] after T031-T035 provide test data

### Parallel Opportunities

- **Setup Phase**: T002, T003, T004, T005 can run in parallel [P]
- **US1 Classification**: T011-T017 can run in parallel [P] (different test files)
- **US1 Alignment**: T020-T029 can run in parallel [P] (different test files)
- **US3 Documentation**: T046-T048 can run in parallel [P] (different sections)
- **Polish Phase**: T055-T059 can run in parallel [P] (different documents)

---

## Parallel Example: User Story 1 Classification

```bash
# Launch all classification tasks together (6 parallel workers):
Task T011: "Classify test_spec002_lifecycle.py"
Task T012: "Classify test_spec002_cancellation.py"
Task T013: "Classify test_spec002_order_creation.py"
Task T014: "Classify test_spec002_payment.py"
Task T015: "Classify test_spec002_idempotency.py"
Task T016: "Classify test_spec002_inventory.py"
Task T017: "Classify test_spec002_wallet.py"

# Once all complete, consolidate results:
Task T018: "Document all classification decisions"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T005)
2. Complete Phase 2: Foundational (T006-T010) - CRITICAL
3. Complete Phase 3: User Story 1 (T011-T035)
4. **STOP and VALIDATE**: All 114 tests classified and documented
5. Gate decision can be made with classification data alone

### Full Implementation (All Stories)

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Tests classified and aligned → Partial gate (need US2 for critical validation)
3. Add User Story 2 → Critical business logic validated → Gate ready (US3 is documentation-only)
4. Add User Story 3 → Deferred debt documented → Complete gate package
5. Polish → Final gate verdict and recommendations

### Sequential Team Strategy

With single developer:

1. Complete Setup (T001-T005)
2. Complete Foundational (T006-T010)
3. Complete User Story 1 (T011-T035) - Takes longest, most critical
4. Complete User Story 2 (T036-T045) - Depends on US1 classification
5. Complete User Story 3 (T046-T054) - Depends on US1 alignment
6. Complete Polish (T055-T062)

---

## Notes

- [P] tasks = different files, no execution dependencies
- [US1/US2/US3] labels map tasks to user stories for traceability
- User Story 1 is the MVP - classification enables gate decision
- User Story 2 validates critical path - required for gate
- User Story 3 is documentation polish - nice to have but not gate-blocking
- Manual classification is intentional per clarification session 2026-02-07
- Test execution order matters: run tests, then classify, then align, then validate
- Commit after each logical task group (e.g., after each test file classification)
- Stop at checkpoint T035 to validate US1 independently before proceeding
- Stop at checkpoint T045 to validate US2 independently before proceeding
