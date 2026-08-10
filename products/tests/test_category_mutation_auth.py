"""
Pre-Flutter remediation (final backend audit H3): category_list's POST branch and
category_detail's PUT/DELETE branch had `@authentication_classes([])` above them -
the exact bug class Phase 4 Part 7.1 fixed for product_detail. Stripping every
authenticator forced request.user to always be AnonymousUser regardless of a valid
JWT Bearer token, so their internal `if not request.user.is_authenticated` checks
could never pass - category create/update/delete were permanently unreachable via
JWT, for any user including real staff. Fixed by removing the stray decorator (same
fix as Part 7.1); these views now use the project's default JWT authentication.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from products.models import Category

User = get_user_model()


def _auth(client, user):
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')


@pytest.mark.django_db
class TestCategoryListMutationAuthentication:
    def setup_method(self):
        self.client = APIClient()
        self.client.defaults['HTTP_HOST'] = 'localhost'
        self.staff_user = User.objects.create_user(
            email='category_staff@test.com', password='testpass123',
            phone_number='+201111111131', is_mobile_verified=True,
            user_type='customer', is_staff=True,
        )
        self.non_staff_user = User.objects.create_user(
            email='category_nonstaff@test.com', password='testpass123',
            phone_number='+201111111132', is_mobile_verified=True,
            user_type='customer',
        )

    def test_get_still_public_no_auth_required(self):
        response = self.client.get('/api/products/categories/')
        assert response.status_code == 200

    def test_unauthenticated_post_rejected(self):
        """The confirmed-broken case: before the fix, this always 401'd via the
        internal check anyway, but for the wrong reason (request.user forced
        AnonymousUser). Still 401 after the fix, now for the intended reason."""
        response = self.client.post(
            '/api/products/categories/', {'name': 'Unauthorized Category'}, format='json',
        )
        assert response.status_code == 401
        assert not Category.objects.filter(name='Unauthorized Category').exists()

    def test_non_staff_post_rejected(self):
        _auth(self.client, self.non_staff_user)
        response = self.client.post(
            '/api/products/categories/', {'name': 'Non-Staff Category'}, format='json',
        )
        assert response.status_code == 403
        assert not Category.objects.filter(name='Non-Staff Category').exists()

    def test_staff_post_with_valid_jwt_creates_category(self):
        """Before the fix: always 401'd regardless of a valid Bearer token, because
        request.user was forced to AnonymousUser."""
        _auth(self.client, self.staff_user)
        response = self.client.post(
            '/api/products/categories/', {'name': 'Staff Created Category'}, format='json',
        )
        assert response.status_code == 201
        assert Category.objects.filter(name='Staff Created Category').exists()


@pytest.mark.django_db
class TestCategoryDetailMutationAuthentication:
    def setup_method(self):
        self.client = APIClient()
        self.client.defaults['HTTP_HOST'] = 'localhost'
        self.staff_user = User.objects.create_user(
            email='category_detail_staff@test.com', password='testpass123',
            phone_number='+201111111133', is_mobile_verified=True,
            user_type='customer', is_staff=True,
        )
        self.non_staff_user = User.objects.create_user(
            email='category_detail_nonstaff@test.com', password='testpass123',
            phone_number='+201111111134', is_mobile_verified=True,
            user_type='customer',
        )
        self.category = Category.objects.create(name='Mutation Test Category')

    def test_get_still_public_no_auth_required(self):
        response = self.client.get(f'/api/products/categories/{self.category.id}/')
        assert response.status_code == 200

    def test_unauthenticated_put_rejected(self):
        response = self.client.put(
            f'/api/products/categories/{self.category.id}/', {'name': 'Hacked'}, format='json',
        )
        assert response.status_code == 401
        self.category.refresh_from_db()
        assert self.category.name != 'Hacked'

    def test_unauthenticated_delete_rejected(self):
        response = self.client.delete(f'/api/products/categories/{self.category.id}/')
        assert response.status_code == 401
        assert Category.objects.filter(id=self.category.id).exists()

    def test_non_staff_put_rejected(self):
        _auth(self.client, self.non_staff_user)
        response = self.client.put(
            f'/api/products/categories/{self.category.id}/', {'name': 'Hacked'}, format='json',
        )
        assert response.status_code == 403
        self.category.refresh_from_db()
        assert self.category.name != 'Hacked'

    def test_non_staff_delete_rejected(self):
        _auth(self.client, self.non_staff_user)
        response = self.client.delete(f'/api/products/categories/{self.category.id}/')
        assert response.status_code == 403
        assert Category.objects.filter(id=self.category.id).exists()

    def test_staff_put_with_valid_jwt_updates_category(self):
        """Before the fix: always 401'd regardless of a valid Bearer token."""
        _auth(self.client, self.staff_user)
        response = self.client.put(
            f'/api/products/categories/{self.category.id}/',
            {'name': 'Updated By Staff'}, format='json',
        )
        assert response.status_code == 200
        self.category.refresh_from_db()
        assert self.category.name == 'Updated By Staff'

    def test_staff_delete_with_valid_jwt_deletes_category(self):
        _auth(self.client, self.staff_user)
        response = self.client.delete(f'/api/products/categories/{self.category.id}/')
        assert response.status_code == 200
        assert not Category.objects.filter(id=self.category.id).exists()
