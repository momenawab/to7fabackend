from django.urls import path, include
from rest_framework.authtoken import views as auth_views
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
from . import api_views
from . import address_views
from . import jwt_views

urlpatterns = [
    # Legacy endpoints (backward compatible)
    path('register/', views.register_user, name='register'),
    # Legacy login endpoint DISABLED - security bypass. Use /api/auth/login/ instead
    # path('login/', views.LoginView.as_view(), name='login'),
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
    
    # New JWT Authentication endpoints (recommended for Flutter)
    path('api/auth/login/', jwt_views.login_view, name='jwt_login'),
    path('api/auth/logout/', jwt_views.logout_view, name='jwt_logout'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='jwt_refresh'),
    path('api/auth/password-reset/request/', jwt_views.request_password_reset, name='password_reset_request'),
    path('api/auth/password-reset/confirm/', jwt_views.confirm_password_reset, name='password_reset_confirm'),
    path('api/auth/email-verification/request/', jwt_views.request_email_verification, name='email_verification_request'),
    path('api/auth/email-verification/verify/', jwt_views.verify_email, name='email_verification_verify'),
    path('api/auth/send-otp/', api_views.send_otp, name='send_otp'),
    path('api/auth/verify-otp/', api_views.verify_otp, name='verify_otp'),

    # Artist and Store endpoints for admin content management
    path('api/artists/top/', api_views.top_artists, name='top_artists'),
    path('api/artists/featured/', api_views.featured_artists, name='featured_artists'),
    path('api/artists/search/', api_views.search_artists, name='search_artists'),
    path('api/stores/top/', api_views.top_stores, name='top_stores'),
    path('api/stores/featured/', api_views.featured_stores, name='featured_stores'),
    path('api/stores/search/', api_views.search_stores, name='search_stores'),
    
    # Admin endpoints for managing featured status and priority
    path('api/admin/artists/<int:artist_id>/toggle-featured/', api_views.toggle_artist_featured, name='toggle_artist_featured'),
    path('api/admin/artists/<int:artist_id>/update-priority/', api_views.update_artist_priority, name='update_artist_priority'),
    path('api/admin/stores/<int:store_id>/toggle-featured/', api_views.toggle_store_featured, name='toggle_store_featured'),
    path('api/admin/stores/<int:store_id>/update-priority/', api_views.update_store_priority, name='update_store_priority'),
    
    # Address management endpoints
    path('api/addresses/', address_views.list_user_addresses, name='list_addresses'),
    path('api/addresses/create/', address_views.create_address, name='create_address'),
    path('api/addresses/<int:address_id>/', address_views.get_address, name='get_address'),
    path('api/addresses/<int:address_id>/update/', address_views.update_address, name='update_address'),
    path('api/addresses/<int:address_id>/delete/', address_views.delete_address, name='delete_address'),
    path('api/addresses/<int:address_id>/set-default/', address_views.set_default_address, name='set_default_address'),
    
] 