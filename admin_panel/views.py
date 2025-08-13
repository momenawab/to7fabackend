from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from datetime import datetime

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status

from custom_auth.models import User, Artist, Store
from products.models import Product, Category
from orders.models import Order
from .models import SellerApplication, AdminActivity, AdminNotification
from notifications.models import Notification

# Helper function to check if user is admin
def is_admin(user):
    return user.is_staff or user.is_superuser

# Authentication views
def admin_login(request):
    # Debug CSRF token
    if request.method == 'POST':
        print(f"CSRF Token in POST: {request.POST.get('csrfmiddlewaretoken', 'NOT FOUND')}")
        print(f"CSRF Token in META: {request.META.get('HTTP_X_CSRFTOKEN', 'NOT FOUND')}")
        print(f"CSRF Cookie: {request.COOKIES.get('csrftoken', 'NOT FOUND')}")
    
    if request.user.is_authenticated and is_admin(request.user):
        return redirect('admin_panel:dashboard')
        
    if request.method == 'POST':
        email = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        
        if user is not None and is_admin(user):
            login(request, user)
            
            # Log admin activity
            AdminActivity.objects.create(
                admin=user,
                action='login',
                description=f"Admin logged in: {user.email}",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            next_url = request.POST.get('next', '')
            if next_url and next_url != '/':
                return redirect(next_url)
            else:
                return redirect('admin_panel:dashboard')
        else:
            messages.error(request, "Invalid email or password, or you don't have admin privileges.")
    
    return render(request, 'admin_panel/login.html')

@login_required
def admin_logout(request):
    if is_admin(request.user):
        # Log admin activity
        AdminActivity.objects.create(
            admin=request.user,
            action='logout',
            description=f"Admin logged out: {request.user.email}",
            ip_address=request.META.get('REMOTE_ADDR')
        )
    
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('admin_panel:login')

# Dashboard view
@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    # Get stats for dashboard
    total_users = User.objects.count()
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    pending_applications = SellerApplication.objects.filter(status='pending').count()
    
    # Recent applications with optimized queries
    recent_applications = SellerApplication.objects.select_related('user').filter(
        status='pending'
    ).order_by('-submitted_at')[:5]
    
    # Recent orders with optimized queries
    recent_orders = Order.objects.select_related('user').all().order_by('-created_at')[:5]
    
    # Notifications
    notifications = AdminNotification.objects.filter(
        is_read=False
    ).order_by('-created_at')[:5]
    
    context = {
        'total_users': total_users,
        'total_products': total_products,
        'total_orders': total_orders,
        'pending_applications': pending_applications,
        'recent_applications': recent_applications,
        'recent_orders': recent_orders,
        'notifications': notifications,
        'active_tab': 'dashboard'
    }
    
    return render(request, 'admin_panel/dashboard.html', context)

# Seller Applications List
@login_required
@user_passes_test(is_admin)
def seller_applications(request):
    status_filter = request.GET.get('status', 'pending')
    
    if status_filter == 'all':
        applications = SellerApplication.objects.select_related('user', 'processed_by').all().order_by('-submitted_at')
    else:
        applications = SellerApplication.objects.select_related('user', 'processed_by').filter(
            status=status_filter
        ).order_by('-submitted_at')
    
    # Pagination
    paginator = Paginator(applications, 10)
    page_number = request.GET.get('page', 1)
    applications_page = paginator.get_page(page_number)
    
    context = {
        'applications': applications_page,
        'status_filter': status_filter,
        'active_tab': 'applications'
    }
    
    return render(request, 'admin_panel/seller_applications.html', context)

# Seller Application Detail
@login_required
@user_passes_test(is_admin)
def seller_application_detail(request, application_id):
    application = get_object_or_404(SellerApplication, id=application_id)
    
    # Get category names instead of IDs
    category_names = []
    if application.categories:
        for cat_id in application.categories:
            try:
                category = Category.objects.get(id=cat_id)
                category_names.append({'id': cat_id, 'name': category.name})
            except Category.DoesNotExist:
                category_names.append({'id': cat_id, 'name': f'Unknown Category (ID: {cat_id})'})
    
    # Get subcategories from details if available
    subcategories = []
    if application.details and 'subcategories:' in application.details.lower():
        import re
        import json
        lines = application.details.split('\n')
        for line in lines:
            if 'subcategories:' in line.lower():
                try:
                    match = re.search(r'subcategories:\s*(\[.*?\])', line)
                    if match:
                        subcat_ids = json.loads(match.group(1))
                        for subcat_id in subcat_ids:
                            try:
                                subcategory = Category.objects.get(id=subcat_id)
                                subcategories.append({'id': subcat_id, 'name': subcategory.name})
                            except Category.DoesNotExist:
                                subcategories.append({'id': subcat_id, 'name': f'Unknown Subcategory (ID: {subcat_id})'})
                except:
                    pass
    
    # Egyptian governorates mapping for shipping costs
    gov_names = {
        '1': 'القاهرة', '2': 'الجيزة', '3': 'الأقصر', '4': 'أسوان', '5': 'أسيوط',
        '6': 'البحيرة', '7': 'بني سويف', '8': 'البحر الأحمر', '9': 'الدقهلية', '10': 'دمياط',
        '11': 'الفيوم', '12': 'الغربية', '13': 'الإسماعيلية', '14': 'كفر الشيخ', '15': 'مطروح',
        '16': 'المنيا', '17': 'المنوفية', '18': 'الوادي الجديد', '19': 'شمال سيناء', '20': 'بورسعيد',
        '21': 'القليوبية', '22': 'قنا', '23': 'الشرقية', '24': 'سوهاج', '25': 'جنوب سيناء',
        '26': 'السويس', '27': 'الإسكندرية'
    }
    
    # Process shipping costs with names
    shipping_costs_with_names = []
    if application.shipping_costs:
        for gov_id, cost in application.shipping_costs.items():
            gov_name = gov_names.get(str(gov_id), f'Governorate {gov_id}')
            shipping_costs_with_names.append({
                'id': gov_id,
                'name': gov_name,
                'cost': float(cost),
                'available': float(cost) > 0
            })
        # Sort by availability first, then by name
        shipping_costs_with_names.sort(key=lambda x: (not x['available'], x['name']))
    
    # Calculate shipping statistics
    shipping_stats = {
        'total': len(shipping_costs_with_names),
        'available': sum(1 for item in shipping_costs_with_names if item['available']),
        'unavailable': sum(1 for item in shipping_costs_with_names if not item['available'])
    }
    
    context = {
        'application': application,
        'category_names': category_names,
        'subcategories': subcategories,
        'shipping_costs_with_names': shipping_costs_with_names,
        'shipping_stats': shipping_stats,
        'active_tab': 'applications'
    }
    
    return render(request, 'admin_panel/seller_application_detail.html', context)

# Process Seller Application
@login_required
@user_passes_test(is_admin)
@require_POST
def process_application(request, application_id):
    """Process a seller application (approve or reject)"""
    application = get_object_or_404(SellerApplication, pk=application_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        admin_notes = request.POST.get('admin_notes', '')
        
        if action == 'approve':
            # Use atomic transaction to ensure data consistency
            with transaction.atomic():
                # Update application status
                application.status = 'approved'
                application.admin_notes = admin_notes
                application.processed_at = timezone.now()
                application.processed_by = request.user
                application.save()
                
                # Update user type and create profile
                user = application.user
                user.user_type = application.user_type
                user.save()
                
                if application.user_type == 'artist':
                    # Use select_for_update to prevent race conditions
                    try:
                        artist_profile = Artist.objects.select_for_update().get(user=user)
                        # Update existing profile
                        artist_profile.specialty = application.specialty
                        artist_profile.bio = application.bio
                        artist_profile.is_verified = True
                        artist_profile.save()
                    except Artist.DoesNotExist:
                        # Create new profile if it doesn't exist
                        Artist.objects.create(
                            user=user,
                            specialty=application.specialty,
                            bio=application.bio,
                            is_verified=True
                        )
                        
                elif application.user_type == 'store':
                    # Use select_for_update to prevent race conditions
                    try:
                        store_profile = Store.objects.select_for_update().get(user=user)
                        # Update existing profile
                        store_profile.store_name = application.store_name
                        store_profile.tax_id = application.tax_id
                        store_profile.has_physical_store = application.has_physical_store
                        store_profile.physical_address = application.physical_address
                        store_profile.is_verified = True
                        store_profile.save()
                    except Store.DoesNotExist:
                        # Create new profile if it doesn't exist
                        Store.objects.create(
                            user=user,
                            store_name=application.store_name,
                            tax_id=application.tax_id,
                            has_physical_store=application.has_physical_store,
                            physical_address=application.physical_address,
                            is_verified=True
                        )
            
            # Log activity
            AdminActivity.objects.create(
                admin=request.user,
                action='approve',
                description=f"Approved seller application #{application.id} for {application.name}",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            # Send notification to user
            notes_message = f"\n\nAdmin notes: {admin_notes}" if admin_notes else ""
            Notification.create_notification(
                user=user,
                title="Your seller application has been approved!",
                message=f"Congratulations! Your application to become a {application.user_type} has been approved.{notes_message}",
                notification_type="system",
                related_object=application
            )
            
            messages.success(request, f"Application #{application.id} has been approved.")
        
        elif action == 'reject':
            # Update application status
            application.status = 'rejected'
            application.admin_notes = admin_notes
            application.processed_at = timezone.now()
            application.processed_by = request.user
            application.save()
            
            # Log activity
            AdminActivity.objects.create(
                admin=request.user,
                action='reject',
                description=f"Rejected seller application #{application.id} for {application.name} - can reapply",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, f"Application #{application.id} has been rejected. User can reapply.")
        
        elif action == 'reject_permanently':
            # Update application status
            application.status = 'rejected_permanently'
            application.admin_notes = admin_notes or 'Application permanently rejected. User cannot reapply.'
            application.processed_at = timezone.now()
            application.processed_by = request.user
            application.save()
            
            # Log activity
            AdminActivity.objects.create(
                admin=request.user,
                action='reject',
                description=f"Permanently rejected seller application #{application.id} for {application.name}",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.warning(request, f"Application #{application.id} has been permanently rejected.")
            
            # Send notification to user
            notes_message = f"\n\nReason for rejection: {admin_notes}" if admin_notes else ""
            Notification.create_notification(
                user=application.user,
                title="Your seller application was not approved",
                message=f"We're sorry, but your application to become a {application.user_type} was not approved at this time.{notes_message}",
                notification_type="system",
                related_object=application
            )
            
            messages.success(request, f"Application #{application.id} has been rejected.")
        
        return redirect('admin_panel:seller_applications')
    
    context = {
        'application': application,
        'active_tab': 'applications'
    }
    
    return render(request, 'admin_panel/process_application.html', context)

# User Management
@login_required
@user_passes_test(is_admin)
def user_management(request):
    user_type = request.GET.get('type', 'all')
    status = request.GET.get('status', 'all')
    search_query = request.GET.get('q', '')
    
    users = User.objects.all()
    
    # Apply filters
    if user_type != 'all':
        users = users.filter(user_type=user_type)
    
    if status == 'active':
        users = users.filter(is_active=True)
    elif status == 'blocked':
        users = users.filter(is_active=False)
    
    if search_query:
        users = users.filter(
            Q(email__icontains=search_query) | 
            Q(first_name__icontains=search_query) | 
            Q(last_name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page', 1)
    users_page = paginator.get_page(page_number)
    
    context = {
        'users': users_page,
        'user_type': user_type,
        'status': status,
        'search_query': search_query,
        'active_tab': 'users'
    }
    
    return render(request, 'admin_panel/user_management.html', context)

# Product Management
@login_required
@user_passes_test(is_admin)
def product_management(request):
    category_id = request.GET.get('category', 'all')
    status = request.GET.get('status', 'all')
    search_query = request.GET.get('q', '')
    
    products = Product.objects.select_related('category', 'seller').all()
    
    # Apply filters
    if category_id != 'all':
        products = products.filter(category_id=category_id)
    
    if status == 'active':
        products = products.filter(is_active=True)
    elif status == 'inactive':
        products = products.filter(is_active=False)
    
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    # Get categories for filter dropdown
    categories = Category.objects.all()
    
    # Pagination
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page', 1)
    products_page = paginator.get_page(page_number)
    
    context = {
        'products': products_page,
        'categories': categories,
        'category_id': category_id,
        'status': status,
        'search_query': search_query,
        'active_tab': 'products'
    }
    
    return render(request, 'admin_panel/product_management.html', context)

# Order Management
@login_required
@user_passes_test(is_admin)
def order_management(request):
    status = request.GET.get('status', 'all')
    search_query = request.GET.get('q', '')
    
    orders = Order.objects.select_related('user').all()
    
    # Apply filters
    if status != 'all':
        orders = orders.filter(status=status)
    
    if search_query:
        orders = orders.filter(
            Q(id__icontains=search_query) | 
            Q(user__email__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page', 1)
    orders_page = paginator.get_page(page_number)
    
    context = {
        'orders': orders_page,
        'status': status,
        'search_query': search_query,
        'active_tab': 'orders'
    }
    
    return render(request, 'admin_panel/order_management.html', context)

# API Views for Admin Panel
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_stats_api(request):
    """API endpoint to get admin dashboard stats"""
    # User stats
    total_users = User.objects.count()
    customer_count = User.objects.filter(user_type='customer').count()
    artist_count = User.objects.filter(user_type='artist').count()
    store_count = User.objects.filter(user_type='store').count()
    
    # Order stats
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    completed_orders = Order.objects.filter(status='completed').count()
    
    # Application stats
    pending_applications = SellerApplication.objects.filter(status='pending').count()
    
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
        'applications': {
            'pending': pending_applications
        }
    }
    
    return Response(data)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def mark_notification_read(request, notification_id):
    """API endpoint to mark notification as read"""
    try:
        notification = AdminNotification.objects.get(id=notification_id)
        notification.is_read = True
        notification.save()
        return Response({'status': 'success'})
    except AdminNotification.DoesNotExist:
        return Response(
            {'error': 'Notification not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

# Reports
@login_required
@user_passes_test(is_admin)
def reports(request):
    """View for reports and analytics"""
    context = {
        'active_tab': 'reports'
    }
    
    return render(request, 'admin_panel/reports.html', context)

# Settings
@login_required
@user_passes_test(is_admin)
def settings(request):
    """View for admin panel settings"""
    context = {
        'active_tab': 'settings'
    }
    
    return render(request, 'admin_panel/settings.html', context)

@login_required
@user_passes_test(is_admin)
def activity_log(request):
    """View for the admin activity log page"""
    # Get filter parameters
    admin_id = request.GET.get('admin')
    action_type = request.GET.get('action')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Filter activities
    activities = AdminActivity.objects.all()
    
    if admin_id:
        activities = activities.filter(admin_id=admin_id)
    
    if action_type:
        activities = activities.filter(action=action_type)
    
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            activities = activities.filter(timestamp__date__gte=date_from)
        except ValueError:
            messages.error(request, 'Invalid date format for date_from. Use YYYY-MM-DD.')
    
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            activities = activities.filter(timestamp__date__lte=date_to)
        except ValueError:
            messages.error(request, 'Invalid date format for date_to. Use YYYY-MM-DD.')
    
    # Pagination
    paginator = Paginator(activities, 25)  # Show 25 activities per page
    page = request.GET.get('page')
    
    try:
        activities = paginator.page(page)
    except PageNotAnInteger:
        activities = paginator.page(1)
    except EmptyPage:
        activities = paginator.page(paginator.num_pages)
    
    # Get all admin users for the filter dropdown
    admins = User.objects.filter(is_staff=True)
    
    context = {
        'activities': activities,
        'admins': admins,
        'active_tab': 'activity_log'
    }
    
    return render(request, 'admin_panel/activity_log.html', context)

@login_required
@user_passes_test(is_admin)
def view_user_profile(request, user_id):
    """View for redirecting to the Django admin interface for user profiles"""
    user = get_object_or_404(User, id=user_id)
    
    # Log admin activity
    AdminActivity.objects.create(
        admin=request.user,
        action='other',
        description=f"Viewed profile of user: {user.email}",
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    # Determine which admin page to redirect to based on user type
    if user.user_type == 'customer':
        try:
            customer = user.customer_profile
            return redirect(f'/admin/custom_auth/customer/{customer.id}/change/')
        except AttributeError:
            messages.warning(request, f"Customer profile not found for user {user.email}")
        except Exception as e:
            messages.error(request, f"Error accessing customer profile: {str(e)}")
    elif user.user_type == 'artist':
        try:
            artist = user.artist_profile
            return redirect(f'/admin/custom_auth/artist/{artist.id}/change/')
        except AttributeError:
            messages.warning(request, f"Artist profile not found for user {user.email}")
        except Exception as e:
            messages.error(request, f"Error accessing artist profile: {str(e)}")
    elif user.user_type == 'store':
        try:
            store = user.store_profile
            return redirect(f'/admin/custom_auth/store/{store.id}/change/')
        except AttributeError:
            messages.warning(request, f"Store profile not found for user {user.email}")
        except Exception as e:
            messages.error(request, f"Error accessing store profile: {str(e)}")
    
    # Default to user admin page
    return redirect(f'/admin/custom_auth/user/{user.id}/change/')

@login_required
@user_passes_test(is_admin)
def view_order(request, order_id):
    """View for redirecting to the Django admin interface for order details"""
    order = get_object_or_404(Order, id=order_id)
    
    # Log admin activity
    AdminActivity.objects.create(
        admin=request.user,
        action='other',
        description=f"Viewed order #{order.id}",
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    # Redirect to the order admin page
    return redirect(f'/admin/orders/order/{order.id}/change/')

# Ads Control
@login_required
@user_passes_test(is_admin)
def ads_control(request):
    """View for ads control and management"""
    context = {
        'active_tab': 'ads_control'
    }
    
    return render(request, 'admin_panel/ads_control.html', context)

# Artists and Stores Management
@login_required
@user_passes_test(is_admin)
def artists_stores(request):
    """View for managing artists and stores that appear in homepage lists"""
    context = {
        'active_tab': 'artists_stores'
    }
    
    return render(request, 'admin_panel/artists_stores.html', context)

# Featured Products Management
@login_required
@user_passes_test(is_admin)
def featured_products(request):
    """View for managing featured products and offers that appear in homepage"""
    context = {
        'active_tab': 'featured_products'
    }
    
    return render(request, 'admin_panel/featured_products.html', context)

# Category Management
@login_required
@user_passes_test(is_admin)
def category_management(request):
    """View for managing categories and subcategories"""
    context = {
        'active_tab': 'categories'
    }
    
    return render(request, 'admin_panel/category_management.html', context)


@login_required
@user_passes_test(is_admin)
def attribute_management(request):
    """View for managing product attributes per category"""
    context = {
        'active_tab': 'attributes'
    }
    
    return render(request, 'admin_panel/attribute_management.html', context)

@login_required
@user_passes_test(is_admin)
def add_product_with_variants(request):
    """View for adding products with variants using the enhanced interface"""
    context = {
        'active_tab': 'products'
    }
    
    # Log admin activity
    AdminActivity.objects.create(
        admin=request.user,
        action='other',
        description="Accessed add product with variants page",
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    return render(request, 'admin_panel/add_product_with_variants.html', context)

@login_required
@user_passes_test(is_admin)
def edit_product_with_variants(request, product_id):
    """View for editing products with variants using the enhanced interface"""
    product = get_object_or_404(Product, id=product_id)
    
    context = {
        'active_tab': 'products',
        'product': product,
        'is_edit': True
    }
    
    # Log admin activity
    AdminActivity.objects.create(
        admin=request.user,
        action='other',
        description=f"Accessed edit product with variants page for product: {product.name}",
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    return render(request, 'admin_panel/edit_product_with_variants.html', context)

@login_required
@user_passes_test(is_admin)
def get_categories_json(request):
    """JSON endpoint to get categories for the admin panel"""
    try:
        from products.models import Category
        
        # Add logging for debugging
        print(f"Categories API called by user: {request.user}")
        print(f"Is user authenticated: {request.user.is_authenticated}")
        print(f"Is user staff: {request.user.is_staff}")
        print(f"Is user superuser: {request.user.is_superuser}")
        
        categories = Category.objects.filter(is_active=True).order_by('name')
        print(f"Found {categories.count()} categories")
        
        categories_data = [
            {
                'id': category.id,
                'name': category.name,
                'description': category.description,
            }
            for category in categories
        ]
        
        print(f"Returning categories data: {categories_data}")
        return JsonResponse(categories_data, safe=False)
        
    except Exception as e:
        print(f"Error in get_categories_json: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
def get_category_attributes_json(request, category_id):
    """JSON endpoint to get category attributes for the admin panel"""
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
        
        return JsonResponse(attributes_data, safe=False)
        
    except Category.DoesNotExist:
        return JsonResponse({'error': 'Category not found'}, status=404)
