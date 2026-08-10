"""
API URL Configuration

This module defines URL routing for API v1 endpoints.
Following API Response Standard with /api/v1/ prefix.

This is the PRIMARY API CONTRACT for all public client-facing endpoints.
"""

from django.urls import path, include
from products import views as product_views
from orders import views as order_views
from cart import views as cart_views
from custom_auth import views as auth_views
from custom_auth import api_views as auth_api_views
from custom_auth import address_views
from custom_auth import jwt_views
from wallet import views as wallet_views
from payment import views as payment_views
from notifications import views as notification_views
from support import views as support_views
from support.contact_views import (
    CreateContactView, ContactListView, ContactDetailView,
    ContactStatsView, UserContactListView
)
from rest_framework_simplejwt.views import TokenRefreshView

# API v1 URL patterns
# Note: This file is included under 'api/v1/' in the main urls.py,
# so we don't add another 'v1/' prefix here
urlpatterns = [
        # Products endpoints (function-based views)
        path('products/', product_views.product_list, name='product-list'),
        path('products/<int:pk>/', product_views.product_detail, name='product-detail'),
        path('products/search/', product_views.product_search, name='product-search'),
        path('products/<int:pk>/reviews/', product_views.product_reviews, name='product-reviews'),
        path('seller/products/', product_views.seller_products, name='seller-products'),
        path('seller/products/<int:pk>/', product_views.seller_product_detail, name='seller-product-detail'),
        path('products/<int:pk>/toggle-featured/', product_views.toggle_product_featured, name='product-toggle-featured'),
        
        # Content endpoints
        path('latest-offers/', product_views.latest_offers, name='latest-offers'),
        path('featured-products/', product_views.featured_products, name='featured-products'),
        path('top-rated-products/', product_views.top_rated_products, name='top-rated-products'),
        path('advertisements/', product_views.advertisements, name='advertisements'),
        path('content-settings/', product_views.content_settings, name='content-settings'),
        
        # Categories endpoints
        path('categories/', product_views.category_list, name='category-list'),
        path('categories/<int:pk>/', product_views.category_detail, name='category-detail'),
        path('categories/for-wizard/', product_views.categories_for_product_wizard, name='categories-for-wizard'),
        path('categories/<int:category_id>/variants/', product_views.category_variants, name='category-variants'),
        path('categories/<int:category_id>/tags/', product_views.category_tags, name='category-tags'),
        path('categories/<int:category_id>/sections/', product_views.subcategory_sections, name='subcategory-sections'),
        path('categories/sections/all/', product_views.all_subcategory_sections, name='all-subcategory-sections'),
        
        # Seller request endpoints
        path('seller/offer-requests/', product_views.seller_offer_requests, name='seller-offer-requests'),
        path('seller/featured-requests/', product_views.seller_featured_requests, name='seller-featured-requests'),
        path('seller/offer-requests/<int:request_id>/', product_views.seller_offer_request_detail, name='seller-offer-request-detail'),
        path('seller/featured-requests/<int:request_id>/', product_views.seller_featured_request_detail, name='seller-featured-request-detail'),
        
        # Attribute management endpoints
        path('admin/attributes/<str:attribute_type>/options/', product_views.get_attribute_options, name='attribute-options'),
        path('admin/categories/<int:category_id>/attributes/', product_views.get_category_attributes, name='category-attributes'),
        path('admin/categories/<int:category_id>/attributes/update/', product_views.update_category_attributes, name='update-category-attributes'),

        # Phase 4 (Part 7.2): debug/arabic/ (debug_arabic_encoding) removed - see
        # products/views.py's removal comment for the full writeup.

        # Orders endpoints
        path('orders/', order_views.order_list, name='order-list'),
        path('orders/<int:pk>/', order_views.order_detail, name='order-detail'),
        path('orders/create/', order_views.create_order, name='order-create'),
        path('orders/<int:pk>/cancel/', order_views.cancel_order, name='order-cancel'),
        path('orders/<int:pk>/status/', order_views.update_order_status, name='order-update-status'),
        path('orders/<int:pk>/capture-payment/', order_views.capture_payment, name='order-capture-payment'),
        path('orders/<int:pk>/release-payment/', order_views.release_payment, name='order-release-payment'),
        path('seller/orders/', order_views.seller_orders, name='seller-orders'),
        path('orders/states/', order_views.order_states, name='order-states'),
        path('orders/<int:pk>/complete/', order_views.admin_complete_order, name='order-admin-complete'),
        path('user/orders/', order_views.user_orders_for_support, name='user-orders-support'),
        
        # Cart endpoints
        path('cart/', cart_views.cart_detail, name='cart-detail'),
        path('cart/add/', cart_views.add_to_cart, name='cart-add'),
        path('cart/items/<int:item_id>/', cart_views.update_cart_item, name='cart-update-item'),
        path('cart/items/<int:item_id>/remove/', cart_views.remove_from_cart, name='cart-remove-item'),
        path('cart/clear/', cart_views.clear_cart, name='cart-clear'),
        
        # Wallet endpoints
        path('wallet/', wallet_views.wallet_details, name='wallet-details'),
        path('wallet/deposit/', wallet_views.deposit_funds, name='wallet-deposit'),
        path('wallet/withdraw/', wallet_views.withdraw_funds, name='wallet-withdraw'),
        path('wallet/transfer/', wallet_views.transfer_funds, name='wallet-transfer'),
        path('wallet/transactions/', wallet_views.transaction_history, name='wallet-transactions'),
        path('wallet/balance-history/', wallet_views.balance_history, name='wallet-balance-history'),
        path('wallet/transactions/<int:transaction_id>/', wallet_views.transaction_detail, name='wallet-transaction-detail'),
        path('admin/wallet/transactions/', wallet_views.all_transactions, name='admin-all-transactions'),
        path('admin/wallet/snapshot/', wallet_views.create_balance_snapshot, name='admin-create-balance-snapshot'),
        
        # Auth endpoints
        path('auth/register/', auth_views.register_user, name='auth-register'),
        path('auth/login/', jwt_views.login_view, name='auth-login'),
        path('auth/logout/', jwt_views.logout_view, name='auth-logout'),
        path('auth/refresh/', TokenRefreshView.as_view(), name='auth-refresh'),
        path('auth/profile/', auth_views.user_profile, name='auth-profile'),
        path('auth/password-reset/request/', jwt_views.request_password_reset, name='password-reset-request'),
        path('auth/password-reset/confirm/', jwt_views.confirm_password_reset, name='password-reset-confirm'),
        path('auth/email-verification/request/', jwt_views.request_email_verification, name='email-verification-request'),
        path('auth/email-verification/verify/', jwt_views.verify_email, name='email-verification-verify'),
        
        # Address endpoints
        path('addresses/', address_views.list_user_addresses, name='address-list'),
        path('addresses/create/', address_views.create_address, name='address-create'),
        path('addresses/<int:address_id>/', address_views.get_address, name='address-detail'),
        path('addresses/<int:address_id>/update/', address_views.update_address, name='address-update'),
        path('addresses/<int:address_id>/delete/', address_views.delete_address, name='address-delete'),
        path('addresses/<int:address_id>/set-default/', address_views.set_default_address, name='address-set-default'),
        
        # Admin/Content endpoints (from products/views.py)
        path('admin/', include([
            path('offers/', product_views.manage_offers),
            path('offers/<int:offer_id>/', product_views.manage_offer_detail),
            path('featured/', product_views.manage_featured_products),
            path('featured/<int:featured_id>/', product_views.manage_featured_detail),
            path('advertisements/', product_views.manage_advertisements),
            path('advertisements/<int:ad_id>/', product_views.manage_advertisement_detail),
            path('categories/manage/', product_views.manage_categories),
            path('categories/create/', product_views.create_category),
            path('categories/<int:category_id>/', product_views.manage_category_detail),
            path('categories/<int:category_id>/update/', product_views.update_category),
            path('categories/<int:category_id>/delete/', product_views.delete_category),
            path('content-settings/', product_views.content_settings),
            path('seller-requests/', product_views.manage_seller_requests),
            path('seller-requests/approve-offer/<int:request_id>/', product_views.approve_offer_request),
            path('seller-requests/approve-featured/<int:request_id>/', product_views.approve_featured_request),
            path('seller-requests/offer-detail/<int:request_id>/', product_views.seller_offer_request_detail),
            path('seller-requests/reject-offer/<int:request_id>/', product_views.reject_offer_request),
            path('seller-requests/featured-detail/<int:request_id>/', product_views.seller_featured_request_detail),
            path('seller-requests/reject-featured/<int:request_id>/', product_views.reject_featured_request),
        ])),
        
        # Seller endpoints
        path('sellers/applications/', auth_api_views.submit_seller_application, name='seller-application'),
        path('artists/top/', auth_api_views.top_artists, name='artists-top'),
        path('artists/featured/', auth_api_views.featured_artists, name='artists-featured'),
        path('artists/search/', auth_api_views.search_artists, name='artists-search'),
        path('artists/<int:artist_id>/toggle-featured/', auth_api_views.toggle_artist_featured, name='artist-toggle-featured'),
        path('artists/<int:artist_id>/update-priority/', auth_api_views.update_artist_priority, name='artist-update-priority'),
        path('stores/top/', auth_api_views.top_stores, name='stores-top'),
        path('stores/featured/', auth_api_views.featured_stores, name='stores-featured'),
        path('stores/search/', auth_api_views.search_stores, name='stores-search'),
        path('stores/<int:store_id>/toggle-featured/', auth_api_views.toggle_store_featured, name='store-toggle-featured'),
        path('stores/<int:store_id>/update-priority/', auth_api_views.update_store_priority, name='store-update-priority'),
        
        # User management endpoints
        path('users/<int:user_id>/', auth_api_views.get_user_details, name='user-detail'),
        path('users/<int:user_id>/block-unblock/', auth_api_views.block_unblock_user, name='user-block-unblock'),
        
        # Payment endpoints
        path('payments/process/', payment_views.process_payment, name='payment-process'),
        path('payments/methods/', payment_views.payment_methods, name='payment-methods'),
        path('payments/methods/<int:pk>/', payment_views.payment_method_detail, name='payment-method-detail'),
        path('payments/verify/', payment_views.verify_payment, name='payment-verify'),
        path('payments/refund/', payment_views.refund_payment, name='payment-refund'),
        
        # Notifications endpoints
        path('notifications/', notification_views.NotificationListView.as_view(), name='notification-list'),
        path('notifications/legacy/', notification_views.notification_list, name='notification-list-legacy'),
        path('notifications/<int:pk>/', notification_views.NotificationDetailView.as_view(), name='notification-detail'),
        path('notifications/<int:pk>/read/', notification_views.mark_notification_read, name='notification-mark-read'),
        path('notifications/<int:pk>/delete/', notification_views.delete_notification, name='notification-delete'),
        path('notifications/read-all/', notification_views.mark_all_read, name='notification-read-all'),
        path('notifications/clear-all/', notification_views.clear_all_notifications, name='notification-clear-all'),
        path('notifications/stats/', notification_views.notification_stats, name='notification-stats'),
        path('notifications/devices/register/', notification_views.register_device, name='notification-register-device'),
        path('notifications/devices/', notification_views.list_user_devices, name='notification-list-devices'),
        path('notifications/devices/<str:device_id>/', notification_views.update_device_settings, name='notification-update-device'),
        path('notifications/devices/<str:device_id>/unregister/', notification_views.unregister_device, name='notification-unregister-device'),
        path('notifications/send/', notification_views.send_notification_api, name='notification-send'),
        path('notifications/push/test/', notification_views.test_push_notification, name='notification-test-push'),
        
        # Support endpoints
        path('support/contact/create/', CreateContactView.as_view(), name='support-contact-create'),
        path('support/contact/', ContactListView.as_view(), name='support-contact-list'),
        path('support/contact/<str:contact_number>/', ContactDetailView.as_view(), name='support-contact-detail'),
        path('support/contact/<str:contact_number>/update/', ContactDetailView.as_view(), name='support-contact-update'),
        path('support/contact/<str:contact_number>/note/', support_views.add_contact_note, name='support-contact-note'),
        path('support/contact/<str:contact_number>/whatsapp/', support_views.get_whatsapp_link, name='support-contact-whatsapp'),
        path('support/contact/stats/', ContactStatsView.as_view(), name='support-contact-stats'),
        path('support/user/contacts/', UserContactListView.as_view(), name='support-user-contacts'),
        path('support/tickets/create/', support_views.create_ticket, name='support-ticket-create'),
]
