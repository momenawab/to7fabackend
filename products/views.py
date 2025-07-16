from django.shortcuts import render, get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Product, Category, Review
from .serializers import ProductSerializer, ProductDetailSerializer, CategorySerializer, ReviewSerializer
from django.db.models import Q

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])  # GET is public, POST requires authentication (handled in view)
def product_list(request):
    """Get all products or create a new product"""
    if request.method == 'GET':
        # Get active products only
        products = Product.objects.filter(is_active=True).order_by('-created_at')
        
        # Filter by category if provided
        category_id = request.query_params.get('category')
        if category_id:
            products = products.filter(category_id=category_id)
            
        # Filter by featured if provided
        featured = request.query_params.get('featured')
        if featured and featured.lower() == 'true':
            products = products.filter(is_featured=True)
        
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        # Only authenticated users can create products
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        
        serializer = ProductSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            product = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([AllowAny])  # GET is public, PUT/DELETE requires authentication (handled in view)
def product_detail(request, pk):
    """Get, update or delete a product"""
    try:
        product = Product.objects.get(pk=pk, is_active=True)
    except Product.DoesNotExist:
        return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = ProductDetailSerializer(product)
        return Response(serializer.data)
    
    # For PUT and DELETE, check if the user is the seller
    if not request.user.is_authenticated:
        return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
    
    if product.seller != request.user:
        return Response({"error": "You don't have permission to modify this product"}, 
                        status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'PUT':
        serializer = ProductSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        product.delete()
        return Response({"message": "Product deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
@permission_classes([AllowAny])
def product_search(request):
    """Search products by name, description, or category"""
    query = request.query_params.get('q', '')
    if not query:
        return Response({"error": "Search query parameter 'q' is required"}, 
                        status=status.HTTP_400_BAD_REQUEST)
    
    # Search in name and description
    products = Product.objects.filter(
        Q(name__icontains=query) | Q(description__icontains=query),
        is_active=True
    ).order_by('-created_at')
    
    # Filter by category if provided
    category_id = request.query_params.get('category')
    if category_id:
        products = products.filter(category_id=category_id)
    
    serializer = ProductSerializer(products, many=True)
    return Response({
        "query": query,
        "results_count": products.count(),
        "results": serializer.data
    })

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])  # GET is public, POST requires authentication (handled in view)
def product_reviews(request, pk):
    """Get all reviews for a product or add a new review"""
    # Check if product exists
    try:
        product = Product.objects.get(pk=pk, is_active=True)
    except Product.DoesNotExist:
        return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        reviews = Review.objects.filter(product=product).order_by('-created_at')
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        # Only authenticated users can add reviews
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Check if user has already reviewed this product
        if Review.objects.filter(product=product, user=request.user).exists():
            return Response({"error": "You have already reviewed this product"}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
        # Create review
        data = request.data.copy()
        data['product'] = pk
        serializer = ReviewSerializer(data=data, context={'request': request})
        
        if serializer.is_valid():
            serializer.save(user=request.user, product=product)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])  # GET is public, POST requires authentication (handled in view)
def category_list(request):
    """Get all categories or create a new category"""
    if request.method == 'GET':
        categories = Category.objects.filter(is_active=True)
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        # Only authenticated users with staff permissions can create categories
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        
        if not request.user.is_staff:
            return Response({"error": "Staff permissions required"}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([AllowAny])  # GET is public, PUT/DELETE requires staff permissions (handled in view)
def category_detail(request, pk):
    """Get category details, update or delete a category"""
    try:
        category = Category.objects.get(pk=pk)
    except Category.DoesNotExist:
        return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = CategorySerializer(category)
        # Get products in this category
        products = Product.objects.filter(category=category, is_active=True)
        product_serializer = ProductSerializer(products, many=True)
        return Response({
            "category": serializer.data,
            "products": product_serializer.data
        })
    
    # Only staff can update or delete categories
    if not request.user.is_authenticated:
        return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
    
    if not request.user.is_staff:
        return Response({"error": "Staff permissions required"}, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'PUT':
        serializer = CategorySerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        category.delete()
        return Response({"message": "Category deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def seller_products(request):
    """Get all products for the authenticated seller or create a new product"""
    # Check if the user is a seller (artist or store)
    if request.user.user_type not in ['artist', 'store']:
        return Response({"error": "Only sellers can access this endpoint"}, 
                        status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        products = Product.objects.filter(seller=request.user).order_by('-created_at')
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = ProductSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            product = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def seller_product_detail(request, pk):
    """Get, update or delete a seller's product"""
    # Check if the user is a seller (artist or store)
    if request.user.user_type not in ['artist', 'store']:
        return Response({"error": "Only sellers can access this endpoint"}, 
                        status=status.HTTP_403_FORBIDDEN)
    
    try:
        product = Product.objects.get(pk=pk, seller=request.user)
    except Product.DoesNotExist:
        return Response({"error": "Product not found or you don't have permission to access it"}, 
                        status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = ProductDetailSerializer(product)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = ProductSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        product.delete()
        return Response({"message": "Product deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
