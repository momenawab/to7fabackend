"""
Base API View

This module provides a base view class for consistent response handling.
Following API Response Standard defined in API_RESPONSE_STANDARD.md
"""

from rest_framework import viewsets
from rest_framework.response import Response
from .utils.response import StandardResponse


class BaseAPIView(viewsets.ViewSet):
    """
    Base view with standard response handling.
    
    All API views should inherit from this class to get access to:
    - get_request_id(): Extract request_id from request
    - success_response(): Return standard success response
    - error_response(): Return standard error response
    - paginated_response(): Return paginated response
    """
    
    def get_request_id(self):
        """
        Get request_id from request.
        
        Returns:
            str: The request_id or None if not available
        """
        return getattr(self.request, 'request_id', None)
    
    def success_response(self, data, message=None, status_code=200):
        """
        Return standard success response.
        
        Args:
            data: The actual response payload
            message: Human-readable success message (optional)
            status_code: HTTP status code (default: 200)
        
        Returns:
            JsonResponse with standard success format
        """
        return StandardResponse.success(
            data=data,
            message=message,
            status_code=status_code,
            request_id=self.get_request_id()
        )
    
    def error_response(self, code, message, details=None, status_code=400):
        """
        Return standard error response.
        
        Args:
            code: Machine-readable error code (UPPER_SNAKE_CASE)
            message: Human-readable error message
            details: Additional error details (optional)
            status_code: HTTP status code (default: 400)
        
        Returns:
            JsonResponse with standard error format
        """
        return StandardResponse.error(
            code=code,
            message=message,
            details=details,
            status_code=status_code,
            request_id=self.get_request_id()
        )
    
    def paginated_response(self, items, page, page_size, total_items, message=None):
        """
        Return paginated response.
        
        Args:
            items: Array of result items
            page: Current page number (1-indexed)
            page_size: Number of items per page
            total_items: Total number of items
            message: Human-readable success message (optional)
        
        Returns:
            JsonResponse with standard paginated format
        """
        return StandardResponse.paginated(
            items=items,
            page=page,
            page_size=page_size,
            total_items=total_items,
            message=message,
            request_id=self.get_request_id()
        )
