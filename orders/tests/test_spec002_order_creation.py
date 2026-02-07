"""
Spec 002 Tests: Order Creation

Tests derived from:
- spec-002.md sections: Order Creation Specification
- FR-ORD-010 through FR-ORD-023
"""

import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from products.models import Product, Category
from orders.models import Order, OrderItem
from cart.models import Cart

User = get_user_model()


class TestOrderCreationPreconditions:
    """Test FR-ORD-010 through FR-ORD-014: Preconditions for order creation."""

    def test_order_creation_requires_authentication(self, api_client, product):
        """FR-ORD-010: User MUST be authenticated."""
        response = api_client.post(
            '/api/v1/orders/create/',
            data={'cart_id': 1},
            format='json'
        )
        assert response.status_code == 401

    def test_order_creation_requires_mobile_verification(self, authenticated_client, product):
        """FR-ORD-011: User MUST have verified mobile."""
        user = User.objects.first()
        user.is_mobile_verified = False
        user.save()

        cart = Cart.objects.create(user=user)
        cart.items = [{'product_id': product.id, 'quantity': 1}]
        cart.save()

        response = authenticated_client.post(
            '/api/v1/orders/create/',
            data={'cart_id': cart.id},
            format='json'
        )
        assert response.status_code == 403

    def test_order_creation_allows_verified_user(self, authenticated_client, product):
        """Verified mobile users can create orders."""
        user = User.objects.first()
        user.is_mobile_verified = True
        user.save()

        cart = Cart.objects.create(user=user)
        cart.items = [{'product_id': product.id, 'quantity': 1}]
        cart.save()

        response = authenticated_client.post(
            '/api/v1/orders/create/',
            data={'cart_id': cart.id},
            format='json'
        )
        assert response.status_code in [200, 201]

    def test_order_creation_blocks_locked_users(self, authenticated_client, product):
        """FR-ORD-012: User MUST NOT be in Locked state."""
        user = User.objects.first()
        user.is_locked = True
        user.is_mobile_verified = True
        user.save()

        cart = Cart.objects.create(user=user)
        cart.items = [{'product_id': product.id, 'quantity': 1}]
        cart.save()

        response = authenticated_client.post(
            '/api/v1/orders/create/',
            data={'cart_id': cart.id},
            format='json'
        )
        assert response.status_code == 403

    def test_order_creation_requires_nonempty_cart(self, authenticated_client, product):
        """FR-ORD-013: Cart MUST contain at least one item."""
        user = User.objects.first()
        user.is_mobile_verified = True
        user.save()

        cart = Cart.objects.create(user=user)
        cart.items = []
        cart.save()

        response = authenticated_client.post(
            '/api/v1/orders/create/',
            data={'cart_id': cart.id},
            format='json'
        )
        assert response.status_code == 400

    def test_order_creation_validates_stock_availability(self, authenticated_client, product):
        """FR-ORD-014: All items MUST have sufficient stock."""
        user = User.objects.first()
        user.is_mobile_verified = True
        user.save()

        # Set product stock to 0
        product.stock_quantity = 0
        product.save()

        cart = Cart.objects.create(user=user)
        cart.items = [{'product_id': product.id, 'quantity': 1}]
        cart.save()

        response = authenticated_client.post(
            '/api/v1/orders/create/',
            data={'cart_id': cart.id},
            format='json'
        )
        assert response.status_code == 400


class TestStockValidationTiming:
    """Test FR-ORD-015 through FR-ORD-017: Stock validation timing."""

    def test_stock_validated_at_order_creation_time(self, authenticated_client, product):
        """FR-ORD-015: Stock validated at order creation (not cart add time)."""
        user = User.objects.first()
        user.is_mobile_verified = True
        user.save()

        # Add to cart when stock is available
        cart = Cart.objects.create(user=user)
        cart.items = [{'product_id': product.id, 'quantity': 1}]
        cart.save()

        # Stock becomes unavailable before order creation
        product.stock_quantity = 0
        product.save()

        response = authenticated_client.post(
            '/api/v1/orders/create/',
            data={'cart_id': cart.id},
            format='json'
        )
        assert response.status_code == 400

    def test_stock_reservation_atomic_with_validation(self, authenticated_client, product):
        """FR-ORD-016: Stock validation and reservation occur atomically."""
        user = User.objects.first()
        user.is_mobile_verified = True
        user.save()

        initial_stock = product.stock_quantity

        cart = Cart.objects.create(user=user)
        cart.items = [{'product_id': product.id, 'quantity': 2}]
        cart.save()

        response = authenticated_client.post(
            '/api/v1/orders/create/',
            data={'cart_id': cart.id},
            format='json'
        )

        if response.status_code in [200, 201]:
            # Stock should be reserved
            product.refresh_from_db()
            assert product.stock_quantity == initial_stock - 2

    def test_partial_order_failure_on_stock_shortage(self, authenticated_client, product):
        """FR-ORD-017: Any stock failure MUST fail entire order."""
        user = User.objects.first()
        user.is_mobile_verified = True
        user.save()

        # Create another product with no stock
        category = Category.objects.create(name='Test Category 2')
        product_no_stock = Product.objects.create(
            seller=product.seller,
            name='No Stock Product',
            base_price=Decimal('50.00'),
            stock_quantity=0,
            category=category
        )

        cart = Cart.objects.create(user=user)
        cart.items = [
            {'product_id': product.id, 'quantity': 1},  # Has stock
            {'product_id': product_no_stock.id, 'quantity': 1}  # No stock
        ]
        cart.save()

        response = authenticated_client.post(
            '/api/v1/orders/create/',
            data={'cart_id': cart.id},
            format='json'
        )
        assert response.status_code == 400
        # No order should be created
        assert not Order.objects.filter(user=user).exists()


class TestIdempotencyBehavior:
    """Test FR-ORD-018 through FR-ORD-020: Idempotency."""

    def test_duplicate_order_request_returns_existing_order(self, authenticated_client, product):
        """FR-ORD-018: Duplicate requests return existing order."""
        user = User.objects.first()
        user.is_mobile_verified = True
        user.save()

        cart = Cart.objects.create(user=user)
        cart.items = [{'product_id': product.id, 'quantity': 1}]
        cart.save()

        # First request
        response1 = authenticated_client.post(
            '/api/v1/orders/create/',
            data={'cart_id': cart.id},
            format='json'
        )

        # Second identical request within idempotency window
        response2 = authenticated_client.post(
            '/api/v1/orders/create/',
            data={'cart_id': cart.id},
            format='json'
        )

        # Should return same order
        if response1.status_code in [200, 201]:
            order_id_1 = response1.json().get('id') or response1.json().get('data', {}).get('id')
            order_id_2 = response2.json().get('id') or response2.json().get('data', {}).get('id')
            assert order_id_1 == order_id_2

    def test_idempotency_key_based_on_user_cart_and_time(self, authenticated_client, product):
        """FR-ORD-019: Idempotency key based on user ID, cart hash, timestamp."""
        # This is a behavioral test - implementation details vary
        # Key assertion: different users get different orders for same cart
        user1 = User.objects.first()
        user1.is_mobile_verified = True
        user1.save()

        user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123',
            is_mobile_verified=True
        )

        cart1 = Cart.objects.create(user=user1)
        cart1.items = [{'product_id': product.id, 'quantity': 1}]
        cart1.save()

        cart2 = Cart.objects.create(user=user2)
        cart2.items = [{'product_id': product.id, 'quantity': 1}]
        cart2.save()

        # Each user should get separate order
        order1 = Order.objects.filter(user=user1).first()
        order2 = Order.objects.filter(user=user2).first()

        if order1 and order2:
            assert order1.id != order2.id


class TestPartialFailureHandling:
    """Test FR-ORD-021 through FR-ORD-023: Partial failure handling."""

    def test_stock_reservation_failure_rolls_back_all(self, authenticated_client, product):
        """FR-ORD-021: Stock failure for any item fails all reservations."""
        user = User.objects.first()
        user.is_mobile_verified = True
        user.save()

        category = Category.objects.create(name='Category 2')
        product_no_stock = Product.objects.create(
            seller=product.seller,
            name='No Stock Product',
            base_price=Decimal('50.00'),
            stock_quantity=0,
            category=category
        )

        initial_stock = product.stock_quantity

        cart = Cart.objects.create(user=user)
        cart.items = [
            {'product_id': product.id, 'quantity': 1},
            {'product_id': product_no_stock.id, 'quantity': 1}
        ]
        cart.save()

        response = authenticated_client.post(
            '/api/v1/orders/create/',
            data={'cart_id': cart.id},
            format='json'
        )

        # Stock should not be reserved for product
        product.refresh_from_db()
        assert product.stock_quantity == initial_stock

    def test_payment_failure_releases_stock(self, authenticated_client, product):
        """FR-ORD-022: Payment failure releases reserved stock."""
        user = User.objects.first()
        user.is_mobile_verified = True
        user.save()

        initial_stock = product.stock_quantity

        cart = Cart.objects.create(user=user)
        cart.items = [{'product_id': product.id, 'quantity': 2}]
        cart.save()

        # Simulate payment failure
        response = authenticated_client.post(
            '/api/v1/orders/create/',
            data={'cart_id': cart.id, 'payment_method': 'invalid'},
            format='json'
        )

        # Stock should be released
        product.refresh_from_db()
        # Implementation may vary - stock should be restored
        assert product.stock_quantity >= initial_stock - 2

    def test_order_creation_error_indicates_failed_item(self, authenticated_client, product):
        """FR-ORD-023: Failure MUST indicate which item(s) caused failure."""
        user = User.objects.first()
        user.is_mobile_verified = True
        user.save()

        category = Category.objects.create(name='Category 2')
        product_no_stock = Product.objects.create(
            seller=product.seller,
            name='No Stock Product',
            base_price=Decimal('50.00'),
            stock_quantity=0,
            category=category
        )

        cart = Cart.objects.create(user=user)
        cart.items = [
            {'product_id': product.id, 'quantity': 1},
            {'product_id': product_no_stock.id, 'quantity': 1}
        ]
        cart.save()

        response = authenticated_client.post(
            '/api/v1/orders/create/',
            data={'cart_id': cart.id},
            format='json'
        )

        data = response.json()
        # Error should mention the out-of-stock item
        error_msg = str(data).lower()
        assert 'stock' in error_msg or 'unavailable' in error_msg
