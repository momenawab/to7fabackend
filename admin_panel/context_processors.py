from products.models import Product
from custom_auth.models import SellerApplication
from support.models import SupportTicket

def admin_panel_context(request):
    """
    Context processor to provide common admin panel data
    """
    if request.user.is_authenticated and hasattr(request.user, 'is_admin') and request.user.is_admin:
        # Count pending products
        pending_products = Product.objects.filter(is_active=False).count()
        
        # Count pending seller applications
        pending_applications = SellerApplication.objects.filter(status='pending').count()
        
        # Count pending support tickets
        pending_tickets = SupportTicket.objects.filter(status__in=['open', 'in_progress']).count()
        
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