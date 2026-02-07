"""
Tests for Refund Flow (User Story 7)

Tests cover:
- Refund transitions order to 'refunded' state
- Wallet credit on refund
- Stock release on refund
- Refund prevention on unpaid orders
"""

import pytest
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta

from orders.models import Order, OrderItem
from orders.atomic_order_system import (
    AtomicOrderCreator,
    OrderStateMachine,
    WalletOrderCoordinator,
    StockLockManager
)
from products.models import Product
from wallet.models import Wallet, Transaction


@pytest.mark.django_db
class TestRefundFlow:
    """Test complete refund flow with wallet credit and stock release."""

    def test_refund_transitions_order_to_refunded_state(self, user, product, user_wallet):
        """
        Test that refund transitions order to 'refunded' state.
        
        Given: An order in 'paid' status with wallet payment
        When: Order is refunded
        Then: Order status should be 'refunded'
        """
        # Create order with wallet payment
        items_data = [{'product_id': product.id, 'quantity': 1}]
        success, order, error = AtomicOrderCreator.create_order(
            user=user,
            items_data=items_data,
            shipping_address="Test Address",
            shipping_cost=Decimal('10.00'),
            payment_method='wallet',
            idempotency_key='refund_test_1',
            use_wallet_payment=True
        )
        assert success, f"Order creation failed: {error}"
        
        # Capture payment to move to 'paid' status
        success, tx, error = WalletOrderCoordinator.capture_payment(
            order_id=order.id,
            idempotency_key='capture_refund_test_1'
        )
        assert success, f"Payment capture failed: {error}"
        
        # Refresh order
        order.refresh_from_db()
        assert order.status == 'paid'
        
        # Refund order
        success, refund_tx, error = WalletOrderCoordinator.refund_payment(
            order_id=order.id,
            idempotency_key='refund_refund_test_1',
            refund_reason='Test refund'
        )
        assert success, f"Refund failed: {error}"
        
        # Refresh order
        order.refresh_from_db()
        assert order.status == 'refunded', \
            f"Order status should be 'refunded', got '{order.status}'"

    def test_wallet_credit_on_refund(self, user, product, user_wallet):
        """
        Test that refund credits wallet with correct amount.
        
        Given: An order with wallet payment of $100
        When: Order is refunded
        Then: Wallet balance should increase by $100
        """
        # Initial wallet balance
        initial_balance = user_wallet.balance
        
        # Create order with wallet payment
        items_data = [{'product_id': product.id, 'quantity': 2}]
        success, order, error = AtomicOrderCreator.create_order(
            user=user,
            items_data=items_data,
            shipping_address="Test Address",
            shipping_cost=Decimal('10.00'),
            payment_method='wallet',
            idempotency_key='wallet_credit_test',
            use_wallet_payment=True
        )
        assert success, f"Order creation failed: {error}"
        
        # Capture payment
        success, tx, error = WalletOrderCoordinator.capture_payment(
            order_id=order.id,
            idempotency_key='capture_wallet_credit_test'
        )
        assert success, f"Payment capture failed: {error}"
        
        # Get payment amount
        payment_amount = tx.amount
        
        # Refresh wallet
        user_wallet.refresh_from_db()
        balance_after_payment = user_wallet.balance
        
        # Refund order
        success, refund_tx, error = WalletOrderCoordinator.refund_payment(
            order_id=order.id,
            idempotency_key='refund_wallet_credit_test',
            refund_reason='Test refund'
        )
        assert success, f"Refund failed: {error}"
        
        # Refresh wallet
        user_wallet.refresh_from_db()
        final_balance = user_wallet.balance
        
        # Verify wallet was credited with refund amount
        assert final_balance == balance_after_payment + payment_amount, \
            f"Wallet balance should be {balance_after_payment + payment_amount}, got {final_balance}"
        
        # Verify refund transaction
        assert refund_tx.transaction_type == 'refund'
        assert refund_tx.amount == payment_amount
        assert refund_tx.status == 'completed'
        assert refund_tx.reference_id == str(order.id)

    def test_stock_release_on_refund(self, user, product, user_wallet):
        """
        Test that refund releases reserved stock.
        
        Given: An order that reserved 2 units of stock
        When: Order is refunded
        Then: Stock should be released (increased by 2)
        """
        # Initial stock
        product.refresh_from_db()
        initial_stock = product.stock_quantity
        
        # Create order with wallet payment
        quantity = 2
        items_data = [{'product_id': product.id, 'quantity': quantity}]
        success, order, error = AtomicOrderCreator.create_order(
            user=user,
            items_data=items_data,
            shipping_address="Test Address",
            shipping_cost=Decimal('10.00'),
            payment_method='wallet',
            idempotency_key='stock_release_test',
            use_wallet_payment=True
        )
        assert success, f"Order creation failed: {error}"
        
        # Capture payment
        success, tx, error = WalletOrderCoordinator.capture_payment(
            order_id=order.id,
            idempotency_key='capture_stock_release_test'
        )
        assert success, f"Payment capture failed: {error}"
        
        # Verify stock was reserved
        product.refresh_from_db()
        stock_after_order = product.stock_quantity
        assert stock_after_order == initial_stock - quantity, \
            f"Stock should be {initial_stock - quantity}, got {stock_after_order}"
        
        # Refund order
        success, refund_tx, error = WalletOrderCoordinator.refund_payment(
            order_id=order.id,
            idempotency_key='refund_stock_release_test',
            refund_reason='Test refund'
        )
        assert success, f"Refund failed: {error}"
        
        # Verify stock was released
        product.refresh_from_db()
        final_stock = product.stock_quantity
        assert final_stock == initial_stock, \
            f"Stock should be {initial_stock} after refund, got {final_stock}"
        
        # Verify order item reservation status
        order_item = OrderItem.objects.get(order=order)
        assert order_item.reservation_status == 'released', \
            f"Reservation status should be 'released', got '{order_item.reservation_status}'"

    def test_refund_prevention_on_unpaid_orders(self, user, product):
        """
        Test that refund is prevented for unpaid orders.
        
        Given: An order in 'pending_payment' status (no payment captured)
        When: Attempt to refund
        Then: Refund should fail with appropriate error
        """
        # Create order without wallet payment
        items_data = [{'product_id': product.id, 'quantity': 1}]
        success, order, error = AtomicOrderCreator.create_order(
            user=user,
            items_data=items_data,
            shipping_address="Test Address",
            shipping_cost=Decimal('10.00'),
            payment_method='instapay',
            idempotency_key='unpaid_refund_test',
            use_wallet_payment=False
        )
        assert success, f"Order creation failed: {error}"
        
        # Verify order is in pending_payment status
        order.refresh_from_db()
        assert order.status == 'pending_payment'
        
        # Attempt to refund unpaid order
        success, refund_tx, error = WalletOrderCoordinator.refund_payment(
            order_id=order.id,
            idempotency_key='refund_unpaid_test',
            refund_reason='Test refund'
        )
        
        # Refund should fail
        assert not success, "Refund should fail for unpaid order"
        assert error is not None, "Error message should be provided"

    def test_refund_prevention_on_cod_orders(self, user, product):
        """
        Test that refund is prevented for COD orders.
        
        Given: A COD order (no payment made)
        When: Attempt to refund
        Then: Refund should fail with appropriate error
        """
        # Create COD order
        items_data = [{'product_id': product.id, 'quantity': 1}]
        success, order, error = AtomicOrderCreator.create_order(
            user=user,
            items_data=items_data,
            shipping_address="Test Address",
            shipping_cost=Decimal('10.00'),
            payment_method='cod',
            idempotency_key='cod_refund_test',
            use_wallet_payment=False
        )
        assert success, f"Order creation failed: {error}"
        
        # Verify order is in cod_pending status
        order.refresh_from_db()
        assert order.status == 'cod_pending'
        
        # Attempt to refund COD order
        success, refund_tx, error = WalletOrderCoordinator.refund_payment(
            order_id=order.id,
            idempotency_key='refund_cod_test',
            refund_reason='Test refund'
        )
        
        # Refund should fail
        assert not success, "Refund should fail for COD order"
        assert error is not None, "Error message should be provided"

    def test_refund_from_delivered_state(self, user, product, user_wallet):
        """
        Test that refund works from 'delivered' state.
        
        Given: An order in 'delivered' status (return/dispute scenario)
        When: Order is refunded
        Then: Order should transition to 'refunded' with wallet credit and stock release
        """
        # Create order with wallet payment
        items_data = [{'product_id': product.id, 'quantity': 1}]
        success, order, error = AtomicOrderCreator.create_order(
            user=user,
            items_data=items_data,
            shipping_address="Test Address",
            shipping_cost=Decimal('10.00'),
            payment_method='wallet',
            idempotency_key='delivered_refund_test',
            use_wallet_payment=True
        )
        assert success, f"Order creation failed: {error}"
        
        # Capture payment
        success, tx, error = WalletOrderCoordinator.capture_payment(
            order_id=order.id,
            idempotency_key='capture_delivered_test'
        )
        assert success, f"Payment capture failed: {error}"
        
        # Move order to delivered
        OrderStateMachine.validate_transition(order.status, 'processing')
        order.status = 'processing'
        order.save()
        
        OrderStateMachine.validate_transition(order.status, 'shipped')
        order.status = 'shipped'
        order.save()
        
        OrderStateMachine.validate_transition(order.status, 'delivered')
        order.status = 'delivered'
        order.save()
        
        # Verify order is in delivered status
        order.refresh_from_db()
        assert order.status == 'delivered'
        
        # Refund order
        success, refund_tx, error = WalletOrderCoordinator.refund_payment(
            order_id=order.id,
            idempotency_key='refund_delivered_test',
            refund_reason='Return request'
        )
        assert success, f"Refund failed: {error}"
        
        # Verify order status
        order.refresh_from_db()
        assert order.status == 'refunded', \
            f"Order status should be 'refunded', got '{order.status}'"

    def test_refund_idempotency(self, user, product, user_wallet):
        """
        Test that refund is idempotent.
        
        Given: An order that has been refunded
        When: Attempt to refund again with same idempotency key
        Then: Should return existing refund transaction without error
        """
        # Create order with wallet payment
        items_data = [{'product_id': product.id, 'quantity': 1}]
        success, order, error = AtomicOrderCreator.create_order(
            user=user,
            items_data=items_data,
            shipping_address="Test Address",
            shipping_cost=Decimal('10.00'),
            payment_method='wallet',
            idempotency_key='idempotency_test',
            use_wallet_payment=True
        )
        assert success, f"Order creation failed: {error}"
        
        # Capture payment
        success, tx, error = WalletOrderCoordinator.capture_payment(
            order_id=order.id,
            idempotency_key='capture_idempotency_test'
        )
        assert success, f"Payment capture failed: {error}"
        
        # Refund order first time
        idempotency_key = 'refund_idempotency_test'
        success, refund_tx1, error = WalletOrderCoordinator.refund_payment(
            order_id=order.id,
            idempotency_key=idempotency_key,
            refund_reason='Test refund'
        )
        assert success, f"First refund failed: {error}"
        
        # Attempt to refund again with same idempotency key
        success, refund_tx2, error = WalletOrderCoordinator.refund_payment(
            order_id=order.id,
            idempotency_key=idempotency_key,
            refund_reason='Test refund'
        )
        
        # Should succeed and return same refund transaction
        assert success, f"Idempotent refund should succeed: {error}"
        assert refund_tx2.id == refund_tx1.id, \
            "Should return existing refund transaction"

    def test_refund_from_processing_state(self, user, product, user_wallet):
        """
        Test that refund works from 'processing' state.
        
        Given: An order in 'processing' status
        When: Order is refunded
        Then: Order should transition to 'refunded' with wallet credit and stock release
        """
        # Create order with wallet payment
        items_data = [{'product_id': product.id, 'quantity': 1}]
        success, order, error = AtomicOrderCreator.create_order(
            user=user,
            items_data=items_data,
            shipping_address="Test Address",
            shipping_cost=Decimal('10.00'),
            payment_method='wallet',
            idempotency_key='processing_refund_test',
            use_wallet_payment=True
        )
        assert success, f"Order creation failed: {error}"
        
        # Capture payment
        success, tx, error = WalletOrderCoordinator.capture_payment(
            order_id=order.id,
            idempotency_key='capture_processing_test'
        )
        assert success, f"Payment capture failed: {error}"
        
        # Move order to processing
        OrderStateMachine.validate_transition(order.status, 'processing')
        order.status = 'processing'
        order.save()
        
        # Verify order is in processing status
        order.refresh_from_db()
        assert order.status == 'processing'
        
        # Refund order
        success, refund_tx, error = WalletOrderCoordinator.refund_payment(
            order_id=order.id,
            idempotency_key='refund_processing_test',
            refund_reason='Customer request'
        )
        assert success, f"Refund failed: {error}"
        
        # Verify order status
        order.refresh_from_db()
        assert order.status == 'refunded', \
            f"Order status should be 'refunded', got '{order.status}'"

    def test_refund_from_shipped_state(self, user, product, user_wallet):
        """
        Test that refund works from 'shipped' state.
        
        Given: An order in 'shipped' status
        When: Order is refunded
        Then: Order should transition to 'refunded' with wallet credit and stock release
        """
        # Create order with wallet payment
        items_data = [{'product_id': product.id, 'quantity': 1}]
        success, order, error = AtomicOrderCreator.create_order(
            user=user,
            items_data=items_data,
            shipping_address="Test Address",
            shipping_cost=Decimal('10.00'),
            payment_method='wallet',
            idempotency_key='shipped_refund_test',
            use_wallet_payment=True
        )
        assert success, f"Order creation failed: {error}"
        
        # Capture payment
        success, tx, error = WalletOrderCoordinator.capture_payment(
            order_id=order.id,
            idempotency_key='capture_shipped_test'
        )
        assert success, f"Payment capture failed: {error}"
        
        # Move order to shipped
        OrderStateMachine.validate_transition(order.status, 'processing')
        order.status = 'processing'
        order.save()
        
        OrderStateMachine.validate_transition(order.status, 'shipped')
        order.status = 'shipped'
        order.save()
        
        # Verify order is in shipped status
        order.refresh_from_db()
        assert order.status == 'shipped'
        
        # Refund order
        success, refund_tx, error = WalletOrderCoordinator.refund_payment(
            order_id=order.id,
            idempotency_key='refund_shipped_test',
            refund_reason='Return request'
        )
        assert success, f"Refund failed: {error}"
        
        # Verify order status
        order.refresh_from_db()
        assert order.status == 'refunded', \
            f"Order status should be 'refunded', got '{order.status}'"
