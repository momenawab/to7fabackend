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
data" is a Part A acceptance criterion. The four *pre-existing* sibling endpoints
(top_artists/search_artists/top_stores/search_stores) deliberately still DO include
it - admin_panel/templates/admin_panel/artists_stores.html's own JS
(`artist.email`/`store.email`) genuinely renders it for the admin dashboard, confirmed
by grepping the template before stripping the field would have broken it. See
_public_artist_dict/_public_store_dict's docstring in api_views.py and
PHASE3_API_PAYMENT_REPORT.md for the full writeup of this tension.
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
class TestSiblingEndpointsStillCarryEmailForAdminDashboard:
    """top_artists/search_artists/top_stores/search_stores predate Phase 3. An
    email-stripping pass (matching artist_list/artist_detail/store_list/store_detail)
    was tried first, then reverted specifically for these four: grepping
    admin_panel/templates/ showed admin_panel/templates/admin_panel/artists_stores.html
    genuinely renders `artist.email`/`store.email` from these exact endpoints for the
    admin dashboard. Stripping it would have broken a real, currently-working feature
    - confirmed by reading the template, not assumed. taxId was never read by that
    template (grepped for it too) and stays stripped. This is a real, flagged tension
    (an AllowAny/no-auth endpoint carrying an admin-only field) - see
    PHASE3_API_PAYMENT_REPORT.md §1 for the Phase 4 recommendation (a separate
    authenticated admin endpoint)."""

    def test_top_artists_still_includes_email(self, client, verified_artist):
        verified_artist.is_featured_on_homepage = True
        verified_artist.save()
        response = client.get('/api/auth/api/artists/top/')
        results = response.json()['results']
        assert results
        assert all(r.get('email') == verified_artist.user.email for r in results if r['id'] == str(verified_artist.user.id))

    def test_search_artists_still_includes_email(self, client, verified_artist):
        response = client.get('/api/auth/api/artists/search/', {'q': 'Amina'})
        results = response.json()['results']
        assert results
        assert all('email' in r for r in results)

    def test_top_stores_still_includes_email_but_not_tax_id(self, client, verified_store):
        verified_store.is_featured_on_homepage = True
        verified_store.save()
        response = client.get('/api/auth/api/stores/top/')
        results = response.json()['results']
        assert results
        assert all('email' in r and 'taxId' not in r for r in results)

    def test_search_stores_still_includes_email(self, client, verified_store):
        response = client.get('/api/auth/api/stores/search/', {'q': 'Test Store'})
        results = response.json()['results']
        assert results
        assert all('email' in r for r in results)
