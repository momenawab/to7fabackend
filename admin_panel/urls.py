from django.urls import path
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
    
    # Order Management
    path('orders/', views.order_management, name='order_management'),
    path('orders/<int:order_id>/view/', views.view_order, name='view_order'),
    
    # Reports
    path('reports/', views.reports, name='reports'),
    
    # Settings
    path('settings/', views.settings, name='settings'),
    
    # API endpoints
    path('api/stats/', views.admin_stats_api, name='admin_stats_api'),
    path('api/notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    
    path('activity-log/', views.activity_log, name='activity_log'),
] 