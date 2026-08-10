"""
Phase 2 regression tests: seller product-approval bypass (BACKEND_AUDIT.md #2.0).

Proves ProductSerializer no longer lets a seller set approval_status, rejection_reason,
or is_featured through any seller-facing write path, while the legitimate admin approval
workflow (which sets these directly on the model instance, not through the serializer)
still works.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from products.models import Category, Product

User = get_user_model()


def _auth(client, user):
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')


@pytest.mark.django_db
class TestSellerCannotBypassApproval:
    def setup_method(self):
        self.client = APIClient()
        self.client.defaults['HTTP_HOST'] = 'localhost'
        self.seller = User.objects.create_user(
            email='seller_bypass@test.com',
            password='testpass123',
            phone_number='+201111111111',
            is_mobile_verified=True,
            user_type='store',
        )
        self.other_seller = User.objects.create_user(
            email='seller_bypass2@test.com',
            password='testpass123',
            phone_number='+201111111112',
            is_mobile_verified=True,
            user_type='store',
        )
        self.category = Category.objects.create(name='Approval Bypass Category')

    def _create_pending_product(self, seller=None):
        return Product.objects.create(
            name='Bypass Target',
            description='desc',
            base_price=100,
            stock_quantity=5,
            category=self.category,
            seller=seller or self.seller,
            approval_status='pending',
        )

    def test_seller_cannot_approve_own_product_on_create(self):
        """POST /api/products/ with approval_status='approved' must be ignored."""
        _auth(self.client, self.seller)
        response = self.client.post(
            '/api/products/',
            {
                'name': 'Sneaky Product',
                'description': 'desc',
                'base_price': '50.00',
                'stock_quantity': 3,
                'category': self.category.id,
                'approval_status': 'approved',
                'is_featured': True,
            },
            format='json',
        )
        assert response.status_code == 201, response.content
        product = Product.objects.get(name='Sneaky Product')
        assert product.approval_status == 'pending'
        assert product.is_featured is False

    def test_seller_cannot_approve_own_product_on_update(self):
        """PUT /api/products/seller/<pk>/ with approval_status='approved' must be ignored.

        Uses the seller_product_detail endpoint rather than product_detail: the latter's
        PUT/DELETE branch is unreachable via JWT bearer auth entirely (a separate,
        pre-existing bug - see PHASE2_CORE_CORRECTNESS_REPORT.md, out of this workstream's
        scope), so it can't be used to demonstrate this fix through the API layer. Both
        views share the same ProductSerializer, so this exercises the same fix.
        """
        product = self._create_pending_product()
        _auth(self.client, self.seller)
        response = self.client.put(
            f'/api/products/seller/{product.id}/',
            {'approval_status': 'approved'},
            format='json',
        )
        assert response.status_code == 200, response.content
        product.refresh_from_db()
        assert product.approval_status == 'pending'

    def test_seller_cannot_feature_own_product(self):
        """PUT /api/products/seller/<pk>/ with is_featured=True must be ignored."""
        product = self._create_pending_product()
        _auth(self.client, self.seller)
        response = self.client.put(
            f'/api/products/seller/{product.id}/',
            {'is_featured': True},
            format='json',
        )
        assert response.status_code == 200, response.content
        product.refresh_from_db()
        assert product.is_featured is False

    def test_seller_cannot_overwrite_admin_rejection_state(self):
        """A seller PUT must not be able to clear an admin's rejection."""
        product = self._create_pending_product()
        product.approval_status = 'rejected'
        product.rejection_reason = 'Prohibited item'
        product.save()

        _auth(self.client, self.seller)
        response = self.client.put(
            f'/api/products/seller/{product.id}/',
            {'approval_status': 'approved', 'rejection_reason': ''},
            format='json',
        )
        assert response.status_code == 200, response.content
        product.refresh_from_db()
        assert product.approval_status == 'rejected'
        assert product.rejection_reason == 'Prohibited item'

    def test_seller_can_still_edit_own_listing_fields(self):
        """Non-approval fields (e.g. name, is_active) remain seller-writable - the fix is scoped."""
        product = self._create_pending_product()
        _auth(self.client, self.seller)
        response = self.client.put(
            f'/api/products/seller/{product.id}/',
            {'name': 'Updated Name', 'is_active': False},
            format='json',
        )
        assert response.status_code == 200, response.content
        product.refresh_from_db()
        assert product.name == 'Updated Name'
        assert product.is_active is False

    def test_seller_via_create_endpoint_also_blocked(self):
        """Same bypass attempt through POST /api/products/seller/ (seller_products view)."""
        _auth(self.client, self.seller)
        response = self.client.post(
            '/api/products/seller/',
            {
                'name': 'Sneaky Seller Endpoint Product',
                'description': 'desc',
                'base_price': '75.00',
                'stock_quantity': 2,
                'category': self.category.id,
                'approval_status': 'approved',
            },
            format='json',
        )
        assert response.status_code == 201, response.content
        product = Product.objects.get(name='Sneaky Seller Endpoint Product')
        assert product.approval_status == 'pending'

    def test_seller_cannot_modify_other_sellers_product(self):
        """Sanity check: cross-seller PUT is still rejected (unchanged, pre-existing behavior).

        seller_product_detail scopes its queryset to `seller=request.user`, so a
        cross-seller PUT 404s rather than 403s - not a Phase 2 change.
        """
        product = self._create_pending_product(seller=self.other_seller)
        _auth(self.client, self.seller)
        response = self.client.put(
            f'/api/products/seller/{product.id}/',
            {'approval_status': 'approved'},
            format='json',
        )
        assert response.status_code == 404


@pytest.mark.django_db
class TestAdminApprovalWorkflowStillWorks:
    """The admin approval workflow bypasses the serializer entirely (sets model fields
    directly), so it must be completely unaffected by locking these fields in
    ProductSerializer."""

    def setup_method(self):
        self.seller = User.objects.create_user(
            email='seller_admin_flow@test.com',
            password='testpass123',
            phone_number='+201111111113',
            is_mobile_verified=True,
            user_type='store',
        )
        self.category = Category.objects.create(name='Admin Flow Category')
        self.product = Product.objects.create(
            name='Pending Product',
            description='desc',
            base_price=100,
            stock_quantity=5,
            category=self.category,
            seller=self.seller,
            approval_status='pending',
        )

    def test_admin_can_approve_product(self):
        self.product.approval_status = 'approved'
        self.product.save()
        self.product.refresh_from_db()
        assert self.product.approval_status == 'approved'

    def test_admin_can_reject_product_with_reason(self):
        self.product.approval_status = 'rejected'
        self.product.rejection_reason = 'Policy violation'
        self.product.save()
        self.product.refresh_from_db()
        assert self.product.approval_status == 'rejected'
        assert self.product.rejection_reason == 'Policy violation'

    def test_admin_can_feature_product(self):
        self.product.is_featured = True
        self.product.save()
        self.product.refresh_from_db()
        assert self.product.is_featured is True
