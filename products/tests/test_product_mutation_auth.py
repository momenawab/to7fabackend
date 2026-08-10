"""
Phase 4 regression test (Part 7.1): product_detail's PUT/DELETE branch was
unreachable via JWT auth. `@authentication_classes([])` stripped every authenticator
from the view, so request.user was unconditionally AnonymousUser no matter what
Bearer token was sent - the seller-ownership branch's `is_authenticated` check always
failed with 401, meaning no seller could ever edit or delete their own product
through the real mobile client. Found and documented (not fixed - correctly out of
scope) in Phase 2 (PHASE2_CORE_CORRECTNESS_REPORT.md); fixed this phase by removing
the stray decorator.
"""
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from products.models import Category, Product

User = get_user_model()


def _auth(client, user):
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')


@pytest.mark.django_db
class TestProductMutationAuthentication:
    def setup_method(self):
        self.client = APIClient()
        self.client.defaults['HTTP_HOST'] = 'localhost'
        self.seller = User.objects.create_user(
            email='mutation_seller@test.com', password='testpass123',
            phone_number='+201111111121', is_mobile_verified=True, user_type='store',
        )
        self.other_user = User.objects.create_user(
            email='mutation_other@test.com', password='testpass123',
            phone_number='+201111111122', is_mobile_verified=True, user_type='customer',
        )
        self.category = Category.objects.create(name='Mutation Test Category')
        self.product = Product.objects.create(
            seller=self.seller, name='Mutation Test Product', description='x',
            base_price=Decimal('50.00'), stock_quantity=10, category=self.category,
            is_active=True, approval_status='approved',
        )

    def test_owner_can_update_product_with_valid_jwt(self):
        """The confirmed-broken case: before the fix, this always 401'd regardless
        of a valid Bearer token, because request.user was forced to AnonymousUser."""
        _auth(self.client, self.seller)
        response = self.client.put(
            f'/api/products/{self.product.id}/', {'name': 'Updated Name'}, format='json',
        )
        assert response.status_code == 200
        self.product.refresh_from_db()
        assert self.product.name == 'Updated Name'

    def test_owner_can_delete_product_with_valid_jwt(self):
        _auth(self.client, self.seller)
        response = self.client.delete(f'/api/products/{self.product.id}/')
        assert response.status_code == 200
        assert not Product.objects.filter(id=self.product.id).exists()

    def test_unauthenticated_put_rejected(self):
        response = self.client.put(
            f'/api/products/{self.product.id}/', {'name': 'Hacked'}, format='json',
        )
        assert response.status_code == 401
        self.product.refresh_from_db()
        assert self.product.name != 'Hacked'

    def test_non_owner_put_rejected(self):
        """Authenticated as a real, valid user - just not this product's seller."""
        _auth(self.client, self.other_user)
        response = self.client.put(
            f'/api/products/{self.product.id}/', {'name': 'Hacked'}, format='json',
        )
        assert response.status_code == 403
        self.product.refresh_from_db()
        assert self.product.name != 'Hacked'

    def test_non_owner_delete_rejected(self):
        _auth(self.client, self.other_user)
        response = self.client.delete(f'/api/products/{self.product.id}/')
        assert response.status_code == 403
        assert Product.objects.filter(id=self.product.id).exists()

    def test_get_still_public_no_auth_required(self):
        """GET must remain reachable without authentication - only PUT/DELETE needed
        the fix."""
        response = self.client.get(f'/api/products/{self.product.id}/')
        assert response.status_code == 200
