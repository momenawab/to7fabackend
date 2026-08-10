# Product Approval System API Documentation

## Overview

This document describes the Product Approval System implemented per **Spec 004 (Product & Inventory Consistency)** and **Spec 005 (Variant System Implementation)**.

### Key Principle

**Dual Approval Requirement**: For a product to be publicly visible, it must have **BOTH**:
- `is_active = True` (database field)
- `approval_status = 'approved'` (workflow field)

## Product Approval States

### Approval Status Values

| Status | Description | Public Visibility |
|--------|-------------|-------------------|
| `pending` | Awaiting admin review | No |
| `approved` | Approved for public listing | Yes (if `is_active=True`) |
| `rejected` | Rejected by admin | No |

### Visibility Matrix

| is_active | approval_status | Visible? | Reason |
|-----------|-----------------|----------|--------|
| `True` | `approved` | **YES** | Both conditions met |
| `True` | `pending` | No | Not approved |
| `True` | `rejected` | No | Explicitly rejected |
| `False` | `approved` | No | Inactive (even if approved) |
| `False` | `pending` | No | Inactive |
| `False` | `rejected` | No | Inactive |

## API Endpoints

### 1. Public Product Listing

**Endpoint**: `GET /api/products/`

**Behavior**: Returns only products with `is_active=True` AND `approval_status='approved'`

**Example Response**:
```json
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "name": "T-Shirt",
      "base_price": "50.00",
      "approval_status": "approved",
      "is_active": true
    }
  ]
}
```

### 2. Add to Cart

**Endpoint**: `POST /api/cart/add/`

**Request Body**:
```json
{
  "product_id": 123,
  "quantity": 2,
  "variant_id": 456
}
```

**Validation Rules**:
- Product must have `approval_status='approved'`
- If product is not approved, returns `400 Bad Request`

**Error Response** (Product Not Approved):
```json
{
  "error": "PRODUCT_NOT_APPROVED",
  "message": "Product must be approved before adding to cart",
  "details": {
    "product_id": 123,
    "approval_status": "pending"
  }
}
```

### 3. Create Order

**Endpoint**: `POST /api/orders/create/`

**Request Body**:
```json
{
  "items": [
    {
      "product_id": 123,
      "quantity": 2,
      "variant_id": 456
    }
  ]
}
```

**Validation Rules**:
- ALL products in order must have `approval_status='approved'`
- If any product is not approved, order creation **fails hard** with explicit error

**Error Response** (Unapproved Products) - Phase 2 fix: previously `ProductVisibilityError`
was swallowed by a generic `ValueError` handler in `orders/views.py` and this payload
never reached the client at all; it now does, using this project's standard error
envelope (`api_error`/`StandardResponse`) rather than the flat shape shown in an earlier
draft of this doc:
```json
{
  "success": false,
  "error": {
    "code": "PRODUCT_VISIBILITY_ERROR",
    "message": "Order contains 2 product(s) that are not approved.",
    "details": {
      "unapproved_products": [
        {
          "product_id": 123,
          "name": "T-Shirt",
          "approval_status": "pending"
        },
        {
          "product_id": 456,
          "name": "Jeans",
          "approval_status": "rejected"
        }
      ]
    }
  },
  "request_id": "..."
}
```

## Invariant Enforcement

The following invariants are enforced by the system:

### INV-010: Unapproved products not in public listings
Public product queries use `Product.objects.approved()` which filters for:
```python
Product.objects.filter(is_active=True, approval_status='approved')
```

### INV-011: Unapproved products cannot be added to cart
Cart add operations validate:
```python
if product.approval_status != 'approved':
    raise ProductNotApprovedError()
```

### INV-012: Unapproved products cannot be in orders
Order creation validates all products:
```python
for item in items_data:
    product = Product.objects.get(id=item['product_id'])
    if product.approval_status != 'approved':
        raise ProductVisibilityError(...)
```

### INV-013: (removed, Phase 2) - was self-contradictory
Product model validation previously rejected `approval_status='approved'` combined
with `is_active=False` at save time. This directly contradicted the Visibility Matrix
above, which documents that exact combination as a legitimate, reachable state
("Inactive (even if approved)") - e.g. a seller pausing an already-approved listing.
The check has been removed; visibility is enforced correctly at the query level via
`Product.objects.approved()`, which already requires both conditions together.

## Variant System (Spec 004 C.1, C.3)

### Canonical Variant System

**`ProductCategoryVariantOption`** is the **ONLY** variant system that owns stock.

| Feature | Status |
|---------|--------|
| ProductCategoryVariantOption | ✅ Canonical (use this) |
| ProductVariant | ⚠️ Deprecated (backward compatibility only) |
| combination_stocks | ❌ Deprecated (ignored) |

### Variant ID Reference

- `OrderItem.variant_id` references `ProductCategoryVariantOption.id`
- `CartItem.variant_id` references `ProductCategoryVariantOption.id`
- Stock restoration uses `variant_id` for precise stock management

### Variant Stock Invariants

| Invariant | Description |
|-----------|-------------|
| INV-001 | Stock only mutated via StockLockManager in atomic blocks |
| INV-002 | Stock checks AFTER select_for_update() lock |
| INV-003 | Cancelled order restores stock to exact variant |
| INV-004 | Stock never goes negative |
| INV-005 | Product.stock_quantity not used for variant products |
| INV-014 | Only ProductCategoryVariantOption can own stock |
| INV-016 | combination_stocks not used for stock |

## Database Indexes

The following indexes optimize approval and variant queries:

```python
# Product approval index (T057)
Index(fields=['is_active', 'approval_status'])

# Variant option index (T058)
Index(fields=['product', 'is_active'])

# OrderItem variant_id index (T056)
Index(fields=['variant_id'])
```

## Deprecation Warnings

The following systems emit `DeprecationWarning` when accessed:

1. **ProductVariant model**: Use `ProductCategoryVariantOption` instead
2. **ProductVariant.stock_count**: Use `ProductCategoryVariantOption.stock_count`
3. **ProductVariant.is_in_stock**: Use `ProductCategoryVariantOption.is_in_stock`
4. **Product.combination_stocks**: Field is write-protected and ignored
5. **CartItem.selected_variants**: Use `variant_id` for inventory operations

## Testing

Run invariant tests to verify compliance:

```bash
# Products invariants (INV-010 through INV-016)
pytest products/tests/test_invariants.py -v

# Orders invariants (INV-001 through INV-009)
pytest orders/tests/test_invariants.py -v

# Cart invariants (INV-017 through INV-019)
pytest cart/tests/test_invariants.py -v
```

## Migration Notes

### Legacy Orders

Orders created before Spec 005 may have `variant_id` values that reference the old `ProductVariant` model. A data migration is required to map these to `ProductCategoryVariantOption.id` values.

### Data Migration Template

```python
def migrate_variant_ids(apps, schema_editor):
    OrderItem = apps.get_model('orders', 'OrderItem')
    ProductVariant = apps.get_model('products', 'ProductVariant')
    ProductCategoryVariantOption = apps.get_model('products', 'ProductCategoryVariantOption')

    for item in OrderItem.objects.filter(variant_id__isnull=False):
        # Map old ProductVariant.id to new ProductCategoryVariantOption.id
        # This requires business logic to determine correct mapping
        pass
```

## Admin Workflow

### Product Approval Process

1. Seller creates product → `approval_status='pending'`
2. Admin reviews product
3. Admin approves → `approval_status='approved'`
4. Product becomes visible (if `is_active=True`)

### Admin Actions

```python
# Approve product
product.approval_status = 'approved'
product.is_active = True
product.save()

# Reject product
product.approval_status = 'rejected'
product.save()

# Deactivate approved product
product.is_active = False
product.save()  # Still approved, but not visible
```

## References

- **Spec 004**: Product & Inventory Consistency Analysis
- **Spec 005**: Variant System Implementation
- **Invariant Tests**: `products/tests/test_invariants.py`, `orders/tests/test_invariants.py`, `cart/tests/test_invariants.py`
