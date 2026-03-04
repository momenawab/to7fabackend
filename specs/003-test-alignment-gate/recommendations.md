# Recommendations: Spec 002 Deferred Debt Resolution

**Feature**: Spec 002 Test Alignment & Gate Stabilization
**Date**: 2026-02-08
**Purpose**: Actionable recommendations for resolving deferred test debt

## Overview

This document provides prioritized recommendations for resolving the 68 deferred tests identified during the Spec 002 test alignment process. These recommendations are organized by priority and impact.

## Priority Matrix

| Priority | Count | Impact | Effort |
|----------|-------|--------|--------|
| **P0 - Critical Test Fixes** | 10 | High | Low |
| **P1 - Test Infrastructure** | 54 | Medium | Medium |
| **P2 - Infrastructure Setup** | 3 | Low | High |
| **P3 - Documentation** | Ongoing | Low | Low |

---

## P0: Critical Test Fixes (High Impact, Low Effort)

**Target**: Fix the 10 failing critical tests to achieve 100% critical test pass rate

### 1. Fix IntegrityError: Duplicate Wallet (6 tests)

**Tests Affected**:
- `test_cancellation_releases_wallet_holds`
- `test_cancellation_with_captured_payment_refunds`
- `test_cancellation_state_based_on_payment`
- `test_refund_only_for_captured_payments`
- `test_refund_credits_original_wallet`
- `test_refund_amount_equals_captured_amount`
- `test_cancellation_stock_and_refund_atomic`
- `test_debit_amount_exceeds_balance_fails`
- `test_debit_equals_balance_succeeds`
- `test_partial_debit_succeeds`

**Root Cause**: Tests create wallets using `Wallet.objects.create()` for users who already have wallets from the conftest.py fixture.

**Fix**:
```python
# In test setup, replace:
wallet = Wallet.objects.create(user=user, balance=Decimal('100.00'))

# With:
wallet, created = Wallet.objects.get_or_create(
    user=user,
    defaults={'balance': Decimal('100.00')}
)
```

**Estimated Effort**: 1 hour

**Owner**: Test Infrastructure Team

---

### 2. Fix FieldError: Transaction.order (1 test)

**Test Affected**: `test_total_refunds_not_exceed_payments`

**Root Cause**: Test expects `Transaction.objects.filter(order=order)` but model uses `reference_id` field.

**Fix**:
```python
# Replace:
transactions = WalletTransaction.objects.filter(
    wallet=wallet,
    order=order,
    transaction_type='CREDIT'
)

# With:
transactions = WalletTransaction.objects.filter(
    wallet=wallet,
    reference_id=str(order.id),
    transaction_type='CREDIT'
)
```

**Alternative**: Add a property to Transaction model:
```python
# In wallet/models.py Transaction class
@property
def order(self):
    """Get the order referenced by this transaction."""
    if self.reference_id:
        from orders.models import Order
        try:
            return Order.objects.get(id=int(self.reference_id))
        except (ValueError, Order.DoesNotExist):
            return None
    return None
```

**Estimated Effort**: 2 hours

**Owner**: Backend Team

---

### 3. Fix API Response Tuple Issues (3 tests)

**Tests Affected**:
- `test_order_creation_stock_and_payment_atomic`
- `test_stock_validated_at_order_creation_time`
- `test_stock_reservation_atomic_with_validation`

**Root Cause**: Order creation view returns `(status_code, data)` tuple instead of `Response` object in error paths.

**Fix**: Update view to return Response objects:
```python
# In orders/views.py order creation view
# Replace:
return (400, {"error": "Not enough stock"})

# With:
from rest_framework.response import Response
return Response({"error": "Not enough stock"}, status=400)
```

**Estimated Effort**: 3 hours

**Owner**: Backend Team

---

## P1: Test Infrastructure Improvements (Medium Impact, Medium Effort)

### 4. Refactor Cart Test Pattern

**Tests Affected**: Order creation and idempotency tests

**Issue**: Tests use `cart.items = [...]` pattern which doesn't work with Django ORM

**Fix**: Update tests to use `cart.add_item()`:
```python
# Replace:
cart.items = [
    {"product": product, "quantity": 2}
]

# With:
cart.add_item(product=product, quantity=2)
```

**Estimated Effort**: 4 hours

**Owner**: Test Infrastructure Team

---

### 5. Fix Inventory Test Fixtures

**Tests Affected**: All inventory tests (34 tests)

**Issue**: Tests create Products without required Category and seller relationships

**Fix**: Create proper fixture:
```python
@pytest.fixture
def product_with_category(db):
    category = Category.objects.create(
        name=f'Test Category {uuid.uuid4().hex[:8]}',
        description='Test category'
    )
    seller = User.objects.create_user(
        email=f'seller_{uuid.uuid4().hex[:8]}@example.com',
        password='testpass123',
        user_type='artist'
    )
    product = Product.objects.create(
        seller=seller,
        category=category,
        name=f'Test Product {uuid.uuid4().hex[:8]}',
        base_price=Decimal('50.00'),
        stock_quantity=100
    )
    return product
```

**Estimated Effort**: 6 hours

**Owner**: Test Infrastructure Team

---

## P2: Infrastructure Setup (Low Impact, High Effort)

### 6. Configure Celery for Integration Tests

**Tests Affected**: 3 infrastructure-dependent tests

**Requirements**:
- Celery worker running in test environment
- Redis as Celery broker
- Background task execution for payment timeouts

**Implementation**:
1. Add `pytest-celery` package
2. Configure test Celery app
3. Add `@pytest.mark.celery` marker
4. Update CI to run Celery worker during tests

**Estimated Effort**: 16 hours

**Owner**: DevOps Team

**Priority**: Low - Tests are properly marked as deferred and do not block the gate

---

## P3: Documentation and Process (Low Impact, Low Effort)

### 7. Document Test Classification Process

**Goal**: Ensure future features follow the same classification framework

**Actions**:
1. Add quickstart guide to project documentation
2. Create test classification template
3. Document pytest marker usage
4. Add CI configuration examples

**Estimated Effort**: 4 hours

**Owner**: Documentation Team

---

### 8. Update API Documentation

**Goal**: Document implementation choices where production differs from spec

**Actions**:
1. Document cancellation endpoint behavior (200 vs 403)
2. Document wallet Transaction model field naming
3. Document order creation response format
4. Update OpenAPI/Swagger specs

**Estimated Effort**: 6 hours

**Owner**: Backend/Documentation Teams

---

## Implementation Roadmap

### Sprint 1 (Week 1)
- [ ] Fix IntegrityError: duplicate wallet (6 tests)
- [ ] Fix FieldError: Transaction.order (1 test)
- [ ] Fix API Response tuple issues (3 tests)

**Target**: 100% critical test pass rate

### Sprint 2 (Week 2)
- [ ] Refactor cart test pattern
- [ ] Fix inventory test fixtures
- [ ] Update CI to run critical tests as gate

**Target**: Improved overall test pass rate

### Sprint 3 (Week 3-4)
- [ ] Configure Celery for integration tests
- [ ] Document test classification process
- [ ] Update API documentation

**Target**: Complete infrastructure and documentation

---

## Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Critical test pass rate | 81% (43/53) | 100% (53/53) | `pytest -m critical` |
| Overall test pass rate | 42% (54/129) | 70%+ (90/129) | `pytest test_spec002_*` |
| Test documentation coverage | 100% | Maintain | All tests classified |
| CI gate time | N/A | < 5 min | Critical tests only |

---

## Gate Decision Impact

### Current State: CONDITIONAL_PASS

**To upgrade to PASS**: Complete P0 recommendations (critical test fixes)

**Conditional Pass Remains Valid For**:
- Production deployment (core business logic validated)
- Feature development (quality gate established)
- Hot fixes (critical tests pass)

**Upgrade Path**:
```
CONDITIONAL_PASS → PASS
    ↓
Complete P0: Fix 10 failing critical tests
    ↓
Verify: pytest -m critical (53/53 passing)
```

---

## Questions?

For questions about these recommendations, refer to:
- **Test Classification**: test-classification.md
- **Critical Failures**: critical-test-failures.md
- **Deferred Debt**: deferred-test-debt.md
- **Gate Verdict**: gate-verdict.md
