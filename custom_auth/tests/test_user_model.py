"""
Test User model extensions for user state logic.

Tests all new fields added to the User model:
- is_mobile_verified
- is_locked
- locked_reason
- locked_at
- is_blocked
- blocked_reason
- blocked_capabilities
- email_verified
- failed_login_attempts
- locked_until
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class TestUserModelExtensions(TestCase):
    """Test User model extensions for user state management."""

    def setUp(self):
        """Set up test user."""
        self.user = User.objects.create_user(
            email=f'test_1f58e114@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
        )

    def test_default_is_mobile_verified_is_false(self):
        """Test that is_mobile_verified defaults to False."""
        self.assertFalse(self.user.is_mobile_verified)

    def test_default_is_locked_is_false(self):
        """Test that is_locked defaults to False."""
        self.assertFalse(self.user.is_locked)

    def test_default_locked_reason_is_none(self):
        """Test that locked_reason defaults to None."""
        self.assertIsNone(self.user.locked_reason)

    def test_default_locked_at_is_none(self):
        """Test that locked_at defaults to None."""
        self.assertIsNone(self.user.locked_at)

    def test_default_is_blocked_is_false(self):
        """Test that is_blocked defaults to False."""
        self.assertFalse(self.user.is_blocked)

    def test_default_blocked_reason_is_none(self):
        """Test that blocked_reason defaults to None."""
        self.assertIsNone(self.user.blocked_reason)

    def test_default_blocked_capabilities_is_empty_list(self):
        """Test that blocked_capabilities defaults to empty list."""
        self.assertEqual(self.user.blocked_capabilities, [])

    def test_default_email_verified_is_false(self):
        """Test that email_verified defaults to False."""
        self.assertFalse(self.user.email_verified)

    def test_default_failed_login_attempts_is_zero(self):
        """Test that failed_login_attempts defaults to 0."""
        self.assertEqual(self.user.failed_login_attempts, 0)

    def test_default_locked_until_is_none(self):
        """Test that locked_until defaults to None."""
        self.assertIsNone(self.user.locked_until)

    def test_can_set_is_mobile_verified_to_true(self):
        """Test setting is_mobile_verified to True."""
        self.user.is_mobile_verified = True
        self.user.save()
        self.assertTrue(self.user.is_mobile_verified)

    def test_can_set_is_locked_to_true(self):
        """Test setting is_locked to True."""
        self.user.is_locked = True
        self.user.locked_reason = 'Too many failed attempts'
        self.user.locked_at = timezone.now()
        self.user.save()
        self.assertTrue(self.user.is_locked)
        self.assertEqual(self.user.locked_reason, 'Too many failed attempts')
        self.assertIsNotNone(self.user.locked_at)

    def test_can_set_is_blocked_to_true(self):
        """Test setting is_blocked to True."""
        self.user.is_blocked = True
        self.user.blocked_reason = 'Violation of terms'
        self.user.blocked_capabilities = ['SELL', 'BUY']
        self.user.save()
        self.assertTrue(self.user.is_blocked)
        self.assertEqual(self.user.blocked_reason, 'Violation of terms')
        self.assertEqual(self.user.blocked_capabilities, ['SELL', 'BUY'])

    def test_can_set_email_verified_to_true(self):
        """Test setting email_verified to True."""
        self.user.email_verified = True
        self.user.save()
        self.assertTrue(self.user.email_verified)

    def test_can_increment_failed_login_attempts(self):
        """Test incrementing failed_login_attempts."""
        self.user.failed_login_attempts = 3
        self.user.save()
        self.assertEqual(self.user.failed_login_attempts, 3)

    def test_can_set_locked_until(self):
        """Test setting locked_until timestamp."""
        future_time = timezone.now() + timezone.timedelta(hours=1)
        self.user.locked_until = future_time
        self.user.save()
        self.assertIsNotNone(self.user.locked_until)

    def test_blocked_capabilities_accepts_list(self):
        """Test that blocked_capabilities accepts a list."""
        capabilities = ['SELL', 'BUY', 'CHECKOUT']
        self.user.blocked_capabilities = capabilities
        self.user.save()
        self.assertEqual(self.user.blocked_capabilities, capabilities)

    def test_blocked_capabilities_can_be_empty_list(self):
        """Test that blocked_capabilities can be empty list."""
        self.user.blocked_capabilities = []
        self.user.save()
        self.assertEqual(self.user.blocked_capabilities, [])

    def test_multiple_users_have_independent_state(self):
        """Test that multiple users have independent state fields."""
        user2 = User.objects.create_user(
            email='test2@example.com',
            password='testpass123',
        )
        
        # Set different states for each user
        self.user.is_locked = True
        self.user.save()
        
        user2.is_locked = False
        user2.is_mobile_verified = True
        user2.save()
        
        # Verify independence
        self.assertTrue(self.user.is_locked)
        self.assertFalse(self.user.is_mobile_verified)
        self.assertFalse(user2.is_locked)
        self.assertTrue(user2.is_mobile_verified)
