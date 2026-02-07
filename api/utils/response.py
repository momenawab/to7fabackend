"""
API Response Standard Helper

This module provides standardized response formatting for all API endpoints.
Following the API Response Standard defined in API_RESPONSE_STANDARD.md
"""

from typing import Any, Optional
from django.http import JsonResponse
import uuid


class StandardResponse:
    """
    Standard response helper for consistent API responses.
    
    All responses follow this structure:
    - Success: {success: true, data: {...}, message: "...", request_id: "..."}
    - Error: {success: false, error: {code, message, details}, request_id: "..."}
    - Paginated: {success: true, data: {items: [...], pagination: {...}}, message: "...", request_id: "..."}
    """
    
    @staticmethod
    def success(
        data: Any,
        message: Optional[str] = None,
        status_code: int = 200,
        request_id: Optional[str] = None
    ) -> JsonResponse:
        """
        Return a standardized success response.
        
        Args:
            data: The actual response payload (object, array, or null)
            message: Human-readable success message (optional)
            status_code: HTTP status code (default: 200)
            request_id: Request ID for tracing (optional, will generate if not provided)
        
        Returns:
            JsonResponse with standard success format
        """
        response_data = {
            "success": True,
            "data": data,
            "message": message,
            "request_id": request_id or str(uuid.uuid4())
        }
        return JsonResponse(response_data, status=status_code)
    
    @staticmethod
    def error(
        code: str,
        message: str,
        details: Optional[Any] = None,
        status_code: int = 400,
        request_id: Optional[str] = None
    ) -> JsonResponse:
        """
        Return a standardized error response.
        
        Args:
            code: Machine-readable error code (UPPER_SNAKE_CASE)
            message: Human-readable error message
            details: Additional error details (field-specific errors, stack traces in dev)
            status_code: HTTP status code (default: 400)
            request_id: Request ID for tracing (optional, will generate if not provided)
        
        Returns:
            JsonResponse with standard error format
        """
        response_data = {
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "details": details
            },
            "request_id": request_id or str(uuid.uuid4())
        }
        return JsonResponse(response_data, status=status_code)
    
    @staticmethod
    def paginated(
        items: list,
        page: int,
        page_size: int,
        total_items: int,
        message: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> JsonResponse:
        """
        Return a paginated response.
        
        Args:
            items: Array of result items
            page: Current page number (1-indexed)
            page_size: Number of items per page
            total_items: Total number of items
            message: Human-readable success message (optional)
            request_id: Request ID for tracing (optional, will generate if not provided)
        
        Returns:
            JsonResponse with standard paginated format
        """
        total_pages = (total_items + page_size - 1) // page_size
        response_data = {
            "success": True,
            "data": {
                "items": items,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_items": total_items,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_previous": page > 1
                }
            },
            "message": message,
            "request_id": request_id or str(uuid.uuid4())
        }
        return JsonResponse(response_data, status=200)
