"""
Tests for COD Payment Flow (User Story 2)

Tests cover:
- COD order creation with initial state = cod_pending
- COD lifecycle: cod_pending → processing → shipped → delivered → completed
- COD cancellation path
"""

import pytest
import uuid
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth import get_user_model
from orders.models import Order, OrderItem
from orders.atomic_order_system import AtomicOrderCreator, OrderStateMachine
from products.models import Product

User = get_user_model()


@pytest.mark.django_db
class TestCODOrderCreation:
    """Test COD order creation with initial state = cod_pending."""

    @pytest.mark.django_db
    def test_cod_order_creates_with_cod_pending_status(self, user, product):
        """
        Test that COD orders are created with initial status = cod_pending.
        
        Given:
            - A verified user
            - A product with available stock
            - payment_method = 'cod'
        When:
            - Order is created
        Then:
            - Order status should be 'cod_pending'
            - payment_timeout_at should be None (no timeout for COD)
        """
        items_data = [
            {
                'product_id': product.id,
                'quantity': 1,
            }
        ]
        
        success, order, error = AtomicOrderCreator.create_order(
            user=user,
            items_data=items_data,
            shipping_address="123 Test St, Cairo, Egypt",
            shipping_cost=Decimal('10.00'),
            payment_method='cod',
            idempotency_key='test_cod_order_001',
            use_wallet_payment=False
        )
        
        assert success is True
        assert order is not None
        assert order.status == 'cod_pending', f"Expected 'cod_pending', got '{order.status}'"
        assert order.payment_method == 'cod'
        assert order.payment_timeout_at is None, "COD orders should not have payment timeout"
        assert order.payment_status is False, "COD orders should not have payment_status=True initially"

    @pytest.mark.django_db
    def test_non_cod_order_creates_with_pending_payment_status(self, user, product):
        """
        Test that non-COD orders (wallet, instapay, credit_card) are created 
        with initial status = pending_payment.
        
        Given:
            - A verified user
            - A product with available stock
            - payment_method = 'wallet'
        When:
            - Order is created
        Then:
            - Order status should be 'pending_payment'
            - payment_timeout_at should be set (15 minutes from now)
        """
        items_data = [
            {
                'product_id': product.id,
                'quantity': 1,
            }
        ]
        
        success, order, error = AtomicOrderCreator.create_order(
            user=user,
            items_data=items_data,
            shipping_address="123 Test St, Cairo, Egypt",
            shipping_cost=Decimal('10.00'),
            payment_method='wallet',
            idempotency_key='test_wallet_order_001',
            use_wallet_payment=False  # Not using wallet for payment in this test
        )
        
        assert success is True
        assert order is not None
        assert order.status == 'pending_payment', f"Expected 'pending_payment', got '{order.status}'"
        assert order.payment_method == 'wallet'
        assert order.payment_timeout_at is not None, "Non-COD orders should have payment timeout"


@pytest.mark.django_db
class TestCODLifecycle:
    """Test COD lifecycle: cod_pending → processing → shipped → delivered → completed."""

    @pytest.mark.django_db
    def test_cod_transition_to_processing(self, user, product):
        """
        Test that COD order can transition from cod_pending to processing.
        
        Given:
            - A COD order in 'cod_pending' status
        When:
            - Order status is updated to 'processing'
        Then:
            - Transition should be valid
            - Order status should be 'processing'
        """
        # Create COD order
        items_data = [{'product_id': product.id, 'quantity': 1}]
        success, order, error = AtomicOrderCreator.create_order(
            user=user,
            items_data=items_data,
            shipping_address="123 Test St, Cairo, Egypt",
            shipping_cost=Decimal('10.00'),
            payment_method='cod',
            idempotency_key='test_cod_lifecycle_001',
            use_wallet_payment=False
        )
        
        assert order.status == 'cod_pending'
        
        # Transition to processing
        OrderStateMachine.validate_transition(order.status, 'processing')
        order.status = 'processing'
        order.save()
        
        assert order.status == 'processing'

    @pytest.mark.django_db
    def test_cod_transition_to_shipped(self, user, product):
        """
        Test that COD order can transition from processing to shipped.
        
        Given:
            - A COD order in 'processing' status
        When:
            - Order status is updated to 'shipped'
        Then:
            - Transition should be valid
            - Order status should be 'shipped'
        """
        # Create COD order and move to processing
        items_data = [{'product_id': product.id, 'quantity': 1}]
        success, order, error = AtomicOrderCreator.create_order(
            user=user,
            items_data=items_data,
            shipping_address="123 Test St, Cairo, Egypt",
            shipping_cost=Decimal('10.00'),
            payment_method='cod',
            idempotency_key='test_cod_lifecycle_002',
            use_wallet_payment=False
        )
        
        order.status = 'processing'
        order.save()
        
        # Transition to shipped
        OrderStateMachine.validate_transition(order.status, 'shipped')
        order.status = 'shipped'
        order.save()
        
        assert order.status == 'shipped'

    @pytest.mark.django_db
    def test_cod_transition_to_delivered(self, user, product):
        """
        Test that COD order can transition from shipped to delivered.
        
        Given:
            - A COD order in 'shipped' status
        When:
            - Order status is updated to 'delivered'
        Then:
            - Transition should be valid
            - Order status should be 'delivered'
            - For COD, delivery confirms payment collection
        """
        # Create COD order and move to shipped
        items_data = [{'product_id': product.id, 'quantity': 1}]
        success, order, error = AtomicOrderCreator.create_order(
            user=user,
            items_data=items_data,
            shipping_address="123 Test St, Cairo, Egypt",
            shipping_cost=Decimal('10.00'),
            payment_method='cod',
            idempotency_key='test_cod_lifecycle_003',
            use_wallet_payment=False
        )
        
        order.status = 'processing'
        order.save()
        order.status = 'shipped'
        order.save()
        
        # Transition to delivered and confirm payment
        success, delivered_order, error = AtomicOrderCreator.confirm_cod_delivery(
            order_id=order.id
        )
        
        assert success is True
        assert delivered_order.status == 'delivered'
        # For COD, delivery confirms payment
        assert delivered_order.payment_status is True, "COD orders should have payment_status=True after delivery"

    @pytest.mark.django_db
    def test_cod_transition_to_completed(self, user, product):
        """
        Test that COD order can transition from delivered to completed.
        
        Given:
            - A COD order in 'delivered' status
        When:
            - Order status is updated to 'completed'
        Then:
            - Transition should be valid
            - Order status should be 'completed'
        """
        # Create COD order and move to delivered
        items_data = [{'product_id': product.id, 'quantity': 1}]
        success, order, error = AtomicOrderCreator.create_order(
            user=user,
            items_data=items_data,
            shipping_address="123 Test St, Cairo, Egypt",
            shipping_cost=Decimal('10.00'),
            payment_method='cod',
            idempotency_key='test_cod_lifecycle_004',
            use_wallet_payment=False
        )
        
        order.status = 'processing'
        order.save()
        order.status = 'shipped'
        order.save()
        order.status = 'delivered'
        order.save()
        
        # Transition to completed
        OrderStateMachine.validate_transition(order.status, 'completed')
        order.status = 'completed'
        order.save()
        
        assert order.status == 'completed'
        assert OrderStateMachine.is_terminal('completed') is True

    @pytest.mark.django_db
    def test_cod_full_lifecycle(self, user, product):
        """
        Test complete COD order lifecycle.
        
        Given:
            - A verified user
            - A product with available stock
        When:
            - COD order is created
            - Order transitions through: cod_pending → processing → shipped → delivered → completed
        Then:
            - All transitions should be valid
            - Order should end in 'completed' status
        """
        items_data = [{'product_id': product.id, 'quantity': 1}]
        
        # Create COD order
        success, order, error = AtomicOrderCreator.create_order(
            user=user,
            items_data=items_data,
            shipping_address="123 Test St, Cairo, Egypt",
            shipping_cost=Decimal('10.00'),
            payment_method='cod',
            idempotency_key='test_cod_full_lifecycle_001',
            use_wallet_payment=False
        )
        
        assert order.status == 'cod_pending'
        
        # Transition through lifecycle
        transitions = ['processing', 'shipped', 'delivered']
        for new_status in transitions:
            OrderStateMachine.validate_transition(order.status, new_status)
            order.status = new_status
            order.save()
        
        # Confirm delivery and mark as paid/completed
        success, completed_order, error = AtomicOrderCreator.confirm_cod_delivery(
            order_id=order.id
        )
        
        assert success is True
        assert completed_order.status == 'completed'
        assert completed_order.payment_status is True


@pytest.mark.django_db
class TestCODCancellation:
    """Test COD cancellation path."""

    @pytest.mark.django_db
    def test_cod_order_can_be_cancelled(self, user, product):
        """
        Test that COD orders can be cancelled from cod_pending status.
        
        Given:
            - A COD order in 'cod_pending' status
        When:
            - Order is cancelled
        Then:
            - Transition should be valid
            - Order status should be 'cancelled'
            - Stock should be released
        """
        # Create COD order
        items_data = [{'product_id': product.id, 'quantity': 1}]
        success, order, error = AtomicOrderCreator.create_order(
            user=user,
            items_data=items_data,
            shipping_address="123 Test St, Cairo, Egypt",
            shipping_cost=Decimal('10.00'),
            payment_method='cod',
            idempotency_key='test_cod_cancel_001',
            use_wallet_payment=False
        )
        
        initial_stock = product.stock_quantity
        
        # Cancel order
        success, cancelled_order, error = AtomicOrderCreator.cancel_order(
            order_id=order.id,
            user=user
        )
        
        assert success is True
        assert cancelled_order.status == 'cancelled'
        
        # Verify stock was released
        product.refresh_from_db()
        assert product.stock_quantity == initial_stock + 1

    @pytest.mark.django_db
    def test_cod_order_cannot_be_cancelled_after_shipped(self, user, product):
        """
        Test that COD orders cannot be cancelled after shipped status.
        
        Given:
            - A COD order in 'shipped' status
        When:
            - Attempt to cancel order
        Then:
            - Cancellation should fail
            - Order status should remain 'shipped'
        """
        # Create COD order and move to shipped
        items_data = [{'product_id': product.id, 'quantity': 1}]
        success, order, error = AtomicOrderCreator.create_order(
            user=user,
            items_data=items_data,
            shipping_address="123 Test St, Cairo, Egypt",
            shipping_cost=Decimal('10.00'),
            payment_method='cod',
            idempotency_key='test_cod_cancel_002',
            use_wallet_payment=False
        )
        
        order.status = 'processing'
        order.save()
        order.status = 'shipped'
        order.save()
        
        # Try to cancel - should fail
        success, cancelled_order, error = AtomicOrderCreator.cancel_order(
            order_id=order.id,
            user=user
        )
        
        assert success is False
        assert 'cannot cancel' in error.lower()
        
        # Verify order status unchanged
        order.refresh_from_db()
        assert order.status == 'shipped'

    @pytest.mark.django_db
    def test_cod_cancellation_from_processing(self, user, product):
        """
        Test that COD orders can be cancelled from processing status.
        
        Given:
            - A COD order in 'processing' status
        When:
            - Order is cancelled
        Then:
            - Transition should be valid
            - Order status should be 'cancelled'
            - Stock should be released
        """
        # Create COD order and move to processing
        items_data = [{'product_id': product.id, 'quantity': 1}]
        success, order, error = AtomicOrderCreator.create_order(
            user=user,
            items_data=items_data,
            shipping_address="123 Test St, Cairo, Egypt",
            shipping_cost=Decimal('10.00'),
            payment_method='cod',
            idempotency_key='test_cod_cancel_003',
            use_wallet_payment=False
        )
        
        order.status = 'processing'
        order.save()
        
        initial_stock = product.stock_quantity
        
        # Cancel order
        success, cancelled_order, error = AtomicOrderCreator.cancel_order(
            order_id=order.id,
            user=user
        )
        
        assert success is True
        assert cancelled_order.status == 'cancelled'
        
        # Verify stock was released
        product.refresh_from_db()
        assert product.stock_quantity == initial_stock + 1

    @pytest.mark.django_db
    def test_cod_cancellation_does_not_require_refund(self, user, product):
        """
        Test that COD order cancellation does not trigger refund.
        
        Given:
            - A COD order in 'cod_pending' status
        When:
            - Order is cancelled
        Then:
            - Order status should be 'cancelled'
            - No refund transaction should be created (COD has no payment to refund)
        """
        from wallet.models import Transaction
        
        # Create COD order
        items_data = [{'product_id': product.id, 'quantity': 1}]
        success, order, error = AtomicOrderCreator.create_order(
            user=user,
            items_data=items_data,
            shipping_address="123 Test St, Cairo, Egypt",
            shipping_cost=Decimal('10.00'),
            payment_method='cod',
            idempotency_key='test_cod_cancel_004',
            use_wallet_payment=False
        )
        
        # Cancel order
        success, cancelled_order, error = AtomicOrderCreator.cancel_order(
            order_id=order.id,
            user=user
        )
        
        assert success is True
        assert cancelled_order.status == 'cancelled'
        
        # Verify no refund transaction was created
        refund_txs = Transaction.objects.filter(
            reference_id=str(order.id),
            transaction_type='refund'
        )
        assert refund_txs.count() == 0, "COD cancellation should not create refund transaction"
