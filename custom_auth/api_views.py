from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
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