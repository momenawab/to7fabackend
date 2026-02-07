"""
Custom Auth Services

This module contains business logic for user authentication, verification,
and authorization operations.
"""

from .user_state import get_user_state
from .verification import (
    send_otp,
    verify_otp,
    check_otp_blocked,
    verification_required,
)
from .lock_block import (
    check_capability_blocked,
    is_user_locked,
    is_user_blocked,
    get_blocked_capabilities,
)

__all__ = [
    "get_user_state",
    "send_otp",
    "verify_otp",
    "check_otp_blocked",
    "verification_required",
    "check_capability_blocked",
    "is_user_locked",
    "is_user_blocked",
    "get_blocked_capabilities",
]
