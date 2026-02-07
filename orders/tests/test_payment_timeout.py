"""
Tests for Payment Timeout (User Story 3)

Tests cover:
- payment_timeout_at calculation (15 minutes from creation)
- Timeout task cancelling expired orders
- Stock release on timeout cancellation
- Wallet hold release on timeout cancellation
"""

import pytest
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from orders.models import Order, OrderItem
from orders.atomic_order_system import AtomicOrderCreator
from orders.tasks import check_payment_timeouts
from products.models import Product

User = get_user_model()


@pytest.mark.django_db
class TestPaymentTimeoutCalculation:
    """Test payment_timeout_at calculation (15 minutes from creation)."""

    @pytest.mark.django_db
    def test_wallet_order_has_payment_timeout(self, user, product):
        """
        Test that wallet orders have payment_timeout_at set to 15 minutes from creation.
        
        Given:
            - A verified user
            - A product with available stock
            - payment_method = 'wallet'
        When:
            - Order is created
        Then:
            - Order status should be 'pending_payment'
            - payment_timeout_at should be set to approximately 15 minutes from now
        """
        items_data = [
            {
                'product_id': product.id,
                'quantity': 1,
            }
        ]
        
        before_creation = timezone.now()
        
        success, order, error = AtomicOrderCreator.create_order(
            user=user,
            items_data=items_data,
            shipping_address="123 Test St, Cairo, Egypt",
            shipping_cost=Decimal('10.00'),
            payment_method='wallet',
            idempotency_key='test_timeout_001',
            use_wallet_payment=False
        )
        
        after_creation = timezone.now()
        
        assert success is True
        assert order is not None
        assert order.status == 'pending_payment'
        assert order.payment_timeout_at is not None
        
        # Verify timeout is approximately 15 minutes from creation time
        expected_min = before_creation + timedelta(minutes=15)
        expected_max = after_creation + timedelta(minutes=15)
        
        assert expected_min <= order.payment_timeout_at <= expected_max, \
            f"payment_timeout_at ({order.payment_timeout_at}) should be ~15 minutes from creation"

    @pytest.mark.django_db
    def test_instapay_order_has_payment_timeout(self, user, product):
        """
        Test that InstaPay orders have payment_timeout_at set.
        
        Given:
            - A verified user
            - A product with available stock
            - payment_method = 'instapay'
        When:
            - Order is created
        Then:
            - Order status should be 'pending_payment'
            - payment_timeout_at should be set to 15 minutes from now
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
            payment_method='instapay',
            idempotency_key='test_timeout_002',
            use_wallet_payment=False
        )
        
        assert success is True
        assert order is not None
        assert order.status == 'pending_payment'
        assert order.payment_timeout_at is not None
        
        # Verify timeout is approximately 15 minutes from creation time
        expected_timeout = timezone.now() + timedelta(minutes=15)
        time_diff = abs((order.payment_timeout_at - expected_timeout).total_seconds())
        assert time_diff < 5, "Timeout should be within 5 seconds of expected time"

    @pytest.mark.django_db
    def test_credit_card_order_has_payment_timeout(self, user, product):
        """
        Test that credit card orders have payment_timeout_at set.
        
        Given:
            - A verified user
            - A product with available stock
            - payment_method = 'credit_card'
        When:
            - Order is created
        Then:
            - Order status should be 'pending_payment'
            - payment_timeout_at should be set to 15 minutes from now
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
            payment_method='credit_card',
            idempotency_key='test_timeout_003',
            use_wallet_payment=False
        )
        
        assert success is True
        assert order is not None
        assert order.status == 'pending_payment'
        assert order.payment_timeout_at is not None
        
        # Verify timeout is approximately 15 minutes from creation time
        expected_timeout = timezone.now() + timedelta(minutes=15)
        time_diff = abs((order.payment_timeout_at - expected_timeout).total_seconds())
        assert time_diff < 5, "Timeout should be within 5 seconds of expected time"

    @pytest.mark.django_db
    def test_cod_order_has_no_payment_timeout(self, user, product):
        """
        Test that COD orders do not have payment_timeout_at set.
        
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
            idempotency_key='test_timeout_004',
            use_wallet_payment=False
        )
        
        assert success is True
        assert order is not None
        assert order.status == 'cod_pending'
        assert order.payment_timeout_at is None, "COD orders should not have payment timeout"


@pytest.mark.django_db
class TestTimeoutTaskCancelsExpiredOrders:
    """Test timeout task cancelling expired orders."""

    @pytest.mark.django_db
    def test_timeout_task_cancels_expired_order(self, user, product):
        """
        Test that the timeout task cancels orders past their payment timeout.
        
        Given:
            - An order in 'pending_payment' status
            - payment_timeout_at is in the past
        When:
            - check_payment_timeouts task is executed
        Then:
            - Order should be cancelled
            - Order status should be 'cancelled'
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
            idempotency_key='test_timeout_task_001',
            use_wallet_payment=False
        )
        
        assert order.status == 'pending_payment'
        
        # Manually set payment_timeout_at to the past
        order.payment_timeout_at = timezone.now() - timedelta(minutes=1)
        order.save()
        
        # Run the timeout task
        check_payment_timeouts()
        
        # Verify order was cancelled
        order.refresh_from_db()
        assert order.status == 'cancelled'

    @pytest.mark.django_db
    def test_timeout_task_does_not_cancel_future_orders(self, user, product):
        """
        Test that the timeout task does not cancel orders with future timeouts.
        
        Given:
            - An order in 'pending_payment' status
            - payment_timeout_at is in the future
        When:
            - check_payment_timeouts task is executed
        Then:
            - Order should remain in 'pending_payment' status
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
            idempotency_key='test_timeout_task_002',
            use_wallet_payment=False
        )
        
        assert order.status == 'pending_payment'
        original_status = order.status
        
        # Ensure payment_timeout_at is in the future
        order.payment_timeout_at = timezone.now() + timedelta(minutes=15)
        order.save()
        
        # Run the timeout task
        check_payment_timeouts()
        
        # Verify order was not cancelled
        order.refresh_from_db()
        assert order.status == original_status, "Order with future timeout should not be cancelled"

    @pytest.mark.django_db
    def test_timeout_task_skips_non_pending_orders(self, user, product):
        """
        Test that the timeout task skips orders not in pending_payment status.
        
        Given:
            - An order in 'paid' status (already paid)
            - payment_timeout_at is in the past
        When:
            - check_payment_timeouts task is executed
        Then:
            - Order should remain in 'paid' status (not cancelled)
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
            idempotency_key='test_timeout_task_003',
            use_wallet_payment=False
        )
        
        # Move order to paid status
        order.status = 'paid'
        order.payment_timeout_at = timezone.now() - timedelta(minutes=1)
        order.save()
        
        # Run the timeout task
        check_payment_timeouts()
        
        # Verify order was not cancelled
        order.refresh_from_db()
        assert order.status == 'paid', "Paid orders should not be cancelled by timeout task"

    @pytest.mark.django_db
    def test_timeout_task_handles_multiple_expired_orders(self, user, product):
        """
        Test that the timeout task cancels multiple expired orders.
        
        Given:
            - Multiple orders in 'pending_payment' status
            - All have payment_timeout_at in the past
        When:
            - check_payment_timeouts task is executed
        Then:
            - All expired orders should be cancelled
        """
        # Create first expired order
        items_data_1 = [{'product_id': product.id, 'quantity': 1}]
        success, order1, error = AtomicOrderCreator.create_order(
            user=user,
            items_data=items_data_1,
            shipping_address="123 Test St, Cairo, Egypt",
            shipping_cost=Decimal('10.00'),
            payment_method='wallet',
            idempotency_key='test_timeout_task_004_1',
            use_wallet_payment=False
        )
        order1.payment_timeout_at = timezone.now() - timedelta(minutes=1)
        order1.save()
        
        # Create second expired order
        items_data_2 = [{'product_id': product.id, 'quantity': 1}]
        success, order2, error = AtomicOrderCreator.create_order(
            user=user,
            items_data=items_data_2,
            shipping_address="456 Test St, Cairo, Egypt",
            shipping_cost=Decimal('10.00'),
            payment_method='wallet',
            idempotency_key='test_timeout_task_004_2',
            use_wallet_payment=False
        )
        order2.payment_timeout_at = timezone.now() - timedelta(minutes=1)
        order2.save()
        
        # Run the timeout task
        check_payment_timeouts()
        
        # Verify both orders were cancelled
        order1.refresh_from_db()
        order2.refresh_from_db()
        assert order1.status == 'cancelled'
        assert order2.status == 'cancelled'


@pytest.mark.django_db
class TestStockReleaseOnTimeoutCancellation:
    """Test stock release on timeout cancellation."""

    @pytest.mark.django_db
    def test_timeout_cancellation_releases_stock(self, user, product):
        """
        Test that timeout cancellation releases reserved stock.
        
        Given:
            - An order in 'pending_payment' status
            - Stock was reserved for the order
            - payment_timeout_at is in the past
        When:
            - check_payment_timeouts task is executed
        Then:
            - Order should be cancelled
            - Stock should be released (returned to available stock)
        """
        initial_stock = product.stock_quantity
        
        items_data = [
            {
                'product_id': product.id,
                'quantity': 2,
            }
        ]
        
        success, order, error = AtomicOrderCreator.create_order(
            user=user,
            items_data=items_data,
            shipping_address="123 Test St, Cairo, Egypt",
            shipping_cost=Decimal('10.00'),
            payment_method='wallet',
            idempotency_key='test_stock_release_001',
            use_wallet_payment=False
        )
        
        # Verify stock was reserved (decreased)
        product.refresh_from_db()
        assert product.stock_quantity == initial_stock - 2
        
        # Set timeout to past and run task
        order.payment_timeout_at = timezone.now() - timedelta(minutes=1)
        order.save()
        check_payment_timeouts()
        
        # Verify stock was released
        product.refresh_from_db()
        assert product.stock_quantity == initial_stock, \
            f"Stock should be released to initial value {initial_stock}, got {product.stock_quantity}"

    @pytest.mark.django_db
    def test_timeout_cancellation_updates_reservation_status(self, user, product):
        """
        Test that timeout cancellation updates reservation_status to 'released'.
        
        Given:
            - An order in 'pending_payment' status
            - OrderItem has reservation_status = 'reserved'
            - payment_timeout_at is in the past
        When:
            - check_payment_timeouts task is executed
        Then:
            - Order should be cancelled
            - OrderItem reservation_status should be 'released'
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
            idempotency_key='test_reservation_status_001',
            use_wallet_payment=False
        )
        
        # Verify initial reservation status
        order_item = order.items.first()
        assert order_item.reservation_status == 'reserved'
        
        # Set timeout to past and run task
        order.payment_timeout_at = timezone.now() - timedelta(minutes=1)
        order.save()
        check_payment_timeouts()
        
        # Verify reservation status was updated
        order_item.refresh_from_db()
        assert order_item.reservation_status == 'released', \
            "Reservation status should be 'released' after timeout cancellation"


@pytest.mark.django_db
class TestWalletHoldReleaseOnTimeoutCancellation:
    """Test wallet hold release on timeout cancellation."""

    @pytest.mark.django_db
    def test_timeout_cancellation_releases_wallet_hold(self, user, product):
        """
        Test that timeout cancellation releases wallet hold for wallet-paid orders.
        
        Given:
            - An order created with wallet payment
            - Wallet hold was placed on the order amount
            - payment_timeout_at is in the past
        When:
            - check_payment_timeouts task is executed
        Then:
            - Order should be cancelled
            - Wallet balance should be restored (hold released)
        """
        from wallet.models import Wallet, Transaction
        
        # Ensure user has a wallet with sufficient balance
        wallet, created = Wallet.objects.get_or_create(user=user)
        wallet.balance = Decimal('1000.00')
        wallet.save()
        
        initial_balance = wallet.balance
        
        items_data = [
            {
                'product_id': product.id,
                'quantity': 1,
            }
        ]
        
        # Create order with wallet payment
        success, order, error = AtomicOrderCreator.create_order(
            user=user,
            items_data=items_data,
            shipping_address="123 Test St, Cairo, Egypt",
            shipping_cost=Decimal('10.00'),
            payment_method='wallet',
            idempotency_key='test_wallet_release_001',
            use_wallet_payment=True
        )
        
        # Verify wallet was debited (hold placed)
        wallet.refresh_from_db()
        assert wallet.balance < initial_balance, "Wallet should be debited for order"
        balance_after_order = wallet.balance
        
        # Set timeout to past and run task
        order.payment_timeout_at = timezone.now() - timedelta(minutes=1)
        order.save()
        check_payment_timeouts()
        
        # Verify wallet balance was restored
        wallet.refresh_from_db()
        assert wallet.balance == initial_balance, \
            f"Wallet balance should be restored to {initial_balance}, got {wallet.balance}"

    @pytest.mark.django_db
    def test_timeout_cancellation_creates_refund_transaction(self, user, product):
        """
        Test that timeout cancellation creates a refund transaction for wallet-paid orders.
        
        Given:
            - An order created with wallet payment
            - Wallet hold was placed
            - payment_timeout_at is in the past
        When:
            - check_payment_timeouts task is executed
        Then:
            - Order should be cancelled
            - A refund transaction should be created
            - Transaction type should be 'refund'
        """
        from wallet.models import Wallet, Transaction
        
        # Ensure user has a wallet with sufficient balance
        wallet, created = Wallet.objects.get_or_create(user=user)
        wallet.balance = Decimal('1000.00')
        wallet.save()
        
        items_data = [
            {
                'product_id': product.id,
                'quantity': 1,
            }
        ]
        
        # Create order with wallet payment
        success, order, error = AtomicOrderCreator.create_order(
            user=user,
            items_data=items_data,
            shipping_address="123 Test St, Cairo, Egypt",
            shipping_cost=Decimal('10.00'),
            payment_method='wallet',
            idempotency_key='test_refund_tx_001',
            use_wallet_payment=True
        )
        
        # Count refund transactions before timeout
        refund_txs_before = Transaction.objects.filter(
            wallet=wallet,
            transaction_type='refund'
        ).count()
        
        # Set timeout to past and run task
        order.payment_timeout_at = timezone.now() - timedelta(minutes=1)
        order.save()
        check_payment_timeouts()
        
        # Verify refund transaction was created
        refund_txs_after = Transaction.objects.filter(
            wallet=wallet,
            transaction_type='refund'
        ).count()
        
        assert refund_txs_after == refund_txs_before + 1, \
            "A refund transaction should be created on timeout cancellation"

    @pytest.mark.django_db
    def test_timeout_cancellation_for_non_wallet_orders(self, user, product):
        """
        Test that timeout cancellation works correctly for non-wallet payment methods.
        
        Given:
            - An order created with instapay payment
            - No wallet hold was placed
            - payment_timeout_at is in the past
        When:
            - check_payment_timeouts task is executed
        Then:
            - Order should be cancelled
            - No refund transaction should be created (no wallet payment)
        """
        from wallet.models import Wallet, Transaction
        
        # Ensure user has a wallet
        wallet, created = Wallet.objects.get_or_create(user=user)
        wallet.balance = Decimal('1000.00')
        wallet.save()
        
        initial_balance = wallet.balance
        
        items_data = [
            {
                'product_id': product.id,
                'quantity': 1,
            }
        ]
        
        # Create order with instapay payment (not wallet)
        success, order, error = AtomicOrderCreator.create_order(
            user=user,
            items_data=items_data,
            shipping_address="123 Test St, Cairo, Egypt",
            shipping_cost=Decimal('10.00'),
            payment_method='instapay',
            idempotency_key='test_non_wallet_001',
            use_wallet_payment=False
        )
        
        # Count refund transactions before timeout
        refund_txs_before = Transaction.objects.filter(
            wallet=wallet,
            transaction_type='refund'
        ).count()
        
        # Set timeout to past and run task
        order.payment_timeout_at = timezone.now() - timedelta(minutes=1)
        order.save()
        check_payment_timeouts()
        
        # Verify order was cancelled
        order.refresh_from_db()
        assert order.status == 'cancelled'
        
        # Verify wallet balance unchanged (no refund for non-wallet payment)
        wallet.refresh_from_db()
        assert wallet.balance == initial_balance
        
        # Verify no refund transaction was created
        refund_txs_after = Transaction.objects.filter(
            wallet=wallet,
            transaction_type='refund'
        ).count()
        assert refund_txs_after == refund_txs_before, \
            "No refund transaction should be created for non-wallet payment"
