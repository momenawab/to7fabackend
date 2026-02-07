"""
Test login user state response.

Tests that login endpoint returns user state fields:
- is_mobile_verified
- is_locked
- is_blocked
- blocked_capabilities
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
import json

User = get_user_model()


class TestLoginUserState(TestCase):
    """Test login endpoint returns user state fields."""

    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email=f'test_c18df539@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
        )
        # Email must be verified for login
        self.user.email_verified = True
        self.user.save()

    def test_login_returns_is_mobile_verified_in_response(self):
        """Test that login response includes is_mobile_verified field."""
        response = self.client.post(
            reverse('jwt_login'),
            data={
                'email': 'test@example.com',
                'password': 'testpass123',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn('data', response_data)
        self.assertIn('user', response_data['data'])
        self.assertIn('is_mobile_verified', response_data['data']['user'])
        self.assertFalse(response_data['data']['user']['is_mobile_verified'])

    def test_login_returns_is_locked_in_response(self):
        """Test that login response includes is_locked field."""
        response = self.client.post(
            reverse('jwt_login'),
            data={
                'email': 'test@example.com',
                'password': 'testpass123',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn('data', response_data)
        self.assertIn('user', response_data['data'])
        self.assertIn('is_locked', response_data['data']['user'])
        self.assertFalse(response_data['data']['user']['is_locked'])

    def test_login_returns_is_blocked_in_response(self):
        """Test that login response includes is_blocked field."""
        response = self.client.post(
            reverse('jwt_login'),
            data={
                'email': 'test@example.com',
                'password': 'testpass123',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn('data', response_data)
        self.assertIn('user', response_data['data'])
        self.assertIn('is_blocked', response_data['data']['user'])
        self.assertFalse(response_data['data']['user']['is_blocked'])

    def test_login_returns_blocked_capabilities_in_response(self):
        """Test that login response includes blocked_capabilities field."""
        response = self.client.post(
            reverse('jwt_login'),
            data={
                'email': 'test@example.com',
                'password': 'testpass123',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn('data', response_data)
        self.assertIn('user', response_data['data'])
        self.assertIn('blocked_capabilities', response_data['data']['user'])
        self.assertEqual(response_data['data']['user']['blocked_capabilities'], [])

    def test_login_with_unverified_mobile_still_works(self):
        """Test that user with unverified mobile can still login."""
        self.user.is_mobile_verified = False
        self.user.save()

        response = self.client.post(
            reverse('jwt_login'),
            data={
                'email': 'test@example.com',
                'password': 'testpass123',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn('data', response_data)
        self.assertIn('access', response_data['data'])
        self.assertIn('refresh', response_data['data'])

    def test_login_with_blocked_capabilities_still_works(self):
        """Test that user with blocked capabilities can still login."""
        self.user.is_blocked = True
        self.user.blocked_capabilities = ['SELL', 'BUY']
        self.user.save()

        response = self.client.post(
            reverse('jwt_login'),
            data={
                'email': 'test@example.com',
                'password': 'testpass123',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn('data', response_data)
        self.assertIn('access', response_data['data'])
        self.assertIn('refresh', response_data['data'])

    def test_login_returns_correct_mobile_verified_state(self):
        """Test that login returns correct mobile verification state."""
        self.user.is_mobile_verified = True
        self.user.save()

        response = self.client.post(
            reverse('jwt_login'),
            data={
                'email': 'test@example.com',
                'password': 'testpass123',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['data']['user']['is_mobile_verified'])

    def test_login_returns_correct_blocked_capabilities(self):
        """Test that login returns correct blocked capabilities."""
        self.user.is_blocked = True
        self.user.blocked_capabilities = ['SELL', 'BUY', 'CHECKOUT']
        self.user.save()

        response = self.client.post(
            reverse('jwt_login'),
            data={
                'email': 'test@example.com',
                'password': 'testpass123',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(
            response_data['data']['user']['blocked_capabilities'],
            ['SELL', 'BUY', 'CHECKOUT']
        )

    def test_login_without_email_verification_fails(self):
        """Test that login fails when email is not verified."""
        self.user.email_verified = False
        self.user.save()

        response = self.client.post(
            reverse('jwt_login'),
            data={
                'email': 'test@example.com',
                'password': 'testpass123',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 403)

    def test_login_with_wrong_password_fails(self):
        """Test that login fails with wrong password."""
        response = self.client.post(
            reverse('jwt_login'),
            data={
                'email': 'test@example.com',
                'password': 'wrongpassword',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 401)

    def test_login_with_nonexistent_user_fails(self):
        """Test that login fails with nonexistent user."""
        response = self.client.post(
            reverse('jwt_login'),
            data={
                'email': 'nonexistent@example.com',
                'password': 'testpass123',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 401)
