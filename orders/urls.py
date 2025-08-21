from django.urls import path
from . import views

urlpatterns = [
    path('', views.order_list, name='order_list'),
    path('<int:pk>/', views.order_detail, name='order_detail'),
    path('create/', views.create_order, name='create_order'),
    path('<int:pk>/cancel/', views.cancel_order, name='cancel_order'),
    path('seller/', views.seller_orders, name='seller_orders'),
    path('seller/<int:pk>/status/', views.update_order_status, name='update_order_status'),
    path('user-orders/', views.user_orders_for_support, name='user_orders_for_support'),
] 