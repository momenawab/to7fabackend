"""
Lock and Block enforcement service.

Provides functions to check user lock/block status and capability restrictions.
"""

import logging
from functools import wraps
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


class CapabilityCode:
    """Canonical capability codes for business restrictions."""
    SELL = "SELL"
    WITHDRAW = "WITHDRAW"
    CREATE_PRODUCT = "CREATE_PRODUCT"
    MANAGE_ORDERS = "MANAGE_ORDERS"
    CREATE_CONSULTATION = "CREATE_CONSULTATION"


def capability_required(capability, methods=None):
    """
    Decorator to check if user has required capability (not blocked).
    
    Args:
        capability: str - Capability code required for this endpoint
        methods: list - HTTP methods that require this check. 
                       Defaults to ['POST', 'PUT', 'DELETE', 'PATCH'].
                       GET and other methods pass through without auth.
    
    Returns:
        Decorator function
    
    Usage:
        @capability_required(CapabilityCode.SELL)
        def create_product(request):
            ...
        
        # Or with explicit methods:
        @capability_required(CapabilityCode.SELL, methods=['POST'])
        def product_list(request):
            ...
    """
    if methods is None:
        methods = ['POST', 'PUT', 'DELETE', 'PATCH']
    
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            # Only enforce capability check for specified methods
            if request.method not in methods:
                # Allow request to pass through for read-only methods
                return view_func(request, *args, **kwargs)
            
            # Check if user is authenticated
            if not request.user.is_authenticated:
                return Response(
                    {
                        "error": {
                            "code": "AUTHENTICATION_FAILED",
                            "message": "Authentication required"
                        }
                    },
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Check if capability is blocked (this takes priority over other checks)
            if check_capability_blocked(request.user, capability):
                logger.warning(
                    f"Capability blocked for user {request.user.id} ({request.user.email}) - Capability: {capability}",
                    extra={
                        'user_id': request.user.id,
                        'email': request.user.email,
                        'action': 'capability_check',
                        'capability': capability,
                        'result': 'blocked',
                        'is_locked': request.user.is_locked,
                        'is_blocked': request.user.is_blocked,
                        'blocked_capabilities': request.user.blocked_capabilities
                    }
                )
                return Response(
                    {
                        "error": {
                            "code": "CAPABILITY_BLOCKED",
                            "message": f"This feature is currently unavailable for your account. Blocked capability: {capability}"
                        }
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Capability not blocked, proceed with view
            return view_func(request, *args, **kwargs)
        
        return wrapped_view
    return decorator


def check_capability_blocked(user, capability):
    """
    Check if a user is blocked from a specific capability.
    
    Args:
        user: User instance
        capability: str - Capability code to check
    
    Returns:
        bool: True if capability is blocked, False otherwise
    
    Raises:
        ValueError: If capability is not a valid CapabilityCode
    """
    valid_capabilities = [
        CapabilityCode.SELL,
        CapabilityCode.WITHDRAW,
        CapabilityCode.CREATE_PRODUCT,
        CapabilityCode.MANAGE_ORDERS,
        CapabilityCode.CREATE_CONSULTATION,
    ]
    
    if capability not in valid_capabilities:
        raise ValueError(f"Invalid capability code: {capability}")
    
    # Check if user is globally locked (all capabilities blocked)
    if user.is_locked:
        return True
    
    # Check if user has capability-specific block
    if user.is_blocked and capability in user.blocked_capabilities:
        return True
    
    return False


def is_user_locked(user):
    """
    Check if user is globally locked (banned).
    
    Args:
        user: User instance
    
    Returns:
        bool: True if user is locked, False otherwise
    """
    return user.is_locked


def is_user_blocked(user):
    """
    Check if user has any business restrictions.
    
    Args:
        user: User instance
    
    Returns:
        bool: True if user is blocked, False otherwise
    """
    return user.is_blocked


def get_blocked_capabilities(user):
    """
    Get list of blocked capabilities for a user.
    
    Args:
        user: User instance
    
    Returns:
        list: List of blocked capability codes
    """
    if user.is_locked:
        # If locked, all capabilities are blocked
        return [
            CapabilityCode.SELL,
            CapabilityCode.WITHDRAW,
            CapabilityCode.CREATE_PRODUCT,
            CapabilityCode.MANAGE_ORDERS,
            CapabilityCode.CREATE_CONSULTATION,
        ]
    
    if user.is_blocked:
        return user.blocked_capabilities
    
    return []
