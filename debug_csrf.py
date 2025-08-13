#!/usr/bin/env python3
"""
Debug script to test CSRF configuration
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'to7fabackend.settings')
django.setup()

from django.conf import settings
from django.test import RequestFactory
from django.middleware.csrf import get_token

def test_csrf_config():
    print("🔍 CSRF Configuration Debug")
    print("=" * 50)
    
    # Check middleware
    middleware = settings.MIDDLEWARE
    csrf_middleware = 'django.middleware.csrf.CsrfViewMiddleware'
    
    print(f"✅ CSRF Middleware enabled: {csrf_middleware in middleware}")
    
    # Check CSRF settings
    csrf_settings = [
        'CSRF_COOKIE_NAME',
        'CSRF_COOKIE_AGE', 
        'CSRF_COOKIE_HTTPONLY',
        'CSRF_COOKIE_SECURE',
        'CSRF_COOKIE_SAMESITE',
        'CSRF_HEADER_NAME',
        'CSRF_USE_SESSIONS'
    ]
    
    print("\n📋 CSRF Settings:")
    for setting in csrf_settings:
        value = getattr(settings, setting, 'NOT SET')
        print(f"   {setting}: {value}")
    
    # Test token generation
    factory = RequestFactory()
    request = factory.get('/')
    
    try:
        token = get_token(request)
        print(f"\n🔑 CSRF Token Generation: ✅ SUCCESS")
        print(f"   Token length: {len(token)} characters")
        print(f"   Token preview: {token[:10]}...")
    except Exception as e:
        print(f"\n❌ CSRF Token Generation FAILED: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Troubleshooting Tips:")
    print("1. Ensure CSRF_COOKIE_HTTPONLY is False for JavaScript access")
    print("2. Check that {% csrf_token %} is in all forms")
    print("3. Verify X-CSRFToken header is sent with AJAX requests")
    print("4. Clear browser cookies and restart Django server")
    print("5. Check browser console for CSRF-related errors")

if __name__ == '__main__':
    test_csrf_config()