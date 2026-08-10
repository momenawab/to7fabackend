import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model

from orders.models import Order
from .fakes import FakeGateway

User = get_user_model()


def make_user(email, **extra):
    return User.objects.create_user(
        email=email,
        password='testpass123456',
        phone_number='+2011' + email[-8:].rjust(8, '0'),
        is_mobile_verified=True,
        email_verified=True,
        user_type=extra.pop('user_type', 'customer'),
        **extra,
    )


@pytest.fixture
def buyer(db):
    return make_user('payment_buyer@test.com')


@pytest.fixture
def other_user(db):
    return make_user('payment_other@test.com')


@pytest.fixture
def staff_user(db):
    return make_user('payment_staff@test.com', is_staff=True)


@pytest.fixture
def pending_order(db, buyer):
    return Order.objects.create(
        user=buyer,
        total_amount=Decimal('250.00'),
        shipping_address='1 Test St',
        shipping_cost=Decimal('0.00'),
        payment_method='paymob',
        status='pending_payment',
        payment_status=False,
        idempotency_key='payment_test_order_1',
    )


@pytest.fixture
def fake_gateway(monkeypatch):
    """Patches payment.services.get_gateway to always return this configured
    FakeGateway instance, regardless of the gateway name requested - the service
    layer under test never talks to the real (credential-less) Paymob adapter."""
    gateway = FakeGateway(configured=True)
    monkeypatch.setattr('payment.services.get_gateway', lambda name: gateway)
    return gateway


@pytest.fixture
def unconfigured_fake_gateway(monkeypatch):
    gateway = FakeGateway(configured=False)
    monkeypatch.setattr('payment.services.get_gateway', lambda name: gateway)
    return gateway
