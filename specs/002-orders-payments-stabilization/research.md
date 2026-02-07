# Research: Orders & Payments Stabilization

**Feature**: 002-orders-payments-stabilization  
**Date**: 2026-01-18  
**Status**: Complete

---

## Technical Context Findings

### Existing Implementation Analysis

| Component | File | Status | Notes |
|-----------|------|--------|-------|
| Order Model | `orders/models.py` | ✅ Exists | Basic model with 5 states: pending, paid, shipped, completed, cancelled |
| OrderItem Model | `orders/models.py` | ✅ Exists | Supports variant_id, seller reference, commission |
| Atomic Order System | `orders/atomic_order_system.py` | ✅ Exists | OrderStateMachine, StockLockManager, WalletOrderCoordinator, AtomicOrderCreator |
| Payment Model | `payment/models.py` | ✅ Exists | PaymentMethod (credit_card, wallet, cash_on_delivery, bank_transfer), Payment states |
| Wallet Model | `wallet/models.py` | ✅ Exists | Full transaction support with deposit, withdraw, transfer, idempotency |
| Cart Model | `cart/models.py` | ✅ Exists | User/session cart, variant support |

### Gap Analysis: Spec vs Current Implementation

#### Order States (Critical Gap)

**Current States**: `pending`, `paid`, `shipped`, `completed`, `cancelled`

**Spec-Required States**:
| State | Current | Required Action |
|-------|---------|-----------------|
| PENDING_PAYMENT | ✅ `pending` (rename only) | Add explicit naming in docs |
| COD_PENDING | ❌ Missing | **ADD** - New state for COD orders |
| PAID | ✅ Exists | No change |
| PROCESSING | ❌ Missing | **ADD** - Seller acknowledgment state |
| SHIPPED | ✅ Exists | No change |
| DELIVERED | ❌ Missing | **ADD** - Delivery confirmed, pre-completion |
| COMPLETED | ✅ Exists | No change |
| CANCELLED | ✅ Exists | No change |
| REFUNDED | ❌ Missing | **ADD** - Distinct from cancelled |
| FAILED | ❌ Missing | **ADD** - Payment failure state |

**Decision**: Extend `STATUS_CHOICES` in Order model with new states.

#### Payment Timeout (Critical Gap)

**Current**: No timeout mechanism found.

**Required**: 15-minute timeout for `pending` orders to auto-cancel.

**Options Evaluated**:
1. **Celery periodic task** - Check every minute for expired orders
2. **Database scheduled event** - MySQL/PostgreSQL event scheduler
3. **Django-Q or APScheduler** - In-process scheduling

**Decision**: Celery periodic task (option 1)
- **Rationale**: Project already uses Django; Celery is standard. Periodic task is simple, auditable, and doesn't require database-level scheduling.
- **Alternatives rejected**: 
  - MySQL events: Less portable, harder to test
  - In-process: Dies with server restart

#### Multi-Seller Order Handling (Significant Gap)

**Current**: `OrderItem.seller` exists but order-level state is singular.

**Required**: Per-line-item seller status tracking for multi-seller orders.

**Options Evaluated**:
1. **Add status field to OrderItem** - Each line item has independent state
2. **Separate SellerOrderFulfillment model** - Junction table for seller-specific tracking
3. **Denormalize to JSON field** - Store seller states in Order.meta

**Decision**: Add `item_status` field to `OrderItem` (option 1)
- **Rationale**: Simplest change. OrderItem already has seller FK. Aggregation logic can derive order-level state.
- **Alternatives rejected**:
  - Junction table: Over-engineering for current scope
  - JSON field: Harder to query and index

#### COD Payment Flow (New Capability)

**Current**: PaymentMethod supports `cash_on_delivery` but no distinct order flow.

**Required**: COD orders skip payment confirmation, go directly to `COD_PENDING` → `PROCESSING`.

**Decision**: Branch order creation logic based on payment method.
- If `payment_method == 'cod'`: Initial state = `cod_pending`
- Else: Initial state = `pending_payment`

#### Stock Reservation Model (Enhancement)

**Current**: Stock is decremented immediately on order creation. No explicit reservation tracking.

**Required per spec**: `StockReservation` record with status (RESERVED/RELEASED/COMMITTED).

**Options Evaluated**:
1. **Add StockReservation model** - Explicit reservation tracking
2. **Track via Transaction logs** - Audit trail without new model
3. **OrderItem.reservation_status** - Inline tracking

**Decision**: Add `reservation_status` field to `OrderItem` (option 3)
- **Rationale**: Minimal model changes. OrderItem already stores product/variant/quantity. Adding status is lightweight.
- **Alternatives rejected**:
  - New model: Additional JOIN for every query
  - Transaction logs: Harder to query current state

---

## Technology Decisions

### Framework & Libraries

| Technology | Decision | Rationale |
|------------|----------|-----------|
| Task Queue | Celery | Standard Django async. Already implied by project structure. |
| Database | MySQL (existing) | No change. Use `select_for_update()` for row locking. |
| Caching | Redis (existing) | Used for OTP in Phase 1. Reuse for rate limiting. |

### Database Changes

| Model | Change | Migration Type |
|-------|--------|----------------|
| Order | Extend STATUS_CHOICES | Data migration for enum |
| Order | Add `payment_timeout_at` | AddField (nullable) |
| OrderItem | Add `item_status` | AddField (default='pending') |
| OrderItem | Add `reservation_status` | AddField (default='reserved') |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| State machine complexity | Medium | High | Comprehensive test coverage for each transition |
| Payment timeout race | Low | Medium | Use `select_for_update()` in timeout task |
| Multi-seller aggregation bugs | Medium | Medium | Clear aggregation rules in code, tests |
| Backward compatibility | Medium | High | Keep old status values valid, new states are additive |

---

## Out of Scope (Deferred)

Per spec clarifications and assumptions:
- Seller payouts (future phase)
- Shipping/delivery tracking integration
- Return/exchange workflows (beyond refund)
- External payment gateway integration (InstaPay, Credit Card APIs)
- Partial refunds
- Partial order cancellation

---

## Summary

The existing `atomic_order_system.py` provides a solid foundation. The stabilization requires:

1. **State model expansion** - 4 new states (COD_PENDING, PROCESSING, DELIVERED, FAILED, REFUNDED)
2. **Payment timeout** - Celery task + `payment_timeout_at` field
3. **Multi-seller tracking** - `OrderItem.item_status` field
4. **COD workflow branch** - Logic branch in AtomicOrderCreator
5. **Reservation tracking** - `OrderItem.reservation_status` field

All changes are additive and reversible via Django migrations.
