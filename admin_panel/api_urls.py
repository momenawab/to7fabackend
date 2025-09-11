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
    
    # Seller Registration (Public endpoints for app users)
    path('seller/apply/', api_views.create_seller_application, name='create_seller_application'),
    path('seller/categories/', api_views.get_categories_for_seller, name='get_categories_for_seller'),
    path('seller/subcategories/<int:category_id>/', api_views.get_subcategories_for_seller, name='get_subcategories_for_seller'),
    path('seller/governorates/', api_views.get_egyptian_governorates, name='get_egyptian_governorates'),
    path('seller/status/', api_views.get_user_application_status, name='get_user_application_status'),
    
    # Seller Dashboard APIs (For approved sellers)
    path('seller/dashboard/test-auth/', api_views.test_seller_auth, name='test_seller_auth'),
    path('seller/dashboard/stats/', api_views.seller_dashboard_stats, name='seller_dashboard_stats'),
    path('seller/dashboard/ad-types/', api_views.get_ad_types, name='seller_ad_types'),
    path('seller/dashboard/ad-bookings/create/', api_views.create_ad_booking, name='seller_create_ad_booking'),
    path('seller/dashboard/products/', api_views.seller_products, name='seller_products'),
    path('seller/dashboard/products/<int:product_id>/', api_views.seller_product_detail, name='seller_product_detail'),
    path('seller/dashboard/products/create/', api_views.create_product_wizard, name='create_product_wizard'),
    path('seller/dashboard/products/<int:product_id>/toggle-status/', api_views.toggle_seller_product_status, name='toggle_seller_product_status'),
    path('seller/dashboard/products/<int:product_id>/duplicate/', api_views.duplicate_seller_product, name='duplicate_seller_product'),
    path('seller/dashboard/products/<int:product_id>/stock/', api_views.update_seller_product_stock, name='update_seller_product_stock'),
    path('seller/dashboard/products/<int:product_id>/variants/<int:variant_id>/stock/', api_views.update_seller_variant_stock, name='update_seller_variant_stock'),
    path('seller/dashboard/products/<int:product_id>/combination-stocks/', api_views.update_combination_variant_stock, name='update_combination_variant_stock'),
    path('seller/dashboard/products/bulk-edit/', api_views.bulk_edit_seller_products, name='bulk_edit_seller_products'),
    path('seller/dashboard/products/export/', api_views.export_seller_products, name='export_seller_products'),
    path('seller/dashboard/analytics/', api_views.seller_product_analytics, name='seller_product_analytics'),
    path('seller/dashboard/orders/', api_views.seller_orders, name='seller_orders'),
    path('seller/dashboard/orders/<int:order_id>/status/', api_views.update_order_status, name='update_order_status'),
    path('seller/dashboard/profile/', api_views.seller_profile, name='seller_profile'),
    
    # Seller Requests Management API endpoints
    path('seller-requests/', api_views.seller_requests_list, name='seller_requests_list'),
    path('seller-requests/<int:request_id>/mark-payment/', api_views.mark_payment_completed, name='mark_payment_completed'),
    path('seller-requests/<int:request_id>/mark-payment-and-approve/', api_views.mark_payment_and_auto_approve, name='mark_payment_and_auto_approve'),
    path('seller-requests/offer/<int:request_id>/approve/', api_views.approve_offer_request, name='approve_offer_request'),
    path('seller-requests/featured/<int:request_id>/approve/', api_views.approve_featured_request, name='approve_featured_request'),
    
    # Ad Type Requirements Management
    path('ad-types/<int:ad_type_id>/requirements/', api_views.update_ad_type_requirements, name='update_ad_type_requirements'),
    
    # Ad Booking Dashboard API endpoints
    path('ad-bookings/<int:booking_id>/', api_views.ad_booking_detail_api, name='ad_booking_detail_api'),
    path('ad-bookings/<int:booking_id>/approve/', api_views.approve_ad_booking_api, name='approve_ad_booking_api'),
    path('ad-bookings/<int:booking_id>/activate/', api_views.activate_ad_booking_api, name='activate_ad_booking_api'),
    path('ad-bookings/<int:booking_id>/reject/', api_views.reject_ad_booking_api, name='reject_ad_booking_api'),
    path('ad-bookings/<int:booking_id>/notes/', api_views.update_ad_booking_notes_api, name='update_ad_booking_notes_api'),
    
    # ========================
    # USER NOTIFICATION MANAGEMENT API
    # ========================
    
    # List and manage user notifications
    path('notifications/', api_views.UserNotificationListView.as_view(), name='user_notifications_list'),
    
    # Send notifications
    path('notifications/send/', api_views.send_user_notification_api, name='send_user_notification'),
    path('notifications/send-bulk/', api_views.send_bulk_notification_api, name='send_bulk_notification'),
    
    # Statistics and data
    path('notifications/stats/', api_views.notification_stats_api, name='notification_stats'),
    path('notifications/users/', api_views.users_for_notifications_api, name='users_for_notifications'),
] 