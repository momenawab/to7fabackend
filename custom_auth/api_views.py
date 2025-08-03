from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from .models import User, Artist, Store
from .serializers import UserSerializer
from admin_panel.models import AdminActivity, SellerApplication, AdminNotification
import logging

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def get_user_details(request, user_id):
    """
    API endpoint to get user details, including blocking information
    """
    user = get_object_or_404(User, id=user_id)
    serializer = UserSerializer(user)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def block_unblock_user(request, user_id):
    """
    API endpoint to block or unblock a user
    """
    target_user = get_object_or_404(User, id=user_id)
    
    # Check if request data is JSON
    if request.content_type == 'application/json':
        data = request.data
    else:
        data = request.POST
    
    action = data.get('action', 'block')
    reason = data.get('reason', '')
    
    # Don't allow blocking yourself
    if target_user == request.user:
        return Response(
            {'error': 'You cannot block yourself'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Don't allow blocking other admins
    if target_user.is_staff or target_user.is_superuser:
        return Response(
            {'error': 'You cannot block admin users'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if action == 'block':
        target_user.is_active = False
        target_user.blocked_at = timezone.now()
        target_user.blocked_by = request.user
        target_user.block_reason = reason
        admin_action = 'block_user'
        message = f"User {target_user.email} has been blocked"
        action_description = f"Blocked user: {target_user.email}"
    else:  # unblock
        target_user.is_active = True
        target_user.unblocked_at = timezone.now()
        target_user.unblocked_by = request.user
        admin_action = 'unblock_user'
        message = f"User {target_user.email} has been unblocked"
        action_description = f"Unblocked user: {target_user.email}"
    
    target_user.save()
    
    # Log admin activity
    AdminActivity.objects.create(
        admin=request.user,
        action=admin_action,
        description=action_description,
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    return Response({
        'status': 'success',
        'message': message
    }) 

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_seller_application(request):
    """
    API endpoint for users to submit seller applications (artist or store)
    """
    user = request.user
    
    # Check if user already has a pending application
    has_pending = SellerApplication.objects.filter(
        user=user, 
        status='pending'
    ).exists()
    
    if has_pending:
        return Response({
            'status': 'error',
            'message': 'You already have a pending seller application'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if user is already a seller
    if user.user_type in ['artist', 'store']:
        return Response({
            'status': 'error',
            'message': f'You are already registered as a {user.user_type}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get application data
    user_type = request.data.get('user_type')
    
    if user_type not in ['artist', 'store']:
        return Response({
            'status': 'error',
            'message': 'Invalid seller type. Must be "artist" or "store"'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Create application object
        application = SellerApplication(
            user=user,
            user_type=user_type,
            name=request.data.get('name') or f"{user.first_name} {user.last_name}",
            email=request.data.get('email') or user.email,
            phone_number=request.data.get('phone_number') or user.phone_number,
            address=request.data.get('address') or user.address,
            shipping_company=request.data.get('shipping_company', ''),
            shipping_costs=request.data.get('shipping_costs', {}),
            details=request.data.get('details', '')
        )
        
        # Handle photo if provided in base64 format
        if 'photo' in request.data and request.data['photo']:
            application.photo = request.data['photo']
        
        # Process categories
        categories = request.data.get('categories', [])
        application.categories = categories
        
        # Handle artist specific fields
        if user_type == 'artist':
            application.specialty = request.data.get('specialty', '')
            application.bio = request.data.get('bio', '')
            
            # Store social media links
            social_media = request.data.get('social_media', {})
            if social_media and isinstance(social_media, dict):
                application.social_media = social_media
        
        # Handle store specific fields
        elif user_type == 'store':
            application.store_name = request.data.get('store_name', '') or request.data.get('name', '')
            application.tax_id = request.data.get('tax_id', '')
            application.has_physical_store = request.data.get('has_physical_store', False)
            
            if application.has_physical_store:
                application.physical_address = request.data.get('physical_address', '')
            
            # Store social media links
            social_media = request.data.get('social_media', {})
            if social_media and isinstance(social_media, dict):
                application.social_media = social_media
        
        application.save()
        
        # Create admin notification
        AdminNotification.objects.create(
            title="New Seller Application",
            message=f"New {user_type} application submitted by {user.email}",
            notification_type="new_application",
            link=f"/dashboard/applications/{application.id}/"
        )
        
        return Response({
            'status': 'success',
            'message': 'Your seller application has been submitted successfully',
            'application_id': application.id
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error processing seller application: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'Error processing your application: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Artist and Store endpoints for admin content management

@api_view(['GET'])
@permission_classes([AllowAny])
def top_artists(request):
    """Get top/featured artists"""
    from products.models import ContentSettings
    from django.db.models import Count
    
    limit = request.query_params.get('limit', 8)
    try:
        limit = int(limit)
    except (ValueError, TypeError):
        limit = 8
    
    # Get settings to check if this section should be shown
    settings = ContentSettings.get_settings()
    if not settings.show_top_artists:
        return Response({
            'results': [],
            'count': 0,
            'message': 'Top artists section is currently disabled'
        })
    
    # Get verified artists with products, ordered by product count
    artists = Artist.objects.filter(
        is_verified=True,
        user__products__isnull=False
    ).annotate(
        product_count=Count('user__products', distinct=True)
    ).filter(
        product_count__gt=0
    ).order_by('-product_count', '-created_at')[:min(limit, settings.max_artists_to_show)]
    
    artist_data = []
    for artist in artists:
        artist_data.append({
            'id': str(artist.user.id),
            'name': f"{artist.user.first_name} {artist.user.last_name}".strip() or artist.user.email.split('@')[0],
            'email': artist.user.email,
            'specialty': artist.specialty,
            'bio': artist.bio,
            'profilePicture': artist.profile_picture.url if artist.profile_picture else None,
            'isVerified': artist.is_verified,
            'productCount': artist.product_count,
            'socialMedia': artist.social_media,
            'joinedAt': artist.created_at.isoformat()
        })
    
    return Response({
        'results': artist_data,
        'count': len(artist_data),
        'settings': {
            'max_artists': settings.max_artists_to_show,
            'refresh_interval': settings.content_refresh_interval
        }
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def featured_artists(request):
    """Get featured artists - same as top for now"""
    return top_artists(request)

@api_view(['GET'])
@permission_classes([AllowAny])
def top_stores(request):
    """Get top/featured stores"""
    from products.models import ContentSettings
    from django.db.models import Count
    
    limit = request.query_params.get('limit', 6)
    try:
        limit = int(limit)
    except (ValueError, TypeError):
        limit = 6
    
    # Get settings to check if this section should be shown
    settings = ContentSettings.get_settings()
    if not settings.show_top_stores:
        return Response({
            'results': [],
            'count': 0,
            'message': 'Top stores section is currently disabled'
        })
    
    # Get verified stores with products, ordered by product count
    stores = Store.objects.filter(
        is_verified=True,
        user__products__isnull=False
    ).annotate(
        product_count=Count('user__products', distinct=True)
    ).filter(
        product_count__gt=0
    ).order_by('-product_count', '-created_at')[:min(limit, settings.max_stores_to_show)]
    
    store_data = []
    for store in stores:
        store_data.append({
            'id': str(store.user.id),
            'name': store.store_name,
            'email': store.user.email,
            'logo': store.logo.url if store.logo else None,
            'taxId': store.tax_id,
            'hasPhysicalStore': store.has_physical_store,
            'physicalAddress': store.physical_address,
            'isVerified': store.is_verified,
            'productCount': store.product_count,
            'socialMedia': store.social_media,
            'joinedAt': store.created_at.isoformat()
        })
    
    return Response({
        'results': store_data,
        'count': len(store_data),
        'settings': {
            'max_stores': settings.max_stores_to_show,
            'refresh_interval': settings.content_refresh_interval
        }
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def featured_stores(request):
    """Get featured stores - same as top for now"""
    return top_stores(request)

@api_view(['GET'])
@permission_classes([AllowAny])
def search_artists(request):
    """Search artists by name or specialty"""
    query = request.query_params.get('q', '')
    if not query:
        return Response({
            "error": "Search query parameter 'q' is required"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Search in user name and artist specialty
    artists = Artist.objects.filter(
        Q(user__first_name__icontains=query) | 
        Q(user__last_name__icontains=query) | 
        Q(specialty__icontains=query),
        is_verified=True
    ).order_by('-created_at')
    
    artist_data = []
    for artist in artists:
        artist_data.append({
            'id': str(artist.user.id),
            'name': f"{artist.user.first_name} {artist.user.last_name}".strip() or artist.user.email.split('@')[0],
            'email': artist.user.email,
            'specialty': artist.specialty,
            'bio': artist.bio,
            'profilePicture': artist.profile_picture.url if artist.profile_picture else None,
            'isVerified': artist.is_verified,
            'socialMedia': artist.social_media,
            'joinedAt': artist.created_at.isoformat()
        })
    
    return Response({
        "query": query,
        "results_count": len(artist_data),
        "results": artist_data
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def search_stores(request):
    """Search stores by name"""
    query = request.query_params.get('q', '')
    if not query:
        return Response({
            "error": "Search query parameter 'q' is required"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Search in store name
    stores = Store.objects.filter(
        store_name__icontains=query,
        is_verified=True
    ).order_by('-created_at')
    
    store_data = []
    for store in stores:
        store_data.append({
            'id': str(store.user.id),
            'name': store.store_name,
            'email': store.user.email,
            'logo': store.logo.url if store.logo else None,
            'hasPhysicalStore': store.has_physical_store,
            'physicalAddress': store.physical_address,
            'isVerified': store.is_verified,
            'socialMedia': store.social_media,
            'joinedAt': store.created_at.isoformat()
        })
    
    return Response({
        "query": query,
        "results_count": len(store_data),
        "results": store_data
    }) 