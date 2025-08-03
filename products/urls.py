from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('<int:pk>/', views.product_detail, name='product_detail'),
    path('categories/', views.category_list, name='category_list'),
    path('categories/<int:pk>/', views.category_detail, name='category_detail'),
    path('search/', views.product_search, name='product_search'),
    path('<int:pk>/reviews/', views.product_reviews, name='product_reviews'),
    path('seller/', views.seller_products, name='seller_products'),
    path('seller/<int:pk>/', views.seller_product_detail, name='seller_product_detail'),
    
    # Admin-controlled content endpoints
    path('latest-offers/', views.latest_offers, name='latest_offers'),
    path('featured/', views.featured_products, name='featured_products'),
    path('top-rated/', views.top_rated_products, name='top_rated_products'),
    path('advertisements/', views.advertisements, name='advertisements'),
    path('content-settings/', views.content_settings, name='content_settings'),
    
    # Admin management endpoints
    path('admin/offers/', views.manage_offers, name='manage_offers'),
    path('admin/offers/<int:offer_id>/', views.manage_offer_detail, name='manage_offer_detail'),
    path('admin/featured/', views.manage_featured_products, name='manage_featured_products'),
    path('admin/featured/<int:featured_id>/', views.manage_featured_detail, name='manage_featured_detail'),
    path('admin/toggle-featured/<int:product_id>/', views.toggle_product_featured, name='toggle_product_featured'),
] 