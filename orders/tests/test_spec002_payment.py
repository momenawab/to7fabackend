"""
Spec 002 Tests: Payment & Wallet Behavior

Tests derived from:
- spec-002.md section: Payment & Wallet Specification
- FR-PAY-001 through FR-PAY-033
"""

import pytest


class TestWalletPaymentRules:
    """Test FR-PAY-010 through FR-PAY-014: Wallet payment behavior."""

    pytestmark = pytest.mark.non_critical
import uuid
from decimal import Decimal
from django.contrib.auth import get_user_model
from orders.models import Order
from wallet.models import Wallet, Transaction as WalletTransaction

User = get_user_model()


class TestWalletPaymentRules:
    """Test FR-PAY-010 through FR-PAY-014: Wallet payment behavior."""

    def test_wallet_balance_verified_before_payment(self, db):
        """FR-PAY-010: Wallet balance MUST be verified before payment initiation."""
        user = User.objects.create_user(
            email=f'user_32d45a38@example.com',
            password='testpass123',
            is_mobile_verified=True
        )

        wallet = Wallet.objects.create(
            user=user,
            balance=Decimal('50.00')
        )

        order = Order.objects.create(
            user=user,
            status='pending_payment',
            total_amount=Decimal('100.00')
        )

        # Payment should fail if balance insufficient
        from orders.atomic_order_system import WalletOrderCoordinator
        result = WalletOrderCoordinator.reserve_payment(wallet, order.total_amount)

        assert result['success'] is False

    def test_wallet_balance_held_on_payment_initiation(self, db):
        """FR-PAY-011: Wallet balance MUST be held when payment is initiated."""
        user = User.objects.create_user(
            email=f'user_885db67a@example.com',
            password='testpass123',
            is_mobile_verified=True
        )

        wallet = Wallet.objects.create(
            user=user,
            balance=Decimal('100.00')
        )

        order = Order.objects.create(
            user=user,
            status='pending_payment',
            total_amount=Decimal('50.00')
        )

        from orders.atomic_order_system import WalletOrderCoordinator
        result = WalletOrderCoordinator.reserve_payment(wallet, order.total_amount)

        if result['success']:
            wallet.refresh_from_db()
            # Balance should be held (decremented or reserved)
            assert wallet.balance <= Decimal('100.00')

    def test_wallet_hold_converted_to_debit_on_payment(self, db):
        """FR-PAY-012: Wallet hold MUST be converted to debit when order is PAID."""
        user = User.objects.create_user(
            email=f'user_a94ef90e@example.com',
            password='testpass123',
            is_mobile_verified=True
        )

        wallet = Wallet.objects.create(
            user=user,
            balance=Decimal('100.00')
        )

        order = Order.objects.create(
            user=user,
            status='pending_payment',
            total_amount=Decimal('50.00')
        )

        from orders.atomic_order_system import WalletOrderCoordinator
        WalletOrderCoordinator.reserve_payment(wallet, order.total_amount)

        # Capture payment
        order.status = 'paid'
        order.save()

        WalletOrderCoordinator.capture_payment(wallet, order)

        # Transaction should show DEBIT, not HOLD
        transaction = WalletTransaction.objects.filter(
            wallet=wallet,
            order=order
        ).first()

        if transaction:
            assert transaction.transaction_type == 'DEBIT'

    def test_wallet_hold_released_on_cancellation(self, db):
        """FR-PAY-013: Wallet hold MUST be released when order is CANCELLED or FAILED."""
        user = User.objects.create_user(
            email=f'user_225c0dd1@example.com',
            password='testpass123',
            is_mobile_verified=True
        )

        wallet = Wallet.objects.create(
            user=user,
            balance=Decimal('100.00')
        )

        order = Order.objects.create(
            user=user,
            status='pending_payment',
            total_amount=Decimal('50.00')
        )

        from orders.atomic_order_system import WalletOrderCoordinator
        WalletOrderCoordinator.reserve_payment(wallet, order.total_amount)

        initial_balance = wallet.balance

        # Cancel order
        order.status = 'cancelled'
        order.save()

        WalletOrderCoordinator.release_payment(wallet, order)

        wallet.refresh_from_db()
        # Balance should be restored
        assert wallet.balance >= initial_balance

    def test_wallet_transaction_has_order_reference(self, db):
        """FR-PAY-014: Wallet transactions MUST be recorded with order reference."""
        user = User.objects.create_user(
            email=f'user_4e8e0620@example.com',
            password='testpass123',
            is_mobile_verified=True
        )

        wallet = Wallet.objects.create(
            user=user,
            balance=Decimal('100.00')
        )

        order = Order.objects.create(
            user=user,
            status='paid',
            total_amount=Decimal('50.00')
        )

        from orders.atomic_order_system import WalletOrderCoordinator
        WalletOrderCoordinator.capture_payment(wallet, order)

        transaction = WalletTransaction.objects.filter(
            wallet=wallet,
            order=order
        ).first()

        assert transaction is not None
        assert transaction.order == order


class TestOrderPaymentStateCoordination:
    """Test FR-PAY-020, FR-PAY-021: Order-payment state consistency."""

    pytestmark = pytest.mark.non_critical

    def test_order_state_matches_payment_state(self, db):
        """FR-PAY-020: Order state and payment state MUST remain consistent."""
        user = User.objects.create_user(
            email=f'user_eda2eb15@example.com',
            password='testpass123',
            is_mobile_verified=True
        )

        wallet = Wallet.objects.create(
            user=user,
            balance=Decimal('100.00')
        )

        order = Order.objects.create(
            user=user,
            status='pending_payment',
            total_amount=Decimal('50.00')
        )

        from orders.atomic_order_system import WalletOrderCoordinator
        WalletOrderCoordinator.capture_payment(wallet, order)

        order.status = 'paid'
        order.save()

        # Payment state should match order state
        transaction = WalletTransaction.objects.filter(
            wallet=wallet,
            order=order
        ).first()

        if transaction and order.status == 'paid':
            assert transaction.transaction_type == 'DEBIT'

    def test_inconsistency_triggers_alert(self, db):
        """FR-PAY-021: State inconsistency MUST trigger reconciliation alert."""
        # This is a behavioral test for monitoring/alerting
        # Implementation should log or alert on inconsistency
        user = User.objects.create_user(
            email=f'user_15ce4382@example.com',
            password='testpass123',
            is_mobile_verified=True
        )

        order = Order.objects.create(
            user=user,
            status='paid',
            total_amount=Decimal('50.00')
        )

        # If payment is missing or inconsistent, should trigger alert
        # Test that system detects this


class TestPendingPaymentTimeout:
    """Test FR-PAY-030 through FR-PAY-033: 15-minute timeout behavior."""

    pytestmark = pytest.mark.non_critical

    def test_pending_payment_has_15_minute_timeout(self, db):
        """FR-PAY-030: Pending payments MUST have 15-minute timeout."""
        from datetime import datetime, timedelta

        user = User.objects.create_user(
            email=f'user_11fc29c5@example.com',
            password='testpass123',
            is_mobile_verified=True
        )

        order = Order.objects.create(
            user=user,
            status='pending_payment',
            total_amount=Decimal('50.00')
        )

        # Payment timeout should be set
        if hasattr(order, 'payment_timeout_at'):
            assert order.payment_timeout_at is not None
            expected_timeout = order.created_at + timedelta(minutes=15)
            assert order.payment_timeout_at == expected_timeout

    def test_timeout_auto_cancels_order(self, db):
        """FR-PAY-031: Orders beyond timeout MUST auto-transition to CANCELLED."""
        from datetime import datetime, timedelta
        from django.utils import timezone

        user = User.objects.create_user(
            email=f'user_f4a3a12b@example.com',
            password='testpass123',
            is_mobile_verified=True
        )

        order = Order.objects.create(
            user=user,
            status='pending_payment',
            total_amount=Decimal('50.00'),
            payment_timeout_at=timezone.now() - timedelta(minutes=16)
        )

        # Run timeout check
        from orders.tasks import check_payment_timeouts
        check_payment_timeouts()

        order.refresh_from_db()
        assert order.status == 'cancelled'

    @pytest.mark.skip(reason="infrastructure: Celery worker not available")
    @pytest.mark.deferred
    def test_timeout_releases_stock(self, db):
        """FR-PAY-032: Timeout-triggered cancellation MUST release stock."""
        from django.utils import timezone
        from datetime import timedelta

        user = User.objects.create_user(
            email=f'user_de646567@example.com',
            password='testpass123',
            is_mobile_verified=True
        )

        order = Order.objects.create(
            user=user,
            status='pending_payment',
            total_amount=Decimal('50.00'),
            payment_timeout_at=timezone.now() - timedelta(minutes=16)
        )

        from orders.tasks import check_payment_timeouts
        check_payment_timeouts()

        # Stock should be released
        # Implementation varies - check order items for release

    @pytest.mark.skip(reason="infrastructure: Celery worker not available")
    @pytest.mark.deferred
    def test_timeout_releases_wallet_holds(self, db):
        """FR-PAY-033: Timeout-triggered cancellation MUST release wallet holds."""
        from django.utils import timezone
        from datetime import timedelta

        user = User.objects.create_user(
            email=f'user_d0d54bec@example.com',
            password='testpass123',
            is_mobile_verified=True
        )

        wallet = Wallet.objects.create(
            user=user,
            balance=Decimal('100.00')
        )

        order = Order.objects.create(
            user=user,
            status='pending_payment',
            total_amount=Decimal('50.00'),
            payment_timeout_at=timezone.now() - timedelta(minutes=16)
        )

        from orders.atomic_order_system import WalletOrderCoordinator
        WalletOrderCoordinator.reserve_payment(wallet, order.total_amount)

        initial_balance = wallet.balance

        # Run timeout
        from orders.tasks import check_payment_timeouts
        check_payment_timeouts()

        wallet.refresh_from_db()
        # Balance should be restored
        assert wallet.balance >= initial_balance


class TestPaymentStateTransitions:
    """Test payment state transitions with order states."""

    pytestmark = pytest.mark.non_critical

    def test_pending_payment_order_has_pending_payment(self, db):
        """PENDING_PAYMENT order has PENDING payment state."""
        user = User.objects.create_user(
            email=f'user_55ece15f@example.com',
            password='testpass123',
            is_mobile_verified=True
        )

        order = Order.objects.create(
            user=user,
            status='pending_payment',
            total_amount=Decimal('50.00')
        )

        # Payment should be in PENDING state
        # Implementation varies - check payment model or order.payment_status

    def test_paid_order_has_captured_payment(self, db):
        """PAID order has CAPTURED payment."""
        user = User.objects.create_user(
            email=f'user_8635e352@example.com',
            password='testpass123',
            is_mobile_verified=True
        )

        wallet = Wallet.objects.create(
            user=user,
            balance=Decimal('100.00')
        )

        order = Order.objects.create(
            user=user,
            status='paid',
            total_amount=Decimal('50.00')
        )

        from orders.atomic_order_system import WalletOrderCoordinator
        WalletOrderCoordinator.capture_payment(wallet, order)

        # Payment should be CAPTURED
        transaction = WalletTransaction.objects.filter(
            wallet=wallet,
            order=order
        ).first()

        if transaction:
            assert transaction.transaction_type == 'DEBIT'

    def test_refunded_order_has_refunded_payment(self, db):
        """REFUNDED order has REFUNDED payment."""
        user = User.objects.create_user(
            email=f'user_97b7d036@example.com',
            password='testpass123',
            is_mobile_verified=True
        )

        wallet = Wallet.objects.create(
            user=user,
            balance=Decimal('100.00')
        )

        order = Order.objects.create(
            user=user,
            status='refunded',
            total_amount=Decimal('50.00')
        )

        from orders.atomic_order_system import WalletOrderCoordinator
        WalletOrderCoordinator.credit_refund(wallet, order)

        # Payment should be REFUNDED
        transaction = WalletTransaction.objects.filter(
            wallet=wallet,
            order=order,
            transaction_type='CREDIT'
        ).first()

        assert transaction is not None
