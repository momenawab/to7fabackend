from decimal import Decimal

from django.db import models
from django.conf import settings


class PaymentMethod(models.Model):
    METHOD_CHOICES = (
        ('credit_card', 'Credit Card'),
        ('wallet', 'Wallet'),
        ('cash_on_delivery', 'Cash on Delivery'),
        ('bank_transfer', 'Bank Transfer'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payment_methods')
    method_type = models.CharField(max_length=20, choices=METHOD_CHOICES)
    is_default = models.BooleanField(default=False)
    details = models.JSONField(default=dict)  # Store method-specific details
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_method_type_display()} for {self.user.email}"

    def save(self, *args, **kwargs):
        # If this is set as default, unset default for other payment methods
        if self.is_default:
            PaymentMethod.objects.filter(
                user=self.user,
                is_default=True
            ).exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)


# Phase 3 (Payment 2.0, Part B): the old `Payment` model (below, until this comment's
# replacement) had a `process_payment()` method that unconditionally set
# status='completed' and order.payment_status=True with no gateway call at all - the
# model-level twin of the fake-success views this phase removes. Verified via grep
# that nothing anywhere ever wrote a Payment row (payment/views.py's stub never called
# Payment.objects.create(), and no other app references payment.models.Payment) or
# read PaymentMethod for an actual charge, so this redesign has no production data to
# migrate - see the accompanying migration for the same verification, documented the
# same way as orders/migrations/0010's production-safety note.
#
# New domain, matching what the Phase 3 brief asks for explicitly: Payment (one per
# Order - the payable amount, snapshotted from Order.total_amount server-side, and its
# overall lifecycle) -> PaymentAttempt (one per try; a Payment can have several after
# retries) -> GatewayTransaction (the gateway's own record of money actually moving,
# tied to one attempt) -> Refund (against a Payment, gateway-confirmed) and
# WebhookEvent (every inbound webhook delivery, for idempotent processing and replay
# protection - see payment/services.py and payment/views.py for how these are used).

class Payment(models.Model):
    """One payment intent per Order. amount is captured from Order.total_amount at
    creation time and never taken from the client - see PaymentService.create_payment.
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),                       # created, no successful attempt yet
        ('processing', 'Processing'),                 # an attempt is in flight at the gateway
        ('paid', 'Paid'),                              # gateway-verified success
        ('failed', 'Failed'),                          # all attempts failed / gateway rejected
        ('cancelled', 'Cancelled'),                    # abandoned before any success
        ('refunded', 'Refunded'),                      # fully refunded
        ('partially_refunded', 'Partially Refunded'),  # refunded < amount
    )

    order = models.OneToOneField('orders.Order', on_delete=models.PROTECT, related_name='gateway_payment')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='gateway_payments')
    gateway = models.CharField(max_length=20, default='paymob')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='EGP')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    amount_refunded = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    # Client-supplied idempotency key (or a server-derived one, e.g. f"order_{order_id}")
    # - a repeated create-payment call with the same key against the same order returns
    # the existing Payment instead of creating a second one. See PaymentService.
    idempotency_key = models.CharField(max_length=255, unique=True, db_index=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Payment #{self.id} ({self.status}) for Order #{self.order_id}"


class PaymentAttempt(models.Model):
    """One try at actually charging via the gateway. Retries after a failure create a
    new attempt under the same Payment rather than a new Payment."""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
    )

    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='attempts')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    gateway_reference = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    failure_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Attempt #{self.id} ({self.status}) for Payment #{self.payment_id}"


class GatewayTransaction(models.Model):
    """The gateway's own record of a money-movement event tied to one attempt -
    populated from either a verify_payment() call or a verified webhook."""
    attempt = models.ForeignKey(PaymentAttempt, on_delete=models.CASCADE, related_name='transactions')
    gateway_transaction_id = models.CharField(max_length=255, db_index=True)
    is_success = models.BooleanField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    # Sanitized gateway response - never card numbers/CVV (never sent to us by a
    # PCI-compliant gateway integration in the first place; enforced by not accepting
    # raw card fields anywhere in this app - see payment/views.py).
    raw_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['gateway_transaction_id'],
                name='payment_gatewaytransaction_unique_gateway_txn_id',
            ),
        ]

    def __str__(self):
        return f"GatewayTransaction {self.gateway_transaction_id} ({'success' if self.is_success else 'failed'})"


class Refund(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
    )

    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='refunds')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    gateway_refund_id = models.CharField(max_length=255, blank=True, null=True)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='requested_refunds')
    idempotency_key = models.CharField(max_length=255, unique=True, db_index=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Refund #{self.id} ({self.status}) of {self.amount} for Payment #{self.payment_id}"


class WebhookEvent(models.Model):
    """Every inbound webhook delivery, valid or not - the audit trail and the
    idempotency/replay-protection mechanism (see PaymentService.handle_webhook).

    event_id may be null for a delivery whose signature didn't even validate (its
    payload can't be trusted enough to extract a real event id from). It's left NULL
    rather than '' specifically so the uniqueness constraint below still works on
    MySQL, which doesn't support conditional/partial unique indexes: standard SQL
    (including MySQL/InnoDB) excludes NULL from uniqueness checks entirely, so any
    number of invalid deliveries (event_id=NULL) can coexist while real event ids are
    still deduplicated.
    """
    gateway = models.CharField(max_length=20)
    # The gateway's own event/transaction identifier. Unique per gateway so a retried
    # or replayed delivery of the same real-world event is recognized and only
    # processed once, however many times it's delivered.
    event_id = models.CharField(max_length=255, null=True, blank=True)
    signature_valid = models.BooleanField()
    processed = models.BooleanField(default=False)
    payload = models.JSONField(default=dict, blank=True)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['gateway', 'event_id'],
                name='payment_webhookevent_unique_gateway_event',
            ),
        ]

    def __str__(self):
        return f"WebhookEvent {self.gateway}:{self.event_id} (processed={self.processed})"
