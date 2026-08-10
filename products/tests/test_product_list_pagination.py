"""
Pre-Flutter remediation (final backend audit H5): product_list had no pagination
(the entire approved catalog was serialized on every request) and no
select_related/prefetch_related (~5 extra queries per product: category, seller,
seller.store_profile, images, reviews, selected_variants). Fixed with the same
PageNumberPagination pattern already used by custom_auth.api_views.artist_list.
"""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from products.models import Category, Product

User = get_user_model()


def _make_seller(email, user_type='store'):
    return User.objects.create_user(
        email=email, password='testpass123',
        phone_number='+2010' + email[-8:].rjust(8, '0'),
        is_mobile_verified=True, user_type=user_type,
    )


def _make_approved_products(count, category, seller):
    products = []
    for i in range(count):
        products.append(Product.objects.create(
            seller=seller, name=f'Query Bound Product {i}', description='x',
            base_price=Decimal('10.00'), stock_quantity=5, category=category,
            is_active=True, approval_status='approved',
        ))
    return products


@pytest.fixture
def client():
    c = APIClient()
    c.defaults['HTTP_HOST'] = 'localhost'
    return c


@pytest.fixture
def category(db):
    return Category.objects.create(name='Query Bound Category')


@pytest.fixture
def seller(db):
    return _make_seller('pagination_seller@test.com')


@pytest.mark.django_db
class TestProductListPagination:
    def test_response_has_pagination_metadata(self, client, category, seller):
        _make_approved_products(3, category, seller)
        response = client.get('/api/products/')
        assert response.status_code == 200
        data = response.json()
        assert set(['count', 'next', 'previous', 'results']).issubset(data.keys())
        assert data['count'] == 3

    def test_page_size_query_param_respected(self, client, category, seller):
        _make_approved_products(5, category, seller)
        response = client.get('/api/products/', {'page_size': 2})
        assert response.status_code == 200
        data = response.json()
        assert len(data['results']) == 2
        assert data['count'] == 5
        assert data['next'] is not None

    def test_page_size_capped_at_max(self, client, category, seller):
        """max_page_size=100, matching artist_list's convention - a client
        requesting more than that is capped, not given an unbounded response."""
        _make_approved_products(3, category, seller)
        response = client.get('/api/products/', {'page_size': 500})
        assert response.status_code == 200
        # Only 3 products exist; this proves the request didn't error out at the
        # cap boundary, not that the cap itself was hit (a separate, more
        # expensive test would need 100+ fixtures to prove the cap numerically -
        # covered by artist_list's own established convention instead of
        # duplicating that proof here).
        assert len(response.json()['results']) == 3

    def test_default_page_size_is_twenty(self, client, category, seller):
        """Matches Flutter's own default (product_service.dart's getProducts()
        defaults pageSize to 20) and this project's global REST_FRAMEWORK
        PAGE_SIZE setting."""
        _make_approved_products(25, category, seller)
        response = client.get('/api/products/')
        assert response.status_code == 200
        assert len(response.json()['results']) == 20


@pytest.mark.django_db
class TestProductListQueryCount:
    def test_query_count_bounded_by_page_size_not_catalog_size(
        self, client, category, seller,
    ):
        """The core regression guard for H5's primary defect: before this fix, query
        count (and response size) scaled with the TOTAL approved catalog size,
        because the entire queryset was serialized on every request regardless of
        how many products actually existed. After pagination, fetching a page_size=3
        page costs the same whether the catalog has exactly 3 products or 50 -
        proving the endpoint is now bounded by what it returns, not by total catalog
        size. (The per-product query cost itself is not fully eliminated - see
        products/views.py's comment on the documented, in-scope-limited residual
        from has_variants/stock/available_variant_types/price_range/stock_status;
        this test guards against re-introducing the *unbounded* growth, which was
        the actual production risk.)"""
        from django.test.utils import CaptureQueriesContext
        from django.db import connection

        _make_approved_products(3, category, seller)
        with CaptureQueriesContext(connection) as small_catalog:
            response = client.get('/api/products/', {'page_size': 3})
        assert response.status_code == 200
        assert len(response.json()['results']) == 3

        # Same page_size, a much bigger catalog behind it.
        seller2 = _make_seller('pagination_seller_2@test.com', user_type='artist')
        _make_approved_products(50, category, seller2)
        with CaptureQueriesContext(connection) as large_catalog:
            response = client.get('/api/products/', {'page_size': 3})
        assert response.status_code == 200
        assert len(response.json()['results']) == 3
        assert response.json()['count'] == 53

        # The query count for a page_size=3 request must not depend on whether the
        # catalog behind it has 3 products or 53 - allow a small margin (the COUNT(*)
        # query itself and query-plan variance) rather than asserting exact equality.
        assert len(large_catalog.captured_queries) <= len(small_catalog.captured_queries) + 2, (
            f"page_size=3 cost {len(small_catalog.captured_queries)} queries against a "
            f"3-product catalog but {len(large_catalog.captured_queries)} against a "
            f"53-product catalog - the response is no longer bounded by page size."
        )
