from django.db import models
from django.conf import settings

class Notification(models.Model):
    TYPE_CHOICES = (
        ('order', 'Order'),
        ('payment', 'Payment'),
        ('system', 'System'),
        ('promotion', 'Promotion'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    is_read = models.BooleanField(default=False)
    related_object_id = models.PositiveIntegerField(blank=True, null=True)
    related_object_type = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
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
        self.is_read = True
        self.save()
        return True
