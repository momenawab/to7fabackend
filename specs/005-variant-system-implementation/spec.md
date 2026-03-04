# Feature Specification: Variant System Implementation

**Feature Branch**: `005-variant-system-implementation`
**Created**: 2025-02-09
**Status**: Draft
**References**: Spec 004 (Product & Inventory Consistency Analysis) - BINDING

## Context

This specification implements the binding architectural decisions from **Spec 004: Product & Inventory Consistency Analysis**. All decisions from Spec 004 are FINAL and BINDING. This specification exists to APPLY those decisions, not to debate or modify them.

**Spec 004 Binding Decisions Reference**:
- C.1: ProductCategoryVariantOption is the ONE canonical variant system
- C.2: ProductCategoryVariantOption.stock_count is the ONE canonical stock field
- C.3: variant_id in OrderItem ALWAYS refers to ProductCategoryVariantOption.id
- C.4: Public visibility requires BOTH is_active=True AND approval_status='approved'
- C.5: Current immediate-decrement stock model is INTENTIONAL and FINAL
- C.6: variant_id is the source of truth for cart items

## Section A: User Stories & Acceptance Criteria

### User Story 1 - Variant System Canonicalization (Priority: P1)

As a system, I need to enforce that ProductCategoryVariantOption is the single source of truth for variant stock and pricing, eliminating ambiguity and preventing stock inconsistencies.

**Why this priority**: This is foundational - without a single canonical variant system, stock operations are unreliable and prone to race conditions. This directly impacts revenue and customer trust.

**Independent Test**: Can be fully tested by creating products with variants, verifying stock operations only use ProductCategoryVariantOption, and confirming ProductVariant fallback returns deprecation warnings.

**Acceptance Scenarios**:

1. **Given** a product with variants configured, **When** stock is decremented, **Then** ONLY ProductCategoryVariantOption.stock_count is modified
2. **Given** code attempts to use ProductVariant for stock operations, **When** the operation is executed, **Then** a deprecation warning is logged and the operation falls back to ProductCategoryVariantOption
3. **Given** a product with combination_stocks populated, **When** stock is queried, **Then** the field is ignored and only ProductCategoryVariantOption.stock_count is used

---

### User Story 2 - Variant Identification Consistency (Priority: P1)

As a system, I need OrderItem.variant_id to unambiguously reference ProductCategoryVariantOption so that stock restoration on cancel/refund always goes to the correct variant.

**Why this priority**: Without this, stock can be released to the wrong variant, causing inventory discrepancies and customer service issues.

**Independent Test**: Can be fully tested by creating orders with variants, cancelling/refunding them, and verifying stock is restored to the exact ProductCategoryVariantOption referenced by variant_id.

**Acceptance Scenarios**:

1. **Given** an order is created with variant_id, **When** the order is created, **Then** variant_id stores a ProductCategoryVariantOption.id
2. **Given** an order with variant_id is cancelled, **When** stock is restored, **Then** it goes to the ProductCategoryVariantOption matching variant_id
3. **Given** legacy orders exist with old variant_ids, **When** stock operations occur, **Then** the system handles them gracefully via migration or fallback

---

### User Story 3 - Product Approval & Visibility Enforcement (Priority: P1)

As a system, I need to enforce that only approved products are visible in public listings, can be added to cart, and can be included in orders.

**Why this priority**: This prevents rejected products from being purchased, which is a critical business requirement for platform quality control.

**Independent Test**: Can be fully tested by creating products with different approval_status values, verifying they only appear in public listings when approved, and confirming cart/order operations reject unapproved products.

**Acceptance Scenarios**:

1. **Given** a product with approval_status='pending', **When** public products are listed, **Then** the product is NOT included
2. **Given** a product with approval_status='rejected', **When** a user attempts to add it to cart, **Then** the API returns a validation error
3. **Given** an order contains a product with approval_status!='approved', **When** order creation is attempted, **Then** the transaction fails with an explicit error and stock is NOT decremented

---

### User Story 4 - Cart Data Structure Canonicalization (Priority: P2)

As a system, I need to enforce that variant_id is the source of truth for cart inventory operations, deprecating the selected_variants JSONField.

**Why this priority**: This simplifies cart-to-order data transfer and eliminates ambiguity about which variant field drives inventory operations.

**Independent Test**: Can be fully tested by adding items to cart with variant_id, verifying stock checks use variant_id, and confirming selected_variants is ignored for inventory.

**Acceptance Scenarios**:

1. **Given** a CartItem with variant_id, **When** stock is checked, **Then** ONLY variant_id is used (selected_variants is ignored)
2. **Given** a CartItem with only selected_variants populated, **When** operations occur, **Then** a deprecation warning is logged
3. **Given** cart is converted to order, **When** order items are created, **Then** they use variant_id from CartItem

---

### User Story 5 - Deprecation & Cleanup Enforcement (Priority: P3)

As a system, I need to mark deprecated systems (ProductVariant, combination_stocks, selected_variants) as read-only and prevent new code from using them.

**Why this priority**: This prevents future code from depending on deprecated systems, ensuring the technical debt doesn't grow.

**Independent Test**: Can be fully tested by attempting to use deprecated systems in new code paths and verifying appropriate warnings or errors are raised.

**Acceptance Scenarios**:

1. **Given** new code attempts to write to combination_stocks, **When** the operation is attempted, **Then** a deprecation warning is raised
2. **Given** new product creation attempts to use ProductVariant, **When** the operation occurs, **Then** a deprecation warning is logged
3. **Given** code tries to use selected_variants for inventory, **When** the operation runs, **Then** a deprecation warning is logged

---

### Edge Cases

- What happens when a product's approval_status changes from 'approved' to 'rejected' while items are in user's cart?
- How does system handle orders with variant_ids that reference deleted ProductCategoryVariantOptions?
- What happens when stock is released for a variant_id that no longer exists?
- How does system handle legacy orders with variant_ids from ProductVariant system before migration?
- What happens when combination_stocks contains data that conflicts with ProductCategoryVariantOption.stock_count?

## Section B: Requirements

### Functional Requirements

#### B.1 Variant System Requirements (Enforces Spec 004 INV-014, INV-015, INV-016)

- **FR-001**: System MUST use ProductCategoryVariantOption.stock_count as the ONLY stock field for variant products (Spec 004 C.2)
- **FR-002**: System MUST deprecate ProductVariant model with warnings and prevent new features from using it (Spec 004 C.1)
- **FR-003**: System MUST ignore combination_stocks JSONField for all stock operations (Spec 004 C.1)
- **FR-004**: System MUST remove combination_stocks field from Product model in a future breaking release (Spec 004 C.1)

#### B.2 Variant Identification Requirements (Enforces Spec 004 INV-006, INV-007)

- **FR-005**: OrderItem.variant_id MUST reference ProductCategoryVariantOption.id for all new orders (Spec 004 C.3)
- **FR-006**: System MUST support variant_id IS NULL for non-variant products (Spec 004 C.3)
- **FR-007**: System MUST migrate existing orders with ProductVariant variant_ids to ProductCategoryVariantOption (Spec 004 C.3)

#### B.3 Stock Operation Requirements (Enforces Spec 004 INV-001, INV-002, INV-003, INV-004)

- **FR-008**: Stock MUST only be mutated by StockLockManager within @transaction.atomic blocks (Spec 004 INV-001)
- **FR-009**: Stock checks MUST occur AFTER acquiring select_for_update() locks (Spec 004 INV-002)
- **FR-010**: Cancelled orders MUST restore stock to the EXACT variant/product using stored variant_id (Spec 004 INV-003)
- **FR-011**: Stock can NEVER be negative - transaction must raise error before going below zero (Spec 004 INV-004)

#### B.4 Product Approval & Visibility Requirements (Enforces Spec 004 INV-010, INV-011, INV-012, INV-013)

- **FR-012**: Product.objects QuerySet MUST have an approved() manager that filters by is_active=True AND approval_status='approved' (Spec 004 C.4)
- **FR-013**: All public-facing views MUST use the approved() manager for product queries (Spec 004 C.4)
- **FR-014**: Cart operations MUST validate approval_status='approved' before adding items (Spec 004 C.4)
- **FR-015**: Order creation MUST hard-fail with explicit error when products have approval_status!='approved' (Spec 004 C.4)

#### B.5 Cart Data Structure Requirements (Enforces Spec 004 INV-017, INV-018, INV-019)

- **FR-016**: CartItem.variant_id MUST be the source of truth for inventory operations (Spec 004 C.6)
- **FR-017**: CartItem.selected_variants JSONField MUST be deprecated and used for display only (Spec 004 C.6)
- **FR-018**: Cart operations MUST validate variant_id references active ProductCategoryVariantOption with stock_count>0 (Spec 004 INV-017, INV-018, INV-019)

#### B.6 Deprecation & Guardrail Requirements

- **FR-019**: System MUST log deprecation warnings when ProductVariant is accessed for stock operations
- **FR-020**: System MUST log deprecation warnings when combination_stocks is accessed
- **FR-021**: System MUST log deprecation warnings when selected_variants is used for inventory operations
- **FR-022**: System MUST raise ValueError when attempting to set combination_stocks

### Key Entities

- **ProductCategoryVariantOption**: Canonical variant system owning stock_count and price_adjustment
- **ProductVariant**: Deprecated variant system - maintains backward compatibility only
- **OrderItem**: Links orders to products with variant_id referencing ProductCategoryVariantOption
- **CartItem**: Links cart to products with variant_id (canonical) and selected_variants (deprecated)
- **Product**: Has is_active and approval_status fields - both must be true for visibility

## Section C: Implementation Tasks

### C.1 Model Layer Changes

| Task ID | Description | Scope | Acceptance Criteria |
|---------|-------------|-------|---------------------|
| **T001** | Add `approved()` QuerySet manager to Product model | products/models.py | Manager filters by is_active=True AND approval_status='approved' |
| **T002** | Add deprecation warning docstrings to ProductVariant model | products/models.py | Docstring clearly states "DEPRECATED: Use ProductCategoryVariantOption" |
| **T003** | Add deprecation warning to Product.stock property when variants exist | products/models.py | Logs warning when Product.stock is accessed on variant products |
| **T004** | Add deprecation warning to combination_stocks field access | products/models.py | Logs warning on read, raises error on write |
| **T005** | Update Product.stock property to ignore combination_stocks | products/models.py | Returns sum of ProductCategoryVariantOption.stock_count, never combination_stocks |

### C.2 Service Layer Changes

| Task ID | Description | Scope | Acceptance Criteria |
|---------|-------------|-------|---------------------|
| **T006** | Update StockLockManager to log deprecation when ProductVariant is accessed | orders/atomic_order_system.py | Logs warning with call stack when falling back to ProductVariant |
| **T007** | Remove ProductVariant fallback path from stock operations (after migration) | orders/atomic_order_system.py | Direct error if ProductVariant referenced without migration flag |
| **T008** | Add validation to AtomicOrderCreator for approval_status on all products | orders/atomic_order_system.py | Raises ValueError with product names if any product is not approved |
| **T009** | Add deprecation warning when selected_variants is used for inventory | cart/services | Logs warning when selected_variants is used instead of variant_id |
| **T010** | Update cart operations to validate variant_id references active variant | cart/services | Raises error if variant_id references inactive or zero-stock variant |

### C.3 API Layer Changes

| Task ID | Description | Scope | Acceptance Criteria |
|---------|-------------|-------|---------------------|
| **T011** | Update product listing views to use approved() manager | products/views.py | Public endpoints filter by is_active=True AND approval_status='approved' |
| **T012** | Add approval_status validation to cart add item endpoint | cart/api_views.py | Returns 400 error with message if product approval_status!='approved' |
| **T013** | Update Product serializer to include deprecation notices for variant fields | products/serializers.py | Documentation reflects canonical system |

### C.4 Migration Tasks

| Task ID | Description | Scope | Acceptance Criteria |
|---------|-------------|-------|---------------------|
| **T014** | Create data migration to map ProductVariant to ProductCategoryVariantOption | products/migrations/XXXX_variant_mapping.py | Creates mapping table for existing ProductVariant data |
| **T015** | Migrate OrderItem.variant_ids from ProductVariant to ProductCategoryVariantOption | orders/migrations/XXXX_migrate_variant_ids.py | Updates variant_id references for existing orders |
| **T016** | Add database constraint to ensure variant_id references valid ProductCategoryVariantOption | orders/migrations/XXXX_variant_constraint.py | Foreign key constraint added after migration complete |

### C.5 Cleanup & Guardrail Tasks

| Task ID | Description | Scope | Acceptance Criteria |
|---------|-------------|-------|---------------------|
| **T017** | Add invariant tests for stock operations | orders/tests/test_invariants.py | Tests verify INV-001 through INV-005 |
| **T018** | Add invariant tests for order operations | orders/tests/test_invariants.py | Tests verify INV-006 through INV-009 |
| **T019** | Add invariant tests for visibility enforcement | products/tests/test_invariants.py | Tests verify INV-010 through INV-013 |
| **T020** | Add invariant tests for variant system | products/tests/test_invariants.py | Tests verify INV-014 through INV-016 |
| **T021** | Add invariant tests for cart operations | cart/tests/test_invariants.py | Tests verify INV-017 through INV-019 |

## Section D: Test Requirements

### D.1 Must-Test Scenarios

The following scenarios MUST have automated tests:

1. **Stock Canonicalization**: Verify stock operations only use ProductCategoryVariantOption.stock_count
2. **Variant Identification**: Verify OrderItem.variant_id always references ProductCategoryVariantOption.id
3. **Approval Enforcement**: Verify products with approval_status!='approved' are excluded from listings
4. **Cart Validation**: Verify unapproved products cannot be added to cart
5. **Order Validation**: Verify orders with unapproved products hard-fail
6. **Stock Restoration**: Verify cancelled orders restore stock to correct variant
7. **Deprecation Warnings**: Verify deprecated system access logs warnings
8. **Migration Integrity**: Verify legacy orders work after variant_id migration

### D.2 Invariant Enforcement

The following invariants from Spec 004 MUST be enforced by tests:

| Invariant | Test Requirement |
|-----------|-----------------|
| **INV-001** | Test verifies stock only mutated via StockLockManager in atomic blocks |
| **INV-002** | Test verifies stock checks after select_for_update() lock |
| **INV-003** | Test verifies cancelled order restores stock to exact variant |
| **INV-004** | Test verifies stock never goes negative (raises error) |
| **INV-005** | Test verifies Product.stock_quantity not used for variant products |
| **INV-006** | Test verifies OrderItem always has valid product.id |
| **INV-007** | Test verifies OrderItem.variant_id is NULL or valid ProductCategoryVariantOption.id |
| **INV-008** | Test verifies reservation_status transitions follow rules |
| **INV-009** | Test verifies order with released item cannot transition to paid |
| **INV-010** | Test verifies unapproved products not in public listings |
| **INV-011** | Test verifies unapproved products cannot be added to cart |
| **INV-012** | Test verifies unapproved products cannot be in orders |
| **INV-013** | Test verifies approval requires is_active=True |
| **INV-014** | Test verifies only ProductCategoryVariantOption owns stock |
| **INV-015** | Test verifies new products use ProductCategoryVariantOption |
| **INV-016** | Test verifies combination_stocks not used for stock |
| **INV-017** | Test verifies CartItem.variant_id is valid ProductCategoryVariantOption or NULL |
| **INV-018** | Test verifies CartItem cannot reference inactive variant |
| **INV-019** | Test verifies CartItem cannot reference zero-stock variant |

### D.3 Regression Tests

The following existing test scenarios should continue to pass:

1. Order creation with variants
2. Stock decrement on order placement
3. Stock release on order cancellation
4. Stock release on order refund
5. Cart item creation and management
6. Product listing and filtering

## Section E: Out of Scope

### E.1 Out of Scope (Deferred)

The following items are explicitly OUT OF SCOPE for this specification:

1. **Removal of ProductVariant model** - Only deprecation, not removal
2. **Removal of combination_stocks field** - Only ignored/deprecated, not removed
3. **Removal of selected_variants JSONField** - Only deprecated, not removed
4. **Performance optimization for variant queries** - Defer to future spec
5. **Caching strategy for product visibility** - Defer to future spec
6. **AR variant system changes** - Out of scope per Spec 004

### E.2 Spec 004 Compliance

This specification MUST NOT:

1. Change any binding decision from Spec 004
2. Introduce new variant systems
3. Modify the invariant list from Spec 004
4. Change the stock reservation model (immediate-decrement is FINAL per Spec 004 C.5)

## Dependencies

- **Spec 004**: Product & Inventory Consistency Analysis (binding architectural decisions)
- **Spec 002**: Orders & Payments Stabilization (order system foundation)
- **Spec 001**: Codex Critical Fixes (core system stability)
