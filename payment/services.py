"""
Phase 3 (Payment 2.0, Part B): payment domain service layer. Every payment/refund view
in payment/views.py goes through here rather than touching models directly - this is
the one place that enforces "the client is never the source of truth for a successful
payment" and "the amount always comes from the order, never the client".

Deliberately does not touch orders/atomic_order_system.py or wallet's
WalletOrderCoordinator (orders/views.py's existing capture_payment/release_payment) -
those implement the wallet/COD payment path and are out of scope ("do NOT rewrite
Wallet"). This service only concerns Order.payment_method values that route through a
real gateway; it updates Order.status/payment_status at the same integration points
those flows already use (plain field writes + save()), never their internals.
"""
import logging

from django.db import transaction
from django.utils import timezone

from orders.models import Order
from .gateways import get_gateway
from .gateways.base import GatewayNotConfigured, GatewayError
from .models import Payment, PaymentAttempt, GatewayTransaction, Refund, WebhookEvent

logger = logging.getLogger(__name__)


class PaymentAuthorizationError(Exception):
    """Order doesn't belong to the requesting user."""
    pass


class InvalidOrderStateError(Exception):
    """Order isn't in a state that can accept a payment (e.g. already paid, or
    cancelled)."""
    pass


class PaymentService:
    GATEWAY_NAME = 'paymob'

    @staticmethod
    def _default_idempotency_key(order_id, user_id):
        return f"payment_create_order_{order_id}_user_{user_id}"

    @classmethod
    @transaction.atomic
    def create_payment(cls, *, user, order_id, idempotency_key=None):
        """Create (or return the existing) Payment for an order, then attempt one
        gateway charge. Amount is always Order.total_amount - never accepts or trusts
        a client-supplied amount, per the Phase 3 brief's explicit rule.

        Returns (payment, attempt, error) where error is None on success, or a short
        error code string. Never raises GatewayNotConfigured/GatewayError - those are
        caught here and reflected in the attempt's failed status + returned error, so
        the row exists for auditability instead of silently vanishing.
        """
        try:
            order = Order.objects.select_for_update().get(pk=order_id)
        except Order.DoesNotExist:
            return None, None, 'ORDER_NOT_FOUND'

        if order.user_id != user.id:
            raise PaymentAuthorizationError(f"Order {order_id} does not belong to user {user.id}")

        # Idempotency: a Payment already exists for this order (OneToOneField enforces
        # at most one) - return it rather than creating a second one. Covers the
        # "duplicate payment creation" case regardless of whether the caller supplied
        # a matching idempotency_key (the order itself is the natural dedup key here;
        # the explicit key additionally protects the very first create from being
        # double-submitted before the OneToOne row exists at all - see the
        # unique constraint on Payment.idempotency_key).
        existing = Payment.objects.filter(order=order).first()
        if existing is not None:
            if existing.status == 'paid':
                return existing, None, 'ALREADY_PAID'
            attempt = cls._attempt_gateway_charge(existing)
            return existing, attempt, None

        if order.status != 'pending_payment':
            raise InvalidOrderStateError(
                f"Order {order_id} is not awaiting payment (status={order.status})"
            )

        key = idempotency_key or cls._default_idempotency_key(order_id, user.id)
        payment = Payment.objects.create(
            order=order,
            user=user,
            gateway=cls.GATEWAY_NAME,
            amount=order.total_amount,  # server-authoritative amount, never client input
            status='pending',
            idempotency_key=key,
        )
        attempt = cls._attempt_gateway_charge(payment)
        return payment, attempt, None

    @classmethod
    def _attempt_gateway_charge(cls, payment):
        attempt = PaymentAttempt.objects.create(payment=payment, status='processing')
        gateway = get_gateway(payment.gateway)
        try:
            intent = gateway.create_payment(
                amount=payment.amount,
                currency=payment.currency,
                order_reference=str(payment.order_id),
                idempotency_key=f"{payment.idempotency_key}_attempt_{attempt.id}",
            )
        except (GatewayNotConfigured, GatewayError) as e:
            attempt.status = 'failed'
            attempt.failure_reason = str(e)
            attempt.save(update_fields=['status', 'failure_reason', 'updated_at'])
            # Same failed-attempt handling regardless of *why* the gateway call
            # failed (unconfigured vs. a live-but-rejecting gateway) - a payment
            # whose only/latest attempt just failed is not usably "pending" any more.
            if payment.status in ('pending', 'processing'):
                payment.status = 'failed'
                payment.save(update_fields=['status', 'updated_at'])
            return attempt

        attempt.gateway_reference = intent.gateway_reference
        attempt.save(update_fields=['gateway_reference', 'updated_at'])
        if payment.status == 'pending':
            payment.status = 'processing'
            payment.save(update_fields=['status', 'updated_at'])
        return attempt

    @classmethod
    @transaction.atomic
    def verify_payment(cls, *, user, payment_id):
        """Server-side check of a specific payment's true status at the gateway -
        never trusts a client's "payment succeeded" claim instead. The order's
        state only changes here (or in handle_webhook) - never from the client."""
        try:
            payment = Payment.objects.select_for_update().get(pk=payment_id)
        except Payment.DoesNotExist:
            return None, 'PAYMENT_NOT_FOUND'
        if payment.user_id != user.id:
            raise PaymentAuthorizationError(f"Payment {payment_id} does not belong to user {user.id}")

        latest_attempt = payment.attempts.order_by('-created_at').first()
        if latest_attempt is None or not latest_attempt.gateway_reference:
            return payment, 'NO_ATTEMPT_TO_VERIFY'

        gateway = get_gateway(payment.gateway)
        try:
            result = gateway.verify_payment(gateway_reference=latest_attempt.gateway_reference)
        except GatewayNotConfigured:
            return payment, 'PAYMENT_GATEWAY_NOT_CONFIGURED'
        except GatewayError:
            return payment, 'GATEWAY_ERROR'

        cls._apply_verification_result(payment, latest_attempt, result)
        return payment, None

    @classmethod
    def _apply_verification_result(cls, payment, attempt, result):
        GatewayTransaction.objects.get_or_create(
            gateway_transaction_id=result.gateway_transaction_id or f"unverified_{attempt.id}",
            defaults={
                'attempt': attempt,
                'is_success': result.is_success,
                'amount': result.amount or payment.amount,
                'raw_response': result.raw,
            },
        )
        if result.is_success:
            attempt.status = 'succeeded'
            attempt.save(update_fields=['status', 'updated_at'])
            cls._mark_payment_paid(payment)
        else:
            attempt.status = 'failed'
            attempt.save(update_fields=['status', 'updated_at'])
            if payment.status not in ('paid', 'refunded', 'partially_refunded'):
                payment.status = 'failed'
                payment.save(update_fields=['status', 'updated_at'])

    @classmethod
    def _mark_payment_paid(cls, payment):
        if payment.status == 'paid':
            return  # already applied - idempotent
        payment.status = 'paid'
        payment.save(update_fields=['status', 'updated_at'])
        order = payment.order
        order.payment_status = True
        order.status = 'paid'
        order.save(update_fields=['payment_status', 'status', 'updated_at'])
        logger.info(f"Payment {payment.id} for order {order.id} marked paid via gateway verification")

    @classmethod
    @transaction.atomic
    def handle_webhook(cls, *, headers, body):
        """Process an inbound gateway webhook delivery. Idempotent and replay-safe:
        - Refuses (does not process) while the gateway is unconfigured - an
          unverifiable signature must never be trusted, so this branch never writes a
          WebhookEvent row claiming a real event happened; it just tells the caller to
          503.
        - A signature that fails verification is logged (signature_valid=False) but
          never processed.
        - The same real event (gateway, event_id) delivered more than once is only
          ever processed once - WebhookEvent.processed guards it, and the
          (gateway, event_id) unique constraint makes a concurrent double-delivery
          race safe too (the loser hits the constraint under the same DB transaction
          semantics used everywhere else in this codebase).

        Returns (status_code, event) where status_code is one of:
        'GATEWAY_NOT_CONFIGURED', 'INVALID_SIGNATURE', 'DUPLICATE', 'PROCESSED'.
        """
        gateway = get_gateway(cls.GATEWAY_NAME)
        try:
            parsed = gateway.verify_webhook(headers=headers, body=body)
        except GatewayNotConfigured:
            return 'GATEWAY_NOT_CONFIGURED', None

        if not parsed.is_valid:
            WebhookEvent.objects.create(
                gateway=cls.GATEWAY_NAME, event_id=None, signature_valid=False,
                processed=False, payload=parsed.raw,
            )
            return 'INVALID_SIGNATURE', None

        existing = WebhookEvent.objects.filter(
            gateway=cls.GATEWAY_NAME, event_id=parsed.event_id
        ).first()
        if existing is not None:
            return 'DUPLICATE', existing

        event = WebhookEvent.objects.create(
            gateway=cls.GATEWAY_NAME, event_id=parsed.event_id, signature_valid=True,
            processed=False, payload=parsed.raw,
        )

        attempt = PaymentAttempt.objects.filter(gateway_reference=parsed.gateway_reference).first()
        if attempt is not None:
            cls._apply_verification_result(
                attempt.payment, attempt,
                _WebhookResultAdapter(parsed),
            )
        event.processed = True
        event.save(update_fields=['processed'])
        return 'PROCESSED', event

    @classmethod
    @transaction.atomic
    def refund(cls, *, user, payment_id, amount=None, reason='', idempotency_key=None):
        """Refund all or part of a paid Payment. `user` must be staff - refunds are an
        admin action, matching the brief's "Authorization" requirement."""
        try:
            payment = Payment.objects.select_for_update().get(pk=payment_id)
        except Payment.DoesNotExist:
            return None, 'PAYMENT_NOT_FOUND'

        if not getattr(user, 'is_staff', False):
            raise PaymentAuthorizationError("Only staff may issue refunds")

        # Idempotency check comes before the refundability/amount checks below when
        # the caller supplied an explicit key: a retried request repeating the same
        # key must return the original refund even though the payment's status has,
        # by then, already moved on to 'refunded' (which the refundability check
        # below would otherwise reject as "nothing left to refund"). Only applies to
        # an explicit key - the auto-generated fallback key depends on refund_amount,
        # which isn't known until after those checks run.
        if idempotency_key:
            existing = Refund.objects.filter(idempotency_key=idempotency_key).first()
            if existing is not None:
                return existing, None

        if payment.status not in ('paid', 'partially_refunded'):
            return None, 'PAYMENT_NOT_REFUNDABLE'

        refund_amount = amount if amount is not None else (payment.amount - payment.amount_refunded)
        if refund_amount <= 0 or refund_amount > (payment.amount - payment.amount_refunded):
            return None, 'INVALID_REFUND_AMOUNT'

        key = idempotency_key or f"refund_payment_{payment_id}_{refund_amount}"
        existing = Refund.objects.filter(idempotency_key=key).first()
        if existing is not None:
            return existing, None

        refund = Refund.objects.create(
            payment=payment, amount=refund_amount, reason=reason,
            status='processing', requested_by=user, idempotency_key=key,
        )

        succeeded_attempt = payment.attempts.filter(status='succeeded').order_by('-created_at').first()
        gateway_transaction_id = None
        if succeeded_attempt is not None:
            latest_txn = succeeded_attempt.transactions.filter(is_success=True).order_by('-created_at').first()
            gateway_transaction_id = latest_txn.gateway_transaction_id if latest_txn else None

        gateway = get_gateway(payment.gateway)
        try:
            result = gateway.refund(gateway_transaction_id=gateway_transaction_id, amount=refund_amount)
        except GatewayNotConfigured:
            refund.status = 'failed'
            refund.save(update_fields=['status', 'updated_at'])
            return refund, 'PAYMENT_GATEWAY_NOT_CONFIGURED'
        except GatewayError:
            refund.status = 'failed'
            refund.save(update_fields=['status', 'updated_at'])
            return refund, 'GATEWAY_ERROR'

        if result.is_success:
            refund.status = 'succeeded'
            refund.gateway_refund_id = result.gateway_refund_id
            refund.save(update_fields=['status', 'gateway_refund_id', 'updated_at'])
            payment.amount_refunded += refund_amount
            payment.status = 'refunded' if payment.amount_refunded >= payment.amount else 'partially_refunded'
            payment.save(update_fields=['amount_refunded', 'status', 'updated_at'])
            return refund, None
        else:
            refund.status = 'failed'
            refund.save(update_fields=['status', 'updated_at'])
            return refund, 'GATEWAY_REFUND_REJECTED'


class _WebhookResultAdapter:
    """Adapts a GatewayWebhookEvent to the same shape _apply_verification_result()
    expects from a GatewayVerificationResult (is_success/gateway_transaction_id/amount/
    raw) - the two dataclasses carry the same information under the same names except
    gateway_transaction_id, which the webhook side calls event_id."""
    def __init__(self, webhook_event):
        self.is_success = webhook_event.is_success
        self.gateway_transaction_id = webhook_event.event_id
        self.amount = webhook_event.amount
        self.raw = webhook_event.raw
