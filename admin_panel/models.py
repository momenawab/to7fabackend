from django.db import models
from django.utils.translation import gettext_lazy as _
from custom_auth.models import User

class AdminActivity(models.Model):
    """Model to track admin activities in the admin panel"""
    ACTION_CHOICES = (
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('other', 'Other'),
    )
    
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_activities')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Admin Activity'
        verbose_name_plural = 'Admin Activities'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.admin.email} - {self.action} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

class AdminNotification(models.Model):
    """Model for admin notifications"""
    TYPE_CHOICES = (
        ('new_application', 'New Seller Application'),
        ('system', 'System Notification'),
        ('report', 'User Report'),
        ('other', 'Other'),
    )
    
    title = models.CharField(max_length=100)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    is_read = models.BooleanField(default=False)
    link = models.CharField(max_length=255, blank=True, null=True)  # Link to relevant page
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.notification_type}: {self.title}"
