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
    path('admin/advertisements/', views.manage_advertisements, name='manage_advertisements'),
    path('admin/advertisements/<int:ad_id>/', views.manage_advertisement_detail, name='manage_advertisement_detail'),
    
    # Category management endpoints
    path('admin/categories/', views.manage_categories, name='manage_categories'),
    path('admin/categories/create/', views.create_category, name='create_category'),
    path('admin/categories/<int:category_id>/', views.manage_category_detail, name='manage_category_detail'),
    path('admin/categories/<int:category_id>/update/', views.update_category, name='update_category'),
    path('admin/categories/<int:category_id>/delete/', views.delete_category, name='delete_category'),
    
    # Attribute management endpoints
    path('admin/attributes/<str:attribute_type>/options/', views.get_attribute_options, name='get_attribute_options'),
    path('admin/categories/<int:category_id>/attributes/', views.get_category_attributes, name='get_category_attributes'),
    path('admin/categories/<int:category_id>/attributes/update/', views.update_category_attributes, name='update_category_attributes'),
    
    # Debug endpoint for Arabic encoding
    path('debug/arabic/', views.debug_arabic_encoding, name='debug_arabic_encoding'),
] 