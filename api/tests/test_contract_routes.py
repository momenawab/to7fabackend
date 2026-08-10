"""
Phase 3 regression tests: API Contract, Part A workstream 7 (route sprawl) and the
canonical-contract decision documented in PHASE3_API_PAYMENT_REPORT.md.

Canonical contract = the legacy /api/... prefixes (per-app), because that's what
Flutter's services actually call at runtime (lib/core/services/*.dart hardcode legacy
paths; the /api/v1/ contract in api/urls.py is comprehensive but unused by the shipped
client - confirmed by grepping for ApiConfig/ApiEndpoints usage). /api/v1/ stays
routed (frozen, not deleted) - these tests prove that too.
"""
import pytest
from django.urls import resolve
from django.urls.exceptions import Resolver404
from django.test import Client


@pytest.mark.django_db
class TestDeadCustomAuthMountRemoved:
    """Phase 3 fix: to7fabackend/urls.py used to mount custom_auth.urls TWICE - once
    at 'api/auth/' (live, used by Flutter) and once at 'custom_auth/' (an internal
    Django app name leaking into the URL, confirmed dead by grepping Flutter and
    admin_panel templates for it - zero hits). Only the dead one was removed."""

    def test_custom_auth_prefix_no_longer_resolves(self):
        with pytest.raises(Resolver404):
            resolve('/custom_auth/register/')

    def test_api_auth_prefix_still_resolves(self):
        """The live mount must be untouched by the dead-mount removal."""
        match = resolve('/api/auth/register/')
        assert match is not None


@pytest.mark.django_db
class TestCanonicalLegacyContractResolves:
    """Confirmed-404 sweep from the Phase 3 API contract audit: every one of these is
    a route Flutter's services actually call (extracted from lib/core/services/*.dart
    literals), verified via Django's resolve(), not assumed from reading urls.py."""

    @pytest.mark.parametrize("path", [
        '/api/products/',
        '/api/products/featured/',
        '/api/products/search/',
        '/api/orders/',
        '/api/orders/create/',
        '/api/cart/',
        '/api/cart/merge/',
        '/api/wallet/',
        '/api/addresses/',
        '/api/auth/api/auth/send-otp/',
        '/api/auth/api/auth/verify-otp/',
        '/api/auth/seller/register/',
        '/api/auth/seller/application/status/',
        '/api/auth/api/artists/',      # was a confirmed 404 before Phase 3
        '/api/auth/api/stores/',       # was a confirmed 404 before Phase 3
    ])
    def test_route_resolves(self, path):
        match = resolve(path)
        assert match is not None

    @pytest.mark.parametrize("path,pk_path", [
        ('orders/1/acknowledge/', '/api/orders/1/acknowledge/'),
        ('orders/1/ship/', '/api/orders/1/ship/'),
        ('orders/1/deliver/', '/api/orders/1/deliver/'),
        ('orders seller status', '/api/orders/seller/1/status/'),
        ('products categories', '/api/products/categories/1/'),
        ('ar settings', '/api/products/ar/products/1/ar-settings/'),
    ])
    def test_pk_route_resolves(self, path, pk_path):
        match = resolve(pk_path)
        assert match is not None


@pytest.mark.django_db
class TestV1ContractFrozenNotDeleted:
    """The /api/v1/ contract (api/urls.py) is frozen for new work, not removed - it
    stays routed for whatever already depends on it (this suite's own Phase 2 tests
    hit /api/v1/auth/login/, for one)."""

    def test_v1_login_still_resolves(self):
        match = resolve('/api/v1/auth/login/')
        assert match is not None

    def test_v1_prefix_still_mounted_in_root_urlconf(self):
        from django.urls import get_resolver
        patterns = [str(p.pattern) for p in get_resolver().url_patterns]
        assert any('api/v1/' in p for p in patterns)
