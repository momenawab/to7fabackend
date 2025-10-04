"""
Health check endpoints for container orchestration
"""
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import redis
from django.conf import settings


def health_check(request):
    """
    Basic health check endpoint
    Returns 200 if service is running
    """
    return JsonResponse({
        'status': 'healthy',
        'service': 'to7fa-backend'
    })


def readiness_check(request):
    """
    Readiness check - verifies all dependencies are ready
    Checks: Database, Redis
    """
    health_status = {
        'status': 'ready',
        'checks': {}
    }

    # Check database connection
    try:
        connection.ensure_connection()
        health_status['checks']['database'] = 'ok'
    except Exception as e:
        health_status['status'] = 'not_ready'
        health_status['checks']['database'] = f'error: {str(e)}'

    # Check Redis connection
    try:
        redis_host = settings.CHANNEL_LAYERS['default']['CONFIG']['hosts'][0][0]
        redis_port = settings.CHANNEL_LAYERS['default']['CONFIG']['hosts'][0][1]
        r = redis.Redis(host=redis_host, port=redis_port, db=0)
        r.ping()
        health_status['checks']['redis'] = 'ok'
    except Exception as e:
        health_status['status'] = 'not_ready'
        health_status['checks']['redis'] = f'error: {str(e)}'

    status_code = 200 if health_status['status'] == 'ready' else 503
    return JsonResponse(health_status, status=status_code)


def liveness_check(request):
    """
    Liveness check - verifies service is alive (not deadlocked)
    Simple check that returns 200
    """
    return JsonResponse({
        'status': 'alive'
    })
