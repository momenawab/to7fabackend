from django.urls import path, include
from rest_framework.authtoken import views as auth_views
from . import views
from . import api_views
from . import address_views

urlpatterns = [
    path('register/', views.register_user, name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout, name='logout'),
    path('profile/', views.user_profile, name='user_profile'),
    path('seller/register/', views.register_seller, name='register_seller'),
    path('seller/apply/', views.SellerApplicationView.as_view(), name='seller_apply'),
    path('seller/application/status/', views.ApplicationStatusView.as_view(), name='application_status'),
    path('password/reset/', views.password_reset_request, name='password_reset'),
    path('password/reset/confirm/', views.password_reset_confirm, name='password_reset_confirm'),
    path('api/token-auth/', auth_views.obtain_auth_token, name='api_token_auth'),
    path('api/users/<int:user_id>/', api_views.get_user_details, name='get_user_details'),
    path('api/users/<int:user_id>/block/', api_views.block_unblock_user, name='block_unblock_user'),
    path('api/seller/apply/', api_views.submit_seller_application, name='api_seller_apply'),
    
    # Artist and Store endpoints for admin content management
    path('api/artists/top/', api_views.top_artists, name='top_artists'),
    path('api/artists/featured/', api_views.featured_artists, name='featured_artists'),
    path('api/artists/search/', api_views.search_artists, name='search_artists'),
    path('api/stores/top/', api_views.top_stores, name='top_stores'),
    path('api/stores/featured/', api_views.featured_stores, name='featured_stores'),
    path('api/stores/search/', api_views.search_stores, name='search_stores'),
    
    # Address management endpoints
    path('api/addresses/', address_views.list_user_addresses, name='list_addresses'),
    path('api/addresses/create/', address_views.create_address, name='create_address'),
    path('api/addresses/<int:address_id>/', address_views.get_address, name='get_address'),
    path('api/addresses/<int:address_id>/update/', address_views.update_address, name='update_address'),
    path('api/addresses/<int:address_id>/delete/', address_views.delete_address, name='delete_address'),
    path('api/addresses/<int:address_id>/set-default/', address_views.set_default_address, name='set_default_address'),
    
] 