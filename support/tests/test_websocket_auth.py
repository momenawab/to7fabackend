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

What IS tested here, directly and without any ASGI harness: authenticate_user(), the
actual security-relevant unit both the old (query-string) and new (subprotocol) code
paths share - it's a plain method taking a token string and returning a user, with no
dependency on how the token reached the consumer. This proves the auth logic itself is
correct; only the transport-level "where does the token come from" wiring in connect()
is not covered by an automated test.
"""
import pytest
from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import RefreshToken

from support.consumers import SupportConsumer

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
