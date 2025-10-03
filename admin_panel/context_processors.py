from products.models import Product
from custom_auth.models import SellerApplication
from support.models import ContactRequest
from .models import AdminUser

def admin_panel_context(request):
    """
    Context processor to provide common admin panel data
    """
    if request.user.is_authenticated and hasattr(request.user, 'is_admin') and request.user.is_admin:
        # Count pending products
        pending_products = Product.objects.filter(is_active=False).count()
        
        # Count pending seller applications
        pending_applications = SellerApplication.objects.filter(status='pending').count()
        
        # Count pending contact requests
        pending_tickets = ContactRequest.objects.filter(status__in=['new', 'in_progress']).count()
        
        return {
            'pending_products': pending_products,
            'pending_applications': pending_applications,
            'pending_tickets': pending_tickets,
        }
    
    return {
        'pending_products': 0,
        'pending_applications': 0,
        'pending_tickets': 0,
    }

def admin_permissions(request):
    """
    Add admin permissions to template context for role-based UI
    """
    context = {
        'user_permissions': set(),
        'is_super_admin': False,
        'user_role_name': None,
        'user_role_display': None,
    }
    
    if request.user.is_authenticated:
        try:
            # Check if user has admin profile
            admin_profile = request.user.admin_profile
            if admin_profile and admin_profile.is_active and admin_profile.can_login:
                # Get user permissions
                context['user_permissions'] = admin_profile.get_all_permissions()
                context['is_super_admin'] = admin_profile.is_super_admin()
                context['user_role_name'] = admin_profile.role.name
                context['user_role_display'] = admin_profile.role.display_name
        except AttributeError:
            # User doesn't have admin profile - check if they're staff/superuser
            if request.user.is_staff or request.user.is_superuser:
                # Give staff/superuser all permissions
                from .models import AdminPermission
                all_permissions = AdminPermission.objects.values_list('name', flat=True)
                context['user_permissions'] = set(all_permissions)
                context['is_super_admin'] = True
                context['user_role_name'] = 'super_admin'
                context['user_role_display'] = 'Super Admin'
    
    return context