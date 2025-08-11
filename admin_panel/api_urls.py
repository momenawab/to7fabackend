from django.urls import path
from rest_framework.routers import DefaultRouter
from . import api_views

app_name = 'admin_api'

urlpatterns = [
    # Test endpoint for debugging
    path('test/auth/', api_views.test_authentication, name='test_auth'),
    
    # Seller Applications
    path('seller-applications/', api_views.SellerApplicationListView.as_view(), name='seller_applications_list'),
    path('seller-applications/<int:pk>/', api_views.SellerApplicationDetailView.as_view(), name='seller_application_detail'),
    path('seller-applications/<int:pk>/approve/', api_views.approve_application, name='approve_application'),
    
    # Dashboard stats
    path('stats/', api_views.admin_stats, name='admin_stats'),
    
    # Users
    path('users/', api_views.UserListView.as_view(), name='user_list'),
    path('users/<int:pk>/', api_views.UserDetailView.as_view(), name='user_detail'),
    path('users/<int:pk>/block/', api_views.block_user, name='block_user'),
    
    # Products
    path('products/', api_views.ProductListView.as_view(), name='product_list'),
    path('products/<int:pk>/', api_views.ProductDetailView.as_view(), name='product_detail'),
    path('products/<int:pk>/toggle-status/', api_views.toggle_product_status, name='toggle_product_status'),
    
    # Orders
    path('orders/', api_views.OrderListView.as_view(), name='order_list'),
    path('orders/<int:pk>/', api_views.OrderDetailView.as_view(), name='order_detail'),
    
    # Reports
    path('reports/summary/', api_views.report_summary, name='report_summary'),
    path('reports/sales/', api_views.sales_report, name='sales_report'),
    path('reports/users/', api_views.user_report, name='user_report'),
    path('reports/products/', api_views.product_report, name='product_report'),
    
    # Activity log endpoints
    path('activity-log/export/', api_views.export_activity_log, name='export_activity_log'),
    
    # Settings
    path('settings/<str:setting_type>/', api_views.get_settings, name='get_settings'),
    path('settings/<str:setting_type>/update/', api_views.update_settings, name='update_settings'),
    
    # Notifications
    path('notifications/', api_views.AdminNotificationListView.as_view(), name='notification_list'),
    path('notifications/<int:pk>/read/', api_views.mark_notification_read, name='mark_notification_read'),
    path('notifications/read-all/', api_views.mark_all_notifications_read, name='mark_all_notifications_read'),
    
    # Ads
    path('ads/active/', api_views.get_active_ads, name='get_active_ads'),
    path('ads/', api_views.list_advertisements, name='list_advertisements'),
    path('ads/create/', api_views.create_advertisement, name='create_advertisement'),
    path('ads/<int:ad_id>/', api_views.manage_advertisement_detail, name='manage_advertisement_detail'),
    
    # Product with Variants Management
    path('products/admin/create-with-variants/', api_views.create_product_with_variants, name='create_product_with_variants'),
    path('products/admin/<int:product_id>/update-with-variants/', api_views.update_product_with_variants, name='update_product_with_variants'),
    path('products/admin/categories/', api_views.get_categories_for_admin, name='get_categories_for_admin'),
    path('products/admin/categories/<int:category_id>/attributes/', api_views.get_category_attributes_for_admin, name='get_category_attributes_for_admin'),
    path('products/admin/attributes/<str:attribute_type>/options/', api_views.get_attribute_options_for_admin, name='get_attribute_options_for_admin'),
] 