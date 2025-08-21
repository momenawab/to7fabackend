import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model
from .models import SupportTicket, SupportMessage

User = get_user_model()

class SupportConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Handle WebSocket connection"""
        self.user = None
        self.ticket_groups = set()
        
        # Authenticate user using JWT token
        token = self.scope.get('query_string', b'').decode('utf-8')
        if token.startswith('token='):
            token = token[6:]  # Remove 'token=' prefix
            self.user = await self.authenticate_user(token)
        
        if self.user and not isinstance(self.user, AnonymousUser):
            await self.accept()
            
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
        """Check if user has access to the ticket"""
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