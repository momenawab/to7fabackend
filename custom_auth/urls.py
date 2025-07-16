from django.urls import path
from rest_framework.authtoken import views as auth_views
from . import views
from . import api_views

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
] 