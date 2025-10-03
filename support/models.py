# Support models - New Contact System Only

# Import new contact system models
from .contact_models import ContactRequest, ContactNote, ContactStats

# Re-export for easier imports
__all__ = ['ContactRequest', 'ContactNote', 'ContactStats']