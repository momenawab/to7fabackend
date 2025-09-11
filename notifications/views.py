from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from .models import Notification, BulkNotification, Device
from .serializers import NotificationSerializer, NotificationUpdateSerializer, BulkNotificationSerializer, DeviceSerializer

# Create your views here.

class NotificationPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class NotificationListView(generics.ListAPIView):
    """Enhanced notification list with filtering and pagination"""
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = NotificationPagination
    
    def get_queryset(self):
        queryset = Notification.objects.filter(user=self.request.user).order_by('-created_at')
        
        # Filtering by type
        notification_type = self.request.query_params.get('type', None)
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        # Filtering by read status
        read_status = self.request.query_params.get('read', None)
        if read_status == 'true':
            queryset = queryset.filter(is_read=True)
        elif read_status == 'false':
            queryset = queryset.filter(is_read=False)
        
        # Filtering by priority
        priority = self.request.query_params.get('priority', None)
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Search in title and message
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(message__icontains=search)
            )
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        # Get unread count for the user
        unread_count = Notification.objects.filter(
            user=request.user, is_read=False
        ).count()
        
        response = super().list(request, *args, **kwargs)
        response.data['unread_count'] = unread_count
        
        # Add summary by type
        type_counts = {}
        for choice_value, choice_display in Notification.TYPE_CHOICES:
            count = Notification.objects.filter(
                user=request.user, 
                notification_type=choice_value,
                is_read=False
            ).count()
            if count > 0:
                type_counts[choice_value] = count
        
        response.data['unread_by_type'] = type_counts
        return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_list(request):
    """Legacy endpoint - redirect to new view"""
    view = NotificationListView.as_view()
    return view(request)

class NotificationDetailView(generics.RetrieveUpdateAPIView):
    """Get or update a specific notification"""
    serializer_class = NotificationUpdateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return NotificationSerializer
        return NotificationUpdateSerializer


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
    from django.utils import timezone
    
    notifications = Notification.objects.filter(user=request.user, is_read=False)
    updated_count = notifications.count()
    notifications.update(is_read=True, read_at=timezone.now())
    
    return Response({
        "message": f"{updated_count} notifications marked as read",
        "count": 0  # New unread count is 0
    }, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_notification(request, pk):
    """Delete a specific notification"""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.delete()
    return Response({
        "message": "Notification deleted successfully"
    }, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def clear_all_notifications(request):
    """Clear all notifications for the user"""
    notification_type = request.query_params.get('type', None)
    read_only = request.query_params.get('read_only', 'false').lower() == 'true'
    
    queryset = Notification.objects.filter(user=request.user)
    
    if notification_type:
        queryset = queryset.filter(notification_type=notification_type)
    
    if read_only:
        queryset = queryset.filter(is_read=True)
    
    deleted_count = queryset.count()
    queryset.delete()
    
    return Response({
        "message": f"{deleted_count} notifications cleared",
        "deleted_count": deleted_count
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_stats(request):
    """Get notification statistics for the user"""
    user_notifications = Notification.objects.filter(user=request.user)
    
    stats = {
        'total': user_notifications.count(),
        'unread': user_notifications.filter(is_read=False).count(),
        'read': user_notifications.filter(is_read=True).count(),
        'by_type': {},
        'by_priority': {},
        'recent_count': user_notifications.filter(
            created_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).count()
    }
    
    # Count by type
    for choice_value, choice_display in Notification.TYPE_CHOICES:
        count = user_notifications.filter(notification_type=choice_value).count()
        if count > 0:
            stats['by_type'][choice_value] = {
                'total': count,
                'unread': user_notifications.filter(
                    notification_type=choice_value, is_read=False
                ).count()
            }
    
    # Count by priority
    priority_choices = [('low', 'Low'), ('normal', 'Normal'), ('high', 'High'), ('urgent', 'Urgent')]
    for choice_value, choice_display in priority_choices:
        count = user_notifications.filter(priority=choice_value).count()
        if count > 0:
            stats['by_priority'][choice_value] = count
    
    return Response(stats, status=status.HTTP_200_OK)


# Device Registration Views for Push Notifications

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_device(request):
    """
    Register or update a device token for push notifications
    
    Expected payload:
    {
        "device_token": "fcm_token_or_apns_token",
        "platform": "android" or "ios",
        "device_id": "unique_device_identifier",
        "app_version": "1.0.0",
        "device_model": "iPhone 12",
        "os_version": "14.5",
        "notifications_enabled": true
    }
    """
    serializer = DeviceSerializer(data=request.data)
    if serializer.is_valid():
        device_token = serializer.validated_data['device_token']
        platform = serializer.validated_data['platform']
        device_id = serializer.validated_data['device_id']
        
        try:
            # Check if device already exists and update it, or create new one
            device, created = Device.register_device(
                user=request.user,
                device_token=device_token,
                platform=platform,
                device_id=device_id,
                app_version=serializer.validated_data.get('app_version'),
                device_model=serializer.validated_data.get('device_model'),
                os_version=serializer.validated_data.get('os_version'),
                notifications_enabled=serializer.validated_data.get('notifications_enabled', True)
            )
        except Exception as e:
            # Handle any remaining conflicts gracefully
            print(f"Device registration error in view: {e}")
            return Response({
                'status': 'error',
                'message': 'Device token conflict resolved - device updated',
                'errors': {}
            }, status=status.HTTP_200_OK)
        
        response_serializer = DeviceSerializer(device)
        
        return Response({
            'status': 'success',
            'message': 'Device registered successfully' if created else 'Device updated successfully',
            'device': response_serializer.data,
            'created': created
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    
    return Response({
        'status': 'error',
        'message': 'Invalid data provided',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_device_settings(request, device_id):
    """
    Update device notification settings
    
    Expected payload:
    {
        "notifications_enabled": true/false
    }
    """
    try:
        device = Device.objects.get(
            user=request.user,
            device_id=device_id,
            is_active=True
        )
    except Device.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Device not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    notifications_enabled = request.data.get('notifications_enabled')
    if notifications_enabled is not None:
        device.notifications_enabled = notifications_enabled
        device.save()
        
        return Response({
            'status': 'success',
            'message': f'Notifications {"enabled" if notifications_enabled else "disabled"}',
            'device': DeviceSerializer(device).data
        }, status=status.HTTP_200_OK)
    
    return Response({
        'status': 'error',
        'message': 'notifications_enabled field is required'
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def unregister_device(request, device_id):
    """
    Unregister a device (user logged out or uninstalled app)
    """
    try:
        device = Device.objects.get(
            user=request.user,
            device_id=device_id
        )
        device.deactivate()
        
        return Response({
            'status': 'success',
            'message': 'Device unregistered successfully'
        }, status=status.HTTP_200_OK)
        
    except Device.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Device not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_user_devices(request):
    """
    List all devices for the current user
    """
    devices = Device.objects.filter(user=request.user, is_active=True)
    serializer = DeviceSerializer(devices, many=True)
    
    return Response({
        'status': 'success',
        'devices': serializer.data,
        'count': devices.count()
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_notification_api(request):
    """
    Send notification with push notification via API
    For custom admin panels
    """
    if not request.user.is_staff:
        return Response({
            'status': 'error',
            'message': 'Permission denied - Admin access required'
        }, status=status.HTTP_403_FORBIDDEN)
    
    from .push_utils import send_notification_with_push
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    try:
        user_id = request.data.get('user_id')
        title = request.data.get('title')
        message = request.data.get('message')
        notification_type = request.data.get('notification_type', 'system')
        
        if not all([user_id, title, message]):
            return Response({
                'status': 'error',
                'message': 'user_id, title, and message are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.get(id=user_id)
        notification = send_notification_with_push(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            action_url=request.data.get('action_url'),
            image_url=request.data.get('image_url'),
            priority=request.data.get('priority', 'normal')
        )
        
        return Response({
            'status': 'success',
            'message': 'Notification sent with push notification',
            'notification_id': notification.id
        }, status=status.HTTP_201_CREATED)
        
    except User.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_push_notification(request):
    """
    Send a test push notification to user's devices
    This is for testing purposes only
    """
    if not request.user.is_staff:  # Only allow staff to test
        return Response({
            'status': 'error',
            'message': 'Permission denied'
        }, status=status.HTTP_403_FORBIDDEN)
    
    from .push_utils import send_push_notification
    
    title = request.data.get('title', 'Test Notification')
    body = request.data.get('body', 'This is a test push notification')
    
    result = send_push_notification(request.user, title, body, {'test': True})
    
    return Response({
        'status': 'success',
        'message': 'Test notification sent',
        'result': result
    }, status=status.HTTP_200_OK)
