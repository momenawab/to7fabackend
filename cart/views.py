from django.shortcuts import render, get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from api.helpers import api_response, api_error, api_success, api_created
from .models import Cart, CartItem
from products.models import Product
from .serializers import (
    CartSerializer,
    CartItemSerializer,
    AddToCartSerializer,
    UpdateCartItemSerializer
)

# Create your views here.


def get_or_create_cart(request):
    """
    Get or create cart based on authentication or session_id.
    For authenticated users: get/create user cart
    For guests: get/create cart using X-Session-ID header
    """
    if request.user.is_authenticated:
        # Authenticated user - get or create user cart
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        # Guest user - get or create cart using session_id from header
        session_id = request.META.get('HTTP_X_SESSION_ID')
        if not session_id:
            # Generate new session_id if not provided
            import uuid
            session_id = str(uuid.uuid4())
        
        # Get or create guest cart
        cart, created = Cart.objects.get_or_create(session_id=session_id)
    
    return cart, created


@api_view(['GET'])
@permission_classes([AllowAny])
def cart_detail(request):
    """
    Get current user's cart details (supports both authenticated and guest users)
    """
    # Get or create cart based on authentication or session_id
    cart, created = get_or_create_cart(request)
    serializer = CartSerializer(cart, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([AllowAny])
def add_to_cart(request):
    """
    Add a product to cart (supports both authenticated and guest users).

    Spec 004 C.4, INV-011: Cart operations MUST validate approval_status='approved'
    """
    serializer = AddToCartSerializer(data=request.data)
    if serializer.is_valid():
        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data['quantity']
        selected_variants = serializer.validated_data.get('selected_variants')
        variant_id = serializer.validated_data.get('variant_id')

        # Get product
        product = get_object_or_404(Product, id=product_id, is_active=True)

        # Spec 004 INV-011: Unapproved products cannot be added to cart
        if product.approval_status != 'approved':
            return Response({
                "error": "PRODUCT_NOT_APPROVED",
                "message": "Product must be approved before adding to cart",
                "details": {
                    "product_id": product_id,
                    "approval_status": product.approval_status
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get or create cart based on authentication or session_id
        cart, created = get_or_create_cart(request)

        try:
            # Add product to cart with variant information
            cart_item = cart.add_item(
                product=product,
                quantity=quantity,
                selected_variants=selected_variants,
                variant_id=variant_id
            )

            # Return updated cart
            cart_serializer = CartSerializer(cart, context={'request': request})
            return Response(cart_serializer.data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([AllowAny])
def update_cart_item(request, item_id):
    """
    Update quantity of a cart item (supports both authenticated and guest users)
    """
    # Get cart item
    cart_item = get_object_or_404(CartItem, id=item_id)
    
    # Check if cart belongs to current user or session
    if request.user.is_authenticated:
        if cart_item.cart.user != request.user:
            return Response(
                {"error": "You don't have permission to modify this cart item"},
                status=status.HTTP_403_FORBIDDEN
            )
    else:
        # For guest users, check session_id
        session_id = request.META.get('HTTP_X_SESSION_ID')
        if cart_item.cart.session_id != session_id:
            return Response(
                {"error": "You don't have permission to modify this cart item"},
                status=status.HTTP_403_FORBIDDEN
            )
    
    serializer = UpdateCartItemSerializer(
        data=request.data,
        context={'product': cart_item.product, 'variant_id': cart_item.variant_id}
    )
    
    if serializer.is_valid():
        quantity = serializer.validated_data['quantity']
        
        # Get cart
        cart = cart_item.cart
        
        try:
            if quantity > 0:
                # Update the item quantity
                cart.update_item_by_id(item_id, quantity)
            else:
                # Remove the item if quantity is 0
                cart.remove_item_by_id(item_id)
            
            # Return updated cart
            cart_serializer = CartSerializer(cart, context={'request': request})
            return Response(cart_serializer.data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([AllowAny])
def remove_from_cart(request, item_id):
    """
    Remove an item from cart (supports both authenticated and guest users)
    """
    # Get cart item
    cart_item = get_object_or_404(CartItem, id=item_id)
    
    # Check if cart belongs to current user or session
    if request.user.is_authenticated:
        if cart_item.cart.user != request.user:
            return Response(
                {"error": "You don't have permission to modify this cart item"},
                status=status.HTTP_403_FORBIDDEN
            )
    else:
        # For guest users, check session_id
        session_id = request.META.get('HTTP_X_SESSION_ID')
        if cart_item.cart.session_id != session_id:
            return Response(
                {"error": "You don't have permission to modify this cart item"},
                status=status.HTTP_403_FORBIDDEN
            )
    
    # Get cart
    cart = cart_item.cart
    
    # Remove item
    cart.remove_item_by_id(item_id)
    
    # Return updated cart
    cart_serializer = CartSerializer(cart, context={'request': request})
    return Response(cart_serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def clear_cart(request):
    """
    Remove all items from cart (supports both authenticated and guest users)
    """
    # Get cart based on authentication or session_id
    cart, created = get_or_create_cart(request)
    
    # Clear cart
    cart.clear()
    
    # Return empty cart
    cart_serializer = CartSerializer(cart, context={'request': request})
    return Response(cart_serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def merge_cart(request):
    """
    Merge guest cart into authenticated user's cart

    Request:
    {
        "session_id": "550e8400-e29b-41d4-a716-446655440000"
    }

    Response (Success):
    {
        "message": "Cart merged successfully",
        "items_added": 3,
        "items_skipped": 1
    }

    Response (Not Found):
    {
        "error": "CART_NOT_FOUND",
        "message": "No guest cart found for this session"
    }
    """
    session_id = request.data.get('session_id', '')

    if not session_id:
        return Response(
            {"error": "MISSING_SESSION_ID", "message": "session_id is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Merge guest cart into user cart
    from .services.cart_merge import merge_guest_cart
    result = merge_guest_cart(request.user, session_id)

    if result['success']:
        return Response({
            "message": "Cart merged successfully",
            "items_added": result['items_added'],
            "items_skipped": result['items_skipped']
        }, status=status.HTTP_200_OK)
    else:
        return Response(
            {"error": "CART_NOT_FOUND", "message": result.get('error', 'No guest cart found for this session')},
            status=status.HTTP_404_NOT_FOUND
        )
