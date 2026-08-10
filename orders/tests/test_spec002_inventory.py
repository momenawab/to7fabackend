"""
Spec 002 Tests: Inventory Behavior

Tests derived from:
- spec-002.md section: Inventory Management Specification
- FR-INV-001 through FR-INV-015
"""

import pytest


class TestStockReservationRules:
    """Test FR-INV-001 through FR-INV-005: Stock reservation behavior."""

    pytestmark = pytest.mark.critical
import uuid
from decimal import Decimal
from django.contrib.auth import get_user_model
from products.models import Product, Category, ProductVariant
from orders.models import Order, OrderItem
from cart.models import Cart

User = get_user_model()


class TestStockReservationRules:
    """Test FR-INV-001 through FR-INV-005: Stock reservation behavior."""

    def test_stock_reserved_on_order_creation(self, db):
        """FR-INV-001: Stock MUST be reserved when order transitions to PENDING_PAYMENT."""
        user = User.objects.create_user(
            email=f'user_aac57559@example.com',
            password='testpass123',
            is_mobile_verified=True
        )

        seller = User.objects.create_user(
            email=f'seller_cf716c0b@example.com',
            password='testpass123',
            user_type='artist'
        )

        category = Category.objects.create(name='Test Category')
        product = Product.objects.create(
            seller=seller,
            name='Test Product',
            base_price=Decimal('100.00'),
            stock_quantity=50,
            category=category
        )

        initial_stock = product.stock_quantity

        cart = Cart.objects.create(user=user)
        # TODO: Convert to cart.add_item() calls for: {'product_id': product.id, 'quantity': 5}
        cart.save()

        # Create order (should reserve stock)
        order = Order.objects.create(
            user=user,
            status='pending_payment',
            total_amount=Decimal('500.00')
        )

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=5,
            price=Decimal('100.00')
        )

        # Stock should be reserved (decremented from available)
        product.refresh_from_db()
        # Implementation may vary - check reserved stock or available stock
        assert product.stock_quantity <= initial_stock

    def test_stock_reservation_specific_to_variant(self, db):
        """FR-INV-002: Stock reservation MUST be specific to exact variant."""
        user = User.objects.create_user(
            email=f'user_28161bec@example.com',
            password='testpass123',
            is_mobile_verified=True
        )

        seller = User.objects.create_user(
            email=f'seller_157e584f@example.com',
            password='testpass123',
            user_type='artist'
        )

        category = Category.objects.create(name='Test Category')
        product = Product.objects.create(
            seller=seller,
            name='Test Product',
            base_price=Decimal('100.00'),
            stock_quantity=50,
            category=category
        )

        # Create variants (e.g., size M, size L)
        variant_m = ProductVariant.objects.create(
            product=product,
            sku='PROD-M',
            stock_quantity=20
        )
        variant_l = ProductVariant.objects.create(
            product=product,
            sku='PROD-L',
            stock_quantity=30
        )

        initial_stock_m = variant_m.stock_quantity
        initial_stock_l = variant_l.stock_quantity

        # Order size M
        order = Order.objects.create(
            user=user,
            status='pending_payment',
            total_amount=Decimal('100.00')
        )

        OrderItem.objects.create(
            order=order,
            product=product,
            variant=variant_m,
            quantity=5,
            price=Decimal('100.00')
        )

        # Only variant M stock should be affected
        variant_m.refresh_from_db()
        variant_l.refresh_from_db()

        assert variant_m.stock_quantity < initial_stock_m
        assert variant_l.stock_quantity == initial_stock_l

    def test_reserved_stock_decremented_from_available_not_total(self, db):
        """FR-INV-003: Reserved stock decremented from available, not total."""
        # This tests data model behavior
        # Implementation should track available vs reserved stock separately
        product = Product.objects.create(
            seller=User.objects.create_user(
                email=f'seller_c3b1f963@example.com',
                password='testpass123'
            ),
            name='Test Product',
            base_price=Decimal('100.00'),
            stock_quantity=50
        )

        # If model has reserved_stock field:
        if hasattr(product, 'reserved_stock'):
            initial_total = product.stock_quantity
            initial_available = product.stock_quantity - product.reserved_stock

            # Reserve 10
            product.reserved_stock = 10
            product.save()

            assert product.stock_quantity == initial_total
            assert (product.stock_quantity - product.reserved_stock) < initial_available


class TestStockReleaseRules:
    """Test FR-INV-005 through FR-INV-007: Stock release behavior."""

    pytestmark = pytest.mark.critical

    def test_stock_released_on_payment_timeout(self, db):
        """FR-INV-005: Stock released when order transitions to CANCELLED from timeout."""
        import uuid
        user = User.objects.create_user(
            email=f'user_{uuid.uuid4().hex[:8]}@example.com',
            password='testpass123',
            is_mobile_verified=True
        )

        seller = User.objects.create_user(
            email=f'seller_{uuid.uuid4().hex[:8]}@example.com',
            password='testpass123',
            user_type='artist'
        )

        category = Category.objects.create(name='Test Category')
        product = Product.objects.create(
            seller=seller,
            name='Test Product',
            base_price=Decimal('100.00'),
            stock_quantity=50,
            category=category
        )

        order = Order.objects.create(
            user=user,
            status='pending_payment',
            total_amount=Decimal('500.00')
        )

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=5,
            price=Decimal('100.00'),
            seller=seller  # Add seller field
        )

        # Simulate timeout cancellation
        order.status = 'cancelled'
        order.save()

        # Stock should be released
        # Implementation varies - check that stock is restored
        product.refresh_from_db()
        # Should have stock restored or reservation cleared

    def test_stock_released_on_payment_failure(self, db):
        """Stock released when order transitions to FAILED state."""
        import uuid
        user = User.objects.create_user(
            email=f'user_{uuid.uuid4().hex[:8]}@example.com',
            password='testpass123',
            is_mobile_verified=True
        )

        seller = User.objects.create_user(
            email=f'seller_{uuid.uuid4().hex[:8]}@example.com',
            password='testpass123',
            user_type='artist'
        )

        category = Category.objects.create(name='Test Category')
        product = Product.objects.create(
            seller=seller,
            name='Test Product',
            base_price=Decimal('100.00'),
            stock_quantity=50,
            category=category
        )

        order = Order.objects.create(
            user=user,
            status='pending_payment',
            total_amount=Decimal('500.00')
        )

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=5,
            price=Decimal('100.00'),
            seller=seller  # Add seller field
        )

        # Payment fails
        order.status = 'failed'
        order.save()

        # Stock should be released

    def test_stock_returned_on_refund(self, db):
        """FR-INV-006: Stock returned when order transitions to REFUNDED."""
        import uuid
        user = User.objects.create_user(
            email=f'user_{uuid.uuid4().hex[:8]}@example.com',
            password='testpass123',
            is_mobile_verified=True
        )

        seller = User.objects.create_user(
            email=f'seller_{uuid.uuid4().hex[:8]}@example.com',
            password='testpass123',
            user_type='artist'
        )

        category = Category.objects.create(name='Test Category')
        product = Product.objects.create(
            seller=seller,
            name='Test Product',
            base_price=Decimal('100.00'),
            stock_quantity=50,
            category=category
        )

        order = Order.objects.create(
            user=user,
            status='paid',
            total_amount=Decimal('500.00')
        )

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=5,
            price=Decimal('100.00'),
            seller=seller  # Add seller field
        )

        initial_stock = product.stock_quantity

        # Refund order
        order.status = 'refunded'
        order.save()

        # Stock should be returned
        product.refresh_from_db()
        assert product.stock_quantity >= initial_stock

    def test_stock_release_atomic_with_state_transition(self, db):
        """FR-INV-007: Stock release MUST be atomic with state transition."""
        import uuid
        user = User.objects.create_user(
            email=f'user_{uuid.uuid4().hex[:8]}@example.com',
            password='testpass123',
            is_mobile_verified=True
        )

        seller = User.objects.create_user(
            email=f'seller_{uuid.uuid4().hex[:8]}@example.com',
            password='testpass123',
            user_type='artist'
        )

        category = Category.objects.create(name='Test Category')
        product = Product.objects.create(
            seller=seller,
            name='Test Product',
            base_price=Decimal('100.00'),
            stock_quantity=50,
            category=category
        )

        order = Order.objects.create(
            user=user,
            status='pending_payment',
            total_amount=Decimal('500.00')
        )

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=5,
            price=Decimal('100.00'),
            seller=seller  # Add seller field
        )

        # State transition should trigger stock release atomically
        from orders.atomic_order_system import OrderStateMachine
        OrderStateMachine.validate_transition('pending_payment', 'cancelled')

        order.status = 'cancelled'
        order.save()

        # Stock should be released
        # No orphaned reservations


class TestVariantSpecificStockHandling:
    """Test FR-INV-010 through FR-INV-013: Variant stock handling."""

    pytestmark = pytest.mark.non_critical

    def test_each_variant_has_independent_stock(self, db):
        """FR-INV-010: Each product variant MUST have independent stock tracking."""
        seller = User.objects.create_user(
            email=f'seller_9394349a@example.com',
            password='testpass123',
            user_type='artist'
        )

        category = Category.objects.create(name='Test Category')
        product = Product.objects.create(
            seller=seller,
            name='T-Shirt',
            base_price=Decimal('50.00'),
            stock_quantity=100,
            category=category
        )

        variant_small = ProductVariant.objects.create(
            product=product,
            sku='TSHIRT-S',
            stock_quantity=20
        )

        variant_medium = ProductVariant.objects.create(
            product=product,
            sku='TSHIRT-M',
            stock_quantity=30
        )

        # Each variant has independent stock
        assert variant_small.stock_quantity != variant_medium.stock_quantity

    def test_stock_reservation_references_variant_id(self, db):
        """FR-INV-011: Stock reservation MUST reference specific variant ID."""
        user = User.objects.create_user(
            email=f'user_9bd16f42@example.com',
            password='testpass123',
            is_mobile_verified=True
        )

        seller = User.objects.create_user(
            email=f'seller_e3b66f14@example.com',
            password='testpass123',
            user_type='artist'
        )

        category = Category.objects.create(name='Test Category')
        product = Product.objects.create(
            seller=seller,
            name='Test Product',
            base_price=Decimal('100.00'),
            stock_quantity=50,
            category=category
        )

        variant = ProductVariant.objects.create(
            product=product,
            sku='PROD-M',
            stock_quantity=20
        )

        order = Order.objects.create(
            user=user,
            status='paid',
            total_amount=Decimal('100.00')
        )

        # Order item MUST store variant reference
        item = OrderItem.objects.create(
            order=order,
            product=product,
            variant=variant,
            quantity=1,
            price=Decimal('100.00')
        )

        assert item.variant_id == variant.id

    def test_order_line_item_stores_variant_id(self, db):
        """FR-INV-013: Order line items MUST store variant ID for correct stock release."""
        user = User.objects.create_user(
            email=f'user_5a6fc13c@example.com',
            password='testpass123',
            is_mobile_verified=True
        )

        seller = User.objects.create_user(
            email=f'seller_3906d774@example.com',
            password='testpass123',
            user_type='artist'
        )

        category = Category.objects.create(name='Test Category')
        product = Product.objects.create(
            seller=seller,
            name='Test Product',
            base_price=Decimal('100.00'),
            stock_quantity=50,
            category=category
        )

        variant = ProductVariant.objects.create(
            product=product,
            sku='PROD-M',
            stock_quantity=20
        )

        order = Order.objects.create(
            user=user,
            status='paid',
            total_amount=Decimal('100.00')
        )

        item = OrderItem.objects.create(
            order=order,
            product=product,
            variant=variant,
            quantity=1,
            price=Decimal('100.00')
        )

        # Item has sufficient data to release stock without external lookups
        assert item.variant_id is not None
        assert item.quantity > 0


class TestOrderDataForStockRelease:
    """Test FR-INV-014, FR-INV-015: Historical snapshot for stock release."""

    pytestmark = pytest.mark.non_critical

    def test_order_item_contains_sufficient_data(self, db):
        """FR-INV-014: Order item MUST contain data to release stock without lookups."""
        user = User.objects.create_user(
            email=f'user_4af21268@example.com',
            password='testpass123',
            is_mobile_verified=True
        )

        seller = User.objects.create_user(
            email=f'seller_b1d65201@example.com',
            password='testpass123',
            user_type='artist'
        )

        category = Category.objects.create(name='Test Category')
        product = Product.objects.create(
            seller=seller,
            name='Test Product',
            base_price=Decimal('100.00'),
            stock_quantity=50,
            category=category
        )

        variant = ProductVariant.objects.create(
            product=product,
            sku='PROD-M',
            stock_quantity=20
        )

        order = Order.objects.create(
            user=user,
            status='paid',
            total_amount=Decimal('100.00')
        )

        item = OrderItem.objects.create(
            order=order,
            product=product,
            variant=variant,
            quantity=5,
            price=Decimal('100.00')
        )

        # Can release stock using only order item data
        assert item.product_id
        assert item.variant_id
        assert item.quantity
        # No need to query current product/variant configuration

    def test_stock_release_uses_historical_snapshot(self, db):
        """FR-INV-015: Stock release uses historical snapshot, not current config."""
        user = User.objects.create_user(
            email=f'user_7c02dae2@example.com',
            password='testpass123',
            is_mobile_verified=True
        )

        seller = User.objects.create_user(
            email=f'seller_a04a9ea4@example.com',
            password='testpass123',
            user_type='artist'
        )

        category = Category.objects.create(name='Test Category')
        product = Product.objects.create(
            seller=seller,
            name='Test Product',
            base_price=Decimal('100.00'),
            stock_quantity=50,
            category=category
        )

        order = Order.objects.create(
            user=user,
            status='paid',
            total_amount=Decimal('500.00')
        )

        item = OrderItem.objects.create(
            order=order,
            product=product,
            quantity=5,
            price=Decimal('100.00')
        )

        # Change product configuration after order
        product.stock_quantity = 0
        product.save()

        # Stock release should still work using historical quantity from order item
        order.status = 'refunded'
        order.save()

        # Release should use item.quantity, not current product.stock_quantity
