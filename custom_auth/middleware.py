"""
Middleware for user lock enforcement.

This module contains middleware to enforce global lock (BAN) status
for authenticated users across all API endpoints.
"""

import logging
from django.http import JsonResponse
from rest_framework import status

logger = logging.getLogger(__name__)


class LockEnforcementMiddleware:
    """
    Middleware to enforce user lock status globally.

    Checks if an authenticated user is locked and returns 403 error
    with USER_LOCKED code before processing the request.

    This ensures that locked users cannot access any API endpoint,
    providing a global ban mechanism.
    """

    def __init__(self, get_response):
        """Initialize middleware with get_response callable."""
        self.get_response = get_response

    def __call__(self, request):
        """
        Process request and check user lock status.

        Args:
            request: The incoming HTTP request

        Returns:
            JsonResponse with 403 if user is locked, otherwise
            proceeds with normal request processing
        """
        # Only check lock status for authenticated users
        if request.user.is_authenticated:
            # Check if user is locked (banned)
            if getattr(request.user, 'is_locked', False):
                logger.warning(
                    f"Locked user {request.user.id} ({request.user.email}) attempted to access {request.method} {request.path}",
                    extra={
                        'user_id': request.user.id,
                        'email': request.user.email,
                        'method': request.method,
                        'path': request.path,
                        'action': 'lock_enforcement',
                        'result': 'blocked',
                        'locked_at': getattr(request.user, 'locked_at', None)
                    }
                )
                return JsonResponse(
                    {
                        'success': False,
                        'error': {
                            'code': 'USER_LOCKED',
                            'message': 'You are banned',
                            'details': {}
                        }
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

        # Proceed with normal request processing
        response = self.get_response(request)
        return response
