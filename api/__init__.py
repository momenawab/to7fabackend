"""
API Response Standard Package

This package provides standardized response formatting for the TO7FA Django REST backend.

Components:
- utils/response.py: StandardResponse helper class
- middleware/request_id.py: RequestIDMiddleware for request tracking
- exceptions.py: custom_exception_handler for standardized error handling
- views.py: BaseAPIView with helper methods
- urls.py: API v1 URL routing

Usage:
    from api.utils.response import StandardResponse
    from api.views import BaseAPIView
    
    class MyAPIView(BaseAPIView):
        def get(self, request):
            return self.success_response(data={"key": "value"})
"""

__version__ = '1.0.0'
__author__ = 'TO7FA Team'

# Export key components for convenience
from .utils.response import StandardResponse
from .views import BaseAPIView

__all__ = [
    'StandardResponse',
    'BaseAPIView',
]
