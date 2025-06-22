from django.shortcuts import render, get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Notification
from .serializers import NotificationSerializer

# Create your views here.

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_list(request):
    """Get all notifications for the authenticated user"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Get unread count
    unread_count = notifications.filter(is_read=False).count()
    
    # Optional filtering by type
    notification_type = request.query_params.get('type', None)
    if notification_type:
        notifications = notifications.filter(notification_type=notification_type)
    
    # Optional filtering by read status
    read_status = request.query_params.get('read', None)
    if read_status == 'true':
        notifications = notifications.filter(is_read=True)
    elif read_status == 'false':
        notifications = notifications.filter(is_read=False)
    
    # Pagination (simple implementation)
    limit = int(request.query_params.get('limit', 10))
    offset = int(request.query_params.get('offset', 0))
    notifications = notifications[offset:offset+limit]
    
    # Serialize the notifications
    serializer = NotificationSerializer(notifications, many=True)
    
    return Response({
        "count": unread_count,
        "results": serializer.data
    }, status=status.HTTP_200_OK)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, pk):
    """Mark a notification as read"""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.mark_as_read()
    serializer = NotificationSerializer(notification)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def mark_all_read(request):
    """Mark all notifications as read"""
    notifications = Notification.objects.filter(user=request.user, is_read=False)
    updated_count = notifications.count()
    notifications.update(is_read=True)
    return Response({
        "message": f"{updated_count} notifications marked as read",
        "count": 0  # New unread count is 0
    }, status=status.HTTP_200_OK)
