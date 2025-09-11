from django.urls import path
from . import ar_views

urlpatterns = [
    # Product AR settings
    path('products/<int:product_id>/ar-settings/', ar_views.get_product_ar_settings, name='product-ar-settings'),

    # AR Frame combinations
    path('frame-combination/', ar_views.get_ar_frame_combination, name='ar-frame-combination'),
    path('available-variants/', ar_views.get_available_ar_frame_variants, name='ar-available-variants'),
    path('frame-assets/', ar_views.ARFrameAssetListView.as_view(), name='ar-frame-assets-list'),

    # AR preview sessions for analytics
    path('preview-session/', ar_views.create_ar_preview_session, name='create-ar-preview-session'),
    path('preview-session/<int:session_id>/', ar_views.update_ar_preview_session, name='update-ar-preview-session'),

    # AR analytics
    path('analytics/', ar_views.ar_analytics, name='ar-analytics'),

    # Products with AR support
    path('products/', ar_views.ProductARSettingsListView.as_view(), name='ar-products-list'),
]