"""
Phase 3 (Payment 2.0, Part B workstream 9): named Paymob adapter, deliberately not
implemented.

The gateway is Paymob (product owner's answer during Phase 3). But this repo has zero
Paymob configuration - no PAYMOB_API_KEY / PAYMOB_INTEGRATION_ID / PAYMOB_HMAC_SECRET /
PAYMOB_IFRAME_ID anywhere in settings, .env, or requirements.txt. That fails the Phase
3 brief's conjunctive gate ("known AND configured") for real gateway calls.

It is tempting to write the real HTTP calls from general knowledge of Paymob's public
API (the classic three-step Accept flow: POST /api/auth/tokens -> POST
/api/ecommerce/orders -> POST /api/acceptance/payment_keys, then an iframe redirect;
webhooks HMAC-signed over a fixed, ordered field concatenation). Deliberately NOT
doing that: Paymob has shipped more than one API generation, this repo has no sandbox
credentials to verify field names, endpoint paths, or the HMAC field ordering against,
and a webhook signature check that *looks* correct but was never verified against a
real payload is a security control that is worse than an honest 503 - it would pass
review while silently accepting forged webhooks. The Phase 3 brief is explicit on this
point ("DO NOT invent API endpoints... DO NOT implement fake gateway calls").

Every method below therefore does exactly one thing: check for configuration, and
raise GatewayNotConfigured because it is never present. Once real credentials exist,
implement each method against Paymob's current documentation and a real sandbox
account, and add gateway-specific tests using recorded real (or sandbox) responses -
not against this docstring's recollection of the API shape.
"""
import os

from .base import (
    PaymentGateway,
    GatewayNotConfigured,
    GatewayPaymentIntent,
    GatewayVerificationResult,
    GatewayWebhookEvent,
    GatewayRefundResult,
)

REQUIRED_ENV_VARS = (
    'PAYMOB_API_KEY',
    'PAYMOB_INTEGRATION_ID',
    'PAYMOB_HMAC_SECRET',
    'PAYMOB_IFRAME_ID',
)


class PaymobGateway(PaymentGateway):
    name = 'paymob'

    def __init__(self):
        self.api_key = os.environ.get('PAYMOB_API_KEY')
        self.integration_id = os.environ.get('PAYMOB_INTEGRATION_ID')
        self.hmac_secret = os.environ.get('PAYMOB_HMAC_SECRET')
        self.iframe_id = os.environ.get('PAYMOB_IFRAME_ID')

    def _ensure_configured(self):
        missing = [name for name in REQUIRED_ENV_VARS if not os.environ.get(name)]
        if missing:
            raise GatewayNotConfigured(
                "Paymob is selected but not configured: missing environment "
                f"variable(s) {', '.join(missing)}. Payment gateway integration is "
                "blocked until these are set and verified against a real Paymob "
                "sandbox account (see payment/gateways/paymob.py module docstring)."
            )

    def create_payment(self, *, amount, currency, order_reference, idempotency_key) -> GatewayPaymentIntent:
        self._ensure_configured()
        raise NotImplementedError("Paymob create_payment is not implemented - see module docstring.")

    def verify_payment(self, *, gateway_reference) -> GatewayVerificationResult:
        self._ensure_configured()
        raise NotImplementedError("Paymob verify_payment is not implemented - see module docstring.")

    def verify_webhook(self, *, headers, body) -> GatewayWebhookEvent:
        self._ensure_configured()
        raise NotImplementedError("Paymob verify_webhook is not implemented - see module docstring.")

    def refund(self, *, gateway_transaction_id, amount) -> GatewayRefundResult:
        self._ensure_configured()
        raise NotImplementedError("Paymob refund is not implemented - see module docstring.")
