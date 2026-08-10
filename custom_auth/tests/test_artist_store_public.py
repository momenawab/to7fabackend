"""
Phase 3 regression test: public artist/store list + detail endpoints
(API Contract, Part A workstream 4).

Confirmed-404 backstory: Flutter's ArtistService/StoreService
(lib/core/services/artist_service.dart, store_service.dart) call
GET /api/auth/api/artists/ (paginated list, with page/page_size/featured/search query
params) and GET /api/auth/api/artists/<id>/ (detail) - only top/featured/search-with-
required-q existed before Phase 3, so both were confirmed 404s. Verified via Django's
resolve() during the Phase 3 API sweep, not just inferred from source.

Also proves the two brand-new endpoints (artist_list/artist_detail/store_list/
store_detail) never include `user.email` - "do not expose private or administrative
data" is a Part A acceptance criterion.

Phase 3 left one tension unresolved: top_artists/search_artists/top_stores/
search_stores (all pre-existing, AllowAny) temporarily kept include_email=True
because admin_panel/templates/admin_panel/artists_stores.html's JS genuinely
rendered artist.email/store.email from them, and no authenticated alternative
existed. Phase 4 Part 7.3 resolved it: added admin_top_artists()/admin_top_stores()
(IsAuthenticated + IsAdminUser), repointed the template at those, and switched all
four public endpoints back to include_email=False. TestSiblingEndpointsNoLongerLeakEmail
and TestAdminArtistStoreEndpoints below replace the old
TestSiblingEndpointsStillCarryEmailForAdminDashboard, which asserted the opposite
(email present) as a documented interim state.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from custom_auth.models import Artist, Store

User = get_user_model()


def _make_user(email, **extra):
    return User.objects.create_user(
        email=email,
        password='testpass123456',
        phone_number='+2010' + email[-8:].rjust(8, '0'),
        is_mobile_verified=True,
        email_verified=True,
        user_type=extra.pop('user_type', 'customer'),
        **extra,
    )


@pytest.fixture
def client():
    c = APIClient()
    c.defaults['HTTP_HOST'] = 'localhost'
    return c


def _make_artist(email, is_verified, **fields):
    """Creating a User with user_type='artist' auto-creates its Artist profile via a
    post_save signal (custom_auth/signals.py) - update the auto-created row rather
    than Artist.objects.create()-ing a second one (would violate the OneToOne)."""
    user = _make_user(email, user_type='artist', **{
        k: fields.pop(k) for k in ('first_name', 'last_name') if k in fields
    })
    artist = Artist.objects.get(user=user)
    for key, value in {**fields, 'is_verified': is_verified}.items():
        setattr(artist, key, value)
    artist.save()
    return artist


def _make_store(email, is_verified, **fields):
    user = _make_user(email, user_type='store')
    store = Store.objects.get(user=user)
    for key, value in {**fields, 'is_verified': is_verified}.items():
        setattr(store, key, value)
    store.save()
    return store


@pytest.fixture
def verified_artist(db):
    return _make_artist(
        'artist_pub@test.com', True, first_name='Amina', last_name='Test',
        specialty='painting', bio='Paints things',
    )


@pytest.fixture
def unverified_artist(db):
    return _make_artist(
        'artist_unverified@test.com', False, first_name='Nour', last_name='Test',
        specialty='sculpture',
    )


@pytest.fixture
def verified_store(db):
    return _make_store('store_pub@test.com', True, store_name='Test Store', tax_id='TAX123')


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        email='artist_store_admin@test.com', password='testpass123456',
        phone_number='+201099999999', is_mobile_verified=True, email_verified=True,
        user_type='customer', is_staff=True,
    )


@pytest.mark.django_db
class TestArtistListEndpoint:
    def test_confirmed_404_route_now_resolves(self, client):
        """The exact route Flutter's ArtistService hits - was a 404 before Phase 3."""
        response = client.get('/api/auth/api/artists/')
        assert response.status_code == 200

    def test_lists_only_verified_artists(self, client, verified_artist, unverified_artist):
        response = client.get('/api/auth/api/artists/')
        ids = [a['id'] for a in response.json()['results']]
        assert str(verified_artist.user.id) in ids
        assert str(unverified_artist.user.id) not in ids

    def test_response_shape_matches_flutter_expectations(self, client, verified_artist):
        """Flutter's getArtists() reads data['results']/data['count']/data['next']/
        data['previous'] - the DRF PageNumberPagination default shape, not the
        {success, data} envelope used elsewhere in this codebase."""
        response = client.get('/api/auth/api/artists/')
        data = response.json()
        assert set(['count', 'next', 'previous', 'results']).issubset(data.keys())

    def test_no_email_leak(self, client, verified_artist):
        response = client.get('/api/auth/api/artists/')
        assert 'email' not in response.json()['results'][0]

    def test_featured_filter(self, client, verified_artist):
        verified_artist.is_featured_on_homepage = True
        verified_artist.save()
        other = _make_artist('artist_pub_2@test.com', True, is_featured_on_homepage=False)

        response = client.get('/api/auth/api/artists/', {'featured': 'true'})
        ids = [a['id'] for a in response.json()['results']]
        assert str(verified_artist.user.id) in ids
        assert str(other.user.id) not in ids

    def test_search_filter(self, client, verified_artist):
        response = client.get('/api/auth/api/artists/', {'search': 'Amina'})
        ids = [a['id'] for a in response.json()['results']]
        assert str(verified_artist.user.id) in ids

    def test_pagination_params_respected(self, client, verified_artist):
        response = client.get('/api/auth/api/artists/', {'page': 1, 'page_size': 1})
        assert response.status_code == 200


@pytest.mark.django_db
class TestArtistDetailEndpoint:
    def test_confirmed_404_route_now_resolves(self, client, verified_artist):
        """The exact route Flutter's ArtistService.getArtistById() hits."""
        response = client.get(f'/api/auth/api/artists/{verified_artist.user.id}/')
        assert response.status_code == 200
        assert response.json()['id'] == str(verified_artist.user.id)

    def test_unverified_artist_not_found(self, client, unverified_artist):
        response = client.get(f'/api/auth/api/artists/{unverified_artist.user.id}/')
        assert response.status_code == 404

    def test_nonexistent_artist_not_found(self, client):
        response = client.get('/api/auth/api/artists/999999/')
        assert response.status_code == 404

    def test_no_email_leak(self, client, verified_artist):
        response = client.get(f'/api/auth/api/artists/{verified_artist.user.id}/')
        assert 'email' not in response.json()


@pytest.mark.django_db
class TestStoreListAndDetailEndpoints:
    def test_confirmed_404_list_route_now_resolves(self, client):
        response = client.get('/api/auth/api/stores/')
        assert response.status_code == 200

    def test_confirmed_404_detail_route_now_resolves(self, client, verified_store):
        response = client.get(f'/api/auth/api/stores/{verified_store.user.id}/')
        assert response.status_code == 200
        assert response.json()['id'] == str(verified_store.user.id)

    def test_no_email_or_tax_id_leak_in_list(self, client, verified_store):
        response = client.get('/api/auth/api/stores/')
        result = response.json()['results'][0]
        assert 'email' not in result
        assert 'taxId' not in result

    def test_no_email_or_tax_id_leak_in_detail(self, client, verified_store):
        response = client.get(f'/api/auth/api/stores/{verified_store.user.id}/')
        data = response.json()
        assert 'email' not in data
        assert 'taxId' not in data


@pytest.mark.django_db
class TestSiblingEndpointsNoLongerLeakEmail:
    """Phase 4 Part 7.3: top_artists/search_artists/top_stores/search_stores are
    still AllowAny/no-auth (Flutter and any anonymous caller can reach them) and now
    never include email, matching artist_list/artist_detail/store_list/store_detail.
    Supersedes the old TestSiblingEndpointsStillCarryEmailForAdminDashboard, which
    documented the pre-Phase-4 leak as a temporarily-accepted tension."""

    def test_top_artists_no_email(self, client, verified_artist):
        verified_artist.is_featured_on_homepage = True
        verified_artist.save()
        response = client.get('/api/auth/api/artists/top/')
        results = response.json()['results']
        assert results
        assert all('email' not in r for r in results)

    def test_search_artists_no_email(self, client, verified_artist):
        response = client.get('/api/auth/api/artists/search/', {'q': 'Amina'})
        results = response.json()['results']
        assert results
        assert all('email' not in r for r in results)

    def test_top_stores_no_email_or_tax_id(self, client, verified_store):
        verified_store.is_featured_on_homepage = True
        verified_store.save()
        response = client.get('/api/auth/api/stores/top/')
        results = response.json()['results']
        assert results
        assert all('email' not in r and 'taxId' not in r for r in results)

    def test_search_stores_no_email(self, client, verified_store):
        response = client.get('/api/auth/api/stores/search/', {'q': 'Test Store'})
        results = response.json()['results']
        assert results
        assert all('email' not in r for r in results)


@pytest.mark.django_db
class TestAdminArtistStoreEndpoints:
    """Phase 4 Part 7.3: admin_top_artists()/admin_top_stores() - the authenticated
    replacement that now carries the email the public endpoints above no longer do.
    admin_panel/templates/admin_panel/artists_stores.html was repointed at these.

    Uses session login (client.force_login), not the JWT _auth() helper used
    elsewhere in this file: admin_panel is entirely Django-session-authenticated
    (admin_panel/views.py's login() uses django.contrib.auth.login()/@login_required
    throughout - there is no JWT issuance anywhere in the admin login flow), so these
    two endpoints are deliberately authentication_classes([SessionAuthentication]),
    not this project's JWT default. A JWT-only-auth admin endpoint would 401 on every
    real admin dashboard request."""

    def test_admin_top_artists_requires_auth(self, client, verified_artist):
        """An anonymous session request is rejected (403 - SessionAuthentication
        never issues a WWW-Authenticate challenge, so DRF's permission_denied()
        raises PermissionDenied rather than NotAuthenticated here; either way the
        request never reaches the view or sees email)."""
        verified_artist.is_featured_on_homepage = True
        verified_artist.save()
        response = client.get('/api/auth/api/admin/artists/top/')
        assert response.status_code == 403

    def test_admin_top_artists_rejects_non_staff(self, client, verified_artist):
        verified_artist.is_featured_on_homepage = True
        verified_artist.save()
        non_staff = _make_user('artist_store_nonstaff@test.com')
        client.force_login(non_staff)
        response = client.get('/api/auth/api/admin/artists/top/')
        assert response.status_code == 403

    def test_admin_top_artists_includes_email_for_staff(self, client, verified_artist, admin_user):
        verified_artist.is_featured_on_homepage = True
        verified_artist.save()
        client.force_login(admin_user)
        response = client.get('/api/auth/api/admin/artists/top/')
        assert response.status_code == 200
        results = response.json()['results']
        assert results
        assert all(r.get('email') == verified_artist.user.email for r in results if r['id'] == str(verified_artist.user.id))

    def test_admin_top_stores_requires_auth(self, client, verified_store):
        """See test_admin_top_artists_requires_auth's docstring for why this is 403."""
        verified_store.is_featured_on_homepage = True
        verified_store.save()
        response = client.get('/api/auth/api/admin/stores/top/')
        assert response.status_code == 403

    def test_admin_top_stores_rejects_non_staff(self, client, verified_store):
        verified_store.is_featured_on_homepage = True
        verified_store.save()
        non_staff = _make_user('store_store_nonstaff@test.com')
        client.force_login(non_staff)
        response = client.get('/api/auth/api/admin/stores/top/')
        assert response.status_code == 403

    def test_admin_top_stores_includes_email_but_not_tax_id_for_staff(self, client, verified_store, admin_user):
        verified_store.is_featured_on_homepage = True
        verified_store.save()
        client.force_login(admin_user)
        response = client.get('/api/auth/api/admin/stores/top/')
        assert response.status_code == 200
        results = response.json()['results']
        assert results
        assert all('email' in r and 'taxId' not in r for r in results)
