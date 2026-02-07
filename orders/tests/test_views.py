"""
Integration tests for order lifecycle endpoints.

Tests for new API endpoints: acknowledge, ship, deliver, complete, refund.
"""

import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from products.models import Product, Category
from orders.models import Order, OrderItem
from custom_auth.models import User

User = get_user_model()


class OrderLifecycleTests(TestCase):
    """Test order lifecycle endpoints for state transitions."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.client.defaults['HTTP_HOST'] = 'localhost'
        
        # Create customer user
        self.customer = User.objects.create_user(
            email='customer@example.com',
            password='testpass123',
            phone_number='+201234567890',
            is_mobile_verified=True,
            user_type='customer'
        )
        
        # Create seller user
        self.seller = User.objects.create_user(
            email='seller@example.com',
            password='testpass123',
            phone_number='+201234567891',
            is_mobile_verified=True,
            user_type='store'
        )
        
        # Create admin user
        self.admin = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123',
            phone_number='+201234567892',
            is_mobile_verified=True
        )
        
        # Create category and product
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            name='Test Product',
            base_price=100.00,
            stock_quantity=10,
            seller=self.seller,
            category=self.category,
            approval_status='approved'
        )
        
        # Create an order in PAID state
        self.order = Order.objects.create(
            user=self.customer,
            total_amount=100.00,
            shipping_address='123 Test St',
            shipping_cost=0.00,
            payment_method='wallet',
            status='paid'
        )
        
        # Create order item
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
            price=100.00,
            seller=self.seller
        )

    def test_acknowledge_order_by_seller(self):
        """
        Test that seller can acknowledge order and it transitions to PROCESSING.
        
        Endpoint: POST /orders/{orderId}/acknowledge/
        Expected: Order status changes from 'paid' to 'processing'
        """
        # Authenticate as seller
        refresh = RefreshToken.for_user(self.seller)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Acknowledge order
        response = self.client.post(f'/api/v1/order/{self.order.id}/acknowledge/')
        
        # Assert successful response
        self.assertEqual(response.status_code, 200)
        
        # Assert order status changed to processing
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'processing')
        
        # Assert response contains updated order
        response_data = response.json()
        self.assertEqual(response_data['success'], True)
        self.assertEqual(response_data['data']['status'], 'processing')

    def test_acknowledge_order_by_non_seller_fails(self):
        """
        Test that non-seller cannot acknowledge order.
        
        Endpoint: POST /orders/{orderId}/acknowledge/
        Expected: 403 Forbidden - only sellers can acknowledge
        """
        # Authenticate as customer
        refresh = RefreshToken.for_user(self.customer)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Attempt to acknowledge order
        response = self.client.post(f'/api/v1/order/{self.order.id}/acknowledge/')
        
        # Assert 403 Forbidden
        self.assertEqual(response.status_code, 403)
        
        # Assert order status unchanged
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'paid')

    def test_acknowledge_order_invalid_state(self):
        """
        Test that acknowledge fails for orders not in valid state.
        
        Endpoint: POST /orders/{orderId}/acknowledge/
        Expected: 400 Bad Request - invalid state transition
        """
        # Set order to completed state (terminal)
        self.order.status = 'completed'
        self.order.save()
        
        # Authenticate as seller
        refresh = RefreshToken.for_user(self.seller)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Attempt to acknowledge order
        response = self.client.post(f'/api/v1/order/{self.order.id}/acknowledge/')
        
        # Assert 400 Bad Request
        self.assertEqual(response.status_code, 400)

    def test_ship_order_by_seller(self):
        """
        Test that seller can ship order and it transitions to SHIPPED.
        
        Endpoint: POST /orders/{orderId}/ship/
        Expected: Order status changes from 'processing' to 'shipped'
        """
        # Set order to processing state
        self.order.status = 'processing'
        self.order.save()
        
        # Authenticate as seller
        refresh = RefreshToken.for_user(self.seller)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Ship order with tracking number
        response = self.client.post(
            f'/api/v1/order/{self.order.id}/ship/',
            {'tracking_number': 'TRACK123456'},
            format='json'
        )
        
        # Assert successful response
        self.assertEqual(response.status_code, 200)
        
        # Assert order status changed to shipped
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'shipped')
        
        # Assert response contains updated order
        response_data = response.json()
        self.assertEqual(response_data['success'], True)
        self.assertEqual(response_data['data']['status'], 'shipped')

    def test_ship_order_by_non_seller_fails(self):
        """
        Test that non-seller cannot ship order.
        
        Endpoint: POST /orders/{orderId}/ship/
        Expected: 403 Forbidden - only sellers can ship
        """
        # Set order to processing state
        self.order.status = 'processing'
        self.order.save()
        
        # Authenticate as customer
        refresh = RefreshToken.for_user(self.customer)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Attempt to ship order
        response = self.client.post(f'/api/v1/order/{self.order.id}/ship/')
        
        # Assert 403 Forbidden
        self.assertEqual(response.status_code, 403)

    def test_deliver_order(self):
        """
        Test that order can be marked as delivered.
        
        Endpoint: POST /orders/{orderId}/deliver/
        Expected: Order status changes from 'shipped' to 'delivered'
        """
        # Set order to shipped state
        self.order.status = 'shipped'
        self.order.save()
        
        # Authenticate as customer
        refresh = RefreshToken.for_user(self.customer)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Deliver order
        response = self.client.post(f'/api/v1/order/{self.order.id}/deliver/')
        
        # Assert successful response
        self.assertEqual(response.status_code, 200)
        
        # Assert order status changed to delivered
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'delivered')
        
        # Assert response contains updated order
        response_data = response.json()
        self.assertEqual(response_data['success'], True)
        self.assertEqual(response_data['data']['status'], 'delivered')

    def test_deliver_order_invalid_state(self):
        """
        Test that delivery fails for orders not in shipped state.
        
        Endpoint: POST /orders/{orderId}/deliver/
        Expected: 400 Bad Request - invalid state transition
        """
        # Set order to processing state
        self.order.status = 'processing'
        self.order.save()
        
        # Authenticate as customer
        refresh = RefreshToken.for_user(self.customer)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Attempt to deliver order
        response = self.client.post(f'/api/v1/order/{self.order.id}/deliver/')
        
        # Assert 400 Bad Request
        self.assertEqual(response.status_code, 400)

    def test_complete_order(self):
        """
        Test that order can be completed.
        
        Endpoint: POST /orders/{orderId}/complete/
        Expected: Order status changes from 'delivered' to 'completed'
        """
        # Set order to delivered state
        self.order.status = 'delivered'
        self.order.save()
        
        # Authenticate as customer
        refresh = RefreshToken.for_user(self.customer)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Complete order
        response = self.client.post(f'/api/v1/order/{self.order.id}/complete/')
        
        # Assert successful response
        self.assertEqual(response.status_code, 200)
        
        # Assert order status changed to completed
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'completed')
        
        # Assert response contains updated order
        response_data = response.json()
        self.assertEqual(response_data['success'], True)
        self.assertEqual(response_data['data']['status'], 'completed')

    def test_complete_order_invalid_state(self):
        """
        Test that completion fails for orders not in delivered state.
        
        Endpoint: POST /orders/{orderId}/complete/
        Expected: 400 Bad Request - invalid state transition
        """
        # Set order to shipped state
        self.order.status = 'shipped'
        self.order.save()
        
        # Authenticate as customer
        refresh = RefreshToken.for_user(self.customer)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Attempt to complete order
        response = self.client.post(f'/api/v1/order/{self.order.id}/complete/')
        
        # Assert 400 Bad Request
        self.assertEqual(response.status_code, 400)

    def test_refund_order_by_admin(self):
        """
        Test that admin can refund order and it transitions to REFUNDED.
        
        Endpoint: POST /orders/{orderId}/refund/
        Expected: Order status changes to 'refunded'
        """
        # Set order to paid state
        self.order.status = 'paid'
        self.order.save()
        
        # Authenticate as admin
        refresh = RefreshToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Refund order with reason
        response = self.client.post(
            f'/api/v1/order/{self.order.id}/refund/',
            {'reason': 'Customer requested refund'},
            format='json'
        )
        
        # Assert successful response
        self.assertEqual(response.status_code, 200)
        
        # Assert order status changed to refunded
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'refunded')
        
        # Assert response contains updated order
        response_data = response.json()
        self.assertEqual(response_data['success'], True)
        self.assertEqual(response_data['data']['status'], 'refunded')

    def test_refund_order_by_non_admin_fails(self):
        """
        Test that non-admin cannot refund order.
        
        Endpoint: POST /orders/{orderId}/refund/
        Expected: 403 Forbidden - only admin can refund
        """
        # Authenticate as customer
        refresh = RefreshToken.for_user(self.customer)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Attempt to refund order
        response = self.client.post(
            f'/api/v1/order/{self.order.id}/refund/',
            {'reason': 'Customer requested refund'},
            format='json'
        )
        
        # Assert 403 Forbidden
        self.assertEqual(response.status_code, 403)

    def test_refund_order_invalid_state(self):
        """
        Test that refund fails for orders not in refundable state.
        
        Endpoint: POST /orders/{orderId}/refund/
        Expected: 400 Bad Request - invalid state transition
        """
        # Set order to cancelled state (already cancelled)
        self.order.status = 'cancelled'
        self.order.save()
        
        # Authenticate as admin
        refresh = RefreshToken.for_user(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Attempt to refund order
        response = self.client.post(
            f'/api/v1/order/{self.order.id}/refund/',
            {'reason': 'Test refund'},
            format='json'
        )
        
        # Assert 400 Bad Request
        self.assertEqual(response.status_code, 400)


class OrderStatesEndpointTests(TestCase):
    """Test order states endpoint for state machine information."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.client.defaults['HTTP_HOST'] = 'localhost'
        
        # Create authenticated user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            phone_number='+201234567890',
            is_mobile_verified=True
        )

    def test_order_states_endpoint(self):
        """
        Test that order states endpoint returns state machine information.
        
        Endpoint: GET /orders/states/
        Expected: Returns states, valid transitions, and cancellable states
        """
        # Authenticate user
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Get order states
        response = self.client.get('/api/v1/order/states/')
        
        # Assert successful response
        self.assertEqual(response.status_code, 200)
        
        # Assert response contains state machine info
        response_data = response.json()
        self.assertEqual(response_data['success'], True)
        self.assertIn('data', response_data)
        self.assertIn('states', response_data['data'])
        self.assertIn('valid_transitions', response_data['data'])
        self.assertIn('cancellable_states', response_data['data'])
