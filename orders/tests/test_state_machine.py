"""
Tests for Order State Machine - User Story 1

Tests the extended state machine with all 10 states and valid transitions.
"""
import pytest
from orders.atomic_order_system import OrderStateMachine


class TestValidTransitions:
    """Test all valid state transitions from the specification."""

    def test_pending_payment_to_paid(self):
        """pending_payment -> paid: Payment confirmed"""
        assert OrderStateMachine.validate_transition('pending_payment', 'paid')

    def test_pending_payment_to_cancelled(self):
        """pending_payment -> cancelled: User cancelled or timeout"""
        assert OrderStateMachine.validate_transition('pending_payment', 'cancelled')

    def test_pending_payment_to_failed(self):
        """pending_payment -> failed: Payment failed"""
        assert OrderStateMachine.validate_transition('pending_payment', 'failed')

    def test_cod_pending_to_processing(self):
        """cod_pending -> processing: Seller acknowledged"""
        assert OrderStateMachine.validate_transition('cod_pending', 'processing')

    def test_cod_pending_to_cancelled(self):
        """cod_pending -> cancelled: User cancelled"""
        assert OrderStateMachine.validate_transition('cod_pending', 'cancelled')

    def test_paid_to_processing(self):
        """paid -> processing: Seller acknowledged"""
        assert OrderStateMachine.validate_transition('paid', 'processing')

    def test_paid_to_cancelled(self):
        """paid -> cancelled: Cancel with refund"""
        assert OrderStateMachine.validate_transition('paid', 'cancelled')

    def test_paid_to_refunded(self):
        """paid -> refunded: Refund processed"""
        assert OrderStateMachine.validate_transition('paid', 'refunded')

    def test_processing_to_shipped(self):
        """processing -> shipped: Order dispatched"""
        assert OrderStateMachine.validate_transition('processing', 'shipped')

    def test_processing_to_cancelled(self):
        """processing -> cancelled: Cancel with refund"""
        assert OrderStateMachine.validate_transition('processing', 'cancelled')

    def test_processing_to_refunded(self):
        """processing -> refunded: Refund processed"""
        assert OrderStateMachine.validate_transition('processing', 'refunded')

    def test_shipped_to_delivered(self):
        """shipped -> delivered: Delivery confirmed"""
        assert OrderStateMachine.validate_transition('shipped', 'delivered')

    def test_shipped_to_refunded(self):
        """shipped -> refunded: Return/dispute refund"""
        assert OrderStateMachine.validate_transition('shipped', 'refunded')

    def test_delivered_to_completed(self):
        """delivered -> completed: Order fulfilled"""
        assert OrderStateMachine.validate_transition('delivered', 'completed')

    def test_delivered_to_refunded(self):
        """delivered -> refunded: Return/dispute refund"""
        assert OrderStateMachine.validate_transition('delivered', 'refunded')

    def test_noop_transition(self):
        """Transition to same state should be allowed (no-op)"""
        assert OrderStateMachine.validate_transition('paid', 'paid')
        assert OrderStateMachine.validate_transition('processing', 'processing')


class TestInvalidTransitions:
    """Test that invalid transitions raise ValueError."""

    def test_terminal_states_cannot_transition(self):
        """Terminal states (completed, cancelled, refunded, failed) cannot transition."""
        terminal_states = ['completed', 'cancelled', 'refunded', 'failed']
        all_states = ['pending_payment', 'cod_pending', 'paid', 'processing', 'shipped', 'delivered']

        for terminal in terminal_states:
            for target in all_states:
                if terminal != target:
                    with pytest.raises(ValueError, match="Invalid state transition"):
                        OrderStateMachine.validate_transition(terminal, target)

    def test_invalid_transition_from_pending_payment(self):
        """pending_payment cannot go to processing/shipped/delivered/completed"""
        invalid_targets = ['processing', 'shipped', 'delivered', 'completed', 'refunded', 'cod_pending']
        for target in invalid_targets:
            with pytest.raises(ValueError, match="Invalid state transition"):
                OrderStateMachine.validate_transition('pending_payment', target)

    def test_invalid_transition_from_cod_pending(self):
        """cod_pending cannot go to paid/shipped/delivered/completed"""
        invalid_targets = ['paid', 'shipped', 'delivered', 'completed', 'refunded', 'failed', 'pending_payment']
        for target in invalid_targets:
            with pytest.raises(ValueError, match="Invalid state transition"):
                OrderStateMachine.validate_transition('cod_pending', target)

    def test_invalid_transition_from_paid(self):
        """paid cannot go to pending_payment/cod_pending/shipped/delivered"""
        invalid_targets = ['pending_payment', 'cod_pending', 'shipped', 'delivered', 'completed', 'failed']
        for target in invalid_targets:
            with pytest.raises(ValueError, match="Invalid state transition"):
                OrderStateMachine.validate_transition('paid', target)

    def test_invalid_transition_from_processing(self):
        """processing cannot go to pending_payment/cod_pending/paid/delivered"""
        invalid_targets = ['pending_payment', 'cod_pending', 'paid', 'delivered', 'completed', 'failed']
        for target in invalid_targets:
            with pytest.raises(ValueError, match="Invalid state transition"):
                OrderStateMachine.validate_transition('processing', target)

    def test_invalid_transition_from_shipped(self):
        """shipped cannot go to pending_payment/cod_pending/paid/processing/completed"""
        invalid_targets = ['pending_payment', 'cod_pending', 'paid', 'processing', 'completed', 'failed', 'cancelled']
        for target in invalid_targets:
            with pytest.raises(ValueError, match="Invalid state transition"):
                OrderStateMachine.validate_transition('shipped', target)

    def test_invalid_transition_from_delivered(self):
        """delivered cannot go to pending_payment/cod_pending/paid/processing/shipped"""
        invalid_targets = ['pending_payment', 'cod_pending', 'paid', 'processing', 'shipped', 'failed', 'cancelled']
        for target in invalid_targets:
            with pytest.raises(ValueError, match="Invalid state transition"):
                OrderStateMachine.validate_transition('delivered', target)


class TestAtomicTransitionEnforcement:
    """Test that transitions are enforced atomically."""

    def test_validate_transition_returns_bool(self):
        """validate_transition should return True for valid transitions."""
        result = OrderStateMachine.validate_transition('pending_payment', 'paid')
        assert result is True

    def test_validate_transition_raises_on_invalid(self):
        """validate_transition should raise ValueError for invalid transitions."""
        with pytest.raises(ValueError):
            OrderStateMachine.validate_transition('completed', 'paid')


class TestTerminalStates:
    """Test terminal state detection."""

    def test_is_terminal_for_completed(self):
        """completed is a terminal state."""
        assert OrderStateMachine.is_terminal('completed')

    def test_is_terminal_for_cancelled(self):
        """cancelled is a terminal state."""
        assert OrderStateMachine.is_terminal('cancelled')

    def test_is_terminal_for_refunded(self):
        """refunded is a terminal state."""
        assert OrderStateMachine.is_terminal('refunded')

    def test_is_terminal_for_failed(self):
        """failed is a terminal state."""
        assert OrderStateMachine.is_terminal('failed')

    def test_is_terminal_false_for_non_terminal(self):
        """Non-terminal states should return False."""
        non_terminal = ['pending_payment', 'cod_pending', 'paid', 'processing', 'shipped', 'delivered']
        for status in non_terminal:
            assert not OrderStateMachine.is_terminal(status)


class TestInitialState:
    """Test initial state determination based on payment method."""

    def test_get_initial_state_for_cod(self):
        """COD orders should start in cod_pending."""
        assert OrderStateMachine.get_initial_state('cod') == 'cod_pending'

    def test_get_initial_state_for_wallet(self):
        """Wallet orders should start in pending_payment."""
        assert OrderStateMachine.get_initial_state('wallet') == 'pending_payment'

    def test_get_initial_state_for_instapay(self):
        """InstaPay orders should start in pending_payment."""
        assert OrderStateMachine.get_initial_state('instapay') == 'pending_payment'

    def test_get_initial_state_for_credit_card(self):
        """Credit card orders should start in pending_payment."""
        assert OrderStateMachine.get_initial_state('credit_card') == 'pending_payment'


class TestCanCancel:
    """Test cancellation eligibility."""

    def test_can_cancel_pending_payment(self):
        """pending_payment orders can be cancelled."""
        assert OrderStateMachine.can_cancel('pending_payment')

    def test_can_cancel_cod_pending(self):
        """cod_pending orders can be cancelled."""
        assert OrderStateMachine.can_cancel('cod_pending')

    def test_can_cancel_paid(self):
        """paid orders can be cancelled (with refund)."""
        assert OrderStateMachine.can_cancel('paid')

    def test_can_cancel_processing(self):
        """processing orders can be cancelled (with refund)."""
        assert OrderStateMachine.can_cancel('processing')

    def test_cannot_cancel_shipped(self):
        """shipped orders cannot be cancelled."""
        assert not OrderStateMachine.can_cancel('shipped')

    def test_cannot_cancel_delivered(self):
        """delivered orders cannot be cancelled."""
        assert not OrderStateMachine.can_cancel('delivered')

    def test_cannot_cancel_completed(self):
        """completed orders cannot be cancelled."""
        assert not OrderStateMachine.can_cancel('completed')

    def test_cannot_cancel_cancelled(self):
        """cancelled orders cannot be cancelled again."""
        assert not OrderStateMachine.can_cancel('cancelled')

    def test_cannot_cancel_refunded(self):
        """refunded orders cannot be cancelled."""
        assert not OrderStateMachine.can_cancel('refunded')

    def test_cannot_cancel_failed(self):
        """failed orders cannot be cancelled."""
        assert not OrderStateMachine.can_cancel('failed')


class TestRequiresRefund:
    """Test refund requirement determination."""

    def test_requires_refund_for_paid(self):
        """paid orders require refund on cancellation."""
        assert OrderStateMachine.requires_refund('paid')

    def test_requires_refund_for_processing(self):
        """processing orders require refund on cancellation."""
        assert OrderStateMachine.requires_refund('processing')

    def test_requires_refund_for_shipped(self):
        """shipped orders require refund on cancellation."""
        assert OrderStateMachine.requires_refund('shipped')

    def test_requires_refund_for_delivered(self):
        """delivered orders require refund on cancellation."""
        assert OrderStateMachine.requires_refund('delivered')

    def test_no_refund_for_pending_payment(self):
        """pending_payment orders don't require refund."""
        assert not OrderStateMachine.requires_refund('pending_payment')

    def test_no_refund_for_cod_pending(self):
        """cod_pending orders don't require refund."""
        assert not OrderStateMachine.requires_refund('cod_pending')

    def test_no_refund_for_terminal_states(self):
        """Terminal states don't require refund."""
        terminal = ['completed', 'cancelled', 'refunded', 'failed']
        for status in terminal:
            assert not OrderStateMachine.requires_refund(status)
