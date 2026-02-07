"""
User state derivation service.

Provides functions to determine user state based on model fields.
"""


def get_user_state(user):
    """
    Derive user state from User model fields.
    
    Args:
        user: User instance or None (for unauthenticated requests)
    
    Returns:
        str: One of the following states:
            - 'GUEST': User is None or not authenticated
            - 'LOCKED': User is globally banned
            - 'BLOCKED': User has business restrictions
            - 'AUTHENTICATED_VERIFIED': User is verified
            - 'AUTHENTICATED_UNVERIFIED': User is not verified
    """
    if user is None or not user.is_authenticated:
        return "GUEST"
    
    if user.is_locked:
        return "LOCKED"
    
    if user.is_blocked:
        return "BLOCKED"
    
    if user.is_mobile_verified:
        return "AUTHENTICATED_VERIFIED"
    
    return "AUTHENTICATED_UNVERIFIED"
