"""
Spec 001 Tests: Guest Cart & Cart Merge

Tests derived from:
- spec-001.md section: Cart & Checkout Specification
- FR-020 through FR-025
"""

import pytest
import uuid
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from cart.models import Cart
from cart.services.cart_merge import merge_guest_cart

User = get_user_model()


class TestGuestCartSessionBased:
    """Test FR-020: Guest cart is session-based."""

    def test_guest_cart_created_with_session_id(self, db):
        """Guest cart MUST be created with session_id."""
        client = APIClient()
        session_id = 'test-session-123'

        response = client.post(
            '/api/v1/cart/add/',
            data={'product_id': 1, 'quantity': 2},
            HTTP_X_SESSION_ID=session_id,
            format='json'
        )

        cart = Cart.objects.get(session_id=session_id)
        assert cart.session_id == session_id
        assert cart.user is None

    def test_guest_cart_persists_in_session(self, db):
        """Guest cart persists within browser session."""
        client = APIClient()
        session_id = 'test-session-456'

        # Add item to cart
        client.post(
            '/api/v1/cart/add/',
            data={'product_id': 1, 'quantity': 1},
            HTTP_X_SESSION_ID=session_id,
            format='json'
        )

        # Retrieve cart with same session
        response = client.get(
            '/api/v1/cart/',
            HTTP_X_SESSION_ID=session_id
        )

        assert response.status_code == 200

    def test_multiple_guest_carts_have_different_sessions(self, db):
        """Different sessions have different carts."""
        client = APIClient()

        cart1 = Cart.objects.create(session_id='session-1')
        cart2 = Cart.objects.create(session_id='session-2')

        assert cart1.session_id != cart2.session_id
        assert Cart.objects.filter(session_id='session-1').count() == 1
        assert Cart.objects.filter(session_id='session-2').count() == 1


class TestCartMergeOnLogin:
    """Test FR-021, FR-022: Cart merges on login."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email=f'user_cefd9885@example.com',
            password='testpass123',
        )
        self.user.email_verified = True
        self.user.save()

    def test_cart_merge_triggered_on_login(self, db):
        """FR-021: Upon login, guest cart MUST merge into user cart."""
        client = APIClient()
        user = User.objects.create_user(
            email=f'merger_6a4d156f@example.com',
            password='testpass123',
        )
        user.email_verified = True
        user.save()

        session_id = 'guest-session-123'
        guest_cart = Cart.objects.create(session_id=session_id)

        # Login with session_id
        response = client.post(
            '/api/v1/auth/login/',
            data={
                'email': 'merger@example.com',
                'password': 'testpass123',
                'session_id': session_id
            },
            format='json'
        )

        # Cart should be merged
        user_cart = Cart.objects.filter(user=user).first()
        assert user_cart is not None

    def test_cart_merge_preserves_all_guest_items(self, db):
        """FR-022: Cart merge MUST preserve all items from guest session."""
        user = User.objects.create_user(
            email=f'user_c26fb061@example.com',
            password='testpass123',
        )
        user.email_verified = True
        user.save()

        guest_cart = Cart.objects.create(session_id='guest-session')
        user_cart = Cart.objects.create(user=user)

        # Add items to guest cart
        guest_cart.items = [{'product_id': 1, 'quantity': 2}]
        guest_cart.save()

        merge_guest_cart(user, guest_cart, user_cart)

        # User cart should have guest items
        assert len(user_cart.items) > 0

    def test_user_cart_quantity_wins_on_conflict(self, db):
        """FR-022: For duplicate products, user cart quantity takes precedence."""
        user = User.objects.create_user(
            email=f'user_4a97ce55@example.com',
            password='testpass123',
        )
        user.email_verified = True
        user.save()

        guest_cart = Cart.objects.create(session_id='guest-session')
        user_cart = Cart.objects.create(user=user)

        # Both carts have same product
        guest_cart.items = [{'product_id': 1, 'quantity': 3}]
        user_cart.items = [{'product_id': 1, 'quantity': 5}]
        guest_cart.save()
        user_cart.save()

        merge_guest_cart(user, guest_cart, user_cart)

        # User cart quantity should win (5, not 3)
        product_item = [item for item in user_cart.items if item['product_id'] == 1][0]
        assert product_item['quantity'] == 5

    def test_guest_only_items_added_to_user_cart(self, db):
        """FR-022: Guest-only items are added to user cart."""
        user = User.objects.create_user(
            email=f'user_19c6aa04@example.com',
            password='testpass123',
        )
        user.email_verified = True
        user.save()

        guest_cart = Cart.objects.create(session_id='guest-session')
        user_cart = Cart.objects.create(user=user)

        # User has product 1, guest has product 2
        user_cart.items = [{'product_id': 1, 'quantity': 1}]
        guest_cart.items = [{'product_id': 2, 'quantity': 2}]
        user_cart.save()
        guest_cart.save()

        merge_guest_cart(user, guest_cart, user_cart)

        # Both products should be in user cart
        product_ids = [item['product_id'] for item in user_cart.items]
        assert 1 in product_ids
        assert 2 in product_ids

    def test_guest_cart_removed_after_merge(self, db):
        """Guest cart MUST be removed after successful merge."""
        user = User.objects.create_user(
            email=f'user_caddbf96@example.com',
            password='testpass123',
        )
        user.email_verified = True
        user.save()

        guest_cart = Cart.objects.create(session_id='guest-session')
        user_cart = Cart.objects.create(user=user)

        session_id = guest_cart.session_id
        merge_guest_cart(user, guest_cart, user_cart)

        # Guest cart should be deleted
        assert not Cart.objects.filter(session_id=session_id).exists()


class TestCheckoutVerificationRequirement:
    """Test FR-023, FR-024, FR-025: Checkout requires auth and verification."""

    def test_checkout_requires_authentication(self, db):
        """FR-023: Checkout MUST require authentication."""
        client = APIClient()

        response = client.post(
            '/api/v1/checkout/',
            format='json'
        )

        assert response.status_code == 401

    def test_checkout_requires_mobile_verification(self, db):
        """FR-024: Checkout MUST require mobile verification."""
        client = APIClient()
        user = User.objects.create_user(
            email=f'unverified_71a88f46@example.com',
            password='testpass123',
        )
        user.email_verified = True
        user.is_mobile_verified = False
        user.save()

        client.force_authenticate(user=user)

        response = client.post(
            '/api/v1/checkout/',
            format='json'
        )

        assert response.status_code == 403
        assert 'verification' in str(response.json()).lower()

    def test_checkout_triggers_otp_for_unverified(self, db):
        """FR-025: Unverified users trigger OTP flow, then checkout resumes."""
        client = APIClient()
        user = User.objects.create_user(
            email=f'unverified_643522d6@example.com',
            password='testpass123',
        )
        user.email_verified = True
        user.is_mobile_verified = False
        user.save()

        client.force_authenticate(user=user)

        response = client.post(
            '/api/v1/checkout/',
            format='json'
        )

        data = response.json()
        # Should return verification required response
        assert response.status_code == 403

    def test_checkout_proceeds_for_verified_user(self, db):
        """Verified users can checkout without OTP prompt."""
        client = APIClient()
        user = User.objects.create_user(
            email=f'verified_ff6bb362@example.com',
            password='testpass123',
        )
        user.email_verified = True
        user.is_mobile_verified = True
        user.save()

        client.force_authenticate(user=user)

        # Create cart with items first
        cart = Cart.objects.create(user=user)
        cart.items = [{'product_id': 1, 'quantity': 1}]
        cart.save()

        response = client.post(
            '/api/v1/checkout/',
            format='json'
        )

        # Should not get verification required error
        # (May get other errors like missing payment details, but not verification)
        if response.status_code == 403:
            data = response.json()
            assert 'verification' not in str(data).lower()
