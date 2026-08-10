"""
Phase 3 regression tests: PaymentService.handle_webhook (Payment 2.0, Part B
workstream 13). Uses FakeGateway.verify_webhook, which treats header
X-Fake-Signature: valid as authentic - never a real Paymob signature check (see
payment/gateways/paymob.py for why that's not implemented).
"""
import json
import pytest

from payment.models import WebhookEvent
from payment.services import PaymentService


@pytest.mark.django_db
class TestHandleWebhook:
    def test_gateway_not_configured_refuses_not_stores(self, unconfigured_fake_gateway):
        status_code, event = PaymentService.handle_webhook(headers={}, body=b'{}')

        assert status_code == 'GATEWAY_NOT_CONFIGURED'
        assert event is None
        assert WebhookEvent.objects.count() == 0  # never stored - can't be trusted

    def test_invalid_signature_logged_but_not_processed(self, fake_gateway):
        status_code, event = PaymentService.handle_webhook(
            headers={'X-Fake-Signature': 'wrong'}, body=json.dumps({'event_id': 'evt_1'}).encode(),
        )

        assert status_code == 'INVALID_SIGNATURE'
        stored = WebhookEvent.objects.get()
        assert stored.signature_valid is False
        assert stored.processed is False

    def test_valid_webhook_marks_payment_paid(self, buyer, pending_order, fake_gateway):
        payment, attempt, _ = PaymentService.create_payment(user=buyer, order_id=pending_order.id)

        body = json.dumps({
            'event_id': 'evt_success_1',
            'gateway_reference': attempt.gateway_reference,
            'is_success': True,
        }).encode()
        status_code, event = PaymentService.handle_webhook(
            headers={'X-Fake-Signature': 'valid'}, body=body,
        )

        assert status_code == 'PROCESSED'
        assert event.processed is True
        payment.refresh_from_db()
        assert payment.status == 'paid'
        pending_order.refresh_from_db()
        assert pending_order.payment_status is True

    def test_duplicate_webhook_delivery_processed_once(self, buyer, pending_order, fake_gateway):
        payment, attempt, _ = PaymentService.create_payment(user=buyer, order_id=pending_order.id)
        body = json.dumps({
            'event_id': 'evt_dup_1', 'gateway_reference': attempt.gateway_reference, 'is_success': True,
        }).encode()
        headers = {'X-Fake-Signature': 'valid'}

        status1, event1 = PaymentService.handle_webhook(headers=headers, body=body)
        status2, event2 = PaymentService.handle_webhook(headers=headers, body=body)

        assert status1 == 'PROCESSED'
        assert status2 == 'DUPLICATE'
        assert event1.id == event2.id
        assert WebhookEvent.objects.filter(event_id='evt_dup_1').count() == 1

    def test_webhook_failure_event_does_not_mark_paid(self, buyer, pending_order, fake_gateway):
        payment, attempt, _ = PaymentService.create_payment(user=buyer, order_id=pending_order.id)
        body = json.dumps({
            'event_id': 'evt_fail_1', 'gateway_reference': attempt.gateway_reference, 'is_success': False,
        }).encode()

        status_code, event = PaymentService.handle_webhook(headers={'X-Fake-Signature': 'valid'}, body=body)

        assert status_code == 'PROCESSED'
        payment.refresh_from_db()
        assert payment.status != 'paid'

    def test_webhook_for_unknown_attempt_does_not_crash(self, fake_gateway):
        """A webhook whose gateway_reference doesn't match any attempt (e.g. a stale
        or foreign event) must not raise - just record the event and move on."""
        body = json.dumps({'event_id': 'evt_unknown', 'gateway_reference': 'nonexistent', 'is_success': True}).encode()

        status_code, event = PaymentService.handle_webhook(headers={'X-Fake-Signature': 'valid'}, body=body)

        assert status_code == 'PROCESSED'
        assert event.processed is True
