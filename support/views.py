# Support views - New Contact System + Backward Compatibility

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

# Import new contact system
from .contact_models import ContactRequest

def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@api_view(['POST'])
@permission_classes([AllowAny])  # Allow both authenticated and anonymous users
def create_ticket(request):
    """Backward compatibility endpoint - redirects to new contact system"""
    try:
        # Extract data from old ticket format and convert to new contact format
        old_data = request.data
        
        # Map old ticket fields to new contact fields
        contact_data = {
            'name': request.user.get_full_name() if request.user.is_authenticated else old_data.get('name', 'App User'),
            'phone': old_data.get('phone', 'Contact via app'),
            'subject': old_data.get('subject', ''),
            'message': old_data.get('description', old_data.get('message', '')),
        }
        
        # Create contact request using new system
        contact = ContactRequest.objects.create(
            user=request.user if request.user.is_authenticated else None,
            name=contact_data['name'],
            phone=contact_data['phone'],
            subject=contact_data['subject'],
            message=contact_data['message'],
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Return response in old ticket format for compatibility
        return Response({
            'success': True,
            'message': 'Contact request submitted successfully. We will contact you via WhatsApp within 24 hours.',
            'ticket': {
                'ticket_id': contact.contact_number,
                'subject': contact.subject,
                'status': 'open',
                'created_at': contact.created_at
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'success': False,
            'errors': {'detail': str(e)}
        }, status=status.HTTP_400_BAD_REQUEST)


# All other views are now handled by the new contact system in contact_views.py
# Import them for backward compatibility if needed
from .contact_views import (
    CreateContactView, ContactListView, ContactDetailView, 
    ContactStatsView, add_contact_note, get_whatsapp_link
)