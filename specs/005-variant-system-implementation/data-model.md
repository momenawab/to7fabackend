# Data Model: Variant System Implementation

**Reference**: Spec 005 (Variant System Implementation)

## Entity: ProductCategoryVariantOption (Canonical Variant System)

**Purpose**: Junction table linking Products to CategoryVariantOptions with stock and price

**Fields**:

| Field | Type | Constraints | Notes |
|-------|------|------------|-------|
| `id` | Integer | Primary Key | Auto-generated |
| `product` | ForeignKey | NOT NULL | References Product(id), CASCADE delete |
| `category_variant_option` | ForeignKey | NOT NULL | References CategoryVariantOption(id), CASCADE delete |
| `stock_count` | PositiveInteger | >= 0 | CANONICAL stock field for variants per Spec 004 C.2 |
| `price_adjustment` | Decimal | >= 0 | Price adjustment from base price |
| `is_active` | Boolean | Default: true | Whether this variant is active |

**Relationships**:
- One Product can have many ProductCategoryVariantOption
- Many OrderItem can reference via variant_id (indirectly through ProductCategoryVariantOption.id)
- Referenced by StockLockManager for stock operations

**State Transitions**: None (active/inactive boolean only)

**Validation Rules**:
- stock_count cannot be negative (enforced by INV-004)
- stock_count can only be mutated via StockLockManager (enforced by INV-001)

---

## Entity: ProductVariant (Deprecated)

**Purpose**: Legacy variant system - DEPRECATED per Spec 004 C.1

**Status**: Marked deprecated with docstring warnings

**Fields**:

| Field | Type | Notes |
|-------|------|-------|
| `id` | Integer | Primary Key |
| `product` | ForeignKey | References Product(id) |
| `sku` | String | Auto-generated SKU |
| `stock_count` | PositiveInteger | DEPRECATED - use ProductCategoryVariantOption.stock_count |
| `price_adjustment` | Decimal | DEPRECATED - use ProductCategoryVariantOption.price_adjustment |
| `is_active` | Boolean | Whether this variant is active |

**Backward Compatibility**: Read-only access maintained for existing orders

**Migration Path**: Data will be migrated to ProductCategoryVariantOption

---

## Entity: OrderItem

**Purpose**: Links orders to products with variant tracking

**Fields**:

| Field | Type | Constraints | Notes |
|-------|------|------------|-------|
| `id` | Integer | Primary Key | Auto-generated |
| `order` | ForeignKey | NOT NULL | References Order(id), CASCADE delete |
| `product` | ForeignKey | NOT NULL | References Product(id), CASCADE delete |
| `variant_id` | PositiveInteger | nullable | CANONICAL reference to ProductCategoryVariantOption.id per Spec 004 C.3 |
| `quantity` | PositiveInteger | >= 1 | Quantity ordered |
| `seller` | ForeignKey | NOT NULL | References User(id), CASCADE delete |
| `reservation_status` | Char | enum | reserved/released/committed |
| `item_status` | Char | enum | pending/processing/shipped/delivered/completed/cancelled |

**Relationships**:
- Belongs to one Order
- References one Product
- Optionally references one ProductCategoryVariantOption (via variant_id)

**State Transitions** (per Spec 004 INV-008):
- reserved → committed (normal flow)
- reserved → released (cancel/refund flow)

**Validation Rules**:
- variant_id must be NULL or reference valid ProductCategoryVariantOption.id (INV-007)
- Cannot transition to paid/processing if reservation_status='released' (INV-009)

---

## Entity: CartItem

**Purpose**: Links cart to products with variant tracking

**Fields**:

| Field | Type | Constraints | Notes |
|-------|------|------------|-------|
| `id` | Integer | Primary Key | Auto-generated |
| `cart` | ForeignKey | NOT NULL | References Cart(id), CASCADE delete |
| `product` | ForeignKey | NOT NULL | References Product(id), CASCADE delete |
| `variant_id` | Integer | nullable | CANONICAL reference for inventory per Spec 004 C.6 |
| `selected_variants` | JSONField | nullable | DEPRECATED for display only per Spec 004 C.6 |
| `quantity` | PositiveInteger | >= 1 | Quantity in cart |

**Validation Rules**:
- variant_id must reference active ProductCategoryVariantOption (INV-018)
- variant_id must reference ProductCategoryVariantOption with stock_count > 0 (INV-019)
- selected_variants is ignored for inventory operations (deprecated)

---

## Entity: Product

**Purpose**: Core product entity with approval and visibility fields

**Fields**:

| Field | Type | Constraints | Notes |
|-------|------|------------|-------|
| `id` | Integer | Primary Key | Auto-generated |
| `name` | String | NOT NULL | Product name |
| `base_price` | Decimal | NOT NULL | Base price for product |
| `stock_quantity` | PositiveInteger | >= 0 | Stock for non-variant products only per Spec 004 C.2 |
| `approval_status` | Char | enum | pending/approved/rejected | Default: pending |
| `is_active` | Boolean | Default: true | Product visibility flag |
| `combination_stocks` | JSONField | default: {} | DEPRECATED - ignored per Spec 004 C.1 |

**QuerySet Managers**:
- `approved()`: Filters by is_active=True AND approval_status='approved'

**State Transitions**: None (status flags only)

**Validation Rules**:
- Public visibility requires is_active=True AND approval_status='approved' (INV-010)
- Setting approval_status='approved' requires is_active=True (INV-013)

---

## Entity: CategoryVariantOption

**Purpose**: Defines available options for each variant type

**Fields**:

| Field | Type | Constraints | Notes |
|-------|------|------------|-------|
| `id` | Integer | Primary Key | Auto-generated |
| `variant_type` | ForeignKey | NOT NULL | References CategoryVariantType(id) |
| `value` | String | NOT NULL | e.g., "Small", "Red", "64GB" |
| `extra_price` | Decimal | Default: 0 | Additional price for this option |
| `is_active` | Boolean | Default: true | Whether option is selectable |

**Relationships**:
- Many ProductCategoryVariantOption can reference this
- Referenced by ProductVariantOption via variant_options

---

## Relationships Diagram

```
Product (1) ───── (many) ───── ProductCategoryVariantOption
        │                             │
        │                             └── (many) ───── CategoryVariantOption
        │
        └──── (1) ───── OrderItem ───── (many) ───── Order

Cart (1) ───── (many) ───── CartItem
                                      │
                                      └── (references) ───── ProductCategoryVariantOption
```

## State Machines

### OrderItem Reservation Status (Spec 004 INV-008)

```
reserved ────────────────────────→ committed
    │                                │
    └──→ released (cancel/refund)
```

### Product Approval Status (Spec 004)

```
pending ──────→ approved ──────→ rejected
             │                    │
             │                    └── (cannot transition back)
```

## Indexes Required

- **orders_orderitem_variant_id**: Index on OrderItem.variant_id for order lookups during stock operations
- **products_product_approved**: Composite index on (is_active, approval_status) for efficient product filtering
- **products_productcategoryvariantoption_product_active**: Composite index on (product, is_active) for variant queries
