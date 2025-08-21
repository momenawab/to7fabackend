from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import uuid

class SupportCategory(models.Model):
    """Categories for support tickets to help organize issues"""
    name = models.CharField(max_length=100, verbose_name=_('Category Name'))
    description = models.TextField(blank=True, null=True, verbose_name=_('Description'))
    icon = models.CharField(max_length=50, blank=True, null=True, help_text="Icon name (e.g., 'bug_report', 'payment', 'account')")
    color = models.CharField(max_length=7, default='#2196F3', help_text="Hex color code (e.g., #FF5722)")
    is_active = models.BooleanField(default=True, verbose_name=_('Is Active'))
    order = models.PositiveIntegerField(default=0, verbose_name=_('Display Order'))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Support Category')
        verbose_name_plural = _('Support Categories')
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    @property
    def ticket_count(self):
        """Get count of tickets in this category"""
        return self.tickets.count()
    
    @property
    def open_ticket_count(self):
        """Get count of open tickets in this category"""
        return self.tickets.filter(status__in=['open', 'in_progress']).count()


class SupportTicket(models.Model):
    """Customer support tickets"""
    
    STATUS_CHOICES = [
        ('open', _('Open')),
        ('in_progress', _('In Progress')),
        ('waiting_customer', _('Waiting for Customer')),
        ('resolved', _('Resolved')),
        ('closed', _('Closed')),
    ]
    
    
    # Ticket identification
    ticket_id = models.CharField(max_length=10, unique=True, editable=False)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # User information
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='support_tickets',
        verbose_name=_('User')
    )
    
    # Ticket details
    category = models.ForeignKey(
        SupportCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets',
        verbose_name=_('Category')
    )
    subject = models.CharField(max_length=200, verbose_name=_('Subject'))
    description = models.TextField(verbose_name=_('Description'))
    
    # Related order (for order-specific issues)
    order_id = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        verbose_name=_('Related Order ID'),
        help_text=_('Order ID if this ticket is related to a specific order')
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open',
        verbose_name=_('Status')
    )
    
    # Assignment
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tickets',
        verbose_name=_('Assigned To'),
        limit_choices_to={'is_staff': True}
    )
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    # Customer satisfaction
    rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        choices=[(i, str(i)) for i in range(1, 6)],
        verbose_name=_('Customer Rating (1-5)')
    )
    feedback = models.TextField(blank=True, null=True, verbose_name=_('Customer Feedback'))
    
    class Meta:
        verbose_name = _('Support Ticket')
        verbose_name_plural = _('Support Tickets')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['order_id']),
        ]
    
    def __str__(self):
        return f"#{self.ticket_id} - {self.subject}"
    
    def save(self, *args, **kwargs):
        if not self.ticket_id:
            # Generate unique ticket ID
            import random
            import string
            while True:
                ticket_id = ''.join(random.choices(string.digits, k=6))
                if not SupportTicket.objects.filter(ticket_id=ticket_id).exists():
                    self.ticket_id = ticket_id
                    break
        super().save(*args, **kwargs)
    
    @property
    def status_color(self):
        """Get status color for UI"""
        colors = {
            'open': '#FF5722',  # Red
            'in_progress': '#FF9800',  # Orange
            'waiting_customer': '#2196F3',  # Blue
            'resolved': '#4CAF50',  # Green
            'closed': '#9E9E9E',  # Grey
        }
        return colors.get(self.status, '#9E9E9E')
    
    
    @property
    def is_overdue(self):
        """Check if ticket is overdue (open for more than 48 hours)"""
        if self.status in ['resolved', 'closed']:
            return False
        from django.utils import timezone
        import datetime
        return (timezone.now() - self.created_at) > datetime.timedelta(hours=48)


class SupportMessage(models.Model):
    """Messages within a support ticket conversation"""
    
    ticket = models.ForeignKey(
        SupportTicket,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_('Ticket')
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_('Sender')
    )
    message = models.TextField(verbose_name=_('Message'))
    
    # Message type
    MESSAGE_TYPES = [
        ('user', _('User Message')),
        ('admin', _('Admin Response')),
        ('system', _('System Message')),
    ]
    message_type = models.CharField(
        max_length=10,
        choices=MESSAGE_TYPES,
        default='user',
        verbose_name=_('Message Type')
    )
    
    # Metadata
    is_internal = models.BooleanField(
        default=False,
        verbose_name=_('Internal Note'),
        help_text=_('Internal notes are only visible to staff')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Support Message')
        verbose_name_plural = _('Support Messages')
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.ticket.ticket_id} - {self.sender.email} - {self.created_at}"


class SupportAttachment(models.Model):
    """File attachments for support tickets"""
    
    def upload_path(instance, filename):
        """Generate upload path for attachments"""
        return f'support/tickets/{instance.ticket.ticket_id}/{filename}'
    
    ticket = models.ForeignKey(
        SupportTicket,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name=_('Ticket')
    )
    message = models.ForeignKey(
        SupportMessage,
        on_delete=models.CASCADE,
        related_name='attachments',
        null=True,
        blank=True,
        verbose_name=_('Message')
    )
    
    file = models.FileField(
        upload_to=upload_path,
        verbose_name=_('File')
    )
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(help_text=_('File size in bytes'))
    content_type = models.CharField(max_length=100)
    
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_('Uploaded By')
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Support Attachment')
        verbose_name_plural = _('Support Attachments')
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.ticket.ticket_id} - {self.original_filename}"
    
    @property
    def is_image(self):
        """Check if attachment is an image"""
        return self.content_type.startswith('image/')
    
    @property
    def file_size_formatted(self):
        """Get formatted file size"""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} MB"