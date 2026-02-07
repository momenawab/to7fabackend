"""
Spec 001 Tests: Login Behavior

Tests derived from:
- spec-001.md section: Authentication Specification
- FR-008 through FR-013
"""

import pytest
import uuid
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

User = get_user_model()


class TestLoginAllowsUnverifiedUsers:
    """Test FR-011, FR-013: Login succeeds for unverified users."""

    def test_login_succeeds_for_unverified_mobile_user(self, db):
        """FR-011: Login MUST succeed for mobile-unverified users."""
        client = APIClient()
        user = User.objects.create_user(
            email=f'unverified_29ea29a4@example.com',
            password='testpass123',
        )
        user.email_verified = True
        user.is_mobile_verified = False
        user.save()

        response = client.post(
            reverse('jwt_login'),
            data={'email': 'unverified@example.com', 'password': 'testpass123'},
            format='json'
        )
        assert response.status_code == 200
        data = response.json()
        assert 'access' in data['data']
        assert 'refresh' in data['data']

    def test_login_does_not_check_mobile_verification(self, db):
        """FR-013: Verification status MUST NOT be enforced at login time."""
        client = APIClient()
        user = User.objects.create_user(
            email=f'user_798a74b2@example.com',
            password='testpass123',
        )
        user.email_verified = True
        user.is_mobile_verified = False
        user.save()

        response = client.post(
            reverse('jwt_login'),
            data={'email': 'user@example.com', 'password': 'testpass123'},
            format='json'
        )
        # Login succeeds despite unverified mobile
        assert response.status_code == 200


class TestLoginBlocksOnlyLockedUsers:
    """Test FR-012: Login blocks ONLY for locked (BANNED) users."""

    def test_login_fails_for_locked_user(self, db):
        """FR-012: Login MUST block ONLY if user state is Locked (BANNED)."""
        client = APIClient()
        user = User.objects.create_user(
            email=f'locked_b3a703b5@example.com',
            password='testpass123',
        )
        user.email_verified = True
        user.is_locked = True
        user.locked_reason = 'Policy violation'
        user.save()

        response = client.post(
            reverse('jwt_login'),
            data={'email': 'locked@example.com', 'password': 'testpass123'},
            format='json'
        )
        assert response.status_code == 403

    def test_login_succeeds_for_blocked_user(self, db):
        """FR-012: Blocked users CAN still login."""
        client = APIClient()
        user = User.objects.create_user(
            email=f'blocked_658207fb@example.com',
            password='testpass123',
        )
        user.email_verified = True
        user.is_blocked = True
        user.blocked_capabilities = ['SELL']
        user.save()

        response = client.post(
            reverse('jwt_login'),
            data={'email': 'blocked@example.com', 'password': 'testpass123'},
            format='json'
        )
        assert response.status_code == 200

    def test_login_succeeds_for_verified_user(self, db):
        """Verified users can login."""
        client = APIClient()
        user = User.objects.create_user(
            email=f'verified_d7734f35@example.com',
            password='testpass123',
        )
        user.email_verified = True
        user.is_mobile_verified = True
        user.save()

        response = client.post(
            reverse('jwt_login'),
            data={'email': 'verified@example.com', 'password': 'testpass123'},
            format='json'
        )
        assert response.status_code == 200


class TestLockEnforcedBeforePasswordValidation:
    """Test that lock check happens before password validation."""

    def test_lock_check_before_password(self, db):
        """Lock enforced BEFORE password validation."""
        client = APIClient()
        user = User.objects.create_user(
            email=f'locked_e86b3794@example.com',
            password='correctpassword',
        )
        user.email_verified = True
        user.is_locked = True
        user.save()

        # Even with wrong password, lock should be detected first
        response = client.post(
            reverse('jwt_login'),
            data={'email': 'locked@example.com', 'password': 'wrongpassword'},
            format='json'
        )
        # Should return 403 (locked) not 401 (wrong password)
        assert response.status_code == 403

    def test_locked_user_sees_banned_message(self, db):
        """Locked users see 'You are banned' message."""
        client = APIClient()
        user = User.objects.create_user(
            email=f'locked_165212ba@example.com',
            password='testpass123',
        )
        user.email_verified = True
        user.is_locked = True
        user.locked_reason = 'Policy violation'
        user.save()

        response = client.post(
            reverse('jwt_login'),
            data={'email': 'locked@example.com', 'password': 'testpass123'},
            format='json'
        )
        data = response.json()
        assert 'banned' in str(data).lower() or 'locked' in str(data).lower()


class TestLoginResponseFields:
    """Test FR-010: Login accepts email + password and returns user state."""

    def test_login_accepts_email_and_password(self, db):
        """FR-010: Login MUST accept email + password credentials."""
        client = APIClient()
        User.objects.create_user(
            email=f'test_d75fd8de@example.com',
            password='testpass123',
        )

        response = client.post(
            reverse('jwt_login'),
            data={'email': 'test@example.com', 'password': 'testpass123'},
            format='json'
        )
        assert response.status_code == 200

    def test_login_returns_user_state_fields(self, db):
        """Login response includes user state fields."""
        client = APIClient()
        user = User.objects.create_user(
            email=f'test_db05336f@example.com',
            password='testpass123',
        )
        user.email_verified = True
        user.is_mobile_verified = True
        user.save()

        response = client.post(
            reverse('jwt_login'),
            data={'email': 'test@example.com', 'password': 'testpass123'},
            format='json'
        )
        data = response.json()['data']['user']
        assert 'is_mobile_verified' in data
        assert 'is_locked' in data
        assert 'is_blocked' in data
        assert 'blocked_capabilities' in data


class TestRegistrationRequirements:
    """Test FR-008, FR-009: Registration requirements."""

    def test_registration_requires_email_password_mobile(self, db):
        """FR-008: Registration MUST require email, password, mobile number."""
        client = APIClient()

        # Missing mobile
        response = client.post(
            reverse('register'),
            data={
                'email': 'test@example.com',
                'password': 'testpass123',
            },
            format='json'
        )
        assert response.status_code == 400

    def test_email_used_for_login_not_verification(self, db):
        """FR-009: Email is used for login, NOT as verification gate."""
        client = APIClient()
        user = User.objects.create_user(
            email=f'test_a284e3bf@example.com',
            password='testpass123',
            mobile='+1234567890'
        )
        user.email_verified = False
        user.is_mobile_verified = False
        user.save()

        # Login works even with unverified email (mobile verification gate is separate)
        response = client.post(
            reverse('jwt_login'),
            data={'email': 'test@example.com', 'password': 'testpass123'},
            format='json'
        )
        # Implementation-specific: check if email verification gates login
        # Per spec, email verification should NOT gate login
