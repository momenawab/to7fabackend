from django.urls import path, include
from . import views

app_name = 'support'

urlpatterns = [
    # NEW CONTACT SYSTEM - Primary endpoints
    path('contact/', include('support.contact_urls')),
    
    # Backward compatibility endpoint for old ticket creation
    path('tickets/create/', views.create_ticket, name='create_ticket'),
]