# Feature Specification: Product & Inventory Consistency Analysis

**Feature Branch**: `004-product-inventory-consistency`
**Created**: 2025-02-09
**Status**: Draft
**Type**: Analysis & Decision Specification (No Implementation)

## Context

This is **Phase 3** of the product & inventory architecture work. Spec 001 and Spec 002 are complete and stable. This phase is **ANALYSIS + DECISION ONLY**. No code, no refactoring, no implementation will be produced from this specification. The output will serve as a binding contract for later implementation phases.

**Goal**: Ensure there is exactly ONE canonical source of truth for product stock and variants, with zero ambiguity, zero leakage, and predictable reservation/release behavior.

---

## Section A: Current Observed Behavior (Facts Only)

### A.1 Variant System Architecture

The system contains **THREE** parallel variant-related systems:

#### A.1.1 ProductCategoryVariantOption
- **Model**: `products.models.ProductCategoryVariantOption` (lines 70-119)
- **Purpose**: Junction table linking Products to CategoryVariantOptions
- **Stock Ownership**: `stock_count` field (PositiveIntegerField)
- **Price Ownership**: `price_adjustment` field + references `CategoryVariantOption.extra_price`
- **Relationships**:
  - `ForeignKey(Product)` via `related_name='selected_variants'`
  - `ForeignKey(CategoryVariantOption)`
- **Current Status**: PRIMARY variant system in use

#### A.1.2 ProductVariant
- **Model**: `products.models.ProductVariant` (lines 578-628)
- **Purpose**: Individual product variants with specific category variant combinations
- **Stock Ownership**: `stock_count` field (PositiveIntegerField)
- **Price Ownership**: `price_adjustment` field
- **Relationships**:
  - `ForeignKey(Product)` via `related_name='variants'`
  - Related to `CategoryVariantOption` through `ProductVariantOption` junction
- **Current Status**: FALLBACK variant system - used when `ProductCategoryVariantOption` lookup fails

#### A.1.3 combination_stocks
- **Location**: `Product.combination_stocks` (lines 158)
- **Type**: JSONField storing stock overrides like `{'29_27': 10}`
- **Purpose**: Stock quantities for specific variant combinations
- **Current Status**: READ-ONLY - takes precedence when populated, but has no write operations

### A.2 Stock Operations

#### A.2.1 Stock Decrement Locations

**Primary**: `orders/atomic_order_system.py:AtomicOrderCreator.create_order()`

1. **ProductCategoryVariantOption path** (lines 764-779):
   - Lock: `ProductCategoryVariantOption.objects.select_for_update().get()`
   - Check: `variant.stock_count < quantity`
   - Decrement: `variant.stock_count -= quantity`

2. **ProductVariant fallback path** (lines 785-800):
   - Lock: `ProductVariant.objects.select_for_update().get()`
   - Check: `variant.stock_count < quantity`
   - Decrement: `variant.stock_count -= quantity`

3. **Non-variant product path** (lines 807-823):
   - Lock: `Product.objects.select_for_update().get()`
   - Check: `product.stock_quantity < quantity`
   - Decrement: `product.stock_quantity -= quantity`

#### A.2.2 Stock Release Locations

**Primary**: `orders/atomic_order_system.py:StockLockManager.release_stock()` (lines 248-305)

1. **ProductCategoryVariantOption path** (lines 267-272):
   - `variant.stock_count += quantity`

2. **ProductVariant fallback path** (lines 279-285):
   - `variant.stock_count += quantity`

3. **Non-variant product path** (lines 296-298):
   - `product.stock_quantity += quantity`

**Called by**:
- `AtomicOrderCreator.cancel_order()` (line 932)
- `WalletOrderCoordinator.refund_payment()` (line 624)

#### A.2.3 Stock Reservation Model

**Critical Finding**: The system does NOT implement "soft" reservation. The term `reserve_stock` is misleading:
- Stock is **immediately decremented** on order creation
- `reservation_status` field on OrderItem tracks state, but stock is physically removed
- `StockLockManager.commit_stock()` only updates `reservation_status` to 'committed' - no quantity change

### A.3 OrderItem Structure

- **Model**: `orders.models.OrderItem` (lines 66-154)
- **Product Reference**: `ForeignKey(Product)` - always populated
- **Variant Reference**: `variant_id` (PositiveIntegerField, nullable) - stores the ID of whichever variant system was used
- **Seller Reference**: `seller` (ForeignKey) - copied at order time
- **Reservation Tracking**: `reservation_status` with choices: reserved/released/committed

**Stock Restoration Data Requirements**:
On cancel/refund, the system needs:
1. `product.id` - available
2. `variant_id` - available (null for non-variant products)
3. `quantity` - available

**No additional lookups required** - all data stored in OrderItem.

### A.4 Product Approval & Visibility System

#### A.4.1 Fields

- **Product.approval_status** (lines 143-148):
  - Choices: 'pending', 'approved', 'rejected'
  - Default: 'pending'

- **Product.is_active** (line 140):
  - Boolean
  - Default: True

- **Product.seller verification**:
  - Via `custom_auth.User.is_mobile_verified`

#### A.4.2 Visibility Enforcement Locations

**Public Product Listing** (`products/views.py:29`):
```python
products = Product.objects.filter(is_active=True)
```
- **Finds**: Only checks `is_active=True`
- **Missing**: No check for `approval_status='approved'`

**Admin Panel** (`admin_panel/api_views.py:220-223`):
- Can filter by `is_active` status
- No filtering by `approval_status`

**SubcategorySectionControl** (`products/models.py:771-775`):
- **Exception**: DOES check `approval_status='approved'`
- Only place in codebase where approval_status is used for visibility

**Critical Gap**: Products with `approval_status='rejected'` but `is_active=True` remain publicly visible.

### A.5 Cart to Order Boundary

#### A.5.1 Cart Models

- **CartItem.selected_variants**: JSONField - stores selected variants as key-value pairs
- **CartItem.variant_id**: IntegerField - stores specific variant ID

#### A.5.2 Order Creation Flow

`AtomicOrderCreator.create_order()` receives:
- `items_data`: List of dicts with `product_id`, `quantity`, `variant_id`

**Inventory checks at order creation**:
1. `select_for_update()` locks acquired BEFORE stock checks
2. Stock validation happens AFTER locks
3. Immediate decrement on validation
4. Transaction atomicity ensures rollback on failure

**No direct cart-to-order mapping** - data must be explicitly transferred.

---

## Section B: Identified Conflicts / Ambiguities

### B.1 Variant System Duplication

**Conflict**: Two parallel variant systems with overlapping purposes:
- `ProductCategoryVariantOption` - currently primary
- `ProductVariant` - fallback only

**Ambiguity**: Which system is canonical for:
- Stock ownership?
- Price calculation?
- Variant identification?

**Impact**:
- Complex fallback logic in stock operations
- Potential for stock inconsistencies if both systems reference same product
- Unclear which system should be used for new features

### B.2 Variant Identification Ambiguity

**Conflict**: `variant_id` field in OrderItem stores an ID, but doesn't indicate:
- Which variant system it belongs to
- Whether it's a ProductCategoryVariantOption ID or ProductVariant ID

**Resolution Method**: Try-catch fallback in stock operations tries one system, then the other.

**Risk**: If both systems have a record with the same ID for different products, stock could be released to the wrong variant.

### B.3 combination_stocks Orphan

**Conflict**: `combination_stocks` JSONField:
- Is READ during stock calculations (takes precedence)
- Has NO write operations in codebase
- Cannot be set through any API

**Status**: Dead code or incomplete feature.

### B.4 Visibility Enforcement Gap

**Conflict**: `approval_status` field exists but is inconsistently enforced:
- Most of codebase ignores it
- One location (`SubcategorySectionControl`) does enforce it
- No documented rule for when it should be checked

**Risk**: Rejected products may remain visible and purchasable.

### B.5 Stock Reservation Terminology

**Conflict**: Code uses "reservation" terminology but implements immediate decrement:
- Method named `reserve_stock()` but physically decrements
- `reservation_status='reserved'` suggests stock is held, but it's actually gone
- `commit_stock()` only updates a status flag, not stock

**Ambiguity**: Is this intentional design or incomplete implementation of true reservation?

### B.6 Cart to Order Data Transfer

**Ambiguity**: Cart has both `selected_variants` (JSON) and `variant_id` (int):
- Which is the source of truth?
- Can they diverge?
- What happens if they conflict?

---

## Section C: Binding Decisions

### C.1 Canonical Variant System

**DECISION**: **ProductCategoryVariantOption is the ONE canonical variant system.**

**ProductVariant Status**: **DEPRECATED**
- Mark as deprecated in code documentation
- Maintain fallback read operations for backward compatibility with existing orders
- No new features should use ProductVariant
- Plan for eventual migration of existing ProductVariant data to ProductCategoryVariantOption

**combination_stocks Status**: **TO BE REMOVED**
- Mark for removal in next breaking release
- No migration required - data is read-only and no write operations exist
- Stock for variant combinations will be calculated from individual ProductCategoryVariantOption records

### C.2 Stock Ownership

**DECISION**: **ProductCategoryVariantOption.stock_count is the ONE canonical stock field for variants.**

**Product.stock_quantity**: Canonical stock field for non-variant products only.

**Hierarchy**:
1. If product has variants: `ProductCategoryVariantOption.stock_count` (per variant)
2. If product has no variants: `Product.stock_quantity`

**ProductVariant.stock_count**: Deprecated - will be migrated away.

### C.3 Variant Identification

**DECISION**: **variant_id in OrderItem ALWAYS refers to ProductCategoryVariantOption.id.**

**For orders created with old ProductVariant system**:
- Existing orders with ProductVariant variant_ids will be handled via migration
- After migration, all variant_ids will reference ProductCategoryVariantOption

**New convention**:
- `variant_id IS NULL` = non-variant product
- `variant_id IS NOT NULL` = ProductCategoryVariantOption.id

### C.4 Product Approval & Visibility

**DECISION**: **Public visibility REQUIRES BOTH conditions:**

1. `Product.is_active = True`
2. `Product.approval_status = 'approved'`

**Enforcement Layer**: **Model Layer (QuerySet-level)**
- All public-facing queries MUST filter by both conditions
- Create a custom QuerySet manager with `Product.objects.approved()` that enforces this
- All public-facing views must use this manager

**Cart Operations**: MUST respect approval status
- Cannot add products with `approval_status != 'approved'` to cart
- API should return validation error if attempted

**Order Creation**: **HARD-FAIL on unapproved products**
- Order creation must validate `approval_status='approved'`
- Raise explicit error if any product in order is not approved
- Transaction will roll back, preventing order creation

### C.5 Stock Reservation Model

**DECISION**: **Current immediate-decrement model is INTENTIONAL and FINAL.**

**Clarification**:
- "Reservation" means "physical stock decrement" in this system
- This is NOT soft reservation
- `reservation_status` field tracks ORDER lifecycle, not STOCK lifecycle
- Stock is decremented when order moves to `pending_payment` or `cod_pending`

**No change to reservation model** - terminology will be clarified in documentation.

### C.6 Cart Data Structure

**DECISION**: **variant_id is the source of truth for cart items.**

**selected_variants (JSONField)**: **DEPRECATED**
- Keep for display/UI purposes only
- Do not use for inventory operations
- May be removed in future version

**variant_id**: Canonical reference for:
- Stock lookups
- Price calculations
- Order creation

---

## Section D: Invariants

### D.1 Stock Invariants

**INV-001**: Stock can only be mutated by `StockLockManager.reserve_stock()` or `StockLockManager.release_stock()` within `@transaction.atomic` blocks.

**INV-002**: Stock checks MUST occur AFTER acquiring `select_for_update()` locks.

**INV-003**: A cancelled order MUST restore stock to the EXACT same variant/product it was decremented from, using stored `variant_id` and `product.id`.

**INV-004**: Stock can NEVER be negative. Transaction must raise error before stock goes below zero.

**INV-005**: For variant products: `Product.stock_quantity` is NOT used for inventory. Only `ProductCategoryVariantOption.stock_count` is valid.

### D.2 Order Invariants

**INV-006**: OrderItem MUST always reference a valid `product.id`.

**INV-007**: OrderItem.variant_id MUST either be NULL (non-variant product) or reference an existing `ProductCategoryVariantOption.id`.

**INV-008**: OrderItem.reservation_status transitions MUST follow: `reserved` → `committed` OR `reserved` → `released`.

**INV-009**: An order with ANY item having `reservation_status='released'` CANNOT transition to `paid` or `processing`.

### D.3 Visibility Invariants

**INV-010**: A product with `approval_status != 'approved'` CANNOT appear in public product listings.

**INV-011**: A product with `approval_status != 'approved'` CANNOT be added to cart.

**INV-012**: A product with `approval_status != 'approved'` CANNOT be included in an order.

**INV-013**: Setting `Product.approval_status='approved'` REQUIRES `is_active=True`. Both must be true for visibility.

### D.4 Variant System Invariants

**INV-014**: `ProductCategoryVariantOption` is the ONLY variant system that can own stock.

**INV-015**: New product creation MUST use `ProductCategoryVariantOption` for variant configuration.

**INV-016**: `combination_stocks` JSONField MUST NOT be used for any stock operations.

### D.5 Cart Invariants

**INV-017**: CartItem.variant_id MUST reference a valid, active `ProductCategoryVariantOption` or be NULL.

**INV-018**: CartItem CANNOT reference a `ProductCategoryVariantOption` with `is_active=False`.

**INV-019**: CartItem CANNOT reference a `ProductCategoryVariantOption` with `stock_count=0`.

---

## Section E: Deferred Items (Out of Scope)

### E.1 Implementation

The following are explicitly OUT OF SCOPE for this specification:
- Any code changes to implement these decisions
- Database migrations
- Test creation
- API changes

### E.2 Future Considerations

These items are deferred to future specifications:
- Migration strategy for existing `ProductVariant` data to `ProductCategoryVariantOption`
- Removal timeline for deprecated `ProductVariant` model
- Removal timeline for `combination_stocks` field
- Performance optimization for variant stock queries
- Caching strategy for product visibility checks

### E.3 Out of Scope Systems

The following systems are NOT reviewed in this specification:
- AR (Augmented Reality) variant system
- Discount/promotion systems
- Shipping/calculation systems
- Commission calculation systems

---

## Appendices

### Appendix A: File Reference Summary

| File | Lines | Purpose |
|------|-------|---------|
| `products/models.py` | 70-119 | ProductCategoryVariantOption definition |
| `products/models.py` | 122-297 | Product model definition |
| `products/models.py` | 578-628 | ProductVariant definition (deprecated) |
| `orders/models.py` | 66-154 | OrderItem definition |
| `orders/atomic_order_system.py` | 147-338 | StockLockManager class |
| `orders/atomic_order_system.py` | 341-643 | WalletOrderCoordinator class |
| `orders/atomic_order_system.py` | 646-1014 | AtomicOrderCreator class |

### Appendix B: State Transition Reference

**Order Status Valid Transitions**:
- `pending_payment` → `paid`, `cancelled`, `failed`
- `cod_pending` → `processing`, `cancelled`
- `paid` → `processing`, `cancelled`, `refunded`
- `processing` → `shipped`, `cancelled`, `refunded`
- `shipped` → `delivered`, `refunded`
- `delivered` → `completed`, `refunded`
- Terminal states: `completed`, `cancelled`, `refunded`, `failed`

**OrderItem Reservation Status Transitions**:
- `reserved` → `committed` (normal flow)
- `reserved` → `released` (cancel/refund flow)

### Appendix C: Glossary

- **Canonical**: The single, authoritative source of truth for a piece of data
- **Stock Reservation**: In this system, immediate physical decrement of stock (not soft reservation)
- **Variant**: A specific configuration of a product (e.g., Size: Large, Color: Red)
- **ProductCategoryVariantOption**: Junction table linking products to their specific variant options with stock/price
- **ProductVariant**: DEPRECATED variant system, being phased out
