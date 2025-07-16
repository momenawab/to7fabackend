from django.shortcuts import render, get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Order, OrderItem
from .serializers import OrderSerializer, OrderDetailSerializer
from django.db import transaction
from django.db.models import Q
from decimal import Decimal

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_list(request):
    """Get all orders for the authenticated user"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_detail(request, pk):
    """Get order details"""
    order = get_object_or_404(Order, pk=pk)
    
    # Check if the user is the owner of the order or the seller of any item in the order
    is_owner = order.user == request.user
    is_seller = OrderItem.objects.filter(order=order, seller=request.user).exists()
    
    if not (is_owner or is_seller):
        return Response({"error": "You don't have permission to view this order"}, 
                        status=status.HTTP_403_FORBIDDEN)
    
    serializer = OrderDetailSerializer(order)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_order(request):
    """Create a new order"""
    # Convert shipping_cost to Decimal if it exists in the request data
    if 'shipping_cost' in request.data and not isinstance(request.data['shipping_cost'], Decimal):
        try:
            request.data['shipping_cost'] = Decimal(str(request.data['shipping_cost']))
        except (ValueError, TypeError):
            return Response({"error": "Invalid shipping_cost value"}, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = OrderSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        try:
            order = serializer.save()
            return Response(OrderDetailSerializer(order).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def cancel_order(request, pk):
    """Cancel an order"""
    order = get_object_or_404(Order, pk=pk, user=request.user)
    
    # Only pending or processing orders can be cancelled
    if order.status not in ['pending', 'processing']:
        return Response({"error": f"Cannot cancel order with status '{order.status}'"}, 
                        status=status.HTTP_400_BAD_REQUEST)
    
    with transaction.atomic():
        # Update order status
        order.status = 'cancelled'
        order.save()
        
        # Restore product stock
        for item in order.items.all():
            product = item.product
            product.stock += item.quantity
            product.save()
    
    return Response(OrderDetailSerializer(order).data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def seller_orders(request):
    """Get all orders for the authenticated seller"""
    # Check if the user is a seller
    if request.user.user_type not in ['artist', 'store']:
        return Response({"error": "Only sellers can access this endpoint"}, 
                        status=status.HTTP_403_FORBIDDEN)
    
    # Get orders that contain items sold by this seller
    order_items = OrderItem.objects.filter(seller=request.user)
    order_ids = order_items.values_list('order_id', flat=True).distinct()
    orders = Order.objects.filter(id__in=order_ids).order_by('-created_at')
    
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_order_status(request, pk):
    """Update order status by seller"""
    # Check if the user is a seller
    if request.user.user_type not in ['artist', 'store']:
        return Response({"error": "Only sellers can access this endpoint"}, 
                        status=status.HTTP_403_FORBIDDEN)
    
    # Check if the order exists and contains items sold by this seller
    order = get_object_or_404(Order, pk=pk)
    if not OrderItem.objects.filter(order=order, seller=request.user).exists():
        return Response({"error": "You don't have permission to update this order"}, 
                        status=status.HTTP_403_FORBIDDEN)
    
    # Validate the new status
    new_status = request.data.get('status')
    if not new_status or new_status not in [s[0] for s in Order.STATUS_CHOICES]:
        return Response({"error": f"Invalid status. Must be one of: {', '.join([s[0] for s in Order.STATUS_CHOICES])}"}, 
                        status=status.HTTP_400_BAD_REQUEST)
    
    # Update the order status
    order.status = new_status
    order.save()
    
    return Response(OrderDetailSerializer(order).data)
