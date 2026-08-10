"""
Phase 4 Part 14: health check endpoint.

Deliberately minimal and public-safe: distinguishes app-up / DB connectivity / Redis
(cache) connectivity, and nothing else. No version numbers, no hostnames, no env var
names or values, no stack traces in the response body (a failure is logged
server-side via `logger.warning`, not echoed to the caller). See
PRODUCTION_READINESS.md for how this is expected to be wired into a deployment's
liveness/readiness checks.

Mounted at the project root (`to7fabackend/urls.py`), not under `api/urls.py` -
`api/urls.py` is the frozen v1 contract (Phase 3 decision) and this isn't a
versioned client-facing resource.
"""
import logging

from django.core.cache import cache
from django.db import connections
from django.db.utils import OperationalError
from django.http import JsonResponse

logger = logging.getLogger(__name__)

_CACHE_PROBE_KEY = 'health_check_probe'


def _check_database():
    try:
        connections['default'].cursor().execute('SELECT 1')
        return True
    except OperationalError:
        logger.warning('Health check: database connectivity check failed', exc_info=True)
        return False


def _check_cache():
    try:
        cache.set(_CACHE_PROBE_KEY, '1', timeout=5)
        return cache.get(_CACHE_PROBE_KEY) == '1'
    except Exception:
        # Redis/cache backends can raise a variety of connection-error types
        # depending on client library; any failure here means "not healthy", not
        # "crash the health check itself".
        logger.warning('Health check: cache connectivity check failed', exc_info=True)
        return False


def health_check(request):
    """GET /health/ - always returns JSON, never raises. 200 when every component is
    healthy, 503 otherwise. The app itself responding at all is the 'app health'
    signal; database and cache are checked explicitly."""
    checks = {
        'database': 'ok' if _check_database() else 'error',
        'cache': 'ok' if _check_cache() else 'error',
    }
    healthy = all(v == 'ok' for v in checks.values())
    return JsonResponse(
        {'status': 'ok' if healthy else 'degraded', 'checks': checks},
        status=200 if healthy else 503,
    )
