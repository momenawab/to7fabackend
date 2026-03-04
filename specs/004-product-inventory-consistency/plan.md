# Implementation Plan: Product & Inventory Consistency Analysis

**Branch**: `004-product-inventory-consistency` | **Date**: 2025-02-09 | **Spec**: [spec.md](./spec.md)
**Type**: Analysis & Decision Specification (No Implementation Phase)

## Summary

This is **Phase 3** of the product & inventory architecture work. This specification is **ANALYSIS + DECISION ONLY**. No code, no refactoring, no implementation will be produced from this plan. The output serves as a binding architectural contract for later implementation phases.

**Primary Goal**: Establish exactly ONE canonical source of truth for product stock and variants, with zero ambiguity, zero leakage, and predictable reservation/release behavior.

**Key Binding Decisions**:
1. **ProductCategoryVariantOption** is the ONE canonical variant system
2. **ProductVariant** is DEPRECATED (fallback maintained for backward compatibility)
3. **combination_stocks** is TO BE REMOVED
4. Public visibility requires BOTH `is_active=True` AND `approval_status='approved'`
5. Current immediate-decrement stock model is INTENTIONAL and FINAL
6. **variant_id** in OrderItem ALWAYS refers to ProductCategoryVariantOption.id

## Technical Context

**Language/Version**: Python 3.14.2
**Primary Dependencies**: Django 4.2.13, Django REST Framework 3.16.0, pytest-django 4.5.2
**Storage**: PostgreSQL (implied from Django usage)
**Testing**: pytest-django
**Target Platform**: Backend API server
**Project Type**: Django web application
**Performance Goals**:
- API endpoints: 200ms (p50), 500ms (p95) per constitution
- Database queries: <100ms per query
- N+1 query patterns prohibited

**Affected Models**:
- `products.Product`
- `products.ProductCategoryVariantOption`
- `products.ProductVariant` (deprecated)
- `orders.OrderItem`
- `cart.CartItem`

**Constraints**:
- Must maintain backward compatibility with existing orders using ProductVariant
- No migration strategy defined in this phase (deferred)
- No removal timeline defined (deferred)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Code Quality
- **Single Responsibility**: The binding decisions clarify ownership - ProductCategoryVariantOption owns stock/price for variants
- **File Size Limit**: No code changes in this phase (analysis only)
- **No Dead Code**: combination_stocks identified for removal; ProductVariant marked deprecated

### Principle II: Testing Standards
- **Invariants as Test Gates**: 19 invariants defined (INV-001 through INV-019) will become test gates in future implementation phases
- **Test Coverage**: No implementation = no new tests required in this phase

### Principle III: User Experience Consistency
- **Error Response Format**: Future cart/order operations will return validation errors for unapproved products
- **Visibility Enforcement**: Public queries will use consistent `Product.objects.approved()` manager

### Principle IV: Performance Requirements
- **Query Optimization**: Decisions enforce single variant system, reducing query complexity
- **N+1 Prevention**: Elimination of fallback logic removes potential N+1 patterns

**Status**: PASSED - No violations. This analysis phase strengthens adherence to all principles.

## Project Structure

### Documentation (this feature)

```text
specs/004-product-inventory-consistency/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # NOT REQUIRED - All decisions are final
├── data-model.md        # NOT REQUIRED - No implementation in this phase
├── quickstart.md        # NOT REQUIRED - No implementation in this phase
├── contracts/           # NOT REQUIRED - No API changes in this phase
├── checklists/          # Requirements checklist
│   └── requirements.md  # Quality validation checklist
└── tasks.md             # NOT CREATED - Implementation deferred to future phase
```

### Source Code (Affected Modules)

```text
products/
├── models.py            # Product, ProductCategoryVariantOption, ProductVariant (lines 70-119, 122-297, 578-628)
└── views.py             # Public product listing (line 29 - needs approval_status filter)

orders/
├── models.py            # OrderItem (lines 66-154)
└── atomic_order_system.py  # StockLockManager, AtomicOrderCreator (lines 147-1014)

cart/
├── models.py            # CartItem (variant_id, selected_variants fields)
└── services/            # Cart operations
```

**Structure Decision**: Existing Django app structure maintained. No new modules created in this analysis phase.

## Complexity Tracking

> **No violations to track** - This is an analysis phase that simplifies the architecture by deprecating duplicate systems.

| Simplification | Impact |
|----------------|--------|
| Single variant system (ProductCategoryVariantOption) | Removes fallback logic complexity |
| combination_stocks removal | Eliminates orphan code |
| variant_id canonical reference | Eliminates identification ambiguity |
| Explicit approval enforcement | Removes visibility inconsistency |

## Phase 0: Research & Analysis

**Status**: COMPLETE

The specification itself contains all research findings. No additional research.md is required because:

1. All binding decisions are final and unambiguous
2. Current system behavior is fully documented (Section A)
3. All conflicts are identified (Section B)
4. All invariants are defined (Section D)

### Resolved Decisions

| Decision | Rationale |
|----------|-----------|
| ProductCategoryVariantOption as canonical | Already primary in codebase; ProductVariant only used as fallback |
| ProductVariant deprecated | Redundant system causing ambiguity; no new features should use it |
| combination_stocks removed | Read-only orphan field with no write operations |
| Hard-fail on unapproved products | Prevents rejected products from being purchased |
| Immediate-decrement model | Current implementation is intentional; changing would require significant redesign |

## Phase 1: Design & Contracts

**Status**: NOT APPLICABLE

This phase does not produce design artifacts because no implementation occurs. The binding decisions in the specification serve as the design contract for future implementation phases.

### For Future Implementation Phases

When implementation begins, the following will be required:

1. **Data Model Changes**:
   - Remove `combination_stocks` field from Product
   - Create `Product.objects.approved()` QuerySet manager
   - Add deprecation warnings to ProductVariant

2. **API Contracts**:
   - Cart endpoints: Validate `approval_status='approved'`
   - Order creation: Hard-fail on unapproved products
   - Product listing: Use `approved()` manager

3. **Migration Strategy**:
   - Migrate existing ProductVariant data to ProductCategoryVariantOption
   - Update OrderItem.variant_id references

## Phase 2: Task Breakdown

**Status**: DEFERRED

Tasks will be generated in a future specification when implementation is ready to begin. Use `/speckit.tasks` on that future specification.

## Implementation Readiness

This specification is **READY FOR REVIEW** as a binding architectural contract. It provides:

1. **Section A**: Complete current behavior documentation
2. **Section B**: Six identified conflicts/ambiguities
3. **Section C**: Six binding decisions (final, no alternatives)
4. **Section D**: Nineteen testable invariants
5. **Section E**: Explicitly deferred items

### Next Steps

1. Review this specification for architectural approval
2. When implementation is approved, create a new feature specification that references these decisions
3. Use `/speckit.tasks` on the implementation specification to generate actionable tasks

## Invariant Summary

**19 Invariants Defined** (will become test gates):

- **Stock** (5): INV-001 through INV-005
- **Order** (4): INV-006 through INV-009
- **Visibility** (4): INV-010 through INV-013
- **Variant System** (3): INV-014 through INV-016
- **Cart** (3): INV-017 through INV-019

See [spec.md](./spec.md) Section D for complete invariant definitions.
