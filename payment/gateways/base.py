"""
Phase 3 (Payment 2.0, Part B workstream 9): gateway-agnostic abstract interface.

To7fa 2.0 has chosen Paymob as its gateway (confirmed by the product owner during
Phase 3), but Paymob is NOT configured anywhere in this repository or environment - no
API key, integration ID, HMAC secret, or iframe ID in settings, .env, or requirements
(verified by grep across all of those during the Phase 3 audit). Per the Phase 3
brief's explicit rule ("gateway integration is implemented only if the gateway is
explicitly known AND configured" - a conjunctive test), knowing the name is not enough
to safely implement real gateway calls.

This interface exists so the domain/service layer (payment/services.py) can be fully
built, tested (via a FakeGateway test double - see payment/tests/), and wired into real
views now, with the gateway swapped in later as a single adapter implementation once
credentials exist and can be verified against a real Paymob sandbox. Every method on
every real adapter must raise GatewayNotConfigured until that's true - never fabricate
a response.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


class GatewayNotConfigured(Exception):
    """Raised by a gateway adapter method when required credentials/config are absent.
    The service layer catches this and surfaces 503 PAYMENT_GATEWAY_NOT_CONFIGURED to
    the client - it must never be swallowed into a fake success or silently ignored."""
    pass


class GatewayError(Exception):
    """Raised for a real, configured gateway call that failed for a gateway-side
    reason (network error, gateway rejected the request, etc.) - distinct from
    GatewayNotConfigured so callers can tell "not set up" from "set up but failed"."""
    pass


@dataclass
class GatewayPaymentIntent:
    """What create_payment() returns: enough for the client to actually pay (e.g. a
    Paymob iframe/checkout URL) plus the gateway's own reference for this attempt."""
    gateway_reference: str
    redirect_url: Optional[str] = None
    raw: dict = field(default_factory=dict)


@dataclass
class GatewayVerificationResult:
    """What verify_payment() returns: the gateway's authoritative view of whether a
    specific attempt actually succeeded. The client's own claim of success is never
    sufficient on its own - this is the thing that is."""
    is_success: bool
    gateway_transaction_id: Optional[str] = None
    amount: Optional[str] = None
    raw: dict = field(default_factory=dict)


@dataclass
class GatewayWebhookEvent:
    """What verify_webhook() returns after validating a webhook's authenticity
    (signature/HMAC). event_id must be stable and unique per real-world event so the
    caller can de-duplicate retried/replayed deliveries."""
    is_valid: bool
    event_id: Optional[str] = None
    gateway_reference: Optional[str] = None
    is_success: Optional[bool] = None
    amount: Optional[str] = None
    raw: dict = field(default_factory=dict)


@dataclass
class GatewayRefundResult:
    is_success: bool
    gateway_refund_id: Optional[str] = None
    raw: dict = field(default_factory=dict)


class PaymentGateway(ABC):
    """One adapter per real-world gateway. Every method takes plain values (not Django
    model instances) so a fake/test implementation never needs a database."""

    name: str

    @abstractmethod
    def create_payment(self, *, amount, currency, order_reference, idempotency_key) -> GatewayPaymentIntent:
        """Start a payment attempt at the gateway. Must never return a "success"
        result - a payment isn't paid until verify_payment()/verify_webhook() says
        so."""
        raise NotImplementedError

    @abstractmethod
    def verify_payment(self, *, gateway_reference) -> GatewayVerificationResult:
        """Ask the gateway, authoritatively, whether a given attempt succeeded. Used
        for client-triggered "check my payment status" flows - never trust the client's
        own claim instead of calling this."""
        raise NotImplementedError

    @abstractmethod
    def verify_webhook(self, *, headers, body) -> GatewayWebhookEvent:
        """Validate a webhook delivery's signature/HMAC and extract its event. Must
        return is_valid=False (not raise) for a bad signature - an invalid webhook is
        an expected occurrence (retries, replay attempts), not an exceptional one."""
        raise NotImplementedError

    @abstractmethod
    def refund(self, *, gateway_transaction_id, amount) -> GatewayRefundResult:
        raise NotImplementedError
