from django.urls import path
from . import address_views

urlpatterns = [
    path('addresses/', address_views.list_user_addresses, name='list_user_addresses'),
    path('addresses/create/', address_views.create_address, name='create_address'),
    path('addresses/<int:address_id>/', address_views.get_address, name='get_address'),
    path('addresses/<int:address_id>/update/', address_views.update_address, name='update_address'),
    path('addresses/<int:address_id>/delete/', address_views.delete_address, name='delete_address'),
    path('addresses/<int:address_id>/set-default/', address_views.set_default_address, name='set_default_address'),
]