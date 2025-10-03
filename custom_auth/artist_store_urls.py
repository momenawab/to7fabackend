from django.urls import path
from . import api_views

urlpatterns = [
    # Artist endpoints
    path('top/', api_views.top_artists, name='top_artists'),
    path('featured/', api_views.featured_artists, name='featured_artists'),
    path('search/', api_views.search_artists, name='search_artists'),
]