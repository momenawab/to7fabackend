# Support serializers - New Contact System Only

# Import new contact system serializers
from .contact_serializers import (
    ContactRequestSerializer, ContactNoteSerializer, ContactStatsSerializer,
    ContactDashboardSerializer, BulkContactActionSerializer, ContactFilterSerializer,
    WhatsAppLinkSerializer, ContactSummarySerializer
)

# Re-export for easier imports
__all__ = [
    'ContactRequestSerializer', 'ContactNoteSerializer', 'ContactStatsSerializer',
    'ContactDashboardSerializer', 'BulkContactActionSerializer', 'ContactFilterSerializer',
    'WhatsAppLinkSerializer', 'ContactSummarySerializer'
]