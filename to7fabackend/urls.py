"""
URL configuration for to7fabackend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    # Redirect root URL to admin panel login
    path('', RedirectView.as_view(pattern_name='admin_panel:login', permanent=False)),
    
    # Django admin
    path('admin/', admin.site.urls),
    
    # Custom Admin Panel
    path('dashboard/', include('admin_panel.urls')),
    
    # App URLs
    path('api/auth/', include('custom_auth.urls')),
    path('custom_auth/', include('custom_auth.urls')),  # Direct access to custom_auth endpoints
    path('api/products/', include('products.urls')),
    path('api/orders/', include('orders.urls')),
    path('api/wallet/', include('wallet.urls')),
    path('api/payments/', include('payment.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/cart/', include('cart.urls')),
    
    # Admin API endpoints
    path('api/admin/', include('admin_panel.api_urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
