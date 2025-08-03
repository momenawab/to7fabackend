from django.db import models
from django.utils.translation import gettext_lazy as _
from custom_auth.models import User

class SellerApplication(models.Model):
    """Model to track seller applications"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    USER_TYPE_CHOICES = (
        ('artist', 'Artist'),
        ('store', 'Store'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seller_applications')
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    name = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='seller_applications/', blank=True, null=True)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField()
    address = models.TextField()
    shipping_company = models.CharField(max_length=100)
    shipping_costs = models.JSONField(default=dict)  # Store costs per governorate
    details = models.TextField()
    categories = models.JSONField(default=list)  # List of category IDs
    
    # Artist-specific fields
    specialty = models.CharField(max_length=100, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    
    # Store-specific fields
    store_name = models.CharField(max_length=100, blank=True, null=True)
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    has_physical_store = models.BooleanField(default=False)
    physical_address = models.TextField(blank=True, null=True)
    
    # Application status
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    processed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        related_name='processed_applications',
        blank=True, 
        null=True
    )
    
    def __str__(self):
        return f"{self.user_type.capitalize()} Application: {self.name} ({self.status})"

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
