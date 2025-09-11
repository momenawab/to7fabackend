from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from django.db.models import Count, Sum, Q, F
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import csv

from custom_auth.models import User, Artist, Store
from products.models import Product, Category, Advertisement, ContentSettings, Tag, CategoryVariantOption, ProductVariant, ProductVariantOption, DiscountRequest, ProductImage
from orders.models import Order, OrderItem
from notifications.models import Notification as UserNotification, Device, PushNotificationLog
from notifications.serializers import NotificationSerializer
from notifications.push_utils import send_notification_with_push
from .models import AdminActivity, AdminNotification
from custom_auth.models import SellerApplication
from .serializers import (
    SellerApplicationSerializer, UserSerializer, ProductSerializer,
    OrderSerializer, AdminNotificationSerializer, SellerApplicationCreateSerializer
)

def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

class AdminPagination(PageNumberPagination):
    """Custom pagination for admin API endpoints"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

# Test endpoint for debugging authentication (secured)
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def test_authentication(request):
    """Test endpoint to debug authentication issues - only for admins"""
    # Only return basic info for security
    data = {
        'user_authenticated': request.user.is_authenticated,
        'user_email': request.user.email,
        'is_staff': request.user.is_staff,
        'message': 'Authentication test successful'
    }
    return Response(data)

# Seller Application Views
class SellerApplicationListView(generics.ListAPIView):
    serializer_class = SellerApplicationSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    pagination_class = AdminPagination
    
    def get_queryset(self):
        status_filter = self.request.query_params.get('status', None)
        queryset = SellerApplication.objects.select_related('user', 'reviewed_by').all().order_by('-created_at')
        
        if status_filter and status_filter != 'all':
            queryset = queryset.filter(status=status_filter)
            
        return queryset

class SellerApplicationDetailView(generics.RetrieveAPIView):
    queryset = SellerApplication.objects.all()
    serializer_class = SellerApplicationSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def approve_application(request, pk):
    application = get_object_or_404(SellerApplication, pk=pk)
    action = request.data.get('approved', False)
    notes = request.data.get('notes', '')
    
    # Process the application
    application.status = 'approved' if action else 'rejected'
    application.admin_notes = notes
    application.reviewed_at = timezone.now()
    application.reviewed_by = request.user
    application.save()
    
    # Log admin activity
    activity_action = 'approve_application' if action else 'reject_application'
    AdminActivity.objects.create(
        admin=request.user,
        action=activity_action,
        description=f"{'Approved' if action else 'Rejected'} seller application #{application.id} for {application.business_name}",
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    # If approved, update user type and create profile
    if action:
        with transaction.atomic():
            user = application.user
            user.user_type = application.seller_type
            user.save()
            
            if application.seller_type == 'artist':
                # Use select_for_update to prevent race conditions
                try:
                    artist_profile = Artist.objects.select_for_update().get(user=user)
                    # Update existing profile
                    artist_profile.specialty = application.specialty or ''
                    artist_profile.bio = application.description
                    artist_profile.social_media = application.social_media
                    artist_profile.is_verified = True
                    if application.profile_picture:
                        artist_profile.profile_picture = application.profile_picture
                    artist_profile.save()
                except Artist.DoesNotExist:
                    # Create new profile if it doesn't exist
                    Artist.objects.create(
                        user=user,
                        specialty=application.specialty or '',
                        bio=application.description,
                        social_media=application.social_media,
                        profile_picture=application.profile_picture,
                        is_verified=True
                    )
            elif application.seller_type == 'store':
                # Use select_for_update to prevent race conditions
                try:
                    store_profile = Store.objects.select_for_update().get(user=user)
                    # Update existing profile
                    store_profile.store_name = application.business_name
                    store_profile.tax_id = application.tax_id or ''
                    store_profile.has_physical_store = application.has_physical_store
                    store_profile.physical_address = application.physical_address or ''
                    store_profile.social_media = application.social_media
                    store_profile.is_verified = True
                    if application.profile_picture:
                        store_profile.logo = application.profile_picture
                    store_profile.save()
                except Store.DoesNotExist:
                    # Create new profile if it doesn't exist
                    Store.objects.create(
                        user=user,
                        store_name=application.business_name,
                        tax_id=application.tax_id or '',
                        has_physical_store=application.has_physical_store,
                        physical_address=application.physical_address or '',
                        social_media=application.social_media,
                        logo=application.profile_picture,
                        is_verified=True
                    )
    
    return Response({
        'status': 'success',
        'message': f"Application has been {'approved' if action else 'rejected'}."
    })

# User Views
class UserListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    pagination_class = AdminPagination
    
    def get_queryset(self):
        user_type = self.request.query_params.get('type', None)
        search_query = self.request.query_params.get('q', None)
        
        queryset = User.objects.all().order_by('-date_joined')
        
        if user_type and user_type != 'all':
            queryset = queryset.filter(user_type=user_type)
            
        if search_query:
            queryset = queryset.filter(
                Q(email__icontains=search_query) | 
                Q(first_name__icontains=search_query) | 
                Q(last_name__icontains=search_query)
            )
            
        return queryset

class UserDetailView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def block_user(request, pk):
    """
    API endpoint to block or unblock a user
    This is a wrapper around the custom_auth block_unblock_user API
    """
    from custom_auth.api_views import block_unblock_user
    # Pass the request directly without modifying it
    return block_unblock_user(request, pk)

# Product Views
class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    pagination_class = AdminPagination
    
    def get_queryset(self):
        category_id = self.request.query_params.get('category', None)
        status = self.request.query_params.get('status', None)
        search_query = self.request.query_params.get('q', None)
        
        queryset = Product.objects.select_related('category', 'seller').all().order_by('-created_at')
        
        if category_id and category_id != 'all':
            queryset = queryset.filter(category_id=category_id)
            
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
            
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | 
                Q(description__icontains=search_query)
            )
            
        return queryset

class ProductDetailView(generics.RetrieveUpdateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def toggle_product_status(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    # Toggle is_active status
    product.is_active = not product.is_active
    product.save()
    
    # Log admin activity
    action = 'activate' if product.is_active else 'deactivate'
    AdminActivity.objects.create(
        admin=request.user,
        action='other',
        description=f"{action.capitalize()}d product #{product.id} - {product.name}",
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    return Response({
        'status': 'success',
        'is_active': product.is_active,
        'message': f"Product has been {'activated' if product.is_active else 'deactivated'}."
    })

# Order Views
class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    pagination_class = AdminPagination
    
    def get_queryset(self):
        status = self.request.query_params.get('status', None)
        search_query = self.request.query_params.get('q', None)
        
        queryset = Order.objects.select_related('user').prefetch_related('items__product').all().order_by('-created_at')
        
        if status and status != 'all':
            queryset = queryset.filter(status=status)
            
        if search_query:
            queryset = queryset.filter(
                Q(id__icontains=search_query) | 
                Q(user__email__icontains=search_query)
            )
            
        return queryset

class OrderDetailView(generics.RetrieveAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

# Dashboard Stats
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_stats(request):
    # User stats
    total_users = User.objects.count()
    customer_count = User.objects.filter(user_type='customer').count()
    artist_count = User.objects.filter(user_type='artist').count()
    store_count = User.objects.filter(user_type='store').count()
    
    # Order stats
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    completed_orders = Order.objects.filter(status='completed').count()
    
    # Product stats
    total_products = Product.objects.count()
    active_products = Product.objects.filter(is_active=True).count()
    
    # Application stats
    pending_applications = SellerApplication.objects.filter(status='pending').count()
    
    # Revenue stats (assuming there's a total_amount field in Order)
    total_revenue = Order.objects.filter(status='completed').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    data = {
        'users': {
            'total': total_users,
            'customers': customer_count,
            'artists': artist_count,
            'stores': store_count
        },
        'orders': {
            'total': total_orders,
            'pending': pending_orders,
            'completed': completed_orders
        },
        'products': {
            'total': total_products,
            'active': active_products
        },
        'applications': {
            'pending': pending_applications
        },
        'revenue': {
            'total': total_revenue
        }
    }
    
    return Response(data)

# Notification Views
class AdminNotificationListView(generics.ListAPIView):
    serializer_class = AdminNotificationSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    pagination_class = AdminPagination
    
    def get_queryset(self):
        is_read = self.request.query_params.get('is_read', None)
        queryset = AdminNotification.objects.all().order_by('-created_at')
        
        if is_read is not None:
            is_read_bool = is_read.lower() == 'true'
            queryset = queryset.filter(is_read=is_read_bool)
            
        return queryset

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def mark_notification_read(request, pk):
    notification = get_object_or_404(AdminNotification, pk=pk)
    notification.is_read = True
    notification.save()
    
    return Response({'status': 'success'})

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def mark_all_notifications_read(request):
    AdminNotification.objects.filter(is_read=False).update(is_read=True)
    
    return Response({'status': 'success'})

# Report API Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def report_summary(request):
    """API endpoint to get summary report data"""
    # Check if user is admin
    from .decorators import is_admin
    if not is_admin(request.user):
        return Response({'error': 'Admin access required'}, status=403)
    
    # Get date range parameters
    days = request.query_params.get('days', '30')
    start_date = request.query_params.get('start_date', None)
    end_date = request.query_params.get('end_date', None)
    
    try:
        # Calculate date range
        if start_date and end_date:
            # Custom date range
            start = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
            end = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            # Days based range
            days = int(days)
            end = timezone.now().date()
            start = end - timezone.timedelta(days=days)
    except (ValueError, TypeError):
        return Response(
            {'error': 'Invalid date parameters'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Sales data
    total_orders = Order.objects.filter(created_at__date__range=(start, end)).count()
    completed_orders = Order.objects.filter(
        created_at__date__range=(start, end),
        status='completed'
    ).count()
    
    # Calculate total revenue
    revenue_data = Order.objects.filter(
        created_at__date__range=(start, end),
        status='completed'
    ).aggregate(
        total_revenue=Sum('total_amount')
    )
    
    total_revenue = revenue_data['total_revenue'] or 0
    
    # Calculate average order value
    avg_order_value = total_revenue / completed_orders if completed_orders > 0 else 0
    
    # Calculate conversion rate (simplified)
    conversion_rate = (completed_orders / total_orders * 100) if total_orders > 0 else 0
    
    # Generate daily sales data
    daily_data = []
    current_date = start
    while current_date <= end:
        day_orders = Order.objects.filter(created_at__date=current_date).count()
        day_revenue = Order.objects.filter(
            created_at__date=current_date,
            status='completed'
        ).aggregate(
            revenue=Sum('total_amount')
        )['revenue'] or 0
        
        daily_data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'orders': day_orders,
            'revenue': day_revenue
        })
        
        current_date += timezone.timedelta(days=1)
    
    # Order status distribution
    status_counts = Order.objects.filter(
        created_at__date__range=(start, end)
    ).values('status').annotate(
        count=Count('id')
    )
    
    status_distribution = {item['status']: item['count'] for item in status_counts}
    
    # Monthly revenue data
    monthly_revenue = []
    for i in range(6):
        month_end = end.replace(day=1) - timezone.timedelta(days=1)
        month_start = month_end.replace(day=1)
        
        month_revenue = Order.objects.filter(
            created_at__date__range=(month_start, month_end),
            status='completed'
        ).aggregate(
            revenue=Sum('total_amount')
        )['revenue'] or 0
        
        monthly_revenue.append({
            'month': month_start.strftime('%b %Y'),
            'revenue': month_revenue
        })
        
        end = month_start - timezone.timedelta(days=1)
    
    monthly_revenue.reverse()
    
    # User data
    total_users = User.objects.count()
    new_users = User.objects.filter(date_joined__date__range=(start, end)).count()
    customer_count = User.objects.filter(user_type='customer').count()
    artist_count = User.objects.filter(user_type='artist').count()
    store_count = User.objects.filter(user_type='store').count()
    
    # User growth data
    user_growth_data = []
    current_date = start
    while current_date <= end:
        day_users = User.objects.filter(date_joined__date=current_date).count()
        
        user_growth_data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'count': day_users
        })
        
        current_date += timezone.timedelta(days=1)
    
    # Product data
    # Top selling products with optimized queries
    top_products = Product.objects.select_related('category', 'seller').annotate(
        units_sold=Count('orderitem')
    ).order_by('-units_sold')[:10]
    
    top_products_data = []
    for product in top_products:
        revenue = OrderItem.objects.filter(
            product=product,
            order__created_at__date__range=(start, end),
            order__status='completed'
        ).aggregate(
            revenue=Sum(F('price') * F('quantity'))
        )['revenue'] or 0
        
        top_products_data.append({
            'id': product.id,
            'name': product.name,
            'category': product.category.name if product.category else 'Uncategorized',
            'units_sold': product.units_sold,
            'revenue': revenue
        })
    
    # Top categories with optimized queries
    top_categories = Category.objects.prefetch_related('products').annotate(
        product_count=Count('products')
    ).order_by('-product_count')[:5]
    
    top_categories_data = []
    for category in top_categories:
        category_revenue = OrderItem.objects.filter(
            product__category=category,
            order__created_at__date__range=(start, end),
            order__status='completed'
        ).aggregate(
            revenue=Sum(F('price') * F('quantity'))
        )['revenue'] or 0
        
        top_categories_data.append({
            'id': category.id,
            'name': category.name,
            'product_count': category.product_count,
            'revenue': category_revenue
        })
    
    # Combine all data
    report_data = {
        'sales': {
            'total_orders': total_orders,
            'completed_orders': completed_orders,
            'total_revenue': total_revenue,
            'average_order_value': avg_order_value,
            'conversion_rate': conversion_rate,
            'daily_data': daily_data,
            'status_distribution': status_distribution,
            'monthly_revenue': monthly_revenue
        },
        'users': {
            'total': total_users,
            'new_users': new_users,
            'customers': customer_count,
            'artists': artist_count,
            'stores': store_count,
            'growth_data': user_growth_data
        },
        'products': {
            'top_products': top_products_data,
            'top_categories': top_categories_data
        }
    }
    
    return Response(report_data)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def sales_report(request):
    """API endpoint to get detailed sales report data"""
    # Similar to report_summary but with more detailed sales data
    # This is a simplified implementation
    return Response({'message': 'Detailed sales report data'})

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def user_report(request):
    """API endpoint to get detailed user report data"""
    # This is a simplified implementation
    return Response({'message': 'Detailed user report data'})

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def product_report(request):
    """API endpoint to get detailed product report data"""
    # This is a simplified implementation
    return Response({'message': 'Detailed product report data'})

# Settings API Views
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def update_settings(request, setting_type):
    """API endpoint to update settings"""
    # This is a simplified implementation
    # In a real application, you would save these settings to the database
    
    # Log admin activity
    AdminActivity.objects.create(
        admin=request.user,
        action='other',
        description=f"Updated {setting_type} settings",
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    return Response({
        'status': 'success',
        'message': f'{setting_type.capitalize()} settings updated successfully'
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def get_settings(request, setting_type):
    """API endpoint to get settings"""
    # This is a simplified implementation
    # In a real application, you would retrieve these settings from the database
    
    # Default settings for demonstration
    settings_data = {
        'general': {
            'site_name': 'To7fa',
            'site_description': 'Your one-stop shop for handmade gifts and crafts',
            'contact_email': 'contact@to7fa.com',
            'contact_phone': '+1 (555) 123-4567',
            'address': '123 Main Street, Cairo, Egypt',
            'currency': 'USD',
            'timezone': 'UTC',
            'maintenance_mode': False
        },
        'notifications': {
            'new_order_notification': True,
            'new_user_notification': True,
            'new_seller_application_notification': True,
            'low_stock_notification': True,
            'low_stock_threshold': 5,
            'order_status_notification': True,
            'promotional_notification': True
        },
        'api': {
            'enable_api': True,
            'api_rate_limit': 60,
            'api_token_expiry': 30,
            'enable_cors': True,
            'allowed_origins': 'https://to7fa.com\nhttps://www.to7fa.com\nhttp://localhost:3000'
        },
        'email': {
            'email_provider': 'smtp',
            'smtp_host': 'smtp.gmail.com',
            'smtp_port': 587,
            'smtp_encryption': 'tls',
            'smtp_username': 'noreply@to7fa.com',
            'from_name': 'To7fa',
            'from_email': 'noreply@to7fa.com'
        },
        'payment': {
            'enable_stripe': True,
            'stripe_test_mode': True,
            'enable_paypal': True,
            'paypal_sandbox': True,
            'enable_cod': True,
            'cod_fee': 5
        },
        'security': {
            'session_timeout': 30,
            'max_login_attempts': 5,
            'lockout_duration': 15,
            'enforce_strong_passwords': True,
            'enable_two_factor': False,
            'enable_captcha': True
        }
    }
    
    if setting_type in settings_data:
        return Response(settings_data[setting_type])
    else:
        return Response(
            {'error': f'Settings type "{setting_type}" not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def export_activity_log(request):
    """API endpoint to export activity log as CSV"""
    # Get filter parameters
    admin_id = request.query_params.get('admin')
    action_type = request.query_params.get('action')
    date_from = request.query_params.get('date_from')
    date_to = request.query_params.get('date_to')
    
    # Filter activities
    activities = AdminActivity.objects.all()
    
    if admin_id:
        activities = activities.filter(admin_id=admin_id)
    
    if action_type:
        activities = activities.filter(action=action_type)
    
    if date_from:
        date_from = timezone.datetime.strptime(date_from, '%Y-%m-%d').date()
        activities = activities.filter(timestamp__date__gte=date_from)
    
    if date_to:
        date_to = timezone.datetime.strptime(date_to, '%Y-%m-%d').date()
        activities = activities.filter(timestamp__date__lte=date_to)
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="activity_log.csv"'
    
    # Create CSV writer
    writer = csv.writer(response)
    writer.writerow(['Admin', 'Action', 'Description', 'IP Address', 'Timestamp'])
    
    # Add data rows
    for activity in activities:
        writer.writerow([
            activity.admin.email,
            activity.get_action_display(),
            activity.description,
            activity.ip_address,
            activity.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    return response

@api_view(['GET'])
@permission_classes([])  # Allow any user to access ads
def get_active_ads(request):
    """API endpoint to get active advertisements"""
    from products.models import Advertisement, ContentSettings
    
    # Get settings to check if ads should be shown
    settings = ContentSettings.get_settings()
    if not settings.show_ads_slider:
        return Response({
            'results': [],
            'count': 0,
            'message': 'Ads slider is currently disabled'
        })
    
    # Get active ads ordered by display order
    ads = Advertisement.objects.filter(
        is_active=True
    ).order_by('order', '-created_at')[:settings.max_ads_to_show]
    
    ads_data = []
    for ad in ads:
        ads_data.append({
            'id': ad.id,
            'title': ad.title,
            'description': ad.description,
            'image': ad.image_display_url,
            'linkUrl': ad.link_url,
            'order': ad.order,
            'createdAt': ad.created_at.isoformat()
        })
    
    return Response({
        'results': ads_data,
        'count': len(ads_data),
        'settings': {
            'max_ads': settings.max_ads_to_show,
            'rotation_interval': settings.ads_rotation_interval,
            'refresh_interval': settings.content_refresh_interval
        }
    })


# Product with Variants API
def validate_uploaded_files(files):
    """Validate uploaded image files"""
    allowed_types = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
    max_file_size = 5 * 1024 * 1024  # 5MB
    
    errors = []
    
    for file in files:
        # Check file type
        if file.content_type not in allowed_types:
            errors.append(f"File '{file.name}' has invalid type. Allowed types: JPEG, PNG, WebP, GIF")
        
        # Check file size
        if file.size > max_file_size:
            errors.append(f"File '{file.name}' is too large. Maximum size: 5MB")
        
        # Check file extension
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        if not any(file.name.lower().endswith(ext) for ext in allowed_extensions):
            errors.append(f"File '{file.name}' has invalid extension")
    
    return errors

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def create_product_with_variants(request):
    """API endpoint to create a product with variants"""
    from products.models import (
        Product, ProductImage, CategoryVariantOption, ProductCategoryVariantOption
    )
    from django.db import transaction
    import json
    
    # Validate uploaded files first
    images = request.FILES.getlist('images')
    if images:
        file_errors = validate_uploaded_files(images)
        if file_errors:
            return Response({
                'status': 'error',
                'errors': file_errors
            }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        
        with transaction.atomic():
            # Validate and extract basic product data
            name = request.data.get('name', '').strip()
            description = request.data.get('description', '').strip()
            base_price = request.data.get('base_price')
            category_id = request.data.get('category')
            
            
            # Validation
            # print(f"Starting validation...")
            if not name:
                # print(f"VALIDATION FAILED: Product name is empty")
                return Response({
                    'status': 'error',
                    'error': 'Product name is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not description:
                print(f"VALIDATION FAILED: Product description is empty")
                return Response({
                    'status': 'error',
                    'error': 'Product description is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                base_price = float(base_price)
                if base_price < 0:
                    raise ValueError("Price cannot be negative")
                print(f"VALIDATION PASSED: base_price = {base_price}")
            except (TypeError, ValueError) as e:
                print(f"VALIDATION FAILED: base_price error - {e}")
                return Response({
                    'status': 'error',
                    'error': 'Valid base price is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                category_id = int(category_id)
                print(f"VALIDATION PASSED: category_id = {category_id}")
            except (TypeError, ValueError) as e:
                print(f"VALIDATION FAILED: category_id error - {e}")
                return Response({
                    'status': 'error',
                    'error': 'Valid category is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Handle boolean conversion
            is_featured = request.data.get('is_featured', False)
            if isinstance(is_featured, str):
                is_featured = is_featured.lower() in ('true', '1', 'yes', 'on')
            
            # Get stock quantity (default to 0 if not provided)
            stock_quantity = request.data.get('stock_quantity', 0)
            try:
                stock_quantity = int(stock_quantity) if stock_quantity else 0
            except (ValueError, TypeError):
                stock_quantity = 0
                
            product_data = {
                'name': name,
                'description': description,
                'base_price': base_price,
                'stock_quantity': stock_quantity,
                'category_id': category_id,
                'is_featured': bool(is_featured),
                'seller': request.user,
                'is_active': True
            }
            
            # Create product
            product = Product.objects.create(**product_data)
            
            # Handle images
            images = request.FILES.getlist('images')
            for i, image_file in enumerate(images):
                ProductImage.objects.create(
                    product=product,
                    image=image_file,
                    is_primary=(i == 0)  # First image is primary
                )
            
            # Parse variants data from frontend
            variants_data_str = request.data.get('variants_data', '[]')
            print(f"DEBUG: Raw variants_data_str: {variants_data_str}")
            
            try:
                variants_data = json.loads(variants_data_str) if variants_data_str else []
                print(f"DEBUG: Parsed variants_data length: {len(variants_data)}")
                print(f"DEBUG: First few variants_data items: {variants_data[:3] if variants_data else 'None'}")
            except json.JSONDecodeError as e:
                print(f"DEBUG: JSON decode error: {e}")
                variants_data = []
            
            # Create variants using the new ProductCategoryVariantOption model
            variants_created = 0
            combination_stocks = {}  # For Flutter app compatibility
            
            if variants_data:
                # Ensure category has the required variant types for the variants being created
                category = product.category
                print(f"DEBUG: Ensuring variant types for category: {category.name}")
                
                # Analyze what variant types are needed based on the variants being created
                variant_types_needed = set()
                for variant_data in variants_data:
                    try:
                        option_id = variant_data.get('option_id')
                        # Try to get the option to see what variant type it belongs to
                        try:
                            category_variant_option = CategoryVariantOption.objects.get(id=option_id)
                            variant_type = category_variant_option.variant_type
                            variant_types_needed.add(variant_type)
                        except CategoryVariantOption.DoesNotExist:
                            print(f"DEBUG: CategoryVariantOption with id {option_id} not found, skipping")
                            continue
                    except Exception as e:
                        print(f"DEBUG: Error analyzing variant data: {e}")
                        continue
                
                # Ensure all needed variant types are associated with the category
                for variant_type in variant_types_needed:
                    if not category.variant_types.filter(id=variant_type.id).exists():
                        # Create CategoryVariantType if it doesn't exist instead of trying to add
                        from products.models import CategoryVariantType
                        category_variant_type, created = CategoryVariantType.objects.get_or_create(
                            category=category,
                            name=variant_type.name,
                            defaults={'is_required': variant_type.is_required}
                        )
                        if created:
                            print(f"DEBUG: Created variant type '{variant_type.name}' for category '{category.name}'")
                        else:
                            print(f"DEBUG: Variant type '{variant_type.name}' already exists for category '{category.name}'")
                
                print(f"DEBUG: Category '{category.name}' now has {category.variant_types.count()} variant types")
                # print(f"DEBUG: Processing {len(variants_data)} variant options...")
                
                # Group variants by combination for combination_stocks
                from collections import defaultdict
                combination_groups = defaultdict(list)
                
                for variant_data in variants_data:
                    # print(f"DEBUG: Processing variant data: {variant_data}")
                    
                    try:
                        option_id = variant_data.get('option_id')
                        stock_count = int(variant_data.get('stock_count', 0))
                        price_adjustment = float(variant_data.get('price_adjustment', 0))
                        
                        # print(f"DEBUG: Creating variant for option_id: {option_id}, stock: {stock_count}, price_adj: {price_adjustment}")
                        
                        # Get the category variant option
                        category_variant_option = CategoryVariantOption.objects.get(id=option_id)
                        # print(f"DEBUG: Found category variant option: {category_variant_option}")
                        
                        # Create the product variant option
                        product_variant, created = ProductCategoryVariantOption.objects.get_or_create(
                            product=product,
                            category_variant_option=category_variant_option,
                            defaults={
                                'stock_count': stock_count,
                                'price_adjustment': price_adjustment,
                                'is_active': True
                            }
                        )
                        
                        if created:
                            variants_created += 1
                            # print(f"DEBUG: Created variant {variants_created}")
                        else:
                            # print(f"DEBUG: Variant already existed, updated it")
                            product_variant.stock_count = stock_count
                            product_variant.price_adjustment = price_adjustment
                            product_variant.save()
                        
                        # Add to combination_stocks for Flutter compatibility
                        # Use the option_id as the key and stock_count as value
                        combination_stocks[str(option_id)] = stock_count
                        
                    except CategoryVariantOption.DoesNotExist:
                        # print(f"DEBUG: CategoryVariantOption with id {option_id} not found")
                        continue
                    except Exception as e:
                        # print(f"DEBUG: Error creating variant: {e}")
                        continue
                
                # Update the product's combination_stocks field for Flutter app compatibility
                product.combination_stocks = combination_stocks
                product.save(update_fields=['combination_stocks'])
                print(f"DEBUG: Updated product.combination_stocks: {product.combination_stocks}")
                print(f"DEBUG: Product has_variants: {product.has_variants}")
                print(f"DEBUG: Product selected_variants count: {product.selected_variants.count()}")
                
                # Log a sample variant for debugging
                sample_variant = product.selected_variants.first()
                if sample_variant:
                    print(f"DEBUG: Sample variant - Type: {sample_variant.variant_type_name}, Value: {sample_variant.variant_option_value}, Stock: {sample_variant.stock_count}")
                    print(f"DEBUG: Sample variant category_variant_option.variant_type: {sample_variant.category_variant_option.variant_type}")
                
            
            # print(f"DEBUG: Total variants created: {variants_created}")
            
            # Log admin activity
            AdminActivity.objects.create(
                admin=request.user,
                action='create',
                description=f"Created product '{product.name}' with {variants_created} variants",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            return Response({
                'status': 'success',
                'message': f'Product created successfully with {variants_created} variants!',
                'product_id': product.id,
                'variants_created': variants_created
            })
            
    except ValueError as e:
        print(f"ValueError in create_product_with_variants: {str(e)}")
        return Response({
            'status': 'error',
            'error': 'Invalid data provided',
            'details': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except PermissionError as e:
        print(f"PermissionError in create_product_with_variants: {str(e)}")
        return Response({
            'status': 'error',
            'error': 'Permission denied',
            'details': str(e)
        }, status=status.HTTP_403_FORBIDDEN)
    except Exception as e:
        # Log the error for debugging
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        logger.error(f"Error creating product with variants: {str(e)}", exc_info=True)
        print(f"FULL ERROR in create_product_with_variants:")
        print(f"Error: {str(e)}")
        print(f"Type: {type(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        
        return Response({
            'status': 'error',
            'error': f'Internal server error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def get_categories_for_admin(request):
    """API endpoint to get all active categories for admin use - sorted hierarchically"""
    from products.models import Category
    
    # Get categories sorted by hierarchy: parent categories first, then subcategories
    parent_categories = Category.objects.filter(is_active=True, parent__isnull=True).order_by('name')
    subcategories = Category.objects.filter(is_active=True, parent__isnull=False).select_related('parent').order_by('parent__name', 'name')
    
    categories_data = []
    
    # Add parent categories first
    for category in parent_categories:
        categories_data.append({
            'id': category.id,
            'name': category.name,
            'description': category.description,
            'parent_id': None,
            'image': category.image.url if category.image else None,
            'is_active': category.is_active,
            'is_parent': True
        })
    
    # Add subcategories grouped under their parents
    for category in subcategories:
        categories_data.append({
            'id': category.id,
            'name': f"  └─ {category.name}",  # Indent subcategories visually
            'description': category.description,
            'parent_id': category.parent_id,
            'image': category.image.url if category.image else None,
            'is_active': category.is_active,
            'is_parent': False,
            'parent_name': category.parent.name
        })
    
    return Response(categories_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def get_category_attributes_for_admin(request, category_id):
    """API endpoint to get attributes available for a specific category"""
    from products.models import Category, CategoryAttribute
    
    try:
        category = Category.objects.get(id=category_id, is_active=True)
        
        category_attributes = CategoryAttribute.objects.filter(
            category=category,
            attribute__is_active=True
        ).select_related('attribute').order_by('sort_order')
        
        attributes_data = []
        for cat_attr in category_attributes:
            attribute = cat_attr.attribute
            
            # Get active options
            options_data = []
            for option in attribute.options.filter(is_active=True).order_by('sort_order'):
                options_data.append({
                    'id': option.id,
                    'value': option.value,
                    'display_name': option.display_name,
                    'color_code': option.color_code,
                    'is_active': option.is_active,
                    'sort_order': option.sort_order
                })
            
            attributes_data.append({
                'id': cat_attr.id,
                'is_required': cat_attr.is_required,
                'sort_order': cat_attr.sort_order,
                'attribute': {
                    'id': attribute.id,
                    'name': attribute.name,
                    'attribute_type': attribute.attribute_type,
                    'is_required': attribute.is_required,
                    'is_active': attribute.is_active,
                    'options': options_data
                }
            })
        
        return Response(attributes_data)
        
    except Category.DoesNotExist:
        return Response({
            'error': 'Category not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def get_attribute_options_for_admin(request, attribute_type):
    """API endpoint to get options for a specific attribute type"""
    from products.models import ProductAttribute
    
    try:
        attribute = ProductAttribute.objects.get(
            attribute_type=attribute_type,
            is_active=True
        )
        
        options_data = []
        for option in attribute.options.filter(is_active=True).order_by('sort_order'):
            options_data.append({
                'id': option.id,
                'value': option.value,
                'display_name': option.display_name,
                'color_code': option.color_code,
                'is_active': option.is_active,
                'sort_order': option.sort_order
            })
        
        return Response(options_data)
        
    except ProductAttribute.DoesNotExist:
        return Response({
            'error': f'Attribute type "{attribute_type}" not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsAdminUser])
def update_product_with_variants(request, product_id):
    """API endpoint to update a product with variants"""
    from products.models import (
        Product, ProductImage, ProductAttribute, ProductAttributeOption, 
        ProductVariant, ProductVariantAttribute
    )
    from django.db import transaction
    import json
    
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return Response({
            'error': 'Product not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    try:
        with transaction.atomic():
            # Update basic product data
            product.name = request.data.get('name', product.name)
            product.description = request.data.get('description', product.description)
            product.base_price = float(request.data.get('base_price', product.base_price))
            
            # Update stock quantity
            stock_quantity = request.data.get('stock_quantity', product.stock_quantity)
            try:
                product.stock_quantity = int(stock_quantity) if stock_quantity else 0
            except (ValueError, TypeError):
                product.stock_quantity = product.stock_quantity  # Keep current value if invalid
            
            category_id = request.data.get('category')
            if category_id:
                from products.models import Category
                product.category = Category.objects.get(id=int(category_id))
            
            product.is_featured = request.data.get('is_featured', False)
            product.is_active = request.data.get('is_active', True)
            product.save()
            
            # Handle images if new ones are uploaded
            images = request.FILES.getlist('images')
            if images:
                # Delete existing images
                product.images.all().delete()
                
                # Add new images
                for i, image_file in enumerate(images):
                    ProductImage.objects.create(
                        product=product,
                        image=image_file,
                        is_primary=(i == 0)  # First image is primary
                    )
            
            # Handle variants if attributes are selected
            selected_attributes = {}
            for key in request.data.keys():
                if key.startswith('selected_') and key.endswith('_options'):
                    attribute_type = key.replace('selected_', '').replace('_options', '')
                    option_ids = request.data.getlist(key)
                    if option_ids:
                        options = ProductAttributeOption.objects.filter(
                            id__in=option_ids,
                            is_active=True
                        )
                        selected_attributes[attribute_type] = list(options)
            
            # Generate new variants if attributes are selected
            variants_created = 0
            if selected_attributes:
                # Delete existing variants
                product.variants.all().delete()
                
                # Generate all combinations
                attribute_types = list(selected_attributes.keys())
                option_lists = [selected_attributes[attr_type] for attr_type in attribute_types]
                
                import itertools
                all_combinations = list(itertools.product(*option_lists))
                
                # Parse variants data from frontend
                variants_data_str = request.data.get('variants_data', '[]')
                variants_data = json.loads(variants_data_str) if variants_data_str else []
                
                for i, combination in enumerate(all_combinations):
                    # Get variant data for this combination (if provided)
                    variant_data = variants_data[i] if i < len(variants_data) else {}
                    
                    # Handle boolean conversion for variant
                    is_active = variant_data.get('is_active', True)
                    if isinstance(is_active, str):
                        is_active = is_active.lower() in ('true', '1', 'yes', 'on')
                    
                    # Create variant
                    variant = ProductVariant.objects.create(
                        product=product,
                        stock_count=int(variant_data.get('stock_count', 0)),
                        price_adjustment=float(variant_data.get('price_adjustment', 0)),
                        is_active=bool(is_active)
                    )
                    
                    # Create variant attributes
                    for option in combination:
                        ProductVariantAttribute.objects.create(
                            variant=variant,
                            attribute=option.attribute,
                            option=option
                        )
                    
                    variants_created += 1
            
            # Log admin activity
            AdminActivity.objects.create(
                admin=request.user,
                action='update',
                description=f"Updated product '{product.name}' with {variants_created} variants",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            return Response({
                'status': 'success',
                'message': f'Product updated successfully with {variants_created} variants!',
                'product_id': product.id,
                'variants_created': variants_created
            })
            
    except ValueError as e:
        return Response({
            'status': 'error',
            'error': 'Invalid data provided',
            'details': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except PermissionError as e:
        return Response({
            'status': 'error',
            'error': 'Permission denied',
            'details': str(e)
        }, status=status.HTTP_403_FORBIDDEN)
    except Exception as e:
        # Log the error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error updating product with variants: {str(e)}", exc_info=True)
        
        return Response({
            'status': 'error',
            'error': 'Internal server error occurred'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Advertisement Management API Endpoints
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def list_advertisements(request):
    """API endpoint to list all advertisements for admin management"""
    
    # Get filter parameters
    category_id = request.query_params.get('category')
    main_only = request.query_params.get('main_only')
    is_active = request.query_params.get('is_active')
    
    # Build queryset
    queryset = Advertisement.objects.select_related('category').all()
    
    # Apply filters
    if main_only == 'true':
        queryset = queryset.filter(show_on_main=True, category__isnull=True)
    elif category_id:
        try:
            category_id = int(category_id)
            queryset = queryset.filter(category_id=category_id)
        except (ValueError, TypeError):
            return Response({
                'error': 'Invalid category ID'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    if is_active == 'true':
        queryset = queryset.filter(is_active=True)
    elif is_active == 'false':
        queryset = queryset.filter(is_active=False)
    
    # Order by category, then order, then creation date
    queryset = queryset.order_by('category__name', 'order', '-created_at')
    
    # Prepare response data
    ads_data = []
    for ad in queryset:
        ads_data.append({
            'id': ad.id,
            'title': ad.title,
            'description': ad.description,
            'imageUrl': ad.image_display_url,
            'linkUrl': ad.link_url,
            'category_id': ad.category_id,
            'category_name': ad.category.name if ad.category else None,
            'show_on_main': ad.show_on_main,
            'display_location': ad.display_location,
            'isActive': ad.is_active,
            'order': ad.order,
            'created_at': ad.created_at.isoformat(),
            'updated_at': ad.updated_at.isoformat()
        })
    
    return Response({
        'advertisements': ads_data,
        'count': len(ads_data)
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def create_advertisement(request):
    """API endpoint to create a new advertisement"""
    
    try:
        # Extract data from request
        title = request.data.get('title', '').strip()
        description = request.data.get('description', '').strip()
        image_url = request.data.get('image_url', '').strip()
        link_url = request.data.get('link_url', '').strip()
        category_id = request.data.get('category')
        show_on_main = request.data.get('show_on_main', True)
        is_active = request.data.get('is_active', True)
        order = request.data.get('order', 0)
        
        # Validation
        if not title:
            return Response({
                'error': 'Advertisement title is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not image_url:
            return Response({
                'error': 'Image URL is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Handle category
        category = None
        if category_id:
            try:
                category_id = int(category_id)
                category = Category.objects.get(id=category_id, is_active=True)
            except (ValueError, TypeError, Category.DoesNotExist):
                return Response({
                    'error': 'Invalid category selected'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create advertisement
        ad = Advertisement.objects.create(
            title=title,
            description=description,
            image_url=image_url,
            link_url=link_url,
            category=category,
            show_on_main=bool(show_on_main),
            is_active=bool(is_active),
            order=int(order)
        )
        
        # Log admin activity
        AdminActivity.objects.create(
            admin=request.user,
            action='create',
            description=f'Created advertisement "{ad.title}" for {ad.display_location}',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response({
            'status': 'success',
            'message': 'Advertisement created successfully',
            'advertisement': {
                'id': ad.id,
                'title': ad.title,
                'description': ad.description,
                'imageUrl': ad.image_display_url,
                'linkUrl': ad.link_url,
                'category_id': ad.category_id,
                'category_name': ad.category.name if ad.category else None,
                'show_on_main': ad.show_on_main,
                'display_location': ad.display_location,
                'isActive': ad.is_active,
                'order': ad.order,
                'created_at': ad.created_at.isoformat(),
                'updated_at': ad.updated_at.isoformat()
            }
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to create advertisement: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated, IsAdminUser])
def manage_advertisement_detail(request, ad_id):
    """API endpoint to get, update, or delete a specific advertisement"""
    
    try:
        ad = Advertisement.objects.select_related('category').get(id=ad_id)
    except Advertisement.DoesNotExist:
        return Response({
            'error': 'Advertisement not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        # Return advertisement details
        return Response({
            'id': ad.id,
            'title': ad.title,
            'description': ad.description,
            'imageUrl': ad.image_display_url,
            'linkUrl': ad.link_url,
            'category_id': ad.category_id,
            'category_name': ad.category.name if ad.category else None,
            'show_on_main': ad.show_on_main,
            'display_location': ad.display_location,
            'isActive': ad.is_active,
            'order': ad.order,
            'created_at': ad.created_at.isoformat(),
            'updated_at': ad.updated_at.isoformat()
        })
    
    elif request.method == 'PUT':
        # Update advertisement
        try:
            # Extract data from request
            if 'title' in request.data:
                ad.title = request.data['title'].strip()
            if 'description' in request.data:
                ad.description = request.data['description'].strip()
            if 'image_url' in request.data:
                ad.image_url = request.data['image_url'].strip()
            if 'link_url' in request.data:
                ad.link_url = request.data['link_url'].strip()
            if 'order' in request.data:
                ad.order = int(request.data['order'])
            if 'is_active' in request.data:
                ad.is_active = bool(request.data['is_active'])
            if 'show_on_main' in request.data:
                ad.show_on_main = bool(request.data['show_on_main'])
            
            # Handle category
            if 'category' in request.data:
                category_id = request.data['category']
                if category_id:
                    try:
                        category_id = int(category_id)
                        ad.category = Category.objects.get(id=category_id, is_active=True)
                    except (ValueError, TypeError, Category.DoesNotExist):
                        return Response({
                            'error': 'Invalid category selected'
                        }, status=status.HTTP_400_BAD_REQUEST)
                else:
                    ad.category = None
            
            # Validation
            if not ad.title:
                return Response({
                    'error': 'Advertisement title is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not ad.image_url:
                return Response({
                    'error': 'Image URL is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            ad.save()
            
            # Log admin activity
            AdminActivity.objects.create(
                admin=request.user,
                action='update',
                description=f'Updated advertisement "{ad.title}" for {ad.display_location}',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            return Response({
                'status': 'success',
                'message': 'Advertisement updated successfully',
                'advertisement': {
                    'id': ad.id,
                    'title': ad.title,
                    'description': ad.description,
                    'imageUrl': ad.image_display_url,
                    'linkUrl': ad.link_url,
                    'category_id': ad.category_id,
                    'category_name': ad.category.name if ad.category else None,
                    'show_on_main': ad.show_on_main,
                    'display_location': ad.display_location,
                    'isActive': ad.is_active,
                    'order': ad.order,
                    'created_at': ad.created_at.isoformat(),
                    'updated_at': ad.updated_at.isoformat()
                }
            })
            
        except Exception as e:
            return Response({
                'error': f'Failed to update advertisement: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'DELETE':
        # Delete advertisement
        try:
            ad_title = ad.title
            ad_location = ad.display_location
            ad.delete()
            
            # Log admin activity
            AdminActivity.objects.create(
                admin=request.user,
                action='delete',
                description=f'Deleted advertisement "{ad_title}" from {ad_location}',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            return Response({
                'status': 'success',
                'message': 'Advertisement deleted successfully'
            })
            
        except Exception as e:
            return Response({
                'error': f'Failed to delete advertisement: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Seller Registration API Endpoints
@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Only authenticated users can apply
def create_seller_application(request):
    """API endpoint for users to submit seller applications"""
    
    # Check if user already has a pending/approved application
    existing_application = SellerApplication.objects.filter(
        user=request.user,
        status__in=['pending', 'approved']
    ).first()
    
    if existing_application:
        return Response({
            'error': 'You already have a pending or approved seller application',
            'status': existing_application.status
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if user has been permanently rejected
    permanently_rejected = SellerApplication.objects.filter(
        user=request.user,
        status='rejected_permanently'
    ).first()
    
    if permanently_rejected:
        return Response({
            'error': 'Your seller application has been permanently rejected. You cannot apply again.',
            'status': 'rejected_permanently',
            'admin_notes': permanently_rejected.admin_notes
        }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = SellerApplicationCreateSerializer(
        data=request.data, 
        context={'request': request}
    )
    
    if serializer.is_valid():
        application = serializer.save()
        
        # Create admin notification
        AdminNotification.objects.create(
            title='New Seller Application',
            message=f'New {application.get_seller_type_display()} application from {application.business_name} ({application.user.email})',
            notification_type='new_application',
            link=f'/admin/seller-applications/{application.id}/'
        )
        
        return Response({
            'status': 'success',
            'message': 'Seller application submitted successfully',
            'application_id': application.id
        }, status=status.HTTP_201_CREATED)
    
    return Response({
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([])  # Allow any user to get categories
def get_categories_for_seller(request):
    """API endpoint to get categories for seller registration"""
    from products.models import Category
    
    categories = Category.objects.filter(is_active=True, parent__isnull=True).order_by('name')
    
    categories_data = []
    for category in categories:
        categories_data.append({
            'id': category.id,
            'name': category.name,
            'description': category.description or '',
        })
    
    return Response(categories_data)


@api_view(['GET'])
@permission_classes([])  # Allow any user to get subcategories
def get_subcategories_for_seller(request, category_id):
    """API endpoint to get subcategories for a main category"""
    from products.models import Category
    
    try:
        # Check if main category exists
        main_category = Category.objects.get(id=category_id, is_active=True)
        
        # Get subcategories
        subcategories = Category.objects.filter(
            parent=main_category, 
            is_active=True
        ).order_by('name')
        
        subcategories_data = []
        for subcategory in subcategories:
            subcategories_data.append({
                'id': subcategory.id,
                'name': subcategory.name,
                'description': subcategory.description or '',
                'parent_id': subcategory.parent_id,
            })
        
        return Response(subcategories_data)
        
    except Category.DoesNotExist:
        return Response({
            'error': 'Category not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([])  # Allow any user to get governorates
def get_egyptian_governorates(request):
    """API endpoint to get Egyptian governorates for shipping costs"""
    
    # Egyptian governorates list
    governorates = [
        {'id': 1, 'name': 'القاهرة', 'name_en': 'Cairo'},
        {'id': 2, 'name': 'الجيزة', 'name_en': 'Giza'},
        {'id': 3, 'name': 'الأقصر', 'name_en': 'Luxor'},
        {'id': 4, 'name': 'أسوان', 'name_en': 'Aswan'},
        {'id': 5, 'name': 'أسيوط', 'name_en': 'Asyut'},
        {'id': 6, 'name': 'البحيرة', 'name_en': 'Beheira'},
        {'id': 7, 'name': 'بني سويف', 'name_en': 'Beni Suef'},
        {'id': 8, 'name': 'البحر الأحمر', 'name_en': 'Red Sea'},
        {'id': 9, 'name': 'الدقهلية', 'name_en': 'Dakahlia'},
        {'id': 10, 'name': 'دمياط', 'name_en': 'Damietta'},
        {'id': 11, 'name': 'الفيوم', 'name_en': 'Fayyum'},
        {'id': 12, 'name': 'الغربية', 'name_en': 'Gharbia'},
        {'id': 13, 'name': 'الإسماعيلية', 'name_en': 'Ismailia'},
        {'id': 14, 'name': 'كفر الشيخ', 'name_en': 'Kafr el-Sheikh'},
        {'id': 15, 'name': 'مطروح', 'name_en': 'Matrouh'},
        {'id': 16, 'name': 'المنيا', 'name_en': 'Minya'},
        {'id': 17, 'name': 'المنوفية', 'name_en': 'Monufia'},
        {'id': 18, 'name': 'الوادي الجديد', 'name_en': 'New Valley'},
        {'id': 19, 'name': 'شمال سيناء', 'name_en': 'North Sinai'},
        {'id': 20, 'name': 'بورسعيد', 'name_en': 'Port Said'},
        {'id': 21, 'name': 'القليوبية', 'name_en': 'Qalyubia'},
        {'id': 22, 'name': 'قنا', 'name_en': 'Qena'},
        {'id': 23, 'name': 'الشرقية', 'name_en': 'Sharqia'},
        {'id': 24, 'name': 'سوهاج', 'name_en': 'Sohag'},
        {'id': 25, 'name': 'جنوب سيناء', 'name_en': 'South Sinai'},
        {'id': 26, 'name': 'السويس', 'name_en': 'Suez'},
        {'id': 27, 'name': 'الإسكندرية', 'name_en': 'Alexandria'},
    ]
    
    return Response(governorates)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_application_status(request):
    """API endpoint to check user's seller application status"""
    
    try:
        # Get the most recent application for this user
        application = SellerApplication.objects.filter(user=request.user).order_by('-created_at').first()
        
        if application:
            return Response({
                'has_application': True,
                'status': application.status,
                'status_display': application.get_status_display(),
                # Provide backward compatibility with Flutter app field names
                'submitted_at': application.created_at.isoformat(),
                'processed_at': application.reviewed_at.isoformat() if application.reviewed_at else None,
                'admin_notes': application.admin_notes,
                'rejection_reason': application.rejection_reason,
                # Also provide new field names for future use
                'created_at': application.created_at.isoformat(),
                'reviewed_at': application.reviewed_at.isoformat() if application.reviewed_at else None,
                'business_name': application.business_name,
                'seller_type': application.seller_type,
                'seller_type_display': application.get_seller_type_display()
            })
        else:
            return Response({
                'has_application': False
            })
    except Exception as e:
        return Response({
            'has_application': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# SELLER DASHBOARD APIs - For approved sellers to manage their business
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def seller_dashboard_stats(request):
    """API endpoint to get seller dashboard statistics"""
    
    # Check if user is an approved seller
    if request.user.user_type not in ['artist', 'store']:
        return Response({'error': 'Only approved sellers can access this endpoint'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    try:
        # Verify seller application is approved
        application = SellerApplication.objects.get(user=request.user, status='approved')
    except SellerApplication.DoesNotExist:
        return Response({'error': 'Seller application not found or not approved'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    # Get seller's products
    products = Product.objects.filter(seller=request.user)
    total_products = products.count()
    active_products = products.filter(is_active=True).count()
    inactive_products = total_products - active_products
    
    # Get seller's orders
    seller_orders = OrderItem.objects.filter(seller=request.user)
    total_orders = seller_orders.count()
    
    # Revenue calculations
    completed_orders = seller_orders.filter(order__status='delivered')
    total_revenue = completed_orders.aggregate(
        revenue=Sum(F('price') * F('quantity'))
    )['revenue'] or 0
    
    # Commission calculations
    total_commission = completed_orders.aggregate(
        commission=Sum('commission_amount')
    )['commission'] or 0
    
    net_revenue = total_revenue - total_commission
    
    # Order status breakdown
    order_statuses = seller_orders.values('order__status').annotate(
        count=Count('id')
    )
    status_breakdown = {item['order__status']: item['count'] for item in order_statuses}
    
    # Monthly revenue for last 6 months
    monthly_revenue = []
    today = timezone.now().date()
    
    for i in range(6):
        month_end = today.replace(day=1) - timezone.timedelta(days=1)
        month_start = month_end.replace(day=1)
        
        month_revenue = seller_orders.filter(
            order__created_at__date__range=(month_start, month_end),
            order__status='delivered'
        ).aggregate(
            revenue=Sum(F('price') * F('quantity'))
        )['revenue'] or 0
        
        monthly_revenue.append({
            'month': month_start.strftime('%b %Y'),
            'revenue': float(month_revenue)
        })
        
        today = month_start - timezone.timedelta(days=1)
    
    monthly_revenue.reverse()
    
    # Top selling products
    top_products = products.annotate(
        total_sold=Count('orderitem')
    ).order_by('-total_sold')[:5]
    
    top_products_data = []
    for product in top_products:
        revenue = seller_orders.filter(
            product=product,
            order__status='delivered'
        ).aggregate(
            revenue=Sum(F('price') * F('quantity'))
        )['revenue'] or 0
        
        top_products_data.append({
            'id': product.id,
            'name': product.name,
            'total_sold': product.total_sold,
            'revenue': float(revenue),
            'price': float(product.base_price)
        })
    
    # Recent orders (last 10)
    recent_orders = seller_orders.select_related('order', 'product').order_by('-order__created_at')[:10]
    recent_orders_data = []
    
    for item in recent_orders:
        recent_orders_data.append({
            'order_id': item.order.id,
            'product_name': item.product.name,
            'quantity': item.quantity,
            'price': float(item.price),
            'total': float(item.price * item.quantity),
            'status': item.order.status,
            'created_at': item.order.created_at.isoformat(),
            'customer_email': item.order.user.email
        })
    
    return Response({
        'products': {
            'total': total_products,
            'active': active_products,
            'inactive': inactive_products
        },
        'orders': {
            'total': total_orders,
            'status_breakdown': status_breakdown
        },
        'revenue': {
            'total': float(total_revenue),
            'commission': float(total_commission),
            'net': float(net_revenue),
            'monthly': monthly_revenue
        },
        'top_products': top_products_data,
        'recent_orders': recent_orders_data
    })


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def seller_products(request):
    """API endpoint for sellers to manage their products"""
    
    # Check if user is an approved seller
    if request.user.user_type not in ['artist', 'store']:
        return Response({'error': 'Only approved sellers can access this endpoint'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        # Get seller's products with filtering and ordering
        products = Product.objects.filter(seller=request.user).select_related('category').prefetch_related('images').order_by('-created_at')
        
        # Apply filters
        status_filter = request.query_params.get('status')
        category_filter = request.query_params.get('category')
        search = request.query_params.get('search')
        
        if status_filter == 'approved':
            products = products.filter(approval_status='approved')
        elif status_filter == 'pending':
            products = products.filter(approval_status='pending')
        elif status_filter == 'rejected':
            products = products.filter(approval_status='rejected')
        elif status_filter == 'active':
            products = products.filter(is_active=True, approval_status='approved')
        elif status_filter == 'inactive':
            products = products.filter(is_active=False, approval_status='approved')
        
        if category_filter and category_filter not in ['الكل', 'all']:
            # Try to filter by category ID if it's a number, otherwise filter by name
            try:
                category_id = int(category_filter)
                products = products.filter(category_id=category_id)
            except ValueError:
                # If it's not a number, filter by category name
                products = products.filter(category__name=category_filter)
        
        if search:
            products = products.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        
        # Paginate results
        from rest_framework.pagination import PageNumberPagination
        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(products, request)
        
        products_data = []
        for product in page:
            # Get primary image
            primary_image = product.images.filter(is_primary=True).first()
            image_url = primary_image.image.url if primary_image else None
            
            # Get sales stats
            total_sold = OrderItem.objects.filter(product=product).aggregate(
                total=Count('id')
            )['total'] or 0
            
            revenue = OrderItem.objects.filter(
                product=product,
                order__status='delivered'
            ).aggregate(
                revenue=Sum(F('price') * F('quantity'))
            )['revenue'] or 0
            
            products_data.append({
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': float(product.base_price),
                'stock': product.stock,
                'category': product.category.name,
                'is_active': product.is_active,
                'approval_status': product.approval_status,
                'image': image_url,
                'total_sold': total_sold,
                'revenue': float(revenue),
                'created_at': product.created_at.isoformat(),
                'updated_at': product.updated_at.isoformat()
            })
        
        return paginator.get_paginated_response(products_data)
    
    elif request.method == 'POST':
        # Create new product
        data = request.data
        
        try:
            with transaction.atomic():
                product = Product.objects.create(
                    name=data.get('name'),
                    description=data.get('description'),
                    base_price=data.get('price'),
                    stock_quantity=data.get('stock', 0),
                    category_id=data.get('category_id'),
                    seller=request.user,
                    is_active=data.get('is_active', True)
                )
                
                # Handle images if provided
                images = request.FILES.getlist('images')
                for i, image in enumerate(images):
                    ProductImage.objects.create(
                        product=product,
                        image=image,
                        is_primary=(i == 0)  # First image is primary
                    )
                
                return Response({
                    'status': 'success',
                    'message': 'Product created successfully',
                    'product_id': product.id
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def seller_product_detail(request, product_id):
    """API endpoint for sellers to manage individual products"""
    
    try:
        product = Product.objects.get(id=product_id, seller=request.user)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        # Use ProductSerializer to get full product data including variants
        from products.serializers import ProductSerializer
        serializer = ProductSerializer(product)
        product_data = serializer.data
        
        # Add seller-specific analytics data
        total_sold = OrderItem.objects.filter(product=product).count()
        revenue = OrderItem.objects.filter(
            product=product,
            order__status='delivered'
        ).aggregate(
            revenue=Sum(F('price') * F('quantity'))
        )['revenue'] or 0
        
        # Add analytics to the product data
        product_data.update({
            'total_sold': total_sold,
            'revenue': float(revenue),
        })
        
        return Response(product_data)
    
    elif request.method == 'PUT':
        # Update product
        data = request.data
        
        try:
            product.name = data.get('name', product.name)
            product.description = data.get('description', product.description)
            product.base_price = data.get('price', product.base_price)
            product.stock_quantity = data.get('stock', product.stock_quantity)
            product.is_active = data.get('is_active', product.is_active)
            
            if 'category_id' in data:
                product.category_id = data['category_id']
            
            product.save()
            
            return Response({
                'status': 'success',
                'message': 'Product updated successfully'
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        # Delete product
        product.delete()
        return Response({
            'status': 'success',
            'message': 'Product deleted successfully'
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def seller_orders(request):
    """API endpoint for sellers to view their orders"""
    
    # Check if user is an approved seller
    if request.user.user_type not in ['artist', 'store']:
        return Response({'error': 'Only approved sellers can access this endpoint'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    # Get seller's order items
    order_items = OrderItem.objects.filter(seller=request.user).select_related('order', 'product')
    
    # Apply filters
    status_filter = request.query_params.get('status')
    date_from = request.query_params.get('date_from')
    date_to = request.query_params.get('date_to')
    search = request.query_params.get('search')
    
    if status_filter:
        order_items = order_items.filter(order__status=status_filter)
    
    if date_from:
        date_from = timezone.datetime.strptime(date_from, '%Y-%m-%d').date()
        order_items = order_items.filter(order__created_at__date__gte=date_from)
    
    if date_to:
        date_to = timezone.datetime.strptime(date_to, '%Y-%m-%d').date()
        order_items = order_items.filter(order__created_at__date__lte=date_to)
    
    if search:
        order_items = order_items.filter(
            Q(order__id__icontains=search) | 
            Q(product__name__icontains=search) |
            Q(order__user__email__icontains=search)
        )
    
    # Paginate results
    from rest_framework.pagination import PageNumberPagination
    paginator = PageNumberPagination()
    paginator.page_size = 20
    page = paginator.paginate_queryset(order_items.order_by('-order__created_at'), request)
    
    orders_data = []
    for item in page:
        orders_data.append({
            'order_id': item.order.id,
            'product': {
                'id': item.product.id,
                'name': item.product.name,
                'image': item.product.images.filter(is_primary=True).first().image.url if item.product.images.filter(is_primary=True).exists() else None
            },
            'quantity': item.quantity,
            'price': float(item.price),
            'total': float(item.price * item.quantity),
            'commission': float(item.commission_amount),
            'net_amount': float((item.price * item.quantity) - item.commission_amount),
            'status': item.order.status,
            'customer': {
                'email': item.order.user.email,
                'name': f"{item.order.user.first_name} {item.order.user.last_name}".strip() or item.order.user.email
            },
            'shipping_address': item.order.shipping_address,
            'created_at': item.order.created_at.isoformat(),
            'updated_at': item.order.updated_at.isoformat()
        })
    
    return paginator.get_paginated_response(orders_data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_order_status(request, order_id):
    """API endpoint for sellers to update order status for their products"""
    
    try:
        # Get the order and verify seller has items in it
        order = Order.objects.get(id=order_id)
        seller_items = OrderItem.objects.filter(order=order, seller=request.user)
        
        if not seller_items.exists():
            return Response({'error': 'No items found for this seller in this order'}, 
                           status=status.HTTP_404_NOT_FOUND)
        
        new_status = request.data.get('status')
        if new_status not in dict(Order.STATUS_CHOICES):
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Update order status
        order.status = new_status
        order.save()
        
        return Response({
            'status': 'success',
            'message': 'Order status updated successfully'
        })
        
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def seller_profile(request):
    """API endpoint for sellers to view their profile information"""
    
    if request.user.user_type not in ['artist', 'store']:
        return Response({'error': 'Only approved sellers can access this endpoint'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    try:
        application = SellerApplication.objects.get(user=request.user, status='approved')
        
        profile_data = {
            'user_type': application.user_type,
            'name': application.name,
            'email': application.email,
            'phone_number': application.phone_number,
            'address': application.address,
            'photo': application.photo.url if application.photo else None,
            'social_media': application.social_media,
            'categories': application.categories,
            'shipping_costs': application.shipping_costs,
            'details': application.details,
            'approved_at': application.reviewed_at.isoformat() if application.reviewed_at else None
        }
        
        # Add type-specific data
        if application.user_type == 'artist':
            profile_data.update({
                'specialty': application.specialty,
                'bio': application.bio
            })
        elif application.user_type == 'store':
            profile_data.update({
                'store_name': application.store_name,
                'tax_id': application.tax_id,
                'has_physical_store': application.has_physical_store,
                'physical_address': application.physical_address
            })
        
        return Response(profile_data)
        
    except SellerApplication.DoesNotExist:
        return Response({'error': 'Seller application not found'}, 
                       status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def test_seller_auth(request):
    """Test endpoint to check seller authentication"""
    return Response({
        'authenticated': True,
        'user_id': request.user.id,
        'username': request.user.username,
        'user_type': getattr(request.user, 'user_type', 'regular'),
        'is_seller': request.user.user_type in ['artist', 'store'] if hasattr(request.user, 'user_type') else False
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_product_wizard(request):
    """Create a new product using the 6-step wizard system"""
    
    # Check if user is an approved seller
    if request.user.user_type not in ['artist', 'store']:
        return Response({'error': 'Only approved sellers can create products'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    try:
        # Verify seller application is approved
        application = SellerApplication.objects.get(user=request.user, status='approved')
    except SellerApplication.DoesNotExist:
        return Response({'error': 'Seller application not found or not approved'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    try:
        with transaction.atomic():
            # Extract product data
            name = request.data.get('name', '').strip()
            description = request.data.get('description', '').strip()
            base_price = request.data.get('base_price')
            stock_quantity = request.data.get('stock_quantity')
            category_id = request.data.get('category_id')
            
            # Helper function to parse boolean from string
            def parse_bool(value):
                if isinstance(value, bool):
                    return value
                if isinstance(value, str):
                    return value.lower() in ('true', '1', 'yes', 'on')
                return bool(value)
            
            # Parse boolean fields
            featured_request_pending = parse_bool(request.data.get('featured_request_pending', False))
            offers_request_pending = parse_bool(request.data.get('offers_request_pending', False))
            
            # print(f"DEBUG: Featured request pending: {featured_request_pending} (type: {type(featured_request_pending)})")
            # print(f"DEBUG: Offers request pending: {offers_request_pending} (type: {type(offers_request_pending)})")
            
            # Validation
            if not name:
                return Response({'error': 'Product name is required'}, 
                               status=status.HTTP_400_BAD_REQUEST)
            
            if not description:
                return Response({'error': 'Product description is required'}, 
                               status=status.HTTP_400_BAD_REQUEST)
            
            if not base_price or float(base_price) <= 0:
                return Response({'error': 'Valid base price is required'}, 
                               status=status.HTTP_400_BAD_REQUEST)
            
            try:
                stock_quantity = int(stock_quantity) if stock_quantity is not None else 0
                if stock_quantity < 0:
                    raise ValueError("Stock cannot be negative")
                print(f"VALIDATION PASSED: stock_quantity = {stock_quantity}")
            except (TypeError, ValueError) as e:
                print(f"VALIDATION FAILED: stock_quantity error - {e}")
                return Response({'error': 'Valid stock quantity is required'}, 
                               status=status.HTTP_400_BAD_REQUEST)
            
            if not category_id:
                return Response({'error': 'Category is required'}, 
                               status=status.HTTP_400_BAD_REQUEST)
            
            # Get category
            try:
                category = Category.objects.get(id=category_id, is_active=True)
            except Category.DoesNotExist:
                return Response({'error': 'Invalid category'}, 
                               status=status.HTTP_400_BAD_REQUEST)
            
            # Handle category variants to determine stock management strategy
            selected_variants = request.data.get('selected_variants', [])
            if isinstance(selected_variants, str):
                import json
                selected_variants = json.loads(selected_variants)
            
            # Debug logging
            # print(f"DEBUG: Product creation request received")
            # print(f"DEBUG: All request data keys: {list(request.data.keys())}")
            # print(f"DEBUG: Name: {name}")
            # print(f"DEBUG: Description length: {len(description)}")
            # print(f"DEBUG: Base price: {base_price}")
            # print(f"DEBUG: Stock quantity: {stock_quantity}")
            # print(f"DEBUG: Category ID: {category_id}")
            # print(f"DEBUG: Category: {category}")
            # print(f"DEBUG: Selected variants data: {selected_variants}")
            # print(f"DEBUG: Has variants: {bool(selected_variants)}")
            
            # print(f"DEBUG: About to create product...")
            
            # Create the product (stock handling depends on variants)
            try:
                if selected_variants:
                    # print(f"DEBUG: Creating product with category variants...")
                    # Product with variants - set stock_quantity to 0, manage at variant level
                    product = Product.objects.create(
                        name=name,
                        description=description,
                        base_price=float(base_price),
                        stock_quantity=0,  # Managed at variant level
                        category=category,
                        seller=request.user,
                        featured_request_pending=featured_request_pending,
                        offers_request_pending=offers_request_pending,
                        is_active=False,  # Admin needs to approve first
                        approval_status='pending'
                    )
                else:
                    # print(f"DEBUG: Creating simple product without variants...")
                    # Simple product without variants - manage stock at product level
                    product = Product.objects.create(
                        name=name,
                        description=description,
                        base_price=float(base_price),
                        stock_quantity=int(stock_quantity),
                        category=category,
                        seller=request.user,
                        featured_request_pending=featured_request_pending,
                        offers_request_pending=offers_request_pending,
                        is_active=False,  # Admin needs to approve first
                        approval_status='pending'
                    )
                # print(f"DEBUG: Product created with ID: {product.id}")
            except Exception as product_creation_error:
                # print(f"DEBUG: Failed to create product: {str(product_creation_error)}")
                raise
            
            # Set request timestamps if requested
            if product.featured_request_pending:
                product.featured_requested_at = timezone.now()
            if product.offers_request_pending:
                product.offers_requested_at = timezone.now()
            product.save()
            
            # Handle tags
            tags_data = request.data.get('tags', [])
            if isinstance(tags_data, str):
                import json
                tags_data = json.loads(tags_data)
            
            for tag_name in tags_data:
                if tag_name.strip():
                    # Try to get existing tag or create new custom tag
                    tag, created = Tag.objects.get_or_create(
                        name=tag_name.strip(),
                        defaults={
                            'is_predefined': False,
                            'created_by': request.user
                        }
                    )
                    product.tags.add(tag)
            
            # Handle category variants if they exist
            if selected_variants:
                # print(f"DEBUG: Processing {len(selected_variants)} category variants...")
                from products.models import CategoryVariantOption, ProductCategoryVariantOption
                
                # Ensure category has the required variant types for the variants being created
                category = product.category
                print(f"DEBUG: Ensuring variant types for seller category: {category.name}")
                
                # Analyze what variant types are needed based on the variants being created
                variant_types_needed = set()
                for variant_data in selected_variants:
                    try:
                        option_id = variant_data.get('option_id')
                        # Try to get the option to see what variant type it belongs to
                        try:
                            category_variant_option = CategoryVariantOption.objects.get(id=option_id)
                            variant_type = category_variant_option.variant_type
                            variant_types_needed.add(variant_type)
                        except CategoryVariantOption.DoesNotExist:
                            print(f"DEBUG: CategoryVariantOption with id {option_id} not found, skipping")
                            continue
                    except Exception as e:
                        print(f"DEBUG: Error analyzing seller variant data: {e}")
                        continue
                
                # Ensure all needed variant types are associated with the category
                for variant_type in variant_types_needed:
                    if not category.variant_types.filter(id=variant_type.id).exists():
                        # Create CategoryVariantType if it doesn't exist instead of trying to add
                        from products.models import CategoryVariantType
                        category_variant_type, created = CategoryVariantType.objects.get_or_create(
                            category=category,
                            name=variant_type.name,
                            defaults={'is_required': variant_type.is_required}
                        )
                        if created:
                            print(f"DEBUG: Created variant type '{variant_type.name}' for seller category '{category.name}'")
                        else:
                            print(f"DEBUG: Variant type '{variant_type.name}' already exists for seller category '{category.name}'")
                
                print(f"DEBUG: Seller category '{category.name}' now has {category.variant_types.count()} variant types")
                
                variants_created = 0
                for variant_data in selected_variants:
                    try:
                        option_id = variant_data.get('option_id')
                        stock_count = int(variant_data.get('stock_count', 0))
                        price_adjustment = float(variant_data.get('price_adjustment', 0))
                        is_active = variant_data.get('is_active', True)
                        
                        if isinstance(is_active, str):
                            is_active = is_active.lower() in ('true', '1', 'yes', 'on')
                        
                        if option_id:
                            category_variant_option = CategoryVariantOption.objects.get(id=option_id)
                            product_variant, created = ProductCategoryVariantOption.objects.get_or_create(
                                product=product,
                                category_variant_option=category_variant_option,
                                defaults={
                                    'stock_count': stock_count,
                                    'price_adjustment': price_adjustment,
                                    'is_active': bool(is_active)
                                }
                            )
                            
                            if created:
                                variants_created += 1
                            else:
                                 print(f"DEBUG: Variant already exists: {product_variant}")
                                
                    except CategoryVariantOption.DoesNotExist:
                        # print(f"DEBUG: CategoryVariantOption with id {option_id} not found")
                        continue
                    except Exception as e:
                        # print(f"DEBUG: Error creating variant: {e}")
                        continue
                
                # print(f"DEBUG: Created {variants_created} category variants for product {product.name}")
                
                # Update product total stock based on selected variants
                total_stock = sum(v.stock_count for v in product.selected_variants.filter(is_active=True))
                product.stock_quantity = total_stock
                product.save()
            
            # Handle images
            images = request.FILES.getlist('images')
            if images:
                # Process and save images as ProductImage objects
                for i, image_file in enumerate(images):
                    ProductImage.objects.create(
                        product=product,
                        image=image_file,
                        is_primary=(i == 0)  # First image is primary
                    )
            
            # Handle discount request
            discount_request_data = request.data.get('discount_request')
            if discount_request_data:
                if isinstance(discount_request_data, str):
                    import json
                    discount_request_data = json.loads(discount_request_data)
                
                DiscountRequest.objects.create(
                    product=product,
                    seller=request.user,
                    original_price=float(discount_request_data.get('original_price', base_price)),
                    requested_discount_percentage=int(discount_request_data.get('requested_discount_percentage', 0)),
                    discount_reason=discount_request_data.get('discount_reason', ''),
                    request_featured=discount_request_data.get('request_featured', False),
                    request_latest_offers=discount_request_data.get('request_latest_offers', False)
                )
            
            # Log admin activity for review (skip if admin field is required)
            try:
                AdminActivity.objects.create(
                    admin=request.user,  # Use the submitting user instead of None
                    action='create',  # Use valid action choice
                    description=f"New product '{product.name}' submitted by {request.user.username} for review",
                    ip_address=request.META.get('REMOTE_ADDR')
                )
            except Exception as activity_error:
                # Don't fail the product creation if activity logging fails
                 print(f"DEBUG: Failed to log admin activity: {str(activity_error)}")
            
            print(f"DEBUG: Product created successfully - ID: {product.id}")
            
            return Response({
                'success': True,
                'message': 'Product created successfully and submitted for admin review',
                'product_id': product.id,
                'data': {
                    'id': product.id,
                    'name': product.name,
                    'price': float(product.base_price),
                    'status': 'pending_review'
                }
            }, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        # print(f"DEBUG: Exception occurred during product creation:")
        # print(f"DEBUG: Error: {str(e)}")
        # print(f"DEBUG: Traceback: {error_traceback}")
        
        return Response({
            'success': False,
            'message': f'Error creating product: {str(e)}',
            'debug_info': error_traceback if settings.DEBUG else None
        }, status=status.HTTP_400_BAD_REQUEST)


# New Seller Product Management Endpoints

@api_view(['PUT', 'POST'])
@permission_classes([IsAuthenticated])
def toggle_seller_product_status(request, product_id):
    """Toggle product active/inactive status for sellers"""
    
    # Check if user is an approved seller
    if request.user.user_type not in ['artist', 'store']:
        return Response({'error': 'Only approved sellers can access this endpoint'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    try:
        product = Product.objects.get(id=product_id, seller=request.user)
        
        # Only allow toggling for approved products
        if product.approval_status != 'approved':
            return Response({
                'error': 'Can only toggle status for approved products',
                'approval_status': product.approval_status
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Store the old status for logging
        old_status = product.is_active
        
        # Toggle the status
        product.is_active = not product.is_active
        product.save()
        
        # Log the activity
        try:
            AdminActivity.objects.create(
                admin=request.user,
                action='toggle_status',
                description=f'Seller {"activated" if product.is_active else "deactivated"} product "{product.name}"',
                ip_address=get_client_ip(request)
            )
        except Exception as e:
            # Don't fail the toggle if logging fails
            print(f"Failed to log activity: {e}")
        
        return Response({
            'status': 'success',
            'message': f'Product {"activated" if product.is_active else "deactivated"} successfully',
            'is_active': product.is_active,
            'product': {
                'id': product.id,
                'name': product.name,
                'is_active': product.is_active,
                'approval_status': product.approval_status
            }
        })
        
    except Product.DoesNotExist:
        return Response({'error': 'Product not found or you do not have permission to modify it'}, 
                       status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': f'Failed to toggle product status: {str(e)}'}, 
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def duplicate_seller_product(request, product_id):
    """Duplicate a product for sellers"""
    
    # Check if user is an approved seller
    if request.user.user_type not in ['artist', 'store']:
        return Response({'error': 'Only approved sellers can access this endpoint'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    try:
        original_product = Product.objects.get(id=product_id, seller=request.user)
        
        # Create duplicate product
        duplicate_product = Product.objects.create(
            name=f"{original_product.name} - نسخة",
            description=original_product.description,
            base_price=original_product.base_price,
            category=original_product.category,
            seller=request.user,
            stock_quantity=original_product.stock_quantity,
            is_active=False,  # Set duplicate as inactive by default
            featured_request_pending=False
        )
        
        # Copy product images if any
        for image in original_product.images.all():
            ProductImage.objects.create(
                product=duplicate_product,
                image=image.image,
                is_primary=image.is_primary
            )
        
        return Response({
            'status': 'success',
            'message': 'Product duplicated successfully',
            'product': {
                'id': duplicate_product.id,
                'name': duplicate_product.name,
                'price': float(duplicate_product.base_price),
                'is_active': duplicate_product.is_active
            }
        }, status=status.HTTP_201_CREATED)
        
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_seller_product_stock(request, product_id):
    """Update product stock quantity for sellers"""
    
    # Check if user is an approved seller
    if request.user.user_type not in ['artist', 'store']:
        return Response({'error': 'Only approved sellers can access this endpoint'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    try:
        product = Product.objects.get(id=product_id, seller=request.user)
        new_stock = request.data.get('stock_quantity')
        
        if new_stock is None:
            return Response({'error': 'stock_quantity is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            new_stock = int(new_stock)
            if new_stock < 0:
                raise ValueError("Stock cannot be negative")
        except ValueError as e:
            return Response({'error': 'Invalid stock quantity'}, status=status.HTTP_400_BAD_REQUEST)
        
        product.stock_quantity = new_stock
        product.save()
        
        return Response({
            'status': 'success',
            'message': 'Stock updated successfully',
            'new_stock': product.stock_quantity
        })
        
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_seller_variant_stock(request, product_id, variant_id):
    """Update variant stock quantity for sellers"""
    
    # Check if user is an approved seller
    if request.user.user_type not in ['artist', 'store']:
        return Response({'error': 'Only approved sellers can access this endpoint'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    try:
        from products.models import ProductCategoryVariantOption
        
        # Verify product belongs to seller
        product = Product.objects.get(id=product_id, seller=request.user)
        
        # Get the variant
        variant = ProductCategoryVariantOption.objects.get(id=variant_id, product=product)
        
        new_stock = request.data.get('stock_count')
        
        if new_stock is None:
            return Response({'error': 'stock_count is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            new_stock = int(new_stock)
            if new_stock < 0:
                raise ValueError("Stock cannot be negative")
        except ValueError as e:
            return Response({'error': 'Valid stock quantity is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        variant.stock_count = new_stock
        variant.save()
        
        return Response({
            'status': 'success',
            'message': 'Variant stock updated successfully',
            'new_stock': new_stock
        })
        
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    except ProductCategoryVariantOption.DoesNotExist:
        return Response({'error': 'Variant not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_combination_variant_stock(request, product_id):
    """Update combination variant stock for sellers (e.g., '29_27' for white+20x30cm)"""
    
    # Check if user is an approved seller
    if request.user.user_type not in ['artist', 'store']:
        return Response({'error': 'Only approved sellers can access this endpoint'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    try:
        # Verify product belongs to seller
        product = Product.objects.get(id=product_id, seller=request.user)
        
        combination_id = request.data.get('combination_id')
        new_stock = request.data.get('stock_count')
        
        if not combination_id:
            return Response({'error': 'combination_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if new_stock is None:
            return Response({'error': 'stock_count is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            new_stock = int(new_stock)
            if new_stock < 0:
                raise ValueError("Stock cannot be negative")
        except ValueError as e:
            return Response({'error': 'Valid stock quantity is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate combination_id format (should be like "29_27")
        if '_' not in combination_id:
            return Response({'error': 'Invalid combination_id format'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Update combination stocks
        if product.combination_stocks is None:
            product.combination_stocks = {}
        
        product.combination_stocks[combination_id] = new_stock
        product.save(update_fields=['combination_stocks', 'updated_at'])
        
        return Response({
            'status': 'success',
            'message': 'Combination variant stock updated successfully',
            'combination_id': combination_id,
            'new_stock': new_stock
        })
        
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def bulk_edit_seller_products(request):
    """Bulk edit multiple products for sellers"""
    
    # Check if user is an approved seller
    if request.user.user_type not in ['artist', 'store']:
        return Response({'error': 'Only approved sellers can access this endpoint'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    try:
        product_ids = request.data.get('product_ids', [])
        update_data = request.data.get('update_data', {})
        
        if not product_ids:
            return Response({'error': 'product_ids is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get products owned by the seller
        products = Product.objects.filter(id__in=product_ids, seller=request.user)
        
        if not products:
            return Response({'error': 'No valid products found'}, status=status.HTTP_404_NOT_FOUND)
        
        updated_count = 0
        for product in products:
            if 'is_active' in update_data:
                product.is_active = update_data['is_active']
            if 'base_price' in update_data:
                product.base_price = update_data['base_price']
            if 'stock_quantity' in update_data:
                product.stock_quantity = update_data['stock_quantity']
            
            product.save()
            updated_count += 1
        
        return Response({
            'status': 'success',
            'message': f'Successfully updated {updated_count} products',
            'updated_count': updated_count
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_seller_products(request):
    """Export seller's products data"""
    
    # Check if user is an approved seller
    if request.user.user_type not in ['artist', 'store']:
        return Response({'error': 'Only approved sellers can access this endpoint'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    try:
        format_type = request.query_params.get('format', 'csv')
        
        # Get seller's products
        products = Product.objects.filter(seller=request.user).select_related('category')
        
        # Prepare data
        export_data = []
        for product in products:
            export_data.append({
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': float(product.base_price),
                'stock': product.stock_quantity,
                'category': product.category.name,
                'is_active': product.is_active,
                'created_at': product.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            })
        
        if format_type == 'csv':
            # For now, return JSON data (CSV generation can be implemented later)
            return Response({
                'status': 'success',
                'message': 'Products exported successfully',
                'format': format_type,
                'data': export_data,
                'count': len(export_data)
            })
        else:
            return Response({'error': 'Unsupported format'}, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def seller_product_analytics(request):
    """Get product analytics for sellers"""
    
    # Check if user is an approved seller
    if request.user.user_type not in ['artist', 'store']:
        return Response({'error': 'Only approved sellers can access this endpoint'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    try:
        # Get seller's products
        products = Product.objects.filter(seller=request.user)
        
        # Calculate analytics
        total_products = products.count()
        active_products = products.filter(is_active=True).count()
        inactive_products = total_products - active_products
        
        # Get total sales and revenue
        total_sales = OrderItem.objects.filter(seller=request.user).aggregate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum(F('price') * F('quantity'))
        )
        
        # Top selling products
        top_products = OrderItem.objects.filter(seller=request.user)\
            .values('product__name')\
            .annotate(total_sold=Sum('quantity'))\
            .order_by('-total_sold')[:5]
        
        # Monthly sales data (last 12 months)
        from datetime import datetime, timedelta
        from dateutil.relativedelta import relativedelta
        
        monthly_data = []
        current_date = datetime.now()
        
        for i in range(12):
            month_start = current_date - relativedelta(months=i)
            month_start = month_start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = month_start + relativedelta(months=1) - timedelta(seconds=1)
            
            month_sales = OrderItem.objects.filter(
                seller=request.user,
                order__created_at__range=[month_start, month_end]
            ).aggregate(
                sales=Sum('quantity'),
                revenue=Sum(F('price') * F('quantity'))
            )
            
            monthly_data.append({
                'month': month_start.strftime('%Y-%m'),
                'sales': month_sales['sales'] or 0,
                'revenue': float(month_sales['revenue'] or 0)
            })
        
        monthly_data.reverse()
        
        return Response({
            'status': 'success',
            'data': {
                'overview': {
                    'total_products': total_products,
                    'active_products': active_products,
                    'inactive_products': inactive_products,
                    'total_sales': total_sales['total_quantity'] or 0,
                    'total_revenue': float(total_sales['total_revenue'] or 0)
                },
                'top_products': list(top_products),
                'monthly_data': monthly_data
            }
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# Seller Requests API Endpoints
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def seller_requests_list(request):
    """Get all seller requests (offers, featured products, and ad bookings)"""
    try:
        from products.models import SellerOfferRequest, SellerFeaturedRequest
        from .models import AdBookingRequest
        
        # Get offer requests with related data
        offer_requests = SellerOfferRequest.objects.select_related(
            'product', 'seller', 'reviewed_by'
        ).order_by('-created_at')
        
        # Get featured requests with related data
        featured_requests = SellerFeaturedRequest.objects.select_related(
            'product', 'seller', 'reviewed_by'
        ).order_by('-created_at')
        
        # Get ad booking requests with related data
        ad_booking_requests = AdBookingRequest.objects.select_related(
            'seller', 'ad_type', 'category'
        ).order_by('-created_at')
        
        # Serialize offer requests
        offer_data = []
        for req in offer_requests:
            offer_data.append({
                'id': req.id,
                'product_name': req.product.name,
                'product_id': req.product.id,
                'seller_name': req.seller.email,
                'seller_type': req.seller.user_type,
                'seller_id': req.seller.id,
                'discount_percentage': req.discount_percentage,
                'original_price': float(req.product.price),
                'offer_price': float(req.offer_price) if req.offer_price else 0,
                'offer_duration_days': req.offer_duration_days,
                'start_date': req.start_date.isoformat() if req.start_date else None,
                'end_date': req.end_date.isoformat() if req.end_date else None,
                'description': req.description or '',
                'status': req.status,
                'status_display': req.get_status_display(),
                'request_fee': float(req.request_fee),
                'payment_reference': req.payment_reference or '',
                'admin_notes': req.admin_notes or '',
                'reviewed_by': req.reviewed_by.email if req.reviewed_by else None,
                'reviewed_at': req.reviewed_at.isoformat() if req.reviewed_at else None,
                'created_at': req.created_at.isoformat(),
                'updated_at': req.updated_at.isoformat(),
            })
        
        # Serialize featured requests
        featured_data = []
        for req in featured_requests:
            featured_data.append({
                'id': req.id,
                'product_name': req.product.name,
                'product_id': req.product.id,
                'seller_name': req.seller.email,
                'seller_type': req.seller.user_type,
                'seller_id': req.seller.id,
                'priority': req.priority,
                'featured_duration_days': req.featured_duration_days,
                'reason': req.reason or '',
                'status': req.status,
                'status_display': req.get_status_display(),
                'request_fee': float(req.request_fee),
                'payment_reference': req.payment_reference or '',
                'admin_notes': req.admin_notes or '',
                'reviewed_by': req.reviewed_by.email if req.reviewed_by else None,
                'reviewed_at': req.reviewed_at.isoformat() if req.reviewed_at else None,
                'created_at': req.created_at.isoformat(),
                'updated_at': req.updated_at.isoformat(),
            })
        
        # Serialize ad booking requests
        ad_booking_data = []
        for req in ad_booking_requests:
            ad_booking_data.append({
                'id': req.id,
                'type': 'ad_booking',
                'ad_type': req.ad_type.name if req.ad_type else None,
                'ad_type_display': req.ad_type.name_ar if req.ad_type and req.ad_type.name_ar else (req.ad_type.name if req.ad_type else None),
                'seller_name': req.seller.email if req.seller else 'Unknown',
                'seller_type': req.seller.user_type if req.seller else None,
                'seller_id': req.seller.id if req.seller else None,
                'category': req.category.name if req.category else None,
                'duration': req.duration,
                'price': float(req.price),
                'total_cost': float(req.total_cost) if req.total_cost else float(req.price),
                'payment_method': req.payment_method,
                'sender_info': req.sender_info or '',
                'ad_title': req.ad_title or '',
                'ad_description': req.ad_description or '',
                'product_id': req.product_id or '',
                'special_offer_percentage': float(req.special_offer_percentage) if req.special_offer_percentage else None,
                'duration_value': req.duration_value,
                'status': req.status,
                'status_display': req.get_status_display(),
                'payment_screenshot': req.payment_screenshot.url if req.payment_screenshot else None,
                'ad_image': req.ad_image.url if req.ad_image else None,
                'admin_notes': req.admin_notes or '',
                'created_at': req.created_at.isoformat(),
                'updated_at': req.updated_at.isoformat(),
            })
        
        # Calculate statistics
        total_offer_requests = len(offer_data)
        total_featured_requests = len(featured_data)
        total_ad_booking_requests = len(ad_booking_data)
        pending_offers = sum(1 for r in offer_data if r['status'] == 'payment_completed')
        pending_featured = sum(1 for r in featured_data if r['status'] == 'payment_completed')
        pending_ad_bookings = sum(1 for r in ad_booking_data if r['status'] == 'payment_submitted')
        
        return Response({
            'status': 'success',
            'offer_requests': offer_data,
            'featured_requests': featured_data,
            'ad_booking_requests': ad_booking_data,
            'total_offer_requests': total_offer_requests,
            'total_featured_requests': total_featured_requests,
            'total_ad_booking_requests': total_ad_booking_requests,
            'pending_requests': pending_offers + pending_featured + pending_ad_bookings,
            'statistics': {
                'total_offer_requests': total_offer_requests,
                'total_featured_requests': total_featured_requests,
                'total_ad_booking_requests': total_ad_booking_requests,
                'pending_offers': pending_offers,
                'pending_featured': pending_featured,
                'pending_ad_bookings': pending_ad_bookings,
            }
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def mark_payment_completed(request, request_id):
    """Mark seller request payment as completed"""
    try:
        from products.models import SellerOfferRequest, SellerFeaturedRequest
        
        request_type = request.data.get('request_type')  # 'offer' or 'featured'
        payment_reference = request.data.get('payment_reference')
        admin_notes = request.data.get('admin_notes', '')
        
        if not payment_reference:
            return Response({'error': 'Payment reference is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if request_type == 'offer':
            seller_request = get_object_or_404(SellerOfferRequest, id=request_id)
        elif request_type == 'featured':
            seller_request = get_object_or_404(SellerFeaturedRequest, id=request_id)
        else:
            return Response({'error': 'Invalid request type'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Update payment status
        seller_request.status = 'payment_completed'
        seller_request.payment_reference = payment_reference
        if admin_notes:
            seller_request.admin_notes = admin_notes
        seller_request.save()
        
        # Log admin activity
        AdminActivity.objects.create(
            admin=request.user,
            action='mark_payment_completed',
            description=f'Marked payment completed for {request_type} request #{request_id}',
            ip_address=get_client_ip(request)
        )
        
        return Response({
            'status': 'success',
            'message': f'Payment marked as completed for {request_type} request #{request_id}'
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def approve_offer_request(request, request_id):
    """Approve offer request and create actual ProductOffer"""
    try:
        from products.models import SellerOfferRequest
        
        offer_request = get_object_or_404(SellerOfferRequest, id=request_id)
        
        # Use the model's built-in approval method
        product_offer = offer_request.approve_and_create_offer(request.user)
        
        if product_offer:
            # Log admin activity
            AdminActivity.objects.create(
                admin=request.user,
                action='approve_offer_request',
                description=f'Approved offer request #{request_id} and created ProductOffer #{product_offer.id}',
                ip_address=get_client_ip(request)
            )
            
            return Response({
                'status': 'success',
                'message': f'Offer request approved and ProductOffer created successfully',
                'offer_id': product_offer.id
            })
        else:
            return Response({
                'error': 'Failed to create ProductOffer. Request may not have completed payment.'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def approve_featured_request(request, request_id):
    """Approve featured request and create actual FeaturedProduct"""
    try:
        from products.models import SellerFeaturedRequest
        
        featured_request = get_object_or_404(SellerFeaturedRequest, id=request_id)
        
        # Use the model's built-in approval method
        featured_product = featured_request.approve_and_create_featured(request.user)
        
        if featured_product:
            # Log admin activity
            AdminActivity.objects.create(
                admin=request.user,
                action='approve_featured_request',
                description=f'Approved featured request #{request_id} and created FeaturedProduct #{featured_product.id}',
                ip_address=get_client_ip(request)
            )
            
            return Response({
                'status': 'success',
                'message': f'Featured request approved and FeaturedProduct created successfully',
                'featured_id': featured_product.id
            })
        else:
            return Response({
                'error': 'Failed to create FeaturedProduct. Request may not have completed payment.'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def mark_payment_and_auto_approve(request, request_id):
    """Mark payment completed and automatically approve request"""
    try:
        from products.models import SellerOfferRequest, SellerFeaturedRequest
        import logging
        logger = logging.getLogger(__name__)
        
        request_type = request.data.get('request_type')  # 'offer' or 'featured'
        payment_reference = request.data.get('payment_reference')
        admin_notes = request.data.get('admin_notes', '')
        
        if not payment_reference:
            return Response({'error': 'Payment reference is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not request_type:
            return Response({'error': 'Request type is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if request_type == 'offer':
            seller_request = get_object_or_404(SellerOfferRequest, id=request_id)
        elif request_type == 'featured':
            seller_request = get_object_or_404(SellerFeaturedRequest, id=request_id)
        else:
            return Response({'error': f'Invalid request type: {request_type}. Must be "offer" or "featured"'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if already approved
        if seller_request.status == 'approved':
            return Response({
                'error': f'This {request_type} request has already been approved and processed.',
                'status': 'already_approved'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Mark payment as completed first
        seller_request.status = 'payment_completed'
        seller_request.payment_reference = payment_reference
        if admin_notes:
            seller_request.admin_notes = admin_notes
        seller_request.save()
        
        # Auto-approve and create actual product
        if request_type == 'offer':
            created_item = seller_request.approve_and_create_offer(request.user)
            item_type = 'ProductOffer'
        else:
            created_item = seller_request.approve_and_create_featured(request.user)
            item_type = 'FeaturedProduct'
        
        if created_item:
            # Log admin activity
            AdminActivity.objects.create(
                admin=request.user,
                action='mark_payment_and_auto_approve',
                description=f'Payment completed and auto-approved {request_type} request #{request_id}, created {item_type} #{created_item.id}',
                ip_address=get_client_ip(request)
            )
            
            return Response({
                'status': 'success',
                'message': f'Payment completed and {request_type} request auto-approved successfully. {item_type} created.',
                'created_item_id': created_item.id
            })
        else:
            return Response({
                'error': f'Payment marked but failed to create {item_type}'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Exception in mark_payment_and_auto_approve: {str(e)}", exc_info=True)
        return Response({'error': f'An error occurred: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)


# ================================
# AD BOOKING API ENDPOINTS
# ================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ad_types(request):
    """Get all active ad types for booking form"""
    try:
        from .models import AdType, AdPricing
        
        ad_types = AdType.objects.filter(is_active=True).prefetch_related('pricing')
        
        data = []
        for ad_type in ad_types:
            type_data = {
                'id': ad_type.id,
                'type': ad_type.name,
                'name': ad_type.get_name_display(),
                'name_ar': ad_type.name_ar,
                'description': ad_type.description,
                'requires_category': ad_type.requires_category,
                'requirements': ad_type.requirements or {},
                'pricing': {}
            }
            
            # Add pricing information
            for pricing in ad_type.pricing.filter(is_active=True):
                type_data['pricing'][pricing.duration] = {
                    'price': float(pricing.price),
                    'min_price': float(pricing.min_price) if pricing.min_price else None,
                    'max_price': float(pricing.max_price) if pricing.max_price else None,
                }
            
            data.append(type_data)
        
        return Response({
            'results': data,
            'count': len(data)
        })
    
    except Exception as e:
        return Response({'error': f'Error fetching ad types: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_ad_booking(request):
    """Create a new ad booking request"""
    try:
        from .models import AdType, AdBookingRequest, AdPricing
        
        # Check if user is a seller (artist or store)
        is_seller = (
            request.user.user_type in ['artist', 'store'] and
            (hasattr(request.user, 'artist_profile') or hasattr(request.user, 'store_profile'))
        )
        
        if not is_seller:
            return Response({
                'error': 'Only approved sellers (artists/stores) can create ad booking requests'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get request data
        data = request.data
        ad_type_name = data.get('ad_type')
        duration = data.get('duration')
        price = data.get('price')
        payment_method = data.get('payment_method')
        sender_info = data.get('sender_info')
        category_id = data.get('category_id')
        
        # Additional fields for enhanced ad booking
        ad_title = data.get('ad_title', '')
        ad_description = data.get('ad_description', '')
        product_id = data.get('product_id')
        offer_percentage = data.get('offer_percentage')
        promotion_duration = data.get('promotion_duration')
        total_price = data.get('total_price', price)
        
        # Validate required fields
        if not all([ad_type_name, duration, price, payment_method]):
            return Response({
                'error': 'Missing required fields: ad_type, duration, price, payment_method'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate payment method
        valid_payment_methods = ['instapay', 'vodafone_cash', 'visa']
        if payment_method not in valid_payment_methods:
            return Response({
                'error': f'Invalid payment method. Must be one of: {", ".join(valid_payment_methods)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get ad type
        try:
            ad_type = AdType.objects.get(name=ad_type_name, is_active=True)
        except AdType.DoesNotExist:
            return Response({
                'error': f'Invalid ad type: {ad_type_name}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate category if required
        category = None
        if ad_type.requires_category:
            if not category_id:
                return Response({
                    'error': 'Category is required for this ad type'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                category = Category.objects.get(id=category_id)
            except Category.DoesNotExist:
                return Response({
                    'error': f'Invalid category ID: {category_id}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate pricing
        try:
            pricing = AdPricing.objects.get(ad_type=ad_type, duration=duration, is_active=True)
            if abs(float(price) - float(pricing.price)) > 0.01:  # Allow small floating point differences
                return Response({
                    'error': f'Price mismatch. Expected: {pricing.price}, received: {price}'
                }, status=status.HTTP_400_BAD_REQUEST)
        except AdPricing.DoesNotExist:
            return Response({
                'error': f'No pricing found for {ad_type_name} - {duration}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create the booking request
        with transaction.atomic():
            booking = AdBookingRequest.objects.create(
                seller=request.user,
                ad_type=ad_type,
                category=category,
                duration=duration,
                price=price,
                payment_method=payment_method,
                sender_info=sender_info,
                ad_title=ad_title,
                ad_description=ad_description,
                product_id=product_id,
                special_offer_percentage=offer_percentage,
                duration_value=promotion_duration,
                total_cost=total_price
            )
            
            # Handle file uploads
            if 'payment_screenshot' in request.FILES:
                booking.payment_screenshot = request.FILES['payment_screenshot']
            
            if 'ad_image' in request.FILES:
                booking.ad_image = request.FILES['ad_image']
            
            booking.save()
            
            # Create admin notification
            AdminNotification.objects.create(
                title='New Ad Booking Request',
                message=f'New ad booking request from {request.user.email} for {ad_type.name_ar}',
                notification_type='ad_booking',
                link=f'/admin/ad-bookings/{booking.id}/'
            )
        
        return Response({
            'message': 'Ad booking request created successfully',
            'booking_id': booking.id,
            'status': booking.status,
            'request_fee': float(booking.price)
        }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error creating ad booking: {str(e)}", exc_info=True)
        return Response({
            'error': f'An error occurred while creating booking: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@require_http_methods(["GET", "POST"])
@login_required
def update_ad_type_requirements(request, ad_type_id):
    """Get or update requirements for a specific ad type"""
    try:
        from .models import AdType
        
        # Check if user is admin
        if not request.user.is_staff:
            return JsonResponse({
                'success': False,
                'message': 'Only admins can access ad type requirements'
            }, status=403)
        
        # Get ad type
        try:
            ad_type = AdType.objects.get(id=ad_type_id)
        except AdType.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': f'Ad type with ID {ad_type_id} not found'
            }, status=404)
        
        if request.method == 'GET':
            # Return current requirements
            return JsonResponse({
                'success': True,
                'ad_type': {
                    'id': ad_type.id,
                    'name': ad_type.name,
                    'name_ar': ad_type.name_ar,
                    'requirements': ad_type.requirements or {}
                }
            })
        
        elif request.method == 'POST':
            # Update requirements
            import json
            
            # Get requirements from POST data
            requirements_str = request.POST.get('requirements')
            if not requirements_str:
                return JsonResponse({
                    'success': False,
                    'message': 'Requirements data is required'
                }, status=400)
            
            try:
                requirements = json.loads(requirements_str)
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid JSON format for requirements'
                }, status=400)
            
            # Validate requirements structure
            valid_fields = ['ad_title', 'ad_description', 'ad_image', 'ad_link', 'category', 'product_id', 'special_offer_percentage']
            valid_values = ['required', 'optional', 'hidden']
            
            for field, value in requirements.items():
                if field not in valid_fields:
                    return JsonResponse({
                        'success': False,
                        'message': f'Invalid field: {field}'
                    }, status=400)
                if value not in valid_values:
                    return JsonResponse({
                        'success': False,
                        'message': f'Invalid value for {field}: {value}. Must be one of: {", ".join(valid_values)}'
                    }, status=400)
            
            # Update ad type requirements
            ad_type.requirements = requirements
            ad_type.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Requirements updated successfully'
            })
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error managing ad type requirements: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f'Failed to manage requirements: {str(e)}'
        }, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_ad_bookings_list(request):
    """Admin endpoint to list all ad booking requests"""
    try:
        from .content_models import AdBookingRequest
        
        bookings = AdBookingRequest.objects.select_related(
            'seller', 'ad_type', 'category'
        ).order_by('-created_at')
        
        # Filter by status if provided
        status_filter = request.GET.get('status')
        if status_filter:
            bookings = bookings.filter(status=status_filter)
        
        # Search by seller email
        search = request.GET.get('search')
        if search:
            bookings = bookings.filter(
                Q(seller__email__icontains=search) |
                Q(seller__first_name__icontains=search) |
                Q(seller__last_name__icontains=search)
            )
        
        # Pagination
        paginator = AdminPagination()
        page = paginator.paginate_queryset(bookings, request)
        
        data = []
        for booking in page:
            data.append({
                'id': booking.id,
                'seller': {
                    'email': booking.seller.email,
                    'name': f"{booking.seller.first_name} {booking.seller.last_name}".strip(),
                },
                'ad_type': {
                    'name': booking.ad_type.name,
                    'name_ar': booking.ad_type.name_ar,
                },
                'category': {
                    'id': booking.category.id,
                    'name': booking.category.name,
                } if booking.category else None,
                'duration': booking.duration,
                'price': float(booking.price),
                'payment_method': booking.payment_method,
                'sender_info': booking.sender_info,
                'payment_screenshot': booking.payment_screenshot.url if booking.payment_screenshot else None,
                'status': booking.status,
                'admin_notes': booking.admin_notes,
                'created_at': booking.created_at.isoformat(),
                'updated_at': booking.updated_at.isoformat(),
            })
        
        return paginator.get_paginated_response(data)
    
    except Exception as e:
        return Response({'error': f'Error fetching ad bookings: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def approve_ad_booking(request, booking_id):
    """Admin endpoint to approve ad booking and create advertisement"""
    try:
        from .content_models import AdBookingRequest
        from datetime import timedelta
        
        booking = get_object_or_404(AdBookingRequest, id=booking_id)
        
        if not booking.can_be_approved():
            return Response({
                'error': f'Booking cannot be approved. Current status: {booking.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get admin input data
        ad_title = request.data.get('ad_title')
        ad_description = request.data.get('ad_description')
        start_date = request.data.get('start_date')
        admin_notes = request.data.get('admin_notes', '')
        
        if not ad_title:
            return Response({
                'error': 'Ad title is required for approval'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            # Update booking status
            booking.status = 'approved'
            booking.ad_title = ad_title
            booking.ad_description = ad_description
            booking.admin_notes = admin_notes
            booking.approved_at = timezone.now()
            
            if start_date:
                booking.start_date = start_date
                # Calculate end date based on duration
                if booking.duration == 'daily':
                    booking.end_date = booking.start_date + timedelta(days=1)
                elif booking.duration == 'weekly':
                    booking.end_date = booking.start_date + timedelta(days=7)
                elif booking.duration == 'monthly':
                    booking.end_date = booking.start_date + timedelta(days=30)
            
            booking.save()
            
            # Create the actual advertisement
            ad = Advertisement.objects.create(
                title=ad_title,
                description=ad_description,
                image=booking.ad_image if booking.ad_image else None,
                image_url=booking.ad_image.url if booking.ad_image else None,
                link_url=booking.ad_link,
                is_active=True,
                order=0,
                category_id=booking.category.id if booking.category else None,
                show_on_main=booking.ad_type.name == 'home_slider'
            )
            
            # Log admin activity
            AdminActivity.objects.create(
                admin=request.user,
                action='approve',
                description=f'Approved ad booking #{booking_id} and created advertisement #{ad.id}',
                ip_address=get_client_ip(request)
            )
        
        return Response({
            'message': 'Ad booking approved successfully',
            'advertisement_id': ad.id,
            'booking_status': booking.status
        })
    
    except Exception as e:
        return Response({'error': f'Error approving ad booking: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def reject_ad_booking(request, booking_id):
    """Admin endpoint to reject ad booking request"""
    try:
        from .content_models import AdBookingRequest
        
        booking = get_object_or_404(AdBookingRequest, id=booking_id)
        
        if booking.status in ['rejected', 'completed']:
            return Response({
                'error': f'Booking cannot be rejected. Current status: {booking.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        admin_notes = request.data.get('admin_notes', '')
        
        booking.status = 'rejected'
        booking.admin_notes = admin_notes
        booking.save()
        
        # Log admin activity
        AdminActivity.objects.create(
            admin=request.user,
            action='reject',
            description=f'Rejected ad booking #{booking_id}',
            ip_address=get_client_ip(request)
        )
        
        return Response({
            'message': 'Ad booking rejected successfully',
            'booking_status': booking.status
        })
    
    except Exception as e:
        return Response({'error': f'Error rejecting ad booking: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Ad Booking Dashboard API endpoints
@api_view(['GET'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated, IsAdminUser])
def ad_booking_detail_api(request, booking_id):
    """Get detailed information about an ad booking"""
    from .models import AdBookingRequest
    
    try:
        booking = AdBookingRequest.objects.select_related(
            'seller', 'ad_type', 'category'
        ).get(id=booking_id)
        
        return Response({
            'id': booking.id,
            'seller_name': booking.seller.get_full_name() or booking.seller.email,
            'seller_email': booking.seller.email,
            'seller_phone': getattr(booking.seller, 'phone', None),
            'ad_type_name': booking.ad_type.name_ar or booking.ad_type.name,
            'category_name': booking.category.name if booking.category else None,
            'duration_display': booking.get_duration_display(),
            'price': str(booking.price),
            'total_cost': str(booking.total_cost) if booking.total_cost else str(booking.price),
            'duration_value': booking.duration_value,
            'payment_method_display': booking.get_payment_method_display(),
            'sender_info': booking.sender_info,
            'ad_title': booking.ad_title,
            'ad_description': booking.ad_description,
            'product_id': booking.product_id,
            'special_offer_percentage': str(booking.special_offer_percentage) if booking.special_offer_percentage else None,
            'status_display': booking.get_status_display(),
            'admin_notes': booking.admin_notes,
            'created_at': booking.created_at.strftime('%b %d, %Y %H:%M'),
            'start_date': booking.start_date.strftime('%b %d, %Y %H:%M') if getattr(booking, 'start_date', None) else None,
            'end_date': booking.end_date.strftime('%b %d, %Y %H:%M') if getattr(booking, 'end_date', None) else None,
        })
        
    except AdBookingRequest.DoesNotExist:
        return Response({'error': 'Ad booking not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def approve_ad_booking_api(request, booking_id):
    """Approve an ad booking request"""
    from .models import AdBookingRequest
    
    try:
        booking = AdBookingRequest.objects.get(id=booking_id)
        
        if booking.status not in ['payment_submitted', 'under_review']:
            return Response({
                'success': False,
                'message': 'This booking cannot be approved in its current status'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        booking.status = 'approved'
        booking.save()
        
        return Response({
            'success': True,
            'message': 'Ad booking approved successfully'
        })
        
    except AdBookingRequest.DoesNotExist:
        return Response({'success': False, 'message': 'Ad booking not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def activate_ad_booking_api(request, booking_id):
    """Activate an approved ad booking and create corresponding advertisement"""
    from .models import AdBookingRequest
    from django.db import transaction
    
    try:
        booking = AdBookingRequest.objects.get(id=booking_id)
        
        if booking.status != 'approved':
            return Response({
                'success': False,
                'message': 'Only approved bookings can be activated'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Use atomic transaction to ensure both operations succeed
        with transaction.atomic():
            # Update booking status and dates
            booking.status = 'active'
            from datetime import datetime, timedelta
            from django.utils import timezone
            now = timezone.now()
            booking.start_date = now
            
            # Calculate duration based on duration_value (multiplier) and duration type
            duration_value = booking.duration_value or 1
            
            if booking.duration == 'daily':
                booking.end_date = now + timedelta(days=duration_value)
            elif booking.duration == 'weekly':
                booking.end_date = now + timedelta(weeks=duration_value)
            elif booking.duration == 'monthly':
                booking.end_date = now + timedelta(days=30 * duration_value)
            else:
                booking.end_date = now + timedelta(days=duration_value)
                
            booking.save()
            
            # Auto-create advertisement based on ad type
            ad_created = _create_advertisement_from_booking(booking)
            
            message = 'Ad booking activated successfully'
            if ad_created:
                message += f' and {booking.ad_type.name_ar} advertisement created'
            
            return Response({
                'success': True,
                'message': message,
                'ad_created': ad_created
            })
        
    except AdBookingRequest.DoesNotExist:
        return Response({'success': False, 'message': 'Ad booking not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _create_advertisement_from_booking(booking):
    """Helper function to create advertisement based on booking ad type"""
    try:
        ad_type = booking.ad_type.name
        
        if ad_type == 'home_slider' or ad_type == 'category_slider':
            # Create Advertisement for sliders
            from products.models import Advertisement
            
            advertisement = Advertisement.objects.create(
                title=booking.ad_title or f"إعلان {booking.ad_type.name_ar}",
                description=booking.ad_description or "",
                image=booking.ad_image,
                link_url=booking.ad_link or "",
                is_active=True,
                order=0
            )
            return True
            
        elif ad_type == 'offer_ad' and booking.product_id:
            # Create ProductOffer
            from products.models import ProductOffer, Product
            
            try:
                product = Product.objects.get(id=booking.product_id)
                offer_percentage = booking.special_offer_percentage or 10
                
                # Calculate duration for offer
                duration_days = 7  # default
                duration_value = booking.duration_value or 1
                
                if booking.duration == 'daily':
                    duration_days = duration_value
                elif booking.duration == 'weekly':
                    duration_days = duration_value * 7
                elif booking.duration == 'monthly':
                    duration_days = duration_value * 30
                
                offer = ProductOffer.objects.create(
                    product=product,
                    discount_percentage=offer_percentage,
                    duration_days=duration_days,
                    is_active=True,
                    created_by=booking.seller
                )
                return True
            except Product.DoesNotExist:
                pass
                
        elif ad_type == 'featured_product' and booking.product_id:
            # Create FeaturedProduct
            from products.models import FeaturedProduct, Product
            
            try:
                product = Product.objects.get(id=booking.product_id)
                
                # Calculate duration for featured product
                duration_days = 7  # default
                duration_value = booking.duration_value or 1
                
                if booking.duration == 'daily':
                    duration_days = duration_value
                elif booking.duration == 'weekly':
                    duration_days = duration_value * 7
                elif booking.duration == 'monthly':
                    duration_days = duration_value * 30
                
                featured = FeaturedProduct.objects.create(
                    product=product,
                    duration_days=duration_days,
                    is_active=True,
                    created_by=booking.seller
                )
                return True
            except Product.DoesNotExist:
                pass
        
        return False
        
    except Exception as e:
        print(f"Error creating advertisement from booking: {e}")
        return False


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def reject_ad_booking_api(request, booking_id):
    """Reject an ad booking request"""
    from .models import AdBookingRequest
    
    try:
        booking = AdBookingRequest.objects.get(id=booking_id)
        reason = request.data.get('reason', '')
        
        if booking.status not in ['payment_submitted', 'under_review']:
            return Response({
                'success': False,
                'message': 'This booking cannot be rejected in its current status'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        booking.status = 'rejected'
        if reason:
            current_notes = booking.admin_notes or ''
            booking.admin_notes = f"{current_notes}\n\nRejection reason: {reason}".strip()
        booking.save()
        
        return Response({
            'success': True,
            'message': 'Ad booking rejected successfully'
        })
        
    except AdBookingRequest.DoesNotExist:
        return Response({'success': False, 'message': 'Ad booking not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def update_ad_booking_notes_api(request, booking_id):
    """Update admin notes for an ad booking"""
    from .models import AdBookingRequest
    
    try:
        booking = AdBookingRequest.objects.get(id=booking_id)
        notes = request.data.get('notes', '')
        
        booking.admin_notes = notes
        booking.save()
        
        return Response({
            'success': True,
            'message': 'Notes updated successfully'
        })
        
    except AdBookingRequest.DoesNotExist:
        return Response({'success': False, 'message': 'Ad booking not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ========================
# USER NOTIFICATION MANAGEMENT VIEWS
# ========================

class UserNotificationListView(generics.ListAPIView):
    """List all user notifications for admin management"""
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    pagination_class = AdminPagination
    
    def get_queryset(self):
        queryset = UserNotification.objects.all().order_by('-created_at')
        
        # Filter by user
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by type
        notification_type = self.request.query_params.get('type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        # Filter by read status
        is_read = self.request.query_params.get('is_read')
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read.lower() == 'true')
        
        # Filter by push status
        push_sent = self.request.query_params.get('push_sent')
        if push_sent is not None:
            queryset = queryset.filter(push_sent=push_sent.lower() == 'true')
        
        return queryset.select_related('user')


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def send_user_notification_api(request):
    """
    Send notification with push notification via Custom Admin API
    """
    try:
        user_id = request.data.get('user_id')
        title = request.data.get('title')
        message = request.data.get('message')
        notification_type = request.data.get('notification_type', 'system')
        priority = request.data.get('priority', 'normal')
        action_url = request.data.get('action_url')
        image_url = request.data.get('image_url')
        
        # Validation
        if not all([user_id, title, message]):
            return Response({
                'success': False,
                'message': 'user_id, title, and message are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Create notification with automatic push
        notification = send_notification_with_push(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            action_url=action_url,
            image_url=image_url,
            priority=priority
        )
        
        return Response({
            'success': True,
            'message': f'✅ Notification sent successfully to {user.email}',
            'notification': {
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'user': user.email,
                'push_sent': notification.push_sent,
                'created_at': notification.created_at
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error sending notification: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def send_bulk_notification_api(request):
    """
    Send notification to multiple users
    """
    try:
        user_ids = request.data.get('user_ids', [])  # List of user IDs
        send_to_all = request.data.get('send_to_all', False)  # Send to all users
        target_audience = request.data.get('target_audience')  # Target audience type
        title = request.data.get('title')
        message = request.data.get('message')
        notification_type = request.data.get('notification_type', 'system')
        priority = request.data.get('priority', 'normal')
        action_url = request.data.get('action_url')
        image_url = request.data.get('image_url')
        
        # Validation
        if not all([title, message]):
            return Response({
                'success': False,
                'message': 'title and message are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get target users based on audience type
        if send_to_all or target_audience == 'all':
            users = User.objects.filter(is_active=True)
        elif target_audience == 'active':
            # Users who have logged in recently (within last 30 days)
            from datetime import datetime, timedelta
            thirty_days_ago = datetime.now() - timedelta(days=30)
            users = User.objects.filter(is_active=True, last_login__gte=thirty_days_ago)
        elif target_audience == 'sellers':
            # Users who are sellers (have seller applications or user_type is seller)
            from django.db.models import Q
            users = User.objects.filter(is_active=True).filter(
                Q(user_type='seller') | 
                Q(sellerapplication__isnull=False)
            ).distinct()
        elif target_audience == 'customers':
            # Users who are not sellers
            from django.db.models import Q
            users = User.objects.filter(is_active=True).exclude(
                Q(user_type='seller') | 
                Q(sellerapplication__isnull=False)
            )
        elif user_ids:
            users = User.objects.filter(id__in=user_ids, is_active=True)
        else:
            return Response({
                'success': False,
                'message': 'Either user_ids, send_to_all, or target_audience must be provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not users.exists():
            return Response({
                'success': False,
                'message': 'No valid users found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Send notifications
        sent_count = 0
        failed_count = 0
        notifications_created = []
        
        for user in users:
            try:
                notification = send_notification_with_push(
                    user=user,
                    title=title,
                    message=message,
                    notification_type=notification_type,
                    action_url=action_url,
                    image_url=image_url,
                    priority=priority
                )
                notifications_created.append({
                    'id': notification.id,
                    'user': user.email,
                    'push_sent': notification.push_sent
                })
                sent_count += 1
            except Exception as e:
                failed_count += 1
                print(f"Failed to send notification to {user.email}: {e}")
        
        return Response({
            'success': True,
            'message': f'✅ Bulk notification sent to {sent_count} users',
            'details': {
                'sent_count': sent_count,
                'failed_count': failed_count,
                'total_users': users.count(),
                'notifications': notifications_created
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error sending bulk notification: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def notification_stats_api(request):
    """Get notification statistics for admin dashboard"""
    try:
        # Basic stats
        total_notifications = UserNotification.objects.count()
        total_users_with_notifications = UserNotification.objects.values('user').distinct().count()
        push_sent_count = UserNotification.objects.filter(push_sent=True).count()
        
        # Recent notifications (last 7 days)
        from datetime import timedelta
        week_ago = timezone.now() - timedelta(days=7)
        recent_notifications = UserNotification.objects.filter(created_at__gte=week_ago).count()
        
        # Notifications by type
        notification_types = UserNotification.objects.values('notification_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Active devices count
        active_devices = Device.objects.filter(is_active=True, notifications_enabled=True).count()
        
        # Push notification logs (last 100)
        recent_push_logs = PushNotificationLog.objects.select_related(
            'notification', 'device'
        ).order_by('-sent_at')[:100]
        
        push_log_data = []
        for log in recent_push_logs:
            push_log_data.append({
                'id': log.id,
                'notification_title': log.notification.title,
                'user_email': log.device.user.email,
                'platform': log.device.platform,
                'status': log.status,
                'sent_at': log.sent_at,
                'error_message': log.error_message
            })
        
        return Response({
            'success': True,
            'stats': {
                'total_notifications': total_notifications,
                'total_users_with_notifications': total_users_with_notifications,
                'push_sent_count': push_sent_count,
                'recent_notifications': recent_notifications,
                'active_devices': active_devices,
                'notification_types': list(notification_types),
                'recent_push_logs': push_log_data
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error getting notification stats: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def users_for_notifications_api(request):
    """Get list of users for notification targeting"""
    try:
        users = User.objects.filter(is_active=True).order_by('email')
        
        # Add device info
        user_data = []
        for user in users:
            devices = Device.objects.filter(user=user, is_active=True, notifications_enabled=True)
            user_data.append({
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'user_type': user.user_type,
                'device_count': devices.count(),
                'has_devices': devices.exists(),
                'platforms': list(devices.values_list('platform', flat=True).distinct())
            })
        
        return Response({
            'success': True,
            'users': user_data,
            'total_users': len(user_data),
            'users_with_devices': len([u for u in user_data if u['has_devices']])
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error getting users: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
