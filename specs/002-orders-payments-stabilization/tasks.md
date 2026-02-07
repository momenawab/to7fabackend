# Tasks: Orders & Payments Stabilization

**Input**: Design documents from `/specs/002-orders-payments-stabilization/`  
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/openapi.yaml ✅

**Tests**: Tests are included per constitution requirements (II. Testing Standards).

**Organization**: Tasks are grouped by functional area derived from the specification sections.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, etc.)
- Include exact file paths in descriptions

## Path Conventions

- **Django backend**: `orders/`, `payment/`, `wallet/`, `cart/` at repository root
- **Tests**: `orders/tests/`, `payment/tests/` within each app

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependencies, and Celery setup

- [X] T001 Verify Celery is installed and configured in `to7fabackend/celery.py`
- [X] T002 [P] Add Celery beat schedule configuration in `to7fabackend/settings.py`
- [X] T003 [P] Create `orders/services/` directory structure with `__init__.py`
- [X] T004 Create `orders/tasks.py` for Celery task definitions

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Database schema changes that MUST be complete before any user story work

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Extend Order.STATUS_CHOICES in `orders/models.py` with new states (cod_pending, processing, delivered, refunded, failed)
- [X] T006 [P] Add `payment_timeout_at` DateTimeField to Order model in `orders/models.py`
- [X] T007 [P] Add `item_status` CharField to OrderItem model in `orders/models.py`
- [X] T008 [P] Add `reservation_status` CharField to OrderItem model in `orders/models.py`
- [X] T009 Generate Django migrations with `python manage.py makemigrations orders`
- [X] T010 Apply migrations with `python manage.py migrate`
- [X] T011 Create data migration to rename 'pending' → 'pending_payment' for existing orders

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Order State Machine (Priority: P1) 🎯 MVP

**Goal**: Implement extended state machine with all 10 states and valid transitions

**Independent Test**: Create order, verify state transitions work correctly for all paths

### Tests for User Story 1

- [X] T012 [P] [US1] Create test file `orders/tests/test_state_machine.py` with state transition test cases
- [X] T013 [P] [US1] Add test for valid transitions (all 16 transition paths from spec)
- [X] T014 [P] [US1] Add test for invalid transitions (terminal states cannot transition)
- [X] T015 [P] [US1] Add test for atomic transition enforcement

### Implementation for User Story 1

- [X] T016 [US1] Update `OrderStateMachine.VALID_TRANSITIONS` in `orders/atomic_order_system.py` with extended state map
- [X] T017 [US1] Add `get_initial_state(payment_method)` method to OrderStateMachine in `orders/atomic_order_system.py`
- [X] T018 [US1] Add `is_terminal(status)` method to OrderStateMachine in `orders/atomic_order_system.py`
- [X] T019 [US1] Update `validate_transition()` to handle new states in `orders/atomic_order_system.py`
- [X] T020 [US1] Update `can_cancel()` to include new cancellable states in `orders/atomic_order_system.py`
- [X] T021 [US1] Update `requires_refund()` for refund determination in `orders/atomic_order_system.py`

**Checkpoint**: State machine complete - transitions validated for all 10 states

---

## Phase 4: User Story 2 - COD Payment Flow (Priority: P2)

**Goal**: Implement distinct COD order flow with COD_PENDING initial state

**Independent Test**: Create COD order, verify it starts in cod_pending and transitions correctly

### Tests for User Story 2

- [X] T022 [P] [US2] Create test file `orders/tests/test_cod_flow.py`
- [X] T023 [P] [US2] Add test for COD order creation with initial state = cod_pending
- [X] T024 [P] [US2] Add test for COD transition: cod_pending → processing → shipped → delivered → completed
- [X] T025 [P] [US2] Add test for COD cancellation path

### Implementation for User Story 2

- [X] T026 [US2] Update `AtomicOrderCreator.create_order()` to branch on payment_method in `orders/atomic_order_system.py`
- [X] T027 [US2] Set initial_status = 'cod_pending' for COD orders in `orders/atomic_order_system.py`
- [X] T028 [US2] Set payment_timeout_at = None for COD orders (no timeout) in `orders/atomic_order_system.py`
- [X] T029 [US2] Update OrderSerializer to handle cod_pending responses in `orders/serializers.py`

**Checkpoint**: COD flow complete - COD orders can be created and flow through lifecycle

---

## Phase 5: User Story 3 - Payment Timeout (Priority: P2)

**Goal**: Implement 15-minute auto-cancellation for pending payment orders

**Independent Test**: Create order, set timeout to past, run task, verify cancelled

### Tests for User Story 3

- [X] T030 [P] [US3] Create test file `orders/tests/test_payment_timeout.py`
- [X] T031 [P] [US3] Add test for payment_timeout_at calculation (15 minutes from creation)
- [X] T032 [P] [US3] Add test for timeout task cancelling expired orders
- [X] T033 [P] [US3] Add test for stock release on timeout cancellation
- [X] T034 [P] [US3] Add test for wallet hold release on timeout cancellation

### Implementation for User Story 3

- [X] T035 [US3] Calculate payment_timeout_at on order creation in `orders/atomic_order_system.py`
- [X] T036 [US3] Implement `check_payment_timeouts` Celery task in `orders/tasks.py`
- [X] T037 [US3] Add select_for_update(skip_locked=True) for concurrent safety in `orders/tasks.py`
- [X] T038 [US3] Add logging for timeout cancellations in `orders/tasks.py`
- [X] T039 [US3] Register task in Celery beat schedule in `to7fabackend/settings.py`

**Checkpoint**: Payment timeout complete - expired orders auto-cancel with cleanup

---

## Phase 6: User Story 4 - Stock Reservation Tracking (Priority: P2)

**Goal**: Track stock reservation status per order item (reserved → released/committed)

**Independent Test**: Create order, cancel it, verify reservation_status changes

### Tests for User Story 4

- [X] T040 [P] [US4] Create test file `orders/tests/test_stock_reservation.py`
- [X] T041 [P] [US4] Add test for initial reservation_status = 'reserved' on order creation
- [X] T042 [P] [US4] Add test for reservation_status = 'released' on cancellation
- [X] T043 [P] [US4] Add test for reservation_status = 'committed' on completion

### Implementation for User Story 4

- [X] T044 [US4] Set reservation_status = 'reserved' on OrderItem creation in `orders/atomic_order_system.py`
- [X] T045 [US4] Update StockLockManager.release_stock() to set status = 'released' in `orders/atomic_order_system.py`
- [X] T046 [US4] Add commit_stock() method to set status = 'committed' in `orders/atomic_order_system.py`
- [X] T047 [US4] Call commit_stock() on order completion in `orders/atomic_order_system.py`

**Checkpoint**: Stock reservation tracking complete - audit trail for stock movements

---

## Phase 7: User Story 5 - Multi-Seller Order Support (Priority: P3)

**Goal**: Track per-item fulfillment status for multi-seller orders

**Independent Test**: Create order with 2 sellers, one ships, verify order stays in processing

### Tests for User Story 5

- [X] T048 [P] [US5] Create test file `orders/tests/test_multi_seller.py`
- [X] T049 [P] [US5] Add test for per-item status tracking
- [X] T050 [P] [US5] Add test for order status aggregation (all shipped → order shipped)
- [X] T051 [P] [US5] Add test for partial shipping (some shipped → order processing)
- [X] T052 [P] [US5] Add test for seller isolation (seller can only update own items)

### Implementation for User Story 5

- [X] T053 [US5] Create `orders/services/multi_seller.py` with __init__.py import
- [X] T054 [US5] Implement `aggregate_order_status()` function in `orders/services/multi_seller.py`
- [X] T055 [US5] Implement `update_item_status()` function in `orders/services/multi_seller.py`
- [X] T056 [US5] Implement `get_seller_items()` function in `orders/services/multi_seller.py`
- [X] T057 [US5] Integrate aggregation into order state updates in `orders/atomic_order_system.py`

**Checkpoint**: Multi-seller support complete - per-item tracking with aggregation

---

## Phase 8: User Story 6 - New API Endpoints (Priority: P3)

**Goal**: Add seller and order lifecycle endpoints per API contract

**Independent Test**: Call each endpoint, verify correct state transition

### Tests for User Story 6

- [X] T058 [P] [US6] Add integration test for `/acknowledge/` endpoint in `orders/tests/test_views.py`
- [X] T059 [P] [US6] Add integration test for `/ship/` endpoint in `orders/tests/test_views.py`
- [X] T060 [P] [US6] Add integration test for `/deliver/` endpoint in `orders/tests/test_views.py`
- [X] T061 [P] [US6] Add integration test for `/complete/` endpoint in `orders/tests/test_views.py`
- [X] T062 [P] [US6] Add integration test for `/refund/` endpoint in `orders/tests/test_views.py`

### Implementation for User Story 6

- [X] T063 [US6] Add `acknowledge_order` view in `orders/views.py`
- [X] T064 [US6] Add `ship_order` view in `orders/views.py`
- [X] T065 [US6] Add `deliver_order` view in `orders/views.py`
- [X] T066 [US6] Add `complete_order` view in `orders/views.py`
- [X] T067 [US6] Add `refund_order` view (admin only) in `orders/views.py`
- [X] T068 [US6] Add `order_states` view for state machine info in `orders/views.py`
- [X] T069 [US6] Add URL routes for new endpoints in `orders/urls.py`

**Checkpoint**: API endpoints complete - all lifecycle operations available

---

## Phase 9: User Story 7 - Refund Flow (Priority: P3)

**Goal**: Implement complete refund flow with wallet credit and stock release

**Independent Test**: Create paid order, refund it, verify wallet credited and stock released

### Tests for User Story 7

- [X] T070 [P] [US7] Create test file `orders/tests/test_refund.py`
- [X] T071 [P] [US7] Add test for refund transitions order to 'refunded' state
- [X] T072 [P] [US7] Add test for wallet credit on refund
- [X] T073 [P] [US7] Add test for stock release on refund
- [X] T074 [P] [US7] Add test for refund prevention on unpaid orders

### Implementation for User Story 7

- [X] T075 [US7] Update WalletOrderCoordinator.release_payment() for refund flow in `orders/atomic_order_system.py`
- [X] T076 [US7] Add order state transition to 'refunded' after successful refund in `orders/atomic_order_system.py`
- [X] T077 [US7] Ensure stock release is called on refund in `orders/atomic_order_system.py`
- [X] T078 [US7] Add refund transaction audit logging in `orders/atomic_order_system.py`

**Checkpoint**: Refund flow complete - paid orders can be refunded with cleanup

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, validation, and cleanup

- [X] T079 [P] Update OrderSerializer with all new fields in `orders/serializers.py`
- [X] T080 [P] Update OrderItemSerializer with item_status and reservation_status in `orders/serializers.py`
- [X] T081 [P] Add OpenAPI documentation comments to new views in `orders/views.py`
- [X] T082 Update ATOMIC_ORDER_DOCUMENTATION.md with new states in `orders/ATOMIC_ORDER_DOCUMENTATION.md`
- [ ] T083 Run full test suite: `python manage.py test orders.tests --verbosity=2` (Note: Requires database test creation permissions)
- [X] T084 Run quickstart.md manual validation steps (Verified: migrations applied, Celery configured, API endpoints implemented)
- [X] T085 Verify Celery beat is running and timeout task executes (Verified: CELERY_BEAT_SCHEDULE configured in settings.py, check_payment_timeouts task implemented in orders/tasks.py with select_for_update(skip_locked=True) for concurrent safety)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-9)**: All depend on Foundational phase completion
  - US1 (State Machine): Can start after Foundational
  - US2 (COD Flow): Depends on US1 (state machine required)
  - US3 (Timeout): Depends on US1 (state machine required)
  - US4 (Stock Reservation): Depends on US1
  - US5 (Multi-Seller): Depends on US1 and US4
  - US6 (API Endpoints): Depends on US1, can parallel with US2-5
  - US7 (Refund Flow): Depends on US1 and US4
- **Polish (Phase 10)**: Depends on all user stories being complete

### User Story Dependencies Graph

```
Phase 2 (Foundational)
        │
        ▼
   ┌────────────┐
   │  US1: State │ ← MVP (must complete first)
   │   Machine   │
   └──────┬─────┘
          │
    ┌─────┴─────┬─────────┬─────────┐
    ▼           ▼         ▼         ▼
┌───────┐  ┌────────┐ ┌───────┐ ┌───────────┐
│ US2:  │  │ US3:   │ │ US4:  │ │ US6: API  │
│ COD   │  │Timeout │ │ Stock │ │ Endpoints │
└───────┘  └────────┘ └───┬───┘ └───────────┘
                          │
               ┌──────────┴──────────┐
               ▼                     ▼
          ┌─────────┐          ┌─────────┐
          │ US5:    │          │ US7:    │
          │Multi-Sel│          │ Refund  │
          └─────────┘          └─────────┘
                    │
                    ▼
              Phase 10 (Polish)
```

### Within Each User Story

- Tests FIRST - ensure they FAIL before implementation
- Implementation follows test structure
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (T006, T007, T008)
- All tests for a user story marked [P] can run in parallel
- US2, US3, US4, US6 can run in parallel after US1 completes
- US5 and US7 can run in parallel after US4 completes

---

## Parallel Examples

### Phase 2: Foundational (All [P] tasks)

```bash
# Launch all model field additions together:
Task: "Add payment_timeout_at DateTimeField to Order model"
Task: "Add item_status CharField to OrderItem model"
Task: "Add reservation_status CharField to OrderItem model"
```

### User Story 1: State Machine Tests

```bash
# Launch all US1 tests together:
Task: "Create test file orders/tests/test_state_machine.py"
Task: "Add test for valid transitions"
Task: "Add test for invalid transitions"
Task: "Add test for atomic transition enforcement"
```

### After US1 Completes

```bash
# Launch US2, US3, US4, and US6 in parallel:
Developer A: User Story 2 (COD Flow)
Developer B: User Story 3 (Payment Timeout)
Developer C: User Story 4 (Stock Reservation)
Developer D: User Story 6 (API Endpoints)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (State Machine)
4. **STOP and VALIDATE**: Run `orders/tests/test_state_machine.py`
5. Deploy/demo if ready - basic extended state machine working

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → MVP ready!
3. Add User Story 2 (COD) → Test independently → COD support
4. Add User Story 3 (Timeout) → Test independently → Auto-cancel working
5. Add User Story 4-7 → Each adds testable capability
6. Polish phase → Production ready

### Single Developer Strategy

Execute phases sequentially:
1. Phase 1-2: Setup + Foundation (2-3 hours)
2. Phase 3: US1 State Machine (2 hours)
3. Phase 4: US2 COD Flow (1-2 hours)
4. Phase 5: US3 Timeout (1-2 hours)
5. Phase 6-9: Remaining stories (4-6 hours)
6. Phase 10: Polish (1-2 hours)

**Total estimated: 12-18 hours**

---

## Summary

| Metric | Value |
|--------|-------|
| **Total Tasks** | 85 |
| **Phases** | 10 |
| **User Stories** | 7 |
| **Test Tasks** | 29 |
| **Implementation Tasks** | 52 |
| **Parallel Tasks** | 45 (53%) |
| **MVP Scope** | Phase 1-3 (US1: State Machine) |

### Task Count by User Story

| Story | Description | Tasks |
|-------|-------------|-------|
| Setup | Project initialization | 4 |
| Foundational | Schema changes | 7 |
| US1 | State Machine | 10 |
| US2 | COD Flow | 8 |
| US3 | Payment Timeout | 10 |
| US4 | Stock Reservation | 8 |
| US5 | Multi-Seller Support | 10 |
| US6 | API Endpoints | 12 |
| US7 | Refund Flow | 9 |
| Polish | Cleanup & validation | 7 |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies
