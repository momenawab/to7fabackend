"""
Phase 4 regression test (Part 7.2): debug_arabic_encoding removed.

Was a public (AllowAny), unauthenticated endpoint returning up to 3 real Category and
3 real Product rows with no approval/visibility filtering - unlike every real
product-listing endpoint (Product.objects.approved()) - so it could leak an
unapproved/rejected product's name and description to anyone. Confirmed dead
(grepped Flutter and admin_panel templates, zero hits) and removed entirely, both
routes it was reachable at.
"""
import pytest
from django.urls import resolve
from django.urls.exceptions import Resolver404


class TestDebugArabicEncodingRemoved:
    """Proven at the URL-resolution level (resolve()), not via a live HTTP request:
    this project's default 404 error page itself crashes for unrelated, pre-existing
    reasons (a template context-processor bug - confirmed by requesting a totally
    unrelated, always-nonexistent URL and observing the identical crash signature,
    `AttributeError: 'super' object has no attribute 'dicts'`, in Django's own
    django/template/context.py). That's a real, newly-discovered defect - flagged in
    PHASE4_PRODUCTION_READINESS_REPORT.md as a deferred finding - but it's orthogonal
    to this endpoint's removal and out of Part 7.2's scope to fix, so this test proves
    the removal precisely (the route no longer resolves to anything) rather than via
    an HTTP-level 404 status assertion that would fail for an unrelated reason.
    """

    def test_legacy_route_no_longer_resolves(self):
        with pytest.raises(Resolver404):
            resolve('/api/products/debug/arabic/')

    def test_v1_route_no_longer_resolves(self):
        with pytest.raises(Resolver404):
            resolve('/api/v1/debug/arabic/')

    def test_view_function_no_longer_exists(self):
        from products import views
        assert not hasattr(views, 'debug_arabic_encoding')
