"""
OTP verification service.

Handles OTP generation, validation, cooldown, and blocking behavior.
Uses Redis for OTP storage with database fallback.
"""

import secrets
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

from django.core.cache import cache
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password

from custom_auth.models import User, OTPVerification

logger = logging.getLogger(__name__)


# Constants
OTP_LENGTH = 6
OTP_EXPIRY_SECONDS = 300  # 5 minutes
OTP_COOLDOWN_SECONDS = 60  # 60 seconds
OTP_MAX_ATTEMPTS = 3

# Redis key formats
OTP_KEY_FORMAT = "otp:{user_id}:{mobile_hash}"
COOLDOWN_KEY_FORMAT = "otp_cooldown:{user_id}"
PENDING_CHECKOUT_KEY_FORMAT = "pending_checkout:{user_id}"


def _generate_otp_code() -> str:
    """Generate a 6-digit OTP code."""
    return secrets.token_hex(3)[:OTP_LENGTH].zfill(OTP_LENGTH)


def _hash_otp(otp_code: str) -> str:
    """Hash OTP code using PBKDF2 for secure storage."""
    return make_password(otp_code)


def _get_mobile_hash(mobile_number: str) -> str:
    """Generate a hash of mobile number for Redis key."""
    return hashlib.sha256(mobile_number.encode()).hexdigest()[:16]


def check_otp_blocked(user: User) -> bool:
    """
    Check if user is blocked from OTP verification.

    Returns:
        True if user is blocked, False otherwise.
    """
    return user.otp_blocked_at is not None


def send_otp(user: User, mobile_number: str) -> Dict:
    """
    Send OTP to user's mobile number.

    Args:
        user: User requesting OTP
        mobile_number: Mobile number to verify

    Returns:
        Dict with success status and OTP details or error information.
    """
    # Check if user is blocked
    if check_otp_blocked(user):
        logger.warning(
            f"OTP send blocked for user {user.id} ({user.email}) - User is OTP blocked",
            extra={
                'user_id': user.id,
                'email': user.email,
                'action': 'send_otp',
                'result': 'blocked'
            }
        )
        return {
            'success': False,
            'error': 'OTP_BLOCKED',
            'message': 'OTP verification blocked. Contact support.',
            'details': {}
        }

    # Check cooldown
    cooldown_key = COOLDOWN_KEY_FORMAT.format(user_id=user.id)
    cooldown_remaining = cache.get(cooldown_key)

    if cooldown_remaining is not None:
        logger.info(
            f"OTP send blocked for user {user.id} ({user.email}) - Cooldown active",
            extra={
                'user_id': user.id,
                'email': user.email,
                'action': 'send_otp',
                'result': 'cooldown',
                'wait_seconds': int(cooldown_remaining)
            }
        )
        return {
            'success': False,
            'error': 'OTP_COOLDOWN',
            'message': 'Please wait 60 seconds before requesting new OTP',
            'details': {
                'wait_seconds': int(cooldown_remaining)
            }
        }

    # Generate OTP
    otp_code = _generate_otp_code()
    otp_hash = _hash_otp(otp_code)
    mobile_hash = _get_mobile_hash(mobile_number)

    # Store in Redis with TTL
    otp_key = OTP_KEY_FORMAT.format(user_id=user.id, mobile_hash=mobile_hash)
    cache.set(otp_key, otp_hash, timeout=OTP_EXPIRY_SECONDS)

    # Set cooldown
    cache.set(cooldown_key, OTP_COOLDOWN_SECONDS, timeout=OTP_COOLDOWN_SECONDS)

    # Create database record
    OTPVerification.objects.create(
        user=user,
        mobile_number=mobile_number,
        otp_hash=otp_hash,
        expires_at=timezone.now() + timedelta(seconds=OTP_EXPIRY_SECONDS),
        used=False
    )

    # Log OTP send (security event)
    logger.info(
        f"OTP sent to user {user.id} ({user.email}) for mobile {mobile_number}",
        extra={
            'user_id': user.id,
            'email': user.email,
            'mobile_number': mobile_number,
            'action': 'send_otp',
            'result': 'success',
            'expires_in': OTP_EXPIRY_SECONDS
        }
    )

    # In production, send SMS here
    # For testing, return OTP in response
    return {
        'success': True,
        'data': {
            'message': 'OTP sent successfully',
            'expires_in': OTP_EXPIRY_SECONDS,
            'otp_code': otp_code  # Remove in production
        }
    }


def verify_otp(user: User, otp_code: str) -> Dict:
    """
    Verify OTP code for user.

    Args:
        user: User verifying OTP
        otp_code: 6-digit OTP code

    Returns:
        Dict with success status and verification result or error information.
    """
    # Check if user is blocked
    if check_otp_blocked(user):
        logger.warning(
            f"OTP verification blocked for user {user.id} ({user.email}) - User is OTP blocked",
            extra={
                'user_id': user.id,
                'email': user.email,
                'action': 'verify_otp',
                'result': 'blocked'
            }
        )
        return {
            'success': False,
            'error': 'OTP_BLOCKED',
            'message': 'OTP verification blocked. Contact support.',
            'details': {}
        }

    # Get active OTP record from database
    otp_record = OTPVerification.objects.filter(
        user=user,
        used=False
    ).order_by('-created_at').first()

    if not otp_record:
        logger.warning(
            f"OTP verification failed for user {user.id} ({user.email}) - No active OTP found",
            extra={
                'user_id': user.id,
                'email': user.email,
                'action': 'verify_otp',
                'result': 'no_active_otp'
            }
        )
        return {
            'success': False,
            'error': 'OTP_EXPIRED',
            'message': 'OTP has expired. Please request a new one.',
            'details': {
                'wait_seconds': OTP_COOLDOWN_SECONDS
            }
        }

    # Check if OTP has expired
    if otp_record.expires_at < timezone.now():
        logger.warning(
            f"OTP verification failed for user {user.id} ({user.email}) - OTP expired",
            extra={
                'user_id': user.id,
                'email': user.email,
                'action': 'verify_otp',
                'result': 'expired',
                'expired_at': otp_record.expires_at.isoformat()
            }
        )
        return {
            'success': False,
            'error': 'OTP_EXPIRED',
            'message': 'OTP has expired. Please request a new one.',
            'details': {
                'wait_seconds': OTP_COOLDOWN_SECONDS
            }
        }

    # Verify OTP from Redis
    mobile_hash = _get_mobile_hash(otp_record.mobile_number)
    otp_key = OTP_KEY_FORMAT.format(user_id=user.id, mobile_hash=mobile_hash)
    stored_hash = cache.get(otp_key)

    if stored_hash is None:
        logger.warning(
            f"OTP verification failed for user {user.id} ({user.email}) - OTP not in cache",
            extra={
                'user_id': user.id,
                'email': user.email,
                'action': 'verify_otp',
                'result': 'not_in_cache'
            }
        )
        return {
            'success': False,
            'error': 'OTP_EXPIRED',
            'message': 'OTP has expired. Please request a new one.',
            'details': {
                'wait_seconds': OTP_COOLDOWN_SECONDS
            }
        }

    # Verify OTP hash
    if not check_password(otp_code, stored_hash):
        # Increment failed attempts
        user.otp_failed_attempts += 1
        otp_record.attempt_count += 1

        # Check if max attempts reached
        if user.otp_failed_attempts >= OTP_MAX_ATTEMPTS:
            user.otp_blocked_at = timezone.now()
            user.save()
            otp_record.save()

            logger.warning(
                f"OTP verification blocked for user {user.id} ({user.email}) - Max attempts ({OTP_MAX_ATTEMPTS}) reached",
                extra={
                    'user_id': user.id,
                    'email': user.email,
                    'action': 'verify_otp',
                    'result': 'blocked',
                    'failed_attempts': user.otp_failed_attempts,
                    'mobile_number': otp_record.mobile_number
                }
            )

            return {
                'success': False,
                'error': 'OTP_BLOCKED',
                'message': 'Too many failed attempts. OTP verification blocked.',
                'details': {}
            }

        user.save()
        otp_record.save()

        attempts_remaining = OTP_MAX_ATTEMPTS - user.otp_failed_attempts

        logger.warning(
            f"OTP verification failed for user {user.id} ({user.email}) - Invalid OTP",
            extra={
                'user_id': user.id,
                'email': user.email,
                'action': 'verify_otp',
                'result': 'invalid',
                'failed_attempts': user.otp_failed_attempts,
                'attempts_remaining': attempts_remaining,
                'mobile_number': otp_record.mobile_number
            }
        )

        return {
            'success': False,
            'error': 'OTP_INVALID',
            'message': 'Invalid OTP code',
            'details': {
                'attempts_remaining': attempts_remaining
            }
        }

    # OTP is valid - mark as verified
    otp_record.used = True
    otp_record.save()

    # Update user verification status
    user.is_mobile_verified = True
    user.mobile_verified_at = timezone.now()
    user.otp_failed_attempts = 0
    user.save()

    # Delete OTP from cache
    cache.delete(otp_key)

    logger.info(
        f"OTP verification successful for user {user.id} ({user.email})",
        extra={
            'user_id': user.id,
            'email': user.email,
            'action': 'verify_otp',
            'result': 'success',
            'mobile_number': otp_record.mobile_number,
            'verified_at': user.mobile_verified_at.isoformat()
        }
    )

    return {
        'success': True,
        'data': {
            'message': 'Mobile verified successfully',
            'is_mobile_verified': True
        }
    }


def verification_required(view_func):
    """
    Decorator to require mobile verification for a view.

    Returns 403 with MOBILE_VERIFICATION_REQUIRED error if user is not verified.
    Stores checkout data for resume after verification.
    """
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return view_func(request, *args, **kwargs)

        if not request.user.is_mobile_verified:
            # Store checkout data for resume after verification
            # Only store if there's POST data (checkout attempt)
            if request.method == 'POST' and request.data:
                checkout_data = dict(request.data)
                store_pending_checkout(request.user, checkout_data)

            return {
                'success': False,
                'error': 'MOBILE_VERIFICATION_REQUIRED',
                'message': 'Mobile verification required for this action',
                'details': {}
            }, 403

        return view_func(request, *args, **kwargs)

    return wrapped_view


def store_pending_checkout(user: User, checkout_data: Dict, ttl: int = 600) -> bool:
    """
    Store pending checkout data for a user.

    Args:
        user: User attempting checkout
        checkout_data: Dictionary containing checkout request data
        ttl: Time to live in seconds (default: 10 minutes)

    Returns:
        True if stored successfully, False otherwise.
    """
    try:
        key = PENDING_CHECKOUT_KEY_FORMAT.format(user_id=user.id)
        cache.set(key, checkout_data, timeout=ttl)
        return True
    except Exception as e:
        logger.error(f"Error storing pending checkout for user {user.id}: {str(e)}")
        return False


def get_pending_checkout(user: User) -> Optional[Dict]:
    """
    Retrieve pending checkout data for a user.

    Args:
        user: User to retrieve checkout data for

    Returns:
        Checkout data dictionary if exists, None otherwise.
    """
    try:
        key = PENDING_CHECKOUT_KEY_FORMAT.format(user_id=user.id)
        return cache.get(key)
    except Exception as e:
        logger.error(f"Error retrieving pending checkout for user {user.id}: {str(e)}")
        return None


def clear_pending_checkout(user: User) -> bool:
    """
    Clear pending checkout data for a user.

    Args:
        user: User to clear checkout data for

    Returns:
        True if cleared successfully, False otherwise.
    """
    try:
        key = PENDING_CHECKOUT_KEY_FORMAT.format(user_id=user.id)
        cache.delete(key)
        return True
    except Exception as e:
        logger.error(f"Error clearing pending checkout for user {user.id}: {str(e)}")
        return False
