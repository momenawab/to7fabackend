# Data Model: Orders & Payments Stabilization

**Feature**: 002-orders-payments-stabilization  
**Date**: 2026-01-18  
**Status**: Complete

---

## Entity Reference

### Order

**Location**: `orders/models.py`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | AutoField | PK | Order identifier |
| user | ForeignKey(User) | NOT NULL | Customer placing order |
| total_amount | DecimalField(10,2) | NOT NULL | Total order amount |
| status | CharField(20) | NOT NULL, choices | Order lifecycle state |
| shipping_address | TextField | NOT NULL | Delivery address |
| shipping_cost | DecimalField(10,2) | DEFAULT 0.00 | Shipping fee |
| payment_method | CharField(50) | NOT NULL | cod, instapay, credit_card |
| payment_status | BooleanField | DEFAULT False | Legacy: True when paid |
| idempotency_key | CharField(255) | UNIQUE, INDEXED, NULL | Duplicate prevention key |
| payment_timeout_at | DateTimeField | NULL | **[NEW]** Auto-cancel deadline |
| created_at | DateTimeField | auto_now_add | Creation timestamp |
| updated_at | DateTimeField | auto_now | Last modification |

**Status Choices (Extended)**:
```python
STATUS_CHOICES = (
    ('pending_payment', 'Pending Payment'),     # Online payment orders
    ('cod_pending', 'COD Pending'),            # [NEW] COD orders awaiting processing
    ('paid', 'Paid'),                          # Payment confirmed
    ('processing', 'Processing'),              # [NEW] Seller acknowledged
    ('shipped', 'Shipped'),                    # Order dispatched
    ('delivered', 'Delivered'),                # [NEW] Received by customer
    ('completed', 'Completed'),                # Order fulfilled
    ('cancelled', 'Cancelled'),                # Order cancelled
    ('refunded', 'Refunded'),                  # [NEW] Payment returned
    ('failed', 'Failed'),                      # [NEW] Payment failed
)
```

**Indexes**:
- `(user, -created_at)` - User order history
- `(status)` - Status filtering
- `(idempotency_key)` - Duplicate lookup
- `(status, payment_timeout_at)` - **[NEW]** Timeout query

---

### OrderItem

**Location**: `orders/models.py`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | AutoField | PK | Line item identifier |
| order | ForeignKey(Order) | NOT NULL, CASCADE | Parent order |
| product | ForeignKey(Product) | NOT NULL, CASCADE | Product purchased |
| quantity | PositiveIntegerField | DEFAULT 1 | Quantity ordered |
| price | DecimalField(10,2) | NOT NULL | Price at purchase time |
| seller | ForeignKey(User) | NOT NULL, CASCADE | Seller fulfilling item |
| commission_rate | DecimalField(5,2) | DEFAULT 10.00 | Platform commission % |
| commission_amount | DecimalField(10,2) | DEFAULT 0.00 | Calculated commission |
| variant_id | PositiveIntegerField | NULL, INDEXED | Product variant reference |
| item_status | CharField(20) | DEFAULT 'pending' | **[NEW]** Per-item fulfillment state |
| reservation_status | CharField(20) | DEFAULT 'reserved' | **[NEW]** Stock reservation state |

**Item Status Choices [NEW]**:
```python
ITEM_STATUS_CHOICES = (
    ('pending', 'Pending'),           # Awaiting seller action
    ('processing', 'Processing'),     # Seller preparing
    ('shipped', 'Shipped'),           # Dispatched by seller
    ('delivered', 'Delivered'),       # Received by customer
    ('completed', 'Completed'),       # Fulfilled
    ('cancelled', 'Cancelled'),       # Cancelled
)
```

**Reservation Status Choices [NEW]**:
```python
RESERVATION_STATUS_CHOICES = (
    ('reserved', 'Reserved'),         # Stock held for order
    ('released', 'Released'),         # Stock returned (cancel/fail)
    ('committed', 'Committed'),       # Stock permanently decremented
)
```

**Indexes**:
- `(order, product)` - Item lookup
- `(seller)` - Seller filtering
- `(variant_id)` - Variant queries
- `(item_status)` - **[NEW]** Status aggregation

---

### Payment

**Location**: `payment/models.py`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | AutoField | PK | Payment identifier |
| order | OneToOneField(Order) | NOT NULL, CASCADE | Order reference |
| amount | DecimalField(10,2) | NOT NULL | Payment amount |
| payment_method | ForeignKey(PaymentMethod) | NULL, SET_NULL | Payment method used |
| transaction_id | CharField(255) | NULL | Gateway transaction ID |
| gateway_response | JSONField | NULL | Gateway response data |
| status | CharField(20) | DEFAULT 'pending' | Payment state |
| created_at | DateTimeField | auto_now_add | Creation timestamp |
| updated_at | DateTimeField | auto_now | Last modification |

**Status Choices (Extended)**:
```python
STATUS_CHOICES = (
    ('pending', 'Pending'),                    # Awaiting confirmation
    ('captured', 'Captured'),                  # [NEW] Payment captured (was 'completed')
    ('completed', 'Completed'),                # Legacy alias
    ('failed', 'Failed'),                      # Payment failed
    ('refunded', 'Refunded'),                  # Full refund issued
    ('partially_refunded', 'Partially Refunded'),  # Partial refund (future)
)
```

---

### Wallet Transaction

**Location**: `wallet/models.py`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | AutoField | PK | Transaction identifier |
| wallet | ForeignKey(Wallet) | NOT NULL, CASCADE | Wallet reference |
| amount | DecimalField(10,2) | NOT NULL | Transaction amount |
| transaction_type | CharField(20) | NOT NULL | deposit, withdrawal, payment, refund, commission |
| status | CharField(20) | DEFAULT 'pending' | Transaction state |
| reference_id | CharField(255) | NULL, INDEXED | Order/external reference |
| description | TextField | NULL | Human-readable description |
| balance_before | DecimalField(10,2) | NOT NULL | Wallet balance before |
| balance_after | DecimalField(10,2) | NOT NULL | Wallet balance after |
| idempotency_key | CharField(255) | UNIQUE, NULL | Duplicate prevention |
| performed_by | ForeignKey(User) | NULL | User who initiated |
| ip_address | GenericIPAddressField | NULL | Audit: IP address |
| user_agent | TextField | NULL | Audit: User agent |
| created_at | DateTimeField | auto_now_add | Creation timestamp |

**Transaction Types for Orders**:
| Type | Trigger | Description |
|------|---------|-------------|
| `payment` | Order created (wallet payment) | Debit from customer |
| `refund` | Order cancelled/refunded | Credit to customer |
| `commission` | Order completed | Credit to platform |

---

## State Transition Diagrams

### Order State Machine

```
                    ┌─────────────────┐
                    │   Initial       │
                    │   (Creation)    │
                    └────────┬────────┘
                             │
            ┌────────────────┴────────────────┐
            │ (payment_method)                │
            ▼                                 ▼
    ┌───────────────┐               ┌──────────────────┐
    │ pending_payment│              │   cod_pending     │
    │ (Online: CC,   │              │ (Cash on Delivery)│
    │  InstaPay,     │              └────────┬─────────┘
    │  Wallet)       │                       │
    └───────┬───────┘                        │
            │                                │
    ┌───────┴───────┬──────────┐            │
    ▼               ▼          ▼            │
┌───────┐      ┌─────────┐ ┌────────┐       │
│ paid  │      │cancelled│ │ failed │       │
└───┬───┘      └─────────┘ └────────┘       │
    │                                        │
    └────────────────┬───────────────────────┘
                     │
                     ▼
              ┌─────────────┐
              │ processing  │ ← Seller acknowledged
              └──────┬──────┘
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
    ┌─────────┐           ┌──────────┐
    │ shipped │           │ cancelled│ → refunded (if paid)
    └────┬────┘           └──────────┘
         │
         ▼
   ┌───────────┐
   │ delivered │ ← Delivery confirmed
   └─────┬─────┘
         │
    ┌────┴────┐
    ▼         ▼
┌──────────┐ ┌──────────┐
│completed │ │ refunded │ (return/dispute)
└──────────┘ └──────────┘

Terminal States: completed, cancelled, refunded, failed
```

### Order-Item Status Aggregation

Order-level status is derived from line item statuses:

| Condition | Order Status |
|-----------|--------------|
| All items `pending` | `paid` or `cod_pending` |
| Any item `processing` | `processing` |
| All items `shipped` | `shipped` |
| All items `delivered` | `delivered` |
| All items `completed` | `completed` |
| All items `cancelled` | `cancelled` |

---

## Relationships

```
User (1) ──────────────< Order (*)
                            │
                            │ (1)
                            ▼
Order (1) ──────────────< OrderItem (*)
                            │
                            │ (*)
                            ▼
OrderItem (*) >──────────── Product (1)
                            │
                            │ (*)
                            ▼
OrderItem (*) >──────────── User (1) [seller]

Order (1) ─────────────── Payment (1)
                            │
                            │ (*)
                            ▼
Payment (*) >──────────── PaymentMethod (1)

User (1) ─────────────── Wallet (1)
                            │
                            │ (1)
                            ▼
Wallet (1) ──────────────< Transaction (*)
```

---

## Migration Plan

### Migration 1: Extend Order Status

```python
# orders/migrations/000X_extend_order_status.py

operations = [
    migrations.AlterField(
        model_name='order',
        name='status',
        field=models.CharField(
            max_length=20,
            choices=[
                ('pending_payment', 'Pending Payment'),
                ('cod_pending', 'COD Pending'),
                ('paid', 'Paid'),
                ('processing', 'Processing'),
                ('shipped', 'Shipped'),
                ('delivered', 'Delivered'),
                ('completed', 'Completed'),
                ('cancelled', 'Cancelled'),
                ('refunded', 'Refunded'),
                ('failed', 'Failed'),
            ],
            default='pending_payment',
        ),
    ),
    migrations.AddField(
        model_name='order',
        name='payment_timeout_at',
        field=models.DateTimeField(null=True, blank=True),
    ),
    migrations.AddIndex(
        model_name='order',
        index=models.Index(fields=['status', 'payment_timeout_at'], name='order_timeout_idx'),
    ),
]
```

### Migration 2: Extend OrderItem

```python
# orders/migrations/000Y_extend_orderitem.py

operations = [
    migrations.AddField(
        model_name='orderitem',
        name='item_status',
        field=models.CharField(
            max_length=20,
            choices=[
                ('pending', 'Pending'),
                ('processing', 'Processing'),
                ('shipped', 'Shipped'),
                ('delivered', 'Delivered'),
                ('completed', 'Completed'),
                ('cancelled', 'Cancelled'),
            ],
            default='pending',
        ),
    ),
    migrations.AddField(
        model_name='orderitem',
        name='reservation_status',
        field=models.CharField(
            max_length=20,
            choices=[
                ('reserved', 'Reserved'),
                ('released', 'Released'),
                ('committed', 'Committed'),
            ],
            default='reserved',
        ),
    ),
    migrations.AddIndex(
        model_name='orderitem',
        index=models.Index(fields=['item_status'], name='orderitem_status_idx'),
    ),
]
```

### Data Migration: Normalize Existing Status

```python
# orders/migrations/000Z_normalize_status.py

def normalize_status(apps, schema_editor):
    Order = apps.get_model('orders', 'Order')
    # Map old 'pending' to 'pending_payment'
    Order.objects.filter(status='pending').update(status='pending_payment')

operations = [
    migrations.RunPython(normalize_status, migrations.RunPython.noop),
]
```

---

## Validation Rules

### Order Creation

| Rule ID | Field | Validation |
|---------|-------|------------|
| V-ORD-001 | items_data | At least one item required |
| V-ORD-002 | quantity | Must be positive integer |
| V-ORD-003 | product | Must exist and be active |
| V-ORD-004 | stock | quantity ≤ available stock (checked under lock) |
| V-ORD-005 | user | Must be authenticated and verified |
| V-ORD-006 | user | Must not be locked (banned) |
| V-ORD-007 | idempotency_key | Must be unique (if provided) |

### State Transitions

| Rule ID | Transition | Validation |
|---------|------------|------------|
| V-ST-001 | Any → Terminal | Terminal states cannot transition |
| V-ST-002 | pending_payment → cancelled | Timeout or user request |
| V-ST-003 | paid → refunded | Requires refund transaction |
| V-ST-004 | processing → shipped | All items must be processed by seller |
| V-ST-005 | delivered → completed | Auto-complete after confirmation period |

### Payment

| Rule ID | Field | Validation |
|---------|-------|------------|
| V-PAY-001 | wallet.balance | Must be ≥ order total (wallet payment) |
| V-PAY-002 | timeout | 15 minutes from order creation |
| V-PAY-003 | refund | Cannot exceed original payment |
