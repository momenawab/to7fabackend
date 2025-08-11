from django.urls import path
from django.http import JsonResponse
from . import views

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
    
    # Category Management
    path('categories/', views.category_management, name='categories'),
    
    # Attribute Management
    path('attributes/', views.attribute_management, name='attributes'),
    
    # Settings
    path('settings/', views.settings, name='settings'),
    
    # API endpoints
    path('api/stats/', views.admin_stats_api, name='admin_stats_api'),
    path('api/notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('api/test/', lambda request: JsonResponse({'status': 'working', 'user': str(request.user)}), name='api_test'),
    path('api/categories/', views.get_categories_json, name='get_categories_json'),
    path('api/categories/<int:category_id>/attributes/', views.get_category_attributes_json, name='get_category_attributes_json'),
    
    path('activity-log/', views.activity_log, name='activity_log'),
] 