"""
ASGI config for to7fabackend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'to7fabackend.settings')

from django.core.asgi import get_asgi_application

# Phase 4 (Part 4, production ASGI server) fix: get_asgi_application() must run - and
# DJANGO_SETTINGS_MODULE must already be set - before anything that imports Django
# models is imported. This file used to `import support.routing` (which imports
# support.consumers, which imports django.contrib.auth.models) at the very top, ahead
# of both of those steps, and the module-level Django model class machinery in
# django.contrib.auth.base_user raises `AppRegistryNotReady: Apps aren't loaded yet.`
# in that case - a real, previously invisible bug: nothing in this project's test
# suite exercises asgi.py under conditions where Django's app registry *isn't*
# already loaded (pytest-django/conftest.py calls django.setup() long before any test
# module - including the "asgi.py imports without error" regression test added in
# Phase 3 - is ever collected, so the ordering bug was masked in every test run).
# Discovered this phase by actually running `daphne to7fabackend.asgi:application`
# for the first time - exactly what Part 4 exists to verify. get_asgi_application()
# now runs first (it calls django.setup() internally), and the Channels-specific
# imports come after it, matching Django Channels' own documented asgi.py structure.
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import support.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            support.routing.websocket_urlpatterns
        )
    ),
})
