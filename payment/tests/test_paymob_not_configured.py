"""
Phase 3 regression test: proves the actual, real PaymobGateway (not the FakeGateway
test double used everywhere else in this test module) genuinely refuses to operate
without credentials - this is the concrete evidence behind the PHASE 3 BLOCKED verdict
for gateway integration, not just a claim in the report.
"""
import pytest

from payment.gateways.base import GatewayNotConfigured
from payment.gateways.paymob import PaymobGateway
from payment.gateways import get_gateway


class TestPaymobGatewayRefusesWithoutCredentials:
    """No monkeypatching of environment variables here on purpose - this must prove
    the gateway is unconfigured in the actual test environment, exactly as it would be
    in production right now, not in some artificially-blanked env."""

    def test_registry_returns_paymob_gateway(self):
        gateway = get_gateway('paymob')
        assert isinstance(gateway, PaymobGateway)

    def test_create_payment_raises_gateway_not_configured(self):
        gateway = PaymobGateway()
        with pytest.raises(GatewayNotConfigured):
            gateway.create_payment(amount='10.00', currency='EGP', order_reference='1', idempotency_key='k')

    def test_verify_payment_raises_gateway_not_configured(self):
        gateway = PaymobGateway()
        with pytest.raises(GatewayNotConfigured):
            gateway.verify_payment(gateway_reference='ref')

    def test_verify_webhook_raises_gateway_not_configured(self):
        gateway = PaymobGateway()
        with pytest.raises(GatewayNotConfigured):
            gateway.verify_webhook(headers={}, body=b'{}')

    def test_refund_raises_gateway_not_configured(self):
        gateway = PaymobGateway()
        with pytest.raises(GatewayNotConfigured):
            gateway.refund(gateway_transaction_id='txn', amount='10.00')

    def test_error_message_names_every_missing_variable(self):
        gateway = PaymobGateway()
        with pytest.raises(GatewayNotConfigured) as exc_info:
            gateway.create_payment(amount='10.00', currency='EGP', order_reference='1', idempotency_key='k')
        message = str(exc_info.value)
        for var in ('PAYMOB_API_KEY', 'PAYMOB_INTEGRATION_ID', 'PAYMOB_HMAC_SECRET', 'PAYMOB_IFRAME_ID'):
            assert var in message
