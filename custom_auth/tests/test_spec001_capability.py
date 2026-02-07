"""
Spec 001 Tests: Capability-Based Authorization

Tests derived from:
- spec-001.md section: Lock & Block Enforcement Rules
- FR-026 through FR-033
"""

import pytest
import uuid
from django.contrib.auth import get_user_model
from custom_auth.services.lock_block import check_capability_blocked, can_perform_action

User = get_user_model()


class TestCapabilityBasedBlocking:
    """Test FR-031, FR-033: Block is enforced per capability."""

    def test_sell_capability_blocked_for_seller(self, db):
        """User blocked from SELL capability cannot sell."""
        user = User.objects.create_user(
            email=f'seller_5bf094f8@example.com',
            password='testpass123',
        )
        user.is_blocked = True
        user.blocked_capabilities = ['SELL']
        user.save()

        assert check_capability_blocked(user, 'SELL')
        result = can_perform_action(user, 'SELL')
        assert not result['allowed']
        assert result['reason'] == 'CAPABILITY_BLOCKED'

    def test_withdraw_capability_blocked(self, db):
        """User blocked from WITHDRAW capability cannot withdraw."""
        user = User.objects.create_user(
            email=f'user_481d3004@example.com',
            password='testpass123',
        )
        user.is_blocked = True
        user.blocked_capabilities = ['WITHDRAW']
        user.save()

        assert check_capability_blocked(user, 'WITHDRAW')
        result = can_perform_action(user, 'WITHDRAW')
        assert not result['allowed']

    def test_multiple_capabilities_blocked(self, db):
        """User can be blocked from multiple capabilities."""
        user = User.objects.create_user(
            email=f'user_5abf1dc1@example.com',
            password='testpass123',
        )
        user.is_blocked = True
        user.blocked_capabilities = ['SELL', 'WITHDRAW', 'CREATE_PRODUCT']
        user.save()

        for capability in ['SELL', 'WITHDRAW', 'CREATE_PRODUCT']:
            assert check_capability_blocked(user, capability)
            result = can_perform_action(user, capability)
            assert not result['allowed']


class TestBlockDoesNotAffectUnrelatedFeatures:
    """Test FR-031: Block enforced per feature, not globally."""

    def test_blocked_seller_can_browse(self, db):
        """Blocked seller CAN browse products."""
        user = User.objects.create_user(
            email=f'seller_38ea339c@example.com',
            password='testpass123',
        )
        user.is_blocked = True
        user.blocked_capabilities = ['SELL']
        user.save()

        result = can_perform_action(user, 'BROWSE')
        assert result['allowed']

    def test_blocked_seller_can_checkout(self, db):
        """Blocked seller CAN checkout as customer."""
        user = User.objects.create_user(
            email=f'seller_64534730@example.com',
            password='testpass123',
        )
        user.is_blocked = True
        user.blocked_capabilities = ['SELL']
        user.is_mobile_verified = True  # Required per FR-014, FR-024
        user.save()

        result = can_perform_action(user, 'CHECKOUT')
        assert result['allowed']

    def test_blocked_seller_can_view_profile(self, db):
        """Blocked seller CAN view own profile."""
        user = User.objects.create_user(
            email=f'seller_f0aa159d@example.com',
            password='testpass123',
        )
        user.is_blocked = True
        user.blocked_capabilities = ['SELL']
        user.save()

        result = can_perform_action(user, 'VIEW_PROFILE')
        assert result['allowed']

    def test_blocked_withdraw_can_still_sell(self, db):
        """User blocked from WITHDRAW can still SELL."""
        user = User.objects.create_user(
            email=f'seller_5a3d9448@example.com',
            password='testpass123',
        )
        user.is_blocked = True
        user.blocked_capabilities = ['WITHDRAW']
        user.save()

        result = can_perform_action(user, 'SELL')
        assert result['allowed']


class TestGlobalLockEnforcement:
    """Test FR-026, FR-027: Lock denies all access globally."""

    def test_locked_user_denied_all_capabilities(self, db):
        """FR-026: Lock enforces total system denial."""
        user = User.objects.create_user(
            email=f'locked_a710cd8e@example.com',
            password='testpass123',
        )
        user.is_locked = True
        user.save()

        actions = ['BROWSE', 'SELL', 'WITHDRAW', 'CHECKOUT', 'VIEW_PROFILE']
        for action in actions:
            result = can_perform_action(user, action)
            assert not result['allowed']
            assert result['reason'] == 'BANNED'

    def test_locked_overrides_blocked_capabilities(self, db):
        """Lock takes precedence over block."""
        user = User.objects.create_user(
            email=f'user_f852ff1f@example.com',
            password='testpass123',
        )
        user.is_locked = True
        user.is_blocked = True
        user.blocked_capabilities = ['SELL']
        user.save()

        result = can_perform_action(user, 'BROWSE')
        assert not result['allowed']
        assert result['reason'] == 'BANNED'


class TestUnblockedCapabilities:
    """Test that unblocked capabilities work normally."""

    def test_unblocked_user_can_sell(self, db):
        """User not blocked from SELL can sell."""
        user = User.objects.create_user(
            email=f'seller_2ab32292@example.com',
            password='testpass123',
        )
        user.is_blocked = False
        user.save()

        result = can_perform_action(user, 'SELL')
        assert result['allowed']

    def test_unblocked_user_can_withdraw(self, db):
        """User not blocked from WITHDRAW can withdraw."""
        user = User.objects.create_user(
            email=f'user_363510a6@example.com',
            password='testpass123',
        )
        user.is_blocked = False
        user.save()

        result = can_perform_action(user, 'WITHDRAW')
        assert result['allowed']

    def test_no_blocked_capabilities_allows_all(self, db):
        """User with empty blocked_capabilities can do everything."""
        user = User.objects.create_user(
            email=f'user_12853df5@example.com',
            password='testpass123',
        )
        user.is_blocked = True
        user.blocked_capabilities = []
        user.is_mobile_verified = True  # Required for CHECKOUT per FR-014, FR-024
        user.save()

        actions = ['SELL', 'WITHDRAW', 'BROWSE', 'CHECKOUT']
        for action in actions:
            result = can_perform_action(user, action)
            assert result['allowed']
