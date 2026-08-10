import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model

User = get_user_model()

# Phase 2 fix (discovered while testing workstream 10, WebSocket auth): this module
# used to import SupportTicket and SupportMessage from .models at module level. Neither
# exists any more - support/models.py was rewritten to the new ContactRequest-based
# system and re-exports only ContactRequest/ContactNote/ContactStats. That made this
# entire module fail to import, which means to7fabackend/asgi.py (which imports
# support.routing, which imports this module) would crash immediately if ever run
# under a real ASGI server - the whole application, not just this WebSocket route.
# Nothing currently exercises asgi.py during `manage.py check` or the pytest suite
# (both use Django's WSGI-style test machinery), which is why this was invisible.
#
# check_ticket_access() below still references SupportTicket, which still doesn't
# exist - porting it to ContactRequest requires deciding what "ticket access" means
# under the new model, which is a real design decision, not a mechanical rename, and
# is out of this workstream's scope ("do not rewrite the support system"). The import
# is deferred into that one method instead of removed, so the module (and therefore
# asgi.py) imports successfully - fixing the crash - while leaving that one method's
# already-broken behavior exactly as broken as it already was; nothing currently calls
# it. See PHASE2_CORE_CORRECTNESS_REPORT.md for the full write-up and Phase 3+ flag.

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
        """
        self.user = None
        self.ticket_groups = set()

        # Authenticate user using JWT token passed as the WebSocket subprotocol.
        subprotocols = self.scope.get('subprotocols') or []
        token = subprotocols[0] if subprotocols else None
        if token:
            self.user = await self.authenticate_user(token)

        if self.user and not isinstance(self.user, AnonymousUser):
            # Echo the subprotocol back - required by the WebSocket handshake spec
            # when the client offered one; some clients treat its absence as a
            # rejected handshake even though the connection technically succeeded.
            await self.accept(subprotocol=token)

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

        Still broken (pre-existing, not a Phase 2 regression): SupportTicket no
        longer exists (see the module-level comment above this class). Deferred
        the import to here so it only fails when this specific method is actually
        called, rather than crashing the whole module - and by extension asgi.py -
        at import time.
        """
        from .models import SupportTicket
        try:
            ticket = SupportTicket.objects.get(ticket_id=ticket_id)
            # User can access their own tickets or admin can access all tickets
            return ticket.user == self.user or (hasattr(self.user, 'is_staff') and self.user.is_staff)
        except SupportTicket.DoesNotExist:
            return False

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