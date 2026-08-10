"""
Phase 3 regression tests: PaymentService (Payment 2.0, Part B workstream 17's test
list, minus the HTTP-layer cases covered in test_payment_views.py and the webhook
cases in test_webhook.py). Every gateway call is a FakeGateway (payment/tests/fakes.py)
- never the real network, per the brief's explicit instruction.
"""
from decimal import Decimal

import pytest

from orders.models import Order
from payment.models import Payment, PaymentAttempt, GatewayTransaction
from payment.services import PaymentService, PaymentAuthorizationError, InvalidOrderStateError


@pytest.mark.django_db
class TestCreatePayment:
    def test_create_payment_success(self, buyer, pending_order, fake_gateway):
        payment, attempt, error = PaymentService.create_payment(user=buyer, order_id=pending_order.id)

        assert error is None
        assert payment.status == 'processing'
        assert payment.amount == pending_order.total_amount
        assert attempt.status == 'processing'
        assert attempt.gateway_reference is not None
        assert len(fake_gateway.created_payments) == 1

    def test_amount_always_from_order_never_trusted_from_caller(self, buyer, pending_order, fake_gateway):
        """PaymentService.create_payment doesn't even accept a client amount
        parameter - proving the amount can only ever come from the order."""
        import inspect
        sig = inspect.signature(PaymentService.create_payment)
        assert 'amount' not in sig.parameters

        payment, _, _ = PaymentService.create_payment(user=buyer, order_id=pending_order.id)
        assert payment.amount == Decimal('250.00')  # pending_order's real total_amount

    def test_duplicate_payment_request_returns_same_payment(self, buyer, pending_order, fake_gateway):
        payment1, _, _ = PaymentService.create_payment(user=buyer, order_id=pending_order.id, idempotency_key='dup-key')
        payment2, _, _ = PaymentService.create_payment(user=buyer, order_id=pending_order.id, idempotency_key='dup-key')

        assert payment1.id == payment2.id
        assert Payment.objects.filter(order=pending_order).count() == 1

    def test_invalid_order_returns_error(self, buyer, fake_gateway):
        payment, attempt, error = PaymentService.create_payment(user=buyer, order_id=999999)
        assert payment is None
        assert error == 'ORDER_NOT_FOUND'

    def test_unauthorized_order_raises(self, other_user, pending_order, fake_gateway):
        """other_user does not own pending_order (buyer does)."""
        with pytest.raises(PaymentAuthorizationError):
            PaymentService.create_payment(user=other_user, order_id=pending_order.id)

    def test_order_not_awaiting_payment_raises(self, buyer, pending_order, fake_gateway):
        pending_order.status = 'cancelled'
        pending_order.save()
        with pytest.raises(InvalidOrderStateError):
            PaymentService.create_payment(user=buyer, order_id=pending_order.id)

    def test_gateway_failure_marks_attempt_failed_not_order_paid(self, buyer, pending_order, monkeypatch):
        from payment.tests.fakes import FakeGateway
        failing_gateway = FakeGateway(configured=True, fail_create=True)
        monkeypatch.setattr('payment.services.get_gateway', lambda name: failing_gateway)

        payment, attempt, error = PaymentService.create_payment(user=buyer, order_id=pending_order.id)

        assert attempt.status == 'failed'
        assert payment.status == 'failed'
        pending_order.refresh_from_db()
        assert pending_order.payment_status is False
        assert pending_order.status == 'pending_payment'

    def test_gateway_not_configured_marks_attempt_failed_with_clear_reason(self, buyer, pending_order, unconfigured_fake_gateway):
        payment, attempt, error = PaymentService.create_payment(user=buyer, order_id=pending_order.id)

        assert attempt.status == 'failed'
        assert 'not configured' in attempt.failure_reason.lower() or 'FakeGateway' in attempt.failure_reason
        assert payment.status == 'failed'


@pytest.mark.django_db
class TestVerifyPayment:
    def test_successful_gateway_response_marks_paid_and_updates_order(self, buyer, pending_order, fake_gateway):
        payment, _, _ = PaymentService.create_payment(user=buyer, order_id=pending_order.id)

        verified, error = PaymentService.verify_payment(user=buyer, payment_id=payment.id)

        assert error is None
        assert verified.status == 'paid'
        pending_order.refresh_from_db()
        assert pending_order.payment_status is True
        assert pending_order.status == 'paid'
        assert GatewayTransaction.objects.filter(attempt__payment=payment, is_success=True).exists()

    def test_verification_failure_does_not_mark_paid(self, buyer, pending_order, monkeypatch):
        from payment.tests.fakes import FakeGateway
        gateway = FakeGateway(configured=True, succeed=False)
        monkeypatch.setattr('payment.services.get_gateway', lambda name: gateway)

        payment, _, _ = PaymentService.create_payment(user=buyer, order_id=pending_order.id)
        verified, error = PaymentService.verify_payment(user=buyer, payment_id=payment.id)

        assert verified.status == 'failed'
        pending_order.refresh_from_db()
        assert pending_order.payment_status is False
        assert pending_order.status != 'paid'

    def test_unauthorized_payment_raises(self, buyer, other_user, pending_order, fake_gateway):
        payment, _, _ = PaymentService.create_payment(user=buyer, order_id=pending_order.id)
        with pytest.raises(PaymentAuthorizationError):
            PaymentService.verify_payment(user=other_user, payment_id=payment.id)

    def test_verify_payment_with_unconfigured_gateway(self, buyer, pending_order, fake_gateway, monkeypatch):
        payment, _, _ = PaymentService.create_payment(user=buyer, order_id=pending_order.id)
        from payment.tests.fakes import FakeGateway
        monkeypatch.setattr('payment.services.get_gateway', lambda name: FakeGateway(configured=False))

        verified, error = PaymentService.verify_payment(user=buyer, payment_id=payment.id)
        assert error == 'PAYMENT_GATEWAY_NOT_CONFIGURED'


@pytest.mark.django_db
class TestRefund:
    def _pay_order(self, buyer, order, fake_gateway):
        payment, _, _ = PaymentService.create_payment(user=buyer, order_id=order.id)
        PaymentService.verify_payment(user=buyer, payment_id=payment.id)
        payment.refresh_from_db()
        return payment

    def test_full_refund_succeeds_and_updates_status(self, buyer, staff_user, pending_order, fake_gateway):
        payment = self._pay_order(buyer, pending_order, fake_gateway)

        refund, error = PaymentService.refund(user=staff_user, payment_id=payment.id, reason='customer request')

        assert error is None
        assert refund.status == 'succeeded'
        payment.refresh_from_db()
        assert payment.status == 'refunded'
        assert payment.amount_refunded == payment.amount

    def test_partial_refund_sets_partially_refunded(self, buyer, staff_user, pending_order, fake_gateway):
        payment = self._pay_order(buyer, pending_order, fake_gateway)

        refund, error = PaymentService.refund(
            user=staff_user, payment_id=payment.id, amount=Decimal('50.00'),
        )

        assert error is None
        payment.refresh_from_db()
        assert payment.status == 'partially_refunded'
        assert payment.amount_refunded == Decimal('50.00')

    def test_refund_idempotent_on_key(self, buyer, staff_user, pending_order, fake_gateway):
        payment = self._pay_order(buyer, pending_order, fake_gateway)

        refund1, _ = PaymentService.refund(user=staff_user, payment_id=payment.id, idempotency_key='refund-key-1')
        refund2, _ = PaymentService.refund(user=staff_user, payment_id=payment.id, idempotency_key='refund-key-1')

        assert refund1.id == refund2.id

    def test_non_staff_cannot_refund(self, buyer, pending_order, fake_gateway):
        payment = self._pay_order(buyer, pending_order, fake_gateway)
        with pytest.raises(PaymentAuthorizationError):
            PaymentService.refund(user=buyer, payment_id=payment.id)

    def test_cannot_refund_unpaid_payment(self, buyer, staff_user, pending_order, fake_gateway):
        payment, _, _ = PaymentService.create_payment(user=buyer, order_id=pending_order.id)
        # Not verified/paid yet.
        refund, error = PaymentService.refund(user=staff_user, payment_id=payment.id)
        assert refund is None
        assert error == 'PAYMENT_NOT_REFUNDABLE'

    def test_refund_amount_exceeding_balance_rejected(self, buyer, staff_user, pending_order, fake_gateway):
        payment = self._pay_order(buyer, pending_order, fake_gateway)
        refund, error = PaymentService.refund(user=staff_user, payment_id=payment.id, amount=Decimal('999999.00'))
        assert refund is None
        assert error == 'INVALID_REFUND_AMOUNT'

    def test_refund_gateway_failure(self, buyer, staff_user, pending_order, fake_gateway, monkeypatch):
        payment = self._pay_order(buyer, pending_order, fake_gateway)
        from payment.tests.fakes import FakeGateway
        failing = FakeGateway(configured=True, fail_refund=True)
        monkeypatch.setattr('payment.services.get_gateway', lambda name: failing)

        refund, error = PaymentService.refund(user=staff_user, payment_id=payment.id)
        assert error == 'GATEWAY_ERROR'
        assert refund.status == 'failed'
