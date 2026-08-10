from django.urls import path
from . import views

urlpatterns = [
    path('process/', views.process_payment, name='process_payment'),
    path('methods/', views.payment_methods, name='payment_methods'),
    path('methods/<int:pk>/', views.payment_method_detail, name='payment_method_detail'),
    path('verify/', views.verify_payment, name='verify_payment'),
    path('refund/', views.refund_payment, name='refund_payment'),
    # Phase 3 (Payment 2.0, Part B workstream 13): gateway webhook receiver.
    path('webhook/', views.payment_webhook, name='payment_webhook'),
] 