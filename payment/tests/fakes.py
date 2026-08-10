"""
Test-only gateway double for Payment 2.0 (Phase 3, Part B). NOT wired into
payment/gateways/__init__.py's registry - it must never be reachable outside the test
suite. The Phase 3 brief is explicit: "Use mocked gateway responses for automated
tests... Do NOT call the real payment gateway from the test suite" - this mocks at the
service layer's own gateway interface boundary (payment/gateways/base.py), never at
Paymob's wire format, since nothing here has ever seen Paymob's real wire format to
mock accurately (see payment/gateways/paymob.py's docstring for why that matters).
"""
from payment.gateways.base import (
    PaymentGateway,
    GatewayNotConfigured,
    GatewayError,
    GatewayPaymentIntent,
    GatewayVerificationResult,
    GatewayWebhookEvent,
    GatewayRefundResult,
)


class FakeGateway(PaymentGateway):
    """Configurable in-memory gateway double.

    - configured=False makes every method raise GatewayNotConfigured, exactly like
      the real (currently credential-less) PaymobGateway - used to prove the service
      layer's "not configured" handling works generically, not just for Paymob.
    - fail_create / fail_verify / fail_refund force a GatewayError on the
      corresponding call, for the "gateway failure" test cases.
    - succeed (default True) controls whether verify_payment/webhooks report success.
    """
    name = 'fake'

    def __init__(self, configured=True, fail_create=False, fail_verify=False,
                 fail_refund=False, succeed=True):
        self.configured = configured
        self.fail_create = fail_create
        self.fail_verify = fail_verify
        self.fail_refund = fail_refund
        self.succeed = succeed
        self._next_ref = 0
        self.created_payments = []

    def _check_configured(self):
        if not self.configured:
            raise GatewayNotConfigured("FakeGateway is configured=False for this test")

    def create_payment(self, *, amount, currency, order_reference, idempotency_key):
        self._check_configured()
        if self.fail_create:
            raise GatewayError("FakeGateway: simulated create_payment failure")
        self._next_ref += 1
        ref = f"fake_ref_{self._next_ref}"
        self.created_payments.append({
            'amount': amount, 'currency': currency,
            'order_reference': order_reference, 'idempotency_key': idempotency_key,
            'gateway_reference': ref,
        })
        return GatewayPaymentIntent(gateway_reference=ref, redirect_url=f"https://fake.gateway/pay/{ref}")

    def verify_payment(self, *, gateway_reference):
        self._check_configured()
        if self.fail_verify:
            raise GatewayError("FakeGateway: simulated verify_payment failure")
        return GatewayVerificationResult(
            is_success=self.succeed,
            gateway_transaction_id=f"txn_{gateway_reference}",
            amount=None,
            raw={'gateway_reference': gateway_reference, 'succeed': self.succeed},
        )

    def verify_webhook(self, *, headers, body):
        self._check_configured()
        valid = headers.get('X-Fake-Signature') == 'valid'
        if not valid:
            return GatewayWebhookEvent(is_valid=False, raw={'reason': 'bad signature'})
        import json
        payload = json.loads(body) if body else {}
        return GatewayWebhookEvent(
            is_valid=True,
            event_id=payload.get('event_id', 'evt_default'),
            gateway_reference=payload.get('gateway_reference'),
            is_success=payload.get('is_success', True),
            amount=payload.get('amount'),
            raw=payload,
        )

    def refund(self, *, gateway_transaction_id, amount):
        self._check_configured()
        if self.fail_refund:
            raise GatewayError("FakeGateway: simulated refund failure")
        return GatewayRefundResult(
            is_success=self.succeed,
            gateway_refund_id=f"refund_{gateway_transaction_id}",
            raw={'amount': str(amount)},
        )
