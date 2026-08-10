from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from .models import User, Artist, Store
from .serializers import UserSerializer
from admin_panel.models import AdminActivity, AdminNotification
from .models import SellerApplication
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
        # Validate profile picture
        profile_picture = request.FILES.get('profile_picture')
        if not profile_picture:
            return Response({
                'status': 'error',
                'message': 'Profile picture is required for seller application'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create application object
        application = SellerApplication(
            user=user,
            seller_type=user_type,
            business_name=request.data.get('business_name') or f"{user.first_name} {user.last_name}",
            phone_number=request.data.get('phone_number') or user.phone_number,
            description=request.data.get('description', ''),
            profile_picture=profile_picture
        )
        
        # Store social media links
        social_media = request.data.get('social_media', {})
        if social_media and isinstance(social_media, dict):
            application.social_media = social_media
        
        # Handle artist specific fields
        if user_type == 'artist':
            application.specialty = request.data.get('specialty', '')
            application.portfolio_link = request.data.get('portfolio_link', '')
        
        # Handle store specific fields
        elif user_type == 'store':
            application.tax_id = request.data.get('tax_id', '')
            application.has_physical_store = request.data.get('has_physical_store', False)
            
            if application.has_physical_store:
                application.physical_address = request.data.get('physical_address', '')
        
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

# Phase 3 (Part A workstream 4, artist/store contract gaps): public-facing dict
# builders shared by every artist/store endpoint below. include_email defaults to
# False - top_artists/search_artists/top_stores/search_stores (all pre-existing,
# served AllowAny/no-auth) used to always include the account's email address (and,
# for stores, tax_id) in the response. "Do not expose private or administrative data"
# is a Phase 3 Part A acceptance criterion, so the two brand-new endpoints this
# workstream adds (artist_list/artist_detail/store_list/store_detail - nothing
# depends on these yet) never include it.
#
# The four pre-existing functions still pass include_email=True, though - verified
# (grep -rn "artists/top\|artists/search\|stores/top\|stores/search" admin_panel/)
# that admin_panel/templates/admin_panel/artists_stores.html's own JS
# (`artist.email`/`store.email`) genuinely renders it for the admin dashboard's use in
# identifying/contacting artists and stores. Stripping it there would have broken a
# real, currently-working admin-panel feature - not a hypothetical one, confirmed by
# reading the template, the same way the Flutter-side check was confirmed rather than
# assumed. This is a real, currently-unresolved tension (an AllowAny/no-auth public
# endpoint carrying an admin-only field) worth flagging for Phase 4: the correct fix is
# a separate authenticated admin endpoint, not preserved here because building one is
# beyond this workstream's "add list/detail" scope - see
# PHASE3_API_PAYMENT_REPORT.md for the full writeup.
def _public_artist_dict(artist, product_count, include_email=False):
    data = {
        'id': str(artist.user.id),
        'name': f"{artist.user.first_name} {artist.user.last_name}".strip() or artist.user.email.split('@')[0],
        'specialty': artist.specialty,
        'bio': artist.bio,
        'profilePicture': artist.profile_picture.url if artist.profile_picture else None,
        'isVerified': artist.is_verified,
        'isFeatured': artist.is_featured_on_homepage,
        'priority': artist.homepage_priority,
        'productCount': product_count,
        'socialMedia': artist.social_media,
        'joinedAt': artist.created_at.isoformat(),
    }
    if include_email:
        data['email'] = artist.user.email
    return data


def _public_store_dict(store, product_count, include_email=False):
    data = {
        'id': str(store.user.id),
        'name': store.store_name,
        'logo': store.logo.url if store.logo else None,
        'hasPhysicalStore': store.has_physical_store,
        'physicalAddress': store.physical_address,
        'isVerified': store.is_verified,
        'isFeatured': store.is_featured_on_homepage,
        'priority': store.homepage_priority,
        'productCount': product_count,
        'socialMedia': store.social_media,
        'joinedAt': store.created_at.isoformat(),
    }
    if include_email:
        data['email'] = store.user.email
    return data


@api_view(['GET'])
@authentication_classes([])
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

    # Get artists - prioritize featured ones, then by verification and product count
    artists = Artist.objects.annotate(
        product_count=Count('user__products', distinct=True)
    ).filter(
        Q(is_featured_on_homepage=True) |
        (Q(is_verified=True) & Q(product_count__gt=0))
    ).order_by(
        '-is_featured_on_homepage',  # Featured first
        'homepage_priority',         # Then by priority (0 = highest)
        '-product_count',           # Then by product count
        '-created_at'              # Finally by creation date
    )[:min(limit, settings.max_artists_to_show)]

    artist_data = [_public_artist_dict(artist, artist.product_count, include_email=True) for artist in artists]

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
@authentication_classes([])
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
    
    # Get stores - prioritize featured ones, then by verification and product count
    stores = Store.objects.annotate(
        product_count=Count('user__products', distinct=True)
    ).filter(
        Q(is_featured_on_homepage=True) | 
        (Q(is_verified=True) & Q(product_count__gt=0))
    ).order_by(
        '-is_featured_on_homepage',  # Featured first
        'homepage_priority',         # Then by priority (0 = highest)
        '-product_count',           # Then by product count
        '-created_at'              # Finally by creation date
    )[:min(limit, settings.max_stores_to_show)]
    
    store_data = [_public_store_dict(store, store.product_count, include_email=True) for store in stores]

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
    
    artist_data = [_public_artist_dict(artist, None, include_email=True) for artist in artists]

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
    
    store_data = [_public_store_dict(store, None, include_email=True) for store in stores]

    return Response({
        "query": query,
        "results_count": len(store_data),
        "results": store_data
    })

@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def artist_list(request):
    """Public, paginated artist list. Phase 3 addition (Part A workstream 4) - Flutter's
    ArtistService.getArtists()/searchArtists() (lib/core/services/artist_service.dart)
    call this exact bare endpoint with page/page_size/featured/search query params;
    only top/featured/search-with-required-q existed before, this was a confirmed 404.

    Only verified artists are listed (matches search_artists' existing is_verified=True
    filter) - an unverified/pending seller profile is not something the public browse
    surface should show.
    """
    from django.db.models import Count
    from rest_framework.pagination import PageNumberPagination

    artists = Artist.objects.annotate(
        product_count=Count('user__products', distinct=True)
    ).filter(is_verified=True)

    featured = request.query_params.get('featured')
    if featured is not None:
        artists = artists.filter(is_featured_on_homepage=(featured.lower() == 'true'))

    search = request.query_params.get('search') or request.query_params.get('q')
    if search:
        artists = artists.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(specialty__icontains=search)
        )

    artists = artists.order_by('-is_featured_on_homepage', 'homepage_priority', '-created_at')

    paginator = PageNumberPagination()
    paginator.page_size_query_param = 'page_size'
    paginator.max_page_size = 100
    page = paginator.paginate_queryset(artists, request)
    data = [_public_artist_dict(artist, artist.product_count) for artist in page]
    return paginator.get_paginated_response(data)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def artist_detail(request, artist_id):
    """Public artist detail by user id. Phase 3 addition (Part A workstream 4) -
    Flutter's ArtistService.getArtistById() calls this exact route; it was a confirmed
    404 before (only top/featured/search existed)."""
    from django.db.models import Count

    try:
        artist = Artist.objects.annotate(
            product_count=Count('user__products', distinct=True)
        ).get(user_id=artist_id, is_verified=True)
    except Artist.DoesNotExist:
        return Response({'message': 'Artist not found'}, status=status.HTTP_404_NOT_FOUND)

    return Response(_public_artist_dict(artist, artist.product_count))


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def store_list(request):
    """Public, paginated store list. Phase 3 addition (Part A workstream 4) - mirrors
    artist_list(); Flutter's StoreService calls the equivalent bare store endpoint the
    same way."""
    from django.db.models import Count
    from rest_framework.pagination import PageNumberPagination

    stores = Store.objects.annotate(
        product_count=Count('user__products', distinct=True)
    ).filter(is_verified=True)

    featured = request.query_params.get('featured')
    if featured is not None:
        stores = stores.filter(is_featured_on_homepage=(featured.lower() == 'true'))

    search = request.query_params.get('search') or request.query_params.get('q')
    if search:
        stores = stores.filter(store_name__icontains=search)

    stores = stores.order_by('-is_featured_on_homepage', 'homepage_priority', '-created_at')

    paginator = PageNumberPagination()
    paginator.page_size_query_param = 'page_size'
    paginator.max_page_size = 100
    page = paginator.paginate_queryset(stores, request)
    data = [_public_store_dict(store, store.product_count) for store in page]
    return paginator.get_paginated_response(data)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def store_detail(request, store_id):
    """Public store detail by user id. Phase 3 addition (Part A workstream 4) - mirrors
    artist_detail()."""
    from django.db.models import Count

    try:
        store = Store.objects.annotate(
            product_count=Count('user__products', distinct=True)
        ).get(user_id=store_id, is_verified=True)
    except Store.DoesNotExist:
        return Response({'message': 'Store not found'}, status=status.HTTP_404_NOT_FOUND)

    return Response(_public_store_dict(store, store.product_count))


# Admin API endpoints for featured status management

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def toggle_artist_featured(request, artist_id):
    """Toggle featured status for an artist"""
    try:
        artist = Artist.objects.get(user_id=artist_id)
        artist.is_featured_on_homepage = not artist.is_featured_on_homepage
        artist.save()
        
        # Log admin activity
        AdminActivity.objects.create(
            admin=request.user,
            action='update',
            description=f"{'Featured' if artist.is_featured_on_homepage else 'Unfeatured'} artist: {artist.user.email}",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response({
            'success': True,
            'featured': artist.is_featured_on_homepage,
            'message': f"Artist {'featured' if artist.is_featured_on_homepage else 'unfeatured'} successfully"
        })
    except Artist.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Artist not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def toggle_store_featured(request, store_id):
    """Toggle featured status for a store"""
    try:
        store = Store.objects.get(user_id=store_id)
        store.is_featured_on_homepage = not store.is_featured_on_homepage
        store.save()
        
        # Log admin activity
        AdminActivity.objects.create(
            admin=request.user,
            action='update',
            description=f"{'Featured' if store.is_featured_on_homepage else 'Unfeatured'} store: {store.store_name}",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response({
            'success': True,
            'featured': store.is_featured_on_homepage,
            'message': f"Store {'featured' if store.is_featured_on_homepage else 'unfeatured'} successfully"
        })
    except Store.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Store not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def update_artist_priority(request, artist_id):
    """Update homepage priority for an artist"""
    try:
        artist = Artist.objects.get(user_id=artist_id)
        priority = request.data.get('priority', 0)
        
        # Ensure priority is a valid number
        try:
            priority = int(priority)
            if priority < 0:
                priority = 0
        except (ValueError, TypeError):
            priority = 0
        
        artist.homepage_priority = priority
        artist.save()
        
        # Log admin activity
        AdminActivity.objects.create(
            admin=request.user,
            action='update',
            description=f"Updated artist priority: {artist.user.email} -> {priority}",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response({
            'success': True,
            'priority': artist.homepage_priority,
            'message': 'Artist priority updated successfully'
        })
    except Artist.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Artist not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def update_store_priority(request, store_id):
    """Update homepage priority for a store"""
    try:
        store = Store.objects.get(user_id=store_id)
        priority = request.data.get('priority', 0)
        
        # Ensure priority is a valid number
        try:
            priority = int(priority)
            if priority < 0:
                priority = 0
        except (ValueError, TypeError):
            priority = 0
        
        store.homepage_priority = priority
        store.save()

        # Log admin activity
        AdminActivity.objects.create(
            admin=request.user,
            action='update',
            description=f"Updated store priority: {store.store_name} -> {priority}",
            ip_address=request.META.get('REMOTE_ADDR')
        )

        return Response({
            'success': True,
            'priority': store.homepage_priority,
            'message': 'Store priority updated successfully'
        })
    except Store.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Store not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_otp(request):
    """
    Send OTP to user's mobile number for verification.
    Subject to 60-second cooldown between requests.
    """
    from .serializers import SendOTPSerializer
    from .services.verification import send_otp as send_otp_service

    serializer = SendOTPSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': 'VALIDATION_ERROR',
            'message': 'Invalid request data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    mobile_number = serializer.validated_data['mobile_number']
    result = send_otp_service(request.user, mobile_number)

    if result.get('success'):
        return Response(result, status=status.HTTP_200_OK)
    else:
        error_code = result.get('error')
        if error_code == 'OTP_COOLDOWN':
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        elif error_code == 'OTP_BLOCKED':
            return Response(result, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_otp(request):
    """
    Verify OTP code and mark mobile as verified.
    After 3 failed attempts, user is permanently blocked from OTP.

    Optional checkout_data parameter can be provided to automatically
    create an order after successful verification.
    """
    from .serializers import VerifyOTPSerializer
    from .services.verification import verify_otp as verify_otp_service
    from .services.verification import (
        get_pending_checkout,
        clear_pending_checkout
    )

    serializer = VerifyOTPSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': 'VALIDATION_ERROR',
            'message': 'Invalid request data',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    otp_code = serializer.validated_data['otp_code']
    result = verify_otp_service(request.user, otp_code)

    if result.get('success'):
        # Check if there's pending checkout data to resume
        pending_checkout = get_pending_checkout(request.user)

        if pending_checkout:
            # Clear pending checkout data
            clear_pending_checkout(request.user)

            # Attempt to create order with pending checkout data
            try:
                from orders.views import create_order
                from django.test import RequestFactory

                # Create a mock request with the pending checkout data
                factory = RequestFactory()
                mock_request = factory.post(
                    '/api/v1/orders/create/',
                    data=pending_checkout,
                    content_type='application/json'
                )
                mock_request.user = request.user

                # Call create_order directly
                order_response = create_order(mock_request)

                # If order creation was successful, include order data in response
                if hasattr(order_response, 'status_code') and order_response.status_code in [200, 201]:
                    import json
                    order_data = json.loads(order_response.content)
                    result['data']['order_created'] = True
                    result['data']['order'] = order_data.get('data')
                else:
                    # Order creation failed, but verification succeeded
                    result['data']['order_created'] = False
                    result['data']['order_error'] = 'Failed to create order. Please try checkout again.'

            except Exception as e:
                logger.error(f"Error creating order after verification: {str(e)}", exc_info=True)
                result['data']['order_created'] = False
                result['data']['order_error'] = 'Failed to create order. Please try checkout again.'

        return Response(result, status=status.HTTP_200_OK)
    else:
        error_code = result.get('error')
        if error_code == 'OTP_BLOCKED':
            return Response(result, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST) 