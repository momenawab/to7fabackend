from django.shortcuts import redirect
from django.urls import resolve
from django.contrib import messages
import re
from .models import AdminActivity

def is_admin(user):
    """Helper function to check if user is admin - same as in views.py"""
    # Check if user is staff or superuser
    if user.is_staff or user.is_superuser:
        return True
    
    # Check if user has admin profile
    try:
        admin_profile = user.admin_profile
        return admin_profile.is_active and admin_profile.can_login
    except AttributeError:
        return False

class AdminPanelMiddleware:
    """
    Middleware to restrict access to the admin panel to admin users.
    If a non-admin user tries to access the admin panel, they will be redirected to the login page.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Check if the request path is for the admin panel
        if request.path.startswith('/dashboard/') and request.path != '/dashboard/login/':
            # If user is not authenticated or not admin, redirect to login
            if not request.user.is_authenticated or not is_admin(request.user):
                messages.error(request, "You don't have permission to access the admin panel.")
                return redirect('admin_panel:login')
        
        response = self.get_response(request)
        return response

class AdminActivityMiddleware:
    """Middleware to track admin login and logout activities"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Login and logout URL patterns
        self.login_url = re.compile(r'^/dashboard/login/$')
        self.logout_url = re.compile(r'^/dashboard/logout/$')
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Track successful login
        if self.login_url.match(request.path) and request.method == 'POST' and response.status_code == 302:
            if request.user.is_authenticated and is_admin(request.user):
                AdminActivity.objects.create(
                    admin=request.user,
                    action='login',
                    description=f"Admin login: {request.user.email}",
                    ip_address=request.META.get('REMOTE_ADDR')
                )
        
        # Track logout
        if self.logout_url.match(request.path) and request.method == 'GET':
            user = getattr(request, '_user', None)
            if user and user.is_authenticated and is_admin(user):
                AdminActivity.objects.create(
                    admin=user,
                    action='logout',
                    description=f"Admin logout: {user.email}",
                    ip_address=request.META.get('REMOTE_ADDR')
                )
        
        return response