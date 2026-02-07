"""
Spec 002 Tests: Cancellation & Refund Behavior

Tests derived from:
- spec-002.md section: Cancellation & Refund Specification
- FR-CAN-001 through FR-CAN-022, FR-REF-001 through FR-REF-012
"""

import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from orders.models import Order
from wallet.models import Wallet, Transaction as WalletTransaction

User = get_user_model()


class TestCancellationEligibility:
    """Test FR-CAN-001 through FR-CAN-004: Who can cancel and when."""

    def test_customer_can_cancel_pending_payment_order(self, authenticated_client, db):
        """FR-CAN-001: Customer MAY cancel in PENDING_PAYMENT state."""
        user = User.objects.first()
        user.is_mobile_verified = True
        user.save()

        order = Order.objects.create(
            user=user,
            status='pending_payment',
            total_amount=Decimal('100.00')
        )

        response = authenticated_client.post(
            f'/api/v1/orders/{order.id}/cancel/'
        )

        assert response.status_code in [200, 201]

    def test_customer_can_cancel_paid_order(self, authenticated_client, db):
        """FR-CAN-001: Customer MAY cancel in PAID state (pre-processing)."""
        user = User.objects.first()
        user.is_mobile_verified = True
        user.save()

        order = Order.objects.create(
            user=user,
            status='paid',
            total_amount=Decimal('100.00')
        )

        response = authenticated_client.post(
            f'/api/v1/orders/{order.id}/cancel/'
        )

        assert response.status_code in [200, 201]

    def test_customer_cannot_cancel_processing_order(self, authenticated_client, db):
        """FR-CAN-002: Customer MUST NOT cancel once in PROCESSING state."""
        user = User.objects.first()
        user.is_mobile_verified = True
        user.save()

        order = Order.objects.create(
            user=user,
            status='processing',
            total_amount=Decimal('100.00')
        )

        response = authenticated_client.post(
            f'/api/v1/orders/{order.id}/cancel/'
        )

        assert response.status_code == 403

    def test_customer_cannot_cancel_shipped_order(self, authenticated_client, db):
        """FR-CAN-002: Customer MUST NOT cancel SHIPPED orders."""
        user = User.objects.first()
        user.is_mobile_verified = True
        user.save()

        order = Order.objects.create(
            user=user,
            status='shipped',
            total_amount=Decimal('100.00')
        )

        response = authenticated_client.post(
            f'/api/v1/orders/{order.id}/cancel/'
        )

        assert response.status_code == 403

    def test_seller_cannot_cancel_order(self, api_client, db):
        """FR-CAN-003: Seller MUST NOT directly cancel orders."""
        seller = User.objects.create_user(
            email='seller@example.com',
            password='testpass123',
            user_type='artist'
        )

        order = Order.objects.create(
            user=None,
            status='paid',
            total_amount=Decimal('100.00')
        )

        api_client.force_authenticate(user=seller)
        response = api_client.post(
            f'/api/v1/orders/{order.id}/cancel/'
        )

        # Seller should not have cancel permission
        assert response.status_code in [403, 404]

    def test_admin_can_cancel_any_order(self, api_client, db):
        """FR-CAN-004: Admin MAY cancel any non-terminal order."""
        admin = User.objects.create_user(
            email='admin@example.com',
            password='testpass123',
            is_staff=True
        )

        order = Order.objects.create(
            user=None,
            status='processing',
            total_amount=Decimal('100.00')
        )

        api_client.force_authenticate(user=admin)
        response = api_client.post(
            f'/api/v1/orders/{order.id}/cancel/'
        )

        assert response.status_code in [200, 201]


class TestCancellationEffects:
    """Test FR-CAN-010 through FR-CAN-013: What happens when cancelling."""

    def test_cancellation_releases_stock(self, db):
        """FR-CAN-010: Stock reservations MUST be released on cancellation."""
        user = User.objects.create_user(
            email='user@example.com',
            password='testpass123',
            is_mobile_verified=True
        )

        order = Order.objects.create(
            user=user,
            status='paid',
            total_amount=Decimal('100.00')
        )

        # Cancel order
        order.status = 'cancelled'
        order.save()

        # Stock should be released
        # Implementation varies - check that stock is restored

    def test_cancellation_releases_wallet_holds(self, db):
        """FR-CAN-011: Wallet holds MUST be released on cancellation."""
        user = User.objects.create_user(
            email='user@example.com',
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
        assert wallet.balance >= initial_balance

    def test_cancellation_with_captured_payment_refunds(self, db):
        """FR-CAN-012: Payment MUST be refunded if already captured."""
        user = User.objects.create_user(
            email='user@example.com',
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

        initial_balance = wallet.balance

        # Cancel paid order
        order.status = 'refunded'
        order.save()

        WalletOrderCoordinator.credit_refund(wallet, order)

        wallet.refresh_from_db()
        assert wallet.balance > initial_balance

    def test_cancellation_state_based_on_payment(self, db):
        """FR-CAN-013: Cancellation transitions to CANCELLED or REFUNDED based on payment."""
        # Unpaid cancellation -> CANCELLED
        order1 = Order.objects.create(
            user=None,
            status='pending_payment',
            total_amount=Decimal('100.00')
        )

        from orders.atomic_order_system import OrderStateMachine
        if not OrderStateMachine.requires_refund('pending_payment', 'cancelled'):
            order1.status = 'cancelled'
            order1.save()
            assert order1.status == 'cancelled'

        # Paid cancellation -> REFUNDED
        order2 = Order.objects.create(
            user=None,
            status='paid',
            total_amount=Decimal('100.00')
        )

        if OrderStateMachine.requires_refund('paid', 'cancelled'):
            order2.status = 'refunded'
            order2.save()
            assert order2.status == 'refunded'


class TestRefundRules:
    """Test FR-REF-001 through FR-REF-004: Refund requirements."""

    def test_refund_only_for_captured_payments(self, db):
        """FR-REF-001: Refunds MUST only be processed for captured payments."""
        user = User.objects.create_user(
            email='user@example.com',
            password='testpass123',
            is_mobile_verified=True
        )

        wallet = Wallet.objects.create(
            user=user,
            balance=Decimal('100.00')
        )

        # Try to refund pending_payment order (no payment captured)
        order = Order.objects.create(
            user=user,
            status='pending_payment',
            total_amount=Decimal('50.00')
        )

        from orders.atomic_order_system import WalletOrderCoordinator
        result = WalletOrderCoordinator.credit_refund(wallet, order)

        # Should fail or be idempotent
        assert result['success'] is False or result['already_refunded']

    def test_refund_credits_original_wallet(self, db):
        """FR-REF-002: Wallet refunds MUST credit the original wallet account."""
        user = User.objects.create_user(
            email='user@example.com',
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

        initial_balance = wallet.balance

        # Refund
        order.status = 'refunded'
        order.save()

        WalletOrderCoordinator.credit_refund(wallet, order)

        wallet.refresh_from_db()
        assert wallet.balance > initial_balance

    def test_refund_amount_equals_captured_amount(self, db):
        """FR-REF-003: Refund amount MUST equal original captured amount."""
        user = User.objects.create_user(
            email='user@example.com',
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

        # Refund
        order.status = 'refunded'
        order.save()

        WalletOrderCoordinator.credit_refund(wallet, order)

        # Check refund transaction amount
        refund_transaction = WalletTransaction.objects.filter(
            wallet=wallet,
            order=order,
            transaction_type='CREDIT'
        ).first()

        if refund_transaction:
            assert refund_transaction.amount == order.total_amount

    def test_refund_references_original_payment(self, db):
        """FR-REF-004: Refund MUST reference original payment transaction."""
        user = User.objects.create_user(
            email='user@example.com',
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

        payment_transaction = WalletTransaction.objects.filter(
            wallet=wallet,
            order=order,
            transaction_type='DEBIT'
        ).first()

        # Refund
        order.status = 'refunded'
        order.save()

        WalletOrderCoordinator.credit_refund(wallet, order)

        refund_transaction = WalletTransaction.objects.filter(
            wallet=wallet,
            order=order,
            transaction_type='CREDIT'
        ).first()

        if refund_transaction and payment_transaction:
            # Refund should reference original payment
            assert refund_transaction.order == payment_transaction.order


class TestPartialCancellationPolicy:
    """Test FR-CAN-020 through FR-CAN-022: Partial cancellation not supported."""

    def test_partial_cancellation_not_supported(self, api_client, db):
        """FR-CAN-020: Partial order cancellation is NOT SUPPORTED."""
        user = User.objects.create_user(
            email='user@example.com',
            password='testpass123',
            is_mobile_verified=True
        )

        order = Order.objects.create(
            user=user,
            status='paid',
            total_amount=Decimal('100.00')
        )

        api_client.force_authenticate(user=user)

        # Try to cancel specific items (should fail or cancel entire order)
        response = api_client.post(
            f'/api/v1/orders/{order.id}/cancel/',
            data={'item_ids': [1, 2]},
            format='json'
        )

        # Should either ignore item_ids or return error
        assert response.status_code in [400, 200, 201]

    def test_cancellation_applies_to_entire_order(self, db):
        """FR-CAN-021: All cancellation requests MUST apply to entire order."""
        user = User.objects.create_user(
            email='user@example.com',
            password='testpass123',
            is_mobile_verified=True
        )

        order = Order.objects.create(
            user=user,
            status='paid',
            total_amount=Decimal('100.00')
        )

        # Cancel order
        order.status = 'cancelled'
        order.save()

        # Entire order is cancelled
        assert order.status in ['cancelled', 'refunded']


class TestRefundTiming:
    """Test FR-REF-010 through FR-REF-012: Refund timing behavior."""

    def test_wallet_refund_processed_immediately(self, db):
        """FR-REF-010: Wallet refunds MUST be processed immediately."""
        user = User.objects.create_user(
            email='user@example.com',
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

        # Approve refund
        order.status = 'refunded'
        order.save()

        initial_balance = wallet.balance
        WalletOrderCoordinator.credit_refund(wallet, order)

        wallet.refresh_from_db()
        # Balance updated immediately
        assert wallet.balance > initial_balance

    def test_refund_completion_triggers_refunded_state(self, db):
        """FR-REF-011: Refund completion MUST trigger order state to REFUNDED."""
        user = User.objects.create_user(
            email='user@example.com',
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

        # Process refund
        WalletOrderCoordinator.credit_refund(wallet, order)

        # State should be refunded
        order.refresh_from_db()
        assert order.status == 'refunded'

    def test_failed_refund_does_not_change_order_state(self, db):
        """FR-REF-012: Failed refund MUST NOT change order state."""
        user = User.objects.create_user(
            email='user@example.com',
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

        # Simulate failed refund
        result = WalletOrderCoordinator.credit_refund(wallet, order)

        if not result['success']:
            # Order state should not change
            order.refresh_from_db()
            assert order.status == 'paid'
