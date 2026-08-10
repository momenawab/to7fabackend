"""
Phase 2 regression tests: product visibility (BACKEND_AUDIT.md §4.2, PHASE2 workstream 3).

Proves an unapproved (pending/rejected) product is unreachable through every affected
public marketplace read path, while an approved product remains visible and a product
made inactive-but-approved-elsewhere is handled consistently.
"""
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from products.models import Category, FeaturedProduct, Product, ProductOffer, Review

User = get_user_model()


@pytest.mark.django_db
class TestProductVisibilityEverywhere:
    def setup_method(self):
        self.client = APIClient()
        self.client.defaults['HTTP_HOST'] = 'localhost'
        self.seller = User.objects.create_user(
            email='visibility_seller@test.com',
            password='testpass123',
            phone_number='+201222222221',
            is_mobile_verified=True,
            user_type='store',
        )
        self.category = Category.objects.create(name='Visibility Category')

        self.approved = Product.objects.create(
            name='Approved Product',
            description='Visible everywhere',
            base_price=100,
            stock_quantity=5,
            category=self.category,
            seller=self.seller,
            approval_status='approved',
            is_active=True,
        )
        self.pending = Product.objects.create(
            name='Pending Product',
            description='Not yet reviewed',
            base_price=100,
            stock_quantity=5,
            category=self.category,
            seller=self.seller,
            approval_status='pending',
            is_active=True,
        )
        self.rejected = Product.objects.create(
            name='Rejected Product',
            description='Should never be public',
            base_price=100,
            stock_quantity=5,
            category=self.category,
            seller=self.seller,
            approval_status='rejected',
            rejection_reason='Policy violation',
            is_active=True,
        )

    # --- product_list (already fixed pre-Phase-2, sanity check it still holds) ---

    def test_product_list_excludes_unapproved(self):
        """Pre-Flutter remediation (final audit H5): product_list switched from the
        api_success() {success, data} envelope to standard DRF pagination
        ({count, next, previous, results}, matching artist_list's convention) - reads
        response.json()['results'] now instead of ['data']. Contract-compatible with
        lib/core/services/product_service.dart's getProducts(), which already parses
        this exact paginated shape."""
        response = self.client.get('/api/products/')
        assert response.status_code == 200
        names = [p['name'] for p in response.json()['results']]
        assert 'Approved Product' in names
        assert 'Pending Product' not in names
        assert 'Rejected Product' not in names

    # --- product_detail (GET branch) ---

    def test_product_detail_shows_approved(self):
        response = self.client.get(f'/api/products/{self.approved.id}/')
        assert response.status_code == 200

    def test_product_detail_hides_pending(self):
        response = self.client.get(f'/api/products/{self.pending.id}/')
        assert response.status_code == 404

    def test_product_detail_hides_rejected(self):
        response = self.client.get(f'/api/products/{self.rejected.id}/')
        assert response.status_code == 404

    def test_product_detail_404_identical_for_missing_and_unapproved(self):
        """Existence of an unapproved product must not be distinguishable from a
        genuinely nonexistent one via the error response."""
        missing_response = self.client.get('/api/products/999999/')
        unapproved_response = self.client.get(f'/api/products/{self.pending.id}/')
        assert missing_response.status_code == unapproved_response.status_code == 404
        assert missing_response.json()['error']['code'] == unapproved_response.json()['error']['code']

    # --- product_search ---

    def test_search_excludes_unapproved(self):
        response = self.client.get('/api/products/search/', {'q': 'Product'})
        assert response.status_code == 200
        names = [p['name'] for p in response.json()['data']['results']]
        assert 'Approved Product' in names
        assert 'Pending Product' not in names
        assert 'Rejected Product' not in names

    # --- product_reviews ---

    def test_reviews_visible_for_approved_product(self):
        response = self.client.get(f'/api/products/{self.approved.id}/reviews/')
        assert response.status_code == 200

    def test_reviews_hidden_for_pending_product(self):
        response = self.client.get(f'/api/products/{self.pending.id}/reviews/')
        assert response.status_code == 404

    def test_reviews_hidden_for_rejected_product(self):
        response = self.client.get(f'/api/products/{self.rejected.id}/reviews/')
        assert response.status_code == 404

    # --- category_detail ---

    def test_category_detail_excludes_unapproved_direct_products(self):
        response = self.client.get(f'/api/products/categories/{self.category.id}/')
        assert response.status_code == 200
        names = [p['name'] for p in response.json()['data']['products']]
        assert 'Approved Product' in names
        assert 'Pending Product' not in names
        assert 'Rejected Product' not in names

    def test_category_detail_excludes_unapproved_subcategory_products(self):
        sub = Category.objects.create(name='Sub Category', parent=self.category)
        approved_sub = Product.objects.create(
            name='Approved Sub Product', description='d', base_price=10,
            stock_quantity=1, category=sub, seller=self.seller,
            approval_status='approved',
        )
        pending_sub = Product.objects.create(
            name='Pending Sub Product', description='d', base_price=10,
            stock_quantity=1, category=sub, seller=self.seller,
            approval_status='pending',
        )
        response = self.client.get(f'/api/products/categories/{self.category.id}/')
        names = [p['name'] for p in response.json()['data']['products']]
        assert 'Approved Sub Product' in names
        assert 'Pending Sub Product' not in names

    # --- latest_offers ---

    def test_latest_offers_excludes_unapproved(self):
        now = timezone.now()
        for product in (self.approved, self.pending, self.rejected):
            ProductOffer.objects.create(
                product=product,
                discount_percentage=20,
                start_date=now - timedelta(days=1),
                end_date=now + timedelta(days=1),
                is_active=True,
            )
        response = self.client.get('/api/products/latest-offers/')
        assert response.status_code == 200
        names = [p['name'] for p in response.json()['results']]
        assert 'Approved Product' in names
        assert 'Pending Product' not in names
        assert 'Rejected Product' not in names

    # --- featured_products ---

    def test_featured_products_excludes_unapproved(self):
        for product in (self.approved, self.pending, self.rejected):
            FeaturedProduct.objects.create(product=product, is_active=True)
        response = self.client.get('/api/products/featured/')
        assert response.status_code == 200
        names = [p['name'] for p in response.json()['results']]
        assert 'Approved Product' in names
        assert 'Pending Product' not in names
        assert 'Rejected Product' not in names

    # --- top_rated_products ---

    def test_top_rated_excludes_unapproved(self):
        customer = User.objects.create_user(
            email='visibility_customer@test.com',
            password='testpass123',
            phone_number='+201222222222',
            is_mobile_verified=True,
            user_type='customer',
        )
        for product in (self.approved, self.pending, self.rejected):
            Review.objects.create(product=product, user=customer, rating=5, comment='great')
        response = self.client.get('/api/products/top-rated/')
        assert response.status_code == 200
        names = [p['name'] for p in response.json()['results']]
        assert 'Approved Product' in names
        assert 'Pending Product' not in names
        assert 'Rejected Product' not in names

    # --- seller can still see their own unapproved products via seller endpoints ---

    def test_seller_can_still_see_own_pending_product_via_seller_endpoint(self):
        refresh_token = _refresh_for(self.seller)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh_token}')
        response = self.client.get(f'/api/products/seller/{self.pending.id}/')
        assert response.status_code == 200


def _refresh_for(user):
    from rest_framework_simplejwt.tokens import RefreshToken
    return str(RefreshToken.for_user(user).access_token)
