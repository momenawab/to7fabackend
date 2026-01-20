# Feature Specification: Orders & Payments Stabilization

**Feature Branch**: `002-orders-payments-stabilization`  
**Created**: 2026-01-18  
**Status**: Draft  
**Input**: Phase 2 — Orders & Payments Stabilization: Order lifecycle, inventory reservation & release, payment & wallet coordination, refund & cancellation behavior

---

## Clarifications

### Session 2026-01-18

- Q: What should be the pending payment timeout duration? → A: 15 minutes (balanced checkout flow)
- Q: Concurrent orders for same limited stock? → A: First-commit-wins (second order fails)
- Q: Payment methods supported? → A: Customer: COD, InstaPay, Credit Card; Seller/Artist: Wallet for withdrawals
- Q: COD orders initial state? → A: New COD_PENDING state (separate tracking for COD orders)
- Q: COD payment confirmation timing? → A: Delivery confirmation triggers COMPLETED (delivery = payment collected)

---

## 1. Order State Model

### 1.1 Valid Order States

| State | Description |
|-------|-------------|
| **PENDING_PAYMENT** | Order created (online payment), awaiting payment confirmation |
| **COD_PENDING** | Order created (Cash on Delivery), awaiting seller processing |
| **PAID** | Payment confirmed, stock reserved, awaiting fulfillment |
| **PROCESSING** | Seller has acknowledged and is preparing the order |
| **SHIPPED** | Order dispatched to customer |
| **DELIVERED** | Order received by customer |
| **COMPLETED** | Order fulfilled, no further action required |
| **CANCELLED** | Order cancelled before fulfillment |
| **REFUNDED** | Order cancelled after payment, funds returned |
| **FAILED** | Order failed due to payment or system error |

### 1.2 State Transition Rules

**Initial State**: 
- Online payment orders (InstaPay, Credit Card) begin in `PENDING_PAYMENT` state
- COD orders begin in `COD_PENDING` state upon creation

**Terminal States**: `COMPLETED`, `CANCELLED`, `REFUNDED`, `FAILED` — no further transitions permitted.

**Allowed Transitions**:

| From State | To State | Trigger | Actor |
|------------|----------|---------|-------|
| PENDING_PAYMENT | PAID | Payment confirmed | System |
| PENDING_PAYMENT | CANCELLED | Payment timeout or customer cancel | System / Customer |
| PENDING_PAYMENT | FAILED | Payment failure | System |
| COD_PENDING | PROCESSING | Seller acknowledges COD order | Seller |
| COD_PENDING | CANCELLED | Customer cancels before processing | Customer / Admin |
| PAID | PROCESSING | Seller acknowledges order | Seller |
| PAID | CANCELLED | Cancellation request (pre-fulfillment) | Customer / Admin |
| PAID | REFUNDED | Refund issued (post-cancel) | Admin / System |
| PROCESSING | SHIPPED | Seller dispatches order | Seller |
| PROCESSING | CANCELLED | Cancellation approved | Admin |
| PROCESSING | REFUNDED | Refund issued | Admin / System |
| SHIPPED | DELIVERED | Delivery confirmation | System / Customer |
| SHIPPED | REFUNDED | Return processed | Admin / System |
| DELIVERED | COMPLETED | Auto-complete after confirmation period | System |
| DELIVERED | REFUNDED | Return/dispute approved | Admin |

### 1.3 State Behavior Constraints

- **FR-ORD-001**: An order MUST NOT transition to any state other than the allowed transitions defined above
- **FR-ORD-002**: An order in a terminal state MUST NOT transition to any other state
- **FR-ORD-003**: State transitions MUST be atomic — partial transitions are not permitted
- **FR-ORD-004**: Each state transition MUST be recorded with timestamp and actor
- **FR-ORD-005**: For COD orders, delivery confirmation implicitly confirms payment — DELIVERED → COMPLETED transition includes payment collection

---

## 2. Order Creation Specification

### 2.1 Preconditions for Order Creation

- **FR-ORD-010**: User MUST be authenticated
- **FR-ORD-011**: User MUST have verified mobile (as per Phase 1 spec)
- **FR-ORD-012**: User MUST NOT be in Locked (BANNED) state
- **FR-ORD-013**: Cart MUST contain at least one item
- **FR-ORD-014**: All cart items MUST have sufficient stock at validation time

### 2.2 Stock Validation Timing

- **FR-ORD-015**: Stock availability MUST be validated at order creation time (not at cart addition time)
- **FR-ORD-016**: Stock validation and reservation MUST occur within the same atomic operation
- **FR-ORD-017**: If any item fails stock validation, order creation MUST fail entirely (no partial orders)

### 2.3 Idempotency Behavior

- **FR-ORD-018**: Duplicate order creation requests with identical cart contents and timestamp within a defined window MUST return the existing order instead of creating a new one
- **FR-ORD-019**: Idempotency key MUST be based on: user ID, cart hash, and timestamp window
- **FR-ORD-020**: Idempotency window MUST be at least 60 seconds

### 2.4 Partial Failure Handling

- **FR-ORD-021**: If stock reservation fails for any item, no stock MUST be reserved for any item
- **FR-ORD-022**: If payment initiation fails after stock reservation, reserved stock MUST be released immediately
- **FR-ORD-023**: Order creation failure MUST return clear error indicating which item(s) caused failure

---

## 3. Inventory Management Specification

### 3.1 Stock Reservation Rules

- **FR-INV-001**: Stock MUST be reserved when order transitions to `PENDING_PAYMENT` state
- **FR-INV-002**: Stock reservation MUST be specific to the exact variant purchased (size, color, etc.)
- **FR-INV-003**: Reserved stock MUST be decremented from available stock but NOT from total stock
- **FR-INV-004**: Reserved stock MUST be time-bounded — unreleased reservations expire after payment timeout (15 minutes)
- **FR-INV-005**: Concurrent stock reservation attempts MUST use first-commit-wins strategy — second transaction receives out-of-stock error

### 3.2 Stock Release Rules

| Event | Stock Action |
|-------|--------------|
| Payment timeout (PENDING_PAYMENT → CANCELLED) | Release reserved stock |
| Payment failure (PENDING_PAYMENT → FAILED) | Release reserved stock |
| Order cancellation (before shipment) | Release reserved stock |
| Order refund (after delivery) | Return stock to available |
| Order completion | Decrement total stock permanently |

- **FR-INV-005**: Stock MUST be released when order transitions to `CANCELLED` or `FAILED` state
- **FR-INV-006**: Stock MUST be returned when order transitions to `REFUNDED` state
- **FR-INV-007**: Stock release MUST be atomic with state transition — no orphaned reservations permitted

### 3.3 Variant-Specific Stock Handling

- **FR-INV-010**: Each product variant MUST have independent stock tracking
- **FR-INV-011**: Stock reservation MUST reference the specific variant ID, not base product ID
- **FR-INV-012**: Combination variants (e.g., size + color) MUST have explicit stock counts per combination
- **FR-INV-013**: Order line items MUST store variant ID to enable correct stock release

### 3.4 Order Data for Stock Release

Each order line item MUST store:
- Product ID
- Variant ID (if applicable)
- Quantity reserved
- Reservation timestamp
- Reservation status (RESERVED / RELEASED / COMMITTED)

- **FR-INV-014**: Order line item MUST contain sufficient data to release stock without external lookups
- **FR-INV-015**: Stock release MUST NOT depend on current product/variant configuration — historical snapshot on order MUST be authoritative

---

## 4. Payment & Wallet Specification

### 4.1 Payment States

| Payment State | Description |
|---------------|-------------|
| **PENDING** | Payment initiated, awaiting confirmation |
| **CAPTURED** | Payment successfully captured |
| **FAILED** | Payment attempt failed |
| **REFUNDED** | Payment reversed, funds returned |
| **PARTIALLY_REFUNDED** | Portion of payment refunded |

### 4.2 Payment Reservation & Capture

- **FR-PAY-001**: Payment MUST be initiated when order is created
- **FR-PAY-002**: Payment confirmation MUST trigger order transition from `PENDING_PAYMENT` to `PAID`
- **FR-PAY-003**: Payment failure MUST trigger order transition from `PENDING_PAYMENT` to `FAILED`

### 4.3 Wallet Payment Rules

- **FR-PAY-010**: Wallet balance MUST be verified before wallet payment initiation
- **FR-PAY-011**: Wallet balance MUST be held (reserved) when payment is initiated
- **FR-PAY-012**: Wallet hold MUST be converted to debit when order transitions to `PAID`
- **FR-PAY-013**: Wallet hold MUST be released when order transitions to `CANCELLED` or `FAILED`
- **FR-PAY-014**: Wallet transactions MUST be recorded with order reference

### 4.4 Wallet Transaction Types

| Transaction Type | Trigger |
|------------------|---------|
| HOLD | Payment initiated |
| DEBIT | Payment captured |
| RELEASE | Payment cancelled/failed |
| CREDIT | Refund processed |

### 4.5 Order-Payment State Coordination

| Order State | Expected Payment State |
|-------------|------------------------|
| PENDING_PAYMENT | PENDING |
| PAID | CAPTURED |
| CANCELLED (pre-payment) | No payment record OR FAILED |
| CANCELLED (post-payment) | CAPTURED → REFUNDED |
| REFUNDED | REFUNDED |
| FAILED | FAILED |

- **FR-PAY-020**: Order state and payment state MUST remain consistent
- **FR-PAY-021**: State inconsistency between order and payment MUST trigger reconciliation alert

### 4.6 Pending Payment Timeout

- **FR-PAY-030**: Pending payments MUST have a 15-minute timeout period
- **FR-PAY-031**: Orders in `PENDING_PAYMENT` state beyond timeout MUST automatically transition to `CANCELLED`
- **FR-PAY-032**: Timeout-triggered cancellation MUST release all stock reservations
- **FR-PAY-033**: Timeout-triggered cancellation MUST release any wallet holds

---

## 5. Cancellation & Refund Specification

### 5.1 Cancellation Eligibility

| Order State | Customer Can Cancel | Seller Can Cancel | Admin Can Cancel |
|-------------|---------------------|-------------------|------------------|
| PENDING_PAYMENT | Yes | No | Yes |
| PAID | Yes (pre-processing) | No | Yes |
| PROCESSING | No | Request only | Yes |
| SHIPPED | No | No | Yes |
| DELIVERED | No | No | Yes (refund only) |

- **FR-CAN-001**: Customer MAY cancel order in `PENDING_PAYMENT` or `PAID` states only
- **FR-CAN-002**: Customer MUST NOT cancel order once in `PROCESSING` state or beyond
- **FR-CAN-003**: Seller MUST NOT directly cancel orders — seller may request admin intervention
- **FR-CAN-004**: Admin MAY cancel or refund any non-terminal order

### 5.2 Cancellation Effects

Upon cancellation:

- **FR-CAN-010**: Stock reservations MUST be released
- **FR-CAN-011**: Wallet holds MUST be released (if payment pending)
- **FR-CAN-012**: Payment MUST be refunded (if payment captured)
- **FR-CAN-013**: Order state MUST transition to `CANCELLED` or `REFUNDED` based on payment state

### 5.3 Refund Rules

- **FR-REF-001**: Refunds MUST only be processed for orders with captured payments
- **FR-REF-002**: Wallet refunds MUST credit the original wallet account
- **FR-REF-003**: Refund amount MUST equal the original captured amount (full refund)
- **FR-REF-004**: Refund transaction MUST reference the original payment transaction

### 5.4 Partial Cancellation Policy

- **FR-CAN-020**: Partial order cancellation (cancelling some items but not others) is **NOT SUPPORTED**
- **FR-CAN-021**: All cancellation requests MUST apply to the entire order
- **FR-CAN-022**: Multi-item orders MUST be cancelled in full or not at all

### 5.5 Refund Timing

- **FR-REF-010**: Wallet refunds MUST be processed immediately upon refund approval
- **FR-REF-011**: Refund completion MUST trigger order state transition to `REFUNDED`
- **FR-REF-012**: Failed refund MUST NOT change order state — must be retried or escalated

---

## 6. Seller Interaction Rules

### 6.1 Seller Permissions on Orders

| Action | Seller Can Perform | Scope |
|--------|-------------------|-------|
| View order | Yes | Own items only |
| Acknowledge order | Yes | Own items only |
| Update to PROCESSING | Yes | Own items only |
| Update to SHIPPED | Yes | Own items only |
| Cancel order | No | N/A |
| Issue refund | No | N/A |

### 6.2 Multi-Seller Order Handling

- **FR-SEL-001**: A single order MAY contain items from multiple sellers
- **FR-SEL-002**: Each seller MUST only view and manage their own items within an order
- **FR-SEL-003**: Seller status updates MUST apply only to their items, not the entire order
- **FR-SEL-004**: Order-level state MUST reflect the aggregate of all seller item states

### 6.3 Order-Level vs Item-Level States

For multi-seller orders:

| Order-Level State | Condition |
|-------------------|-----------|
| PAID | Payment confirmed, waiting for sellers to process |
| PROCESSING | At least one seller has started processing |
| SHIPPED | All sellers have shipped their items |
| DELIVERED | All items delivered |
| COMPLETED | All items completed |

- **FR-SEL-010**: Order MUST remain in `PAID` state until at least one seller transitions to `PROCESSING`
- **FR-SEL-011**: Order MUST transition to `SHIPPED` only when ALL sellers have shipped
- **FR-SEL-012**: Order MUST transition to `DELIVERED` only when ALL items are delivered

### 6.4 Seller Cancellation Restrictions

- **FR-SEL-020**: Sellers MUST NOT have permission to cancel orders
- **FR-SEL-021**: Sellers MUST NOT have permission to issue refunds
- **FR-SEL-022**: Seller disputes MUST be escalated to admin for resolution
- **FR-SEL-023**: If seller cannot fulfill, seller MUST request admin cancellation

---

## 7. System Invariants & Guarantees

### 7.1 Atomicity Expectations

- **FR-SYS-001**: Order creation, stock reservation, and payment initiation MUST be atomic
- **FR-SYS-002**: Order cancellation, stock release, and payment refund MUST be atomic
- **FR-SYS-003**: State transitions MUST be atomic — no intermediate states during transition

### 7.2 Rollback Behavior

- **FR-SYS-010**: If stock reservation succeeds but payment initiation fails, stock MUST be rolled back
- **FR-SYS-011**: If payment succeeds but order confirmation fails, system MUST retry order confirmation (not rollback payment)
- **FR-SYS-012**: On any partial failure during order creation, all changes MUST be rolled back

### 7.3 Invariants (MUST NEVER BE VIOLATED)

| Invariant | Description |
|-----------|-------------|
| INV-001 | Stock quantity MUST never be negative |
| INV-002 | Wallet balance MUST never be negative |
| INV-003 | An order MUST NOT be simultaneously in CANCELLED and PAID states |
| INV-004 | An order MUST NOT have CAPTURED payment while in CANCELLED state (unless transitioning to REFUNDED) |
| INV-005 | Reserved stock MUST NOT exceed available stock |
| INV-006 | Total refunds MUST NOT exceed total payments for an order |
| INV-007 | A refund MUST NOT exist without a corresponding captured payment |
| INV-008 | Order items MUST NOT reference non-existent variants |
| INV-009 | Wallet debit MUST NOT exceed wallet balance |
| INV-010 | Every stock reservation MUST have a corresponding release or commitment |

### 7.4 Consistency Guarantees

- **FR-SYS-020**: Order state, payment state, and inventory state MUST be consistent at all times
- **FR-SYS-021**: Any detected inconsistency MUST trigger immediate alert for reconciliation
- **FR-SYS-022**: Reconciliation MUST prioritize: (1) customer funds safety, (2) stock accuracy, (3) order correctness

### 7.5 Failure Recovery

- **FR-SYS-030**: Pending payment timeouts MUST be automatically processed
- **FR-SYS-031**: Orphaned stock reservations (no corresponding order) MUST be released by cleanup process
- **FR-SYS-032**: Orphaned wallet holds (no corresponding order) MUST be released by cleanup process
- **FR-SYS-033**: System MUST log all recovery actions for audit

---

## Key Entities

- **Order**: Customer order containing line items, state, payment reference, timestamps
- **OrderLineItem**: Individual item in order with product/variant reference, quantity, price snapshot, reservation status
- **StockReservation**: Record of reserved stock linked to order, with reservation timestamp and status
- **Payment**: Payment record with state, amount, order reference, transaction timestamps
- **WalletTransaction**: Wallet operation record with type, amount, order reference, timestamp
- **RefundRecord**: Refund record linked to payment, with amount, reason, timestamp

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: 100% of completed orders have matching stock decrements (no orphaned reservations)
- **SC-002**: 100% of cancelled orders have released stock reservations within 5 seconds
- **SC-003**: 100% of refunds are processed within 24 hours of approval
- **SC-004**: 0% of orders have inconsistent order-payment states after reconciliation
- **SC-005**: 100% of pending payment timeouts trigger automatic cancellation
- **SC-006**: 0% of wallet balances go negative under any operation sequence
- **SC-007**: 100% of multi-seller orders aggregate correctly to order-level state
- **SC-008**: 0% of stock quantities go negative under concurrent order processing

---

## Assumptions

- **Customer Payment Methods**: COD (Cash on Delivery), InstaPay, and Credit Card
- **Seller/Artist Wallet**: Used for payouts/withdrawals (not customer payments)
- Partial refunds are not supported in current scope
- Partial order cancellation is not supported in current scope
- Seller payouts are out of scope for this specification (future phase)
- Shipping/delivery tracking integration is out of scope (future phase)
- Return/exchange workflows are out of scope beyond basic refund handling
- Stock is managed at variant level; base product stock is derived from variant totals
- Payment timeout is 15 minutes (as clarified)

