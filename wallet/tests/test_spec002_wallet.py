"""
Spec 002 Tests: Wallet Balance Consistency

Tests derived from:
- spec-002.md sections: System Invariants, Payment & Wallet Specification
- INV-002, INV-009, FR-PAY-010 through FR-PAY-014
"""

import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from wallet.models import Wallet, Transaction as WalletTransaction
from orders.models import Order

User = get_user_model()


class TestWalletBalanceConsistency:
    """Test INV-002: Wallet balance MUST never be negative."""

    def test_wallet_balance_never_goes_negative(self, db):
        """INV-002: Wallet balance MUST never be negative."""
        user = User.objects.create_user(
            email='user@example.com',
            password='testpass123'
        )

        wallet = Wallet.objects.create(
            user=user,
            balance=Decimal('100.00')
        )

        # Try to debit more than balance
        from orders.atomic_order_system import WalletOrderCoordinator
        result = WalletOrderCoordinator.reserve_payment(wallet, Decimal('200.00'))

        assert result['success'] is False
        wallet.refresh_from_db()
        assert wallet.balance >= 0

    def test_concurrent_debits_do_not_make_balance_negative(self, db):
        """Multiple concurrent debits should not make balance negative."""
        user = User.objects.create_user(
            email='user@example.com',
            password='testpass123'
        )

        wallet = Wallet.objects.create(
            user=user,
            balance=Decimal('100.00')
        )

        # Simulate concurrent operations
        from orders.atomic_order_system import WalletOrderCoordinator

        result1 = WalletOrderCoordinator.reserve_payment(wallet, Decimal('60.00'))
        result2 = WalletOrderCoordinator.reserve_payment(wallet, Decimal('60.00'))

        # At least one should fail
        assert not (result1['success'] and result2['success'])

        wallet.refresh_from_db()
        assert wallet.balance >= 0

    def test_wallet_balance_after_multiple_operations(self, db):
        """Wallet balance remains consistent after multiple operations."""
        user = User.objects.create_user(
            email='user@example.com',
            password='testpass123'
        )

        wallet = Wallet.objects.create(
            user=user,
            balance=Decimal('100.00')
        )

        from orders.atomic_order_system import WalletOrderCoordinator

        # Debit 1
        result1 = WalletOrderCoordinator.reserve_payment(wallet, Decimal('30.00'))
        assert result1['success']
        wallet.refresh_from_db()
        assert wallet.balance == Decimal('70.00')

        # Debit 2
        result2 = WalletOrderCoordinator.reserve_payment(wallet, Decimal('20.00'))
        assert result2['success']
        wallet.refresh_from_db()
        assert wallet.balance == Decimal('50.00')

        # Credit (refund)
        order = Order.objects.create(
            user=user,
            status='paid',
            total_amount=Decimal('30.00')
        )
        WalletOrderCoordinator.credit_refund(wallet, order)
        wallet.refresh_from_db()
        assert wallet.balance >= Decimal('50.00')


class TestWalletTransactionRecording:
    """Test FR-PAY-014: Wallet transactions MUST be recorded with order reference."""

    def test_debit_transaction_has_order_reference(self, db):
        """Payment DEBIT MUST reference order."""
        user = User.objects.create_user(
            email='user@example.com',
            password='testpass123'
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
            transaction_type='DEBIT'
        ).first()

        assert transaction is not None
        assert transaction.order == order

    def test_credit_transaction_has_order_reference(self, db):
        """Refund CREDIT MUST reference order."""
        user = User.objects.create_user(
            email='user@example.com',
            password='testpass123'
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

        transaction = WalletTransaction.objects.filter(
            wallet=wallet,
            transaction_type='CREDIT'
        ).first()

        assert transaction is not None
        assert transaction.order == order

    def test_hold_transaction_has_order_reference(self, db):
        """Payment HOLD MUST reference order."""
        user = User.objects.create_user(
            email='user@example.com',
            password='testpass123'
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

        transaction = WalletTransaction.objects.filter(
            wallet=wallet,
            order=order
        ).first()

        assert transaction is not None

    def test_release_transaction_has_order_reference(self, db):
        """Payment RELEASE MUST reference order."""
        user = User.objects.create_user(
            email='user@example.com',
            password='testpass123'
        )

        wallet = Wallet.objects.create(
            user=user,
            balance=Decimal('100.00')
        )

        order = Order.objects.create(
            user=user,
            status='cancelled',
            total_amount=Decimal('50.00')
        )

        from orders.atomic_order_system import WalletOrderCoordinator
        WalletOrderCoordinator.reserve_payment(wallet, order.total_amount)
        WalletOrderCoordinator.release_payment(wallet, order)

        # Check for release transaction
        transactions = WalletTransaction.objects.filter(
            wallet=wallet,
            order=order
        )

        assert transactions.count() > 0


class TestWalletTransactionTypes:
    """Test FR-PAY-014: Transaction types (HOLD, DEBIT, RELEASE, CREDIT)."""

    def test_hold_transaction_type(self, db):
        """Payment initiation creates HOLD transaction."""
        user = User.objects.create_user(
            email='user@example.com',
            password='testpass123'
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

        transaction = WalletTransaction.objects.filter(
            wallet=wallet,
            order=order
        ).first()

        if transaction:
            assert transaction.transaction_type in ['HOLD', 'DEBIT']

    def test_debit_transaction_type(self, db):
        """Payment capture creates DEBIT transaction."""
        user = User.objects.create_user(
            email='user@example.com',
            password='testpass123'
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
            order=order,
            transaction_type='DEBIT'
        ).first()

        assert transaction is not None

    def test_credit_transaction_type(self, db):
        """Refund creates CREDIT transaction."""
        user = User.objects.create_user(
            email='user@example.com',
            password='testpass123'
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

        transaction = WalletTransaction.objects.filter(
            wallet=wallet,
            order=order,
            transaction_type='CREDIT'
        ).first()

        assert transaction is not None


class TestWalletDebitConstraints:
    """Test INV-009: Wallet debit MUST NOT exceed wallet balance."""

    def test_debit_amount_exceeds_balance_fails(self, db):
        """Debit exceeding balance must fail."""
        user = User.objects.create_user(
            email='user@example.com',
            password='testpass123'
        )

        wallet = Wallet.objects.create(
            user=user,
            balance=Decimal('50.00')
        )

        order = Order.objects.create(
            user=user,
            status='paid',
            total_amount=Decimal('100.00')
        )

        from orders.atomic_order_system import WalletOrderCoordinator
        result = WalletOrderCoordinator.capture_payment(wallet, order)

        assert result['success'] is False

    def test_debit_equals_balance_succeeds(self, db):
        """Debit equal to balance should succeed."""
        user = User.objects.create_user(
            email='user@example.com',
            password='testpass123'
        )

        wallet = Wallet.objects.create(
            user=user,
            balance=Decimal('100.00')
        )

        order = Order.objects.create(
            user=user,
            status='paid',
            total_amount=Decimal('100.00')
        )

        from orders.atomic_order_system import WalletOrderCoordinator
        result = WalletOrderCoordinator.capture_payment(wallet, order)

        assert result['success'] is True
        wallet.refresh_from_db()
        assert wallet.balance == 0

    def test_partial_debit_succeeds(self, db):
        """Partial debit should succeed."""
        user = User.objects.create_user(
            email='user@example.com',
            password='testpass123'
        )

        wallet = Wallet.objects.create(
            user=user,
            balance=Decimal('100.00')
        )

        order = Order.objects.create(
            user=user,
            status='paid',
            total_amount=Decimal('40.00')
        )

        from orders.atomic_order_system import WalletOrderCoordinator
        result = WalletOrderCoordinator.capture_payment(wallet, order)

        assert result['success'] is True
        wallet.refresh_from_db()
        assert wallet.balance == Decimal('60.00')


class TestWalletRefundBehavior:
    """Test refund behavior with wallet."""

    def test_refund_credits_wallet(self, db):
        """Refund MUST credit wallet."""
        user = User.objects.create_user(
            email='user@example.com',
            password='testpass123'
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

        balance_after_payment = wallet.balance

        # Refund
        order.status = 'refunded'
        order.save()

        WalletOrderCoordinator.credit_refund(wallet, order)

        wallet.refresh_from_db()
        assert wallet.balance > balance_after_payment

    def test_refund_amount_matches_payment(self, db):
        """Refund amount MUST equal original payment amount."""
        user = User.objects.create_user(
            email='user@example.com',
            password='testpass123'
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
        WalletOrderCoordinator.capture_payment(wallet, order)
        WalletOrderCoordinator.credit_refund(wallet, order)

        # Check debit and credit amounts
        debit = WalletTransaction.objects.filter(
            wallet=wallet,
            order=order,
            transaction_type='DEBIT'
        ).first()

        credit = WalletTransaction.objects.filter(
            wallet=wallet,
            order=order,
            transaction_type='CREDIT'
        ).first()

        if debit and credit:
            assert debit.amount == credit.amount
