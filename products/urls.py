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
] 