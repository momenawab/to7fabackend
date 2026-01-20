# Quickstart: Orders & Payments Stabilization

**Feature**: 002-orders-payments-stabilization  
**Date**: 2026-01-18  
**Prerequisites**: Python 3.9+, Django 4.2, MySQL, Redis

---

## Setup

### 1. Apply Migrations

```bash
cd "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend"
source .venv/bin/activate

# Generate migrations for new fields
python manage.py makemigrations orders

# Apply all migrations
python manage.py migrate
```

### 2. Verify Celery (for Payment Timeout)

Celery is required for the payment timeout scheduler.

```bash
# Install Celery if not present
pip install celery[redis]

# Verify Redis connection
redis-cli ping  # Should return PONG
```

### 3. Start Services

```bash
# Terminal 1: Django server
python manage.py runserver

# Terminal 2: Celery worker (for timeout tasks)
celery -A to7fabackend worker -l INFO

# Terminal 3: Celery beat (for periodic tasks)
celery -A to7fabackend beat -l INFO
```

---

## Key API Endpoints

### Order Creation

**POST** `/api/orders/create/`

```bash
curl -X POST http://localhost:8000/api/orders/create/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "items_data": [
      {"product_id": 1, "quantity": 2}
    ],
    "shipping_address": "123 Main St, Cairo",
    "payment_method": "wallet",
    "idempotency_key": "order_unique_key_123"
  }'
```

**COD Order**:
```bash
curl -X POST http://localhost:8000/api/orders/create/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "items_data": [
      {"product_id": 1, "quantity": 1}
    ],
    "shipping_address": "456 Elm St, Cairo",
    "payment_method": "cod"
  }'
```

### Order State Transitions

**Seller Acknowledge (PAID/COD_PENDING → PROCESSING)**:
```bash
curl -X POST http://localhost:8000/api/orders/<order_id>/acknowledge/ \
  -H "Authorization: Bearer <seller_token>"
```

**Seller Ship (PROCESSING → SHIPPED)**:
```bash
curl -X POST http://localhost:8000/api/orders/<order_id>/ship/ \
  -H "Authorization: Bearer <seller_token>"
```

**Delivery Confirm (SHIPPED → DELIVERED)**:
```bash
curl -X POST http://localhost:8000/api/orders/<order_id>/deliver/ \
  -H "Authorization: Bearer <token>"
```

**Order Cancel**:
```bash
curl -X POST http://localhost:8000/api/orders/<order_id>/cancel/ \
  -H "Authorization: Bearer <token>"
```

---

## Testing

### Run All Tests

```bash
cd "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend"
python manage.py test orders.tests --verbosity=2
```

### Run Specific Test Categories

```bash
# State machine tests
python manage.py test orders.tests.test_state_machine

# Stock reservation tests
python manage.py test orders.tests.test_stock_reservation

# Payment timeout tests
python manage.py test orders.tests.test_payment_timeout

# COD flow tests
python manage.py test orders.tests.test_cod_flow

# Multi-seller tests
python manage.py test orders.tests.test_multi_seller
```

---

## Order State Reference

| State | Description | Next States |
|-------|-------------|-------------|
| `pending_payment` | Online payment orders awaiting payment | `paid`, `cancelled`, `failed` |
| `cod_pending` | COD orders awaiting seller processing | `processing`, `cancelled` |
| `paid` | Payment confirmed, awaiting seller | `processing`, `cancelled`, `refunded` |
| `processing` | Seller preparing order | `shipped`, `cancelled`, `refunded` |
| `shipped` | Order dispatched | `delivered`, `refunded` |
| `delivered` | Customer received | `completed`, `refunded` |
| `completed` | Order fulfilled (terminal) | - |
| `cancelled` | Order cancelled (terminal) | - |
| `refunded` | Payment returned (terminal) | - |
| `failed` | Payment failed (terminal) | - |

---

## Payment Methods

| Method | Code | Initial State | Notes |
|--------|------|---------------|-------|
| Wallet | `wallet` | `pending_payment` | Immediate debit |
| InstaPay | `instapay` | `pending_payment` | External confirmation |
| Credit Card | `credit_card` | `pending_payment` | External confirmation |
| Cash on Delivery | `cod` | `cod_pending` | No upfront payment |

---

## Troubleshooting

### Order Stuck in pending_payment

Check if payment timeout task is running:
```bash
# Check Celery worker status
celery -A to7fabackend inspect active

# Manually trigger timeout check
python manage.py shell
>>> from orders.tasks import check_payment_timeouts
>>> check_payment_timeouts.delay()
```

### Stock Not Released After Cancel

Verify OrderItem.reservation_status:
```python
from orders.models import OrderItem
OrderItem.objects.filter(order_id=<order_id>).values('reservation_status')
```

### Multi-Seller Order State Issues

Check per-item status:
```python
from orders.models import Order
order = Order.objects.get(id=<order_id>)
for item in order.items.all():
    print(f"{item.product.name}: {item.item_status} (seller: {item.seller})")
```

---

## Configuration

### Payment Timeout (settings.py)

```python
# Payment timeout in minutes
PAYMENT_TIMEOUT_MINUTES = 15

# Timeout check interval (Celery beat)
CELERY_BEAT_SCHEDULE = {
    'check-payment-timeouts': {
        'task': 'orders.tasks.check_payment_timeouts',
        'schedule': 60.0,  # Every minute
    },
}
```

### Order Completion Delay (settings.py)

```python
# Days after delivery before auto-complete
ORDER_AUTO_COMPLETE_DAYS = 7
```
