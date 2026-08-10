"""
Gateway registry. Phase 3 (Payment 2.0, Part B): the service layer (payment/services.py)
asks for a gateway by name and gets back an object implementing the abstract interface
in base.py - it never imports a concrete gateway module directly, so adding a second
gateway later (or a TestGateway used only by the test suite) doesn't touch the service
layer at all.
"""
from .base import PaymentGateway, GatewayNotConfigured
from .paymob import PaymobGateway

_REGISTRY = {
    'paymob': PaymobGateway,
}


def get_gateway(name):
    """Return a gateway adapter instance for `name`. Raises KeyError for an unknown
    gateway name (a programming error - the caller chose the name) - NOT
    GatewayNotConfigured, which is reserved for "this real gateway has no
    credentials"."""
    try:
        gateway_cls = _REGISTRY[name]
    except KeyError:
        raise KeyError(
            f"Unknown payment gateway '{name}'. Registered gateways: {list(_REGISTRY)}"
        )
    return gateway_cls()
