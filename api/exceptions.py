"""
Custom Exception Handler

This module provides standardized error handling for all API endpoints.
Following API Response Standard defined in API_RESPONSE_STANDARD.md
"""

from rest_framework.views import exception_handler
from rest_framework.exceptions import (
    ValidationError,
    AuthenticationFailed,
    PermissionDenied,
    NotFound,
    APIException
)
from .utils.response import StandardResponse


def custom_exception_handler(exc, context):
    """
    Custom exception handler for standardized error responses.
    
    Uses exception.detail if available (e.g., ValidationError) for cleaner,
    more structured validation error messages for Flutter UI.
    Falls back to str(exc) if .detail not available.
    
    Args:
        exc: The exception that was raised
        context: Request context (includes request object)
    
    Returns:
        Response with standard error format or None (if DRF handles it)
    """
    # Call DRF's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Get request_id from request
        request = context.get('request')
        request_id = getattr(request, 'request_id', None) if request else None
        
        # Map DRF exceptions to standard error codes
        error_code = 'INTERNAL_SERVER_ERROR'
        if isinstance(exc, ValidationError):
            error_code = 'VALIDATION_ERROR'
        elif isinstance(exc, AuthenticationFailed):
            error_code = 'AUTHENTICATION_FAILED'
        elif isinstance(exc, PermissionDenied):
            error_code = 'PERMISSION_DENIED'
        elif isinstance(exc, NotFound):
            error_code = 'NOT_FOUND'
        elif isinstance(exc, APIException):
            error_code = 'API_ERROR'
        
        # Use exception.detail if available for cleaner messages
        # Otherwise fall back to str(exc)
        error_message = getattr(exc, 'detail', str(exc))
        
        # Build standard error response
        standard_response = StandardResponse.error(
            code=error_code,
            message=error_message,
            details=response.data if hasattr(response, 'data') else None,
            status_code=response.status_code,
            request_id=request_id
        )
        
        # Update response with standard format
        response.data = standard_response.data
        response.status_code = standard_response.status_code
    
    return response
