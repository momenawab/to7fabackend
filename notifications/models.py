from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

class Notification(models.Model):
    TYPE_CHOICES = (
        ('sale', 'Sale'),
        ('order_update', 'Order Update'),
        ('ticket_update', 'Ticket Update'),
        ('app_update', 'New App Update'),
        ('new_product', 'New Product from Liked Stores'),
        ('order', 'Order'),  # Keep for backward compatibility
        ('payment', 'Payment'),
        ('system', 'System'),
        ('promotion', 'Promotion'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    is_read = models.BooleanField(default=False)
    
    # Enhanced related object handling
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')
    
    # Additional fields for better functionality
    action_url = models.URLField(blank=True, null=True, help_text="URL to redirect when notification is tapped")
    image_url = models.URLField(blank=True, null=True, help_text="Image for notification")
    priority = models.CharField(max_length=10, choices=[
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], default='normal')
    
    # Push notification settings
    send_push = models.BooleanField(default=True)
    push_sent = models.BooleanField(default=False)
    push_sent_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Legacy fields for backward compatibility
    related_object_id = models.PositiveIntegerField(blank=True, null=True)
    related_object_type = models.CharField(max_length=50, blank=True, null=True)
    
    def __str__(self):
        return f"{self.notification_type} notification for {self.user.email}: {self.title}"
    
    class Meta:
        ordering = ['-created_at']
    
    @classmethod
    def create_notification(cls, user, title, message, notification_type, related_object=None):
        """Helper method to create a notification"""
        notification = cls(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type
        )
        
        if related_object:
            notification.related_object_id = related_object.id
            notification.related_object_type = related_object.__class__.__name__
            
        notification.save()
        return notification
    
    def mark_as_read(self):
        """Mark notification as read"""
        from django.utils import timezone
        self.is_read = True
        self.read_at = timezone.now()
        self.save()
        return True


class BulkNotification(models.Model):
    """Model for admin to create bulk notifications"""
    TARGET_CHOICES = (
        ('all_users', 'All Users'),
        ('buyers', 'All Buyers'),
        ('sellers', 'All Sellers'),
        ('active_users', 'Active Users (Last 30 Days)'),
        ('specific_users', 'Specific Users'),
    )
    
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=Notification.TYPE_CHOICES)
    target_audience = models.CharField(max_length=20, choices=TARGET_CHOICES)
    specific_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        blank=True,
        help_text="Only used when target_audience is 'specific_users'"
    )
    
    # Optional fields
    action_url = models.URLField(blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    priority = models.CharField(max_length=10, choices=[
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], default='normal')
    
    # Scheduling
    schedule_for = models.DateTimeField(null=True, blank=True, help_text="Leave empty to send immediately")
    
    # Status tracking
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    recipient_count = models.PositiveIntegerField(default=0)
    
    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='created_bulk_notifications'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Bulk Notification'
        verbose_name_plural = 'Bulk Notifications'
    
    def __str__(self):
        return f"Bulk notification: {self.title} ({self.target_audience})"
    
    def get_target_users(self):
        """Get the list of users to send notifications to"""
        from django.contrib.auth import get_user_model
        from django.utils import timezone
        from datetime import timedelta
        
        User = get_user_model()
        
        if self.target_audience == 'all_users':
            return User.objects.filter(is_active=True)
        elif self.target_audience == 'buyers':
            # Users who have made orders
            return User.objects.filter(is_active=True, user_type='buyer')
        elif self.target_audience == 'sellers':
            # Users who are sellers
            return User.objects.filter(is_active=True, user_type='seller')
        elif self.target_audience == 'active_users':
            # Users who logged in within last 30 days
            thirty_days_ago = timezone.now() - timedelta(days=30)
            return User.objects.filter(is_active=True, last_login__gte=thirty_days_ago)
        elif self.target_audience == 'specific_users':
            return self.specific_users.filter(is_active=True)
        
        return User.objects.none()
    
    def send_notifications(self):
        """Create individual notifications for all target users"""
        from django.utils import timezone
        
        if self.is_sent:
            return False, "Notifications already sent"
        
        users = self.get_target_users()
        notifications_created = []
        
        for user in users:
            notification = Notification.objects.create(
                user=user,
                title=self.title,
                message=self.message,
                notification_type=self.notification_type,
                action_url=self.action_url,
                image_url=self.image_url,
                priority=self.priority,
            )
            notifications_created.append(notification)
        
        # Update bulk notification status
        self.is_sent = True
        self.sent_at = timezone.now()
        self.recipient_count = len(notifications_created)
        self.save()
        
        return True, f"Sent {len(notifications_created)} notifications"


class Device(models.Model):
    """Model for storing user device tokens for push notifications"""
    PLATFORM_CHOICES = (
        ('ios', 'iOS'),
        ('android', 'Android'),
        ('web', 'Web'),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='devices'
    )
    device_token = models.CharField(
        max_length=500, 
        unique=True,
        help_text="FCM token for Android, APNs token for iOS"
    )
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES)
    device_id = models.CharField(
        max_length=255, 
        help_text="Unique device identifier"
    )
    app_version = models.CharField(max_length=50, blank=True, null=True)
    device_model = models.CharField(max_length=100, blank=True, null=True)
    os_version = models.CharField(max_length=50, blank=True, null=True)
    
    # Status tracking
    is_active = models.BooleanField(default=True)
    last_used = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Push notification settings
    notifications_enabled = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-last_used']
        unique_together = ['user', 'device_id', 'platform']
        verbose_name = 'Device'
        verbose_name_plural = 'Devices'
    
    def __str__(self):
        return f"{self.user.email} - {self.platform} - {self.device_model or 'Unknown'}"
    
    @classmethod
    def register_device(cls, user, device_token, platform, device_id, **kwargs):
        """Register or update a device token"""
        try:
            # First try to find by device_token to handle token reuse
            try:
                existing_device = cls.objects.get(device_token=device_token)
                # Update existing device with new user and info
                existing_device.user = user
                existing_device.device_id = device_id
                existing_device.platform = platform
                existing_device.app_version = kwargs.get('app_version')
                existing_device.device_model = kwargs.get('device_model')
                existing_device.os_version = kwargs.get('os_version')
                existing_device.is_active = True
                existing_device.notifications_enabled = kwargs.get('notifications_enabled', True)
                existing_device.save()
                return existing_device, False
            except cls.DoesNotExist:
                pass
            
            # Try to find by user, device_id, platform combination
            device, created = cls.objects.update_or_create(
                user=user,
                device_id=device_id,
                platform=platform,
                defaults={
                    'device_token': device_token,
                    'app_version': kwargs.get('app_version'),
                    'device_model': kwargs.get('device_model'),
                    'os_version': kwargs.get('os_version'),
                    'is_active': True,
                    'notifications_enabled': kwargs.get('notifications_enabled', True),
                }
            )
            return device, created
            
        except Exception as e:
            # If there's still a conflict, try to handle it gracefully
            print(f"Device registration error: {e}")
            # Find and return existing device
            try:
                existing_device = cls.objects.get(device_token=device_token)
                return existing_device, False
            except cls.DoesNotExist:
                raise e
    
    def deactivate(self):
        """Deactivate device (user logged out or uninstalled)"""
        self.is_active = False
        self.save()


class PushNotificationLog(models.Model):
    """Log push notification attempts for debugging and analytics"""
    STATUS_CHOICES = (
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
    )
    
    notification = models.ForeignKey(
        Notification, 
        on_delete=models.CASCADE, 
        related_name='push_logs'
    )
    device = models.ForeignKey(
        Device, 
        on_delete=models.CASCADE,
        related_name='push_logs'
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    response_data = models.JSONField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-sent_at']
        verbose_name = 'Push Notification Log'
        verbose_name_plural = 'Push Notification Logs'
    
    def __str__(self):
        return f"{self.notification.title} -> {self.device.user.email} ({self.status})"
