from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Q
from django.utils import timezone
from .contact_models import ContactRequest, ContactNote, ContactStats


class ContactNoteInline(admin.TabularInline):
    model = ContactNote
    extra = 0
    readonly_fields = ('author', 'created_at')
    fields = ('note', 'note_type', 'author', 'created_at')
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    list_display = (
        'contact_number', 'name', 'subject_preview', 'phone', 'status_badge', 
        'priority_badge', 'assigned_to', 'created_at', 'overdue_badge', 'whatsapp_link'
    )
    list_filter = (
        'status', 'priority', 'assigned_to', 'created_at',
        ('contacted_at', admin.DateFieldListFilter),
    )
    search_fields = ('contact_number', 'name', 'phone', 'subject', 'message')
    readonly_fields = ('contact_number', 'id', 'created_at', 'whatsapp_url_display', 'response_time_display')
    ordering = ('-created_at',)
    
    actions = [
        'mark_as_contacted', 'mark_as_resolved', 'mark_as_closed', 
        'assign_to_me', 'set_high_priority', 'set_normal_priority'
    ]
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('contact_number', 'id', 'name', 'phone', 'whatsapp_url_display')
        }),
        ('Request Details', {
            'fields': ('subject', 'message', 'user')
        }),
        ('Status & Assignment', {
            'fields': ('status', 'priority', 'assigned_to', 'admin_notes')
        }),
        ('Timeline', {
            'fields': ('created_at', 'contacted_at', 'resolved_at', 'closed_at', 'response_time_display'),
            'classes': ('collapse',)
        }),
        ('WhatsApp Integration', {
            'fields': ('whatsapp_conversation_id',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ContactNoteInline]
    
    def subject_preview(self, obj):
        """Show truncated subject"""
        if len(obj.subject) > 30:
            return obj.subject[:30] + '...'
        return obj.subject
    subject_preview.short_description = 'Subject'
    
    def status_badge(self, obj):
        """Show colored status badge"""
        color = obj.status_color
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def priority_badge(self, obj):
        """Show colored priority badge"""
        color = obj.priority_color
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">{}</span>',
            color, obj.get_priority_display().upper()
        )
    priority_badge.short_description = 'Priority'
    
    def overdue_badge(self, obj):
        """Show overdue warning"""
        if obj.is_overdue:
            return format_html('<span style="color: red; font-weight: bold;">⚠️ OVERDUE</span>')
        elif obj.status == 'new':
            # Calculate time remaining
            from django.utils import timezone
            import datetime
            time_left = datetime.timedelta(hours=24) - (timezone.now() - obj.created_at)
            hours_left = time_left.total_seconds() / 3600
            if hours_left > 0:
                return format_html('<span style="color: orange;">{:.1f}h left</span>', hours_left)
        return '✅'
    overdue_badge.short_description = 'Status'
    
    def whatsapp_link(self, obj):
        """Show WhatsApp contact link"""
        url = obj.whatsapp_url
        return format_html(
            '<a href="{}" target="_blank" style="background: #25D366; color: white; padding: 4px 8px; border-radius: 4px; text-decoration: none; font-size: 11px;">📱 WhatsApp</a>',
            url
        )
    whatsapp_link.short_description = 'Contact'
    
    def whatsapp_url_display(self, obj):
        """Show WhatsApp URL in detail view"""
        url = obj.whatsapp_url
        return format_html(
            '<a href="{}" target="_blank" style="color: #25D366; font-weight: bold;">Open WhatsApp Conversation</a><br/><small>{}</small>',
            url, url
        )
    whatsapp_url_display.short_description = 'WhatsApp Link'
    
    def response_time_display(self, obj):
        """Show response time if available"""
        time = obj.response_time
        if time:
            return format_html('<span style="color: green; font-weight: bold;">{}</span>', time)
        return '-'
    response_time_display.short_description = 'Response Time'
    
    # Custom actions
    def mark_as_contacted(self, request, queryset):
        """Mark selected requests as contacted"""
        from django.utils import timezone
        updated = 0
        for contact in queryset:
            if contact.status == 'new':
                contact.status = 'contacted'
                if not contact.contacted_at:
                    contact.contacted_at = timezone.now()
                contact.save()
                
                # Add note
                ContactNote.objects.create(
                    contact=contact,
                    author=request.user,
                    note=f"Marked as contacted via WhatsApp by {request.user.get_full_name()}",
                    note_type='contact'
                )
                updated += 1
        
        self.message_user(request, f'{updated} contact(s) marked as contacted.')
    mark_as_contacted.short_description = "Mark as contacted via WhatsApp"
    
    def mark_as_resolved(self, request, queryset):
        """Mark selected requests as resolved"""
        from django.utils import timezone
        updated = 0
        for contact in queryset:
            if contact.status in ['new', 'contacted']:
                contact.status = 'resolved'
                contact.resolved_at = timezone.now()
                contact.save()
                
                # Add note
                ContactNote.objects.create(
                    contact=contact,
                    author=request.user,
                    note=f"Marked as resolved by {request.user.get_full_name()}",
                    note_type='resolution'
                )
                updated += 1
        
        self.message_user(request, f'{updated} contact(s) marked as resolved.')
    mark_as_resolved.short_description = "Mark as resolved"
    
    def mark_as_closed(self, request, queryset):
        """Mark selected requests as closed"""
        from django.utils import timezone
        updated = 0
        for contact in queryset:
            if contact.status != 'closed':
                contact.status = 'closed'
                contact.closed_at = timezone.now()
                contact.save()
                
                # Add note
                ContactNote.objects.create(
                    contact=contact,
                    author=request.user,
                    note=f"Marked as closed by {request.user.get_full_name()}",
                    note_type='update'
                )
                updated += 1
        
        self.message_user(request, f'{updated} contact(s) marked as closed.')
    mark_as_closed.short_description = "Mark as closed"
    
    def assign_to_me(self, request, queryset):
        """Assign selected requests to current user"""
        updated = queryset.update(assigned_to=request.user)
        self.message_user(request, f'{updated} contact(s) assigned to you.')
    assign_to_me.short_description = "Assign to me"
    
    def set_high_priority(self, request, queryset):
        """Set high priority"""
        updated = queryset.update(priority='high')
        self.message_user(request, f'{updated} contact(s) set to high priority.')
    set_high_priority.short_description = "Set high priority"
    
    def set_normal_priority(self, request, queryset):
        """Set normal priority"""
        updated = queryset.update(priority='normal')
        self.message_user(request, f'{updated} contact(s) set to normal priority.')
    set_normal_priority.short_description = "Set normal priority"
    
    def get_queryset(self, request):
        """Optimize queries"""
        return super().get_queryset(request).select_related('user', 'assigned_to')
    
    def changelist_view(self, request, extra_context=None):
        """Add dashboard stats to changelist"""
        # Get today's stats
        today = timezone.now().date()
        stats = {}
        
        try:
            today_stats = ContactStats.objects.get(date=today)
            stats['today'] = today_stats
        except ContactStats.DoesNotExist:
            # Create today's stats
            stats['today'] = ContactStats.update_daily_stats(today)
        
        # Get counts for different statuses
        all_requests = ContactRequest.objects.all()
        stats['total'] = all_requests.count()
        stats['new'] = all_requests.filter(status='new').count()
        stats['contacted'] = all_requests.filter(status='contacted').count()
        stats['overdue'] = sum(1 for req in all_requests.filter(status='new') if req.is_overdue)
        
        # Get user's assigned
        stats['my_assigned'] = all_requests.filter(assigned_to=request.user).exclude(status='closed').count()
        
        extra_context = extra_context or {}
        extra_context['contact_stats'] = stats
        
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(ContactNote)
class ContactNoteAdmin(admin.ModelAdmin):
    list_display = ('contact', 'note_preview', 'note_type', 'author', 'created_at')
    list_filter = ('note_type', 'created_at', 'author')
    search_fields = ('contact__contact_number', 'contact__name', 'note', 'author__username')
    readonly_fields = ('created_at',)
    
    def note_preview(self, obj):
        """Show truncated note"""
        if len(obj.note) > 50:
            return obj.note[:50] + '...'
        return obj.note
    note_preview.short_description = 'Note'
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(ContactStats)
class ContactStatsAdmin(admin.ModelAdmin):
    list_display = (
        'date', 'total_requests', 'new_requests', 'contacted_requests', 
        'resolved_requests', 'overdue_requests', 'avg_response_time_display'
    )
    list_filter = ('date',)
    readonly_fields = (
        'total_requests', 'new_requests', 'contacted_requests', 'resolved_requests', 
        'closed_requests', 'avg_response_time_minutes', 'avg_resolution_time_hours', 
        'overdue_requests', 'created_at', 'updated_at'
    )
    ordering = ('-date',)
    
    actions = ['update_stats']
    
    def avg_response_time_display(self, obj):
        """Show formatted average response time"""
        if obj.avg_response_time_minutes:
            if obj.avg_response_time_minutes < 60:
                return f"{obj.avg_response_time_minutes:.1f} min"
            else:
                return f"{obj.avg_response_time_minutes/60:.1f} hours"
        return '-'
    avg_response_time_display.short_description = 'Avg Response Time'
    
    def update_stats(self, request, queryset):
        """Update statistics for selected dates"""
        updated = 0
        for stats in queryset:
            ContactStats.update_daily_stats(stats.date)
            updated += 1
        
        self.message_user(request, f'Updated statistics for {updated} date(s).')
    update_stats.short_description = "Update statistics"


# Custom admin site configuration for better organization
class ContactAdminSite(admin.AdminSite):
    site_header = 'TO7FA Contact Management'
    site_title = 'TO7FA Contacts'
    index_title = 'Customer Contact Dashboard'
    
    def index(self, request, extra_context=None):
        """Custom dashboard with contact statistics"""
        extra_context = extra_context or {}
        
        # Get quick stats
        today = timezone.now().date()
        
        # Today's stats
        today_requests = ContactRequest.objects.filter(created_at__date=today)
        extra_context['today_new'] = today_requests.count()
        extra_context['today_contacted'] = today_requests.filter(status='contacted').count()
        
        # Overall stats
        all_requests = ContactRequest.objects.all()
        extra_context['total_requests'] = all_requests.count()
        extra_context['pending_requests'] = all_requests.filter(status__in=['new', 'contacted']).count()
        extra_context['overdue_requests'] = sum(1 for req in all_requests.filter(status='new') if req.is_overdue)
        
        # My assigned
        extra_context['my_requests'] = all_requests.filter(assigned_to=request.user).exclude(status='closed').count()
        
        return super().index(request, extra_context)