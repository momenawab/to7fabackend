"""
Phase 3 regression tests: payment views (Payment 2.0, Part B workstream 8 - deleting
the fake-success implementation - and workstream 17's HTTP-layer test cases).
"""
import json
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from payment.models import Payment


@pytest.fixture
def client():
    c = APIClient()
    c.defaults['HTTP_HOST'] = 'localhost'
    return c


def _auth(client, user):
    from rest_framework_simplejwt.tokens import RefreshToken
    access = str(RefreshToken.for_user(user).access_token)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')


@pytest.mark.django_db
class TestNoFakeSuccessSurvives:
    """The exact regression this workstream exists to prevent: every payment endpoint
    used to return a hardcoded success message with no real transaction. None of these
    calls may return an unqualified 200 'success' without a real Payment row backing
    it, and none may report success while the gateway is unconfigured."""

    def test_process_payment_with_unconfigured_gateway_returns_503_not_fake_success(
        self, client, buyer, pending_order,
    ):
        # No fake_gateway fixture here on purpose - exercises the real
        # (credential-less) Paymob adapter end to end through the view.
        _auth(client, buyer)
        response = client.post('/api/payments/process/', {'order_id': pending_order.id}, format='json')

        assert response.status_code == 503
        body = response.json()
        assert 'processed successfully' not in json.dumps(body).lower()
        payment = Payment.objects.get(order=pending_order)
        assert payment.status == 'failed'  # not 'completed', not faked

    def test_verify_payment_with_unconfigured_gateway_returns_503(self, client, buyer, pending_order, fake_gateway):
        _auth(client, buyer)
        create_response = client.post('/api/payments/process/', {'order_id': pending_order.id}, format='json')
        payment_id = create_response.json()['data']['id'] if create_response.status_code == 201 else Payment.objects.get(order=pending_order).id

        # Switch to the real (unconfigured) gateway for the verify call.
        import payment.services as services_module
        from payment.gateways import get_gateway as real_get_gateway
        original = services_module.get_gateway
        services_module.get_gateway = real_get_gateway
        try:
            response = client.post('/api/payments/verify/', {'payment_id': payment_id}, format='json')
        finally:
            services_module.get_gateway = original

        assert response.status_code == 503

    def test_client_provided_amount_is_ignored(self, client, buyer, pending_order, fake_gateway):
        """Sending a lowball 'amount' in the request body must not change what gets
        charged - the view doesn't even read it."""
        _auth(client, buyer)
        response = client.post('/api/payments/process/', {
            'order_id': pending_order.id, 'amount': '0.01',
        }, format='json')

        payment = Payment.objects.get(order=pending_order)
        assert payment.amount == pending_order.total_amount
        assert payment.amount != Decimal('0.01')


@pytest.mark.django_db
class TestProcessPaymentEndpoint:
    def test_create_payment_success(self, client, buyer, pending_order, fake_gateway):
        _auth(client, buyer)
        response = client.post('/api/payments/process/', {'order_id': pending_order.id}, format='json')
        assert response.status_code == 201
        assert response.json()['data']['status'] in ('processing', 'pending')

    def test_missing_order_id_is_validation_error(self, client, buyer):
        _auth(client, buyer)
        response = client.post('/api/payments/process/', {}, format='json')
        assert response.status_code == 400

    def test_invalid_order_returns_404(self, client, buyer, fake_gateway):
        _auth(client, buyer)
        response = client.post('/api/payments/process/', {'order_id': 999999}, format='json')
        assert response.status_code == 404

    def test_unauthorized_order_returns_403(self, client, other_user, pending_order, fake_gateway):
        _auth(client, other_user)
        response = client.post('/api/payments/process/', {'order_id': pending_order.id}, format='json')
        assert response.status_code == 403

    def test_unauthenticated_request_rejected(self, client, pending_order):
        response = client.post('/api/payments/process/', {'order_id': pending_order.id}, format='json')
        assert response.status_code == 401

    def test_duplicate_payment_request_returns_same_payment_not_error(self, client, buyer, pending_order, fake_gateway):
        _auth(client, buyer)
        r1 = client.post('/api/payments/process/', {'order_id': pending_order.id, 'idempotency_key': 'k1'}, format='json')
        r2 = client.post('/api/payments/process/', {'order_id': pending_order.id, 'idempotency_key': 'k1'}, format='json')
        assert r1.json()['data']['id'] == r2.json()['data']['id']
        assert Payment.objects.filter(order=pending_order).count() == 1


@pytest.mark.django_db
class TestRefundEndpointAuthorization:
    def test_non_staff_cannot_refund(self, client, buyer, pending_order, fake_gateway):
        from payment.services import PaymentService
        payment, _, _ = PaymentService.create_payment(user=buyer, order_id=pending_order.id)
        PaymentService.verify_payment(user=buyer, payment_id=payment.id)

        _auth(client, buyer)
        response = client.post('/api/payments/refund/', {'payment_id': payment.id}, format='json')
        assert response.status_code == 403

    def test_staff_can_refund_paid_payment(self, client, buyer, staff_user, pending_order, fake_gateway):
        from payment.services import PaymentService
        payment, _, _ = PaymentService.create_payment(user=buyer, order_id=pending_order.id)
        PaymentService.verify_payment(user=buyer, payment_id=payment.id)

        _auth(client, staff_user)
        response = client.post('/api/payments/refund/', {'payment_id': payment.id}, format='json')
        assert response.status_code == 200
        assert response.json()['data']['status'] == 'succeeded'


@pytest.mark.django_db
class TestWebhookEndpoint:
    def test_webhook_with_unconfigured_gateway_returns_503(self, client):
        response = client.post(
            '/api/payments/webhook/', data=json.dumps({'event_id': 'evt_1'}),
            content_type='application/json',
        )
        assert response.status_code == 503

    def test_webhook_does_not_require_authentication(self, client):
        """The gateway calls this, not a logged-in app user - AllowAny is correct
        here, not a bug; authenticity comes from signature verification instead."""
        response = client.post(
            '/api/payments/webhook/', data=json.dumps({'event_id': 'evt_1'}),
            content_type='application/json',
        )
        assert response.status_code != 401


@pytest.mark.django_db
class TestPaymentMethodsNeverStoreRawCardData:
    def test_raw_card_number_rejected(self, client, buyer):
        _auth(client, buyer)
        response = client.post('/api/payments/methods/', {
            'method_type': 'credit_card',
            'details': {'card_number': '4111111111111111', 'cvv': '123'},
        }, format='json')
        assert response.status_code == 400

    def test_safe_metadata_accepted(self, client, buyer):
        _auth(client, buyer)
        response = client.post('/api/payments/methods/', {
            'method_type': 'credit_card',
            'details': {'last4': '1111', 'brand': 'visa', 'gateway_token': 'tok_abc'},
        }, format='json')
        assert response.status_code == 201
