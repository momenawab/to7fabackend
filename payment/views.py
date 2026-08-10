"""
Phase 3 (Payment 2.0, Part B workstream 8): real payment views, replacing the fake-
success stubs. Every one of the five endpoints below used to unconditionally return a
hardcoded success message (e.g. process_payment: `{"message": "Payment processed
successfully"}`, status 200, no gateway call, no DB write at all) regardless of input.
None of that survives - every view now goes through PaymentService, which is the only
place order/payment state is allowed to change, and every path that would need a real
Paymob call returns 503 PAYMENT_GATEWAY_NOT_CONFIGURED instead of fabricating success
(see payment/gateways/paymob.py for why).
"""
import logging

from decimal import Decimal, InvalidOperation

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from api.helpers import api_success, api_error, api_created

from .models import Payment, PaymentMethod
from .services import (
    PaymentService, PaymentAuthorizationError, InvalidOrderStateError,
)

logger = logging.getLogger(__name__)

_ERROR_STATUS = {
    'ORDER_NOT_FOUND': status.HTTP_404_NOT_FOUND,
    'PAYMENT_NOT_FOUND': status.HTTP_404_NOT_FOUND,
    'ALREADY_PAID': status.HTTP_409_CONFLICT,
    'NO_ATTEMPT_TO_VERIFY': status.HTTP_400_BAD_REQUEST,
    'PAYMENT_GATEWAY_NOT_CONFIGURED': status.HTTP_503_SERVICE_UNAVAILABLE,
    'GATEWAY_ERROR': status.HTTP_502_BAD_GATEWAY,
    'PAYMENT_NOT_REFUNDABLE': status.HTTP_400_BAD_REQUEST,
    'INVALID_REFUND_AMOUNT': status.HTTP_400_BAD_REQUEST,
    'GATEWAY_REFUND_REJECTED': status.HTTP_502_BAD_GATEWAY,
}


def _payment_dict(payment):
    return {
        'id': payment.id,
        'order_id': payment.order_id,
        'gateway': payment.gateway,
        'amount': str(payment.amount),
        'currency': payment.currency,
        'status': payment.status,
        'amount_refunded': str(payment.amount_refunded),
        'created_at': payment.created_at.isoformat(),
    }


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_payment(request):
    """Create a payment for an order and attempt one gateway charge.

    Security (Phase 3 brief workstream 12): authenticated user required; order
    ownership is checked server-side; the payable amount is always
    Order.total_amount, never read from the request body at all - a client-supplied
    'amount' field, if sent, is silently ignored rather than trusted.
    """
    order_id = request.data.get('order_id')
    if not order_id:
        return api_error(request, code='VALIDATION_ERROR', message='order_id is required', status_code=400)

    idempotency_key = request.data.get('idempotency_key')

    try:
        payment, attempt, error = PaymentService.create_payment(
            user=request.user, order_id=order_id, idempotency_key=idempotency_key,
        )
    except PaymentAuthorizationError:
        return api_error(request, code='PERMISSION_DENIED', message='This order does not belong to you', status_code=403)
    except InvalidOrderStateError as e:
        return api_error(request, code='INVALID_ORDER_STATE', message=str(e), status_code=400)

    if error == 'ORDER_NOT_FOUND':
        return api_error(request, code='ORDER_NOT_FOUND', message='Order not found', status_code=404)
    if error == 'ALREADY_PAID':
        return api_success(request, data=_payment_dict(payment), message='Order is already paid')

    data = _payment_dict(payment)
    if attempt is not None:
        data['attempt_status'] = attempt.status
        if attempt.status == 'failed':
            return api_error(
                request, code='PAYMENT_GATEWAY_NOT_CONFIGURED' if 'not configured' in (attempt.failure_reason or '') else 'PAYMENT_ATTEMPT_FAILED',
                message=attempt.failure_reason or 'Payment attempt failed', status_code=503, details=data,
            )
    return api_created(request, data=data, message='Payment created')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_payment(request):
    """Server-side verification of a payment's true gateway status. Never trusts a
    client-supplied 'success' flag - only ever asks PaymentService, which asks the
    gateway."""
    payment_id = request.data.get('payment_id')
    if not payment_id:
        return api_error(request, code='VALIDATION_ERROR', message='payment_id is required', status_code=400)

    try:
        payment, error = PaymentService.verify_payment(user=request.user, payment_id=payment_id)
    except PaymentAuthorizationError:
        return api_error(request, code='PERMISSION_DENIED', message='This payment does not belong to you', status_code=403)

    if error == 'PAYMENT_NOT_FOUND':
        return api_error(request, code='PAYMENT_NOT_FOUND', message='Payment not found', status_code=404)
    if error and error != 'NO_ATTEMPT_TO_VERIFY':
        return api_error(request, code=error, message=error.replace('_', ' ').title(), status_code=_ERROR_STATUS.get(error, 400))

    return api_success(request, data=_payment_dict(payment))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refund_payment(request):
    """Admin-only refund. Requires an IsAuthenticated + staff check (mirrored from
    PaymentService.refund, which is the actual enforcement point) so a non-staff
    caller gets a clean 403 before any refund logic runs."""
    if not getattr(request.user, 'is_staff', False):
        return api_error(request, code='PERMISSION_DENIED', message='Only staff may issue refunds', status_code=403)

    payment_id = request.data.get('payment_id')
    if not payment_id:
        return api_error(request, code='VALIDATION_ERROR', message='payment_id is required', status_code=400)

    amount = None
    if request.data.get('amount') is not None:
        try:
            amount = Decimal(str(request.data['amount']))
        except InvalidOperation:
            return api_error(request, code='VALIDATION_ERROR', message='amount must be a valid decimal', status_code=400)

    try:
        refund, error = PaymentService.refund(
            user=request.user, payment_id=payment_id, amount=amount,
            reason=request.data.get('reason', ''),
            idempotency_key=request.data.get('idempotency_key'),
        )
    except PaymentAuthorizationError:
        return api_error(request, code='PERMISSION_DENIED', message='Only staff may issue refunds', status_code=403)

    if error == 'PAYMENT_NOT_FOUND':
        return api_error(request, code='PAYMENT_NOT_FOUND', message='Payment not found', status_code=404)
    if error:
        return api_error(request, code=error, message=error.replace('_', ' ').title(), status_code=_ERROR_STATUS.get(error, 400))

    return api_success(request, data={
        'id': refund.id, 'payment_id': refund.payment_id, 'amount': str(refund.amount),
        'status': refund.status, 'gateway_refund_id': refund.gateway_refund_id,
    })


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def payment_webhook(request):
    """Gateway webhook receiver. AllowAny because the gateway itself calls this, not
    an authenticated app user - authenticity comes entirely from
    PaymentService.handle_webhook's signature verification, not from Django auth.

    Refuses (503) rather than store-and-process while the gateway is unconfigured -
    an unverifiable signature must never be trusted enough to change payment state.
    """
    status_code, event = PaymentService.handle_webhook(headers=request.headers, body=request.body)

    if status_code == 'GATEWAY_NOT_CONFIGURED':
        return Response({'error': 'PAYMENT_GATEWAY_NOT_CONFIGURED'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    if status_code == 'INVALID_SIGNATURE':
        return Response({'error': 'INVALID_SIGNATURE'}, status=status.HTTP_400_BAD_REQUEST)
    # DUPLICATE and PROCESSED both return 200 - a webhook sender should not retry
    # either case, and a duplicate delivery is not an error from the gateway's
    # perspective, just a no-op on our side.
    return Response({'status': status_code}, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def payment_methods(request):
    """List or add the user's saved payment methods. Unaffected by the fake-payment
    bug - PaymentMethod never simulated a charge, it only ever stored user preference
    metadata - but wired up for real here since it was also a stub before."""
    if request.method == 'GET':
        methods = PaymentMethod.objects.filter(user=request.user).order_by('-is_default', '-created_at')
        data = [{
            'id': m.id, 'method_type': m.method_type, 'is_default': m.is_default,
            'details': m.details, 'created_at': m.created_at.isoformat(),
        } for m in methods]
        return api_success(request, data=data)

    method_type = request.data.get('method_type')
    valid_types = dict(PaymentMethod.METHOD_CHOICES)
    if method_type not in valid_types:
        return api_error(request, code='VALIDATION_ERROR', message=f"method_type must be one of {list(valid_types)}", status_code=400)

    # Never accept raw card numbers/CVV (Phase 3 brief workstream 16) - `details` is
    # for non-sensitive metadata only (e.g. a gateway-issued card token, last 4
    # digits, brand). This is enforced by simple key-blocking rather than a full PCI
    # tokenization flow, which is out of scope until the gateway integration exists.
    details = request.data.get('details', {}) or {}
    blocked_keys = {'card_number', 'cvv', 'cvc', 'card_number_full', 'pan'}
    if blocked_keys & set(k.lower() for k in details.keys()):
        return api_error(
            request, code='VALIDATION_ERROR',
            message='Raw card numbers/CVV must never be sent to or stored by this API',
            status_code=400,
        )

    method = PaymentMethod.objects.create(
        user=request.user, method_type=method_type,
        is_default=bool(request.data.get('is_default', False)), details=details,
    )
    return api_created(request, data={
        'id': method.id, 'method_type': method.method_type,
        'is_default': method.is_default, 'details': method.details,
    })


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def payment_method_detail(request, pk):
    try:
        method = PaymentMethod.objects.get(pk=pk, user=request.user)
    except PaymentMethod.DoesNotExist:
        return api_error(request, code='NOT_FOUND', message='Payment method not found', status_code=404)

    if request.method == 'GET':
        return api_success(request, data={
            'id': method.id, 'method_type': method.method_type,
            'is_default': method.is_default, 'details': method.details,
        })
    elif request.method == 'PUT':
        if 'is_default' in request.data:
            method.is_default = bool(request.data['is_default'])
        method.save()
        return api_success(request, data={'id': method.id, 'is_default': method.is_default})
    else:
        method.delete()
        return api_success(request, message='Payment method deleted')
