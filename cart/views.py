from django.shortcuts import render, get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Cart, CartItem
from products.models import Product
from .serializers import (
    CartSerializer, 
    CartItemSerializer, 
    AddToCartSerializer, 
    UpdateCartItemSerializer
)

# Create your views here.

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cart_detail(request):
    """
    Get the current user's cart details
    """
    # Get or create cart for the user
    cart, created = Cart.objects.get_or_create(user=request.user)
    serializer = CartSerializer(cart, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_cart(request):
    """
    Add a product to the cart
    """
    serializer = AddToCartSerializer(data=request.data)
    if serializer.is_valid():
        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data['quantity']
        selected_variants = serializer.validated_data.get('selected_variants')
        variant_id = serializer.validated_data.get('variant_id')
        
        # Get the product
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        # Get or create cart for the user
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        try:
            # Add the product to the cart with variant information
            cart_item = cart.add_item(
                product=product, 
                quantity=quantity,
                selected_variants=selected_variants,
                variant_id=variant_id
            )
            
            # Return the updated cart
            cart_serializer = CartSerializer(cart, context={'request': request})
            return Response(cart_serializer.data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_cart_item(request, item_id):
    """
    Update the quantity of a cart item
    """
    # Get the cart item
    cart_item = get_object_or_404(CartItem, id=item_id)
    
    # Check if the cart belongs to the current user
    if cart_item.cart.user != request.user:
        return Response(
            {"error": "You don't have permission to modify this cart item"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = UpdateCartItemSerializer(
        data=request.data,
        context={'product': cart_item.product}
    )
    
    if serializer.is_valid():
        quantity = serializer.validated_data['quantity']
        
        # Get the cart
        cart = cart_item.cart
        
        try:
            if quantity > 0:
                # Update the item quantity
                cart.update_item_by_id(item_id, quantity)
            else:
                # Remove the item if quantity is 0
                cart.remove_item_by_id(item_id)
            
            # Return the updated cart
            cart_serializer = CartSerializer(cart, context={'request': request})
            return Response(cart_serializer.data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_cart(request, item_id):
    """
    Remove an item from the cart
    """
    # Get the cart item
    cart_item = get_object_or_404(CartItem, id=item_id)
    
    # Check if the cart belongs to the current user
    if cart_item.cart.user != request.user:
        return Response(
            {"error": "You don't have permission to modify this cart item"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get the cart
    cart = cart_item.cart
    
    # Remove the item
    cart.remove_item_by_id(item_id)
    
    # Return the updated cart
    cart_serializer = CartSerializer(cart, context={'request': request})
    return Response(cart_serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def clear_cart(request):
    """
    Remove all items from the cart
    """
    # Get the user's cart
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Clear the cart
    cart.clear()
    
    # Return the empty cart
    cart_serializer = CartSerializer(cart, context={'request': request})
    return Response(cart_serializer.data, status=status.HTTP_200_OK)
