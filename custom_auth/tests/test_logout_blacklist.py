"""
Phase 2 regression test: JWT logout blacklisting (workstream 9).

Proves the full flow: login -> refresh token issued -> logout -> refresh token rejected.
Before this fix, logout was a no-op against the token itself (SIMPLE_JWT already had
ROTATE_REFRESH_TOKENS/BLACKLIST_AFTER_ROTATION=True, but
rest_framework_simplejwt.token_blacklist was not installed), so a stolen refresh token
stayed valid for its full lifetime even after the legitimate user logged out.

Only one test exercises the real /login/ endpoint (login rate-limiting is real and
Redis-backed, and repeated hits within the test run would throttle each other); the
other two use RefreshToken.for_user() directly to set up tokens, matching the pattern
already used elsewhere in this test suite (e.g. orders/tests/test_views.py) - they're
about logout's tolerance for missing/invalid tokens, not login itself.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


def _make_user(email):
    return User.objects.create_user(
        email=email,
        password='testpass123456',
        phone_number='+2015555555' + email[-2:],
        is_mobile_verified=True,
        email_verified=True,
        user_type='customer',
    )


@pytest.mark.django_db
class TestLogoutBlacklistsRefreshToken:
    def setup_method(self):
        self.client = APIClient()
        self.client.defaults['HTTP_HOST'] = 'localhost'

    def test_login_logout_refresh_rejected(self):
        user = _make_user('logout_blacklist01@test.com')

        # 1. Login
        login_response = self.client.post(
            '/api/v1/auth/login/',
            {'email': user.email, 'password': 'testpass123456'},
            format='json',
        )
        assert login_response.status_code == 200, login_response.content
        tokens = login_response.json()['data']
        access = tokens['access']
        refresh = tokens['refresh']
        assert access and refresh

        # 2. Logout, sending the current refresh token.
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        logout_response = self.client.post('/api/v1/auth/logout/', {'refresh': refresh}, format='json')
        assert logout_response.status_code == 200, logout_response.content

        # 3. The refresh token must now be rejected.
        self.client.credentials()  # refresh endpoint doesn't require an access token
        refresh_after = self.client.post('/api/v1/auth/refresh/', {'refresh': refresh}, format='json')
        assert refresh_after.status_code == 401, refresh_after.content

    def test_logout_without_refresh_token_still_succeeds(self):
        """Backward compatibility: clients that don't send a refresh token must not
        get a broken logout - it just can't invalidate anything for them."""
        user = _make_user('logout_blacklist02@test.com')
        access = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')

        logout_response = self.client.post('/api/v1/auth/logout/', {}, format='json')
        assert logout_response.status_code == 200, logout_response.content

    def test_logout_with_already_invalid_refresh_token_still_succeeds(self):
        """An expired/garbage refresh token at logout time must not turn logout itself
        into a failure - the end goal (this token is unusable) already holds."""
        user = _make_user('logout_blacklist03@test.com')
        access = str(RefreshToken.for_user(user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')

        logout_response = self.client.post(
            '/api/v1/auth/logout/', {'refresh': 'not-a-real-token'}, format='json',
        )
        assert logout_response.status_code == 200, logout_response.content

    def test_refresh_token_rejected_via_direct_blacklist(self):
        """Direct proof that RefreshToken(...).blacklist() actually invalidates the
        token for the real /refresh/ endpoint, independent of the /login/ + /logout/
        HTTP round trip covered above."""
        user = _make_user('logout_blacklist04@test.com')
        refresh = RefreshToken.for_user(user)
        refresh_str = str(refresh)

        # Works before blacklisting.
        ok_response = self.client.post('/api/v1/auth/refresh/', {'refresh': refresh_str}, format='json')
        assert ok_response.status_code == 200, ok_response.content

        # SIMPLE_JWT.ROTATE_REFRESH_TOKENS rotates on every use - blacklist the
        # freshest token, matching what logout would actually receive from a client.
        latest_refresh = ok_response.json()['refresh']
        RefreshToken(latest_refresh).blacklist()

        rejected_response = self.client.post('/api/v1/auth/refresh/', {'refresh': latest_refresh}, format='json')
        assert rejected_response.status_code == 401, rejected_response.content
