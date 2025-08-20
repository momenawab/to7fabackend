from django.urls import path
from . import views

app_name = 'support'

urlpatterns = [
    # Public API endpoints for mobile app users
    path('categories/', views.get_support_categories, name='support_categories'),
    path('tickets/', views.user_tickets, name='user_tickets'),
    path('tickets/create/', views.create_ticket, name='create_ticket'),
    path('tickets/<str:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    path('tickets/<str:ticket_id>/message/', views.add_message, name='add_message'),
    path('tickets/<str:ticket_id>/rate/', views.rate_ticket, name='rate_ticket'),
    
    # Admin API endpoints
    path('admin/tickets/', views.admin_tickets, name='admin_tickets'),
    path('admin/tickets/<str:ticket_id>/', views.admin_update_ticket, name='admin_update_ticket'),
    path('admin/tickets/<str:ticket_id>/reply/', views.admin_reply_ticket, name='admin_reply_ticket'),
    path('admin/stats/', views.admin_stats, name='admin_stats'),
]