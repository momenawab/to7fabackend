"""
Test lock enforcement on login.

Tests that locked users cannot login and that lock check happens
before password check.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

User = get_user_model()


class TestLockEnforcement(TestCase):
    """Test lock enforcement on login endpoint."""

    def setUp(self):
        """Set up test client and users."""
        self.client = APIClient()
        
        # Create a locked user
        self.locked_user = User.objects.create_user(
            email='locked@example.com',
            password='testpass123',
            first_name='Locked',
            last_name='User',
        )
        self.locked_user.email_verified = True
        self.locked_user.is_locked = True
        self.locked_user.locked_reason = 'Too many failed attempts'
        self.locked_user.locked_at = timezone.now()
        self.locked_user.save()

        # Create an unlocked user
        self.unlocked_user = User.objects.create_user(
            email='unlocked@example.com',
            password='testpass123',
            first_name='Unlocked',
            last_name='User',
        )
        self.unlocked_user.email_verified = True
        self.unlocked_user.save()

    def test_locked_user_cannot_login(self):
        """Test that locked user cannot login (403 USER_LOCKED)."""
        response = self.client.post(
            reverse('jwt_login'),
            data={
                'email': 'locked@example.com',
                'password': 'testpass123',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 403)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertIn('code', response_data['error'])
        self.assertEqual(response_data['error']['code'], 'USER_LOCKED')

    def test_locked_user_with_correct_password_still_blocked(self):
        """Test that locked user with correct password is still blocked."""
        response = self.client.post(
            reverse('jwt_login'),
            data={
                'email': 'locked@example.com',
                'password': 'testpass123',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 403)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error']['code'], 'USER_LOCKED')

    def test_unlocked_user_can_login_normally(self):
        """Test that unlocked user can login normally."""
        response = self.client.post(
            reverse('jwt_login'),
            data={
                'email': 'unlocked@example.com',
                'password': 'testpass123',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn('data', response_data)
        self.assertIn('access', response_data['data'])
        self.assertIn('refresh', response_data['data'])

    def test_lock_check_happens_before_password_check(self):
        """Test that lock check happens before password check."""
        # Even with wrong password, locked user should get USER_LOCKED error
        response = self.client.post(
            reverse('jwt_login'),
            data={
                'email': 'locked@example.com',
                'password': 'wrongpassword',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 403)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error']['code'], 'USER_LOCKED')
        # Should not be AUTHENTICATION_FAILED
        self.assertNotEqual(response_data['error']['code'], 'AUTHENTICATION_FAILED')

    def test_locked_user_with_wrong_password_still_gets_locked_error(self):
        """Test that locked user with wrong password still gets locked error."""
        response = self.client.post(
            reverse('jwt_login'),
            data={
                'email': 'locked@example.com',
                'password': 'wrongpassword',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 403)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error']['code'], 'USER_LOCKED')

    def test_unlocked_user_with_wrong_password_fails_with_auth_error(self):
        """Test that unlocked user with wrong password fails with auth error."""
        response = self.client.post(
            reverse('jwt_login'),
            data={
                'email': 'unlocked@example.com',
                'password': 'wrongpassword',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 401)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error']['code'], 'INVALID_CREDENTIALS')

    def test_locked_user_response_includes_locked_reason(self):
        """Test that locked user error response includes locked reason."""
        response = self.client.post(
            reverse('jwt_login'),
            data={
                'email': 'locked@example.com',
                'password': 'testpass123',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 403)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertIn('message', response_data['error'])
        # The message should contain information about lock
        message = response_data['error']['message'].lower()
        self.assertTrue('banned' in message or 'lock' in message)

    def test_user_can_be_unlocked_and_login(self):
        """Test that user can be unlocked and then login."""
        # Lock user
        self.unlocked_user.is_locked = True
        self.unlocked_user.locked_reason = 'Test lock'
        self.unlocked_user.locked_at = timezone.now()
        self.unlocked_user.save()

        # Try to login (should fail)
        response = self.client.post(
            reverse('jwt_login'),
            data={
                'email': 'unlocked@example.com',
                'password': 'testpass123',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 403)

        # Unlock user
        self.unlocked_user.is_locked = False
        self.unlocked_user.locked_reason = None
        self.unlocked_user.locked_at = None
        self.unlocked_user.save()

        # Try to login again (should succeed)
        response = self.client.post(
            reverse('jwt_login'),
            data={
                'email': 'unlocked@example.com',
                'password': 'testpass123',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn('data', response_data)
        self.assertIn('access', response_data['data'])

    def test_locked_user_without_email_verified_still_blocked(self):
        """Test that locked user without email verified is still blocked."""
        self.locked_user.email_verified = False
        self.locked_user.save()

        response = self.client.post(
            reverse('jwt_login'),
            data={
                'email': 'locked@example.com',
                'password': 'testpass123',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 403)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error']['code'], 'USER_LOCKED')


class TestLockEnforcementMiddleware(TestCase):
    """Test LockEnforcementMiddleware blocks locked users globally."""

    def setUp(self):
        """Set up test client and users."""
        self.client = APIClient()

        # Create a locked user
        self.locked_user = User.objects.create_user(
            email='locked@example.com',
            password='testpass123',
            first_name='Locked',
            last_name='User',
        )
        self.locked_user.email_verified = True
        self.locked_user.is_locked = True
        self.locked_user.locked_reason = 'Too many failed attempts'
        self.locked_user.locked_at = timezone.now()
        self.locked_user.save()

        # Create an unlocked user
        self.unlocked_user = User.objects.create_user(
            email='unlocked@example.com',
            password='testpass123',
            first_name='Unlocked',
            last_name='User',
        )
        self.unlocked_user.email_verified = True
        self.unlocked_user.save()

        # Get tokens for both users
        from rest_framework_simplejwt.tokens import RefreshToken

        self.locked_token = str(RefreshToken.for_user(self.locked_user).access_token)
        self.unlocked_token = str(RefreshToken.for_user(self.unlocked_user).access_token)

    def test_middleware_blocks_locked_user(self):
        """Test that middleware blocks locked user from any endpoint."""
        response = self.client.get(
            '/api/v1/cart/',
            HTTP_AUTHORIZATION=f'Bearer {self.locked_token}',
        )
        self.assertEqual(response.status_code, 403)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertIn('code', response_data['error'])
        self.assertEqual(response_data['error']['code'], 'USER_LOCKED')

    def test_middleware_blocks_locked_user_from_all_endpoints(self):
        """Test that middleware blocks locked user from multiple endpoints."""
        endpoints = [
            '/api/v1/cart/',
            '/api/v1/products/',
            '/api/v1/orders/',
        ]

        for endpoint in endpoints:
            response = self.client.get(
                endpoint,
                HTTP_AUTHORIZATION=f'Bearer {self.locked_token}',
            )
            self.assertEqual(response.status_code, 403, f'Failed for endpoint: {endpoint}')
            response_data = response.json()
            self.assertIn('error', response_data)
            self.assertEqual(response_data['error']['code'], 'USER_LOCKED')

    def test_middleware_allows_unlocked_user(self):
        """Test that middleware allows unlocked user to access endpoints."""
        response = self.client.get(
            '/api/v1/cart/',
            HTTP_AUTHORIZATION=f'Bearer {self.unlocked_token}',
        )
        # Should not get 403 USER_LOCKED
        self.assertNotEqual(response.status_code, 403)

    def test_middleware_does_not_block_unauthenticated_requests(self):
        """Test that middleware does not block unauthenticated requests."""
        response = self.client.get('/api/v1/products/')
        # Should not get 403 USER_LOCKED for unauthenticated requests
        self.assertNotEqual(response.status_code, 403)

    def test_middleware_returns_correct_error_message(self):
        """Test that middleware returns correct error message for locked users."""
        response = self.client.get(
            '/api/v1/cart/',
            HTTP_AUTHORIZATION=f'Bearer {self.locked_token}',
        )
        self.assertEqual(response.status_code, 403)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertIn('message', response_data['error'])
        self.assertIn('banned', response_data['error']['message'].lower())

    def test_middleware_blocks_locked_user_mid_transaction(self):
        """Test that middleware blocks locked user mid-transaction (payment)."""
        # Simulate a payment request
        response = self.client.post(
            '/api/v1/orders/checkout/',
            HTTP_AUTHORIZATION=f'Bearer {self.locked_token}',
            format='json',
        )
        self.assertEqual(response.status_code, 403)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error']['code'], 'USER_LOCKED')

    def test_middleware_blocks_locked_user_from_post_requests(self):
        """Test that middleware blocks locked user from POST requests."""
        response = self.client.post(
            '/api/v1/cart/add/',
            HTTP_AUTHORIZATION=f'Bearer {self.locked_token}',
            data={'product_id': 1, 'quantity': 1},
            format='json',
        )
        self.assertEqual(response.status_code, 403)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error']['code'], 'USER_LOCKED')


class TestBlockEnforcement(TestCase):
    """Test block enforcement for business restrictions."""

    def setUp(self):
        """Set up test client and users."""
        # Use api_client fixture from conftest.py
        from django.test import Client
        self.client = Client()
        # Set HTTP_HOST to 'testserver' to match ALLOWED_HOSTS
        self.client.defaults['HTTP_HOST'] = 'testserver'

        # Create a blocked seller (blocked from SELL capability)
        self.blocked_seller = User.objects.create_user(
            email='blocked_seller@example.com',
            password='testpass123',
            first_name='Blocked',
            last_name='Seller',
        )
        self.blocked_seller.email_verified = True
        self.blocked_seller.is_blocked = True
        self.blocked_seller.blocked_capabilities = ['SELL']
        self.blocked_seller.blocked_reason = 'Policy violation'
        self.blocked_seller.save()

        # Create an unblocked seller
        self.unblocked_seller = User.objects.create_user(
            email='unblocked_seller@example.com',
            password='testpass123',
            first_name='Unblocked',
            last_name='Seller',
        )
        self.unblocked_seller.email_verified = True
        self.unblocked_seller.save()

        # Create a blocked customer (blocked from WITHDRAW capability)
        self.blocked_customer = User.objects.create_user(
            email='blocked_customer@example.com',
            password='testpass123',
            first_name='Blocked',
            last_name='Customer',
        )
        self.blocked_customer.email_verified = True
        self.blocked_customer.is_blocked = True
        self.blocked_customer.blocked_capabilities = ['WITHDRAW']
        self.blocked_customer.blocked_reason = 'Withdrawal restriction'
        self.blocked_customer.save()

        # Get tokens for all users
        from rest_framework_simplejwt.tokens import RefreshToken

        self.blocked_seller_token = str(RefreshToken.for_user(self.blocked_seller).access_token)
        self.unblocked_seller_token = str(RefreshToken.for_user(self.unblocked_seller).access_token)
        self.blocked_customer_token = str(RefreshToken.for_user(self.blocked_customer).access_token)

    def test_blocked_user_can_access_customer_endpoints(self):
        """Test that blocked user can still access customer endpoints."""
        # Customer endpoints should work for blocked users
        customer_endpoints = [
            '/api/v1/products/',
            '/api/v1/cart/',
        ]

        for endpoint in customer_endpoints:
            response = self.client.get(
                endpoint,
                HTTP_AUTHORIZATION=f'Bearer {self.blocked_seller_token}',
            )
            # Should not get CAPABILITY_BLOCKED for customer endpoints
            self.assertNotEqual(response.status_code, 403, f'Failed for endpoint: {endpoint}')

    def test_blocked_user_denied_from_seller_endpoints(self):
        """Test that blocked user is denied from seller endpoints."""
        # Attempt to access seller-specific endpoint
        response = self.client.post(
            '/api/v1/products/',
            HTTP_AUTHORIZATION=f'Bearer {self.blocked_seller_token}',
            data={
                'name': 'Test Product',
                'description': 'Test product description',
                'price': 100,
            },
            format='json',
        )
        # Should get CAPABILITY_BLOCKED error
        self.assertEqual(response.status_code, 403)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error']['code'], 'CAPABILITY_BLOCKED')

    def test_unblocked_user_can_access_seller_endpoints(self):
        """Test that unblocked user can access seller endpoints."""
        response = self.client.post(
            '/api/v1/products/',
            HTTP_AUTHORIZATION=f'Bearer {self.unblocked_seller_token}',
            data={'name': 'Test Product', 'price': 100},
            format='json',
        )
        # Should not get CAPABILITY_BLOCKED error
        # May get other errors (validation, auth), but not CAPABILITY_BLOCKED
        if response.status_code == 403:
            response_data = response.json()
            self.assertNotIn('error', response_data)
            self.assertNotEqual(response_data.get('error', {}).get('code'), 'CAPABILITY_BLOCKED')

    def test_blocked_capabilities_check(self):
        """Test that blocked_capabilities check works correctly."""
        from custom_auth.services.lock_block import check_capability_blocked, CapabilityCode

        # Test blocked seller
        is_sell_blocked = check_capability_blocked(self.blocked_seller, CapabilityCode.SELL)
        self.assertTrue(is_sell_blocked)

        # Test unblocked seller
        is_sell_unblocked = check_capability_blocked(self.unblocked_seller, CapabilityCode.SELL)
        self.assertFalse(is_sell_unblocked)

        # Test blocked customer for WITHDRAW
        is_withdraw_blocked = check_capability_blocked(self.blocked_customer, CapabilityCode.WITHDRAW)
        self.assertTrue(is_withdraw_blocked)

        # Test blocked customer for other capabilities (not blocked)
        is_create_product_blocked = check_capability_blocked(self.blocked_customer, CapabilityCode.CREATE_PRODUCT)
        self.assertFalse(is_create_product_blocked)

    def test_invalid_capability_raises_error(self):
        """Test that invalid capability code raises ValueError."""
        from custom_auth.services.lock_block import check_capability_blocked

        with self.assertRaises(ValueError) as context:
            check_capability_blocked(self.blocked_seller, 'INVALID_CAPABILITY')
        self.assertIn('Invalid capability code', str(context.exception))


class TestSellerApplicationBlockEnforcement(TestCase):
    """Test block enforcement for seller application status changes."""

    def setUp(self):
        """Set up test client and users."""
        from django.test import Client
        self.client = Client()
        self.client.defaults['HTTP_HOST'] = 'testserver'

        # Create a customer user with pending seller application
        self.pending_applicant = User.objects.create_user(
            email='pending@example.com',
            password='testpass123',
            first_name='Pending',
            last_name='Applicant',
        )
        self.pending_applicant.email_verified = True
        self.pending_applicant.save()

        # Create a customer user with approved seller application
        self.approved_seller = User.objects.create_user(
            email='approved@example.com',
            password='testpass123',
            first_name='Approved',
            last_name='Seller',
        )
        self.approved_seller.email_verified = True
        self.approved_seller.user_type = 'artist'
        self.approved_seller.save()

        # Create a customer user with rejected seller application
        self.rejected_applicant = User.objects.create_user(
            email='rejected@example.com',
            password='testpass123',
            first_name='Rejected',
            last_name='Applicant',
        )
        self.rejected_applicant.email_verified = True
        self.rejected_applicant.is_blocked = True
        self.rejected_applicant.blocked_capabilities = ['SELL']
        self.rejected_applicant.blocked_reason = 'Application rejected'
        self.rejected_applicant.save()

        # Create seller applications
        from custom_auth.models import SellerApplication

        self.pending_application = SellerApplication.objects.create(
            user=self.pending_applicant,
            seller_type='artist',
            status='pending',
            business_name='Pending Artist Business',
            description='Test pending application',
            phone_number='+201234567890',
        )

        self.approved_application = SellerApplication.objects.create(
            user=self.approved_seller,
            seller_type='artist',
            status='approved',
            business_name='Approved Artist Business',
            description='Test approved application',
            phone_number='+201234567891',
        )

        self.rejected_application = SellerApplication.objects.create(
            user=self.rejected_applicant,
            seller_type='artist',
            status='rejected',
            business_name='Rejected Artist Business',
            description='Test rejected application',
            phone_number='+201234567892',
            rejection_reason='Portfolio quality insufficient',
        )

        # Get tokens
        from rest_framework_simplejwt.tokens import RefreshToken

        self.pending_token = str(RefreshToken.for_user(self.pending_applicant).access_token)
        self.approved_token = str(RefreshToken.for_user(self.approved_seller).access_token)
        self.rejected_token = str(RefreshToken.for_user(self.rejected_applicant).access_token)

    def test_pending_application_blocks_seller_features(self):
        """Test that pending seller application blocks seller features."""
        # Attempt to access seller-specific endpoint (create product)
        response = self.client.post(
            '/api/v1/products/',
            HTTP_AUTHORIZATION=f'Bearer {self.pending_token}',
            data={
                'name': 'Test Product',
                'description': 'Test product description',
                'price': 100,
            },
            format='json',
        )
        # Should get CAPABILITY_BLOCKED error
        self.assertEqual(response.status_code, 403)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error']['code'], 'CAPABILITY_BLOCKED')

    def test_pending_applicant_can_access_customer_features(self):
        """Test that pending applicant can still access customer features."""
        # Customer endpoints should work for pending applicants
        customer_endpoints = [
            '/api/v1/products/',
            '/api/v1/cart/',
        ]

        for endpoint in customer_endpoints:
            response = self.client.get(
                endpoint,
                HTTP_AUTHORIZATION=f'Bearer {self.pending_token}',
            )
            # Should not get CAPABILITY_BLOCKED for customer endpoints
            self.assertNotEqual(response.status_code, 403, f'Failed for endpoint: {endpoint}')

    def test_approved_application_unlocks_seller_features(self):
        """Test that approved seller application unlocks seller features."""
        # Attempt to access seller-specific endpoint (create product)
        response = self.client.post(
            '/api/v1/products/',
            HTTP_AUTHORIZATION=f'Bearer {self.approved_token}',
            data={
                'name': 'Test Product',
                'description': 'Test product description',
                'price': 100,
            },
            format='json',
        )
        # Should not get CAPABILITY_BLOCKED error
        # May get other errors (validation, auth), but not CAPABILITY_BLOCKED
        if response.status_code == 403:
            response_data = response.json()
            self.assertNotEqual(response_data.get('error', {}).get('code'), 'CAPABILITY_BLOCKED')

    def test_rejected_application_blocks_seller_features(self):
        """Test that rejected seller application blocks seller features."""
        # Attempt to access seller-specific endpoint (create product)
        response = self.client.post(
            '/api/v1/products/',
            HTTP_AUTHORIZATION=f'Bearer {self.rejected_token}',
            data={
                'name': 'Test Product',
                'description': 'Test product description',
                'price': 100,
            },
            format='json',
        )
        # Should get CAPABILITY_BLOCKED error
        self.assertEqual(response.status_code, 403)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error']['code'], 'CAPABILITY_BLOCKED')

    def test_rejected_applicant_can_access_customer_features(self):
        """Test that rejected applicant can still access customer features."""
        # Customer endpoints should work for rejected applicants
        customer_endpoints = [
            '/api/v1/products/',
            '/api/v1/cart/',
        ]

        for endpoint in customer_endpoints:
            response = self.client.get(
                endpoint,
                HTTP_AUTHORIZATION=f'Bearer {self.rejected_token}',
            )
            # Should not get CAPABILITY_BLOCKED for customer endpoints
            self.assertNotEqual(response.status_code, 403, f'Failed for endpoint: {endpoint}')

    def test_pending_applicant_has_blocked_capabilities(self):
        """Test that pending applicant has SELL capability blocked."""
        from custom_auth.services.lock_block import check_capability_blocked, CapabilityCode

        is_sell_blocked = check_capability_blocked(self.pending_applicant, CapabilityCode.SELL)
        self.assertTrue(is_sell_blocked)

        # Should not be blocked from other capabilities
        is_withdraw_blocked = check_capability_blocked(self.pending_applicant, CapabilityCode.WITHDRAW)
        self.assertFalse(is_withdraw_blocked)

    def test_approved_seller_has_no_blocked_capabilities(self):
        """Test that approved seller has no blocked capabilities."""
        from custom_auth.services.lock_block import check_capability_blocked, CapabilityCode

        is_sell_blocked = check_capability_blocked(self.approved_seller, CapabilityCode.SELL)
        self.assertFalse(is_sell_blocked)

        is_withdraw_blocked = check_capability_blocked(self.approved_seller, CapabilityCode.WITHDRAW)
        self.assertFalse(is_withdraw_blocked)

    def test_rejected_applicant_has_sell_capability_blocked(self):
        """Test that rejected applicant has SELL capability blocked."""
        from custom_auth.services.lock_block import check_capability_blocked, CapabilityCode

        is_sell_blocked = check_capability_blocked(self.rejected_applicant, CapabilityCode.SELL)
        self.assertTrue(is_sell_blocked)
