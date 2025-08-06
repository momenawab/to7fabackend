from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count, Sum, Q, F
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
import csv

from custom_auth.models import User, Artist, Store
from products.models import Product, Category
from orders.models import Order, OrderItem
from .models import SellerApplication, AdminActivity, AdminNotification
from .serializers import (
    SellerApplicationSerializer, UserSerializer, ProductSerializer,
    OrderSerializer, AdminNotificationSerializer
)

# Test endpoint for debugging authentication
@api_view(['GET'])
@permission_classes([])  # No permissions required
def test_authentication(request):
    """Test endpoint to debug authentication issues"""
    data = {
        'user_authenticated': request.user.is_authenticated,
        'user_id': request.user.id if request.user.is_authenticated else None,
        'user_email': request.user.email if request.user.is_authenticated else None,
        'is_staff': request.user.is_staff if request.user.is_authenticated else None,
        'is_superuser': request.user.is_superuser if request.user.is_authenticated else None,
        'session_key': request.session.session_key,
        'auth_header': request.META.get('HTTP_AUTHORIZATION', 'None'),
        'csrf_token': request.META.get('HTTP_X_CSRFTOKEN', 'None'),
    }
    return Response(data)

# Seller Application Views
class SellerApplicationListView(generics.ListAPIView):
    serializer_class = SellerApplicationSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        status_filter = self.request.query_params.get('status', None)
        queryset = SellerApplication.objects.all().order_by('-submitted_at')
        
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
    application.processed_at = timezone.now()
    application.processed_by = request.user
    application.save()
    
    # Log admin activity
    activity_action = 'approve_application' if action else 'reject_application'
    AdminActivity.objects.create(
        admin=request.user,
        action=activity_action,
        description=f"{'Approved' if action else 'Rejected'} seller application #{application.id} for {application.name}",
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    # If approved, update user type and create profile
    if action:
        user = application.user
        user.user_type = application.user_type
        user.save()
        
        if application.user_type == 'artist':
            # Create artist profile
            Artist.objects.create(
                user=user,
                specialty=application.specialty,
                bio=application.bio,
                is_verified=True
            )
        elif application.user_type == 'store':
            # Create store profile
            Store.objects.create(
                user=user,
                store_name=application.store_name,
                tax_id=application.tax_id,
                has_physical_store=application.has_physical_store,
                physical_address=application.physical_address,
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
    
    def get_queryset(self):
        user_type = self.request.query_params.get('type', None)
        search_query = self.request.query_params.get('q', None)
        
        queryset = User.objects.all()
        
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
    
    def get_queryset(self):
        category_id = self.request.query_params.get('category', None)
        status = self.request.query_params.get('status', None)
        search_query = self.request.query_params.get('q', None)
        
        queryset = Product.objects.all()
        
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
    
    def get_queryset(self):
        status = self.request.query_params.get('status', None)
        search_query = self.request.query_params.get('q', None)
        
        queryset = Order.objects.all()
        
        if status and status != 'all':
            queryset = queryset.filter(status=status)
            
        if search_query:
            queryset = queryset.filter(
                Q(id__icontains=search_query) | 
                Q(customer__email__icontains=search_query)
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
@permission_classes([IsAuthenticated, IsAdminUser])
def report_summary(request):
    """API endpoint to get summary report data"""
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
    # Top selling products
    top_products = Product.objects.annotate(
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
    
    # Top categories
    top_categories = Category.objects.annotate(
        product_count=Count('product')
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
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def create_product_with_variants(request):
    """API endpoint to create a product with variants"""
    from products.models import (
        Product, ProductImage, ProductAttribute, ProductAttributeOption, 
        ProductVariant, ProductVariantAttribute
    )
    from django.db import transaction
    import json
    
    try:
        with transaction.atomic():
            # Extract basic product data
            product_data = {
                'name': request.data.get('name'),
                'description': request.data.get('description'),
                'base_price': float(request.data.get('base_price', 0)),
                'category_id': int(request.data.get('category')),
                'is_featured': request.data.get('is_featured', False),
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
            
            # Get selected attribute options
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
            
            # Generate variants
            variants_created = 0
            if selected_attributes:
                # Get all combinations
                attribute_types = list(selected_attributes.keys())
                option_lists = [selected_attributes[attr_type] for attr_type in attribute_types]
                
                # Generate all combinations using itertools.product
                import itertools
                all_combinations = list(itertools.product(*option_lists))
                
                # Parse variants data from frontend
                variants_data_str = request.data.get('variants_data', '[]')
                variants_data = json.loads(variants_data_str) if variants_data_str else []
                
                for i, combination in enumerate(all_combinations):
                    # Get variant data for this combination (if provided)
                    variant_data = variants_data[i] if i < len(variants_data) else {}
                    
                    # Create variant
                    variant = ProductVariant.objects.create(
                        product=product,
                        stock_count=int(variant_data.get('stock_count', 0)),
                        price_adjustment=float(variant_data.get('price_adjustment', 0)),
                        is_active=variant_data.get('is_active', True)
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
            
    except Exception as e:
        return Response({
            'status': 'error',
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def get_categories_for_admin(request):
    """API endpoint to get all active categories for admin use"""
    from products.models import Category
    
    categories = Category.objects.filter(is_active=True).order_by('name')
    
    categories_data = []
    for category in categories:
        categories_data.append({
            'id': category.id,
            'name': category.name,
            'description': category.description,
            'parent_id': category.parent_id,
            'image': category.image.url if category.image else None,
            'is_active': category.is_active
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
                    
                    # Create variant
                    variant = ProductVariant.objects.create(
                        product=product,
                        stock_count=int(variant_data.get('stock_count', 0)),
                        price_adjustment=float(variant_data.get('price_adjustment', 0)),
                        is_active=variant_data.get('is_active', True)
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
            
    except Exception as e:
        return Response({
            'status': 'error',
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST) 