"""
Integration tests for checkout verification gate.

Tests that unverified users are blocked from checkout and verified users can checkout.
"""

import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from products.models import Product, ProductVariant
from cart.models import Cart, CartItem
from custom_auth.models import User

User = get_user_model()


class CheckoutVerificationTests(TestCase):
    """Test checkout verification gate functionality."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        # Set valid HTTP_HOST header for APIClient
        self.client.defaults['HTTP_HOST'] = 'localhost'
        
        # Create unverified user
        self.unverified_user = User.objects.create_user(
            email='unverified@example.com',
            password='testpass123',
            phone_number='+201234567890',
            is_mobile_verified=False
        )
        
        # Create verified user
        self.verified_user = User.objects.create_user(
            email='verified@example.com',
            password='testpass123',
            phone_number='+201234567891',
            is_mobile_verified=True
        )
        
        # Create a category for testing
        from products.models import Category
        self.category = Category.objects.create(
            name='Test Category'
        )
        
        # Create product for testing
        self.product = Product.objects.create(
            name='Test Product',
            base_price=100.00,
            stock_quantity=10,
            seller=self.verified_user,
            category=self.category,
            approval_status='approved'
        )
        
        # Create cart for unverified user
        self.unverified_cart = Cart.objects.create(user=self.unverified_user)
        CartItem.objects.create(
            cart=self.unverified_cart,
            product=self.product,
            quantity=2
        )
        
        # Create cart for verified user
        self.verified_cart = Cart.objects.create(user=self.verified_user)
        CartItem.objects.create(
            cart=self.verified_cart,
            product=self.product,
            quantity=1
        )

    def test_unverified_user_blocked_from_checkout(self):
        """
        Test that unverified user receives 403 MOBILE_VERIFICATION_REQUIRED
        when attempting to create an order.
        """
        # Authenticate as unverified user
        refresh = RefreshToken.for_user(self.unverified_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Attempt to create order (checkout)
        order_data = {
            'items_data': [
                {
                    'product_id': self.product.id,
                    'quantity': 1,
                    'variant_id': None
                }
            ],
            'shipping_address': '123 Test St, Test City',
            'shipping_cost': 15.50,
            'payment_method': 'wallet',
            'idempotency_key': 'test_order_123',
            'use_wallet_payment': True
        }
        
        response = self.client.post('/api/v1/order/create/', order_data, format='json')
        
        # Assert 403 Forbidden response
        self.assertEqual(response.status_code, 403)
        
        # Assert error code is MOBILE_VERIFICATION_REQUIRED
        response_data = response.json()
        self.assertEqual(response_data['success'], False)
        self.assertEqual(response_data['error'], 'MOBILE_VERIFICATION_REQUIRED')
        self.assertIn('Mobile verification required', response_data['message'])

    def test_verified_user_can_checkout(self):
        """
        Test that verified user can successfully create an order.
        """
        # Authenticate as verified user
        refresh = RefreshToken.for_user(self.verified_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Create order (checkout)
        order_data = {
            'items_data': [
                {
                    'product_id': self.product.id,
                    'quantity': 1,
                    'variant_id': None
                }
            ],
            'shipping_address': '123 Test St, Test City',
            'shipping_cost': 15.50,
            'payment_method': 'wallet',
            'idempotency_key': 'test_order_456',
            'use_wallet_payment': True
        }
        
        response = self.client.post('/api/v1/order/create/', order_data, format='json')
        
        # Assert successful response (201 Created or 200 OK)
        self.assertIn(response.status_code, [200, 201])
        
        # Assert order was created
        response_data = response.json()
        self.assertEqual(response_data['success'], True)
        self.assertIn('data', response_data)
        self.assertIn('id', response_data['data'])
        
        # Verify order exists in database
        from orders.models import Order
        order = Order.objects.get(id=response_data['data']['id'])
        self.assertEqual(order.user, self.verified_user)
        self.assertEqual(order.status, 'pending')
