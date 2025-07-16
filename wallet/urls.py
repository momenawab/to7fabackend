from django.urls import path
from . import views

urlpatterns = [
    path('', views.wallet_details, name='wallet_details'),
    path('deposit/', views.deposit_funds, name='deposit_funds'),
    path('withdraw/', views.withdraw_funds, name='withdraw_funds'),
    path('transactions/', views.transaction_history, name='transaction_history'),
] 