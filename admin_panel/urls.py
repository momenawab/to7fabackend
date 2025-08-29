from django.urls import path
from django.http import JsonResponse
from . import views, api_views

app_name = 'admin_panel'

urlpatterns = [
    # Authentication
    path('login/', views.admin_login, name='login'),
    path('logout/', views.admin_logout, name='logout'),
    
    # Dashboard
    path('', views.admin_dashboard, name='dashboard'),
    
    # Seller Applications
    path('applications/', views.seller_applications, name='seller_applications'),
    path('applications/<int:application_id>/', views.seller_application_detail, name='seller_application_detail'),
    path('applications/<int:application_id>/process/', views.process_application, name='process_application'),
    
    # User Management
    path('users/', views.user_management, name='user_management'),
    path('users/<int:user_id>/profile/', views.view_user_profile, name='view_user_profile'),
    
    # Product Management
    path('products/', views.product_management, name='product_management'),
    path('products/add-with-variants/', views.add_product_with_variants, name='add_product_with_variants'),
    path('products/<int:product_id>/edit-with-variants/', views.edit_product_with_variants, name='edit_product_with_variants'),
    
    # Product Approval
    path('product-approval/', views.product_approval, name='product_approval'),
    path('product-approval/<int:product_id>/process/', views.process_product_approval, name='process_product_approval'),
    path('api/product/<int:product_id>/details/', views.product_detail_api, name='product_detail_api'),
    
    # Order Management
    path('orders/', views.order_management, name='order_management'),
    path('orders/<int:order_id>/view/', views.view_order, name='view_order'),
    
    # Reports
    path('reports/', views.reports, name='reports'),
    
    # Ads Control
    path('ads/', views.ads_control, name='ads_control'),
    
    # Artists and Stores Management
    path('artists-stores/', views.artists_stores, name='artists_stores'),
    
    # Featured Products Management
    path('featured-products/', views.featured_products, name='featured_products'),
    
    # Seller Requests Management
    path('seller-requests/', views.seller_requests_management, name='seller_requests_management'),
    
    # Category Management
    path('categories/', views.category_management, name='categories'),
    
    # Attribute Management
    path('attributes/', views.attribute_management, name='attributes'),
    
    # Subcategory Sections Management
    path('subcategory-sections/', views.subcategory_sections_management, name='subcategory_sections'),
    path('api/subcategory-sections/create/', views.create_subcategory_section_api, name='create_subcategory_section_api'),
    path('api/subcategory-sections/<int:section_id>/toggle/', views.toggle_subcategory_section_api, name='toggle_subcategory_section_api'),
    path('api/subcategory-sections/<int:section_id>/update/', views.update_subcategory_section_api, name='update_subcategory_section_api'),
    path('api/subcategory-sections/<int:section_id>/delete/', views.delete_subcategory_section_api, name='delete_subcategory_section_api'),
    
    # Variant Management
    path('variants/', views.variant_management, name='variant_management'),
    path('variants/create-type/', views.create_variant_type, name='create_variant_type'),
    path('variants/create-option/', views.create_variant_option, name='create_variant_option'),
    path('variants/delete-type/', views.delete_variant_type, name='delete_variant_type'),
    path('variants/update-priority/', views.update_variant_priority, name='update_variant_priority'),
    path('variants/delete-option/', views.delete_variant_option, name='delete_variant_option'),
    
    # Support Tickets
    path('support-tickets/', views.support_tickets, name='support_tickets'),
    path('support-tickets/<str:ticket_id>/', views.support_ticket_detail, name='support_ticket_detail'),
    path('support-tickets/<str:ticket_id>/update/', views.update_support_ticket, name='update_support_ticket'),
    path('support-tickets/<str:ticket_id>/typing/', views.send_typing_indicator, name='send_typing_indicator'),
    
    # Admin Management
    path('admin-management/', views.admin_management, name='admin_management'),
    path('api/admin-users/create/', views.create_admin_user, name='create_admin_user'),
    path('api/admin-users/<int:user_id>/', views.get_admin_user_details, name='get_admin_user_details'),
    path('api/admin-users/<int:user_id>/update/', views.update_admin_user, name='update_admin_user'),
    path('api/admin-users/<int:user_id>/delete/', views.delete_admin_user, name='delete_admin_user'),
    path('api/admin-permissions-roles/', views.get_permissions_and_roles, name='get_permissions_and_roles'),
    
    # Settings
    path('settings/', views.settings, name='settings'),
    
    # API endpoints
    path('api/stats/', views.admin_stats_api, name='admin_stats_api'),
    path('api/notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('api/test/', lambda request: JsonResponse({'status': 'working', 'user': str(request.user)}), name='api_test'),
    path('api/categories/', views.get_categories_json, name='get_categories_json'),
    path('api/categories/<int:category_id>/attributes/', views.get_category_attributes_json, name='get_category_attributes_json'),
    path('api/categories/<int:category_id>/variants/', views.get_category_variants_json, name='get_category_variants_json'),
    
    path('activity-log/', views.activity_log, name='activity_log'),
    
    # Seller Requests API endpoints
    path('api/seller-requests/', api_views.seller_requests_list, name='seller_requests_list'),
    path('api/seller-requests/<int:request_id>/mark-payment/', api_views.mark_payment_completed, name='mark_payment_completed'),
    path('api/seller-requests/<int:request_id>/mark-payment-and-approve/', api_views.mark_payment_and_auto_approve, name='mark_payment_and_auto_approve'),
    path('api/seller-requests/offer/<int:request_id>/approve/', api_views.approve_offer_request, name='approve_offer_request'),
    path('api/seller-requests/featured/<int:request_id>/approve/', api_views.approve_featured_request, name='approve_featured_request'),
] 