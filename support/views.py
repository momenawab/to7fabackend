from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404
from django.http import Http404
from .models import SupportCategory, SupportTicket, SupportMessage, SupportAttachment
from .serializers import (
    SupportCategorySerializer, SupportTicketSerializer, SupportTicketDetailSerializer,
    SupportMessageSerializer, CreateTicketSerializer, CreateMessageSerializer
)


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class SupportPagination(PageNumberPagination):
    """Custom pagination for support endpoints"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


# Public API endpoints for mobile app users
@api_view(['GET'])
def get_support_categories(request):
    """Get all active support categories for ticket creation"""
    categories = SupportCategory.objects.filter(is_active=True).order_by('order', 'name')
    serializer = SupportCategorySerializer(categories, many=True)
    return Response({
        'success': True,
        'categories': serializer.data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_tickets(request):
    """Get user's support tickets with pagination"""
    tickets = SupportTicket.objects.filter(user=request.user).select_related(
        'category', 'assigned_to'
    ).prefetch_related('messages')
    
    # Filter by status if provided
    status_filter = request.query_params.get('status')
    if status_filter and status_filter != 'all':
        tickets = tickets.filter(status=status_filter)
    
    # Search functionality
    search = request.query_params.get('search')
    if search:
        tickets = tickets.filter(
            Q(ticket_id__icontains=search) |
            Q(subject__icontains=search) |
            Q(description__icontains=search)
        )
    
    # Pagination
    paginator = SupportPagination()
    page = paginator.paginate_queryset(tickets, request)
    
    serializer = SupportTicketSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ticket_detail(request, ticket_id):
    """Get detailed view of a specific ticket with messages"""
    try:
        ticket = SupportTicket.objects.select_related(
            'category', 'assigned_to', 'user'
        ).prefetch_related(
            'messages__sender', 'attachments'
        ).get(ticket_id=ticket_id, user=request.user)
    except SupportTicket.DoesNotExist:
        return Response({
            'error': 'Ticket not found or you do not have permission to view it'
        }, status=status.HTTP_404_NOT_FOUND)
    
    serializer = SupportTicketDetailSerializer(ticket)
    return Response({
        'success': True,
        'ticket': serializer.data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_ticket(request):
    """Create a new support ticket"""
    serializer = CreateTicketSerializer(data=request.data)
    if serializer.is_valid():
        ticket = serializer.save(
            user=request.user,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Create initial message with ticket description
        SupportMessage.objects.create(
            ticket=ticket,
            sender=request.user,
            message=ticket.description,
            message_type='user'
        )
        
        # Return ticket details
        response_serializer = SupportTicketDetailSerializer(ticket)
        return Response({
            'success': True,
            'message': 'Support ticket created successfully',
            'ticket': response_serializer.data
        }, status=status.HTTP_201_CREATED)
    
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_message(request, ticket_id):
    """Add a message to an existing ticket"""
    try:
        ticket = SupportTicket.objects.get(ticket_id=ticket_id, user=request.user)
    except SupportTicket.DoesNotExist:
        return Response({
            'error': 'Ticket not found or you do not have permission to access it'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Don't allow messages on closed tickets
    if ticket.status == 'closed':
        return Response({
            'error': 'Cannot add messages to closed tickets'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = CreateMessageSerializer(data=request.data)
    if serializer.is_valid():
        message = serializer.save(
            ticket=ticket,
            sender=request.user,
            message_type='user'
        )
        
        # Update ticket status if it was resolved
        if ticket.status == 'resolved':
            ticket.status = 'open'
            ticket.save(update_fields=['status', 'updated_at'])
        
        response_serializer = SupportMessageSerializer(message)
        return Response({
            'success': True,
            'message': 'Message added successfully',
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)
    
    return Response({
        'success': False,
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rate_ticket(request, ticket_id):
    """Rate a resolved/closed ticket"""
    try:
        ticket = SupportTicket.objects.get(
            ticket_id=ticket_id, 
            user=request.user,
            status__in=['resolved', 'closed']
        )
    except SupportTicket.DoesNotExist:
        return Response({
            'error': 'Ticket not found, not accessible, or not in a rateable state'
        }, status=status.HTTP_404_NOT_FOUND)
    
    rating = request.data.get('rating')
    feedback = request.data.get('feedback', '')
    
    if not rating or not (1 <= int(rating) <= 5):
        return Response({
            'error': 'Rating must be between 1 and 5'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    ticket.rating = int(rating)
    ticket.feedback = feedback
    ticket.save(update_fields=['rating', 'feedback'])
    
    return Response({
        'success': True,
        'message': 'Thank you for your feedback!'
    })


# Admin API endpoints
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_tickets(request):
    """Get all support tickets for admin panel"""
    tickets = SupportTicket.objects.select_related(
        'category', 'assigned_to', 'user'
    ).prefetch_related('messages')
    
    # Filter by status
    status_filter = request.query_params.get('status')
    if status_filter and status_filter != 'all':
        tickets = tickets.filter(status=status_filter)
    
    # Filter by priority
    priority_filter = request.query_params.get('priority')
    if priority_filter and priority_filter != 'all':
        tickets = tickets.filter(priority=priority_filter)
    
    # Filter by category
    category_filter = request.query_params.get('category')
    if category_filter and category_filter != 'all':
        tickets = tickets.filter(category_id=category_filter)
    
    # Filter by assigned user
    assigned_filter = request.query_params.get('assigned')
    if assigned_filter and assigned_filter != 'all':
        if assigned_filter == 'unassigned':
            tickets = tickets.filter(assigned_to__isnull=True)
        else:
            tickets = tickets.filter(assigned_to_id=assigned_filter)
    
    # Search
    search = request.query_params.get('search')
    if search:
        tickets = tickets.filter(
            Q(ticket_id__icontains=search) |
            Q(subject__icontains=search) |
            Q(user__email__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search)
        )
    
    # Pagination
    paginator = SupportPagination()
    page = paginator.paginate_queryset(tickets, request)
    
    serializer = SupportTicketSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_update_ticket(request, ticket_id):
    """Update ticket status, priority, assignment etc."""
    try:
        ticket = SupportTicket.objects.get(ticket_id=ticket_id)
    except SupportTicket.DoesNotExist:
        return Response({
            'error': 'Ticket not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    allowed_fields = ['status', 'priority', 'assigned_to']
    updated_fields = []
    
    for field in allowed_fields:
        if field in request.data:
            if field == 'assigned_to':
                # Handle assignment
                assigned_id = request.data[field]
                if assigned_id:
                    try:
                        from custom_auth.models import User
                        assigned_user = User.objects.get(id=assigned_id, is_staff=True)
                        setattr(ticket, field, assigned_user)
                    except User.DoesNotExist:
                        return Response({
                            'error': 'Invalid assigned user'
                        }, status=status.HTTP_400_BAD_REQUEST)
                else:
                    setattr(ticket, field, None)
            else:
                setattr(ticket, field, request.data[field])
            updated_fields.append(field)
    
    # Handle status changes
    if 'status' in request.data:
        if request.data['status'] == 'resolved' and not ticket.resolved_at:
            ticket.resolved_at = timezone.now()
            updated_fields.append('resolved_at')
        elif request.data['status'] == 'closed' and not ticket.closed_at:
            ticket.closed_at = timezone.now()
            updated_fields.append('closed_at')
    
    if updated_fields:
        updated_fields.append('updated_at')
        ticket.save(update_fields=updated_fields)
    
    serializer = SupportTicketDetailSerializer(ticket)
    return Response({
        'success': True,
        'message': 'Ticket updated successfully',
        'ticket': serializer.data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_reply_ticket(request, ticket_id):
    """Admin reply to a ticket"""
    try:
        ticket = SupportTicket.objects.get(ticket_id=ticket_id)
    except SupportTicket.DoesNotExist:
        return Response({
            'error': 'Ticket not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    message_text = request.data.get('message')
    is_internal = request.data.get('is_internal', False)
    
    if not message_text:
        return Response({
            'error': 'Message content is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    message = SupportMessage.objects.create(
        ticket=ticket,
        sender=request.user,
        message=message_text,
        message_type='admin',
        is_internal=is_internal
    )
    
    # Update ticket status if needed
    if ticket.status == 'open':
        ticket.status = 'in_progress'
        ticket.save(update_fields=['status', 'updated_at'])
    
    serializer = SupportMessageSerializer(message)
    return Response({
        'success': True,
        'message': 'Reply sent successfully',
        'data': serializer.data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_stats(request):
    """Get support statistics for admin dashboard"""
    stats = {
        'total_tickets': SupportTicket.objects.count(),
        'open_tickets': SupportTicket.objects.filter(status='open').count(),
        'in_progress_tickets': SupportTicket.objects.filter(status='in_progress').count(),
        'resolved_tickets': SupportTicket.objects.filter(status='resolved').count(),
        'closed_tickets': SupportTicket.objects.filter(status='closed').count(),
        'unassigned_tickets': SupportTicket.objects.filter(assigned_to__isnull=True).count(),
        'overdue_tickets': len([t for t in SupportTicket.objects.filter(status__in=['open', 'in_progress']) if t.is_overdue]),
    }
    
    # Tickets by category
    category_stats = SupportCategory.objects.annotate(
        ticket_count=Count('tickets')
    ).values('name', 'ticket_count')
    
    # Recent activity (last 7 days)
    from datetime import timedelta
    week_ago = timezone.now() - timedelta(days=7)
    recent_tickets = SupportTicket.objects.filter(created_at__gte=week_ago).count()
    
    return Response({
        'success': True,
        'stats': {
            **stats,
            'recent_tickets': recent_tickets,
            'category_stats': list(category_stats)
        }
    })