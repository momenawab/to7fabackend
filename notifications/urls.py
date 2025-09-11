from django.urls import path
from . import views

urlpatterns = [
    # Enhanced notification endpoints
    path('', views.NotificationListView.as_view(), name='notification_list'),
    path('legacy/', views.notification_list, name='notification_list_legacy'),  # Keep old endpoint
    path('<int:pk>/', views.NotificationDetailView.as_view(), name='notification_detail'),
    path('<int:pk>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('<int:pk>/delete/', views.delete_notification, name='delete_notification'),
    
    # Bulk operations
    path('read-all/', views.mark_all_read, name='mark_all_read'),
    path('clear-all/', views.clear_all_notifications, name='clear_all_notifications'),
    
    # Statistics
    path('stats/', views.notification_stats, name='notification_stats'),
    
    # Device registration endpoints for push notifications
    path('devices/register/', views.register_device, name='register_device'),
    path('devices/', views.list_user_devices, name='list_user_devices'),
    path('devices/<str:device_id>/', views.update_device_settings, name='update_device_settings'),
    path('devices/<str:device_id>/unregister/', views.unregister_device, name='unregister_device'),
    
    # Send notification with push (for custom admin)
    path('send/', views.send_notification_api, name='send_notification_api'),
    
    # Testing endpoint
    path('push/test/', views.test_push_notification, name='test_push_notification'),
] 