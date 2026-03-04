# Quick Start: Variant System Implementation

**Feature**: Spec 005 - Variant System Implementation
**Purpose**: Verification guide after implementation deployment
**Last Updated**: 2025-02-09

---

## Overview

This guide helps you verify that the variant system implementation is working correctly after deployment. It focuses on validating the binding architectural decisions from Spec 004.

---

## Prerequisites

- Django server running (`python manage.py runserver`)
- Database with test products and variants
- pytest configured for running invariant tests

---

## 1. Verify Canonical Variant System

### 1.1 Run Invariant Tests

```bash
# Test that only ProductCategoryVariantOption owns variant stock
pytest products/tests/test_invariants.py -k "INV_014" -v

# Test that new products use ProductCategoryVariantOption
pytest products/tests/test_invariants.py -k "INV_015" -v

# Test that combination_stocks is not used for stock
pytest products/tests/test_invariants.py -k "INV_016" -v
```

**Expected Result**: All tests pass

### 1.2 Verify ProductVariant Deprecation

```python
# In Django shell: python manage.py shell
from products.models import Product, ProductVariant, ProductCategoryVariantOption

# This should trigger a deprecation warning
variant = ProductVariant.objects.first()
stock = variant.stock_count  # Should log DEPRECATED warning

# Verify the canonical system works
canonical = ProductCategoryVariantOption.objects.first()
stock = canonical.stock_count  # Should work without warning
```

**Expected Result**: Deprecation warning logged for ProductVariant access

---

## 2. Verify Approval & Visibility Enforcement

### 2.1 Test Product Listing

```bash
# Create test products with different approval statuses
# In Django shell:
from products.models import Product

Product.objects.create(
    name="Pending Product",
    approval_status='pending',
    is_active=True
)

Product.objects.create(
    name="Rejected Product",
    approval_status='rejected',
    is_active=True
)

Product.objects.create(
    name="Approved Product",
    approval_status='approved',
    is_active=True
)
```

```bash
# Test public API - should only return approved products
curl -X GET http://localhost:8000/api/v1/products/
```

**Expected Result**:
- Only "Approved Product" appears in response
- "Pending Product" and "Rejected Product" are NOT included

### 2.2 Verify approved() Manager

```python
# In Django shell:
from products.models import Product

# Using approved() manager
approved_products = Product.objects.approved()
print(f"Approved count: {approved_products.count()}")

# Regular query (includes non-approved)
all_active = Product.objects.filter(is_active=True)
print(f"All active count: {all_active.count()}")
```

**Expected Result**:
- `approved_products.count()` = 1 (only approved product)
- `all_active.count()` = 3 (all active products regardless of approval)

### 2.3 Test Cart Validation

```bash
# Try adding a rejected product to cart
curl -X POST http://localhost:8000/api/v1/cart/items/ \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": <REJECTED_PRODUCT_ID>,
    "quantity": 1
  }'
```

**Expected Result**: 400 error with message about product not being approved

```json
{
  "error": "PRODUCT_NOT_APPROVED",
  "message": "Product must be approved before adding to cart",
  "details": {
    "product_id": 123,
    "approval_status": "rejected"
  }
}
```

---

## 3. Verify Variant Identification Consistency

### 3.1 Run Order Invariant Tests

```bash
# Test OrderItem.variant_id references
pytest orders/tests/test_invariants.py -k "INV_006 or INV_007" -v
```

**Expected Result**: All tests pass

### 3.2 Test Order Creation with Variants

```python
# In Django shell:
from products.models import Product, ProductCategoryVariantOption
from orders.atomic_order_system import AtomicOrderCreator
from custom_auth.models import User

# Get test data
seller = User.objects.filter(role='seller').first()
product = Product.objects.approved().first()
variant = ProductCategoryVariantOption.objects.filter(product=product).first()

# Create order with variant
creator = AtomicOrderCreator()
order = creator.create_order(
    user=User.objects.first(),
    items_data=[{
        'product_id': product.id,
        'variant_id': variant.id,  # This should be ProductCategoryVariantOption.id
        'quantity': 1
    }],
    seller_id=seller.id
)

# Verify OrderItem.variant_id references ProductCategoryVariantOption
order_item = order.items.first()
assert order_item.variant_id == variant.id
```

**Expected Result**: Order created successfully, variant_id correctly stored

---

## 4. Verify Stock Operations

### 4.1 Run Stock Invariant Tests

```bash
# Test stock operations follow invariant rules
pytest orders/tests/test_invariants.py -k "INV_001 or INV_002 or INV_003 or INV_004" -v
```

**Expected Result**: All tests pass

### 4.2 Verify Stock Decrement

```python
# In Django shell:
from products.models import ProductCategoryVariantOption
from orders.atomic_order_system import AtomicOrderCreator

variant = ProductCategoryVariantOption.objects.first()
initial_stock = variant.stock_count
print(f"Initial stock: {initial_stock}")

# Create order (stock should decrement)
creator = AtomicOrderCreator()
order = creator.create_order(
    user=User.objects.first(),
    items_data=[{
        'product_id': variant.product.id,
        'variant_id': variant.id,
        'quantity': 2
    }],
    seller_id=variant.product.seller.id
)

# Verify stock decreased
variant.refresh_from_db()
print(f"Stock after order: {variant.stock_count}")
assert variant.stock_count == initial_stock - 2
```

**Expected Result**: Stock decremented from ProductCategoryVariantOption.stock_count

### 4.3 Verify Stock Restoration on Cancel

```python
# In Django shell:
from orders.atomic_order_system import StockLockManager

# Cancel the order
stock_before_cancel = variant.stock_count
StockLockManager.release_stock(order)
variant.refresh_from_db()

print(f"Stock after cancel: {variant.stock_count}")
assert variant.stock_count == stock_before_cancel + 2
```

**Expected Result**: Stock restored to the same ProductCategoryVariantOption

---

## 5. Verify Cart Data Structure

### 5.1 Run Cart Invariant Tests

```bash
# Test CartItem.variant_id behavior
pytest cart/tests/test_invariants.py -k "INV_017 or INV_018 or INV_019" -v
```

**Expected Result**: All tests pass

### 5.2 Verify variant_id is Source of Truth

```python
# In Django shell:
from cart.models import CartItem
from products.models import Product, ProductCategoryVariantOption

# Add item to cart with variant_id
cart_item = CartItem.objects.create(
    cart=Cart.objects.first(),
    product=Product.objects.first(),
    variant_id=ProductCategoryVariantOption.objects.first().id,
    quantity=1
)

# selected_variants should be ignored for inventory
assert cart_item.variant_id is not None  # Canonical reference
```

**Expected Result**: variant_id used for all inventory operations

---

## 6. Check Deprecation Warnings

### 6.1 View Logs for Warnings

```bash
# View application logs for deprecation messages
tail -f logs/app.log | grep DEPRECATED
```

**Expected Warnings**:
- `ProductVariant.stock_count is deprecated`
- `combination_stocks is deprecated`
- `selected_variants is deprecated for inventory operations`

### 6.2 Test Deprecation Triggering

```python
# In Django shell with warnings enabled:
import warnings
warnings.simplefilter('always')

from products.models import ProductVariant

variant = ProductVariant.objects.first()
stock = variant.stock_count  # Should trigger DeprecationWarning
```

**Expected Result**: DeprecationWarning raised

---

## Full Test Suite

Run all invariant tests together:

```bash
# Stock invariants
pytest orders/tests/test_invariants.py -k "INV_001 or INV_002 or INV_003 or INV_004 or INV_005" -v

# Order invariants
pytest orders/tests/test_invariants.py -k "INV_006 or INV_007 or INV_008 or INV_009" -v

# Visibility invariants
pytest products/tests/test_invariants.py -k "INV_010 or INV_011 or INV_012 or INV_013" -v

# Variant system invariants
pytest products/tests/test_invariants.py -k "INV_014 or INV_015 or INV_016" -v

# Cart invariants
pytest cart/tests/test_invariants.py -k "INV_017 or INV_018 or INV_019" -v
```

---

## Troubleshooting

### Issue: Tests fail with "Product not found"

**Solution**: Ensure test products are created with proper approval_status:

```python
Product.objects.create(
    name="Test Product",
    approval_status='approved',
    is_active=True
)
```

### Issue: variant_id foreign key constraint error

**Solution**: Ensure data migration has run to convert legacy variant_ids:

```bash
python manage.py migrate orders 000X_migrate_variant_ids
```

### Issue: Deprecation warnings not appearing

**Solution**: Ensure Python warnings are enabled in Django settings:

```python
# settings.py
import warnings
warnings.simplefilter('default', DeprecationWarning)
```

---

## Success Criteria

Implementation is successful when:

1. ✅ All 19 invariant tests pass
2. ✅ Public product listings only show approved products
3. ✅ Cart operations reject unapproved products
4. ✅ Order creation fails on unapproved products
5. ✅ variant_id always references ProductCategoryVariantOption
6. ✅ Stock operations only use ProductCategoryVariantOption.stock_count
7. ✅ Deprecation warnings logged for deprecated system access

---

## Next Steps

After verification:

1. Monitor production logs for deprecation warnings
2. Plan migration strategy for existing ProductVariant data
3. Schedule removal of deprecated systems in future release
4. Update API documentation to reflect approval requirements
