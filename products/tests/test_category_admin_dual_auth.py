"""
Pre-Flutter remediation (final backend audit H4): manage_categories/create_category/
manage_category_detail/update_category/delete_category (the admin-prefixed category
CRUD views) already used the project's default JWT authentication correctly - the
bug was entirely in admin_panel/templates/admin_panel/category_management.html,
which sends this session-authenticated dashboard's requests with
'Authorization: Bearer ' + localStorage.getItem('access_token') - always literally
"Bearer null", since nothing in the admin login flow (django.contrib.auth.login(),
never JWT) ever populates that key. An invalid Bearer token makes JWTAuthentication
raise immediately, which stops DRF's authentication chain before it would ever have
tried a session cookie.

Fixed by (1) removing that header from the template and (2) adding
SessionAuthentication *alongside* (not instead of) the existing JWT default on these
five views - the real Flutter mobile app calls this exact endpoint prefix too
(lib/core/services/category_service.dart's getCategoriesHierarchical/createCategory/
updateCategory/deleteCategory, confirmed by reading the file, not assumed), so
switching to session-only would have broken it.

This file proves both callers now work and neither broke the other:
- TestCategoryAdminJwtAuthentication: the Flutter/mobile path (unchanged behavior).
- TestCategoryAdminSessionAuthentication: the admin-dashboard path (the actual fix),
  including one CSRF-enforcing test proving the template's existing
  X-CSRFToken/csrfmiddlewaretoken pattern genuinely satisfies DRF's CSRF check for
  session-authenticated mutations, not just verified by reading the template.
- TestCategoryAdminRejectsUnauthorized: neither credential type bypasses staff-only.
"""
import pytest
from django.contrib.auth import get_user_model
from django.middleware.csrf import get_token
from django.test import RequestFactory
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from products.models import Category

User = get_user_model()


def _jwt_auth(client, user):
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(
        email='category_admin_staff@test.com', password='testpass123',
        phone_number='+201111111141', is_mobile_verified=True,
        user_type='customer', is_staff=True,
    )


@pytest.fixture
def non_staff_user(db):
    return User.objects.create_user(
        email='category_admin_nonstaff@test.com', password='testpass123',
        phone_number='+201111111142', is_mobile_verified=True,
        user_type='customer',
    )


@pytest.fixture
def category(db):
    return Category.objects.create(name='Dual Auth Test Category')


@pytest.mark.django_db
class TestCategoryAdminJwtAuthentication:
    """The Flutter mobile app's path - must remain unaffected by the SessionAuthentication
    addition (it was already working via the project's default JWT auth)."""

    def setup_method(self):
        self.client = APIClient()
        self.client.defaults['HTTP_HOST'] = 'localhost'

    def test_jwt_staff_can_list(self, staff_user):
        _jwt_auth(self.client, staff_user)
        response = self.client.get('/api/products/admin/categories/')
        assert response.status_code == 200

    def test_jwt_staff_can_create(self, staff_user):
        _jwt_auth(self.client, staff_user)
        response = self.client.post(
            '/api/products/admin/categories/create/', {'name': 'JWT Created'}, format='json',
        )
        assert response.status_code in (200, 201)
        assert Category.objects.filter(name='JWT Created').exists()

    def test_jwt_staff_can_update(self, staff_user, category):
        _jwt_auth(self.client, staff_user)
        response = self.client.put(
            f'/api/products/admin/categories/{category.id}/update/',
            {'name': 'JWT Updated'}, format='json',
        )
        assert response.status_code == 200
        category.refresh_from_db()
        assert category.name == 'JWT Updated'

    def test_jwt_staff_can_delete(self, staff_user, category):
        _jwt_auth(self.client, staff_user)
        response = self.client.delete(f'/api/products/admin/categories/{category.id}/delete/')
        assert response.status_code == 204
        assert not Category.objects.filter(id=category.id).exists()


@pytest.mark.django_db
class TestCategoryAdminSessionAuthentication:
    """The admin_panel dashboard's path - the actual fix. Uses force_login (a real
    Django session, the same mechanism the browser has after admin_panel's session
    login) rather than a JWT."""

    def setup_method(self):
        self.client = APIClient()
        self.client.defaults['HTTP_HOST'] = 'localhost'

    def test_session_staff_can_list(self, staff_user):
        self.client.force_login(staff_user)
        response = self.client.get('/api/products/admin/categories/')
        assert response.status_code == 200

    def test_session_staff_can_create(self, staff_user):
        self.client.force_login(staff_user)
        response = self.client.post(
            '/api/products/admin/categories/create/', {'name': 'Session Created'}, format='json',
        )
        assert response.status_code in (200, 201)
        assert Category.objects.filter(name='Session Created').exists()

    def test_session_staff_can_update(self, staff_user, category):
        self.client.force_login(staff_user)
        response = self.client.put(
            f'/api/products/admin/categories/{category.id}/update/',
            {'name': 'Session Updated'}, format='json',
        )
        assert response.status_code == 200
        category.refresh_from_db()
        assert category.name == 'Session Updated'

    def test_session_staff_can_delete(self, staff_user, category):
        self.client.force_login(staff_user)
        response = self.client.delete(f'/api/products/admin/categories/{category.id}/delete/')
        assert response.status_code == 204
        assert not Category.objects.filter(id=category.id).exists()

    def test_csrf_enforcement_genuinely_satisfied_by_the_templates_own_pattern(self, staff_user):
        """Not just 'the template sends a header, trust it' - a real CSRF-enforcing
        client, a real cookie/token round-trip via Django's own get_token(), and the
        exact 'X-CSRFToken' header name category_management.html's JS actually sends.
        Proves the fix works end-to-end for session-authenticated mutations, not
        merely by reading the template."""
        client = APIClient(enforce_csrf_checks=True)
        client.defaults['HTTP_HOST'] = 'localhost'
        client.force_login(staff_user)

        # Obtain a real CSRF token/cookie the way the admin dashboard's own page
        # load does (Django's {% csrf_token %} calls get_token() under the hood).
        request = RequestFactory().get('/')
        request.session = client.session
        token = get_token(request)
        client.cookies['csrftoken'] = token

        response = client.post(
            '/api/products/admin/categories/create/',
            {'name': 'CSRF Verified Category'},
            format='json',
            HTTP_X_CSRFTOKEN=token,
        )
        assert response.status_code in (200, 201)
        assert Category.objects.filter(name='CSRF Verified Category').exists()

    def test_csrf_enforcement_rejects_missing_token(self, staff_user):
        """The negative case: a session-authenticated mutation with no CSRF token at
        all is rejected, proving enforce_csrf is genuinely active (not accidentally
        bypassed) rather than the positive test above passing for an unrelated
        reason."""
        client = APIClient(enforce_csrf_checks=True)
        client.defaults['HTTP_HOST'] = 'localhost'
        client.force_login(staff_user)
        response = client.post(
            '/api/products/admin/categories/create/',
            {'name': 'Should Not Be Created'},
            format='json',
        )
        assert response.status_code == 403
        assert not Category.objects.filter(name='Should Not Be Created').exists()


@pytest.mark.django_db
class TestCategoryAdminRejectsUnauthorized:
    def setup_method(self):
        self.client = APIClient()
        self.client.defaults['HTTP_HOST'] = 'localhost'

    def test_anonymous_rejected(self):
        response = self.client.get('/api/products/admin/categories/')
        assert response.status_code in (401, 403)

    def test_jwt_non_staff_rejected(self, non_staff_user):
        _jwt_auth(self.client, non_staff_user)
        response = self.client.get('/api/products/admin/categories/')
        assert response.status_code == 403

    def test_session_non_staff_rejected(self, non_staff_user):
        self.client.force_login(non_staff_user)
        response = self.client.get('/api/products/admin/categories/')
        assert response.status_code == 403
