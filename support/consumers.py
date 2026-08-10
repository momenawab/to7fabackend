import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model

User = get_user_model()

# Phase 2 fix (workstream 10, WebSocket auth): this module used to import SupportTicket
# and SupportMessage from .models at module level. Neither exists any more -
# support/models.py was rewritten to the new ContactRequest-based system and re-exports
# only ContactRequest/ContactNote/ContactStats. That made this entire module fail to
# import, which means to7fabackend/asgi.py (which imports support.routing, which
# imports this module) would crash immediately if ever run under a real ASGI server -
# the whole application, not just this WebSocket route. Phase 2 stopped the crash by
# deferring the import into check_ticket_access() only.
#
# Phase 3 fix: check_ticket_access() is now ported to ContactRequest for real (see
# below), keyed on contact_number (the identifier support/views.create_ticket already
# returns to clients as "ticket_id" - there was never a separate ticket ID scheme).


def extract_token_and_subprotocol(subprotocols):
    """Parse the WebSocket subprotocol list into (token, subprotocol_to_echo).

    Pulled out of connect() as a plain function so the parsing logic itself is
    unit-testable without an ASGI test harness (see support/tests/test_websocket_auth.py
    for why channels.testing/daphne aren't available here).

    Handles the two shapes actually in play:
    - ('authorization', <token>): what the real Flutter client sends
      (lib/core/services/websocket_service.dart: `protocols: ['authorization', token]`).
    - (<token>,): a bare single-value list, kept for any other client using the
      simpler scheme this consumer originally documented.
    Anything else (empty, or 2+ elements not starting with 'authorization') yields no
    token, so connect() closes the connection as unauthorized.
    """
    if len(subprotocols) >= 2 and subprotocols[0].lower() == 'authorization':
        return subprotocols[1], subprotocols[0]
    elif len(subprotocols) == 1:
        return subprotocols[0], subprotocols[0]
    return None, (subprotocols[0] if subprotocols else None)


class SupportConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Handle WebSocket connection.

        Phase 2 fix (BACKEND_AUDIT.md / PHASE2 workstream 10): the JWT used to be read
        from the query string (?token=...), which URLs commonly end up in proxy/access
        logs. Read it from the WebSocket subprotocol header (Sec-WebSocket-Protocol)
        instead - the client connects with `protocols: [<jwt>]`, which lives in a
        request header, not the logged URL. Chosen over an initial-authentication-
        message approach to keep this the same synchronous authenticate-then-
        accept-or-reject flow that was already here (same close code, same shape),
        rather than introducing a pending/unauthenticated connection state and a
        timeout for clients that never send an auth message.

        Phase 3 fix: Phase 2 assumed a single-element subprotocol list
        (`[<jwt>]`), but the actual Flutter client
        (lib/core/services/websocket_service.dart) connects with
        `protocols: ['authorization', token]` - a fixed label plus the token, two
        elements. Reading `subprotocols[0]` therefore grabbed the literal string
        "authorization", never the token, and every real connection from the app
        would have been rejected as unauthorized. Now handles both shapes: a
        ('authorization', <token>) pair (what the app actually sends) or a bare
        single-element [<token>] list (kept for any other/future client using the
        simpler scheme this was originally documented as).
        """
        self.user = None
        self.ticket_groups = set()

        # Authenticate user using JWT token passed as the WebSocket subprotocol.
        subprotocols = self.scope.get('subprotocols') or []
        token, offered_subprotocol = extract_token_and_subprotocol(subprotocols)

        if token:
            self.user = await self.authenticate_user(token)

        if self.user and not isinstance(self.user, AnonymousUser):
            # Echo the subprotocol back - required by the WebSocket handshake spec
            # when the client offered one; some clients treat its absence as a
            # rejected handshake even though the connection technically succeeded.
            # Must echo one of the values the client actually offered (RFC 6455
            # 4.2.2), not the raw token - in the ('authorization', token) shape the
            # token itself was never an offered subprotocol value.
            await self.accept(subprotocol=offered_subprotocol)

            # Send connection confirmation
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'message': 'WebSocket connection established',
                'user_id': self.user.id
            }))
        else:
            await self.close(code=4001)  # Unauthorized

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave all ticket groups
        for group_name in self.ticket_groups:
            await self.channel_layer.group_discard(group_name, self.channel_name)

    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'join_ticket':
                await self.join_ticket(data.get('ticket_id'))
            elif message_type == 'leave_ticket':
                await self.leave_ticket(data.get('ticket_id'))
            elif message_type == 'typing':
                await self.handle_typing(data.get('ticket_id'), data.get('is_typing', False))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))

    async def join_ticket(self, ticket_id):
        """Join a specific ticket group for real-time updates"""
        if not ticket_id:
            return
            
        # Verify user has access to this ticket
        has_access = await self.check_ticket_access(ticket_id)
        if not has_access:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Access denied to this ticket'
            }))
            return

        group_name = f'support_ticket_{ticket_id}'
        await self.channel_layer.group_add(group_name, self.channel_name)
        self.ticket_groups.add(group_name)

        await self.send(text_data=json.dumps({
            'type': 'joined_ticket',
            'ticket_id': ticket_id
        }))

    async def leave_ticket(self, ticket_id):
        """Leave a specific ticket group"""
        if not ticket_id:
            return
            
        group_name = f'support_ticket_{ticket_id}'
        await self.channel_layer.group_discard(group_name, self.channel_name)
        self.ticket_groups.discard(group_name)

        await self.send(text_data=json.dumps({
            'type': 'left_ticket',
            'ticket_id': ticket_id
        }))

    async def handle_typing(self, ticket_id, is_typing):
        """Handle typing indicators"""
        if not ticket_id:
            return
            
        group_name = f'support_ticket_{ticket_id}'
        await self.channel_layer.group_send(group_name, {
            'type': 'typing_indicator',
            'ticket_id': ticket_id,
            'user_id': self.user.id,
            'user_name': self.user.get_full_name() or self.user.email,
            'is_typing': is_typing
        })

    # Group message handlers
    async def support_message(self, event):
        """Send support message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'support_message',
            'ticket_id': event['ticket_id'],
            'message': event['message']
        }))

    async def ticket_updated(self, event):
        """Send ticket update to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'ticket_updated',
            'ticket_id': event['ticket_id'],
            'update_type': event.get('update_type', 'general')
        }))

    async def typing_indicator(self, event):
        """Send typing indicator to WebSocket"""
        # Don't send typing indicator back to the sender
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing_indicator',
                'ticket_id': event['ticket_id'],
                'user_name': event['user_name'],
                'is_typing': event['is_typing']
            }))

    @database_sync_to_async
    def authenticate_user(self, token):
        """Authenticate user using JWT token"""
        try:
            UntypedToken(token)
            from rest_framework_simplejwt.authentication import JWTAuthentication
            jwt_auth = JWTAuthentication()
            validated_token = jwt_auth.get_validated_token(token)
            user = jwt_auth.get_user(validated_token)
            return user
        except (InvalidToken, TokenError):
            return AnonymousUser()

    @database_sync_to_async
    def check_ticket_access(self, ticket_id):
        """Check if user has access to the ticket.

        Phase 3 fix: ported to the real model. There is no SupportTicket any more -
        support/views.create_ticket (the only place "ticket_id" was ever handed to a
        client) creates a ContactRequest and returns its `contact_number` as
        "ticket_id". So `ticket_id` here IS a ContactRequest.contact_number; join
        groups are named accordingly in join_ticket()/leave_ticket().

        Access rule mirrors the REST API's own authorization exactly rather than
        inventing a new one:
        - Staff: always allowed (matches ContactDetailView's permission_classes =
          [IsAdminUser], the only REST endpoint that reads a single contact today).
        - Regular authenticated user: allowed only if they are the ContactRequest's
          own `user` FK (matches the one identity-safe branch of
          UserContactListView's queryset). Deliberately does NOT also match by phone
          number or name the way UserContactListView's *list* filter does - that
          fuzzy matching is fine for "which of my own submissions show up in my
          list" but is not an identity check, and would let one user read another's
          support conversation by guessing/spoofing a phone number. Using it here
          would be a real authorization bug, not just a stricter rule.
        """
        from .contact_models import ContactRequest
        if self.user is None or isinstance(self.user, AnonymousUser):
            return False
        if getattr(self.user, 'is_staff', False):
            return True
        return ContactRequest.objects.filter(
            contact_number=ticket_id, user=self.user
        ).exists()

# Utility function to send real-time updates
def send_ticket_update(ticket_id, message_data=None, update_type='message'):
    """Send real-time update for a ticket"""
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    
    channel_layer = get_channel_layer()
    group_name = f'support_ticket_{ticket_id}'
    
    if update_type == 'message' and message_data:
        async_to_sync(channel_layer.group_send)(group_name, {
            'type': 'support_message',
            'ticket_id': ticket_id,
            'message': message_data
        })
    else:
        async_to_sync(channel_layer.group_send)(group_name, {
            'type': 'ticket_updated',
            'ticket_id': ticket_id,
            'update_type': update_type
        })

def send_typing_indicator(ticket_id, user_name, is_typing):
    """Send typing indicator for a ticket"""
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    
    channel_layer = get_channel_layer()
    group_name = f'support_ticket_{ticket_id}'
    
    async_to_sync(channel_layer.group_send)(group_name, {
        'type': 'typing_indicator',
        'ticket_id': ticket_id,
        'user_name': user_name,
        'is_typing': is_typing,
        'user_id': 0  # Admin user ID
    })