# Implementation Plan: Variant System Implementation

**Branch**: `005-variant-system-implementation` | **Date**: 2025-02-09 | **Spec**: [spec.md](./spec.md)
**References**: Spec 004 (Product & Inventory Consistency Analysis) - BINDING

## Summary

This specification implements the binding architectural decisions from Spec 004 to fully stabilize product variants, inventory ownership, and stock reservation consistency. The primary goal is to enforce a single canonical source of truth for variant stock and eliminate ambiguity in stock operations.

**Key Binding Decisions from Spec 004**:
- C.1: ProductCategoryVariantOption is the ONE canonical variant system
- C.2: ProductCategoryVariantOption.stock_count is the ONE canonical stock field
- C.3: variant_id in OrderItem ALWAYS refers to ProductCategoryVariantOption.id
- C.4: Public visibility requires BOTH is_active=True AND approval_status='approved'
- C.5: Current immediate-decrement stock model is INTENTIONAL and FINAL
- C.6: variant_id is the source of truth for cart items

## Technical Context

**Language/Version**: Python 3.14.2
**Primary Dependencies**: Django 4.2.13, Django REST Framework 3.16.0, pytest-django 4.5.2
**Storage**: PostgreSQL
**Testing**: pytest-django
**Target Platform**: Backend API server
**Project Type**: Django web application

**Performance Goals**:
- API endpoints: 200ms (p50), 500ms (p95) per constitution
- Database queries: <100ms individually
- N+1 query patterns: PROHIBITED

**Affected Models**:
- `products.Product` (add approved() QuerySet manager)
- `products.ProductCategoryVariantOption` (canonical variant system)
- `products.ProductVariant` (deprecated - warnings only)
- `orders.OrderItem` (variant_id canonical reference)
- `cart.CartItem` (variant_id as source of truth, selected_variants deprecated)

**Constraints**:
- Must maintain backward compatibility with existing orders using ProductVariant
- Must not remove deprecated systems in this phase (deprecation only)
- All changes must comply with 19 invariants from Spec 004

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Code Quality
- **Single Responsibility**: Each task has one clear purpose (model changes, service changes, API changes, migrations, tests)
- **No Dead Code**: combination_stocks and ProductVariant marked deprecated for removal in future phase
- **Documentation**: Deprecation warnings will be added to guide future developers

### Principle II: Testing Standards
- **Test Coverage**: 19 invariant tests will be added (INV-001 through INV-019)
- **Test-First**: Invariant tests will verify compliance with Spec 004 decisions
- **Regression Tests**: Existing order/cart/stock tests must continue to pass

### Principle III: User Experience Consistency
- **Error Response Format**: Consistent validation errors for unapproved products
- **Status Codes**: 400 errors for rejected products in cart/order
- **Deprecation Policy**: Deprecated systems will log warnings for observability

### Principle IV: Performance Requirements
- **Query Optimization**: Single variant system eliminates N+1 patterns from fallback logic
- **Database Indexing**: New variant_id constraints will require indexes

**Status**: PASSED - No violations. This implementation strengthens adherence to all principles.

## Project Structure

### Documentation (this feature)

```text
specs/005-variant-system-implementation/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── product-visibility.yaml
└── checklists/
    └── requirements.md  # Quality validation checklist
```

### Source Code (affected modules only)

```text
products/
├── models.py            # Product model changes (approved() manager, deprecation warnings)
├── views.py             # Product listing (use approved() manager)
└── serializers.py       # Product serializer (deprecation notices)

orders/
├── models.py            # OrderItem (variant_id reference documentation)
└── atomic_order_system.py  # StockLockManager, AtomicOrderCreator (deprecation, validation)

cart/
├── models.py            # CartItem (selected_variants deprecation)
├── services/            # Cart operations (variant_id validation, deprecation)
└── api_views.py         # Cart endpoint (approval_status validation)

tests/
├── products/
│   └── test_invariants.py  # INV-010 through INV-016
├── orders/
│   └── test_invariants.py  # INV-001, INV-002, INV-003, INV-004, INV-006, INV-007, INV-008, INV-009
└── cart/
    └── test_invariants.py  # INV-017, INV-018, INV-019
```

**Structure Decision**: Existing Django app structure maintained. No new modules created.

## Complexity Tracking

> **No violations to track** - This implementation simplifies the architecture by enforcing canonical systems.

| Simplification | Impact |
|----------------|--------|
| Single variant system (ProductCategoryVariantOption) | Removes fallback logic complexity |
| combination_stocks ignored | Eliminates orphan code path |
| variant_id canonical reference | Eliminates identification ambiguity |
| Explicit approval enforcement | Removes visibility inconsistency |

## Phase 0: Research & Analysis

**Status**: COMPLETE - All decisions from Spec 004 are binding.

Since this specification implements binding architectural decisions from Spec 004, no research is required. All technical decisions have already been made.

### Resolved Decisions (from Spec 004)

| Decision | Source | Implementation Action |
|----------|--------|---------------------|
| ProductCategoryVariantOption is canonical | Spec 004 C.1 | Deprecate ProductVariant, ignore combination_stocks |
| ProductCategoryVariantOption.stock_count is canonical | Spec 004 C.2 | Use only this field for variant stock operations |
| variant_id references ProductCategoryVariantOption.id | Spec 004 C.3 | Enforce in OrderItem, migrate legacy data |
| Public visibility requires is_active=True AND approval_status='approved' | Spec 004 C.4 | Create approved() manager, validate in cart/order |
| Immediate-decrement model is FINAL | Spec 004 C.5 | No changes to stock operations, clarify documentation |
| variant_id is source of truth for cart | Spec 004 C.6 | Use variant_id, deprecate selected_variants |

## Phase 1: Design & Contracts

### data-model.md

**Entity: ProductCategoryVariantOption (Canonical Variant System)**

- **Purpose**: Junction table linking Products to CategoryVariantOptions with stock and price
- **Fields**:
  - `product` (ForeignKey) - Reference to Product
  - `category_variant_option` (ForeignKey) - Reference to CategoryVariantOption
  - `stock_count` (PositiveIntegerField) - CANONICAL stock field for variants
  - `price_adjustment` (DecimalField) - Price adjustment from base price
  - `is_active` (Boolean) - Whether this variant is active
- **Relationships**:
  - One Product can have many ProductCategoryVariantOption
  - Many OrderItem can reference via variant_id
- **Constraints**: Stock must never be negative

**Entity: ProductVariant (Deprecated)**

- **Purpose**: Legacy variant system - DEPRECATED per Spec 004 C.1
- **Status**: Marked deprecated with docstring warnings
- **Backward Compatibility**: Read-only access for existing orders
- **Migration Path**: Data will be migrated to ProductCategoryVariantOption

**Entity: OrderItem**

- **Purpose**: Links orders to products with variant tracking
- **Fields**:
  - `product` (ForeignKey) - Reference to Product
  - `variant_id` (PositiveIntegerField, nullable) - CANONICAL reference to ProductCategoryVariantOption.id
  - `quantity` (PositiveIntegerField) - Quantity ordered
  - `seller` (ForeignKey) - Seller at order time
  - `reservation_status` (CharField) - Order lifecycle tracking
- **Constraints**: variant_id must be NULL or reference valid ProductCategoryVariantOption

**Entity: CartItem**

- **Purpose**: Links cart to products with variant tracking
- **Fields**:
  - `product` (ForeignKey) - Reference to Product
  - `variant_id` (IntegerField, nullable) - CANONICAL reference for inventory
  - `selected_variants` (JSONField) - DEPRECATED for display only

### contracts/

**API Contract: Product Visibility**

```python
# GET /api/v1/products/
# Public product listing endpoint

# Response (success)
{
    "data": [
        {
            "id": 1,
            "name": "Product Name",
            "approval_status": "approved",
            "is_active": true
        }
    ],
    "pagination": {
        "page": 1,
        "page_size": 20,
        "total": 100
    }
}
```

**API Contract: Cart Add Item**

```python
# POST /api/v1/cart/items/
# Add item to cart

# Request
{
    "product_id": 123,
    "variant_id": 456,  # ProductCategoryVariantOption.id
    "quantity": 1
}

# Response (error - unapproved product)
{
    "error": "PRODUCT_NOT_APPROVED",
    "message": "Product must be approved before adding to cart",
    "details": {
        "product_id": 123,
        "approval_status": "pending"
    }
}
```

**API Contract: Order Creation**

```python
# POST /api/v1/orders/
# Create order with validation

# Response (error - unapproved product)
{
    "error": "PRODUCT_NOT_APPROVED",
    "message": "Order contains products that are not approved",
    "details": {
        "unapproved_products": [
            {"product_id": 123, "name": "Product Name", "approval_status": "rejected"}
        ]
    }
}
```

### quickstart.md

**Quick Start: Variant System Implementation**

This guide helps you verify the variant system implementation after deployment.

**1. Verify Canonical Variant System**

```bash
# Run invariant tests
pytest products/tests/test_invariants.py -k "INV_014 or INV_015 or INV_016"
```

**2. Verify Approval Enforcement**

```bash
# Test product visibility
curl -X GET http://localhost:8000/api/v1/products/
# Should only return products with approval_status='approved'

# Try adding unapproved product to cart
curl -X POST http://localhost:8000/api/v1/cart/items/ \
  -H "Content-Type: application/json" \
  -d '{"product_id": 123, "variant_id": 456, "quantity": 1}'
# Should return 400 error
```

**3. Verify Deprecation Warnings**

```bash
# Check logs for deprecation warnings when using old systems
tail -f logs/app.log | grep DEPRECATED
```

## Phase 2: Task Breakdown

**Status**: READY FOR /speckit.tasks

Tasks will be organized by user story priority:
- **Phase 3**: User Story 1 - Variant System Canonicalization (P1)
- **Phase 4**: User Story 2 - Variant Identification Consistency (P1)
- **Phase 5**: User Story 3 - Product Approval & Visibility Enforcement (P1)
- **Phase 6**: User Story 4 - Cart Data Structure Canonicalization (P2)
- **Phase 7**: User Story 5 - Deprecation & Cleanup Enforcement (P3)
- **Final Phase**: Polish & Invariant Tests

## Implementation Readiness

This specification is **READY FOR TASK GENERATION**:

1. All binding decisions from Spec 004 are carried forward
2. 5 user stories prioritized (3 P1, 1 P2, 1 P3)
3. 22 functional requirements with Spec 004 references
4. 21 implementation tasks defined with scopes
5. 19 invariant tests mapped from Spec 004
6. Data model changes documented
7. API contracts defined
8. Edge cases identified
9. Out-of-scope items explicitly deferred

## Next Steps

1. **Run `/speckit.tasks`** to generate actionable task breakdown
2. Review tasks.md for completeness
3. Begin implementation following Phase 3-7 order

## Invariant Summary

**19 Invariants from Spec 004 will be enforced**:

- **Stock** (5): INV-001 through INV-005
- **Order** (4): INV-006 through INV-009
- **Visibility** (4): INV-010 through INV-013
- **Variant System** (3): INV-014 through INV-016
- **Cart** (3): INV-017 through INV-019

See [spec.md](./spec.md) Section D for complete invariant definitions.
