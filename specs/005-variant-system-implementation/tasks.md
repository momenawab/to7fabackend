# Tasks: Variant System Implementation

**Input**: Design documents from `/specs/005-variant-system-implementation/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Invariant tests are REQUIRED per Spec 004 - 19 invariants must be enforced.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Django project structure: `products/`, `orders/`, `cart/` apps
- Tests: `products/tests/`, `orders/tests/`, `cart/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Verify Django project structure and dependencies (Python 3.14.2, Django 4.2.13, DRF 3.16.0)
- [x] T002 [P] Configure warnings module for deprecation logging in settings.py (add `logging.captureWarnings(True)` and configure 'py.warnings' logger)
- [x] T003 [P] Verify pytest-django 4.5.2 is configured in pytest.ini

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Review existing Product, ProductCategoryVariantOption, ProductVariant models in products/models.py (verify stock_count fields exist, document current implementation)
- [x] T005 Review existing OrderItem model in orders/models.py (verify variant_id field exists and is nullable, document current implementation)
- [x] T006 Review existing CartItem model in cart/models.py (verify variant_id and selected_variants fields exist, document current implementation)
- [x] T007 Review existing StockLockManager in orders/atomic_order_system.py (verify reserve_stock/release_stock methods, document current implementation)
- [x] T008 Create test directories for invariant tests: products/tests/, orders/tests/, cart/tests/

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Variant System Canonicalization (Priority: P1) 🎯 MVP

**Goal**: Enforce that ProductCategoryVariantOption is the single source of truth for variant stock and pricing.

**Independent Test**:
- Create products with variants, verify stock operations only use ProductCategoryVariantOption.stock_count
- Confirm ProductVariant fallback returns deprecation warnings
- Verify combination_stocks is ignored in stock calculations

### Invariant Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T009 [P] [US1] Create test_invariants.py in products/tests/ with INV-014 test (only ProductCategoryVariantOption can own stock)
- [x] T010 [P] [US1] Create INV-015 test in products/tests/test_invariants.py (new products use ProductCategoryVariantOption)
- [x] T011 [P] [US1] Create INV-016 test in products/tests/test_invariants.py (combination_stocks not used for stock)
- [x] T012 [P] [US1] Create INV-001 test in orders/tests/test_invariants.py (stock only mutated via StockLockManager in atomic blocks)
- [x] T013 [P] [US1] Create INV-002 test in orders/tests/test_invariants.py (stock checks after select_for_update() lock)
- [x] T014 [P] [US1] Create INV-003 test in orders/tests/test_invariants.py (cancelled order restores stock to exact variant)
- [x] T015 [P] [US1] Create INV-004 test in orders/tests/test_invariants.py (stock never goes negative)
- [x] T016 [P] [US1] Create INV-005 test in orders/tests/test_invariants.py (Product.stock_quantity not used for variant products)

### Implementation for User Story 1

- [x] T017 [US1] Add deprecation warning docstring to ProductVariant model in products/models.py (lines 578-628)
- [x] T018 [US1] Add deprecation warning to Product.stock property when variants exist in products/models.py
- [x] T019 [US1] Update Product.stock property to ignore combination_stocks in products/models.py (return sum of ProductCategoryVariantOption.stock_count)
- [x] T020 [US1] Add deprecation warning to combination_stocks field getter in products/models.py (logs warning when accessed)
- [x] T021 [US1] Add ValueError to combination_stocks setter in products/models.py (prevents writing to deprecated field)
- [x] T022 [US1] Update StockLockManager to log deprecation when ProductVariant is accessed in orders/atomic_order_system.py (lines 248-305)
- [x] T023 [US1] Add deprecation warning helper function in orders/atomic_order_system.py (logs warning with call stack)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Variant Identification Consistency (Priority: P1)

**Goal**: Ensure OrderItem.variant_id unambiguously references ProductCategoryVariantOption for correct stock restoration.

**Independent Test**:
- Create orders with variants, cancel/refund them
- Verify stock is restored to the exact ProductCategoryVariantOption referenced by variant_id
- Confirm legacy orders with old variant_ids are handled gracefully

### Invariant Tests for User Story 2

- [x] T024 [P] [US2] Create INV-006 test in orders/tests/test_invariants.py (OrderItem always has valid product.id)
- [x] T025 [P] [US2] Create INV-007 test in orders/tests/test_invariants.py (OrderItem.variant_id is NULL or valid ProductCategoryVariantOption.id)
- [x] T026 [P] [US2] Create INV-008 test in orders/tests/test_invariants.py (reservation_status transitions follow rules)
- [x] T027 [P] [US2] Create INV-009 test in orders/tests/test_invariants.py (order with released item cannot transition to paid)

### Implementation for User Story 2

- [x] T028 [US2] Update OrderItem.variant_id field documentation in orders/models.py (clarifies it references ProductCategoryVariantOption.id)
- [x] T029 [US2] Add variant_id validation comment in OrderItem model in orders/models.py (notes migration requirement for legacy data)
- [x] T030 [US2] Update AtomicOrderCreator.create_order to validate variant_id references ProductCategoryVariantOption in orders/atomic_order_system.py (lines 646-1014)
- [x] T031 [US2] Update StockLockManager.release_stock to use variant_id for ProductCategoryVariantOption lookup in orders/atomic_order_system.py (lines 248-305)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Product Approval & Visibility Enforcement (Priority: P1)

**Goal**: Enforce that only approved products are visible in public listings, can be added to cart, and can be included in orders.

**Independent Test**:
- Create products with approval_status='pending', 'approved', 'rejected'
- Verify only 'approved' products appear in public listings
- Confirm cart operations reject unapproved products
- Verify order creation hard-fails on unapproved products

### Invariant Tests for User Story 3

- [x] T032 [P] [US3] Create INV-010 test in products/tests/test_invariants.py (unapproved products not in public listings)
- [x] T033 [P] [US3] Create INV-011 test in products/tests/test_invariants.py (unapproved products cannot be added to cart)
- [x] T034 [P] [US3] Create INV-012 test in products/tests/test_invariants.py (unapproved products cannot be in orders)
- [x] T035 [P] [US3] Create INV-013 test in products/tests/test_invariants.py (approval requires is_active=True)

### Implementation for User Story 3

- [x] T036 [P] [US3] Add ProductQuerySet with approved() manager in products/models.py (filters by is_active=True AND approval_status='approved')
- [x] T037 [P] [US3] Update Product.objects to use ProductQuerySet.as_manager() in products/models.py
- [x] T038 [P] [US3] Add validation for approval_status='approved' requiring is_active=True in Product.clean() method in products/models.py
- [x] T039 [US3] Update product listing views to use approved() manager in products/views.py (public endpoints only)
- [x] T040 [US3] Add approval_status validation to cart add item endpoint in cart/views.py (returns 400 error if not approved)
- [x] T041 [US3] Add approval_status validation to AtomicOrderCreator.create_order in orders/atomic_order_system.py (hard-fail with explicit error)
- [x] T042 [US3] Add ProductVisibilityError exception class in orders/atomic_order_system.py (for approval validation failures)
- [x] T043 [US3] Update Product serializer to include deprecation notice for variant fields in products/serializers.py

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - Cart Data Structure Canonicalization (Priority: P2)

**Goal**: Enforce that variant_id is the source of truth for cart inventory operations, deprecating selected_variants.

**Independent Test**:
- Add items to cart with variant_id
- Verify stock checks use variant_id
- Confirm selected_variants is ignored for inventory

### Invariant Tests for User Story 4

- [x] T044 [P] [US4] Create INV-017 test in cart/tests/test_invariants.py (CartItem.variant_id is valid ProductCategoryVariantOption or NULL)
- [x] T045 [P] [US4] Create INV-018 test in cart/tests/test_invariants.py (CartItem cannot reference inactive variant)
- [x] T046 [P] [US4] Create INV-019 test in cart/tests/test_invariants.py (CartItem cannot reference zero-stock variant)

### Implementation for User Story 4

- [x] T047 [US4] Add deprecation warning to selected_variants usage in cart/services/ (logs warning when used for inventory)
- [x] T048 [US4] Update cart operations to validate variant_id references active ProductCategoryVariantOption in cart/services/
- [x] T049 [US4] Update cart operations to validate variant_id references ProductCategoryVariantOption with stock_count > 0 in cart/services/
- [x] T050 [US4] Add selected_variants deprecation comment to CartItem model in cart/models.py (clarifies display-only usage)

**Checkpoint**: At this point, all P1 and P2 user stories should be independently functional

---

## Phase 7: User Story 5 - Deprecation & Cleanup Enforcement (Priority: P3)

**Goal**: Mark deprecated systems as read-only and prevent new code from using them.

**Independent Test**:
- Attempt to use deprecated systems in new code paths
- Verify appropriate warnings or errors are raised
- Confirm deprecation warnings appear in logs

### Implementation for User Story 5

- [x] T051 [P] [US5] Add deprecation warning to ProductVariant stock property getter in products/models.py
- [x] T052 [P] [US5] Add deprecation warning to ProductVariant price_adjustment property getter in products/models.py
- [x] T053 [US5] Add deprecation warning to selected_variants field access in cart/models.py
- [x] T054 [US5] Update all relevant docstrings to include DEPRECATED notices in products/models.py
- [x] T055 [US5] Configure Django logging to capture deprecation warnings in settings.py (completed in Phase 1)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T056 [P] Add database index for OrderItem.variant_id in orders/migrations/ (for stock restoration lookups)
- [x] T057 [P] Add composite index on Product(is_active, approval_status) in products/migrations/ (for approved() manager)
- [x] T058 [P] Add composite index on ProductCategoryVariantOption(product, is_active) in products/migrations/ (for variant queries)
- [x] T059 Run all invariant tests and verify 19 invariants pass (pytest products/tests/test_invariants.py orders/tests/test_invariants.py cart/tests/test_invariants.py)
- [x] T060 Run quickstart.md validation steps from specs/005-variant-system-implementation/quickstart.md
- [x] T061 Update API documentation to reflect approval requirements in docs/
- [x] T062 Code cleanup and verify no linting errors (install and run ruff check ., or flake8 . per project configuration)
- [x] T063 [P] Verify test coverage meets 80% threshold per constitution (pytest --cov=products --cov=orders --cov=cart --cov-report=term-missing)
- [ ] T064 Verify existing order/cart/stock regression tests still pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - No dependencies on US1
- **User Story 3 (P1)**: Can start after Foundational (Phase 2) - No dependencies on US1/US2
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - No dependencies on US1/US2/US3
- **User Story 5 (P3)**: Can start after Foundational (Phase 2) - No dependencies on other stories

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Model changes before service changes
- Service changes before API changes
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- P1 user stories (US1, US2, US3) can be worked on in parallel by different team members
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "T009 [P] [US1] Create test_invariants.py in products/tests/ with INV-014 test"
Task: "T010 [P] [US1] Create INV-015 test in products/tests/test_invariants.py"
Task: "T011 [P] [US1] Create INV-016 test in products/tests/test_invariants.py"
Task: "T012 [P] [US1] Create INV-001 test in orders/tests/test_invariants.py"
Task: "T013 [P] [US1] Create INV-002 test in orders/tests/test_invariants.py"
Task: "T014 [P] [US1] Create INV-003 test in orders/tests/test_invariants.py"
Task: "T015 [P] [US1] Create INV-004 test in orders/tests/test_invariants.py"
Task: "T016 [P] [US1] Create INV-005 test in orders/tests/test_invariants.py"
```

---

## Parallel Example: P1 User Stories (Multi-Team)

```bash
# Once Foundational phase completes, three developers can work in parallel:

# Developer A: User Story 1 - Variant System Canonicalization
Tasks T009-T023

# Developer B: User Story 2 - Variant Identification Consistency
Tasks T024-T031

# Developer C: User Story 3 - Product Approval & Visibility Enforcement
Tasks T032-T043
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

**MVP delivers**:
- ProductCategoryVariantOption as canonical variant system
- ProductVariant deprecated with warnings
- combination_stocks ignored
- Stock invariants INV-001 through INV-005, INV-014 through INV-016 enforced

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Test independently → Deploy/Demo
6. Add User Story 5 → Test independently → Deploy/Demo
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Variant System Canonicalization)
   - Developer B: User Story 2 (Variant Identification Consistency)
   - Developer C: User Story 3 (Approval & Visibility Enforcement)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify invariant tests fail before implementing (TDD approach)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- 19 invariant tests map from Spec 004 and MUST all pass
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

---

## Invariant Test Mapping

| Invariant | Test Task | Category |
|-----------|-----------|----------|
| INV-001 | T012 | Stock |
| INV-002 | T013 | Stock |
| INV-003 | T014 | Stock |
| INV-004 | T015 | Stock |
| INV-005 | T016 | Stock |
| INV-006 | T024 | Order |
| INV-007 | T025 | Order |
| INV-008 | T026 | Order |
| INV-009 | T027 | Order |
| INV-010 | T032 | Visibility |
| INV-011 | T033 | Visibility |
| INV-012 | T034 | Visibility |
| INV-013 | T035 | Visibility |
| INV-014 | T009 | Variant System |
| INV-015 | T010 | Variant System |
| INV-016 | T011 | Variant System |
| INV-017 | T044 | Cart |
| INV-018 | T045 | Cart |
| INV-019 | T046 | Cart |

**Total**: 64 tasks (including all tests, implementation, and polish tasks)
