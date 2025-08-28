from functools import wraps
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from .models import AdminUser

def admin_required(permission_name=None):
    """
    Decorator to check if user has admin access and optionally specific permission
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(request, *args, **kwargs):
            # Check if user is admin
            if not is_admin(request.user):
                messages.error(request, "You don't have admin privileges.")
                return redirect('admin_panel:login')
            
            # Check specific permission if required
            if permission_name:
                if not has_admin_permission(request.user, permission_name):
                    messages.error(request, f"You don't have permission to access this section.")
                    return redirect('admin_panel:dashboard')
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator

def is_admin(user):
    """Check if user is admin"""
    if user.is_staff or user.is_superuser:
        return True
    
    try:
        admin_profile = user.admin_profile
        return admin_profile.is_active and admin_profile.can_login
    except AttributeError:
        return False

def has_admin_permission(user, permission_name):
    """Check if admin user has specific permission"""
    if user.is_superuser:
        return True
    
    try:
        admin_profile = user.admin_profile
        if admin_profile and admin_profile.is_active:
            return admin_profile.has_permission(permission_name)
    except AttributeError:
        # Fallback for staff users
        if user.is_staff:
            return True
    
    return False

def get_user_permissions(user):
    """Get all permissions for a user"""
    if user.is_superuser:
        from .models import AdminPermission
        return set(AdminPermission.objects.values_list('name', flat=True))
    
    try:
        admin_profile = user.admin_profile
        if admin_profile and admin_profile.is_active:
            return admin_profile.get_all_permissions()
    except AttributeError:
        if user.is_staff:
            from .models import AdminPermission
            return set(AdminPermission.objects.values_list('name', flat=True))
    
    return set()