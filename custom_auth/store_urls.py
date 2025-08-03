from django.urls import path
from . import api_views

urlpatterns = [
    # Store endpoints
    path('top/', api_views.top_stores, name='top_stores'),
    path('featured/', api_views.featured_stores, name='featured_stores'),
    path('search/', api_views.search_stores, name='search_stores'),
]