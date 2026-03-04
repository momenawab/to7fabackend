# Research: Variant System Implementation

**Feature**: Spec 005 - Variant System Implementation
**Status**: COMPLETE - All decisions from Spec 004 are binding
**Date**: 2025-02-09

## Overview

This is an **implementation specification** that applies binding architectural decisions from Spec 004 (Product & Inventory Consistency Analysis). Since Spec 004 already made all binding architectural decisions, this research document consolidates those decisions for implementation reference.

---

## Resolved Decisions from Spec 004

### Decision 1: Canonical Variant System

**Source**: Spec 004, Section C.1

**Decision**: `ProductCategoryVariantOption` is the ONE canonical variant system.

**Implementation Implications**:
- `ProductVariant` model is DEPRECATED
- `combination_stocks` JSONField is TO BE REMOVED
- All new code must use `ProductCategoryVariantOption` for variant operations
- Fallback logic to `ProductVariant` should log deprecation warnings

**Rationale**: The system contains three parallel variant systems, causing ambiguity and potential inconsistencies. `ProductCategoryVariantOption` was identified as the primary system in use.

**Alternatives Considered**:
- Keep `ProductVariant` as primary - Rejected because `ProductCategoryVariantOption` is already in primary use
- Create entirely new variant system - Rejected due to unnecessary complexity and migration cost

---

### Decision 2: Stock Ownership

**Source**: Spec 004, Section C.2

**Decision**: `ProductCategoryVariantOption.stock_count` is the ONE canonical stock field for variants.

**Implementation Implications**:
- For variant products: use only `ProductCategoryVariantOption.stock_count`
- For non-variant products: use `Product.stock_quantity`
- `ProductVariant.stock_count` is deprecated

**Stock Hierarchy**:
1. If product has variants → `ProductCategoryVariantOption.stock_count` (per variant)
2. If product has no variants → `Product.stock_quantity`

**Rationale**: Clear ownership prevents stock inconsistencies and eliminates ambiguity about which field to modify during stock operations.

---

### Decision 3: Variant Identification

**Source**: Spec 004, Section C.3

**Decision**: `variant_id` in OrderItem ALWAYS refers to `ProductCategoryVariantOption.id`.

**Implementation Implications**:
- `variant_id IS NULL` = non-variant product
- `variant_id IS NOT NULL` = `ProductCategoryVariantOption.id`
- Legacy orders with `ProductVariant` variant_ids will need migration
- New convention must be enforced in `OrderItem` creation

**Rationale**: The current try-catch fallback pattern creates risk of stock being released to the wrong variant if both systems have records with the same ID.

---

### Decision 4: Product Approval & Visibility

**Source**: Spec 004, Section C.4

**Decision**: Public visibility REQUIRES BOTH: `is_active=True` AND `approval_status='approved'`.

**Implementation Implications**:
- Create `Product.objects.approved()` QuerySet manager
- All public views must use this manager
- Cart operations must validate `approval_status='approved'`
- Order creation must hard-fail on unapproved products
- `approval_status='approved'` requires `is_active=True`

**Current Gap**: Most of the codebase only checks `is_active=True`, ignoring `approval_status`. Products with `approval_status='rejected'` remain publicly visible.

**Rationale**: The approval system exists but is inconsistently enforced. This creates a critical business risk where rejected products can be purchased.

---

### Decision 5: Stock Reservation Model

**Source**: Spec 004, Section C.5

**Decision**: Current immediate-decrement model is INTENTIONAL and FINAL.

**Implementation Implications**:
- NO changes to stock reservation model
- "Reservation" means immediate physical decrement in this system
- `reservation_status` tracks ORDER lifecycle, not STOCK lifecycle
- Only documentation clarifications needed

**Rationale**: The current system was intentionally designed as immediate-decrement, not soft reservation. The terminology is misleading but the behavior is correct.

---

### Decision 6: Cart Data Structure

**Source**: Spec 004, Section C.6

**Decision**: `variant_id` is the source of truth for cart items.

**Implementation Implications**:
- `variant_id` is canonical for stock lookups, price calculations, order creation
- `selected_variants` (JSONField) is DEPRECATED for display only
- Do not use `selected_variants` for inventory operations

**Rationale**: Having two sources of truth for variant selection in cart creates ambiguity and potential for data divergence.

---

## Technology Considerations

### Django ORM Patterns

**QuerySet Manager for Approval Enforcement**:

```python
# products/models.py
class ProductQuerySet(models.QuerySet):
    def approved(self):
        return self.filter(is_active=True, approval_status='approved')

class Product(models.Model):
    objects = ProductQuerySet.as_manager()
```

**select_for_update() for Stock Operations**:

All stock operations must use `select_for_update()` to prevent race conditions:
```python
variant = ProductCategoryVariantOption.objects.select_for_update().get(id=variant_id)
```

### Deprecation Warning Pattern

Use Python's `warnings` module for deprecation warnings:

```python
import warnings

def deprecated_stock_operation(self):
    warnings.warn(
        "ProductVariant.stock_count is deprecated. Use ProductCategoryVariantOption.stock_count",
        DeprecationWarning,
        stacklevel=2
    )
    # Fallback logic...
```

---

## Database Migration Strategy

### Phase 1: Add Constraints (Future)
- Add foreign key constraint for `OrderItem.variant_id` → `ProductCategoryVariantOption.id`
- This requires all existing variant_ids to be migrated first

### Phase 2: Data Migration (Future)
- Create mapping from `ProductVariant` records to `ProductCategoryVariantOption`
- Update `OrderItem.variant_id` references
- Back up data before migration

### Phase 3: Remove Deprecated Systems (Future)
- Remove `ProductVariant` model
- Remove `combination_stocks` field
- Remove `selected_variants` field

---

## Testing Strategy

### Invariant Tests

19 invariants from Spec 004 must be tested:

**Stock Invariants** (INV-001 through INV-005):
- INV-001: Stock only mutated via StockLockManager in atomic blocks
- INV-002: Stock checks after select_for_update() lock
- INV-003: Cancelled order restores stock to exact variant
- INV-004: Stock never goes negative
- INV-005: Product.stock_quantity not used for variant products

**Order Invariants** (INV-006 through INV-009):
- INV-006: OrderItem always has valid product.id
- INV-007: OrderItem.variant_id is NULL or valid ProductCategoryVariantOption.id
- INV-008: reservation_status transitions follow rules
- INV-009: Order with released item cannot transition to paid

**Visibility Invariants** (INV-010 through INV-013):
- INV-010: Unapproved products not in public listings
- INV-011: Unapproved products cannot be added to cart
- INV-012: Unapproved products cannot be in orders
- INV-013: approval requires is_active=True

**Variant System Invariants** (INV-014 through INV-016):
- INV-014: Only ProductCategoryVariantOption can own stock
- INV-015: New products use ProductCategoryVariantOption
- INV-016: combination_stocks not used for stock

**Cart Invariants** (INV-017 through INV-019):
- INV-017: CartItem.variant_id is valid ProductCategoryVariantOption or NULL
- INV-018: CartItem cannot reference inactive variant
- INV-019: CartItem cannot reference zero-stock variant

---

## Edge Cases and Considerations

### Edge Case 1: Approval Status Change During Cart Session
**Scenario**: User adds product to cart, then seller changes approval_status to 'rejected'

**Handling**: Cart should validate approval status on checkout, not on add. This allows users to keep cart items while giving seller control.

### Edge Case 2: Deleted ProductCategoryVariantOption
**Scenario**: Order references variant_id that no longer exists

**Handling**: Do not use CASCADE delete. Keep variant records for historical orders. Use `is_active=False` instead of deletion.

### Edge Case 3: Stock Release for Non-Existent variant_id
**Scenario**: Order cancelled, but variant_id references deleted variant

**Handling**: Transaction must fail gracefully. Log error and alert admin for manual intervention.

### Edge Case 4: Legacy Orders Before Migration
**Scenario**: Old orders have variant_ids from ProductVariant system

**Handling**: Migration must map all existing variant_ids before adding foreign key constraint.

### Edge Case 5: combination_stocks Data Conflicts
**Scenario**: combination_stocks has data that differs from ProductCategoryVariantOption.stock_count

**Handling**: Ignore combination_stocks entirely. No migration needed since field is read-only and has no write operations.

---

## Implementation Dependencies

### Required Specs
- **Spec 001**: Codex Critical Fixes (core system stability)
- **Spec 002**: Orders & Payments Stabilization (order system foundation)
- **Spec 004**: Product & Inventory Consistency Analysis (binding decisions)

### Database Dependencies
- PostgreSQL database with existing Django tables
- Existing Product, ProductCategoryVariantOption, ProductVariant, OrderItem, CartItem models

### External Dependencies
- Django 4.2.13
- Django REST Framework 3.16.0
- pytest-django 4.5.2

---

## Performance Considerations

### Query Optimization
- Single variant system eliminates try-catch fallback logic
- `approved()` manager can use database index on `(is_active, approval_status)`
- `select_for_update()` on stock operations prevents race conditions

### Indexing Requirements
- `OrderItem.variant_id`: Index for stock restoration lookups
- `Product(is_active, approval_status)`: Composite index for approved() manager
- `ProductCategoryVariantOption(product, is_active)`: Composite index for variant queries

---

## Open Questions

None. All architectural decisions were made in Spec 004 and are binding.

---

## Next Steps

1. ✅ Research complete - no open questions
2. ✅ Proceed to Phase 1: Design & Contracts
3. ✅ Generate data-model.md
4. ✅ Generate API contracts
5. ✅ Generate quickstart.md
6. ⏭️ Ready for `/speckit.tasks` command
