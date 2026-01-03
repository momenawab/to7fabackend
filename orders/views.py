from django.shortcuts import render, get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from api.helpers import api_response, api_error, api_success, api_created
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderDetailSerializer
from .atomic_order_system import (
    OrderStateMachine,
    AtomicOrderCreator,
    WalletOrderCoordinator,
    StockLockManager
)
from django.db import transaction
from django.db.models import Q
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_list(request):
    """Get all orders for authenticated user"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    serializer = OrderSerializer(orders, many=True, context={'request': request})
    return api_success(request, data=serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_detail(request, pk):
    """Get order details"""
    order = get_object_or_404(Order, pk=pk)
    
    # Check if user is owner of order or seller of any item in the order
    is_owner = order.user == request.user
    is_seller = OrderItem.objects.filter(order=order, seller=request.user).exists()
    
    if not (is_owner or is_seller):
        return api_error(
            request,
            code='PERMISSION_DENIED',
            message="You don't have permission to view this order",
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    serializer = OrderDetailSerializer(order, context={'request': request})
    return api_success(request, data=serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_order(request):
    """
    Create a new order atomically.
    
    This endpoint:
    - Uses AtomicOrderCreator for atomic order creation
    - Prevents overselling through stock locking
    - Prevents duplicate orders through idempotency
    - Coordinates wallet payment atomically
    - Provides complete rollback on any failure
    
    Request body:
    {
        "items_data": [
            {"product_id": 1, "quantity": 2, "variant_id": null},
            {"product_id": 2, "quantity": 1, "variant_id": 5}
        ],
        "shipping_address": "123 Main St, City, Country",
        "shipping_cost": 15.50,
        "payment_method": "wallet",
        "idempotency_key": "order_12345_abcde",
        "use_wallet_payment": true
    }
    """
    serializer = OrderSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        try:
            order = serializer.save()
            return api_created(request, data=OrderDetailSerializer(order, context={'request': request}).data)
        except ValueError as e:
            # Known business logic errors (insufficient stock, etc.)
            return api_error(
                request,
                code='VALIDATION_ERROR',
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            # Unexpected errors
            logger.error(f"Unexpected error creating order: {str(e)}", exc_info=True)
            return api_error(
                request,
                code='INTERNAL_ERROR',
                message="Failed to create order. Please try again.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    return api_error(
        request,
        code='VALIDATION_ERROR',
        message='Validation failed',
        details=serializer.errors,
        status_code=status.HTTP_400_BAD_REQUEST
    )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def cancel_order(request, pk):
    """
    Cancel an order atomically with proper rollback.
    
    This endpoint:
    - Validates order belongs to user
    - Validates order can be cancelled
    - Releases all reserved stock
    - Refunds payment if applicable
    - Updates order status to CANCELLED
    - All operations are atomic
    
    Valid cancellation states: pending, paid
    """
    try:
        success, order, error = AtomicOrderCreator.cancel_order(
            order_id=pk,
            user=request.user
        )
        
        if not success:
            return api_error(
                request,
                code='VALIDATION_ERROR',
                message=error,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        return api_success(request, data=OrderDetailSerializer(order, context={'request': request}).data)
        
    except Exception as e:
        logger.error(f"Error cancelling order {pk}: {str(e)}", exc_info=True)
        return api_error(
            request,
            code='INTERNAL_ERROR',
            message="Failed to cancel order. Please try again.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_order_status(request, pk):
    """
    Update order status by seller with state machine validation.
    
    This endpoint:
    - Validates user is a seller
    - Validates seller owns items in order
    - Uses OrderStateMachine to validate transitions
    - Prevents invalid state changes
    
    Valid transitions:
    - pending -> paid (payment captured)
    - paid -> shipped (seller shipped)
    - shipped -> completed (delivery confirmed)
    - pending -> cancelled (user cancelled)
    - paid -> cancelled (refund required)
    """
    # Check if user is a seller
    if request.user.user_type not in ['artist', 'store']:
        return api_error(
            request,
            code='PERMISSION_DENIED',
            message="Only sellers can access this endpoint",
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # Check if order exists and contains items sold by this seller
    order = get_object_or_404(Order, pk=pk)
    if not OrderItem.objects.filter(order=order, seller=request.user).exists():
        return api_error(
            request,
            code='PERMISSION_DENIED',
            message="You don't have permission to update this order",
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # Validate new status
    new_status = request.data.get('status')
    if not new_status or new_status not in [s[0] for s in Order.STATUS_CHOICES]:
        return api_error(
            request,
            code='INVALID_STATUS',
            message=f"Invalid status. Must be one of: {', '.join([s[0] for s in Order.STATUS_CHOICES])}",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate state transition using state machine
    try:
        OrderStateMachine.validate_transition(order.status, new_status)
    except ValueError as e:
        return api_error(
            request,
            code='INVALID_TRANSITION',
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Update order status with lock to prevent race conditions
    # Lock order row to ensure only one status update at a time
    from django.db import transaction
    with transaction.atomic():
        locked_order = Order.objects.select_for_update().get(id=pk)
        locked_order.status = new_status
        locked_order.save()
        logger.info(f"Order {pk} status updated from {locked_order.status} to {new_status} by seller {request.user.id}")
    
    return api_success(request, data=OrderDetailSerializer(locked_order, context={'request': request}).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def capture_payment(request, pk):
    """
    Capture payment for a pending order.
    
    This endpoint:
    - Validates order belongs to user
    - Marks pending payment transaction as completed
    - Updates order status to 'paid'
    - All operations are atomic
    
    Only applicable for orders with pending payment transactions.
    """
    try:
        order = get_object_or_404(Order, pk=pk)
        
        # Validate ownership
        if order.user != request.user:
            return api_error(
                request,
                code='PERMISSION_DENIED',
                message="You don't have permission to capture payment for this order",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Validate order status
        if order.status != 'pending':
            return api_error(
                request,
                code='INVALID_STATUS',
                message=f"Cannot capture payment for order with status '{order.status}'",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Capture payment atomically
        idempotency_key = request.data.get('idempotency_key') or f"capture_{order.id}"
        success, tx, error = WalletOrderCoordinator.capture_payment(
            order_id=pk,
            idempotency_key=idempotency_key
        )
        
        if not success:
            return api_error(
                request,
                code='PAYMENT_ERROR',
                message=error,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Return updated order
        order.refresh_from_db()
        return api_success(request, data=OrderDetailSerializer(order, context={'request': request}).data)
        
    except Exception as e:
        logger.error(f"Error capturing payment for order {pk}: {str(e)}", exc_info=True)
        return api_error(
            request,
            code='INTERNAL_ERROR',
            message="Failed to capture payment. Please try again.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def release_payment(request, pk):
    """
    Release payment (refund) for an order.
    
    This endpoint:
    - Validates order belongs to user
    - Creates refund transaction
    - Marks original payment as failed
    - Updates order status to 'cancelled'
    - All operations are atomic
    
    Only applicable for orders with pending payment transactions.
    """
    try:
        order = get_object_or_404(Order, pk=pk)
        
        # Validate ownership
        if order.user != request.user:
            return api_error(
                request,
                code='PERMISSION_DENIED',
                message="You don't have permission to release payment for this order",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # Validate order status
        if order.status not in ['pending', 'paid']:
            return api_error(
                request,
                code='INVALID_STATUS',
                message=f"Cannot release payment for order with status '{order.status}'",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Release payment atomically
        idempotency_key = request.data.get('idempotency_key') or f"release_{order.id}"
        refund_reason = request.data.get('refund_reason', 'Payment released by user')
        
        success, refund_tx, error = WalletOrderCoordinator.release_payment(
            order_id=pk,
            idempotency_key=idempotency_key,
            refund_reason=refund_reason
        )
        
        if not success:
            return api_error(
                request,
                code='PAYMENT_ERROR',
                message=error,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Return updated order
        order.refresh_from_db()
        return api_success(request, data=OrderDetailSerializer(order, context={'request': request}).data)
        
    except Exception as e:
        logger.error(f"Error releasing payment for order {pk}: {str(e)}", exc_info=True)
        return api_error(
            request,
            code='INTERNAL_ERROR',
            message="Failed to release payment. Please try again.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def seller_orders(request):
    """Get all orders for authenticated seller"""
    # Check if user is a seller
    if request.user.user_type not in ['artist', 'store']:
        return api_error(
            request,
            code='PERMISSION_DENIED',
            message="Only sellers can access this endpoint",
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # Get orders that contain items sold by this seller
    order_items = OrderItem.objects.filter(seller=request.user)
    order_ids = order_items.values_list('order_id', flat=True).distinct()
    orders = Order.objects.filter(id__in=order_ids).order_by('-created_at')
    
    serializer = OrderSerializer(orders, many=True, context={'request': request})
    return api_success(request, data=serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_orders_for_support(request):
    """Get simplified user orders list for support ticket creation"""
    try:
        orders = Order.objects.filter(user=request.user).order_by('-created_at')[:20]  # Latest 20 orders
        
        orders_data = []
        for order in orders:
            orders_data.append({
                'id': str(order.id),
                'total_amount': str(order.total_amount),
                'status': order.get_status_display(),
                'created_at': order.created_at.strftime('%Y-%m-%d'),
                'item_count': order.items.count(),
            })
        
        return api_success(request, data={'orders': orders_data})
    except Exception as e:
        logger.error(f"Error getting orders for support: {str(e)}", exc_info=True)
        return api_error(
            request,
            code='INTERNAL_ERROR',
            message=str(e),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_complete_order(request, pk):
    """
    Admin endpoint to mark an order as completed.
    
    This endpoint:
    - Validates order exists
    - Uses OrderStateMachine to validate transition
    - Updates order status to 'completed'
    """
    try:
        order = get_object_or_404(Order, pk=pk)
        
        # Validate state transition
        OrderStateMachine.validate_transition(order.status, 'completed')
        
        # Update order status
        order.status = 'completed'
        order.save()
        
        logger.info(f"Order {pk} marked as completed by admin {request.user.id}")
        return api_success(request, data=OrderDetailSerializer(order, context={'request': request}).data)
        
    except ValueError as e:
        return api_error(
            request,
            code='INVALID_TRANSITION',
            message=str(e),
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Error completing order {pk}: {str(e)}", exc_info=True)
        return api_error(
            request,
            code='INTERNAL_ERROR',
            message="Failed to complete order. Please try again.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_states(request):
    """
    Get available order states and valid transitions.
    
    This endpoint provides information about:
    - All possible order states
    - Valid transitions from each state
    - Which states can be cancelled
    """
    return api_success(request, data={
        'states': [
            {'value': value, 'label': label}
            for value, label in Order.STATUS_CHOICES
        ],
        'valid_transitions': OrderStateMachine.VALID_TRANSITIONS,
        'cancellable_states': ['pending', 'paid'],
        'refund_required_states': ['paid']
    })
