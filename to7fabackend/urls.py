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

API Versioning Strategy (Phase 6):
- PRIMARY API CONTRACT: /api/v1/ - All public client-facing endpoints
- BACKWARD COMPATIBILITY: Legacy routes maintained for existing clients
- ADMIN PANEL: /dashboard/ - Unchanged, admin-only interface
- DJANGO ADMIN: /admin/ - Unchanged, Django's built-in admin
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
    
    # Custom Admin Panel (unchanged - admin-only interface)
    path('dashboard/', include('admin_panel.urls')),
    
    # ============================================================================
    # PRIMARY API CONTRACT - Version 1
    # All public client-facing endpoints are under /api/v1/
    # This is the recommended API contract for all clients
    # ============================================================================
    path('api/v1/', include('api.urls')),
    
    # ============================================================================
    # BACKWARD COMPATIBILITY - Legacy Routes
    # These routes are maintained for existing clients
    # They will continue to work but are deprecated for new integrations
    # ============================================================================
    
    # Legacy authentication endpoints (deprecated - use /api/v1/auth/ instead)
    # Phase 3 (API Contract Part A workstream 7, route sprawl): the second mount at
    # 'custom_auth/' (an internal Django app name leaking into the URL) is removed -
    # confirmed dead via `grep -rn custom_auth/ lib/ admin_panel/templates/` (Flutter
    # and the admin templates) with zero hits. The 'api/auth/' mount stays exactly as
    # is, including the ugly-but-live double nesting this produces for JWT routes
    # (custom_auth/urls.py itself defines paths starting with 'api/auth/...', so JWT
    # login is genuinely reachable at /api/auth/api/auth/login/) - Flutter's own code
    # comment in lib/core/config/api_config.dart ("JWT login at
    # /api/auth/api/auth/login/") confirms this is real, currently-used production
    # traffic, not dead duplication safe to collapse without a coordinated Flutter
    # change (out of scope - backend-only phase, no Flutter changes).
    path('api/auth/', include('custom_auth.urls')),
    
    # Legacy app-specific endpoints (deprecated - use /api/v1/ instead)
    path('api/products/', include('products.urls')),
    path('api/orders/', include('orders.urls')),
    path('api/wallet/', include('wallet.urls')),
    path('api/payments/', include('payment.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/cart/', include('cart.urls')),
    path('api/support/', include('support.urls')),
    path('api/', include('custom_auth.address_urls')),
    path('api/artists/', include('custom_auth.artist_store_urls')),
    path('api/stores/', include('custom_auth.store_urls')),
    
    # Admin API endpoints (deprecated - use /api/v1/admin/ instead)
    path('api/admin/', include('admin_panel.api_urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
