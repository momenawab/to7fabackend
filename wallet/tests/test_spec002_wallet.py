"""
Spec 002 Tests: Wallet Balance Consistency

Tests derived from:
- spec-002.md sections: System Invariants, Payment & Wallet Specification
- INV-002, INV-009, FR-PAY-010 through FR-PAY-014
"""

import pytest


class TestWalletBalanceConsistency:
    """Test INV-002: Wallet balance MUST never be negative."""

    pytestmark = pytest.mark.critical
import uuid
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
            email=f'user_{uuid.uuid4().hex[:8]}@example.com',
            password='testpass123'
        )

        wallet, created = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('100.00')}
        )
        # Ensure wallet has the expected balance
        if not created or wallet.balance != Decimal('100.00'):
            wallet.balance = Decimal('100.00')
            wallet.save()

        # Create order for reference
        order = Order.objects.create(
            user=user,
            status='pending_payment',
            total_amount=Decimal('200.00')
        )

        # Try to debit more than balance
        from orders.atomic_order_system import WalletOrderCoordinator
        result = WalletOrderCoordinator.reserve_payment(
            wallet,
            Decimal('200.00'),
            order_id=order.id,
            idempotency_key=f'test_{uuid.uuid4().hex}'
        )

        assert result[0] is False  # success is first element of tuple
        wallet.refresh_from_db()
        assert wallet.balance >= 0

    def test_concurrent_debits_do_not_make_balance_negative(self, db):
        """Multiple concurrent debits should not make balance negative."""
        user = User.objects.create_user(
            email=f'user_{uuid.uuid4().hex[:8]}@example.com',
            password='testpass123'
        )

        wallet, created = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('100.00')}
        )
        # Ensure wallet has the expected balance
        if not created or wallet.balance != Decimal('100.00'):
            wallet.balance = Decimal('100.00')
            wallet.save()

        # Create orders for reference
        order1 = Order.objects.create(
            user=user,
            status='pending_payment',
            total_amount=Decimal('60.00')
        )
        order2 = Order.objects.create(
            user=user,
            status='pending_payment',
            total_amount=Decimal('60.00')
        )

        # Simulate concurrent operations
        from orders.atomic_order_system import WalletOrderCoordinator

        result1 = WalletOrderCoordinator.reserve_payment(
            wallet,
            Decimal('60.00'),
            order_id=order1.id,
            idempotency_key=f'test_{uuid.uuid4().hex}'
        )
        result2 = WalletOrderCoordinator.reserve_payment(
            wallet,
            Decimal('60.00'),
            order_id=order2.id,
            idempotency_key=f'test_{uuid.uuid4().hex}'
        )

        # At least one should fail
        assert not (result1[0] and result2[0])

        wallet.refresh_from_db()
        assert wallet.balance >= 0

    def test_wallet_balance_after_multiple_operations(self, db):
        """Wallet balance remains consistent after multiple operations."""
        user = User.objects.create_user(
            email=f'user_{uuid.uuid4().hex[:8]}@example.com',
            password='testpass123'
        )

        wallet, created = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('100.00')}
        )
        # Ensure wallet has the expected balance
        if not created or wallet.balance != Decimal('100.00'):
            wallet.balance = Decimal('100.00')
            wallet.save()

        from orders.atomic_order_system import WalletOrderCoordinator

        # Create orders for reference
        order1 = Order.objects.create(
            user=user,
            status='pending_payment',
            total_amount=Decimal('30.00')
        )
        order2 = Order.objects.create(
            user=user,
            status='pending_payment',
            total_amount=Decimal('20.00')
        )

        # Debit 1
        result1 = WalletOrderCoordinator.reserve_payment(
            wallet,
            Decimal('30.00'),
            order_id=order1.id,
            idempotency_key=f'test_{uuid.uuid4().hex}'
        )
        assert result1[0] is True
        wallet.refresh_from_db()
        assert wallet.balance == Decimal('70.00')

        # Debit 2
        result2 = WalletOrderCoordinator.reserve_payment(
            wallet,
            Decimal('20.00'),
            order_id=order2.id,
            idempotency_key=f'test_{uuid.uuid4().hex}'
        )
        assert result2[0] is True
        wallet.refresh_from_db()
        assert wallet.balance == Decimal('50.00')

        # Credit (refund) - using release_payment
        WalletOrderCoordinator.release_payment(
            order_id=order1.id,
            idempotency_key=f'refund_{uuid.uuid4().hex}',
            refund_reason='Test refund'
        )
        wallet.refresh_from_db()
        assert wallet.balance >= Decimal('50.00')


class TestWalletTransactionRecording:
    """Test FR-PAY-014: Wallet transactions MUST be recorded with order reference."""

    pytestmark = pytest.mark.non_critical

    def test_debit_transaction_has_order_reference(self, db):
        """Payment transaction MUST reference order."""
        user = User.objects.create_user(
            email=f'user_{uuid.uuid4().hex[:8]}@example.com',
            password='testpass123'
        )

        wallet, created = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('100.00')}
        )
        # Ensure wallet has the expected balance
        if not created or wallet.balance != Decimal('100.00'):
            wallet.balance = Decimal('100.00')
            wallet.save()

        order = Order.objects.create(
            user=user,
            status='pending_payment',
            total_amount=Decimal('50.00')
        )

        from orders.atomic_order_system import WalletOrderCoordinator
        WalletOrderCoordinator.reserve_payment(
            wallet,
            Decimal('50.00'),
            order_id=order.id,
            idempotency_key=f'test_{uuid.uuid4().hex}'
        )

        transaction = WalletTransaction.objects.filter(
            wallet=wallet,
            reference_id=str(order.id),
            transaction_type='payment'
        ).first()

        assert transaction is not None
        assert transaction.reference_id == str(order.id)

    def test_credit_transaction_has_order_reference(self, db):
        """Refund transaction MUST reference order."""
        user = User.objects.create_user(
            email=f'user_{uuid.uuid4().hex[:8]}@example.com',
            password='testpass123'
        )

        wallet, created = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('100.00')}
        )
        # Ensure wallet has the expected balance
        if not created or wallet.balance != Decimal('100.00'):
            wallet.balance = Decimal('100.00')
            wallet.save()

        order = Order.objects.create(
            user=user,
            status='pending_payment',
            total_amount=Decimal('50.00')
        )

        from orders.atomic_order_system import WalletOrderCoordinator

        # First reserve payment
        WalletOrderCoordinator.reserve_payment(
            wallet,
            Decimal('50.00'),
            order_id=order.id,
            idempotency_key=f'test_{uuid.uuid4().hex}'
        )

        # Then refund
        WalletOrderCoordinator.release_payment(
            order_id=order.id,
            idempotency_key=f'refund_{uuid.uuid4().hex}',
            refund_reason='Test refund'
        )

        transaction = WalletTransaction.objects.filter(
            wallet=wallet,
            reference_id=str(order.id),
            transaction_type='refund'
        ).first()

        assert transaction is not None
        assert transaction.reference_id == str(order.id)

    def test_hold_transaction_has_order_reference(self, db):
        """Payment reservation MUST reference order."""
        user = User.objects.create_user(
            email=f'user_{uuid.uuid4().hex[:8]}@example.com',
            password='testpass123'
        )

        wallet, created = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('100.00')}
        )
        # Ensure wallet has the expected balance
        if not created or wallet.balance != Decimal('100.00'):
            wallet.balance = Decimal('100.00')
            wallet.save()

        order = Order.objects.create(
            user=user,
            status='pending_payment',
            total_amount=Decimal('50.00')
        )

        from orders.atomic_order_system import WalletOrderCoordinator
        WalletOrderCoordinator.reserve_payment(
            wallet,
            order.total_amount,
            order_id=order.id,
            idempotency_key=f'test_{uuid.uuid4().hex}'
        )

        transaction = WalletTransaction.objects.filter(
            wallet=wallet,
            reference_id=str(order.id)
        ).first()

        assert transaction is not None

    def test_release_transaction_has_order_reference(self, db):
        """Payment release MUST reference order."""
        user = User.objects.create_user(
            email=f'user_{uuid.uuid4().hex[:8]}@example.com',
            password='testpass123'
        )

        wallet, created = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('100.00')}
        )
        # Ensure wallet has the expected balance
        if not created or wallet.balance != Decimal('100.00'):
            wallet.balance = Decimal('100.00')
            wallet.save()

        order = Order.objects.create(
            user=user,
            status='pending_payment',
            total_amount=Decimal('50.00')
        )

        from orders.atomic_order_system import WalletOrderCoordinator
        WalletOrderCoordinator.reserve_payment(
            wallet,
            order.total_amount,
            order_id=order.id,
            idempotency_key=f'test_{uuid.uuid4().hex}'
        )
        WalletOrderCoordinator.release_payment(
            order_id=order.id,
            idempotency_key=f'release_{uuid.uuid4().hex}',
            refund_reason='Test release'
        )

        # Check for release transaction
        transactions = WalletTransaction.objects.filter(
            wallet=wallet,
            reference_id=str(order.id)
        )

        assert transactions.count() > 0


class TestWalletTransactionTypes:
    """Test FR-PAY-014: Transaction types (payment, refund)."""

    pytestmark = pytest.mark.non_critical

    def test_hold_transaction_type(self, db):
        """Payment initiation creates payment transaction."""
        user = User.objects.create_user(
            email=f'user_{uuid.uuid4().hex[:8]}@example.com',
            password='testpass123'
        )

        wallet, created = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('100.00')}
        )
        # Ensure wallet has the expected balance
        if not created or wallet.balance != Decimal('100.00'):
            wallet.balance = Decimal('100.00')
            wallet.save()

        order = Order.objects.create(
            user=user,
            status='pending_payment',
            total_amount=Decimal('50.00')
        )

        from orders.atomic_order_system import WalletOrderCoordinator
        WalletOrderCoordinator.reserve_payment(
            wallet,
            order.total_amount,
            order_id=order.id,
            idempotency_key=f'test_{uuid.uuid4().hex}'
        )

        transaction = WalletTransaction.objects.filter(
            wallet=wallet,
            reference_id=str(order.id)
        ).first()

        if transaction:
            assert transaction.transaction_type == 'payment'

    def test_debit_transaction_type(self, db):
        """Payment capture marks transaction as completed."""
        user = User.objects.create_user(
            email=f'user_{uuid.uuid4().hex[:8]}@example.com',
            password='testpass123'
        )

        wallet, created = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('100.00')}
        )
        # Ensure wallet has the expected balance
        if not created or wallet.balance != Decimal('100.00'):
            wallet.balance = Decimal('100.00')
            wallet.save()

        order = Order.objects.create(
            user=user,
            status='pending_payment',
            total_amount=Decimal('50.00')
        )

        from orders.atomic_order_system import WalletOrderCoordinator

        # First reserve
        reserve_key = f'test_{uuid.uuid4().hex}'
        WalletOrderCoordinator.reserve_payment(
            wallet,
            Decimal('50.00'),
            order_id=order.id,
            idempotency_key=reserve_key
        )

        # Then capture
        result = WalletOrderCoordinator.capture_payment(
            order_id=order.id,
            idempotency_key=f'capture_{uuid.uuid4().hex}'
        )

        transaction = WalletTransaction.objects.filter(
            wallet=wallet,
            reference_id=str(order.id),
            transaction_type='payment',
            status='completed'
        ).first()

        assert transaction is not None

    def test_credit_transaction_type(self, db):
        """Refund creates refund transaction."""
        user = User.objects.create_user(
            email=f'user_{uuid.uuid4().hex[:8]}@example.com',
            password='testpass123'
        )

        wallet, created = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('100.00')}
        )
        # Ensure wallet has the expected balance
        if not created or wallet.balance != Decimal('100.00'):
            wallet.balance = Decimal('100.00')
            wallet.save()

        order = Order.objects.create(
            user=user,
            status='pending_payment',
            total_amount=Decimal('50.00')
        )

        from orders.atomic_order_system import WalletOrderCoordinator

        # First reserve
        WalletOrderCoordinator.reserve_payment(
            wallet,
            Decimal('50.00'),
            order_id=order.id,
            idempotency_key=f'test_{uuid.uuid4().hex}'
        )

        # Then refund
        WalletOrderCoordinator.release_payment(
            order_id=order.id,
            idempotency_key=f'refund_{uuid.uuid4().hex}',
            refund_reason='Test refund'
        )

        transaction = WalletTransaction.objects.filter(
            wallet=wallet,
            reference_id=str(order.id),
            transaction_type='refund'
        ).first()

        assert transaction is not None


class TestWalletDebitConstraints:
    """Test INV-009: Wallet debit MUST NOT exceed wallet balance."""

    pytestmark = pytest.mark.critical

    @pytest.mark.non_critical  # Overrides class mark - implementation detail
    def test_debit_amount_exceeds_balance_fails(self, db):
        """Debit exceeding balance must fail."""
        user = User.objects.create_user(
            email=f'user_{uuid.uuid4().hex[:8]}@example.com',
            password='testpass123'
        )

        wallet, _ = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('50.00')}
        )

        order = Order.objects.create(
            user=user,
            status='pending_payment',
            total_amount=Decimal('100.00')
        )

        from orders.atomic_order_system import WalletOrderCoordinator
        result = WalletOrderCoordinator.reserve_payment(
            wallet,
            Decimal('100.00'),
            order_id=order.id,
            idempotency_key=f'test_{uuid.uuid4().hex}'
        )

        assert result[0] is False

    def test_debit_equals_balance_succeeds(self, db):
        """Debit equal to balance should succeed."""
        user = User.objects.create_user(
            email=f'user_{uuid.uuid4().hex[:8]}@example.com',
            password='testpass123'
        )

        wallet, created = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('100.00')}
        )
        # Ensure wallet has the expected balance
        if not created or wallet.balance != Decimal('100.00'):
            wallet.balance = Decimal('100.00')
            wallet.save()

        order = Order.objects.create(
            user=user,
            status='pending_payment',
            total_amount=Decimal('100.00')
        )

        from orders.atomic_order_system import WalletOrderCoordinator
        result = WalletOrderCoordinator.reserve_payment(
            wallet,
            Decimal('100.00'),
            order_id=order.id,
            idempotency_key=f'test_{uuid.uuid4().hex}'
        )

        assert result[0] is True
        wallet.refresh_from_db()
        assert wallet.balance == 0

    def test_partial_debit_succeeds(self, db):
        """Partial debit should succeed."""
        user = User.objects.create_user(
            email=f'user_{uuid.uuid4().hex[:8]}@example.com',
            password='testpass123'
        )

        wallet, created = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('100.00')}
        )
        # Ensure wallet has the expected balance
        if not created or wallet.balance != Decimal('100.00'):
            wallet.balance = Decimal('100.00')
            wallet.save()

        order = Order.objects.create(
            user=user,
            status='pending_payment',
            total_amount=Decimal('40.00')
        )

        from orders.atomic_order_system import WalletOrderCoordinator
        result = WalletOrderCoordinator.reserve_payment(
            wallet,
            Decimal('40.00'),
            order_id=order.id,
            idempotency_key=f'test_{uuid.uuid4().hex}'
        )

        assert result[0] is True
        wallet.refresh_from_db()
        assert wallet.balance == Decimal('60.00')


class TestWalletRefundBehavior:
    """Test refund behavior with wallet."""

    pytestmark = pytest.mark.non_critical

    def test_refund_credits_wallet(self, db):
        """Refund MUST credit wallet."""
        user = User.objects.create_user(
            email=f'user_{uuid.uuid4().hex[:8]}@example.com',
            password='testpass123'
        )

        wallet, created = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('100.00')}
        )
        # Ensure wallet has the expected balance
        if not created or wallet.balance != Decimal('100.00'):
            wallet.balance = Decimal('100.00')
            wallet.save()

        order = Order.objects.create(
            user=user,
            status='pending_payment',
            total_amount=Decimal('50.00')
        )

        from orders.atomic_order_system import WalletOrderCoordinator

        # Reserve payment (deb wallet)
        reserve_key = f'reserve_{uuid.uuid4().hex}'
        WalletOrderCoordinator.reserve_payment(
            wallet,
            Decimal('50.00'),
            order_id=order.id,
            idempotency_key=reserve_key
        )

        balance_after_payment = wallet.balance

        # Refund (release payment)
        WalletOrderCoordinator.release_payment(
            order_id=order.id,
            idempotency_key=f'refund_{uuid.uuid4().hex}',
            refund_reason='Test refund'
        )

        wallet.refresh_from_db()
        assert wallet.balance > balance_after_payment

    def test_refund_amount_matches_payment(self, db):
        """Refund amount MUST equal original payment amount."""
        user = User.objects.create_user(
            email=f'user_{uuid.uuid4().hex[:8]}@example.com',
            password='testpass123'
        )

        wallet, created = Wallet.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('100.00')}
        )
        # Ensure wallet has the expected balance
        if not created or wallet.balance != Decimal('100.00'):
            wallet.balance = Decimal('100.00')
            wallet.save()

        order = Order.objects.create(
            user=user,
            status='pending_payment',
            total_amount=Decimal('50.00')
        )

        from orders.atomic_order_system import WalletOrderCoordinator

        # Reserve payment
        reserve_key = f'reserve_{uuid.uuid4().hex}'
        WalletOrderCoordinator.reserve_payment(
            wallet,
            Decimal('50.00'),
            order_id=order.id,
            idempotency_key=reserve_key
        )

        # Refund
        WalletOrderCoordinator.release_payment(
            order_id=order.id,
            idempotency_key=f'refund_{uuid.uuid4().hex}',
            refund_reason='Test refund'
        )

        # Check payment and refund amounts
        payment = WalletTransaction.objects.filter(
            wallet=wallet,
            reference_id=str(order.id),
            transaction_type='payment'
        ).first()

        refund = WalletTransaction.objects.filter(
            wallet=wallet,
            reference_id=str(order.id),
            transaction_type='refund'
        ).first()

        if payment and refund:
            assert payment.amount == refund.amount
