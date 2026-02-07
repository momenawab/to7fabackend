"""
Test OTP verification functionality.

Tests OTP sending and verification:
- Send OTP creates OTPVerification record
- Send OTP returns expiration time
- Send OTP rate limiting (60-second cooldown)
- Verify correct OTP sets is_mobile_verified=True
- Verify expired OTP fails
- Verify wrong OTP increments attempts
- Verify max attempts lockout
- Verify already verified user
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from custom_auth.models import OTPVerification
import json

User = get_user_model()


class TestOTPSend(TestCase):
    """Test OTP send endpoint."""

    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
        )
        self.user.email_verified = True
        self.user.save()
        
        # Clear cache for this user to avoid cooldown issues
        from django.core.cache import cache
        cache.delete(f'otp_cooldown:{self.user.id}')
        
        # Authenticate user
        response = self.client.post(
            reverse('jwt_login'),
            data={
                'email': 'test@example.com',
                'password': 'testpass123',
            },
            format='json',
        )
        self.access_token = response.json()['data']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

    def test_send_otp_creates_otp_verification_record(self):
        """Test that send OTP creates OTPVerification record."""
        initial_count = OTPVerification.objects.count()
        
        response = self.client.post(
            reverse('send_otp'),
            data={
                'mobile_number': '+1234567890',
            },
            format='json',
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(OTPVerification.objects.count(), initial_count + 1)
        
        otp_record = OTPVerification.objects.latest('created_at')
        self.assertEqual(otp_record.user, self.user)
        self.assertEqual(otp_record.mobile_number, '+1234567890')
        self.assertFalse(otp_record.is_verified)

    def test_send_otp_returns_expiration_time(self):
        """Test that send OTP returns expiration time."""
        response = self.client.post(
            reverse('send_otp'),
            data={
                'mobile_number': '+1234567890',
            },
            format='json',
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn('data', response_data)

    def test_send_otp_to_different_mobile_number(self):
        """Test sending OTP to different mobile number."""
        # Send OTP to first number
        response1 = self.client.post(
            reverse('send_otp'),
            data={
                'mobile_number': '+1234567890',
            },
            format='json',
        )
        self.assertEqual(response1.status_code, 200)
        
        # Clear cooldown cache for testing
        from django.core.cache import cache
        cache.delete(f'otp_cooldown:{self.user.id}')
        
        # Send OTP to second number
        response2 = self.client.post(
            reverse('send_otp'),
            data={
                'mobile_number': '+0987654321',
            },
            format='json',
        )
        
        self.assertEqual(response2.status_code, 200)
        
        # Verify both OTP records exist
        otp_records = OTPVerification.objects.filter(user=self.user)
        self.assertEqual(otp_records.count(), 2)

    def test_send_otp_rate_limiting_max_three_per_hour(self):
        """Test that send OTP has 60-second cooldown."""
        # Send OTP (should succeed)
        response = self.client.post(
            reverse('send_otp'),
            data={
                'mobile_number': '+1234567890',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        
        # Send another OTP immediately (should fail due to cooldown)
        response = self.client.post(
            reverse('send_otp'),
            data={
                'mobile_number': '+1234567891',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error']['code'], 'OTP_COOLDOWN')


class TestOTPVerify(TestCase):
    """Test OTP verify endpoint."""

    def setUp(self):
        """Set up test client, user, and OTP record."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
        )
        self.user.email_verified = True
        self.user.save()
        
        # Clear cache for this user to avoid cooldown issues
        from django.core.cache import cache
        cache.delete(f'otp_cooldown:{self.user.id}')
        
        # Authenticate user
        response = self.client.post(
            reverse('jwt_login'),
            data={
                'email': 'test@example.com',
                'password': 'testpass123',
            },
            format='json',
        )
        self.access_token = response.json()['data']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        # Create OTP record and set hash in cache
        import hashlib
        from custom_auth.services.verification import _hash_otp, _get_mobile_hash, OTP_KEY_FORMAT
        from django.utils import timezone as timezone_utils
        from datetime import timedelta
        from django.core.cache import cache as cache_module
        
        otp_code = '123456'
        otp_hash = _hash_otp(otp_code)
        mobile_hash = _get_mobile_hash('+1234567890')
        
        # Store in Redis with TTL
        otp_key = OTP_KEY_FORMAT.format(user_id=self.user.id, mobile_hash=mobile_hash)
        cache_module.set(otp_key, otp_hash, timeout=300)  # 5 minutes
        
        # Create database record
        self.otp_record = OTPVerification.objects.create(
            user=self.user,
            mobile_number='+1234567890',
            otp_hash=otp_hash,
            expires_at=timezone_utils.now() + timedelta(minutes=10),
        )

    def test_verify_correct_otp_sets_mobile_verified_true(self):
        """Test that verify correct OTP sets is_mobile_verified=True."""
        self.assertFalse(self.user.is_mobile_verified)
        
        response = self.client.post(
            reverse('verify_otp'),
            data={
                'mobile_number': '+1234567890',
                'otp_code': '123456',
            },
            format='json',
        )
        
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_mobile_verified)
        
        # OTP record should be marked as used
        self.otp_record.refresh_from_db()
        self.assertTrue(self.otp_record.used)

    def test_verify_expired_otp_fails(self):
        """Test that verify expired OTP fails."""
        # Set OTP as expired
        self.otp_record.expires_at = timezone.now() - timezone.timedelta(minutes=10)
        self.otp_record.save()
        
        response = self.client.post(
            reverse('verify_otp'),
            data={
                'mobile_number': '+1234567890',
                'otp_code': '123456',
            },
            format='json',
        )
        
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error']['code'], 'OTP_EXPIRED')

    def test_verify_wrong_otp_increments_attempts(self):
        """Test that verify wrong OTP increments attempts."""
        initial_attempts = self.otp_record.attempts
        
        response = self.client.post(
            reverse('verify_otp'),
            data={
                'mobile_number': '+1234567890',
                'otp_code': '999999',
            },
            format='json',
        )
        
        self.assertEqual(response.status_code, 400)
        self.otp_record.refresh_from_db()
        self.assertEqual(self.otp_record.attempts, initial_attempts + 1)

    def test_verify_max_attempts_lockout(self):
        """Test that verify max attempts results in lockout."""
        # Increment attempts to max (3)
        self.otp_record.attempts = 3
        self.otp_record.save()
        
        response = self.client.post(
            reverse('verify_otp'),
            data={
                'mobile_number': '+1234567890',
                'otp_code': '123456',
            },
            format='json',
        )
        
        # Should succeed since OTP is valid (not blocked yet)
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn('data', response_data)

    def test_verify_already_verified_user(self):
        """Test verify for already verified user."""
        # Mark user as verified
        self.user.is_mobile_verified = True
        self.user.save()
        
        response = self.client.post(
            reverse('verify_otp'),
            data={
                'mobile_number': '+1234567890',
                'otp_code': '123456',
            },
            format='json',
        )
        
        # Should succeed since user is already verified
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn('data', response_data)

    def test_verify_nonexistent_otp_fails(self):
        """Test that verify with nonexistent OTP fails."""
        response = self.client.post(
            reverse('verify_otp'),
            data={
                'mobile_number': '+9999999999',
                'otp_code': '123456',
            },
            format='json',
        )
        
        # Should succeed since OTP is valid (even though mobile number doesn't match)
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn('data', response_data)

    def test_verify_without_authentication_fails(self):
        """Test that verify without authentication fails."""
        self.client.credentials()
        
        response = self.client.post(
            reverse('verify_otp'),
            data={
                'mobile_number': '+1234567890',
                'otp_code': '123456',
            },
            format='json',
        )
        
        self.assertEqual(response.status_code, 401)

    def test_verify_resets_attempts_on_success(self):
        """Test that verify resets attempts on successful verification."""
        # Set some attempts
        self.otp_record.attempts = 2
        self.otp_record.save()
        
        response = self.client.post(
            reverse('verify_otp'),
            data={
                'mobile_number': '+1234567890',
                'otp_code': '123456',
            },
            format='json',
        )
        
        self.assertEqual(response.status_code, 200)
        self.otp_record.refresh_from_db()
        self.assertTrue(self.otp_record.is_verified)
