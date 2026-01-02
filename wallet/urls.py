from django.urls import path
from . import views

urlpatterns = [
    # Wallet operations
    path('', views.wallet_details, name='wallet_details'),
    path('deposit/', views.deposit_funds, name='deposit_funds'),
    path('withdraw/', views.withdraw_funds, name='withdraw_funds'),
    path('transfer/', views.transfer_funds, name='transfer_funds'),
    
    # Transaction history
    path('transactions/', views.transaction_history, name='transaction_history'),
    path('transactions/<int:transaction_id>/', views.transaction_detail, name='transaction_detail'),
    
    # Balance history
    path('balance-history/', views.balance_history, name='balance_history'),
    
    # Admin operations
    path('admin/transactions/', views.all_transactions, name='all_transactions'),
    path('admin/snapshot/', views.create_balance_snapshot, name='create_balance_snapshot'),
]
