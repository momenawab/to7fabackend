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

from custom_auth.models import User, Artist, Store, SellerApplication
from products.models import Product, Category, ProductImage
from orders.models import Order
from .models import AdminActivity, AdminNotification
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
    ).order_by('-created_at')[:5]
    
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
    """View for managing seller applications - pending, approved, rejected applications"""
    status_filter = request.GET.get('status', 'pending')
    seller_type_filter = request.GET.get('seller_type', 'all')
    search_query = request.GET.get('q', '')
    
    # Base queryset
    applications = SellerApplication.objects.select_related('user', 'reviewed_by')
    
    # Apply filters
    if status_filter != 'all':
        applications = applications.filter(status=status_filter)
    
    if seller_type_filter != 'all':
        applications = applications.filter(seller_type=seller_type_filter)
    
    if search_query:
        applications = applications.filter(
            Q(business_name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    applications = applications.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(applications, 10)
    page_number = request.GET.get('page', 1)
    applications_page = paginator.get_page(page_number)
    
    # Statistics
    stats = {
        'pending': SellerApplication.objects.filter(status='pending').count(),
        'approved': SellerApplication.objects.filter(status='approved').count(),
        'rejected': SellerApplication.objects.filter(status='rejected').count(),
        'total': SellerApplication.objects.count(),
    }
    
    context = {
        'applications': applications_page,
        'status_filter': status_filter,
        'seller_type_filter': seller_type_filter,
        'search_query': search_query,
        'stats': stats,
        'active_tab': 'applications'
    }
    
    return render(request, 'admin_panel/seller_applications.html', context)

# Seller Application Detail
@login_required
@user_passes_test(is_admin)
def seller_application_detail(request, application_id):
    """View detailed information about a seller application"""
    application = get_object_or_404(SellerApplication, id=application_id)
    
    # Process categories data
    category_names = []
    if application.categories:
        from products.models import Category
        category_ids = application.categories if isinstance(application.categories, list) else []
        category_names = Category.objects.filter(id__in=category_ids).values('id', 'name')
    
    # Process subcategories data - check if there's a subcategory model
    subcategories = []
    if application.subcategories:
        # For now, just display the subcategory data as is since we don't have a Subcategory model
        subcategories = application.subcategories if isinstance(application.subcategories, list) else []
    
    # Process shipping costs data - using Egyptian governorates
    shipping_costs_with_names = []
    shipping_stats = {'available': 0, 'total': 0}
    
    # List of Egyptian governorates (same as in custom_auth/views.py)
    governorates = [
        'Cairo', 'Alexandria', 'Giza', 'Qalyubia', 'Sharqia',
        'Dakahlia', 'Gharbia', 'Menoufia', 'Beheira', 'Kafr El Sheikh',
        'Damietta', 'Port Said', 'Ismailia', 'Suez', 'North Sinai',
        'South Sinai', 'Beni Suef', 'Fayoum', 'Minya', 'Assiut',
        'Sohag', 'Qena', 'Luxor', 'Aswan', 'Red Sea',
        'New Valley', 'Matruh'
    ]
    
    if application.shipping_costs:
        for index, governorate in enumerate(governorates, 1):
            # Shipping costs are stored with string indices (1, 2, 3, etc.)
            cost_data = application.shipping_costs.get(str(index), 0)
            
            if isinstance(cost_data, dict):
                is_available = cost_data.get('available', False)
                cost = cost_data.get('cost', 0) if is_available else 0
            else:
                # Handle case where cost_data is just a number
                is_available = cost_data > 0 if isinstance(cost_data, (int, float)) else False
                cost = cost_data if is_available else 0
            
            shipping_costs_with_names.append({
                'name': governorate,
                'cost': cost,
                'available': is_available
            })
            
            shipping_stats['total'] += 1
            if is_available:
                shipping_stats['available'] += 1
    
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
        rejection_reason = request.POST.get('rejection_reason', '')
        
        if action == 'approve':
            # Use atomic transaction to ensure data consistency
            with transaction.atomic():
                # Update application status
                application.status = 'approved'
                application.admin_notes = admin_notes
                application.reviewed_at = timezone.now()
                application.reviewed_by = request.user
                application.save()
                
                # Update user type and create profile
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
                        artist_profile.save()
                    except Artist.DoesNotExist:
                        # Create new profile if it doesn't exist
                        Artist.objects.create(
                            user=user,
                            specialty=application.specialty or '',
                            bio=application.description,
                            social_media=application.social_media,
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
                            is_verified=True
                        )
            
            # Log activity
            AdminActivity.objects.create(
                admin=request.user,
                action='approve',
                description=f"Approved seller application #{application.id} for {application.business_name}",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            # Send notification to user
            notes_message = f"\n\nAdmin notes: {admin_notes}" if admin_notes else ""
            Notification.create_notification(
                user=user,
                title="Your seller application has been approved!",
                message=f"Congratulations! Your application to become a {application.seller_type} has been approved.{notes_message}",
                notification_type="system",
                related_object=application
            )
            
            messages.success(request, f"Application #{application.id} has been approved.")
        
        elif action == 'reject':
            # Update application status
            application.status = 'rejected'
            application.admin_notes = admin_notes
            application.rejection_reason = rejection_reason
            application.reviewed_at = timezone.now()
            application.reviewed_by = request.user
            application.save()
            
            # Log activity
            AdminActivity.objects.create(
                admin=request.user,
                action='reject',
                description=f"Rejected seller application #{application.id} for {application.business_name}",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            # Send notification to user
            rejection_message = f"Reason: {rejection_reason}" if rejection_reason else ""
            notes_message = f"\n\nAdmin notes: {admin_notes}" if admin_notes else ""
            Notification.create_notification(
                user=application.user,
                title="Your seller application has been rejected",
                message=f"Unfortunately, your application to become a {application.seller_type} has been rejected. {rejection_message}{notes_message}",
                notification_type="system",
                related_object=application
            )
            
            messages.success(request, f"Application #{application.id} has been rejected.")
        
        elif action == 'reject_permanently':
            # Update application status
            application.status = 'rejected_permanently'
            application.admin_notes = admin_notes or 'Application permanently rejected. User cannot reapply.'
            application.reviewed_at = timezone.now()
            application.reviewed_by = request.user
            application.save()
            
            # Log activity
            AdminActivity.objects.create(
                admin=request.user,
                action='reject',
                description=f"Permanently rejected seller application #{application.id} for {application.business_name}",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.warning(request, f"Application #{application.id} has been permanently rejected.")
            
            # Send notification to user
            notes_message = f"\n\nReason for rejection: {admin_notes}" if admin_notes else ""
            Notification.create_notification(
                user=application.user,
                title="Your seller application was not approved",
                message=f"We're sorry, but your application to become a {application.seller_type} was not approved at this time.{notes_message}",
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
    
    users = User.objects.all().order_by('-date_joined')
    
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
    
    products = Product.objects.select_related('category', 'seller').all().order_by('-created_at')
    
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

# Product Approval Management
@login_required
@user_passes_test(is_admin)
def product_approval(request):
    """View for managing product approvals - pending, approved, rejected products"""
    status_filter = request.GET.get('status', 'pending')
    search_query = request.GET.get('q', '')
    category_id = request.GET.get('category', 'all')
    
    # Get products based on approval status
    if status_filter == 'pending':
        products = Product.objects.filter(is_active=False).select_related('category', 'seller').order_by('-created_at')
    elif status_filter == 'approved':
        products = Product.objects.filter(is_active=True).select_related('category', 'seller').order_by('-created_at')
    else:  # all
        products = Product.objects.all().select_related('category', 'seller').order_by('-created_at')
    
    # Apply filters
    if category_id != 'all':
        products = products.filter(category_id=category_id)
    
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(seller__email__icontains=search_query)
        )
    
    # Get categories for filter dropdown
    categories = Category.objects.all()
    
    # Get statistics
    stats = {
        'pending': Product.objects.filter(is_active=False).count(),
        'approved': Product.objects.filter(is_active=True).count(),
        'total': Product.objects.count(),
    }
    
    # Pagination
    paginator = Paginator(products, 15)
    page_number = request.GET.get('page', 1)
    products_page = paginator.get_page(page_number)
    
    context = {
        'products': products_page,
        'categories': categories,
        'category_id': category_id,
        'status_filter': status_filter,
        'search_query': search_query,
        'stats': stats,
        'active_tab': 'product_approval'
    }
    
    return render(request, 'admin_panel/product_approval.html', context)

@login_required
@user_passes_test(is_admin)
@require_POST
def process_product_approval(request, product_id):
    """Process product approval - approve, reject, or edit"""
    product = get_object_or_404(Product, id=product_id)
    action = request.POST.get('action')
    admin_notes = request.POST.get('admin_notes', '')
    
    if action == 'approve':
        product.is_active = True
        product.save()
        
        # Create notification for seller
        Notification.objects.create(
            user=product.seller,
            title='تم قبول المنتج',
            message=f'تم قبول منتجك "{product.name}" ونشره في المتجر.',
            notification_type='product_approved'
        )
        
        # Log admin activity
        AdminActivity.objects.create(
            admin=request.user,
            action='approve_product',
            description=f'Approved product "{product.name}" (ID: {product.id}) by {product.seller.email}',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        messages.success(request, f'تم قبول المنتج "{product.name}" بنجاح')
        
    elif action == 'reject':
        rejection_reason = request.POST.get('rejection_reason', 'لم يتم تحديد السبب')
        
        # For now, we'll keep the product but mark it as inactive
        # In the future, you might want to add a rejection reason field to the Product model
        product.is_active = False
        product.save()
        
        # Create notification for seller
        Notification.objects.create(
            user=product.seller,
            title='تم رفض المنتج',
            message=f'تم رفض منتجك "{product.name}". السبب: {rejection_reason}',
            notification_type='product_rejected'
        )
        
        # Log admin activity
        AdminActivity.objects.create(
            admin=request.user,
            action='reject_product',
            description=f'Rejected product "{product.name}" (ID: {product.id}) by {product.seller.email}. Reason: {rejection_reason}',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        messages.success(request, f'تم رفض المنتج "{product.name}" بنجاح')
        
    elif action == 'edit':
        # Redirect to edit page
        return redirect('admin_panel:edit_product_with_variants', product_id=product.id)
    
    return redirect('admin_panel:product_approval')

# Order Management
@login_required
@user_passes_test(is_admin)
def order_management(request):
    status = request.GET.get('status', 'all')
    search_query = request.GET.get('q', '')
    
    orders = Order.objects.select_related('user').all().order_by('-created_at')
    
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
    activities = AdminActivity.objects.all().order_by('-timestamp')
    
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


@login_required
@user_passes_test(is_admin)
def variant_management(request):
    """Variant management page for categories"""
    from products.models import Category, CategoryVariantType, CategoryVariantOption
    
    # Get all categories with their variant counts
    categories = Category.objects.annotate(
        variant_types_count=Count('variant_types'),
        total_options_count=Count('variant_types__options')
    ).order_by('name')
    
    # Get categories with variants for summary
    categories_with_variants = categories.filter(variant_types_count__gt=0)
    total_variant_types = CategoryVariantType.objects.count()
    total_variant_options = CategoryVariantOption.objects.count()
    
    # Log admin activity
    AdminActivity.objects.create(
        admin=request.user,
        action='other',
        description=f'Viewed variant management page'
    )
    
    context = {
        'active_tab': 'variants',
        'categories': categories,
        'categories_with_variants': categories_with_variants,
        'stats': {
            'total_categories': categories.count(),
            'categories_with_variants': categories_with_variants.count(),
            'total_variant_types': total_variant_types,
            'total_variant_options': total_variant_options,
        }
    }
    
    return render(request, 'admin_panel/variant_management.html', context)


@login_required
@user_passes_test(is_admin)
@require_POST
def create_variant_type(request):
    """Create a new variant type for a category"""
    from products.models import Category, CategoryVariantType
    
    try:
        category_id = request.POST.get('category_id')
        name = request.POST.get('name', '').strip()
        is_required = request.POST.get('is_required') == 'true'
        
        if not category_id or not name:
            return JsonResponse({'success': False, 'error': 'Category ID and name are required'})
        
        category = get_object_or_404(Category, id=category_id)
        
        # Check if variant type already exists for this category
        if CategoryVariantType.objects.filter(category=category, name=name).exists():
            return JsonResponse({'success': False, 'error': f'Variant type "{name}" already exists for this category'})
        
        # Create the variant type
        variant_type = CategoryVariantType.objects.create(
            category=category,
            name=name,
            is_required=is_required
        )
        
        # Log admin activity
        AdminActivity.objects.create(
            admin=request.user,
            action='create',
            description=f'Created variant type "{name}" for category "{category.name}"'
        )
        
        return JsonResponse({
            'success': True,
            'variant_type': {
                'id': variant_type.id,
                'name': variant_type.name,
                'is_required': variant_type.is_required,
                'category_name': category.name
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@user_passes_test(is_admin)
@require_POST
def create_variant_option(request):
    """Create a new variant option for a variant type"""
    from products.models import CategoryVariantType, CategoryVariantOption
    
    try:
        variant_type_id = request.POST.get('variant_type_id')
        value = request.POST.get('value', '').strip()
        extra_price = request.POST.get('extra_price', '0')
        is_active = request.POST.get('is_active', 'true') == 'true'
        
        if not variant_type_id or not value:
            return JsonResponse({'success': False, 'error': 'Variant type ID and value are required'})
        
        variant_type = get_object_or_404(CategoryVariantType, id=variant_type_id)
        
        # Check if option already exists for this variant type
        if CategoryVariantOption.objects.filter(variant_type=variant_type, value=value).exists():
            return JsonResponse({'success': False, 'error': f'Option "{value}" already exists for this variant type'})
        
        # Convert extra_price to float
        try:
            extra_price = float(extra_price)
        except (ValueError, TypeError):
            extra_price = 0.0
        
        # Create the variant option
        variant_option = CategoryVariantOption.objects.create(
            variant_type=variant_type,
            value=value,
            extra_price=extra_price,
            is_active=is_active
        )
        
        # Log admin activity
        AdminActivity.objects.create(
            admin=request.user,
            action='create',
            description=f'Created variant option "{value}" for variant type "{variant_type.name}" in category "{variant_type.category.name}"'
        )
        
        return JsonResponse({
            'success': True,
            'variant_option': {
                'id': variant_option.id,
                'value': variant_option.value,
                'extra_price': float(variant_option.extra_price),
                'is_active': variant_option.is_active,
                'variant_type_name': variant_type.name
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@user_passes_test(is_admin)
def get_category_variants_json(request, category_id):
    """JSON endpoint to get category variants for the admin panel"""
    from products.models import Category, CategoryVariantType
    
    try:
        category = get_object_or_404(Category, id=category_id)
        
        variant_types = CategoryVariantType.objects.filter(category=category).prefetch_related('options')
        
        variants_data = []
        for variant_type in variant_types:
            options_data = []
            for option in variant_type.options.all().order_by('id'):
                options_data.append({
                    'id': option.id,
                    'value': option.value,
                    'extra_price': float(option.extra_price),
                    'is_active': option.is_active
                })
            
            variants_data.append({
                'id': variant_type.id,
                'name': variant_type.name,
                'is_required': variant_type.is_required,
                'options': options_data
            })
        
        return JsonResponse({'variants': variants_data})
        
    except Category.DoesNotExist:
        return JsonResponse({'error': 'Category not found'}, status=404)


@login_required
@user_passes_test(is_admin)
@require_POST
def delete_variant_type(request):
    """Delete a variant type and all its options"""
    from products.models import CategoryVariantType
    
    try:
        variant_type_id = request.POST.get('variant_type_id')
        
        if not variant_type_id:
            return JsonResponse({'success': False, 'error': 'Variant type ID is required'})
        
        variant_type = get_object_or_404(CategoryVariantType, id=variant_type_id)
        category_name = variant_type.category.name
        variant_name = variant_type.name
        
        # Delete the variant type (this will cascade delete all options)
        variant_type.delete()
        
        # Log admin activity
        AdminActivity.objects.create(
            admin=request.user,
            action='delete',
            description=f'Deleted variant type "{variant_name}" from category "{category_name}"'
        )
        
        return JsonResponse({'success': True, 'message': f'Variant type "{variant_name}" deleted successfully'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@user_passes_test(is_admin)
@require_POST
def delete_variant_option(request):
    """Delete a variant option"""
    from products.models import CategoryVariantOption
    
    try:
        option_id = request.POST.get('option_id')
        
        if not option_id:
            return JsonResponse({'success': False, 'error': 'Option ID is required'})
        
        option = get_object_or_404(CategoryVariantOption, id=option_id)
        variant_type_name = option.variant_type.name
        category_name = option.variant_type.category.name
        option_value = option.value
        
        # Delete the option
        option.delete()
        
        # Log admin activity
        AdminActivity.objects.create(
            admin=request.user,
            action='delete',
            description=f'Deleted variant option "{option_value}" from variant type "{variant_type_name}" in category "{category_name}"'
        )
        
        return JsonResponse({'success': True, 'message': f'Variant option "{option_value}" deleted successfully'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
