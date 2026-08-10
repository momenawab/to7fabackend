"""
Phase 2 regression test: WebSocket JWT authentication (workstream 10).

LIMITATION (documented per the Phase 2 brief's own guidance, not glossed over): this
project has no ASGI test server installed (`daphne` is not in requirements.txt - see
BACKEND_AUDIT.md's note on no production ASGI server being configured either).
channels.testing's package __init__ unconditionally imports daphne.testing
(channels/testing/__init__.py -> .live -> daphne.testing.DaphneProcess), so even the
lower-level ApplicationCommunicator is unimportable here without it. That means the full
WebSocket handshake - subprotocol negotiation, connect()'s accept()/close() branching -
cannot be exercised end-to-end in this environment without adding a new dependency,
which is out of Phase 2 scope (no production deployment / dependency changes beyond
what a workstream specifically requires).

What IS tested here, directly and without any ASGI harness: authenticate_user() (token
-> user resolution), extract_token_and_subprotocol() (subprotocol-list -> token
parsing, pulled out of connect() specifically so it's unit-testable), and
check_ticket_access() (contact_number -> access decision). Together these cover every
piece of connect()'s authorization logic except the literal accept()/close() ASGI
calls, which do need a real handshake to exercise.
"""
import pytest
from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import RefreshToken

from support.consumers import SupportConsumer, extract_token_and_subprotocol

User = get_user_model()


@pytest.fixture
def user(transactional_db):
    return User.objects.create_user(
        email='ws_auth@test.com',
        password='testpass123',
        user_type='customer',
    )


@pytest.mark.django_db(transaction=True)
class TestSupportConsumerAuthenticateUser:
    """transaction=True/transactional_db: authenticate_user() is wrapped in
    @database_sync_to_async, which runs the actual query in a separate thread. The
    default `db` fixture wraps each test in an uncommitted transaction that other
    threads can't see, so the thread-pool worker can't find the just-created user -
    needs a real (transactional_db) database connection instead."""
    def test_valid_token_resolves_to_correct_user(self, user):
        token = str(RefreshToken.for_user(user).access_token)
        consumer = SupportConsumer()

        result = async_to_sync(consumer.authenticate_user)(token)

        assert result.id == user.id
        assert not isinstance(result, AnonymousUser)

    def test_invalid_token_resolves_to_anonymous_user(self):
        consumer = SupportConsumer()

        result = async_to_sync(consumer.authenticate_user)('not-a-real-token')

        assert isinstance(result, AnonymousUser)

    def test_refresh_token_is_rejected_only_access_tokens_authenticate(self, user):
        """Sanity check that authenticate_user() validates token TYPE, not just
        signature - a refresh token (even a valid one) must not authenticate a
        WebSocket connection; only an access token should."""
        refresh = RefreshToken.for_user(user)
        consumer = SupportConsumer()

        result = async_to_sync(consumer.authenticate_user)(str(refresh))

        assert isinstance(result, AnonymousUser)


class TestSupportConsumerTokenSource:
    """Proves connect() now reads the token from the WebSocket subprotocol list, not
    the query string - the actual fix for this workstream. No ASGI harness needed:
    this only inspects the source, since scope['subprotocols'] parsing has no
    meaningful behavior to unit-test in isolation beyond "does the code read from the
    right place", which is best proven by reading it back out of the fixed file
    (channels.testing's unavailability, per the module docstring above, blocks a
    behavioral connect() test)."""

    def test_connect_no_longer_reads_query_string_for_token(self):
        import inspect
        source = inspect.getsource(SupportConsumer.connect)
        assert "query_string" not in source
        assert "scope.get('subprotocols'" in source or 'scope.get("subprotocols"' in source


class TestExtractTokenAndSubprotocol:
    """Phase 3 regression: Phase 2's connect() assumed a single-element subprotocol
    list (`[<jwt>]`). The real Flutter client
    (lib/core/services/websocket_service.dart) actually connects with
    `protocols: ['authorization', token]` - two elements, a fixed label first. Reading
    subprotocols[0] therefore grabbed the literal string "authorization" and never the
    token, so every real connection from the app would have failed authentication.
    Pulled the parsing into extract_token_and_subprotocol() specifically so this bug
    class is unit-testable without an ASGI harness."""

    def test_authorization_pair_extracts_second_element_as_token(self):
        token, echoed = extract_token_and_subprotocol(['authorization', 'the-jwt'])
        assert token == 'the-jwt'
        assert echoed == 'authorization'

    def test_authorization_pair_is_case_insensitive(self):
        token, echoed = extract_token_and_subprotocol(['Authorization', 'the-jwt'])
        assert token == 'the-jwt'

    def test_bare_single_token_still_supported(self):
        token, echoed = extract_token_and_subprotocol(['the-jwt'])
        assert token == 'the-jwt'
        assert echoed == 'the-jwt'

    def test_empty_subprotocols_yields_no_token(self):
        token, echoed = extract_token_and_subprotocol([])
        assert token is None
        assert echoed is None

    def test_two_elements_not_starting_with_authorization_yields_no_token(self):
        """Not a scheme this consumer understands - must not silently treat either
        element as a token."""
        token, echoed = extract_token_and_subprotocol(['some-other-scheme', 'value'])
        assert token is None


@pytest.fixture
def other_user(transactional_db):
    return User.objects.create_user(
        email='ws_auth_other@test.com',
        password='testpass123',
        user_type='customer',
    )


@pytest.fixture
def staff_user(transactional_db):
    return User.objects.create_user(
        email='ws_auth_staff@test.com',
        password='testpass123',
        user_type='customer',
        is_staff=True,
    )


@pytest.fixture
def contact_request(transactional_db, user):
    from support.contact_models import ContactRequest
    return ContactRequest.objects.create(
        user=user, name='Test User', phone='+201000000000',
        subject='Help', message='Something is broken',
    )


@pytest.mark.django_db(transaction=True)
class TestCheckTicketAccess:
    """Phase 3 regression: check_ticket_access() ported from the dead SupportTicket
    model to the real ContactRequest model, keyed on contact_number. Mirrors the REST
    API's own authorization (ContactDetailView is IsAdminUser-only; a regular user may
    only ever read their own via the `user` FK - see the method's docstring for why
    UserContactListView's fuzzy phone/name list-filter is deliberately NOT reused here
    for a single-record access decision)."""

    def test_owner_has_access(self, user, contact_request):
        consumer = SupportConsumer()
        consumer.user = user

        result = async_to_sync(consumer.check_ticket_access)(contact_request.contact_number)

        assert result is True

    def test_other_authenticated_user_denied(self, other_user, contact_request):
        consumer = SupportConsumer()
        consumer.user = other_user

        result = async_to_sync(consumer.check_ticket_access)(contact_request.contact_number)

        assert result is False

    def test_staff_has_access_to_any_contact(self, staff_user, contact_request):
        consumer = SupportConsumer()
        consumer.user = staff_user

        result = async_to_sync(consumer.check_ticket_access)(contact_request.contact_number)

        assert result is True

    def test_anonymous_user_denied(self, contact_request):
        consumer = SupportConsumer()
        consumer.user = AnonymousUser()

        result = async_to_sync(consumer.check_ticket_access)(contact_request.contact_number)

        assert result is False

    def test_nonexistent_contact_number_denied(self, user):
        consumer = SupportConsumer()
        consumer.user = user

        result = async_to_sync(consumer.check_ticket_access)('00000000')

        assert result is False


class TestAsgiImportSucceeds:
    """Phase 2's headline discovery: to7fabackend/asgi.py used to crash on import
    because this module (transitively imported via support.routing) imported
    SupportTicket/SupportMessage, which don't exist. Phase 2 stopped the crash by
    deferring that import; Phase 3 removes it entirely (check_ticket_access no longer
    needs it). This test is the actual regression guard for "ASGI starts successfully"
    - it doesn't need daphne or a running server, just a successful import, which is
    exactly what was broken."""

    def test_asgi_module_imports_without_error(self):
        import importlib
        import to7fabackend.asgi
        importlib.reload(to7fabackend.asgi)
