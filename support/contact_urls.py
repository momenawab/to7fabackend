from django.urls import path
from .contact_views import (
    CreateContactView,
    ContactListView,
    ContactDetailView,
    ContactStatsView,
    UserContactListView,
    add_contact_note,
    get_whatsapp_link,
)

app_name = 'contact'

urlpatterns = [
    # Public contact creation
    path('create/', CreateContactView.as_view(), name='create-contact'),
    
    # User contact management
    path('list/', UserContactListView.as_view(), name='user-contact-list'),
    
    # Admin contact management
    path('admin/list/', ContactListView.as_view(), name='contact-list'),
    path('stats/', ContactStatsView.as_view(), name='contact-stats'),
    path('<str:contact_number>/', ContactDetailView.as_view(), name='contact-detail'),
    path('<str:contact_number>/note/', add_contact_note, name='add-contact-note'),
    path('<str:contact_number>/whatsapp/', get_whatsapp_link, name='whatsapp-link'),
]