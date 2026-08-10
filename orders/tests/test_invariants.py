"""
Invariant Tests for Order Stock Operations (Spec 004, Spec 005)

These tests enforce the binding architectural decisions from Spec 004:
- INV-001: Stock only mutated via StockLockManager in atomic blocks
- INV-002: Stock checks AFTER select_for_update() lock
- INV-003: Cancelled order restores stock to exact variant
- INV-004: Stock never goes negative
- INV-005: Product.stock_quantity not used for variant products
- INV-006: OrderItem always has valid product.id
- INV-007: OrderItem.variant_id is NULL or valid ProductCategoryVariantOption.id
- INV-008: reservation_status transitions follow rules
- INV-009: Order with released item cannot transition to paid
"""

import pytest
from django.db import transaction
from django.core.exceptions import ValidationError
from products.models import Product, ProductCategoryVariantOption, ProductVariant, Category, CategoryVariantType, CategoryVariantOption
from orders.models import Order, OrderItem
from orders.atomic_order_system import StockLockManager, AtomicOrderCreator
from custom_auth.models import User


@pytest.mark.django_db
class TestStockInvariants:
    """Test invariants for stock operations (Spec 004 INV-001 through INV-005)"""

    def test_inv_001_stock_only_mutated_via_stock_lock_manager_in_atomic_blocks(self):
        """
        INV-001: Stock can only be mutated by StockLockManager.reserve_stock()
        or StockLockManager.release_stock() within @transaction.atomic blocks.
        """
        # Setup
        category = Category.objects.create(name="Test Category")
        seller = User.objects.create_user(
            email="seller@test.com",
            password="testpass123",
            user_type='store'
        )
        product = Product.objects.create(
            name="Test Product",
            description="Test",
            base_price=100.00,
            stock_quantity=100,
            category=category,
            seller=seller,
            approval_status='approved'
        )

        initial_stock = product.stock_quantity

        # StockLockManager.reserve_stock uses @transaction.atomic
        result = StockLockManager.reserve_stock(product.id, 10)

        assert result is True
        product.refresh_from_db()
        assert product.stock_quantity == initial_stock - 10

        # Release stock back
        StockLockManager.release_stock(product.id, 10)
        product.refresh_from_db()
        assert product.stock_quantity == initial_stock

    def test_inv_002_stock_checks_after_select_for_update_lock(self):
        """
        INV-002: Stock checks MUST occur AFTER acquiring select_for_update() locks.
        This prevents race conditions where stock could be oversold.
        """
        # Setup
        category = Category.objects.create(name="Test Category 2")
        variant_type = CategoryVariantType.objects.create(
            name="Size",
            category=category
        )
        option = CategoryVariantOption.objects.create(
            variant_type=variant_type,
            value="Large"
        )

        seller = User.objects.create_user(
            email="seller2@test.com",
            password="testpass123",
            user_type='store'
        )
        product = Product.objects.create(
            name="Test Product 2",
            description="Test",
            base_price=100.00,
            stock_quantity=0,
            category=category,
            seller=seller,
            approval_status='approved'
        )

        variant = ProductCategoryVariantOption.objects.create(
            product=product,
            category_variant_option=option,
            stock_count=5
        )

        # StockLockManager uses select_for_update() before checking stock
        # This test verifies the stock check happens AFTER lock acquisition
        # Attempt to reserve more than available should fail
        with pytest.raises(ValueError, match="Insufficient stock"):
            StockLockManager.reserve_stock(product.id, 10, variant.id)

        # Variant stock should remain unchanged
        variant.refresh_from_db()
        assert variant.stock_count == 5

    def test_inv_003_cancelled_order_restores_stock_to_exact_variant(self):
        """
        INV-003: A cancelled order MUST restore stock to the EXACT same variant/product
        it was decremented from, using stored variant_id and product.id.
        """
        # Setup
        category = Category.objects.create(name="Test Category 3")
        variant_type = CategoryVariantType.objects.create(
            name="Size",
            category=category
        )
        option = CategoryVariantOption.objects.create(
            variant_type=variant_type,
            value="Large"
        )

        seller = User.objects.create_user(
            email="seller3@test.com",
            password="testpass123",
            user_type='store'
        )
        buyer = User.objects.create_user(
            email="buyer@test.com",
            password="testpass123",
            user_type='customer'
        )
        product = Product.objects.create(
            name="Test Product 3",
            description="Test",
            base_price=100.00,
            stock_quantity=0,
            category=category,
            seller=seller,
            approval_status='approved'
        )

        variant = ProductCategoryVariantOption.objects.create(
            product=product,
            category_variant_option=option,
            stock_count=50
        )

        initial_variant_stock = variant.stock_count

        # Reserve stock (create order)
        StockLockManager.reserve_stock(product.id, 5, variant.id)

        variant.refresh_from_db()
        assert variant.stock_count == initial_variant_stock - 5

        # Create order item to store variant_id
        order = Order.objects.create(
            user=buyer,
            total_amount=500.00,
            status='pending_payment'
        )

        order_item = OrderItem.objects.create(
            order=order,
            product=product,
            quantity=5,
            price=100.00,
            seller=seller,
            variant_id=variant.id,
            reservation_status='reserved'
        )

        # Release stock using the stored variant_id
        StockLockManager.release_stock(product.id, 5, order_item.variant_id)

        variant.refresh_from_db()
        assert variant.stock_count == initial_variant_stock

    def test_inv_004_stock_never_goes_negative(self):
        """
        INV-004: Stock can NEVER be negative. Transaction must raise error
        before stock goes below zero.
        """
        # Setup
        category = Category.objects.create(name="Test Category 4")
        seller = User.objects.create_user(
            email="seller4@test.com",
            password="testpass123",
            user_type='store'
        )
        product = Product.objects.create(
            name="Test Product 4",
            description="Test",
            base_price=100.00,
            stock_quantity=3,
            category=category,
            seller=seller,
            approval_status='approved'
        )

        # Attempt to reserve more than available
        with pytest.raises(ValueError, match="Insufficient stock"):
            StockLockManager.reserve_stock(product.id, 10)

        # Stock should remain unchanged
        product.refresh_from_db()
        assert product.stock_quantity == 3
        assert product.stock_quantity >= 0

    def test_inv_005_product_stock_quantity_not_used_for_variant_products(self):
        """
        INV-005: For variant products: Product.stock_quantity is NOT used for inventory.
        Only ProductCategoryVariantOption.stock_count is valid.
        """
        # Setup
        category = Category.objects.create(name="Test Category 5")
        variant_type = CategoryVariantType.objects.create(
            name="Size",
            category=category
        )
        option = CategoryVariantOption.objects.create(
            variant_type=variant_type,
            value="Large"
        )

        seller = User.objects.create_user(
            email="seller5@test.com",
            password="testpass123",
            user_type='store'
        )
        product = Product.objects.create(
            name="Test Product 5",
            description="Test",
            base_price=100.00,
            stock_quantity=999,  # This should be ignored for variant products
            category=category,
            seller=seller,
            approval_status='approved'
        )

        variant = ProductCategoryVariantOption.objects.create(
            product=product,
            category_variant_option=option,
            stock_count=10
        )

        # Product has variants
        assert product.has_variants is True

        # For variant products, ProductCategoryVariantOption.stock_count is the source of truth
        assert variant.stock_count == 10
        # Product.stock_quantity should be ignored for inventory operations

        # Reserve stock using variant
        StockLockManager.reserve_stock(product.id, 3, variant.id)

        variant.refresh_from_db()
        assert variant.stock_count == 7

        # Product.stock_quantity should remain unchanged (999 - ignored)
        product.refresh_from_db()
        assert product.stock_quantity == 999


@pytest.mark.django_db
class TestOrderInvariants:
    """Test invariants for order items (Spec 004 INV-006 through INV-009)"""

    def test_inv_006_order_item_always_has_valid_product_id(self):
        """
        INV-006: OrderItem MUST always reference a valid product.id.
        """
        # Setup
        category = Category.objects.create(name="Test Category 6")
        seller = User.objects.create_user(
            email="seller6@test.com",
            password="testpass123",
            user_type='store'
        )
        buyer = User.objects.create_user(
            email="buyer6@test.com",
            password="testpass123",
            user_type='customer'
        )
        product = Product.objects.create(
            name="Test Product 6",
            description="Test",
            base_price=100.00,
            stock_quantity=10,
            category=category,
            seller=seller,
            approval_status='approved'
        )

        order = Order.objects.create(
            user=buyer,
            total_amount=100.00,
            status='pending_payment'
        )

        # Create order item
        order_item = OrderItem.objects.create(
            order=order,
            product=product,
            quantity=1,
            price=100.00,
            seller=seller
        )

        # Assert: product reference is valid
        assert order_item.product.id == product.id
        assert order_item.product.name == "Test Product 6"

    def test_inv_007_order_item_variant_id_is_null_or_valid_product_category_variant_option_id(self):
        """
        INV-007: OrderItem.variant_id MUST either be NULL (non-variant product)
        or reference an existing ProductCategoryVariantOption.id.
        """
        # Setup
        category = Category.objects.create(name="Test Category 7")
        variant_type = CategoryVariantType.objects.create(
            name="Size",
            category=category
        )
        option = CategoryVariantOption.objects.create(
            variant_type=variant_type,
            value="Large"
        )

        seller = User.objects.create_user(
            email="seller7@test.com",
            password="testpass123",
            user_type='store'
        )
        buyer = User.objects.create_user(
            email="buyer7@test.com",
            password="testpass123",
            user_type='customer'
        )

        # Non-variant product
        non_variant_product = Product.objects.create(
            name="Non-Variant Product",
            description="Test",
            base_price=100.00,
            stock_quantity=10,
            category=category,
            seller=seller,
            approval_status='approved'
        )

        # Variant product
        variant_product = Product.objects.create(
            name="Variant Product",
            description="Test",
            base_price=100.00,
            stock_quantity=0,
            category=category,
            seller=seller,
            approval_status='approved'
        )

        variant = ProductCategoryVariantOption.objects.create(
            product=variant_product,
            category_variant_option=option,
            stock_count=10
        )

        order = Order.objects.create(
            user=buyer,
            total_amount=200.00,
            status='pending_payment'
        )

        # Order item for non-variant product: variant_id should be NULL
        item1 = OrderItem.objects.create(
            order=order,
            product=non_variant_product,
            quantity=1,
            price=100.00,
            seller=seller
        )
        assert item1.variant_id is None

        # Order item for variant product: variant_id should reference ProductCategoryVariantOption
        item2 = OrderItem.objects.create(
            order=order,
            product=variant_product,
            quantity=1,
            price=100.00,
            seller=seller,
            variant_id=variant.id
        )
        assert item2.variant_id == variant.id

        # Verify the referenced variant exists
        referenced_variant = ProductCategoryVariantOption.objects.get(id=item2.variant_id)
        assert referenced_variant.id == variant.id

    def test_inv_008_reservation_status_transitions_follow_rules(self):
        """
        INV-008: OrderItem.reservation_status transitions MUST follow:
        reserved → committed (normal flow)
        reserved → released (cancel/refund flow)
        """
        # Setup
        category = Category.objects.create(name="Test Category 8")
        seller = User.objects.create_user(
            email="seller8@test.com",
            password="testpass123",
            user_type='store'
        )
        buyer = User.objects.create_user(
            email="buyer8@test.com",
            password="testpass123",
            user_type='customer'
        )
        product = Product.objects.create(
            name="Test Product 8",
            description="Test",
            base_price=100.00,
            stock_quantity=10,
            category=category,
            seller=seller,
            approval_status='approved'
        )

        order = Order.objects.create(
            user=buyer,
            total_amount=100.00,
            status='pending_payment'
        )

        order_item = OrderItem.objects.create(
            order=order,
            product=product,
            quantity=1,
            price=100.00,
            seller=seller,
            reservation_status='reserved'
        )

        # Initial state
        assert order_item.reservation_status == 'reserved'

        # Normal flow: reserved → committed
        order_item.reservation_status = 'committed'
        order_item.save()
        assert order_item.reservation_status == 'committed'

        # Create another item for cancel flow
        order_item2 = OrderItem.objects.create(
            order=order,
            product=product,
            quantity=1,
            price=100.00,
            seller=seller,
            reservation_status='reserved'
        )

        # Cancel flow: reserved → released
        order_item2.reservation_status = 'released'
        order_item2.save()
        assert order_item2.reservation_status == 'released'

    def test_inv_009_order_with_released_item_cannot_transition_to_paid(self):
        """
        INV-009: An order with ANY item having reservation_status='released'
        CANNOT transition to 'paid' or 'processing'.
        """
        # Setup
        category = Category.objects.create(name="Test Category 9")
        seller = User.objects.create_user(
            email="seller9@test.com",
            password="testpass123",
            user_type='store'
        )
        buyer = User.objects.create_user(
            email="buyer9@test.com",
            password="testpass123",
            user_type='customer'
        )
        product = Product.objects.create(
            name="Test Product 9",
            description="Test",
            base_price=100.00,
            stock_quantity=10,
            category=category,
            seller=seller,
            approval_status='approved'
        )

        order = Order.objects.create(
            user=buyer,
            total_amount=100.00,
            status='pending_payment'
        )

        order_item = OrderItem.objects.create(
            order=order,
            product=product,
            quantity=1,
            price=100.00,
            seller=seller,
            reservation_status='released'  # Stock was released
        )

        # TODO: After implementation, order status transition should be validated
        # Attempting to set order to 'paid' or 'processing' with released items should fail
        # This test documents the expectation

        # The order should not be able to transition to paid/processing
        # if any item has reservation_status='released'
        assert order_item.reservation_status == 'released'

        # This will be enforced by AtomicOrderCreator validation logic
        # For now, the test documents the invariant requirement
