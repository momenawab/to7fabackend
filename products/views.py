from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import (
    Product, Category, Review, Advertisement, ContentSettings, ProductOffer, FeaturedProduct,
    ProductAttribute, ProductAttributeOption, CategoryAttribute, Tag, CategoryVariantType,
    CategoryVariantOption, DiscountRequest, ProductVariant, ProductVariantOption, SubcategorySectionControl
)
from .serializers import (
    ProductSerializer, ProductDetailSerializer, CategorySerializer, ReviewSerializer,
    ProductAttributeSerializer, ProductAttributeOptionSerializer, CategoryAttributeSerializer,
    SubcategorySectionControlSerializer
)
from django.db.models import Q, Count
from django.utils import timezone

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

        # Get products in this category AND all its subcategories
        # This is crucial for ReactiveSubcategorySections to work properly
        if category.parent is None:
            # For main categories: get direct products + all subcategory products
            subcategories = Category.objects.filter(parent=category, is_active=True)
            subcategory_ids = [sub.id for sub in subcategories]

            # Get products from main category and all its subcategories
            products = Product.objects.filter(
                category_id__in=[category.id] + subcategory_ids,
                is_active=True
            ).order_by('-created_at')
        else:
            # For subcategories: only get products directly assigned to this subcategory
            products = Product.objects.filter(category=category, is_active=True)

        product_serializer = ProductSerializer(products, many=True)

        # Include subcategories in response for ReactiveSubcategorySections
        if category.parent is None:
            # For main categories, include subcategories list with section control info
            subcategories_data = []
            for sub in subcategories:
                # Get section control info if it exists
                section_enabled = True  # Default to enabled
                max_products = 4  # Default max products
                section_priority = 0  # Default priority

                try:
                    from .models import SubcategorySectionControl
                    section_control = SubcategorySectionControl.objects.get(subcategory=sub)
                    section_enabled = section_control.is_section_enabled
                    max_products = section_control.max_products_to_show
                    section_priority = section_control.section_priority
                except SubcategorySectionControl.DoesNotExist:
                    pass  # Use defaults

                subcategories_data.append({
                    'id': sub.id,
                    'name': sub.name,
                    'description': sub.description,
                    'parent': sub.parent.id if sub.parent else None,
                    'image': sub.image.url if sub.image else None,
                    'is_active': sub.is_active,
                    'section_enabled': section_enabled,
                    'max_products': max_products,
                    'section_priority': section_priority,
                })

            return Response({
                "category": serializer.data,
                "products": product_serializer.data,
                "subcategories": subcategories_data
            })
        else:
            # For subcategories, no need to include subcategories list
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

# New admin-controlled content endpoints

@api_view(['GET'])
@permission_classes([AllowAny])
def latest_offers(request):
    """Get latest products with offers/discounts"""
    limit = request.query_params.get('limit', 10)
    try:
        limit = int(limit)
    except (ValueError, TypeError):
        limit = 10

    # Get settings to check if this section should be shown
    settings = ContentSettings.get_settings()
    if not settings.show_latest_offers:
        return Response({
            'results': [],
            'count': 0,
            'message': 'Latest offers section is currently disabled'
        })

    # Get current active offers
    now = timezone.now()
    offers = ProductOffer.objects.filter(
        is_active=True,
        start_date__lte=now,
        end_date__gte=now,
        product__is_active=True
    ).select_related('product', 'product__category').order_by('-created_at')[:min(limit, settings.max_products_per_section)]

    # Serialize the products with offer information
    results = []
    for offer in offers:
        product_data = ProductSerializer(offer.product, context={'request': request}).data
        # Add offer-specific data for Flutter app
        product_data.update({
            'offer_id': offer.id,
            'original_price': float(offer.product.price),
            'offer_price': float(offer.offer_price),
            'discount_percentage': offer.discount_percentage,
            'savings_amount': float(offer.savings_amount),
            'offer_description': offer.description,
            'offer_end_date': offer.end_date.isoformat(),
            'is_offer': True
        })
        results.append(product_data)

    return Response({
        'results': results,
        'count': len(results),
        'settings': {
            'max_items': settings.max_products_per_section,
            'refresh_interval': settings.content_refresh_interval
        }
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def featured_products(request):
    """Get featured products"""
    limit = request.query_params.get('limit', 10)
    try:
        limit = int(limit)
    except (ValueError, TypeError):
        limit = 10

    # Get settings to check if this section should be shown
    settings = ContentSettings.get_settings()
    if not settings.show_featured_products:
        return Response({
            'results': [],
            'count': 0,
            'message': 'Featured products section is currently disabled'
        })

    # Get current featured products from FeaturedProduct model
    now = timezone.now()
    featured_products = FeaturedProduct.objects.filter(
        is_active=True,
        product__is_active=True
    ).filter(
        Q(featured_until__isnull=True) | Q(featured_until__gte=now)
    ).select_related('product', 'product__category').order_by('priority', '-featured_since')[:min(limit, settings.max_products_per_section)]

    # Serialize the products with featured information
    results = []
    for featured in featured_products:
        product_data = ProductSerializer(featured.product, context={'request': request}).data
        # Add featured-specific data for Flutter app
        product_data.update({
            'featured_id': featured.id,
            'featured_since': featured.featured_since.isoformat(),
            'featured_until': featured.featured_until.isoformat() if featured.featured_until else None,
            'featured_reason': featured.reason,
            'featured_priority': featured.priority,
            'is_featured': True
        })

        # Check if this product also has an active offer
        active_offer = ProductOffer.objects.filter(
            product=featured.product,
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        ).first()

        if active_offer:
            product_data.update({
                'offer_id': active_offer.id,
                'original_price': float(featured.product.price),
                'offer_price': float(active_offer.offer_price),
                'discount_percentage': active_offer.discount_percentage,
                'savings_amount': float(active_offer.savings_amount),
                'offer_description': active_offer.description,
                'offer_end_date': active_offer.end_date.isoformat(),
                'is_offer': True,
                'has_both_featured_and_offer': True
            })

        results.append(product_data)

    return Response({
        'results': results,
        'count': len(results),
        'settings': {
            'max_items': settings.max_products_per_section,
            'refresh_interval': settings.content_refresh_interval
        }
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def top_rated_products(request):
    """Get top rated products"""
    limit = request.query_params.get('limit', 10)
    try:
        limit = int(limit)
    except (ValueError, TypeError):
        limit = 10

    # Get settings
    settings = ContentSettings.get_settings()

    # Get products with reviews and order by average rating
    products = Product.objects.filter(
        is_active=True,
        reviews__isnull=False
    ).annotate(
        review_count=Count('reviews')
    ).filter(
        review_count__gt=0
    ).order_by('-created_at')[:min(limit, settings.max_products_per_section)]

    serializer = ProductSerializer(products, many=True)
    return Response({
        'results': serializer.data,
        'count': products.count(),
        'settings': {
            'max_items': settings.max_products_per_section,
            'refresh_interval': settings.content_refresh_interval
        }
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def advertisements(request):
    """Get active advertisements for slider with optional category filtering"""
    # Get settings to check if ads should be shown
    settings = ContentSettings.get_settings()
    if not settings.show_ads_slider:
        return Response({
            'results': [],
            'count': 0,
            'message': 'Ads slider is currently disabled'
        })

    # Get category parameter from query string
    category_id = request.query_params.get('category')

    # Base query for active ads
    ads_query = Advertisement.objects.filter(is_active=True)

    if category_id:
        try:
            # Filter ads for specific category
            category_id = int(category_id)
            ads_query = ads_query.filter(category_id=category_id)

            # Verify category exists
            try:
                category = Category.objects.get(id=category_id)
                category_name = category.name
            except Category.DoesNotExist:
                return Response({
                    'results': [],
                    'count': 0,
                    'message': 'Category not found'
                }, status=status.HTTP_404_NOT_FOUND)

        except (ValueError, TypeError):
            return Response({
                'error': 'Invalid category ID'
            }, status=status.HTTP_400_BAD_REQUEST)
    else:
        # Main page ads - show ads with show_on_main=True and category=None
        ads_query = ads_query.filter(show_on_main=True, category__isnull=True)
        category_name = 'Main Page'

    # Get ads with limit and count before slicing
    ads_count = ads_query.count()
    ads = ads_query.order_by('order', '-created_at')[:settings.max_ads_to_show]

    ads_data = []
    for ad in ads:
        ads_data.append({
            'id': str(ad.id),
            'title': ad.title,
            'description': ad.description,
            'imageUrl': ad.image_display_url,
            'linkUrl': ad.link_url,
            'isActive': ad.is_active,
            'order': ad.order,
            'category_id': ad.category_id,
            'category_name': ad.category.name if ad.category else None,
            'display_location': ad.display_location
        })

    return Response({
        'results': ads_data,
        'count': len(ads_data),
        'category': category_name if 'category_name' in locals() else 'Main Page',
        'category_id': category_id,
        'settings': {
            'max_ads': settings.max_ads_to_show,
            'rotation_interval': settings.ads_rotation_interval,
            'refresh_interval': settings.content_refresh_interval
        }
    })

@api_view(['GET', 'PUT', 'POST'])
@permission_classes([AllowAny])
def content_settings(request):
    """Get or update content display settings"""
    if request.method == 'GET':
        # Get current settings
        settings = ContentSettings.get_settings()

        return Response({
            'showLatestOffers': settings.show_latest_offers,
            'showFeaturedProducts': settings.show_featured_products,
            'showTopArtists': settings.show_top_artists,
            'showTopStores': settings.show_top_stores,
            'showAdsSlider': settings.show_ads_slider,
            'maxProductsPerSection': settings.max_products_per_section,
            'maxArtistsToShow': settings.max_artists_to_show,
            'maxStoresToShow': settings.max_stores_to_show,
            'maxAdsToShow': settings.max_ads_to_show,
            'adsRotationInterval': settings.ads_rotation_interval,
            'contentRefreshInterval': settings.content_refresh_interval,
            'enableContentCache': settings.enable_content_cache,
            'cacheDuration': settings.cache_duration
        })
    
    elif request.method in ['PUT', 'POST']:
        # Only staff can update settings
        if not request.user.is_authenticated or not request.user.is_staff:
            return Response({"error": "Admin permissions required"}, status=status.HTTP_403_FORBIDDEN)
        
        # Get current settings (singleton pattern)
        settings = ContentSettings.get_settings()
        
        # Update settings from request data
        data = request.data
        if 'showTopArtists' in data:
            settings.show_top_artists = data['showTopArtists']
        if 'showTopStores' in data:
            settings.show_top_stores = data['showTopStores']
        if 'showLatestOffers' in data:
            settings.show_latest_offers = data['showLatestOffers']
        if 'showFeaturedProducts' in data:
            settings.show_featured_products = data['showFeaturedProducts']
        if 'showAdsSlider' in data:
            settings.show_ads_slider = data['showAdsSlider']
        if 'maxProductsPerSection' in data:
            settings.max_products_per_section = data['maxProductsPerSection']
        if 'maxArtistsToShow' in data:
            settings.max_artists_to_show = data['maxArtistsToShow']
        if 'maxStoresToShow' in data:
            settings.max_stores_to_show = data['maxStoresToShow']
        if 'maxAdsToShow' in data:
            settings.max_ads_to_show = data['maxAdsToShow']
        if 'adsRotationInterval' in data:
            settings.ads_rotation_interval = data['adsRotationInterval']
        if 'contentRefreshInterval' in data:
            settings.content_refresh_interval = data['contentRefreshInterval']
        if 'enableContentCache' in data:
            settings.enable_content_cache = data['enableContentCache']
        if 'cacheDuration' in data:
            settings.cache_duration = data['cacheDuration']
        
        # Save the updated settings
        settings.save()
        
        # Log admin activity
        from admin_panel.models import AdminActivity
        AdminActivity.objects.create(
            admin=request.user,
            action='update_content_settings',
            description='Updated homepage content display settings',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response({
            'success': True,
            'message': 'Content settings updated successfully',
            'settings': {
                'showLatestOffers': settings.show_latest_offers,
                'showFeaturedProducts': settings.show_featured_products,
                'showTopArtists': settings.show_top_artists,
                'showTopStores': settings.show_top_stores,
                'showAdsSlider': settings.show_ads_slider,
                'maxProductsPerSection': settings.max_products_per_section,
                'maxArtistsToShow': settings.max_artists_to_show,
                'maxStoresToShow': settings.max_stores_to_show,
                'maxAdsToShow': settings.max_ads_to_show,
                'adsRotationInterval': settings.ads_rotation_interval,
                'contentRefreshInterval': settings.content_refresh_interval,
                'enableContentCache': settings.enable_content_cache,
                'cacheDuration': settings.cache_duration
            }
        })
    
    return Response({"error": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

# Admin management endpoints for offers and featured products

@csrf_exempt
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def manage_offers(request):
    """Manage product offers for admin dashboard"""
    if not request.user.is_staff:
        return Response({"error": "Staff permissions required"}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        # Get only valid/active offers with product details (hide expired offers)
        from django.utils import timezone
        now = timezone.now()
        offers = ProductOffer.objects.select_related('product', 'product__category').filter(
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        ).order_by('-created_at')

        results = []
        for offer in offers:
            product_data = ProductSerializer(offer.product).data
            product_data.update({
                'offer_id': offer.id,
                'original_price': float(offer.product.price),
                'offer_price': float(offer.offer_price),
                'discount_percentage': offer.discount_percentage,
                'savings_amount': float(offer.savings_amount),
                'offer_description': offer.description,
                'start_date': offer.start_date.isoformat(),
                'end_date': offer.end_date.isoformat(),
                'is_offer_active': offer.is_active,
                'is_offer_valid': offer.is_valid,
                'created_at': offer.created_at.isoformat()
            })
            results.append(product_data)

        return Response({
            'results': results,
            'count': len(results)
        })

    elif request.method == 'POST':
        # Create new offer
        try:
            product_id = request.data.get('product_id')
            product = Product.objects.get(id=product_id, is_active=True)

            # Check if product already has an active offer
            existing_offer = ProductOffer.objects.filter(
                product=product,
                is_active=True
            ).first()

            if existing_offer:
                return Response({
                    'error': 'This product already has an active offer'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Parse datetime strings to timezone-aware datetimes
            from django.utils.dateparse import parse_datetime
            from django.utils import timezone as tz
            
            start_date_str = request.data.get('start_date')
            end_date_str = request.data.get('end_date')
            
            # Parse and make timezone-aware
            start_date = parse_datetime(start_date_str)
            end_date = parse_datetime(end_date_str)
            
            if start_date and not start_date.tzinfo:
                start_date = tz.make_aware(start_date)
            if end_date and not end_date.tzinfo:
                end_date = tz.make_aware(end_date)

            offer = ProductOffer.objects.create(
                product=product,
                discount_percentage=request.data.get('discount_percentage'),
                start_date=start_date,
                end_date=end_date,
                description=request.data.get('description', ''),
                is_active=request.data.get('is_active', True)
            )

            # Also feature the product if requested
            if request.data.get('also_feature', False):
                featured, created = FeaturedProduct.objects.get_or_create(
                    product=product,
                    defaults={
                        'priority': request.data.get('featured_priority', 0),
                        'reason': f"Featured with offer - {offer.discount_percentage}% OFF",
                        'is_active': True
                    }
                )

            return Response({
                'message': 'Offer created successfully',
                'offer_id': offer.id
            }, status=status.HTTP_201_CREATED)

        except Product.DoesNotExist:
            return Response({
                'error': 'Product not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def manage_offer_detail(request, offer_id):
    """Manage individual offer"""
    try:
        offer = ProductOffer.objects.get(id=offer_id)
    except ProductOffer.DoesNotExist:
        return Response({
            'error': 'Offer not found'
        }, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        product_data = ProductSerializer(offer.product).data
        product_data.update({
            'offer_id': offer.id,
            'original_price': float(offer.product.price),
            'offer_price': float(offer.offer_price),
            'discount_percentage': offer.discount_percentage,
            'savings_amount': float(offer.savings_amount),
            'offer_description': offer.description,
            'start_date': offer.start_date.isoformat(),
            'end_date': offer.end_date.isoformat(),
            'is_offer_active': offer.is_active,
            'is_offer_valid': offer.is_valid
        })
        return Response(product_data)

    elif request.method == 'PUT':
        # Update offer
        offer.discount_percentage = request.data.get('discount_percentage', offer.discount_percentage)
        offer.start_date = request.data.get('start_date', offer.start_date)
        offer.end_date = request.data.get('end_date', offer.end_date)
        offer.description = request.data.get('description', offer.description)
        offer.is_active = request.data.get('is_active', offer.is_active)
        offer.save()

        return Response({
            'message': 'Offer updated successfully'
        })

    elif request.method == 'DELETE':
        offer.delete()
        return Response({
            'message': 'Offer deleted successfully'
        })

@csrf_exempt
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def manage_featured_products(request):
    """Manage featured products for admin dashboard"""
    if not request.user.is_staff:
        return Response({"error": "Staff permissions required"}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        # Get all featured products
        featured_products = FeaturedProduct.objects.select_related('product', 'product__category').order_by('priority', '-featured_since')

        results = []
        for featured in featured_products:
            product_data = ProductSerializer(featured.product).data
            product_data.update({
                'featured_id': featured.id,
                'featured_since': featured.featured_since.isoformat(),
                'featured_until': featured.featured_until.isoformat() if featured.featured_until else None,
                'featured_reason': featured.reason,
                'featured_priority': featured.priority,
                'is_featured_active': featured.is_active,
                'is_featured_valid': featured.is_valid
            })
            results.append(product_data)

        return Response({
            'results': results,
            'count': len(results)
        })

    elif request.method == 'POST':
        # Feature a product
        try:
            product_id = request.data.get('product_id')
            product = Product.objects.get(id=product_id, is_active=True)

            # Check if product is already featured
            existing_featured = FeaturedProduct.objects.filter(
                product=product,
                is_active=True
            ).first()

            if existing_featured:
                return Response({
                    'error': 'This product is already featured'
                }, status=status.HTTP_400_BAD_REQUEST)

            featured = FeaturedProduct.objects.create(
                product=product,
                priority=request.data.get('priority', 0),
                featured_until=request.data.get('featured_until'),
                reason=request.data.get('reason', ''),
                is_active=request.data.get('is_active', True)
            )

            return Response({
                'message': 'Product featured successfully',
                'featured_id': featured.id
            }, status=status.HTTP_201_CREATED)

        except Product.DoesNotExist:
            return Response({
                'error': 'Product not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def manage_featured_detail(request, featured_id):
    """Manage individual featured product"""
    try:
        featured = FeaturedProduct.objects.get(id=featured_id)
    except FeaturedProduct.DoesNotExist:
        return Response({
            'error': 'Featured product not found'
        }, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        product_data = ProductSerializer(featured.product).data
        product_data.update({
            'featured_id': featured.id,
            'featured_since': featured.featured_since.isoformat(),
            'featured_until': featured.featured_until.isoformat() if featured.featured_until else None,
            'featured_reason': featured.reason,
            'featured_priority': featured.priority,
            'is_featured_active': featured.is_active,
            'is_featured_valid': featured.is_valid
        })
        return Response(product_data)

    elif request.method == 'PUT':
        # Update featured product
        featured.priority = request.data.get('priority', featured.priority)
        featured.featured_until = request.data.get('featured_until', featured.featured_until)
        featured.reason = request.data.get('reason', featured.reason)
        featured.is_active = request.data.get('is_active', featured.is_active)
        featured.save()

        return Response({
            'message': 'Featured product updated successfully'
        })

    elif request.method == 'DELETE':
        featured.delete()
        return Response({
            'message': 'Featured product removed successfully'
        })

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_product_featured(request, product_id):
    """Toggle featured status of a product"""
    if not request.user.is_staff:
        return Response({"error": "Staff permissions required"}, status=status.HTTP_403_FORBIDDEN)

    try:
        product = Product.objects.get(id=product_id, is_active=True)

        featured = FeaturedProduct.objects.filter(product=product).first()

        if featured:
            # Remove from featured
            featured.delete()
            message = 'Product removed from featured'
            is_featured = False
        else:
            # Add to featured
            FeaturedProduct.objects.create(
                product=product,
                priority=request.data.get('priority', 0),
                reason=request.data.get('reason', 'Admin featured'),
                is_active=True
            )
            message = 'Product added to featured'
            is_featured = True

        return Response({
            'message': message,
            'is_featured': is_featured
        })

    except Product.DoesNotExist:
        return Response({
            'error': 'Product not found'
        }, status=status.HTTP_404_NOT_FOUND)

# Advertisement Management API Endpoints

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])  # Require authentication for creating/managing ads
def manage_advertisements(request):
    """Manage advertisements for admin panel"""
    if request.method == 'GET':
        # Get all advertisements for admin management
        ads = Advertisement.objects.select_related('category').all().order_by('category', 'order', '-created_at')

        ads_data = []
        for ad in ads:
            ads_data.append({
                'id': str(ad.id),
                'title': ad.title,
                'description': ad.description,
                'imageUrl': ad.image_display_url,
                'linkUrl': ad.link_url,
                'isActive': ad.is_active,
                'showOnMain': ad.show_on_main,
                'order': ad.order,
                'category_id': ad.category_id,
                'category_name': ad.category.name if ad.category else None,
                'display_location': ad.display_location,
                'created_at': ad.created_at.isoformat(),
                'updated_at': ad.updated_at.isoformat()
            })

        return Response({
            'results': ads_data,
            'count': len(ads_data)
        })

    elif request.method == 'POST':
        # Create new advertisement
        try:
            # Validate required fields
            title = request.data.get('title', '').strip()
            if not title:
                return Response({
                    'error': 'Title is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            image_url = request.data.get('imageUrl', '').strip()
            if not image_url:
                return Response({
                    'error': 'Image URL is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Handle category assignment
            category = None
            category_id = request.data.get('category_id')
            if category_id:
                try:
                    category = Category.objects.get(id=category_id)
                except Category.DoesNotExist:
                    return Response({
                        'error': 'Category not found'
                    }, status=status.HTTP_404_NOT_FOUND)

            # Create the advertisement
            ad = Advertisement.objects.create(
                title=title,
                description=request.data.get('description', '').strip(),
                image_url=image_url,
                link_url=request.data.get('linkUrl', '').strip(),
                category=category,
                is_active=request.data.get('isActive', True),
                show_on_main=request.data.get('showOnMain', True),
                order=request.data.get('order', 0)
            )

            return Response({
                'id': str(ad.id),
                'title': ad.title,
                'description': ad.description,
                'imageUrl': ad.image_display_url,
                'linkUrl': ad.link_url,
                'isActive': ad.is_active,
                'showOnMain': ad.show_on_main,
                'order': ad.order,
                'category_id': ad.category_id,
                'category_name': ad.category.name if ad.category else None,
                'display_location': ad.display_location,
                'created_at': ad.created_at.isoformat(),
                'message': 'Advertisement created successfully'
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'error': f'Failed to create advertisement: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def manage_advertisement_detail(request, ad_id):
    """Manage individual advertisement"""
    try:
        ad = Advertisement.objects.get(id=ad_id)
    except Advertisement.DoesNotExist:
        return Response({
            'error': 'Advertisement not found'
        }, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response({
            'id': str(ad.id),
            'title': ad.title,
            'description': ad.description,
            'imageUrl': ad.image_display_url,
            'linkUrl': ad.link_url,
            'isActive': ad.is_active,
            'showOnMain': ad.show_on_main,
            'order': ad.order,
            'category_id': ad.category_id,
            'category_name': ad.category.name if ad.category else None,
            'display_location': ad.display_location,
            'created_at': ad.created_at.isoformat(),
            'updated_at': ad.updated_at.isoformat()
        })

    elif request.method == 'PUT':
        # Update advertisement
        try:
            if 'title' in request.data:
                ad.title = request.data['title'].strip()
            if 'description' in request.data:
                ad.description = request.data['description'].strip()
            if 'imageUrl' in request.data:
                ad.image_url = request.data['imageUrl'].strip()
            if 'linkUrl' in request.data:
                ad.link_url = request.data['linkUrl'].strip()
            if 'isActive' in request.data:
                ad.is_active = request.data['isActive']
            if 'showOnMain' in request.data:
                ad.show_on_main = request.data['showOnMain']
            if 'order' in request.data:
                ad.order = request.data['order']
            if 'category_id' in request.data:
                category_id = request.data['category_id']
                if category_id:
                    try:
                        ad.category = Category.objects.get(id=category_id)
                    except Category.DoesNotExist:
                        return Response({
                            'error': 'Category not found'
                        }, status=status.HTTP_404_NOT_FOUND)
                else:
                    ad.category = None

            ad.save()

            return Response({
                'id': str(ad.id),
                'title': ad.title,
                'description': ad.description,
                'imageUrl': ad.image_display_url,
                'linkUrl': ad.link_url,
                'isActive': ad.is_active,
                'order': ad.order,
                'updated_at': ad.updated_at.isoformat(),
                'message': 'Advertisement updated successfully'
            })

        except Exception as e:
            return Response({
                'error': f'Failed to update advertisement: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        ad.delete()
        return Response({
            'message': 'Advertisement deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)

# Category Management API Endpoints

@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def manage_categories(request):
    """Get all categories for admin management with hierarchical structure"""
    if not request.user.is_staff:
        return Response({"error": "Staff permissions required"}, status=status.HTTP_403_FORBIDDEN)

    # Get all categories
    categories = Category.objects.all().order_by('name')

    # Build hierarchical structure
    parent_categories = []
    category_dict = {}

    # First pass: create dictionary of all categories
    for category in categories:
        category_data = {
            'id': category.id,
            'name': category.name,
            'description': category.description,
            'image': category.image.url if category.image else None,
            'is_active': category.is_active,
            'created_at': category.created_at.isoformat(),
            'updated_at': category.updated_at.isoformat(),
            'parent_id': category.parent.id if category.parent else None,
            'parent_name': category.parent.name if category.parent else None,
            'product_count': category.products.count(),
            'children': []
        }
        category_dict[category.id] = category_data

    # Second pass: build hierarchy
    for category in categories:
        category_data = category_dict[category.id]
        if category.parent:
            # This is a subcategory, add to parent's children
            if category.parent.id in category_dict:
                category_dict[category.parent.id]['children'].append(category_data)
        else:
            # This is a parent category
            parent_categories.append(category_data)

    return Response({
        'results': parent_categories,
        'total_count': categories.count(),
        'parent_count': len(parent_categories),
        'subcategory_count': categories.filter(parent__isnull=False).count()
    })

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_category(request):
    """Create a new category or subcategory"""
    if not request.user.is_staff:
        return Response({"error": "Staff permissions required"}, status=status.HTTP_403_FORBIDDEN)

    # Debug logging (can be removed in production)
    print(f"Create request data: {request.data}")
    print(f"Create request content type: {request.content_type}")
    print(f"Create is_active value: {request.data.get('is_active')} (type: {type(request.data.get('is_active'))})")

    try:
        name = request.data.get('name', '').strip()
        if not name:
            return Response({
                'error': 'Category name is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if category with this name already exists
        if Category.objects.filter(name__iexact=name).exists():
            return Response({
                'error': 'A category with this name already exists'
            }, status=status.HTTP_400_BAD_REQUEST)

        parent_id = request.data.get('parent_id')
        parent_category = None

        if parent_id:
            try:
                parent_category = Category.objects.get(id=parent_id)
                # Ensure parent is not a subcategory (prevent deep nesting)
                if parent_category.parent:
                    return Response({
                        'error': 'Cannot create subcategory under another subcategory. Only 2-level hierarchy is supported.'
                    }, status=status.HTTP_400_BAD_REQUEST)
            except Category.DoesNotExist:
                return Response({
                    'error': 'Parent category not found'
                }, status=status.HTTP_404_NOT_FOUND)

        # Handle is_active field properly
        is_active_value = request.data.get('is_active', True)
        if isinstance(is_active_value, str):
            is_active = is_active_value.lower() in ['true', '1', 'yes', 'on']
        else:
            is_active = bool(is_active_value)

        category = Category.objects.create(
            name=name,
            description=request.data.get('description', '').strip(),
            parent=parent_category,
            is_active=is_active
        )

        # Handle image upload if provided
        if 'image' in request.FILES:
            category.image = request.FILES['image']
            category.save()

        return Response({
            'id': category.id,
            'name': category.name,
            'description': category.description,
            'image': category.image.url if category.image else None,
            'is_active': category.is_active,
            'parent_id': category.parent.id if category.parent else None,
            'parent_name': category.parent.name if category.parent else None,
            'created_at': category.created_at.isoformat(),
            'message': f'Category "{category.name}" created successfully'
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            'error': f'Failed to create category: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def manage_category_detail(request, category_id):
    """Get category details with products and subcategories"""
    if not request.user.is_staff:
        return Response({"error": "Staff permissions required"}, status=status.HTTP_403_FORBIDDEN)

    try:
        category = Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        return Response({
            'error': 'Category not found'
        }, status=status.HTTP_404_NOT_FOUND)

    # Get subcategories
    subcategories = Category.objects.filter(parent=category).order_by('name')
    subcategory_data = [{
        'id': sub.id,
        'name': sub.name,
        'description': sub.description,
        'image': sub.image.url if sub.image else None,
        'is_active': sub.is_active,
        'product_count': sub.products.count()
    } for sub in subcategories]

    # Get products in this category
    products = Product.objects.filter(category=category).order_by('-created_at')[:10]  # Latest 10 products
    product_data = [{
        'id': product.id,
        'name': product.name,
        'price': float(product.price),
        'is_active': product.is_active,
        'seller_name': product.seller_name,
        'created_at': product.created_at.isoformat()
    } for product in products]

    return Response({
        'id': category.id,
        'name': category.name,
        'description': category.description,
        'image': category.image.url if category.image else None,
        'is_active': category.is_active,
        'parent_id': category.parent.id if category.parent else None,
        'parent_name': category.parent.name if category.parent else None,
        'created_at': category.created_at.isoformat(),
        'updated_at': category.updated_at.isoformat(),
        'subcategories': subcategory_data,
        'subcategory_count': len(subcategory_data),
        'products': product_data,
        'total_product_count': category.products.count()
    })

@csrf_exempt
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_category(request, category_id):
    """Update category details"""
    if not request.user.is_staff:
        return Response({"error": "Staff permissions required"}, status=status.HTTP_403_FORBIDDEN)

    # Debug logging (can be removed in production)
    print(f"Request data: {request.data}")
    print(f"Request content type: {request.content_type}")
    print(f"Is_active value: {request.data.get('is_active')} (type: {type(request.data.get('is_active'))})")

    try:
        category = Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        return Response({
            'error': 'Category not found'
        }, status=status.HTTP_404_NOT_FOUND)

    try:
        # Update name if provided
        if 'name' in request.data:
            new_name = request.data['name'].strip()
            if not new_name:
                return Response({
                    'error': 'Category name cannot be empty'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check if another category with this name exists
            if Category.objects.filter(name__iexact=new_name).exclude(id=category_id).exists():
                return Response({
                    'error': 'A category with this name already exists'
                }, status=status.HTTP_400_BAD_REQUEST)

            category.name = new_name

        # Update other fields
        if 'description' in request.data:
            category.description = request.data['description'].strip()

        if 'is_active' in request.data:
            # Handle both boolean and string values
            is_active_value = request.data['is_active']
            if isinstance(is_active_value, str):
                category.is_active = is_active_value.lower() in ['true', '1', 'yes', 'on']
            else:
                category.is_active = bool(is_active_value)

        # Handle parent change
        if 'parent_id' in request.data:
            parent_id = request.data['parent_id']
            if parent_id:
                try:
                    parent_category = Category.objects.get(id=parent_id)
                    # Prevent circular references
                    if parent_category.id == category.id:
                        return Response({
                            'error': 'Category cannot be its own parent'
                        }, status=status.HTTP_400_BAD_REQUEST)

                    # Prevent deep nesting
                    if parent_category.parent:
                        return Response({
                            'error': 'Cannot move category under a subcategory. Only 2-level hierarchy is supported.'
                        }, status=status.HTTP_400_BAD_REQUEST)

                    # Prevent moving parent under its child
                    if category.children.filter(id=parent_category.id).exists():
                        return Response({
                            'error': 'Cannot move category under its own subcategory'
                        }, status=status.HTTP_400_BAD_REQUEST)

                    category.parent = parent_category
                except Category.DoesNotExist:
                    return Response({
                        'error': 'Parent category not found'
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                category.parent = None

        # Handle image upload
        if 'image' in request.FILES:
            category.image = request.FILES['image']

        category.save()

        return Response({
            'id': category.id,
            'name': category.name,
            'description': category.description,
            'image': category.image.url if category.image else None,
            'is_active': category.is_active,
            'parent_id': category.parent.id if category.parent else None,
            'parent_name': category.parent.name if category.parent else None,
            'updated_at': category.updated_at.isoformat(),
            'message': f'Category "{category.name}" updated successfully'
        })

    except Exception as e:
        return Response({
            'error': f'Failed to update category: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_category(request, category_id):
    """Delete a category"""
    if not request.user.is_staff:
        return Response({"error": "Staff permissions required"}, status=status.HTTP_403_FORBIDDEN)

    try:
        category = Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        return Response({
            'error': 'Category not found'
        }, status=status.HTTP_404_NOT_FOUND)

    # Check if category has products
    product_count = category.products.count()
    if product_count > 0:
        return Response({
            'error': f'Cannot delete category. It contains {product_count} products. Please move or delete the products first.'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Check if category has subcategories
    subcategory_count = category.children.count()
    if subcategory_count > 0:
        return Response({
            'error': f'Cannot delete category. It has {subcategory_count} subcategories. Please delete or move the subcategories first.'
        }, status=status.HTTP_400_BAD_REQUEST)

    category_name = category.name
    category.delete()

    return Response({
        'message': f'Category "{category_name}" deleted successfully'
    }, status=status.HTTP_204_NO_CONTENT)


# Attribute Management API Endpoints

@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_attribute_options(request, attribute_type):
    """Get all options for a specific attribute type"""
    if not request.user.is_staff:
        return Response({"error": "Staff permissions required"}, status=status.HTTP_403_FORBIDDEN)

    try:
        attribute = ProductAttribute.objects.get(attribute_type=attribute_type)
        options = attribute.options.all().order_by('sort_order')
        serializer = ProductAttributeOptionSerializer(options, many=True)
        return Response(serializer.data)
    except ProductAttribute.DoesNotExist:
        return Response({'error': 'Attribute not found'}, status=status.HTTP_404_NOT_FOUND)


@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_category_attributes(request, category_id):
    """Get all attributes for a specific category"""
    if not request.user.is_staff:
        return Response({"error": "Staff permissions required"}, status=status.HTTP_403_FORBIDDEN)

    try:
        category = Category.objects.get(id=category_id)
        category_attributes = category.category_attributes.all().order_by('sort_order')
        serializer = CategoryAttributeSerializer(category_attributes, many=True)
        return Response(serializer.data)
    except Category.DoesNotExist:
        return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_category_attributes(request, category_id):
    """Update which attributes and options are available for a category"""
    if not request.user.is_staff:
        return Response({"error": "Staff permissions required"}, status=status.HTTP_403_FORBIDDEN)

    try:
        import json
        data = json.loads(request.body)

        category = Category.objects.get(id=category_id)

        # Clear existing category attributes
        CategoryAttribute.objects.filter(category=category).delete()

        # Add frame colors if enabled
        if data.get('frame_colors', {}).get('enabled', False):
            frame_color_attr = ProductAttribute.objects.get(attribute_type='frame_color')

            # First, disable all frame color options for this attribute
            ProductAttributeOption.objects.filter(attribute=frame_color_attr).update(is_active=False)

            # Enable selected options
            selected_colors = data['frame_colors'].get('options', [])
            if selected_colors:
                ProductAttributeOption.objects.filter(
                    attribute=frame_color_attr,
                    id__in=selected_colors
                ).update(is_active=True)

            # Create category attribute relationship
            CategoryAttribute.objects.create(
                category=category,
                attribute=frame_color_attr,
                is_required=False,
                sort_order=0
            )

        # Add sizes if enabled
        if data.get('sizes', {}).get('enabled', False):
            size_attr = ProductAttribute.objects.get(attribute_type='size')

            # First, disable all size options for this attribute
            ProductAttributeOption.objects.filter(attribute=size_attr).update(is_active=False)

            # Enable selected options
            selected_sizes = data['sizes'].get('options', [])
            if selected_sizes:
                ProductAttributeOption.objects.filter(
                    attribute=size_attr,
                    id__in=selected_sizes
                ).update(is_active=True)

            # Create category attribute relationship
            CategoryAttribute.objects.create(
                category=category,
                attribute=size_attr,
                is_required=data['sizes'].get('required', False),
                sort_order=1
            )

        return Response({
            'message': f'Attributes updated successfully for category "{category.name}"'
        })

    except Category.DoesNotExist:
        return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)
    except ProductAttribute.DoesNotExist:
        return Response({'error': 'Attribute not found'}, status=status.HTTP_404_NOT_FOUND)
    except json.JSONDecodeError:
        return Response({'error': 'Invalid JSON data'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def debug_arabic_encoding(request):
    """Debug endpoint to test Arabic encoding"""
    try:
        # Test Arabic strings
        test_data = {
            'categories': [],
            'products': [],
            'test_strings': {
                'arabic_greeting': 'مرحبا بك في تحفة',
                'arabic_numbers': '١٢٣٤٥٦٧٨٩٠',
                'mixed_text': 'Welcome مرحبا',
                'product_name': 'لوحة فنية جميلة',
                'description': 'هذا منتج رائع بوصف عربي طويل يحتوي على كلمات متنوعة'
            }
        }

        # Get some real categories
        categories = Category.objects.all()[:3]
        for cat in categories:
            test_data['categories'].append({
                'id': cat.id,
                'name': cat.name,
                'description': cat.description,
                'name_length': len(cat.name),
                'contains_arabic': bool(cat.name and any('\u0600' <= c <= '\u06FF' for c in cat.name))
            })

        # Get some real products
        products = Product.objects.all()[:3]
        for prod in products:
            test_data['products'].append({
                'id': prod.id,
                'name': prod.name,
                'description': prod.description[:100] if prod.description else '',
                'name_length': len(prod.name),
                'contains_arabic': bool(prod.name and any('\u0600' <= c <= '\u06FF' for c in prod.name))
            })

        return Response(test_data)
    except Exception as e:
        return Response({
            'error': f'Debug endpoint failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# New Product Wizard API Endpoints

@api_view(['GET'])
@permission_classes([AllowAny])
def categories_for_product_wizard(request):
    """Get all active categories with descriptions for product creation wizard"""
    try:
        categories = Category.objects.filter(is_active=True, parent__isnull=True).order_by('name')

        category_data = []
        for category in categories:
            category_data.append({
                'id': category.id,
                'name': category.name,
                'description': category.description or f'منتجات {category.name} عالية الجودة',
                'image': category.image.url if category.image else None
            })

        return Response({
            'categories': category_data
        })
    except Exception as e:
        return Response({
            'categories': [],
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def category_variants(request, category_id):
    """Get all variant types and options for a specific category"""
    try:
        category = Category.objects.get(id=category_id, is_active=True)
        variant_types = CategoryVariantType.objects.filter(category=category).order_by('name')

        variants_data = []
        for variant_type in variant_types:
            options_data = []
            for option in variant_type.options.filter(is_active=True):
                options_data.append({
                    'id': option.id,
                    'value': option.value,
                    'extra_price': float(option.extra_price) if option.extra_price else 0
                })

            variants_data.append({
                'id': variant_type.id,
                'name': variant_type.name,
                'is_required': variant_type.is_required,
                'options': options_data
            })

        return Response({
            'variants': variants_data
        })
    except Category.DoesNotExist:
        return Response({
            'variants': [],
            'error': 'Category not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([AllowAny])
def category_tags(request, category_id):
    """Get all predefined tags for a specific category"""
    try:
        category = Category.objects.get(id=category_id, is_active=True)
        tags = Tag.objects.filter(
            Q(category=category) | Q(category__isnull=True),
            is_predefined=True
        ).order_by('name')

        tags_data = []
        for tag in tags:
            tags_data.append({
                'id': tag.id,
                'name': tag.name,
                'category_specific': tag.category is not None
            })

        return Response({
            'tags': tags_data
        })
    except Category.DoesNotExist:
        return Response({
            'tags': [],
            'error': 'Category not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'tags': [],
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def subcategory_sections(request, category_id):
    """Get enabled subcategory sections for a specific parent category"""
    try:
        # Get the parent category
        parent_category = Category.objects.get(id=category_id, is_active=True)

        # Get enabled subcategory sections for this parent category
        sections = SubcategorySectionControl.objects.filter(
            subcategory__parent=parent_category,
            subcategory__is_active=True,
            is_section_enabled=True
        ).select_related(
            'subcategory', 'subcategory__parent'
        ).prefetch_related(
            'featured_products'
        ).order_by('section_priority', 'subcategory__name')

        serializer = SubcategorySectionControlSerializer(sections, many=True, context={'request': request})

        return Response({
            'parent_category': {
                'id': parent_category.id,
                'name': parent_category.name
            },
            'sections': serializer.data
        })

    except Category.DoesNotExist:
        return Response({
            'parent_category': None,
            'sections': [],
            'error': 'Parent category not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'parent_category': None,
            'sections': [],
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def all_subcategory_sections(request):
    """Get all enabled subcategory sections grouped by parent category"""
    try:
        # Get all enabled sections
        sections = SubcategorySectionControl.objects.filter(
            subcategory__is_active=True,
            is_section_enabled=True
        ).select_related(
            'subcategory', 'subcategory__parent'
        ).prefetch_related(
            'featured_products'
        ).order_by(
            'subcategory__parent__name', 'section_priority', 'subcategory__name'
        )

        # Group by parent category
        sections_by_category = {}
        for section in sections:
            parent_id = section.subcategory.parent.id
            parent_name = section.subcategory.parent.name

            if parent_id not in sections_by_category:
                sections_by_category[parent_id] = {
                    'parent_category': {
                        'id': parent_id,
                        'name': parent_name
                    },
                    'sections': []
                }

            section_serializer = SubcategorySectionControlSerializer(section, context={'request': request})
            sections_by_category[parent_id]['sections'].append(section_serializer.data)

        return Response({
            'sections_by_category': list(sections_by_category.values())
        })

    except Exception as e:
        return Response({
            'sections_by_category': [],
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============== SELLER REQUEST VIEWS ===============

@csrf_exempt
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def seller_offer_requests(request):
    """Manage seller offer requests"""
    from .models import SellerOfferRequest
    
    if not request.user.user_type in ['artist', 'store']:
        return Response({"error": "Only sellers can create offer requests"}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        # Get seller's offer requests
        requests = SellerOfferRequest.objects.filter(seller=request.user).order_by('-created_at')
        
        results = []
        for req in requests:
            results.append({
                'id': req.id,
                'product_id': req.product.id,
                'product_name': req.product.name,
                'product_price': float(req.product.price),
                'discount_percentage': req.discount_percentage,
                'offer_price': float(req.offer_price),
                'savings_amount': float(req.savings_amount),
                'start_date': req.start_date.isoformat(),
                'end_date': req.end_date.isoformat(),
                'description': req.description,
                'status': req.status,
                'status_display': req.get_status_display(),
                'request_fee': float(req.request_fee),
                'payment_reference': req.payment_reference,
                'admin_notes': req.admin_notes,
                'created_at': req.created_at.isoformat(),
                'updated_at': req.updated_at.isoformat(),
            })
        
        return Response({
            'results': results,
            'count': len(results)
        })

    elif request.method == 'POST':
        # Create new offer request
        try:
            product_id = request.data.get('product_id')
            product = Product.objects.get(id=product_id, seller=request.user, is_active=True)

            # Check if there's already an active request for this product
            existing_request = SellerOfferRequest.objects.filter(
                product=product,
                seller=request.user,
                status__in=['pending_payment', 'payment_completed', 'under_review']
            ).first()

            if existing_request:
                return Response({
                    'error': f'You already have an active offer request for this product (Status: {existing_request.get_status_display()})'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Parse dates
            from django.utils.dateparse import parse_datetime
            start_date = parse_datetime(request.data.get('start_date'))
            end_date = parse_datetime(request.data.get('end_date'))

            if not start_date or not end_date:
                return Response({
                    'error': 'Invalid start_date or end_date format. Use ISO format.'
                }, status=status.HTTP_400_BAD_REQUEST)

            if start_date >= end_date:
                return Response({
                    'error': 'End date must be after start date'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Create the offer request
            offer_request = SellerOfferRequest.objects.create(
                product=product,
                seller=request.user,
                discount_percentage=request.data.get('discount_percentage'),
                start_date=start_date,
                end_date=end_date,
                description=request.data.get('description', ''),
                request_fee=50.00  # Default fee
            )

            return Response({
                'id': offer_request.id,
                'message': f'Offer request created successfully! Please pay {offer_request.request_fee} SAR to proceed.',
                'request_fee': float(offer_request.request_fee),
                'status': offer_request.status,
                'payment_instructions': 'Please contact admin to complete payment and activate your offer request.'
            }, status=status.HTTP_201_CREATED)

        except Product.DoesNotExist:
            return Response({
                'error': 'Product not found or you do not own this product'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'Failed to create offer request: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def seller_featured_requests(request):
    """Manage seller featured product requests"""
    from .models import SellerFeaturedRequest
    
    if not request.user.user_type in ['artist', 'store']:
        return Response({"error": "Only sellers can create featured requests"}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        # Get seller's featured requests
        requests = SellerFeaturedRequest.objects.filter(seller=request.user).order_by('-created_at')
        
        results = []
        for req in requests:
            results.append({
                'id': req.id,
                'product_id': req.product.id,
                'product_name': req.product.name,
                'product_price': float(req.product.price),
                'priority': req.priority,
                'featured_duration_days': req.featured_duration_days,
                'reason': req.reason,
                'status': req.status,
                'status_display': req.get_status_display(),
                'request_fee': float(req.request_fee),
                'payment_reference': req.payment_reference,
                'admin_notes': req.admin_notes,
                'created_at': req.created_at.isoformat(),
                'updated_at': req.updated_at.isoformat(),
            })
        
        return Response({
            'results': results,
            'count': len(results)
        })

    elif request.method == 'POST':
        # Create new featured request
        try:
            product_id = request.data.get('product_id')
            product = Product.objects.get(id=product_id, seller=request.user, is_active=True)

            # Check if there's already an active request for this product
            existing_request = SellerFeaturedRequest.objects.filter(
                product=product,
                seller=request.user,
                status__in=['pending_payment', 'payment_completed', 'under_review']
            ).first()

            if existing_request:
                return Response({
                    'error': f'You already have an active featured request for this product (Status: {existing_request.get_status_display()})'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Create the featured request
            featured_request = SellerFeaturedRequest.objects.create(
                product=product,
                seller=request.user,
                priority=request.data.get('priority', 0),
                featured_duration_days=request.data.get('featured_duration_days', 30),
                reason=request.data.get('reason', ''),
                request_fee=100.00  # Default fee for featured products
            )

            return Response({
                'id': featured_request.id,
                'message': f'Featured request created successfully! Please pay {featured_request.request_fee} SAR to proceed.',
                'request_fee': float(featured_request.request_fee),
                'status': featured_request.status,
                'payment_instructions': 'Please contact admin to complete payment and activate your featured request.'
            }, status=status.HTTP_201_CREATED)

        except Product.DoesNotExist:
            return Response({
                'error': 'Product not found or you do not own this product'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'Failed to create featured request: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


# =============== ADMIN REQUEST MANAGEMENT VIEWS ===============

@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def manage_seller_requests(request):
    """Get all seller requests for admin management"""
    from .models import SellerOfferRequest, SellerFeaturedRequest
    
    if not request.user.is_staff:
        return Response({"error": "Admin permissions required"}, status=status.HTTP_403_FORBIDDEN)

    # Get offer requests
    offer_requests = SellerOfferRequest.objects.all().order_by('-created_at')
    offer_results = []
    for req in offer_requests:
        offer_results.append({
            'id': req.id,
            'type': 'offer',
            'product_id': req.product.id,
            'product_name': req.product.name,
            'seller_name': req.seller.email,
            'seller_type': req.seller.user_type,
            'discount_percentage': req.discount_percentage,
            'offer_price': float(req.offer_price),
            'original_price': float(req.product.price),
            'start_date': req.start_date.isoformat(),
            'end_date': req.end_date.isoformat(),
            'status': req.status,
            'status_display': req.get_status_display(),
            'request_fee': float(req.request_fee),
            'payment_reference': req.payment_reference,
            'created_at': req.created_at.isoformat(),
        })

    # Get featured requests
    featured_requests = SellerFeaturedRequest.objects.all().order_by('-created_at')
    featured_results = []
    for req in featured_requests:
        featured_results.append({
            'id': req.id,
            'type': 'featured',
            'product_id': req.product.id,
            'product_name': req.product.name,
            'seller_name': req.seller.email,
            'seller_type': req.seller.user_type,
            'featured_duration_days': req.featured_duration_days,
            'priority': req.priority,
            'status': req.status,
            'status_display': req.get_status_display(),
            'request_fee': float(req.request_fee),
            'payment_reference': req.payment_reference,
            'created_at': req.created_at.isoformat(),
        })

    return Response({
        'offer_requests': offer_results,
        'featured_requests': featured_results,
        'total_offer_requests': len(offer_results),
        'total_featured_requests': len(featured_results),
    })


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_offer_request(request, request_id):
    """Approve seller offer request and create actual offer"""
    from .models import SellerOfferRequest
    
    if not request.user.is_staff:
        return Response({"error": "Admin permissions required"}, status=status.HTTP_403_FORBIDDEN)

    try:
        offer_request = SellerOfferRequest.objects.get(id=request_id)
        
        if offer_request.status != 'payment_completed':
            return Response({
                'error': 'Request must have completed payment before approval'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Approve and create the actual offer
        product_offer = offer_request.approve_and_create_offer(request.user)
        
        if product_offer:
            return Response({
                'message': f'Offer request approved successfully! Product "{offer_request.product.name}" is now featured in latest offers.',
                'offer_id': product_offer.id
            })
        else:
            return Response({
                'error': 'Failed to create offer. Request status may not be valid.'
            }, status=status.HTTP_400_BAD_REQUEST)

    except SellerOfferRequest.DoesNotExist:
        return Response({
            'error': 'Offer request not found'
        }, status=status.HTTP_404_NOT_FOUND)


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_featured_request(request, request_id):
    """Approve seller featured request and create actual featured product"""
    from .models import SellerFeaturedRequest
    
    if not request.user.is_staff:
        return Response({"error": "Admin permissions required"}, status=status.HTTP_403_FORBIDDEN)

    try:
        featured_request = SellerFeaturedRequest.objects.get(id=request_id)
        
        if featured_request.status != 'payment_completed':
            return Response({
                'error': 'Request must have completed payment before approval'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Approve and create the actual featured product
        featured_product = featured_request.approve_and_create_featured(request.user)
        
        if featured_product:
            return Response({
                'message': f'Featured request approved successfully! Product "{featured_request.product.name}" is now featured.',
                'featured_id': featured_product.id
            })
        else:
            return Response({
                'error': 'Failed to create featured product. Request status may not be valid.'
            }, status=status.HTTP_400_BAD_REQUEST)

    except SellerFeaturedRequest.DoesNotExist:
        return Response({
            'error': 'Featured request not found'
        }, status=status.HTTP_404_NOT_FOUND)


# =============== ADDITIONAL VIEWS FOR COMPLETENESS ===============

@csrf_exempt
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def seller_offer_request_detail(request, request_id):
    """Get, update or delete specific seller offer request"""
    from .models import SellerOfferRequest
    
    try:
        offer_request = SellerOfferRequest.objects.get(id=request_id, seller=request.user)
    except SellerOfferRequest.DoesNotExist:
        return Response({
            'error': 'Offer request not found'
        }, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response({
            'id': offer_request.id,
            'product_id': offer_request.product.id,
            'product_name': offer_request.product.name,
            'discount_percentage': offer_request.discount_percentage,
            'offer_price': float(offer_request.offer_price),
            'start_date': offer_request.start_date.isoformat(),
            'end_date': offer_request.end_date.isoformat(),
            'description': offer_request.description,
            'status': offer_request.status,
            'status_display': offer_request.get_status_display(),
            'request_fee': float(offer_request.request_fee),
            'payment_reference': offer_request.payment_reference,
            'admin_notes': offer_request.admin_notes,
            'created_at': offer_request.created_at.isoformat(),
        })

    elif request.method == 'DELETE':
        if offer_request.status in ['approved', 'rejected']:
            return Response({
                'error': 'Cannot delete approved or rejected requests'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        offer_request.delete()
        return Response({
            'message': 'Offer request deleted successfully'
        })


@csrf_exempt
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def seller_featured_request_detail(request, request_id):
    """Get, update or delete specific seller featured request"""
    from .models import SellerFeaturedRequest
    
    try:
        featured_request = SellerFeaturedRequest.objects.get(id=request_id, seller=request.user)
    except SellerFeaturedRequest.DoesNotExist:
        return Response({
            'error': 'Featured request not found'
        }, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response({
            'id': featured_request.id,
            'product_id': featured_request.product.id,
            'product_name': featured_request.product.name,
            'priority': featured_request.priority,
            'featured_duration_days': featured_request.featured_duration_days,
            'reason': featured_request.reason,
            'status': featured_request.status,
            'status_display': featured_request.get_status_display(),
            'request_fee': float(featured_request.request_fee),
            'payment_reference': featured_request.payment_reference,
            'admin_notes': featured_request.admin_notes,
            'created_at': featured_request.created_at.isoformat(),
        })

    elif request.method == 'DELETE':
        if featured_request.status in ['approved', 'rejected']:
            return Response({
                'error': 'Cannot delete approved or rejected requests'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        featured_request.delete()
        return Response({
            'message': 'Featured request deleted successfully'
        })


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_offer_request(request, request_id):
    """Reject seller offer request"""
    from .models import SellerOfferRequest
    
    if not request.user.is_staff:
        return Response({"error": "Admin permissions required"}, status=status.HTTP_403_FORBIDDEN)

    try:
        offer_request = SellerOfferRequest.objects.get(id=request_id)
        
        offer_request.status = 'rejected'
        offer_request.admin_notes = request.data.get('admin_notes', '')
        offer_request.reviewed_by = request.user
        offer_request.reviewed_at = timezone.now()
        offer_request.save()

        return Response({
            'message': f'Offer request for "{offer_request.product.name}" has been rejected.'
        })

    except SellerOfferRequest.DoesNotExist:
        return Response({
            'error': 'Offer request not found'
        }, status=status.HTTP_404_NOT_FOUND)


@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_featured_request(request, request_id):
    """Reject seller featured request"""
    from .models import SellerFeaturedRequest
    
    if not request.user.is_staff:
        return Response({"error": "Admin permissions required"}, status=status.HTTP_403_FORBIDDEN)

    try:
        featured_request = SellerFeaturedRequest.objects.get(id=request_id)
        
        featured_request.status = 'rejected'
        featured_request.admin_notes = request.data.get('admin_notes', '')
        featured_request.reviewed_by = request.user
        featured_request.reviewed_at = timezone.now()
        featured_request.save()

        return Response({
            'message': f'Featured request for "{featured_request.product.name}" has been rejected.'
        })

    except SellerFeaturedRequest.DoesNotExist:
        return Response({
            'error': 'Featured request not found'
        }, status=status.HTTP_404_NOT_FOUND)
