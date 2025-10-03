from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.urls import reverse
import uuid


class ContactRequest(models.Model):
    """Simple contact requests from users for WhatsApp support"""
    
    STATUS_CHOICES = [
        ('new', _('New')),
        ('contacted', _('Contacted via WhatsApp')),
        ('resolved', _('Resolved')),
        ('closed', _('Closed')),
    ]
    
    PRIORITY_CHOICES = [
        ('low', _('Low')),
        ('normal', _('Normal')),
        ('high', _('High')),
        ('urgent', _('Urgent')),
    ]
    
    # Basic identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contact_number = models.CharField(max_length=8, unique=True, editable=False)
    
    # User information (can be anonymous or registered)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='contact_requests',
        verbose_name=_('User'),
        null=True,
        blank=True
    )
    
    # Contact details from form
    name = models.CharField(max_length=100, verbose_name=_('Full Name'))
    phone = models.CharField(max_length=20, verbose_name=_('WhatsApp Phone Number'))
    subject = models.CharField(max_length=200, verbose_name=_('Subject'))
    message = models.TextField(verbose_name=_('Message'))
    
    # Status and priority
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name=_('Status')
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='normal',
        verbose_name=_('Priority')
    )
    
    # Assignment
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_contacts',
        verbose_name=_('Assigned To'),
        limit_choices_to={'is_staff': True}
    )
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    contacted_at = models.DateTimeField(null=True, blank=True, verbose_name=_('First Contact Time'))
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    # Admin notes (internal)
    admin_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Admin Notes'),
        help_text=_('Internal notes for admin use only')
    )
    
    # WhatsApp conversation link or reference
    whatsapp_conversation_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('WhatsApp Conversation ID'),
        help_text=_('Reference to WhatsApp conversation')
    )
    
    class Meta:
        verbose_name = _('Contact Request')
        verbose_name_plural = _('Contact Requests')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['phone']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['priority', 'status']),
        ]
    
    def __str__(self):
        return f"#{self.contact_number} - {self.name} - {self.subject}"
    
    def save(self, *args, **kwargs):
        if not self.contact_number:
            # Generate unique contact number (8 digits)
            import random
            while True:
                contact_number = str(random.randint(10000000, 99999999))
                if not ContactRequest.objects.filter(contact_number=contact_number).exists():
                    self.contact_number = contact_number
                    break
        super().save(*args, **kwargs)
    
    @property
    def status_color(self):
        """Get status color for UI"""
        colors = {
            'new': '#FF5722',  # Red - needs attention
            'contacted': '#FF9800',  # Orange - in progress
            'resolved': '#4CAF50',  # Green - resolved
            'closed': '#9E9E9E',  # Grey - closed
        }
        return colors.get(self.status, '#9E9E9E')
    
    @property
    def priority_color(self):
        """Get priority color for UI"""
        colors = {
            'low': '#9E9E9E',  # Grey
            'normal': '#2196F3',  # Blue
            'high': '#FF9800',  # Orange
            'urgent': '#FF5722',  # Red
        }
        return colors.get(self.priority, '#2196F3')
    
    @property
    def whatsapp_url(self):
        """Generate WhatsApp URL for direct contact"""
        # Remove all non-digit characters from phone
        clean_phone = ''.join(filter(str.isdigit, self.phone))
        
        # Add country code if not present (assuming Egypt +20)
        if not clean_phone.startswith('20'):
            if clean_phone.startswith('0'):
                clean_phone = '20' + clean_phone[1:]
            else:
                clean_phone = '20' + clean_phone
        
        # Create message template
        message = f"مرحباً {self.name}، هذا رد على استفسارك: {self.subject}"
        
        return f"https://wa.me/{clean_phone}?text={message}"
    
    @property
    def is_overdue(self):
        """Check if contact request is overdue (new for more than 24 hours)"""
        if self.status != 'new':
            return False
        from django.utils import timezone
        import datetime
        return (timezone.now() - self.created_at) > datetime.timedelta(hours=24)
    
    @property
    def response_time(self):
        """Calculate response time if contacted"""
        if self.contacted_at:
            delta = self.contacted_at - self.created_at
            hours = delta.total_seconds() / 3600
            if hours < 1:
                minutes = delta.total_seconds() / 60
                return f"{minutes:.0f} minutes"
            elif hours < 24:
                return f"{hours:.1f} hours"
            else:
                days = hours / 24
                return f"{days:.1f} days"
        return None


class ContactNote(models.Model):
    """Admin notes and updates for contact requests"""
    
    contact = models.ForeignKey(
        ContactRequest,
        on_delete=models.CASCADE,
        related_name='notes',
        verbose_name=_('Contact Request')
    )
    
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=_('Author')
    )
    
    note = models.TextField(verbose_name=_('Note'))
    
    # Note type
    NOTE_TYPES = [
        ('contact', _('Contact Made')),
        ('update', _('Status Update')),
        ('resolution', _('Resolution')),
        ('internal', _('Internal Note')),
    ]
    note_type = models.CharField(
        max_length=15,
        choices=NOTE_TYPES,
        default='internal',
        verbose_name=_('Note Type')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Contact Note')
        verbose_name_plural = _('Contact Notes')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.contact.contact_number} - {self.get_note_type_display()} - {self.author.get_full_name()}"


class ContactStats(models.Model):
    """Daily statistics for contact requests"""
    
    date = models.DateField(unique=True)
    
    # Counts
    total_requests = models.PositiveIntegerField(default=0)
    new_requests = models.PositiveIntegerField(default=0)
    contacted_requests = models.PositiveIntegerField(default=0)
    resolved_requests = models.PositiveIntegerField(default=0)
    closed_requests = models.PositiveIntegerField(default=0)
    
    # Response times
    avg_response_time_minutes = models.FloatField(null=True, blank=True)
    avg_resolution_time_hours = models.FloatField(null=True, blank=True)
    
    # Overdue
    overdue_requests = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Contact Statistics')
        verbose_name_plural = _('Contact Statistics')
        ordering = ['-date']
    
    def __str__(self):
        return f"Stats for {self.date} - {self.total_requests} requests"
    
    @classmethod
    def update_daily_stats(cls, date=None):
        """Update statistics for a specific date"""
        from django.utils import timezone
        
        if date is None:
            date = timezone.now().date()
        
        # Get all requests for this date
        requests = ContactRequest.objects.filter(created_at__date=date)
        
        # Calculate stats
        stats, created = cls.objects.get_or_create(date=date)
        
        stats.total_requests = requests.count()
        stats.new_requests = requests.filter(status='new').count()
        stats.contacted_requests = requests.filter(status='contacted').count()
        stats.resolved_requests = requests.filter(status='resolved').count()
        stats.closed_requests = requests.filter(status='closed').count()
        
        # Calculate response times
        contacted_requests = requests.filter(contacted_at__isnull=False)
        if contacted_requests.exists():
            response_times = []
            for req in contacted_requests:
                if req.response_time:
                    delta = req.contacted_at - req.created_at
                    response_times.append(delta.total_seconds() / 60)  # in minutes
            
            if response_times:
                stats.avg_response_time_minutes = sum(response_times) / len(response_times)
        
        # Calculate overdue
        stats.overdue_requests = sum(1 for req in requests if req.is_overdue)
        
        stats.save()
        return stats