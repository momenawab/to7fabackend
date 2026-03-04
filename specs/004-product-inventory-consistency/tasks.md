---

description: "Task list for feature implementation"
---

# Tasks: Product & Inventory Consistency Analysis

**Input**: Design documents from `/specs/004-product-inventory-consistency/`
**Prerequisites**: plan.md, spec.md

**Status**: NO TASKS - ANALYSIS & DECISION SPECIFICATION

---

## ⚠️ IMPORTANT: No Implementation Tasks

This is **Phase 3** of the product & inventory architecture work - an **Analysis & Decision** specification.

**This specification does NOT include:**
- User stories
- Implementation tasks
- Database migrations
- Test requirements
- API changes

**This specification DOES include:**
- Complete current behavior documentation (Section A)
- Six identified conflicts/ambiguities (Section B)
- Six binding architectural decisions (Section C)
- Nineteen testable invariants (Section D)

---

## Purpose of This Specification

This specification serves as a **binding architectural contract** for future implementation phases.

### Binding Decisions

1. **ProductCategoryVariantOption** is the ONE canonical variant system
2. **ProductVariant** is DEPRECATED (fallback maintained for backward compatibility)
3. **combination_stocks** is TO BE REMOVED
4. Public visibility requires BOTH `is_active=True` AND `approval_status='approved'`
5. Current immediate-decrement stock model is INTENTIONAL and FINAL
6. **variant_id** in OrderItem ALWAYS refers to ProductCategoryVariantOption.id

### 19 Invariants (Future Test Gates)

- **Stock** (5): INV-001 through INV-005
- **Order** (4): INV-006 through INV-009
- **Visibility** (4): INV-010 through INV-013
- **Variant System** (3): INV-014 through INV-016
- **Cart** (3): INV-017 through INV-019

See [spec.md](./spec.md) Section D for complete invariant definitions.

---

## Next Steps

### When Implementation is Ready

1. Create a **new feature specification** for implementation
2. Reference the binding decisions from this specification (004)
3. Include user stories, requirements, and acceptance criteria
4. Run `/speckit.plan` on the new specification
5. Run `/speckit.tasks` on the new specification to generate actionable tasks

### Future Implementation Will Require

Based on the binding decisions in this specification, implementation will need:

1. **Data Model Changes**:
   - Remove `combination_stocks` field from Product model (`products/models.py:158`)
   - Create `Product.objects.approved()` QuerySet manager
   - Add deprecation warnings to ProductVariant (`products/models.py:578-628`)

2. **API Changes**:
   - Cart endpoints: Validate `approval_status='approved'` before adding items
   - Order creation: Hard-fail on unapproved products
   - Product listing: Use `approved()` manager in public views

3. **Migration Strategy**:
   - Migrate existing ProductVariant data to ProductCategoryVariantOption
   - Update OrderItem.variant_id references
   - Handle backward compatibility for existing orders

---

## Affected Files (For Future Reference)

| File | Lines | Purpose |
|------|-------|---------|
| `products/models.py` | 70-119 | ProductCategoryVariantOption (canonical) |
| `products/models.py` | 122-297 | Product model (approval_status, is_active) |
| `products/models.py` | 158 | combination_stocks (to be removed) |
| `products/models.py` | 578-628 | ProductVariant (deprecated) |
| `products/views.py` | 29 | Public product listing (needs approval filter) |
| `orders/models.py` | 66-154 | OrderItem (variant_id field) |
| `orders/atomic_order_system.py` | 147-338 | StockLockManager (stock operations) |
| `orders/atomic_order_system.py` | 646-1014 | AtomicOrderCreator (order creation) |
| `cart/models.py` | 125-126 | CartItem (variant_id, selected_variants) |

---

## Documentation References

- **Specification**: [spec.md](./spec.md)
- **Implementation Plan**: [plan.md](./plan.md)
- **Requirements Checklist**: [checklists/requirements.md](./checklists/requirements.md)

---

**Version**: 1.0.0 | **Date**: 2025-02-09 | **Status**: Architectural Contract
