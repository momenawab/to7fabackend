"""
Tests for Stock Reservation Tracking (User Story 4)

Tests verify that reservation_status is properly tracked throughout the order lifecycle:
- reserved: Stock held for order (initial state)
- released: Stock returned to inventory (on cancellation/timeout)
- committed: Stock permanently decremented (on order completion)
"""

import pytest
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

from orders.models import Order, OrderItem
from orders.atomic_order_system import AtomicOrderCreator, StockLockManager
from products.models import Product
from custom_auth.models import User


@pytest.mark.django_db
class TestStockReservationInitialStatus:
    """Test that reservation_status is set to 'reserved' on order creation."""

    def test_reservation_status_reserved_on_order_creation_wallet_payment(self, user, product_with_stock):
        """
        Test that when an order is created with wallet payment,
        all order items have reservation_status = 'reserved'.
        """
        # Arrange
        items_data = [
            {
                'product_id': product_with_stock.id,
                'quantity': 2,
                'variant_id': None
            }
        ]
        shipping_address = "123 Test Street"
        shipping_cost = Decimal('10.00')
        payment_method = 'wallet'
        idempotency_key = 'test-reservation-001'

        # Act
        success, order, error = AtomicOrderCreator.create_order(
            user=user,
            items_data=items_data,
            shipping_address=shipping_address,
            shipping_cost=shipping_cost,
            payment_method=payment_method,
            idempotency_key=idempotency_key,
            use_wallet_payment=True
        )

        # Assert
        assert success is True
        assert order is not None
        assert error is None

        # Verify all items have reservation_status = 'reserved'
        order_items = OrderItem.objects.filter(order=order)
        assert order_items.count() == 1

        for item in order_items:
            assert item.reservation_status == 'reserved', \
                f"Expected reservation_status='reserved', got '{item.reservation_status}'"

    def test_reservation_status_reserved_on_order_creation_cod_payment(self, user, product_with_stock):
        """
        Test that when a COD order is created,
        all order items have reservation_status = 'reserved'.
        """
        # Arrange
        items_data = [
            {
                'product_id': product_with_stock.id,
                'quantity': 1,
                'variant_id': None
            }
        ]
        shipping_address = "456 COD Street"
        shipping_cost = Decimal('15.00')
        payment_method = 'cod'
        idempotency_key = 'test-reservation-cod-001'

        # Act
        success, order, error = AtomicOrderCreator.create_order(
            user=user,
            items_data=items_data,
            shipping_address=shipping_address,
            shipping_cost=shipping_cost,
            payment_method=payment_method,
            idempotency_key=idempotency_key,
            use_wallet_payment=False
        )

        # Assert
        assert success is True
        assert order is not None

        # Verify all items have reservation_status = 'reserved'
        order_items = OrderItem.objects.filter(order=order)
        for item in order_items:
            assert item.reservation_status == 'reserved', \
                f"Expected reservation_status='reserved' for COD order, got '{item.reservation_status}'"

    def test_reservation_status_reserved_for_multiple_items(self, user, product_with_stock, another_product):
        """
        Test that when an order has multiple items,
        all items have reservation_status = 'reserved'.
        """
        # Arrange
        items_data = [
            {
                'product_id': product_with_stock.id,
                'quantity': 1,
                'variant_id': None
            },
            {
                'product_id': another_product.id,
                'quantity': 2,
                'variant_id': None
            }
        ]
        shipping_address = "789 Multi Street"
        shipping_cost = Decimal('20.00')
        payment_method = 'wallet'
        idempotency_key = 'test-reservation-multi-001'

        # Act
        success, order, error = AtomicOrderCreator.create_order(
            user=user,
            items_data=items_data,
            shipping_address=shipping_address,
            shipping_cost=shipping_cost,
            payment_method=payment_method,
            idempotency_key=idempotency_key,
            use_wallet_payment=True
        )

        # Assert
        assert success is True

        # Verify all items have reservation_status = 'reserved'
        order_items = OrderItem.objects.filter(order=order)
        assert order_items.count() == 2

        for item in order_items:
            assert item.reservation_status == 'reserved', \
                f"Item {item.id} should have reservation_status='reserved', got '{item.reservation_status}'"


@pytest.mark.django_db
class TestStockReservationReleasedOnCancellation:
    """Test that reservation_status is set to 'released' on order cancellation."""

    def test_reservation_status_released_on_cancellation_pending_payment(self, user, product_with_stock, user_wallet):
        """
        Test that when a pending_payment order is cancelled,
        all order items have reservation_status = 'released'.
        """
        # Arrange - Create order
        items_data = [
            {
                'product_id': product_with_stock.id,
                'quantity': 2,
                'variant_id': None
            }
        ]
        shipping_address = "123 Cancel Street"
        shipping_cost = Decimal('10.00')
        payment_method = 'wallet'
        idempotency_key = 'test-release-001'

        success, order, error = AtomicOrderCreator.create_order(
            user=user,
            items_data=items_data,
            shipping_address=shipping_address,
            shipping_cost=shipping_cost,
            payment_method=payment_method,
            idempotency_key=idempotency_key,
            use_wallet_payment=True
        )

        assert success is True
        assert order.status == 'pending_payment'

        # Get initial stock
        initial_stock = Product.objects.get(id=product_with_stock.id).stock_quantity

        # Act - Cancel order
        success, cancelled_order, error = AtomicOrderCreator.cancel_order(
            order_id=order.id,
            user=user,
            reason="User cancelled"
        )

        # Assert
        assert success is True
        assert cancelled_order.status == 'cancelled'

        # Verify all items have reservation_status = 'released'
        order_items = OrderItem.objects.filter(order=order)
        for item in order_items:
            assert item.reservation_status == 'released', \
                f"Expected reservation_status='released' after cancellation, got '{item.reservation_status}'"

        # Verify stock was released
        final_stock = Product.objects.get(id=product_with_stock.id).stock_quantity
        assert final_stock == initial_stock + 2, \
            f"Stock should be released. Initial: {initial_stock}, Final: {final_stock}"

    def test_reservation_status_released_on_cancellation_cod_order(self, user, product_with_stock):
        """
        Test that when a COD order is cancelled,
        all order items have reservation_status = 'released'.
        """
        # Arrange - Create COD order
        items_data = [
            {
                'product_id': product_with_stock.id,
                'quantity': 1,
                'variant_id': None
            }
        ]
        shipping_address = "456 COD Cancel Street"
        shipping_cost = Decimal('15.00')
        payment_method = 'cod'
        idempotency_key = 'test-release-cod-001'

        success, order, error = AtomicOrderCreator.create_order(
            user=user,
            items_data=items_data,
            shipping_address=shipping_address,
            shipping_cost=shipping_cost,
            payment_method=payment_method,
            idempotency_key=idempotency_key,
            use_wallet_payment=False
        )

        assert success is True
        assert order.status == 'cod_pending'

        # Get initial stock
        initial_stock = Product.objects.get(id=product_with_stock.id).stock_quantity

        # Act - Cancel COD order
        success, cancelled_order, error = AtomicOrderCreator.cancel_order(
            order_id=order.id,
            user=user,
            reason="COD order cancelled"
        )

        # Assert
        assert success is True
        assert cancelled_order.status == 'cancelled'

        # Verify all items have reservation_status = 'released'
        order_items = OrderItem.objects.filter(order=order)
        for item in order_items:
            assert item.reservation_status == 'released', \
                f"COD order item should have reservation_status='released', got '{item.reservation_status}'"

        # Verify stock was released
        final_stock = Product.objects.get(id=product_with_stock.id).stock_quantity
        assert final_stock == initial_stock + 1, \
            f"COD stock should be released. Initial: {initial_stock}, Final: {final_stock}"

    def test_reservation_status_released_on_payment_timeout(self, user, product_with_stock, user_wallet):
        """
        Test that when an order is cancelled due to payment timeout,
        all order items have reservation_status = 'released'.
        """
        # Arrange - Create order
        items_data = [
            {
                'product_id': product_with_stock.id,
                'quantity': 3,
                'variant_id': None
            }
        ]
        shipping_address = "789 Timeout Street"
        shipping_cost = Decimal('10.00')
        payment_method = 'wallet'
        idempotency_key = 'test-release-timeout-001'

        success, order, error = AtomicOrderCreator.create_order(
            user=user,
            items_data=items_data,
            shipping_address=shipping_address,
            shipping_cost=shipping_cost,
            payment_method=payment_method,
            idempotency_key=idempotency_key,
            use_wallet_payment=True
        )

        assert success is True
        assert order.status == 'pending_payment'

        # Set payment timeout to past
        order.payment_timeout_at = timezone.now() - timedelta(minutes=20)
        order.save()

        # Get initial stock
        initial_stock = Product.objects.get(id=product_with_stock.id).stock_quantity

        # Act - Cancel order (simulating timeout)
        success, cancelled_order, error = AtomicOrderCreator.cancel_order(
            order_id=order.id,
            user=None,  # System-initiated
            reason="Payment timeout"
        )

        # Assert
        assert success is True
        assert cancelled_order.status == 'cancelled'

        # Verify all items have reservation_status = 'released'
        order_items = OrderItem.objects.filter(order=order)
        for item in order_items:
            assert item.reservation_status == 'released', \
                f"Timeout cancellation should set reservation_status='released', got '{item.reservation_status}'"

        # Verify stock was released
        final_stock = Product.objects.get(id=product_with_stock.id).stock_quantity
        assert final_stock == initial_stock + 3, \
            f"Timeout should release stock. Initial: {initial_stock}, Final: {final_stock}"


@pytest.mark.django_db
class TestStockReservationCommittedOnCompletion:
    """Test that reservation_status is set to 'committed' on order completion."""

    def test_reservation_status_committed_on_cod_order_completion(self, user, product_with_stock):
        """
        Test that when a COD order is completed,
        all order items have reservation_status = 'committed'.
        """
        # Arrange - Create COD order
        items_data = [
            {
                'product_id': product_with_stock.id,
                'quantity': 1,
                'variant_id': None
            }
        ]
        shipping_address = "123 Complete Street"
        shipping_cost = Decimal('15.00')
        payment_method = 'cod'
        idempotency_key = 'test-commit-cod-001'

        success, order, error = AtomicOrderCreator.create_order(
            user=user,
            items_data=items_data,
            shipping_address=shipping_address,
            shipping_cost=shipping_cost,
            payment_method=payment_method,
            idempotency_key=idempotency_key,
            use_wallet_payment=False
        )

        assert success is True
        assert order.status == 'cod_pending'

        # Get initial stock
        initial_stock = Product.objects.get(id=product_with_stock.id).stock_quantity

        # Act - Confirm COD delivery (which completes the order)
        success, completed_order, error = AtomicOrderCreator.confirm_cod_delivery(
            order_id=order.id
        )

        # Assert
        assert success is True
        assert completed_order.status == 'completed'
        assert completed_order.payment_status is True

        # Verify all items have reservation_status = 'committed'
        order_items = OrderItem.objects.filter(order=order)
        for item in order_items:
            assert item.reservation_status == 'committed', \
                f"Completed order should have reservation_status='committed', got '{item.reservation_status}'"

        # Verify stock remains decremented (not released)
        final_stock = Product.objects.get(id=product_with_stock.id).stock_quantity
        assert final_stock == initial_stock, \
            f"Stock should remain decremented (committed). Initial: {initial_stock}, Final: {final_stock}"

    def test_reservation_status_committed_for_multiple_items(self, user, product_with_stock, another_product):
        """
        Test that when an order with multiple items is completed,
        all items have reservation_status = 'committed'.
        """
        # Arrange - Create COD order with multiple items
        items_data = [
            {
                'product_id': product_with_stock.id,
                'quantity': 1,
                'variant_id': None
            },
            {
                'product_id': another_product.id,
                'quantity': 2,
                'variant_id': None
            }
        ]
        shipping_address = "456 Multi Complete Street"
        shipping_cost = Decimal('20.00')
        payment_method = 'cod'
        idempotency_key = 'test-commit-multi-001'

        success, order, error = AtomicOrderCreator.create_order(
            user=user,
            items_data=items_data,
            shipping_address=shipping_address,
            shipping_cost=shipping_cost,
            payment_method=payment_method,
            idempotency_key=idempotency_key,
            use_wallet_payment=False
        )

        assert success is True

        # Get initial stocks
        initial_stock_1 = Product.objects.get(id=product_with_stock.id).stock_quantity
        initial_stock_2 = Product.objects.get(id=another_product.id).stock_quantity

        # Act - Confirm COD delivery
        success, completed_order, error = AtomicOrderCreator.confirm_cod_delivery(
            order_id=order.id
        )

        # Assert
        assert success is True
        assert completed_order.status == 'completed'

        # Verify all items have reservation_status = 'committed'
        order_items = OrderItem.objects.filter(order=order)
        assert order_items.count() == 2

        for item in order_items:
            assert item.reservation_status == 'committed', \
                f"Item {item.id} should have reservation_status='committed', got '{item.reservation_status}'"

        # Verify all stocks remain decremented
        final_stock_1 = Product.objects.get(id=product_with_stock.id).stock_quantity
        final_stock_2 = Product.objects.get(id=another_product.id).stock_quantity

        assert final_stock_1 == initial_stock_1, \
            f"Product 1 stock should remain decremented. Initial: {initial_stock_1}, Final: {final_stock_1}"
        assert final_stock_2 == initial_stock_2, \
            f"Product 2 stock should remain decremented. Initial: {initial_stock_2}, Final: {final_stock_2}"


@pytest.mark.django_db
class TestStockReservationLifecycle:
    """Test the complete lifecycle of reservation_status."""

    def test_full_lifecycle_reserved_to_released(self, user, product_with_stock, user_wallet):
        """
        Test complete lifecycle: reserved (creation) -> released (cancellation).
        """
        # Arrange - Create order
        items_data = [
            {
                'product_id': product_with_stock.id,
                'quantity': 2,
                'variant_id': None
            }
        ]
        shipping_address = "123 Lifecycle Street"
        shipping_cost = Decimal('10.00')
        payment_method = 'wallet'
        idempotency_key = 'test-lifecycle-release-001'

        # Create order
        success, order, error = AtomicOrderCreator.create_order(
            user=user,
            items_data=items_data,
            shipping_address=shipping_address,
            shipping_cost=shipping_cost,
            payment_method=payment_method,
            idempotency_key=idempotency_key,
            use_wallet_payment=True
        )

        # Assert - Initial state
        assert success is True
        order_items = OrderItem.objects.filter(order=order)
        for item in order_items:
            assert item.reservation_status == 'reserved'

        # Act - Cancel order
        success, cancelled_order, error = AtomicOrderCreator.cancel_order(
            order_id=order.id,
            user=user,
            reason="Test lifecycle"
        )

        # Assert - Released state
        assert success is True
        assert cancelled_order.status == 'cancelled'

        order_items = OrderItem.objects.filter(order=order)
        for item in order_items:
            assert item.reservation_status == 'released'

    def test_full_lifecycle_reserved_to_committed(self, user, product_with_stock):
        """
        Test complete lifecycle: reserved (creation) -> committed (completion).
        """
        # Arrange - Create COD order
        items_data = [
            {
                'product_id': product_with_stock.id,
                'quantity': 1,
                'variant_id': None
            }
        ]
        shipping_address = "456 Lifecycle Street"
        shipping_cost = Decimal('15.00')
        payment_method = 'cod'
        idempotency_key = 'test-lifecycle-commit-001'

        # Create order
        success, order, error = AtomicOrderCreator.create_order(
            user=user,
            items_data=items_data,
            shipping_address=shipping_address,
            shipping_cost=shipping_cost,
            payment_method=payment_method,
            idempotency_key=idempotency_key,
            use_wallet_payment=False
        )

        # Assert - Initial state
        assert success is True
        order_items = OrderItem.objects.filter(order=order)
        for item in order_items:
            assert item.reservation_status == 'reserved'

        # Act - Complete order
        success, completed_order, error = AtomicOrderCreator.confirm_cod_delivery(
            order_id=order.id
        )

        # Assert - Committed state
        assert success is True
        assert completed_order.status == 'completed'

        order_items = OrderItem.objects.filter(order=order)
        for item in order_items:
            assert item.reservation_status == 'committed'
