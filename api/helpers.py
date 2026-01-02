"""
API Response Helpers for Function-Based Views

This module provides helper functions for function-based views to use
the standard response format without requiring class-based view migration.

Usage:
    from api.helpers import api_response, api_error, api_success
    
    @api_view(['GET'])
    def my_view(request):
        data = {...}
        return api_response(request, data=data, message="Success")
"""

from .utils.response import StandardResponse


def get_request_id(request):
    """
    Extract request_id from request object.
    
    Args:
        request: Django request object
        
    Returns:
        str: request_id or None
    """
    return getattr(request, 'request_id', None)


def api_response(request, data=None, message=None, status_code=200):
    """
    Create a standard API response.
    
    Args:
        request: Django request object
        data: Response data
        message: Optional success message
        status_code: HTTP status code
        
    Returns:
        JsonResponse: Standard response format
    """
    request_id = get_request_id(request)
    return StandardResponse.success(
        data=data,
        message=message,
        status_code=status_code,
        request_id=request_id
    )


def api_error(request, code, message, details=None, status_code=400):
    """
    Create a standard API error response.
    
    Args:
        request: Django request object
        code: Error code (e.g., 'VALIDATION_ERROR')
        message: Error message
        details: Optional error details
        status_code: HTTP status code
        
    Returns:
        JsonResponse: Standard error response format
    """
    request_id = get_request_id(request)
    return StandardResponse.error(
        code=code,
        message=message,
        details=details,
        status_code=status_code,
        request_id=request_id
    )


def api_success(request, data=None, message=None):
    """
    Create a standard API success response (status 200).
    
    Args:
        request: Django request object
        data: Response data
        message: Optional success message
        
    Returns:
        JsonResponse: Standard success response format
    """
    return api_response(request, data=data, message=message, status_code=200)


def api_created(request, data=None, message=None):
    """
    Create a standard API created response (status 201).
    
    Args:
        request: Django request object
        data: Response data
        message: Optional success message
        
    Returns:
        JsonResponse: Standard success response format with 201 status
    """
    return api_response(request, data=data, message=message, status_code=201)


def api_paginated(request, items, page, page_size, total_items, message=None):
    """
    Create a standard API paginated response.
    
    Args:
        request: Django request object
        items: List of items
        page: Current page number
        page_size: Items per page
        total_items: Total number of items
        message: Optional success message
        
    Returns:
        JsonResponse: Standard paginated response format
    """
    request_id = get_request_id(request)
    return StandardResponse.paginated(
        items=items,
        page=page,
        page_size=page_size,
        total_items=total_items,
        message=message,
        request_id=request_id
    )
