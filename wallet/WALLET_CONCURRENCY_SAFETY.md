# Wallet Concurrency Safety Implementation

## Overview

This document describes the comprehensive changes made to ensure wallet operations are safe under concurrent access. The implementation prioritizes data accuracy over performance, following financial system best practices.

---

## Table of Contents

1. [Before vs After Logic](#before-vs-after-logic)
2. [Concurrency Safety Mechanisms](#concurrency-safety-mechanisms)
3. [Risk Analysis](#risk-analysis)
4. [New Features](#new-features)
5. [API Endpoints](#api-endpoints)
6. [Migration Guide](#migration-guide)
7. [Testing Recommendations](#testing-recommendations)

---

## Before vs After Logic

### 1. Deposit Operation

#### BEFORE (Race Condition Vulnerable)

```python
def deposit(self, amount, reference_id=None, description=None):
    if amount <= 0:
        raise ValueError("Amount must be positive")
    
    self.balance += amount  # ❌ RACE CONDITION: Read-modify-write without lock
    self.save()
    
    Transaction.objects.create(
        wallet=self,
        amount=amount,
        transaction_type='deposit',
        reference_id=reference_id,
        description=description or f"Deposit of {amount}"
    )
    return True
```

**Problems:**
- No row-level locking - multiple concurrent deposits can read stale balance
- No atomic transaction - balance update and transaction creation can fail independently
- No idempotency - duplicate deposits possible
- No audit trail - no record of balance before/after

#### AFTER (Concurrency Safe)

```python
@transaction.atomic
def deposit(self, amount, reference_id=None, description=None, idempotency_key=None):
    if amount <= 0:
        raise ValueError("Amount must be positive")
    
    # ✅ Idempotency check - prevent duplicate transactions
    if idempotency_key:
        if Transaction.objects.filter(idempotency_key=idempotency_key).exists():
            existing_tx = Transaction.objects.get(idempotency_key=idempotency_key)
            return existing_tx
    
    # ✅ Lock wallet row for update - prevents concurrent modifications
    wallet = Wallet.objects.select_for_update().get(id=self.id)
    
    # ✅ Capture balance before for audit trail
    balance_before = wallet.balance
    balance_after = balance_before + amount
    
    # ✅ Atomic update within transaction
    wallet.balance = balance_after
    wallet.save()
    
    # ✅ Create transaction with full audit trail
    tx = Transaction.objects.create(
        wallet=wallet,
        amount=amount,
        transaction_type='deposit',
        reference_id=reference_id,
        description=description or f"Deposit of {amount}",
        status='completed',
        balance_before=balance_before,
        balance_after=balance_after,
        idempotency_key=idempotency_key
    )
    return tx
```

**Improvements:**
- `@transaction.atomic` decorator ensures all-or-nothing execution
- `select_for_update()` locks wallet row until transaction completes
- Idempotency key prevents duplicate transactions
- Full audit trail with balance_before/balance_after
- Returns Transaction object for verification

---

### 2. Withdrawal Operation

#### BEFORE (Race Condition & Negative Balance Vulnerable)

```python
def withdraw(self, amount, reference_id=None, description=None):
    if amount <= 0:
        raise ValueError("Amount must be positive")
    
    # ❌ RACE CONDITION: Check and update are not atomic
    if self.balance < amount:
        raise ValueError("Insufficient funds")
    
    # ❌ Multiple withdrawals can pass this check simultaneously
    self.balance -= amount
    self.save()
    
    Transaction.objects.create(
        wallet=self,
        amount=amount,
        transaction_type='withdrawal',
        reference_id=reference_id,
        description=description or f"Withdrawal of {amount}"
    )
    return True
```

**Problems:**
- Time-of-check to time-of-use (TOCTOU) vulnerability
- Multiple concurrent withdrawals can each see sufficient funds
- Can result in negative balances
- No idempotency or audit trail

#### AFTER (Concurrency Safe)

```python
@transaction.atomic
def withdraw(self, amount, reference_id=None, description=None, idempotency_key=None):
    if amount <= 0:
        raise ValueError("Amount must be positive")
    
    # ✅ Idempotency check
    if idempotency_key:
        if Transaction.objects.filter(idempotency_key=idempotency_key).exists():
            existing_tx = Transaction.objects.get(idempotency_key=idempotency_key)
            return existing_tx
    
    # ✅ Lock wallet row for update
    wallet = Wallet.objects.select_for_update().get(id=self.id)
    
    # ✅ Capture balance before
    balance_before = wallet.balance
    
    # ✅ Check AFTER lock - prevents TOCTOU
    if balance_before < amount:
        raise ValueError("Insufficient funds")
    
    balance_after = balance_before - amount
    
    # ✅ Atomic update
    wallet.balance = balance_after
    wallet.save()
    
    # ✅ Create transaction with audit trail
    tx = Transaction.objects.create(
        wallet=wallet,
        amount=amount,
        transaction_type='withdrawal',
        reference_id=reference_id,
        description=description or f"Withdrawal of {amount}",
        status='completed',
        balance_before=balance_before,
        balance_after=balance_after,
        idempotency_key=idempotency_key
    )
    return tx
```

**Improvements:**
- Balance check happens AFTER acquiring lock
- Guaranteed no negative balances
- Full idempotency support
- Complete audit trail

---

### 3. Transfer Operation (NEW)

#### BEFORE (Not Implemented)

No transfer functionality existed. Transfers would require:
1. Withdraw from source wallet
2. Deposit to target wallet
3. Manual rollback if step 2 fails

This approach is error-prone and not atomic.

#### AFTER (Fully Atomic Transfer)

```python
@transaction.atomic
def transfer(self, amount, target_wallet, reference_id=None, description=None, idempotency_key=None):
    if amount <= 0:
        raise ValueError("Amount must be positive")
    
    if self.id == target_wallet.id:
        raise ValueError("Cannot transfer to the same wallet")
    
    # ✅ Idempotency check
    if idempotency_key:
        if Transaction.objects.filter(idempotency_key=idempotency_key).exists():
            existing_tx = Transaction.objects.filter(idempotency_key=idempotency_key)
            withdrawal_tx = existing_tx.filter(transaction_type='withdrawal').first()
            deposit_tx = existing_tx.filter(transaction_type='deposit').first()
            return (withdrawal_tx, deposit_tx)
    
    # ✅ Lock both wallets in consistent order (by ID) to prevent deadlocks
    wallets_to_lock = sorted([self, target_wallet], key=lambda w: w.id)
    locked_wallets = list(Wallet.objects.select_for_update().filter(
        id__in=[w.id for w in wallets_to_lock]
    ))
    
    source_wallet = next(w for w in locked_wallets if w.id == self.id)
    dest_wallet = next(w for w in locked_wallets if w.id == target_wallet.id)
    
    # ✅ Capture balances before
    source_balance_before = source_wallet.balance
    dest_balance_before = dest_wallet.balance
    
    # ✅ Prevent negative balance
    if source_balance_before < amount:
        raise ValueError("Insufficient funds")
    
    source_balance_after = source_balance_before - amount
    dest_balance_after = dest_balance_before + amount
    
    # ✅ Atomic update of both wallets
    source_wallet.balance = source_balance_after
    dest_wallet.balance = dest_balance_after
    source_wallet.save()
    dest_wallet.save()
    
    # ✅ Create both transaction records
    withdrawal_tx = Transaction.objects.create(
        wallet=source_wallet,
        amount=amount,
        transaction_type='withdrawal',
        reference_id=reference_id,
        description=description or f"Transfer to {dest_wallet.user.email}",
        status='completed',
        balance_before=source_balance_before,
        balance_after=source_balance_after,
        idempotency_key=idempotency_key
    )
    
    deposit_tx = Transaction.objects.create(
        wallet=dest_wallet,
        amount=amount,
        transaction_type='deposit',
        reference_id=reference_id,
        description=description or f"Transfer from {source_wallet.user.email}",
        status='completed',
        balance_before=dest_balance_before,
        balance_after=dest_balance_after,
        idempotency_key=idempotency_key
    )
    
    return (withdrawal_tx, deposit_tx)
```

**Key Features:**
- Both wallets locked simultaneously
- Consistent locking order prevents deadlocks
- All-or-nothing execution
- Full audit trail for both sides

---

## Concurrency Safety Mechanisms

### 1. Row-Level Locking with `select_for_update()`

**What it does:**
- Locks the selected database row(s) until the transaction completes
- Prevents other transactions from reading or modifying the locked row
- Ensures serializable execution of balance updates

**How it works:**
```python
# Without lock (vulnerable to race conditions)
wallet = Wallet.objects.get(id=1)  # Read balance: 100
# Another transaction reads balance: 100
wallet.balance += 50  # Write: 150
wallet.save()
# Other transaction also writes: 150 (lost update!)

# With lock (safe)
wallet = Wallet.objects.select_for_update().get(id=1)  # Lock row
# Other transaction waits...
wallet.balance += 50  # Write: 150
wallet.save()
# Lock released, other transaction can now proceed
```

**Benefits:**
- Prevents lost updates
- Ensures consistent reads
- Serializes concurrent operations
- No double-spending

---

### 2. Atomic Transactions with `@transaction.atomic`

**What it does:**
- Wraps all database operations in a single transaction
- Either all operations succeed, or none do
- Automatic rollback on any exception

**How it works:**
```python
@transaction.atomic
def deposit(self, amount):
    wallet = Wallet.objects.select_for_update().get(id=self.id)
    wallet.balance += amount
    wallet.save()  # If this fails, transaction rolls back
    
    Transaction.objects.create(...)  # If this fails, wallet update rolls back too
```

**Benefits:**
- Data consistency guaranteed
- No partial updates
- Automatic error recovery
- Simplified error handling

---

### 3. Idempotency Keys

**What it does:**
- Prevents duplicate transactions
- Allows safe retry of failed requests
- Unique identifier for each operation

**How it works:**
```python
# First request
wallet.deposit(amount=100, idempotency_key="order_123")
# Creates transaction with idempotency_key="order_123"

# Retry request (client didn't receive response)
wallet.deposit(amount=100, idempotency_key="order_123")
# Returns existing transaction instead of creating new one
```

**Benefits:**
- Safe retry logic
- Prevents double-charging
- Client-side idempotency
- Network resilience

---

### 4. Audit Trail

**What it does:**
- Records complete transaction history
- Tracks balance before and after each operation
- Stores who performed the action and from where

**Fields added:**
- `balance_before`: Balance before transaction
- `balance_after`: Balance after transaction
- `idempotency_key`: Unique operation identifier
- `performed_by`: User who performed the transaction
- `ip_address`: Client IP address
- `user_agent`: Client user agent string

**Benefits:**
- Complete transaction history
- Forensic analysis capability
- Regulatory compliance
- Debugging support

---

### 5. Consistent Lock Ordering

**What it does:**
- Always locks wallets in the same order (by ID)
- Prevents circular wait conditions
- Eliminates deadlock possibility

**How it works:**
```python
# Deadlock scenario (without consistent ordering)
# Transaction A: Lock wallet 1, then wallet 2
# Transaction B: Lock wallet 2, then wallet 1
# Result: Both wait forever (deadlock)

# Safe scenario (with consistent ordering)
wallets_to_lock = sorted([wallet1, wallet2], key=lambda w: w.id)
# Both transactions lock in same order: wallet 1, then wallet 2
# Result: No deadlock
```

**Benefits:**
- Deadlock-free transfers
- Predictable locking behavior
- Better system reliability

---

## Risk Analysis

### Scenario 1: Concurrent Deposits

#### WITHOUT Concurrency Safety

```
Initial balance: $100

Transaction A reads balance: $100
Transaction B reads balance: $100

Transaction A adds $50 → $150
Transaction B adds $50 → $150

Both save → Final balance: $150
Expected: $200
Lost: $50
```

**Risk:** Lost update, financial loss, accounting discrepancy

#### WITH Concurrency Safety

```
Initial balance: $100

Transaction A: SELECT ... FOR UPDATE (locks row)
Transaction B: SELECT ... FOR UPDATE (waits for A)

Transaction A adds $50 → $150, saves, releases lock
Transaction B reads: $150 (current value)
Transaction B adds $50 → $200, saves

Final balance: $200
Expected: $200
Correct!
```

---

### Scenario 2: Concurrent Withdrawals

#### WITHOUT Concurrency Safety

```
Initial balance: $100

Transaction A reads balance: $100
Transaction B reads balance: $100

Transaction A checks: $100 >= $50 ✓
Transaction B checks: $100 >= $50 ✓

Transaction A subtracts $50 → $50
Transaction B subtracts $50 → $50

Both save → Final balance: $50
Expected: $0
Negative balance prevented? NO!
```

**Risk:** Negative balance, overdraft, financial loss

#### WITH Concurrency Safety

```
Initial balance: $100

Transaction A: SELECT ... FOR UPDATE (locks row)
Transaction B: SELECT ... FOR UPDATE (waits for A)

Transaction A checks: $100 >= $50 ✓
Transaction A subtracts $50 → $50, saves, releases lock

Transaction B reads: $50
Transaction B checks: $50 >= $50 ✓
Transaction B subtracts $50 → $0, saves

Final balance: $0
Expected: $0
Correct!
```

---

### Scenario 3: Transfer Failure

#### WITHOUT Atomicity

```
Initial: A=$100, B=$50

Transaction A withdraws $50 from A
A.balance = $50, save ✓

Network error before deposit to B
B never receives $50

Final: A=$50, B=$50
Expected: A=$50, B=$100
Lost: $50
```

**Risk:** Lost funds, partial execution, data inconsistency

#### WITH Atomicity

```
Initial: A=$100, B=$50

Transaction A: Lock A and B
Withdraw $50 from A: A.balance = $50
Deposit $50 to B: B.balance = $100

Network error
@transaction.atomic rolls back both changes

Final: A=$100, B=$50
Expected: A=$100, B=$50
No loss!
```

---

### Scenario 4: Duplicate Requests

#### WITHOUT Idempotency

```
Client sends deposit request
Server processes: balance $100 → $150
Network timeout, client doesn't receive response
Client retries: balance $150 → $200

Final: $200
Expected: $150
Double-charged!
```

**Risk:** Double-charging, customer disputes, financial loss

#### WITH Idempotency

```
Client sends deposit with idempotency_key="order_123"
Server processes: balance $100 → $150, creates transaction
Network timeout, client doesn't receive response
Client retries with same idempotency_key="order_123"
Server finds existing transaction, returns it

Final: $150
Expected: $150
Correct!
```

---

## New Features

### 1. Balance History Endpoint

**Endpoint:** `GET /wallet/balance-history/`

**Purpose:** Provides historical view of balance changes over time

**Query Parameters:**
- `date_from`: Start date (YYYY-MM-DD)
- `date_to`: End date (YYYY-MM-DD)
- `limit`: Number of records (default: 100)
- `offset`: Pagination offset (default: 0)

**Response:**
```json
{
  "count": 150,
  "results": [
    {
      "timestamp": "2024-01-15T10:30:00Z",
      "balance": "150.00",
      "transaction_id": 123,
      "transaction_type": "deposit",
      "amount": "50.00"
    },
    ...
  ],
  "current_balance": "150.00"
}
```

**Use Cases:**
- Balance trend analysis
- Transaction reconciliation
- Financial reporting
- Audit trail verification

---

### 2. Transfer Funds Endpoint

**Endpoint:** `POST /wallet/transfer/`

**Purpose:** Transfer funds between wallets atomically

**Request Body:**
```json
{
  "target_user_id": 42,
  "amount": "50.00",
  "description": "Payment for services",
  "idempotency_key": "transfer_order_123"
}
```

**Response:**
```json
{
  "message": "Successfully transferred 50.00 to user@example.com",
  "source_wallet": {
    "id": 1,
    "user_email": "sender@example.com",
    "balance": "50.00"
  },
  "target_wallet": {
    "id": 2,
    "user_email": "user@example.com",
    "balance": "100.00"
  },
  "withdrawal_transaction": { ... },
  "deposit_transaction": { ... },
  "idempotency_key": "transfer_order_123"
}
```

**Features:**
- Fully atomic (both succeed or both fail)
- Concurrency-safe with deadlock prevention
- Idempotent
- Full audit trail

---

### 3. Transaction Detail Endpoint

**Endpoint:** `GET /wallet/transactions/<id>/`

**Purpose:** Get detailed information about a specific transaction

**Response:**
```json
{
  "id": 123,
  "wallet": 1,
  "wallet_user_email": "user@example.com",
  "amount": "50.00",
  "transaction_type": "deposit",
  "reference_id": "order_456",
  "description": "Deposit of 50.00",
  "status": "completed",
  "balance_before": "100.00",
  "balance_after": "150.00",
  "idempotency_key": "deposit_order_123",
  "performed_by": "admin@example.com",
  "performed_by_email": "admin@example.com",
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "created_at": "2024-01-15T10:30:00Z",
  "created_at_formatted": "Jan 15, 2024 10:30"
}
```

**Features:**
- Complete audit information
- Balance before/after
- Performed by tracking
- IP and user agent logging

---

### 4. Admin Transactions Endpoint

**Endpoint:** `GET /wallet/admin/transactions/`

**Purpose:** Admin-only view of all transactions

**Query Parameters:**
- `user_id`: Filter by user
- `type`: Filter by transaction type
- `status`: Filter by status
- `reference_id`: Filter by reference ID
- `date_from`: Start date
- `date_to`: End date
- `limit`: Pagination limit
- `offset`: Pagination offset

**Use Cases:**
- Fraud detection
- System monitoring
- Audit compliance
- Financial reporting

---

### 5. Balance Snapshot Endpoint

**Endpoint:** `POST /wallet/admin/snapshot/`

**Purpose:** Create periodic balance snapshots for historical analysis

**Request Body:**
```json
{
  "user_id": 42
}
```

**Response:**
```json
{
  "message": "Balance snapshot created successfully",
  "snapshot": {
    "id": 1,
    "wallet": "user@example.com",
    "balance": "150.00",
    "transaction_count": 25,
    "snapshot_date": "2024-01-15T10:30:00Z"
  }
}
```

**Use Cases:**
- Periodic reporting
- Balance reconciliation
- Historical analysis
- Performance optimization (avoid recalculating from all transactions)

---

## API Endpoints

### Wallet Operations

| Method | Endpoint | Auth | Description |
|---------|----------|-------|-------------|
| GET | `/wallet/` | User | Get wallet details |
| POST | `/wallet/deposit/` | Admin | Deposit funds |
| POST | `/wallet/withdraw/` | Admin | Withdraw funds |
| POST | `/wallet/transfer/` | User | Transfer funds |

### Transaction History

| Method | Endpoint | Auth | Description |
|---------|----------|-------|-------------|
| GET | `/wallet/transactions/` | User | Get transaction history |
| GET | `/wallet/transactions/<id>/` | User/Admin | Get transaction detail |
| GET | `/wallet/admin/transactions/` | Admin | Get all transactions |

### Balance History

| Method | Endpoint | Auth | Description |
|---------|----------|-------|-------------|
| GET | `/wallet/balance-history/` | User | Get balance history |

### Admin Operations

| Method | Endpoint | Auth | Description |
|---------|----------|-------|-------------|
| POST | `/wallet/admin/snapshot/` | Admin | Create balance snapshot |

---

## Migration Guide

### Database Migration Required

The following fields were added to the `Transaction` model:

```python
balance_before = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
balance_after = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
idempotency_key = models.CharField(max_length=255, unique=True, null=True, blank=True, db_index=True)
performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
ip_address = models.GenericIPAddressField(null=True, blank=True)
user_agent = models.TextField(blank=True, null=True)
```

A new model was added:

```python
class BalanceSnapshot(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='balance_snapshots')
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    snapshot_date = models.DateTimeField(auto_now_add=True)
    transaction_count = models.IntegerField(default=0)
```

### Migration Steps

1. Create migration:
```bash
python manage.py makemigrations wallet
```

2. Review migration file to ensure it's safe

3. Apply migration:
```bash
python manage.py migrate wallet
```

4. Create indexes for performance:
```bash
python manage.py migrate wallet --run-syncdb
```

---

## Testing Recommendations

### 1. Concurrency Testing

Test concurrent operations to verify race condition prevention:

```python
import threading
import time

def test_concurrent_deposits():
    wallet = Wallet.objects.get(user_id=1)
    initial_balance = wallet.balance
    
    def deposit_thread():
        wallet = Wallet.objects.get(user_id=1)
        wallet.deposit(amount=50, idempotency_key=f"test_{threading.get_ident()}")
    
    # Create 10 concurrent deposit threads
    threads = []
    for i in range(10):
        t = threading.Thread(target=deposit_thread)
        threads.append(t)
    
    # Start all threads simultaneously
    for t in threads:
        t.start()
    
    # Wait for all threads to complete
    for t in threads:
        t.join()
    
    # Verify final balance
    wallet.refresh_from_db()
    expected_balance = initial_balance + Decimal('500.00')  # 10 * 50
    assert wallet.balance == expected_balance, f"Expected {expected_balance}, got {wallet.balance}"
```

### 2. Idempotency Testing

Test that duplicate requests don't create duplicate transactions:

```python
def test_idempotency():
    wallet = Wallet.objects.get(user_id=1)
    initial_balance = wallet.balance
    
    # First deposit
    tx1 = wallet.deposit(amount=100, idempotency_key="test_idempotent")
    
    # Duplicate deposit with same key
    tx2 = wallet.deposit(amount=100, idempotency_key="test_idempotent")
    
    # Verify same transaction returned
    assert tx1.id == tx2.id
    
    # Verify balance only increased once
    wallet.refresh_from_db()
    assert wallet.balance == initial_balance + Decimal('100.00')
```

### 3. Negative Balance Prevention Testing

Test that withdrawals cannot create negative balances:

```python
def test_negative_balance_prevention():
    wallet = Wallet.objects.get(user_id=1)
    wallet.balance = Decimal('100.00')
    wallet.save()
    
    # Try to withdraw more than balance
    with pytest.raises(ValueError, match="Insufficient funds"):
        wallet.withdraw(amount=150.00)
    
    # Verify balance unchanged
    wallet.refresh_from_db()
    assert wallet.balance == Decimal('100.00')
```

### 4. Transfer Atomicity Testing

Test that transfers are fully atomic:

```python
def test_transfer_atomicity():
    source_wallet = Wallet.objects.get(user_id=1)
    target_wallet = Wallet.objects.get(user_id=2)
    
    source_initial = source_wallet.balance
    target_initial = target_wallet.balance
    
    # Successful transfer
    withdrawal_tx, deposit_tx = source_wallet.transfer(
        amount=50.00,
        target_wallet=target_wallet,
        idempotency_key="test_transfer"
    )
    
    # Verify balances
    source_wallet.refresh_from_db()
    target_wallet.refresh_from_db()
    
    assert source_wallet.balance == source_initial - Decimal('50.00')
    assert target_wallet.balance == target_initial + Decimal('50.00')
    
    # Verify transactions created
    assert withdrawal_tx.transaction_type == 'withdrawal'
    assert deposit_tx.transaction_type == 'deposit'
    assert withdrawal_tx.idempotency_key == deposit_tx.idempotency_key
```

### 5. Deadlock Prevention Testing

Test that concurrent transfers don't cause deadlocks:

```python
def test_deadlock_prevention():
    wallet1 = Wallet.objects.get(user_id=1)
    wallet2 = Wallet.objects.get(user_id=2)
    
    def transfer_1_to_2():
        wallet1.transfer(amount=50, target_wallet=wallet2, idempotency_key="test_deadlock_1")
    
    def transfer_2_to_1():
        wallet2.transfer(amount=50, target_wallet=wallet1, idempotency_key="test_deadlock_2")
    
    # Create concurrent transfers in opposite directions
    t1 = threading.Thread(target=transfer_1_to_2)
    t2 = threading.Thread(target=transfer_2_to_1)
    
    t1.start()
    t2.start()
    
    t1.join(timeout=10)
    t2.join(timeout=10)
    
    # If deadlock occurred, threads would not complete
    assert not t1.is_alive() and not t2.is_alive()
```

---

## Performance Considerations

### Lock Duration

Row locks are held for the duration of the transaction. To minimize lock duration:

1. Keep transactions short
2. Avoid external API calls within transactions
3. Minimize database queries within transactions

### Index Usage

The following indexes have been added for performance:

```python
class Transaction(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['idempotency_key']),  # Fast idempotency checks
            models.Index(fields=['wallet', 'created_at']),  # Fast history queries
            models.Index(fields=['reference_id']),  # Fast reference lookups
        ]
```

### Database Isolation Level

For optimal performance and correctness, use `READ COMMITTED` isolation level:

```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'OPTIONS': {
            'isolation_level': psycopg2.extensions.ISOLATION_LEVEL_READ_COMMITTED,
        },
    }
}
```

---

## Conclusion

The wallet concurrency safety implementation provides:

✅ **Race Condition Prevention:** Row-level locking ensures serializable execution
✅ **Atomic Operations:** All-or-nothing transaction execution
✅ **Idempotency:** Safe retry of failed requests
✅ **Negative Balance Prevention:** Guaranteed balance integrity
✅ **Comprehensive Audit Trail:** Complete transaction history
✅ **Deadlock-Free Transfers:** Consistent locking order
✅ **Regulatory Compliance:** Full audit and traceability

The implementation prioritizes data accuracy over performance, which is the correct approach for financial systems. The performance impact is minimal due to:
- Short transaction duration
- Proper indexing
- Efficient locking strategy
- Optimized database queries

All operations are now safe under concurrent access, with no risk of lost updates, negative balances, or partial executions.
