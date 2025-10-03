# Support admin - New Contact System Only

from django.contrib import admin

# Import and register new contact system admin
from .contact_admin import ContactRequestAdmin, ContactNoteAdmin, ContactStatsAdmin
from .contact_models import ContactRequest, ContactNote, ContactStats

# The new contact system admin classes are automatically registered via @admin.register decorators
# in contact_admin.py. No additional registration needed here.