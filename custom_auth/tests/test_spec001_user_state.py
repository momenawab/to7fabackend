"""
Spec 001 Tests: User State Derivation

Tests derived from:
- spec-001.md sections: User State Definitions, Global Enforcement Matrix
- FR-001 through FR-007
"""

import pytest
import uuid
from django.contrib.auth import get_user_model
from custom_auth.services.user_state import get_user_state
from custom_auth.services.lock_block import can_perform_action

User = get_user_model()


class TestGuestStateDerivation:
    """Test FR-002: Guest state allows browsing, viewing products, adding to cart."""

    def test_guest_user_has_no_authentication(self):
        """Unauthenticated request derives GUEST state."""
        user = None
        state = get_user_state(user)
        assert state == 'GUEST'

    def test_guest_state_allows_browse(self):
        """FR-002: Guest state MUST allow browsing."""
        from custom_auth.services.lock_block import can_perform_action
        assert can_perform_action(None, 'BROWSE')['allowed']

    def test_guest_state_allows_view_product(self):
        """FR-002: Guest state MUST allow viewing products."""
        from custom_auth.services.lock_block import can_perform_action
        assert can_perform_action(None, 'VIEW_PRODUCT')['allowed']

    def test_guest_state_allows_add_to_cart(self):
        """FR-002: Guest state MUST allow adding to cart."""
        from custom_auth.services.lock_block import can_perform_action
        assert can_perform_action(None, 'ADD_TO_CART')['allowed']


class TestAuthenticatedUnverifiedStateDerivation:
    """Test FR-003, FR-004: Authenticated unverified mobile behavior."""

    def test_unverified_user_derives_correct_state(self, user):
        """User with is_mobile_verified=False derives AUTHENTICATED_UNVERIFIED."""
        user.is_mobile_verified = False
        user.is_locked = False
        user.is_blocked = False
        user.save()
        state = get_user_state(user)
        assert state == 'AUTHENTICATED_UNVERIFIED'

    def test_unverified_state_allows_browsing(self, user):
        """FR-003: Unverified state MUST allow browsing."""
        user.is_mobile_verified = False
        user.is_locked = False
        user.is_blocked = False
        user.save()
        from custom_auth.services.lock_block import can_perform_action
        assert can_perform_action(user, 'BROWSE')['allowed']

    def test_unverified_state_allows_cart_management(self, user):
        """FR-003: Unverified state MUST allow cart management."""
        user.is_mobile_verified = False
        user.is_locked = False
        user.is_blocked = False
        user.save()
        from custom_auth.services.lock_block import can_perform_action
        assert can_perform_action(user, 'VIEW_CART')['allowed']

    def test_unverified_state_allows_profile_viewing(self, user):
        """FR-003: Unverified state MUST allow profile viewing."""
        user.is_mobile_verified = False
        user.is_locked = False
        user.is_blocked = False
        user.save()
        from custom_auth.services.lock_block import can_perform_action
        assert can_perform_action(user, 'VIEW_PROFILE')['allowed']

    def test_unverified_state_blocks_checkout(self, user):
        """FR-004: Unverified state MUST NOT allow checkout."""
        user.is_mobile_verified = False
        user.is_locked = False
        user.is_blocked = False
        user.save()
        from custom_auth.services.lock_block import can_perform_action
        result = can_perform_action(user, 'CHECKOUT')
        assert not result['allowed']
        assert result['reason'] == 'VERIFICATION_REQUIRED'

    def test_unverified_state_blocks_payment(self, user):
        """FR-004: Unverified state MUST NOT allow payment."""
        user.is_mobile_verified = False
        user.is_locked = False
        user.is_blocked = False
        user.save()
        from custom_auth.services.lock_block import can_perform_action
        result = can_perform_action(user, 'PAY')
        assert not result['allowed']
        assert result['reason'] == 'VERIFICATION_REQUIRED'

    def test_unverified_state_blocks_order_creation(self, user):
        """FR-004: Unverified state MUST NOT allow order creation."""
        user.is_mobile_verified = False
        user.is_locked = False
        user.is_blocked = False
        user.save()
        from custom_auth.services.lock_block import can_perform_action
        result = can_perform_action(user, 'CREATE_ORDER')
        assert not result['allowed']
        assert result['reason'] == 'VERIFICATION_REQUIRED'


class TestAuthenticatedVerifiedStateDerivation:
    """Test FR-005: Authenticated verified mobile behavior."""

    def test_verified_user_derives_correct_state(self, user):
        """User with is_mobile_verified=True derives AUTHENTICATED_VERIFIED."""
        user.is_mobile_verified = True
        user.is_locked = False
        user.is_blocked = False
        user.save()
        state = get_user_state(user)
        assert state == 'AUTHENTICATED_VERIFIED'

    def test_verified_state_allows_checkout(self, user):
        """FR-005: Verified state MUST allow checkout."""
        user.is_mobile_verified = True
        user.is_locked = False
        user.is_blocked = False
        user.save()
        from custom_auth.services.lock_block import can_perform_action
        assert can_perform_action(user, 'CHECKOUT')['allowed']

    def test_verified_state_allows_payment(self, user):
        """FR-005: Verified state MUST allow payment."""
        user.is_mobile_verified = True
        user.is_locked = False
        user.is_blocked = False
        user.save()
        from custom_auth.services.lock_block import can_perform_action
        assert can_perform_action(user, 'PAY')['allowed']

    def test_verified_state_allows_order_creation(self, user):
        """FR-005: Verified state MUST allow order creation."""
        user.is_mobile_verified = True
        user.is_locked = False
        user.is_blocked = False
        user.save()
        from custom_auth.services.lock_block import can_perform_action
        assert can_perform_action(user, 'CREATE_ORDER')['allowed']

    def test_verified_state_allows_wallet_usage(self, user):
        """FR-005: Verified state MUST allow wallet usage."""
        user.is_mobile_verified = True
        user.is_locked = False
        user.is_blocked = False
        user.save()
        from custom_auth.services.lock_block import can_perform_action
        assert can_perform_action(user, 'WALLET_PAYMENT')['allowed']


class TestLockedStateDerivation:
    """Test FR-006: Locked (BANNED) state denies all access."""

    def test_locked_user_derives_correct_state(self, user):
        """User with is_locked=True derives LOCKED state regardless of other fields."""
        user.is_locked = True
        user.is_mobile_verified = True
        user.is_blocked = False
        user.save()
        state = get_user_state(user)
        assert state == 'LOCKED'

    def test_locked_state_denies_all_access(self, user):
        """FR-006: Locked state MUST deny all system access globally."""
        user.is_locked = True
        user.save()
        from custom_auth.services.lock_block import can_perform_action

        actions = ['BROWSE', 'VIEW_CART', 'CHECKOUT', 'PAY', 'VIEW_PROFILE']
        for action in actions:
            result = can_perform_action(user, action)
            assert not result['allowed']
            assert result['reason'] == 'BANNED'

    def test_locked_state_overrides_verification(self, user):
        """Locked state takes precedence over verified status."""
        user.is_locked = True
        user.is_mobile_verified = True
        user.save()
        from custom_auth.services.lock_block import can_perform_action
        result = can_perform_action(user, 'CHECKOUT')
        assert not result['allowed']
        assert result['reason'] == 'BANNED'


class TestBlockedStateDerivation:
    """Test FR-007, FR-030 through FR-033: Blocked (business restriction) state."""

    def test_blocked_user_derives_correct_state(self, user):
        """User with is_blocked=True derives BLOCKED state."""
        user.is_blocked = True
        user.is_locked = False
        user.blocked_capabilities = ['SELL']
        user.save()
        state = get_user_state(user)
        assert state == 'BLOCKED'

    def test_blocked_state_allows_login(self, user):
        """FR-032: Blocked users CAN login."""
        user.is_blocked = True
        user.blocked_capabilities = ['SELL']
        user.save()
        from custom_auth.services.lock_block import can_perform_action
        assert can_perform_action(user, 'LOGIN')['allowed']

    def test_blocked_state_allows_browsing(self, user):
        """FR-032: Blocked users CAN browse."""
        user.is_blocked = True
        user.blocked_capabilities = ['SELL']
        user.save()
        from custom_auth.services.lock_block import can_perform_action
        assert can_perform_action(user, 'BROWSE')['allowed']

    def test_blocked_state_allows_customer_features(self, user):
        """FR-032: Blocked users CAN use customer features."""
        user.is_blocked = True
        user.blocked_capabilities = ['SELL']
        user.is_mobile_verified = True  # Required per FR-014, FR-024
        user.save()
        from custom_auth.services.lock_block import can_perform_action
        assert can_perform_action(user, 'CHECKOUT')['allowed']

    def test_blocked_state_blocks_specific_capability(self, user):
        """FR-033: Blocked users MUST NOT access blocked capabilities."""
        user.is_blocked = True
        user.blocked_capabilities = ['SELL']
        user.save()
        from custom_auth.services.lock_block import can_perform_action
        result = can_perform_action(user, 'SELL')
        assert not result['allowed']
        assert result['reason'] == 'CAPABILITY_BLOCKED'

    def test_blocked_state_allows_unblocked_capabilities(self, user):
        """FR-031: Block is enforced per feature, not globally."""
        user.is_blocked = True
        user.blocked_capabilities = ['SELL', 'WITHDRAW']
        user.save()
        from custom_auth.services.lock_block import can_perform_action
        # BROWSE is not in blocked_capabilities
        assert can_perform_action(user, 'BROWSE')['allowed']


class TestStateDerivationPrecedence:
    """Test that state derivation follows correct precedence rules."""

    def test_locked_takes_precedence_over_blocked(self, user):
        """LOCKED state takes precedence over BLOCKED."""
        user.is_locked = True
        user.is_blocked = True
        user.save()
        state = get_user_state(user)
        assert state == 'LOCKED'

    def test_locked_takes_precedence_over_verified(self, user):
        """LOCKED state takes precedence over verified status."""
        user.is_locked = True
        user.is_mobile_verified = True
        user.is_blocked = False
        user.save()
        state = get_user_state(user)
        assert state == 'LOCKED'

    def test_blocked_takes_precedence_over_unverified(self, user):
        """BLOCKED state is distinct from unverified status."""
        user.is_blocked = True
        user.is_mobile_verified = False
        user.is_locked = False
        user.blocked_capabilities = ['SELL']
        user.save()
        state = get_user_state(user)
        assert state == 'BLOCKED'

    def test_verified_is_default_when_no_restrictions(self, user):
        """When not locked/blocked and verified, returns AUTHENTICATED_VERIFIED."""
        user.is_mobile_verified = True
        user.is_locked = False
        user.is_blocked = False
        user.save()
        state = get_user_state(user)
        assert state == 'AUTHENTICATED_VERIFIED'
