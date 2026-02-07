"""
Request ID Middleware

This middleware handles request_id generation and tracking for all API requests.
Following API Response Standard defined in API_RESPONSE_STANDARD.md
"""

import uuid
from django.utils.deprecation import MiddlewareMixin


class RequestIDMiddleware(MiddlewareMixin):
    """
    Middleware to handle request_id generation and tracking.
    
    Single source of truth: request.request_id
    
    Flow:
    1. Check if client provided X-Request-ID header
    2. Generate UUID if not provided
    3. Attach to request.request_id
    4. Add to response headers (X-Request-ID)
    """
    
    def process_request(self, request):
        # Check if client provided request_id via header
        request_id = request.headers.get('X-Request-ID')
        
        # Generate new ID if not provided
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # Attach to request (single source of truth)
        request.request_id = request_id
    
    def process_response(self, request, response):
        # Add request_id to response headers
        if hasattr(request, 'request_id'):
            response['X-Request-ID'] = request.request_id
        return response
