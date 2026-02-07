# Implementation Plan: Orders & Payments Stabilization

**Branch**: `002-orders-payments-stabilization` | **Date**: 2026-01-18 | **Spec**: [spec.md](file:///Users/momen/untitled%20folder/To7fa/TO7FAA/to7fabackend/specs/002-orders-payments-stabilization/spec.md)  
**Input**: Feature specification from `/specs/002-orders-payments-stabilization/spec.md`

---

## Summary

Stabilize the order lifecycle and payment coordination system by:
- **Extending order states** to include COD_PENDING, PROCESSING, DELIVERED, REFUNDED, FAILED
- **Implementing payment timeout** (15-minute auto-cancel for pending orders)
- **Adding multi-seller support** via per-item status tracking
- **Ensuring atomic stock/payment operations** remain consistent
- **Supporting COD payment flow** with distinct lifecycle

The existing `atomic_order_system.py` provides a solid foundation. This plan extends it to match the clarified specification.

---

## Technical Context

**Language/Version**: Python 3.9+ (Django 4.2.13)  
**Primary Dependencies**: Django REST Framework 3.16.0, SimpleJWT 5.5.0, Celery 5.x, django-redis 5.4.0  
**Storage**: MySQL (MySQLClient 2.2.7), Redis  
**Testing**: pytest-django  
**Target Platform**: Linux server (Django backend API)  
**Project Type**: Backend API (Django REST)  
**Performance Goals**: 200ms p50, 500ms p95 per constitution; 15-min payment timeout  
**Constraints**: Database queries <100ms, no N+1 patterns, first-commit-wins concurrency  
**Scale/Scope**: E-commerce platform with multi-seller orders

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status | Justification |
|-----------|------|--------|---------------|
| **I. Code Quality** | Files ≤300 lines | ✅ PASS | Split state machine, timeout task, multi-seller logic |
| **I. Code Quality** | Single Responsibility | ✅ PASS | Separate modules for state transitions, timeout, seller |
| **II. Testing Standards** | 80% coverage on critical paths | ⚠️ PENDING | Tests defined in verification plan |
| **II. Testing Standards** | Unit + Integration tests | ⚠️ PENDING | Test structure defined |
| **III. UX Consistency** | Error response format | ✅ PASS | Standard JSON error format used |
| **III. UX Consistency** | 401/403/404 correct usage | ✅ PASS | Existing patterns maintained |
| **IV. Performance** | 200ms p50, 500ms p95 | ✅ PASS | select_for_update() for atomicity |
| **IV. Performance** | No N+1 queries | ✅ PASS | select_related/prefetch used |

**Gate Result**: ✅ PASS (Testing to be implemented in execution)

---

## Project Structure

### Documentation (this feature)

```text
specs/002-orders-payments-stabilization/
├── plan.md              # This file
├── research.md          # Phase 0 output ✅
├── data-model.md        # Phase 1 output ✅
├── quickstart.md        # Phase 1 output ✅
├── contracts/           # Phase 1 output ✅
│   └── openapi.yaml     # API contract
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
orders/
├── models.py            # [MODIFY] Extend STATUS_CHOICES, add fields
├── atomic_order_system.py  # [MODIFY] Update state machine, add COD support
├── services/            # [NEW] Business logic layer
│   ├── __init__.py
│   ├── state_machine.py # Extended state transitions
│   ├── timeout.py       # Payment timeout logic
│   └── multi_seller.py  # Multi-seller aggregation
├── tasks.py             # [NEW] Celery tasks for timeout
├── serializers.py       # [MODIFY] Add new fields, states
├── views.py             # [MODIFY] Add new endpoints
├── urls.py              # [MODIFY] Add new routes
└── tests/               # [MODIFY] Add new test cases
    ├── test_state_machine.py
    ├── test_payment_timeout.py
    ├── test_cod_flow.py
    └── test_multi_seller.py

payment/
├── models.py            # [MODIFY] Add 'captured' status
└── services/            # [NEW] Payment coordination
    ├── __init__.py
    └── gateway.py       # Future: payment gateway abstraction
```

**Structure Decision**: Extend existing Django app structure. New `services/` subdirectories for business logic separation per Single Responsibility principle. Celery tasks in dedicated `tasks.py`.

---

## Proposed Changes

### Component 1: Order State Model Extension

#### [MODIFY] [models.py](file:///Users/momen/untitled%20folder/To7fa/TO7FAA/to7fabackend/orders/models.py)

**Order Model Changes**:

| Change | Details |
|--------|---------|
| Extend `STATUS_CHOICES` | Add: `cod_pending`, `processing`, `delivered`, `refunded`, `failed` |
| Rename `pending` → `pending_payment` | Data migration for existing orders |
| Add `payment_timeout_at` | DateTimeField, nullable, indexed with status |
| Add index | `(status, payment_timeout_at)` for timeout queries |

**OrderItem Model Changes**:

| Change | Details |
|--------|---------|
| Add `item_status` | CharField with choices: pending, processing, shipped, delivered, completed, cancelled |
| Add `reservation_status` | CharField with choices: reserved, released, committed |
| Add index | `(item_status)` for aggregation queries |

---

### Component 2: Extended State Machine

#### [MODIFY] [atomic_order_system.py](file:///Users/momen/untitled%20folder/To7fa/TO7FAA/to7fabackend/orders/atomic_order_system.py)

Update `OrderStateMachine.VALID_TRANSITIONS`:

```python
VALID_TRANSITIONS = {
    'pending_payment': ['paid', 'cancelled', 'failed'],
    'cod_pending': ['processing', 'cancelled'],
    'paid': ['processing', 'cancelled', 'refunded'],
    'processing': ['shipped', 'cancelled', 'refunded'],
    'shipped': ['delivered', 'refunded'],
    'delivered': ['completed', 'refunded'],
    'cancelled': [],
    'completed': [],
    'refunded': [],
    'failed': [],
}
```

Add methods:
- `get_initial_state(payment_method)` → Returns `cod_pending` for COD, else `pending_payment`
- `is_terminal(status)` → Check if state is terminal

---

### Component 3: COD Payment Flow

#### [MODIFY] [atomic_order_system.py](file:///Users/momen/untitled%20folder/To7fa/TO7FAA/to7fabackend/orders/atomic_order_system.py)

Update `AtomicOrderCreator.create_order()`:

```python
# Determine initial state based on payment method
if payment_method == 'cod':
    initial_status = 'cod_pending'
    payment_timeout_at = None  # No timeout for COD
else:
    initial_status = 'pending_payment'
    payment_timeout_at = timezone.now() + timedelta(minutes=15)
```

---

### Component 4: Payment Timeout Service

#### [NEW] [tasks.py](file:///Users/momen/untitled%20folder/To7fa/TO7FAA/to7fabackend/orders/tasks.py)

Celery task to check and cancel expired orders:

```python
from celery import shared_task
from django.utils import timezone
from orders.models import Order
from orders.atomic_order_system import AtomicOrderCreator

@shared_task
def check_payment_timeouts():
    """Cancel orders past payment timeout."""
    expired_orders = Order.objects.filter(
        status='pending_payment',
        payment_timeout_at__lte=timezone.now()
    ).select_for_update(skip_locked=True)
    
    for order in expired_orders:
        AtomicOrderCreator.cancel_order(
            order_id=order.id,
            user=None,  # System-initiated
            reason='Payment timeout'
        )
```

#### [MODIFY] to7fabackend/celery.py

Add beat schedule:

```python
CELERY_BEAT_SCHEDULE = {
    'check-payment-timeouts': {
        'task': 'orders.tasks.check_payment_timeouts',
        'schedule': 60.0,  # Every minute
    },
}
```

---

### Component 5: Multi-Seller Support

#### [NEW] [services/multi_seller.py](file:///Users/momen/untitled%20folder/To7fa/TO7FAA/to7fabackend/orders/services/multi_seller.py)

Aggregation logic for order-level state:

```python
def aggregate_order_status(order):
    """Derive order status from line item statuses."""
    item_statuses = order.items.values_list('item_status', flat=True)
    
    if all(s == 'cancelled' for s in item_statuses):
        return 'cancelled'
    if all(s == 'completed' for s in item_statuses):
        return 'completed'
    if all(s == 'delivered' for s in item_statuses):
        return 'delivered'
    if all(s == 'shipped' for s in item_statuses):
        return 'shipped'
    if any(s == 'processing' for s in item_statuses):
        return 'processing'
    return order.status  # Keep current
```

---

### Component 6: New API Endpoints

#### [MODIFY] [views.py](file:///Users/momen/untitled%20folder/To7fa/TO7FAA/to7fabackend/orders/views.py)

Add endpoints:

| Endpoint | Method | Action |
|----------|--------|--------|
| `/orders/<id>/acknowledge/` | POST | Seller acknowledges → PROCESSING |
| `/orders/<id>/ship/` | POST | Seller ships → SHIPPED |
| `/orders/<id>/deliver/` | POST | Delivery confirmed → DELIVERED |
| `/orders/<id>/complete/` | POST | Order completed → COMPLETED |
| `/orders/<id>/refund/` | POST | Admin refund → REFUNDED |
| `/orders/states/` | GET | List valid states and transitions |

#### [MODIFY] [urls.py](file:///Users/momen/untitled%20folder/To7fa/TO7FAA/to7fabackend/orders/urls.py)

Add routes for new endpoints.

---

## Verification Plan

### Automated Tests

**Framework**: pytest-django (existing)

**Test Run Command**:
```bash
cd "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend"
source .venv/bin/activate
python manage.py test orders.tests --verbosity=2
```

#### Unit Tests

| Test File | Coverage |
|-----------|----------|
| `orders/tests/test_state_machine.py` | All state transitions, invalid transitions, terminal states |
| `orders/tests/test_payment_timeout.py` | Timeout calculation, auto-cancel, COD excluded |
| `orders/tests/test_cod_flow.py` | COD initial state, transitions, delivery=payment |
| `orders/tests/test_multi_seller.py` | Per-item status, order aggregation, seller isolation |
| `orders/tests/test_stock_reservation.py` | Reservation status, release, commit |

#### Integration Tests

| Test | Description |
|------|-------------|
| `test_order_creation_with_wallet_payment` | Full flow: create, pay, process, ship, deliver, complete |
| `test_order_creation_with_cod` | COD flow: create → cod_pending → processing → complete |
| `test_concurrent_stock_reservation` | Race condition: first-commit-wins |
| `test_payment_timeout_cancellation` | Order auto-cancelled after 15 minutes |
| `test_multi_seller_order_aggregation` | Order status reflects aggregated item statuses |
| `test_refund_restores_stock_and_wallet` | Full refund flow with cleanup |

#### Contract Tests

| Test | Description |
|------|-------------|
| `test_api_contract_order_create` | Validates request/response against OpenAPI |
| `test_api_contract_order_cancel` | Error responses match schema |

### Manual Verification

> Recommended after automated tests pass.

1. **COD Order Flow**:
   - Create order with `payment_method: cod`
   - Verify initial state is `cod_pending`
   - Acknowledge order as seller → verify `processing`
   - Mark as shipped → verify `shipped`
   - Confirm delivery → verify `delivered` → `completed`

2. **Payment Timeout**:
   - Create order with wallet payment
   - Wait or manually set `payment_timeout_at` to past
   - Run `check_payment_timeouts` task
   - Verify order is `cancelled`, stock released

3. **Multi-Seller Order**:
   - Create order with items from 2 different sellers
   - Seller A ships their item
   - Verify order is still `processing` (Seller B hasn't shipped)
   - Seller B ships → verify order is now `shipped`

---

## Dependencies & Risk

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Celery not configured | Medium | High | Document setup in quickstart; fallback manual task |
| State migration breaks existing orders | Low | High | Additive changes only; data migration normalizes |
| Concurrency bugs in timeout task | Low | Medium | Use `select_for_update(skip_locked=True)` |
| Multi-seller aggregation complexity | Medium | Medium | Comprehensive test coverage |

---

## Complexity Tracking

> No constitution violations requiring justification.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| N/A | N/A | N/A |

---

## Artifacts Generated

| Artifact | Path | Status |
|----------|------|--------|
| Research | [research.md](file:///Users/momen/untitled%20folder/To7fa/TO7FAA/to7fabackend/specs/002-orders-payments-stabilization/research.md) | ✅ Complete |
| Data Model | [data-model.md](file:///Users/momen/untitled%20folder/To7fa/TO7FAA/to7fabackend/specs/002-orders-payments-stabilization/data-model.md) | ✅ Complete |
| Quickstart | [quickstart.md](file:///Users/momen/untitled%20folder/To7fa/TO7FAA/to7fabackend/specs/002-orders-payments-stabilization/quickstart.md) | ✅ Complete |
| API Contract | [openapi.yaml](file:///Users/momen/untitled%20folder/To7fa/TO7FAA/to7fabackend/specs/002-orders-payments-stabilization/contracts/openapi.yaml) | ✅ Complete |

---

## Next Steps

1. **Review this plan** - User approval required before proceeding
2. **Run `/speckit.tasks`** - Generate detailed task breakdown
3. **Execute tasks** - Implement changes per task list
4. **Verify** - Run test suite, manual verification
