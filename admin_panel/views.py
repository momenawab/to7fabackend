from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
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
from .decorators import admin_required, has_admin_permission
from notifications.models import Notification
from support.models import SupportTicket, SupportCategory, SupportMessage

# Helper function to check if user is admin
def is_admin(user):
    # Check if user is staff or superuser
    if user.is_staff or user.is_superuser:
        return True
    
    # Check if user has admin profile
    try:
        admin_profile = user.admin_profile
        return admin_profile.is_active and admin_profile.can_login
    except AttributeError:
        return False

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
@admin_required('seller_applications')
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
@admin_required('users_management')
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
@admin_required('products_management')
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
@admin_required('product_approval')
def product_approval(request):
    """View for managing product approvals - pending, approved, rejected products"""
    status_filter = request.GET.get('status', 'pending')
    search_query = request.GET.get('q', '')
    category_id = request.GET.get('category', 'all')

    # Get products based on approval status
    if status_filter == 'pending':
        products = Product.objects.filter(approval_status='pending').select_related('category', 'seller').order_by('-created_at')
    elif status_filter == 'approved':
        products = Product.objects.filter(approval_status='approved').select_related('category', 'seller').order_by('-created_at')
    elif status_filter == 'rejected':
        products = Product.objects.filter(approval_status='rejected').select_related('category', 'seller').order_by('-created_at')
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
        'pending': Product.objects.filter(approval_status='pending').count(),
        'approved': Product.objects.filter(approval_status='approved').count(),
        'rejected': Product.objects.filter(approval_status='rejected').count(),
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
        product.approval_status = 'approved'
        product.is_active = True
        product.rejection_reason = None  # Clear any previous rejection reason
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

        # Mark product as rejected with reason
        product.approval_status = 'rejected'
        product.is_active = False
        product.rejection_reason = rejection_reason
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

    elif action == 'approve_featured':
        product.is_featured = True
        product.featured_request_pending = False
        product.save()
        
        # Create featured product entry
        from products.models import FeaturedProduct
        FeaturedProduct.objects.get_or_create(
            product=product,
            defaults={'reason': 'Approved by admin from seller request'}
        )

        # Create notification for seller
        Notification.objects.create(
            user=product.seller,
            title='تم قبول طلب المنتج المميز',
            message=f'تم قبول طلبك لجعل منتج "{product.name}" مميزاً.',
            notification_type='featured_approved'
        )

        # Log admin activity
        AdminActivity.objects.create(
            admin=request.user,
            action='approve_featured_request',
            description=f'Approved featured request for product "{product.name}" (ID: {product.id})',
            ip_address=request.META.get('REMOTE_ADDR')
        )

        messages.success(request, f'تم قبول طلب المنتج المميز لـ "{product.name}"')

    elif action == 'reject_featured':
        product.featured_request_pending = False
        product.save()

        # Create notification for seller
        Notification.objects.create(
            user=product.seller,
            title='تم رفض طلب المنتج المميز',
            message=f'تم رفض طلبك لجعل منتج "{product.name}" مميزاً.',
            notification_type='featured_rejected'
        )

        # Log admin activity
        AdminActivity.objects.create(
            admin=request.user,
            action='reject_featured_request',
            description=f'Rejected featured request for product "{product.name}" (ID: {product.id})',
            ip_address=request.META.get('REMOTE_ADDR')
        )

        messages.success(request, f'تم رفض طلب المنتج المميز لـ "{product.name}"')

    elif action == 'approve_offers':
        product.offers_request_pending = False
        product.save()
        
        # Create product offer entry
        from products.models import ProductOffer
        from datetime import timedelta
        from django.utils import timezone
        
        # Create a default offer (you can customize this)
        ProductOffer.objects.get_or_create(
            product=product,
            defaults={
                'discount_percentage': 10,  # Default 10% discount
                'start_date': timezone.now(),
                'end_date': timezone.now() + timedelta(days=30),
                'description': 'Latest offer approved by admin'
            }
        )

        # Create notification for seller
        Notification.objects.create(
            user=product.seller,
            title='تم قبول طلب العروض الحديثة',
            message=f'تم قبول طلبك لإضافة منتج "{product.name}" إلى العروض الحديثة.',
            notification_type='offers_approved'
        )

        # Log admin activity
        AdminActivity.objects.create(
            admin=request.user,
            action='approve_offers_request',
            description=f'Approved latest offers request for product "{product.name}" (ID: {product.id})',
            ip_address=request.META.get('REMOTE_ADDR')
        )

        messages.success(request, f'تم قبول طلب العروض الحديثة لـ "{product.name}"')

    elif action == 'reject_offers':
        product.offers_request_pending = False
        product.save()

        # Create notification for seller
        Notification.objects.create(
            user=product.seller,
            title='تم رفض طلب العروض الحديثة',
            message=f'تم رفض طلبك لإضافة منتج "{product.name}" إلى العروض الحديثة.',
            notification_type='offers_rejected'
        )

        # Log admin activity
        AdminActivity.objects.create(
            admin=request.user,
            action='reject_offers_request',
            description=f'Rejected latest offers request for product "{product.name}" (ID: {product.id})',
            ip_address=request.META.get('REMOTE_ADDR')
        )

        messages.success(request, f'تم رفض طلب العروض الحديثة لـ "{product.name}"')

    elif action == 'edit':
        # Redirect to edit page
        return redirect('admin_panel:edit_product_with_variants', product_id=product.id)

    return redirect('admin_panel:product_approval')

@login_required
@user_passes_test(is_admin)
def product_detail_api(request, product_id):
    """API endpoint to get detailed product information for the approval modal"""
    try:
        product = get_object_or_404(Product, id=product_id)
        
        # Get product images
        product_images = []
        for img in product.images.all():
            product_images.append({
                'image': img.image.url if img.image else '',
                'is_primary': img.is_primary
            })
        
        # Get product variants
        product_variants = []
        for variant in product.selected_variants.filter(is_active=True):
            product_variants.append({
                'variant_type': variant.variant_type_name,
                'value': variant.variant_option_value,
                'stock_count': variant.stock_count,
                'final_price': str(variant.final_price),
                'price_adjustment': str(variant.price_adjustment)
            })
        
        # Get seller information
        seller_info = {
            'email': product.seller.email,
            'user_type': product.seller.user_type,
            'name': None,
            'store_name': None,
            'date_joined': product.seller.date_joined.isoformat()
        }
        
        # Add seller-specific information
        if product.seller.user_type == 'artist':
            try:
                seller_info['name'] = f"{product.seller.first_name} {product.seller.last_name}".strip()
            except:
                pass
        elif product.seller.user_type == 'store':
            try:
                seller_info['store_name'] = product.seller.store_profile.store_name
            except:
                pass
        
        # Prepare response data
        product_data = {
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'base_price': str(product.base_price),
            'stock': product.stock,
            'category': product.category.name,
            'approval_status': product.approval_status,
            'rejection_reason': product.rejection_reason,
            'is_featured': product.is_featured,
            'is_active': product.is_active,
            'featured_request_pending': product.featured_request_pending,
            'offers_request_pending': product.offers_request_pending,
            'featured_requested_at': product.featured_requested_at.isoformat() if product.featured_requested_at else None,
            'offers_requested_at': product.offers_requested_at.isoformat() if product.offers_requested_at else None,
            'created_at': product.created_at.isoformat(),
            'updated_at': product.updated_at.isoformat(),
            'images': product_images,
            'variants': product_variants,
            'seller': seller_info
        }
        
        return JsonResponse({
            'success': True,
            'product': product_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error loading product details: {str(e)}'
        }, status=500)

# Order Management
@admin_required('orders_view')
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
@admin_required('analytics_view')
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
@admin_required('advertising_management')
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
@admin_required('categories_management')
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
def subcategory_sections_management(request):
    """View for managing subcategory sections display control"""
    from products.models import SubcategorySectionControl, Category
    
    # Get all subcategories 
    subcategories = Category.objects.filter(
        parent__isnull=False, is_active=True
    ).select_related('parent')
    
    # Get all existing section controls
    existing_controls = {}
    for control in SubcategorySectionControl.objects.select_related('subcategory'):
        existing_controls[control.subcategory.id] = control
    
    # Group by parent category
    categories_data = {}
    for subcategory in subcategories:
        parent = subcategory.parent
        if parent.id not in categories_data:
            categories_data[parent.id] = {
                'parent': parent,
                'subcategories': []
            }
        
        # Get section control if it exists
        section_control = existing_controls.get(subcategory.id, None)
            
        categories_data[parent.id]['subcategories'].append({
            'subcategory': subcategory,
            'section_control': section_control
        })
    
    # Log admin activity
    AdminActivity.objects.create(
        admin=request.user,
        action='VIEW',
        description='Viewed subcategory sections management'
    )
    
    context = {
        'active_tab': 'subcategory_sections',
        'categories_data': list(categories_data.values())
    }

    return render(request, 'admin_panel/subcategory_sections_management.html', context)

# API endpoints for subcategory sections management

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def create_subcategory_section_api(request):
    """API endpoint to create a new subcategory section control"""
    try:
        from products.models import SubcategorySectionControl, Category
        
        subcategory_id = request.POST.get('subcategory_id')
        is_section_enabled = request.POST.get('is_section_enabled') == 'true'
        max_products_to_show = int(request.POST.get('max_products_to_show', 4))
        section_priority = int(request.POST.get('section_priority', 0))
        
        # Validate subcategory exists and is actually a subcategory
        try:
            subcategory = Category.objects.get(id=subcategory_id, parent__isnull=False)
        except Category.DoesNotExist:
            return JsonResponse({'error': 'Invalid subcategory'}, status=400)
        
        # Check if section control already exists
        if SubcategorySectionControl.objects.filter(subcategory=subcategory).exists():
            return JsonResponse({'error': 'Section control already exists for this subcategory'}, status=400)
        
        # Create the section control
        section_control = SubcategorySectionControl.objects.create(
            subcategory=subcategory,
            is_section_enabled=is_section_enabled,
            max_products_to_show=max_products_to_show,
            section_priority=section_priority
        )
        
        # Log admin activity
        AdminActivity.objects.create(
            admin=request.user,
            action='create',
            description=f"Created section control for subcategory '{subcategory.name}'",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Section control created for {subcategory.name}',
            'section_id': section_control.id
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def toggle_subcategory_section_api(request, section_id):
    """API endpoint to toggle (pause/resume) a subcategory section"""
    try:
        from products.models import SubcategorySectionControl
        
        print(f"DEBUG: Toggle API called with section_id: {section_id}")
        print(f"DEBUG: Request method: {request.method}")
        print(f"DEBUG: Request user: {request.user}")
        
        section_control = SubcategorySectionControl.objects.get(id=section_id)
        print(f"DEBUG: Found section control: {section_control}")
        
        # Toggle the enabled state
        section_control.is_section_enabled = not section_control.is_section_enabled
        section_control.save()
        
        # Log admin activity
        action = "enabled" if section_control.is_section_enabled else "disabled"
        AdminActivity.objects.create(
            admin=request.user,
            action='update',
            description=f"{action.capitalize()} section for subcategory '{section_control.subcategory.name}'",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return JsonResponse({
            'success': True,
            'is_enabled': section_control.is_section_enabled,
            'message': f'Section {action} successfully'
        })
        
    except SubcategorySectionControl.DoesNotExist:
        return JsonResponse({'error': 'Section control not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def update_subcategory_section_api(request, section_id):
    """API endpoint to update subcategory section settings"""
    try:
        from products.models import SubcategorySectionControl
        import json
        
        section_control = SubcategorySectionControl.objects.get(id=section_id)
        
        # Parse JSON data
        data = json.loads(request.body)
        
        # Update fields if provided
        if 'max_products_to_show' in data:
            section_control.max_products_to_show = int(data['max_products_to_show'])
        if 'section_priority' in data:
            section_control.section_priority = int(data['section_priority'])
        if 'is_section_enabled' in data:
            section_control.is_section_enabled = bool(data['is_section_enabled'])
            
        section_control.save()
        
        # Log admin activity
        AdminActivity.objects.create(
            admin=request.user,
            action='update',
            description=f"Updated section settings for subcategory '{section_control.subcategory.name}'",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Section updated successfully'
        })
        
    except SubcategorySectionControl.DoesNotExist:
        return JsonResponse({'error': 'Section control not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["DELETE"])
def delete_subcategory_section_api(request, section_id):
    """API endpoint to delete subcategory section control"""
    try:
        from products.models import SubcategorySectionControl
        
        section_control = SubcategorySectionControl.objects.get(id=section_id)
        subcategory_name = section_control.subcategory.name
        
        section_control.delete()
        
        # Log admin activity
        AdminActivity.objects.create(
            admin=request.user,
            action='delete',
            description=f"Deleted section control for subcategory '{subcategory_name}'",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Section control for {subcategory_name} deleted successfully'
        })
        
    except SubcategorySectionControl.DoesNotExist:
        return JsonResponse({'error': 'Section control not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

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

        # Get categories sorted by hierarchy: parent categories first, then subcategories
        parent_categories = Category.objects.filter(is_active=True, parent__isnull=True).order_by('name')
        subcategories = Category.objects.filter(is_active=True, parent__isnull=False).select_related('parent').order_by('parent__name', 'name')
        
        print(f"Found {parent_categories.count()} parent categories and {subcategories.count()} subcategories")

        # Build hierarchical category data
        categories_data = []
        
        # Add parent categories first
        for category in parent_categories:
            categories_data.append({
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'parent_id': None,
                'is_parent': True
            })
        
        # Add subcategories grouped under their parents
        for category in subcategories:
            categories_data.append({
                'id': category.id,
                'name': f"  └─ {category.name}",  # Indent subcategories visually
                'description': category.description,
                'parent_id': category.parent.id,
                'is_parent': False,
                'parent_name': category.parent.name
            })

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


@admin_required('variants_management')
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
        priority = int(request.POST.get('priority', 999))

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
            is_required=is_required,
            priority=priority
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
    """JSON endpoint to get category variants for the admin panel, including inherited variants from parent categories"""
    from products.models import Category, CategoryVariantType

    try:
        category = get_object_or_404(Category, id=category_id)

        # Collect all categories in the hierarchy (current + all parents)
        categories_to_check = [category]
        current_cat = category
        while current_cat.parent is not None:
            categories_to_check.append(current_cat.parent)
            current_cat = current_cat.parent

        # Get variant types from all categories in the hierarchy
        all_variant_types = CategoryVariantType.objects.filter(
            category__in=categories_to_check
        ).prefetch_related('options').order_by('priority', 'name')

        # Group variants by name to merge options from different levels
        variants_by_name = {}
        for variant_type in all_variant_types:
            variant_name = variant_type.name

            if variant_name not in variants_by_name:
                variants_by_name[variant_name] = {
                    'id': variant_type.id,  # Use the most specific (deepest) variant type ID
                    'name': variant_name,
                    'is_required': variant_type.is_required,
                    'priority': variant_type.priority,
                    'options': [],
                    'category_source': variant_type.category.name
                }

            # Add options from this variant type, avoiding duplicates by value
            existing_option_values = {opt['value'] for opt in variants_by_name[variant_name]['options']}

            for option in variant_type.options.filter(is_active=True):
                if option.value not in existing_option_values:
                    variants_by_name[variant_name]['options'].append({
                        'id': option.id,
                        'value': option.value,
                        'extra_price': float(option.extra_price),
                        'is_active': option.is_active,
                        'variant_type_id': variant_type.id,
                        'category_source': variant_type.category.name
                    })
                    existing_option_values.add(option.value)

        # Convert to list and sort
        variants_data = list(variants_by_name.values())
        variants_data.sort(key=lambda x: x['name'])

        # Sort options within each variant type
        for variant in variants_data:
            variant['options'].sort(key=lambda x: x['value'])

        return JsonResponse({
            'success': True,
            'variants': variants_data,
            'category_hierarchy': [cat.name for cat in reversed(categories_to_check)]
        })

    except Category.DoesNotExist:
        return JsonResponse({'error': 'Category not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


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
def update_variant_priority(request):
    """Update the priority of a variant type"""
    from products.models import CategoryVariantType

    try:
        variant_type_id = request.POST.get('variant_type_id')
        priority = request.POST.get('priority')

        if not variant_type_id or priority is None:
            return JsonResponse({'success': False, 'error': 'Variant type ID and priority are required'})

        try:
            priority = int(priority)
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Priority must be a valid number'})

        if priority < 1 or priority > 999:
            return JsonResponse({'success': False, 'error': 'Priority must be between 1 and 999'})

        variant_type = get_object_or_404(CategoryVariantType, id=variant_type_id)
        old_priority = variant_type.priority
        variant_type.priority = priority
        variant_type.save()

        # Log admin activity
        AdminActivity.objects.create(
            admin=request.user,
            action='update',
            description=f'Updated priority for variant type "{variant_type.name}" from {old_priority} to {priority}'
        )
        
        return JsonResponse({
            'success': True, 
            'message': f'Priority updated successfully',
            'variant_type': {
                'id': variant_type.id,
                'name': variant_type.name,
                'priority': variant_type.priority,
                'is_required': variant_type.is_required
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# Support Tickets Management
@admin_required('support_tickets')
def support_tickets(request):
    """View for managing support tickets"""
    status_filter = request.GET.get('status', 'all')
    order_filter = request.GET.get('order', 'all')
    category_filter = request.GET.get('category', 'all')
    assigned_filter = request.GET.get('assigned', 'all')
    search_query = request.GET.get('q', '')
    
    # Base queryset
    tickets = SupportTicket.objects.select_related('user', 'category', 'assigned_to').prefetch_related('messages')
    
    # Apply filters
    if status_filter != 'all':
        tickets = tickets.filter(status=status_filter)
    
    if order_filter != 'all':
        if order_filter == 'with_order':
            tickets = tickets.exclude(order_id__isnull=True).exclude(order_id='')
        elif order_filter == 'no_order':
            tickets = tickets.filter(Q(order_id__isnull=True) | Q(order_id=''))
    
    if category_filter != 'all':
        tickets = tickets.filter(category_id=category_filter)
    
    if assigned_filter != 'all':
        if assigned_filter == 'unassigned':
            tickets = tickets.filter(assigned_to__isnull=True)
        else:
            tickets = tickets.filter(assigned_to_id=assigned_filter)
    
    if search_query:
        tickets = tickets.filter(
            Q(ticket_id__icontains=search_query) |
            Q(subject__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(order_id__icontains=search_query)
        )
    
    tickets = tickets.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(tickets, 15)
    page_number = request.GET.get('page', 1)
    tickets_page = paginator.get_page(page_number)
    
    # Get categories and staff users for filters
    categories = SupportCategory.objects.filter(is_active=True).order_by('name')
    staff_users = User.objects.filter(is_staff=True).order_by('first_name', 'last_name')
    
    # Statistics
    stats = {
        'total': SupportTicket.objects.count(),
        'open': SupportTicket.objects.filter(status='open').count(),
        'in_progress': SupportTicket.objects.filter(status='in_progress').count(),
        'waiting_customer': SupportTicket.objects.filter(status='waiting_customer').count(),
        'resolved': SupportTicket.objects.filter(status='resolved').count(),
        'closed': SupportTicket.objects.filter(status='closed').count(),
        'unassigned': SupportTicket.objects.filter(assigned_to__isnull=True).count(),
        'overdue': len([t for t in SupportTicket.objects.filter(status__in=['open', 'in_progress']) if t.is_overdue]),
    }
    
    context = {
        'tickets': tickets_page,
        'categories': categories,
        'staff_users': staff_users,
        'status_filter': status_filter,
        'order_filter': order_filter,
        'category_filter': category_filter,
        'assigned_filter': assigned_filter,
        'search_query': search_query,
        'stats': stats,
        'active_tab': 'support'
    }
    
    return render(request, 'admin_panel/support_tickets.html', context)


@login_required
@user_passes_test(is_admin)
def support_ticket_detail(request, ticket_id):
    """View detailed information about a support ticket"""
    ticket = get_object_or_404(
        SupportTicket.objects.select_related('user', 'category', 'assigned_to').prefetch_related(
            'messages__sender', 'attachments'
        ),
        ticket_id=ticket_id
    )
    
    # Get all staff users for assignment dropdown
    staff_users = User.objects.filter(is_staff=True).order_by('first_name', 'last_name')
    
    context = {
        'ticket': ticket,
        'staff_users': staff_users,
        'active_tab': 'support'
    }
    
    return render(request, 'admin_panel/support_ticket_detail.html', context)


@login_required
@user_passes_test(is_admin)
@require_POST
def update_support_ticket(request, ticket_id):
    """Update support ticket status, priority, assignment etc."""
    ticket = get_object_or_404(SupportTicket, ticket_id=ticket_id)
    
    action = request.POST.get('action')
    
    if action == 'update_status':
        new_status = request.POST.get('status')
        if new_status in ['open', 'in_progress', 'waiting_customer', 'resolved', 'closed']:
            old_status = ticket.status
            ticket.status = new_status
            
            # Update timestamps based on status
            if new_status == 'resolved' and old_status != 'resolved':
                ticket.resolved_at = timezone.now()
            elif new_status == 'closed' and old_status != 'closed':
                ticket.closed_at = timezone.now()
            
            ticket.save()
            messages.success(request, f'Ticket status updated to {ticket.get_status_display()}')
            
            # Log activity
            AdminActivity.objects.create(
                admin=request.user,
                action='update',
                description=f'Updated ticket #{ticket.ticket_id} status from {old_status} to {new_status}',
                ip_address=request.META.get('REMOTE_ADDR')
            )
    
    elif action == 'update_priority':
        new_priority = request.POST.get('priority')
        if new_priority in ['low', 'normal', 'high', 'urgent']:
            old_priority = ticket.priority
            ticket.priority = new_priority
            ticket.save()
            messages.success(request, f'Ticket priority updated to {ticket.get_priority_display()}')
            
            # Log activity
            AdminActivity.objects.create(
                admin=request.user,
                action='update',
                description=f'Updated ticket #{ticket.ticket_id} priority from {old_priority} to {new_priority}',
                ip_address=request.META.get('REMOTE_ADDR')
            )
    
    elif action == 'assign':
        assigned_to_id = request.POST.get('assigned_to')
        if assigned_to_id:
            try:
                assigned_user = User.objects.get(id=assigned_to_id, is_staff=True)
                old_assigned = ticket.assigned_to
                ticket.assigned_to = assigned_user
                ticket.save()
                messages.success(request, f'Ticket assigned to {assigned_user.get_full_name() or assigned_user.email}')
                
                # Log activity
                AdminActivity.objects.create(
                    admin=request.user,
                    action='assign',
                    description=f'Assigned ticket #{ticket.ticket_id} to {assigned_user.email}',
                    ip_address=request.META.get('REMOTE_ADDR')
                )
            except User.DoesNotExist:
                messages.error(request, 'Invalid user selected for assignment')
        else:
            # Unassign ticket
            old_assigned = ticket.assigned_to
            ticket.assigned_to = None
            ticket.save()
            messages.success(request, 'Ticket unassigned')
            
            # Log activity
            AdminActivity.objects.create(
                admin=request.user,
                action='unassign',
                description=f'Unassigned ticket #{ticket.ticket_id}',
                ip_address=request.META.get('REMOTE_ADDR')
            )
    
    elif action == 'reply':
        message_text = request.POST.get('message')
        is_internal = request.POST.get('is_internal') == 'on'
        
        if message_text:
            message = SupportMessage.objects.create(
                ticket=ticket,
                sender=request.user,
                message=message_text,
                message_type='admin',
                is_internal=is_internal
            )
            
            # Update ticket status if it was open
            if ticket.status == 'open':
                ticket.status = 'in_progress'
                ticket.save()
            
            messages.success(request, 'Reply sent successfully')
            
            # Log activity
            AdminActivity.objects.create(
                admin=request.user,
                action='reply',
                description=f'Replied to ticket #{ticket.ticket_id}' + (' (internal note)' if is_internal else ''),
                ip_address=request.META.get('REMOTE_ADDR')
            )
        else:
            messages.error(request, 'Message content is required')
    
    return redirect('admin_panel:support_ticket_detail', ticket_id=ticket_id)
def support_tickets(request):
    """View for managing support tickets"""
    status_filter = request.GET.get('status', 'all')
    order_filter = request.GET.get('order', 'all')
    category_filter = request.GET.get('category', 'all')
    assigned_filter = request.GET.get('assigned', 'all')
    search_query = request.GET.get('q', '')
    
    # Base queryset
    tickets = SupportTicket.objects.select_related('user', 'category', 'assigned_to').prefetch_related('messages')
    
    # Apply filters
    if status_filter != 'all':
        tickets = tickets.filter(status=status_filter)
    
    if order_filter != 'all':
        if order_filter == 'with_order':
            tickets = tickets.exclude(order_id__isnull=True).exclude(order_id='')
        elif order_filter == 'no_order':
            tickets = tickets.filter(Q(order_id__isnull=True) | Q(order_id=''))
    
    if category_filter != 'all':
        tickets = tickets.filter(category_id=category_filter)
    
    if assigned_filter != 'all':
        if assigned_filter == 'unassigned':
            tickets = tickets.filter(assigned_to__isnull=True)
        else:
            tickets = tickets.filter(assigned_to_id=assigned_filter)
    
    if search_query:
        tickets = tickets.filter(
            Q(ticket_id__icontains=search_query) |
            Q(subject__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(order_id__icontains=search_query)
        )
    
    tickets = tickets.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(tickets, 15)
    page_number = request.GET.get('page', 1)
    tickets_page = paginator.get_page(page_number)
    
    # Get categories and staff users for filters
    categories = SupportCategory.objects.filter(is_active=True).order_by('name')
    staff_users = User.objects.filter(is_staff=True).order_by('first_name', 'last_name')
    
    # Statistics
    stats = {
        'total': SupportTicket.objects.count(),
        'open': SupportTicket.objects.filter(status='open').count(),
        'in_progress': SupportTicket.objects.filter(status='in_progress').count(),
        'waiting_customer': SupportTicket.objects.filter(status='waiting_customer').count(),
        'resolved': SupportTicket.objects.filter(status='resolved').count(),
        'closed': SupportTicket.objects.filter(status='closed').count(),
        'unassigned': SupportTicket.objects.filter(assigned_to__isnull=True).count(),
        'overdue': len([t for t in SupportTicket.objects.filter(status__in=['open', 'in_progress']) if t.is_overdue]),
    }
    
    context = {
        'tickets': tickets_page,
        'categories': categories,
        'staff_users': staff_users,
        'status_filter': status_filter,
        'order_filter': order_filter,
        'category_filter': category_filter,
        'assigned_filter': assigned_filter,
        'search_query': search_query,
        'stats': stats,
        'active_tab': 'support'
    }
    
    return render(request, 'admin_panel/support_tickets.html', context)


@login_required
@user_passes_test(is_admin)
def support_ticket_detail(request, ticket_id):
    """View detailed information about a support ticket"""
    ticket = get_object_or_404(
        SupportTicket.objects.select_related('user', 'category', 'assigned_to').prefetch_related(
            'messages__sender', 'attachments'
        ),
        ticket_id=ticket_id
    )
    
    # Get all staff users for assignment dropdown
    staff_users = User.objects.filter(is_staff=True).order_by('first_name', 'last_name')
    
    context = {
        'ticket': ticket,
        'staff_users': staff_users,
        'active_tab': 'support'
    }
    
    return render(request, 'admin_panel/support_ticket_detail.html', context)


@login_required
@user_passes_test(is_admin)
@require_POST
def update_support_ticket(request, ticket_id):
    """Update support ticket status, priority, assignment etc."""
    ticket = get_object_or_404(SupportTicket, ticket_id=ticket_id)
    
    action = request.POST.get('action')
    
    if action == 'update_status':
        new_status = request.POST.get('status')
        if new_status in ['open', 'in_progress', 'waiting_customer', 'resolved', 'closed']:
            old_status = ticket.status
            ticket.status = new_status
            
            # Update timestamps based on status
            if new_status == 'resolved' and old_status != 'resolved':
                ticket.resolved_at = timezone.now()
            elif new_status == 'closed' and old_status != 'closed':
                ticket.closed_at = timezone.now()
            
            ticket.save()
            messages.success(request, f'Ticket status updated to {ticket.get_status_display()}')
            
            # Log activity
            AdminActivity.objects.create(
                admin=request.user,
                action='update',
                description=f'Updated ticket #{ticket.ticket_id} status from {old_status} to {new_status}',
                ip_address=request.META.get('REMOTE_ADDR')
            )
    
    elif action == 'update_priority':
        new_priority = request.POST.get('priority')
        if new_priority in ['low', 'normal', 'high', 'urgent']:
            old_priority = ticket.priority
            ticket.priority = new_priority
            ticket.save()
            messages.success(request, f'Ticket priority updated to {ticket.get_priority_display()}')
            
            # Log activity
            AdminActivity.objects.create(
                admin=request.user,
                action='update',
                description=f'Updated ticket #{ticket.ticket_id} priority from {old_priority} to {new_priority}',
                ip_address=request.META.get('REMOTE_ADDR')
            )
    
    elif action == 'assign':
        assigned_to_id = request.POST.get('assigned_to')
        if assigned_to_id:
            try:
                assigned_user = User.objects.get(id=assigned_to_id, is_staff=True)
                old_assigned = ticket.assigned_to
                ticket.assigned_to = assigned_user
                ticket.save()
                messages.success(request, f'Ticket assigned to {assigned_user.get_full_name() or assigned_user.email}')
                
                # Log activity
                AdminActivity.objects.create(
                    admin=request.user,
                    action='assign',
                    description=f'Assigned ticket #{ticket.ticket_id} to {assigned_user.email}',
                    ip_address=request.META.get('REMOTE_ADDR')
                )
            except User.DoesNotExist:
                messages.error(request, 'Invalid user selected for assignment')
        else:
            # Unassign ticket
            old_assigned = ticket.assigned_to
            ticket.assigned_to = None
            ticket.save()
            messages.success(request, 'Ticket unassigned')
            
            # Log activity
            AdminActivity.objects.create(
                admin=request.user,
                action='unassign',
                description=f'Unassigned ticket #{ticket.ticket_id}',
                ip_address=request.META.get('REMOTE_ADDR')
            )
    
    elif action == 'reply':
        message_text = request.POST.get('message')
        is_internal = request.POST.get('is_internal') == 'on'
        
        if message_text:
            message = SupportMessage.objects.create(
                ticket=ticket,
                sender=request.user,
                message=message_text,
                message_type='admin',
                is_internal=is_internal
            )
            
            # Update ticket status if it's open
            if ticket.status == 'open':
                ticket.status = 'in_progress'
                ticket.save()
            
            messages.success(request, 'Reply sent successfully')
            
            # Log activity
            AdminActivity.objects.create(
                admin=request.user,
                action='reply',
                description=f'Replied to ticket #{ticket.ticket_id}' + (' (internal note)' if is_internal else ''),
                ip_address=request.META.get('REMOTE_ADDR')
            )
        else:
            messages.error(request, 'Message content is required')
    
    return redirect('admin_panel:support_ticket_detail', ticket_id=ticket_id)


@login_required
@user_passes_test(is_admin)


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


@login_required
@user_passes_test(is_admin)
@require_POST
def update_support_ticket(request, ticket_id):
    """Handle support ticket updates (replies, status changes, etc.)"""
    ticket = get_object_or_404(SupportTicket, ticket_id=ticket_id)
    action = request.POST.get('action')
    
    if action == 'reply':
        message = request.POST.get('message', '').strip()
        is_internal = request.POST.get('is_internal') == 'on'
        
        if message:
            # Create new message
            new_message = SupportMessage.objects.create(
                ticket=ticket,
                sender=request.user,
                message=message,
                message_type='admin',
                is_internal=is_internal,
            )
            
            # Update ticket status if needed
            if ticket.status == 'open':
                ticket.status = 'in_progress'
                ticket.save()
            
            # Send real-time update via WebSocket
            from support.consumers import send_ticket_update
            if not is_internal:  # Only send external messages to users
                message_data = {
                    'id': new_message.id,
                    'message': new_message.message,
                    'sender': {
                        'name': new_message.sender.get_full_name() or new_message.sender.email,
                        'type': 'admin'
                    },
                    'timestamp': new_message.created_at.isoformat(),
                    'message_type': new_message.message_type,
                }
                send_ticket_update(ticket.ticket_id, message_data, 'message')
            
            # Log admin activity
            AdminActivity.objects.create(
                admin=request.user,
                action='other',
                description=f'Replied to support ticket #{ticket.ticket_id}: {message[:50]}...' if len(message) > 50 else f'Replied to support ticket #{ticket.ticket_id}: {message}',
            )
            
            messages.success(request, 'Reply sent successfully!')
        else:
            messages.error(request, 'Message cannot be empty.')
            
    elif action == 'status_change':
        new_status = request.POST.get('status')
        if new_status and new_status in dict(SupportTicket.STATUS_CHOICES):
            old_status = ticket.status
            ticket.status = new_status
            
            # Set timestamps for status changes
            if new_status == 'resolved':
                ticket.resolved_at = timezone.now()
            elif new_status == 'closed':
                ticket.closed_at = timezone.now()
                
            ticket.save()
            
            # Send real-time status update via WebSocket
            from support.consumers import send_ticket_update
            send_ticket_update(ticket.ticket_id, None, 'status_change')
            
            # Log admin activity
            AdminActivity.objects.create(
                admin=request.user,
                action='update',
                description=f'Changed status of support ticket #{ticket.ticket_id} from "{old_status}" to "{new_status}"',
            )
            
            messages.success(request, f'Ticket status updated to {new_status}.')
        else:
            messages.error(request, 'Invalid status.')
            
    elif action == 'assign':
        assignee_id = request.POST.get('assigned_to')
        if assignee_id:
            try:
                assignee = User.objects.get(id=assignee_id, is_staff=True)
                old_assignee = ticket.assigned_to
                ticket.assigned_to = assignee
                ticket.save()
                
                # Log admin activity
                AdminActivity.objects.create(
                    admin=request.user,
                    action='update',
                    description=f'Assigned support ticket #{ticket.ticket_id} from "{old_assignee or "Unassigned"}" to "{assignee.get_full_name() or assignee.email}"',
                )
                
                messages.success(request, f'Ticket assigned to {assignee.get_full_name() or assignee.email}.')
            except User.DoesNotExist:
                messages.error(request, 'Invalid assignee.')
        else:
            ticket.assigned_to = None
            ticket.save()
            messages.success(request, 'Ticket unassigned.')
    
    return redirect('admin_panel:support_ticket_detail', ticket_id=ticket_id)


@user_passes_test(is_admin)
@require_POST
def send_typing_indicator(request, ticket_id):
    """Send typing indicator for support ticket"""
    import json
    
    try:
        ticket = get_object_or_404(SupportTicket, ticket_id=ticket_id)
        data = json.loads(request.body)
        is_typing = data.get('is_typing', False)
        
        # Send typing indicator via WebSocket
        from support.consumers import send_typing_indicator
        send_typing_indicator(
            ticket_id=ticket.ticket_id,
            user_name=request.user.get_full_name() or request.user.email,
            is_typing=is_typing
        )
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        print(f'Error sending typing indicator: {e}')
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ================================
# ADMIN MANAGEMENT VIEWS
# ================================

@admin_required('admin_management')
def admin_management(request):
    """Admin management page"""
    from .models import AdminUser, AdminRole
    
    # Check if user has admin management permission
    try:
        admin_user = request.user.admin_profile
        if not admin_user.has_permission('admin_management'):
            messages.error(request, 'You do not have permission to access admin management')
            return redirect('admin_panel:dashboard')
    except:
        # If user doesn't have admin profile, they must be a super user
        if not request.user.is_superuser:
            messages.error(request, 'You do not have permission to access admin management')
            return redirect('admin_panel:dashboard')
    
    admin_users = AdminUser.objects.select_related('user', 'role').order_by('-created_at')
    roles = AdminRole.objects.filter(is_active=True).order_by('display_name')
    
    context = {
        'active_tab': 'admin_management',
        'admin_users': admin_users,
        'roles': roles,
    }
    
    # Log admin activity
    AdminActivity.objects.create(
        admin=request.user,
        action='other',
        description="Accessed admin management page",
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    return render(request, 'admin_panel/admin_management.html', context)


@login_required
@user_passes_test(is_admin)
@require_POST
def create_admin_user(request):
    """Create a new admin user"""
    from .models import AdminUser, AdminRole, AdminPermission
    from django.contrib.auth import get_user_model
    import json
    
    User = get_user_model()
    
    try:
        # Check permissions
        admin_user = request.user.admin_profile
        if not admin_user.has_permission('admin_management'):
            return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
    except:
        if not request.user.is_superuser:
            return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
    
    try:
        data = json.loads(request.body)
        print(f"DEBUG: Received data for admin creation: {data}")  # Debug output
        
        # Validate required fields
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        role_id = data.get('role') or data.get('role_id')  # Accept both 'role' and 'role_id'
        additional_permissions = data.get('additional_permissions', [])
        
        if not email or not password or not role_id:
            return JsonResponse({
                'success': False,
                'message': 'Email, password, and role are required'
            })
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            return JsonResponse({
                'success': False,
                'message': 'User with this email already exists'
            })
        
        # Get role
        role = AdminRole.objects.get(id=role_id, is_active=True)
        
        # Create user
        user = User.objects.create_user(
            email=email,
            password=password,
            user_type='admin',
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', '')
        )
        
        # Create admin profile
        admin_profile = AdminUser.objects.create(
            user=user,
            role=role,
            is_active=data.get('is_active', True),
            can_login=data.get('can_login', True),
            created_by=request.user
        )
        
        # Add additional permissions if provided
        if additional_permissions:
            permissions = AdminPermission.objects.filter(id__in=additional_permissions)
            admin_profile.additional_permissions.set(permissions)
        
        # Log admin activity
        try:
            from .models import AdminActivity
            AdminActivity.objects.create(
                admin=request.user,
                action='create',
                description=f"Created admin user: {email} with role: {role.display_name}",
                ip_address=request.META.get('REMOTE_ADDR')
            )
        except Exception as log_error:
            # Don't fail user creation if logging fails
            print(f"Failed to log admin activity: {log_error}")
        
        return JsonResponse({
            'success': True,
            'message': f'Admin user {email} created successfully',
            'admin_id': admin_profile.id
        })
        
    except AdminRole.DoesNotExist:
        print(f"DEBUG: AdminRole.DoesNotExist - role_id: {role_id}")
        return JsonResponse({'success': False, 'message': 'Invalid role selected'})
    except Exception as e:
        print(f"DEBUG: Exception in create_admin_user: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
@user_passes_test(is_admin)
def get_admin_user_details(request, admin_id):
    """Get admin user details"""
    from .models import AdminUser
    
    try:
        admin_user = AdminUser.objects.select_related('user', 'role').get(id=admin_id)
        
        return JsonResponse({
            'success': True,
            'admin': {
                'id': admin_user.id,
                'email': admin_user.user.email,
                'first_name': admin_user.user.first_name,
                'last_name': admin_user.user.last_name,
                'role_id': admin_user.role.id,
                'role_name': admin_user.role.display_name,
                'is_active': admin_user.is_active,
                'can_login': admin_user.can_login,
                'additional_permissions': list(admin_user.additional_permissions.values('id', 'display_name')),
                'created_at': admin_user.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'last_login': admin_user.user.last_login.strftime('%Y-%m-%d %H:%M:%S') if admin_user.user.last_login else None
            }
        })
        
    except AdminUser.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Admin user not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
@user_passes_test(is_admin)
@require_POST
def update_admin_user(request, admin_id):
    """Update admin user"""
    from .models import AdminUser, AdminRole, AdminPermission
    import json
    
    try:
        # Check permissions
        admin_user_profile = request.user.admin_profile
        if not admin_user_profile.has_permission('admin_management'):
            return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
    except:
        if not request.user.is_superuser:
            return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
    
    try:
        admin_user = AdminUser.objects.get(id=admin_id)
        data = json.loads(request.body)
        
        # Update user fields
        user = admin_user.user
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'email' in data and data['email'] != user.email:
            # Check if email is already taken
            from django.contrib.auth import get_user_model
            User = get_user_model()
            if User.objects.filter(email=data['email']).exclude(id=user.id).exists():
                return JsonResponse({'success': False, 'message': 'Email already exists'})
            user.email = data['email']
        
        user.save()
        
        # Update admin profile fields
        if 'role_id' in data:
            role = AdminRole.objects.get(id=data['role_id'], is_active=True)
            admin_user.role = role
        
        if 'is_active' in data:
            admin_user.is_active = data['is_active']
        
        if 'can_login' in data:
            admin_user.can_login = data['can_login']
        
        admin_user.save()
        
        # Update additional permissions
        if 'additional_permissions' in data:
            permissions = AdminPermission.objects.filter(id__in=data['additional_permissions'])
            admin_user.additional_permissions.set(permissions)
        
        # Log admin activity
        AdminActivity.objects.create(
            admin=request.user,
            action='update',
            description=f"Updated admin user: {user.email}",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Admin user updated successfully'
        })
        
    except AdminUser.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Admin user not found'}, status=404)
    except AdminRole.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invalid role selected'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
@user_passes_test(is_admin)
@require_POST
def delete_admin_user(request, admin_id):
    """Delete admin user"""
    from .models import AdminUser
    
    try:
        # Check permissions
        admin_user_profile = request.user.admin_profile
        if not admin_user_profile.has_permission('admin_management'):
            return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
    except:
        if not request.user.is_superuser:
            return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
    
    try:
        admin_user = AdminUser.objects.get(id=admin_id)
        
        # Prevent deletion of current user
        if admin_user.user == request.user:
            return JsonResponse({'success': False, 'message': 'Cannot delete your own account'})
        
        user_email = admin_user.user.email
        
        # Delete user (this will cascade delete the admin profile)
        admin_user.user.delete()
        
        # Log admin activity
        AdminActivity.objects.create(
            admin=request.user,
            action='delete',
            description=f"Deleted admin user: {user_email}",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Admin user {user_email} deleted successfully'
        })
        
    except AdminUser.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Admin user not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
@user_passes_test(is_admin)
def get_permissions_and_roles(request):
    """Get all permissions and roles for admin management"""
    from .models import AdminPermission, AdminRole
    
    try:
        permissions = AdminPermission.objects.all().values('id', 'name', 'display_name', 'description')
        roles = AdminRole.objects.filter(is_active=True).values('id', 'name', 'display_name', 'description')
        
        return JsonResponse({
            'success': True,
            'permissions': list(permissions),
            'roles': list(roles)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)
