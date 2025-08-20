from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import SupportCategory, SupportTicket, SupportMessage, SupportAttachment


@admin.register(SupportCategory)
class SupportCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'ticket_count', 'open_ticket_count', 'is_active', 'order')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('order', 'name')
    
    def ticket_count(self, obj):
        return obj.ticket_count
    ticket_count.short_description = 'Total Tickets'
    
    def open_ticket_count(self, obj):
        count = obj.open_ticket_count
        if count > 0:
            return format_html('<span style="color: red; font-weight: bold;">{}</span>', count)
        return count
    open_ticket_count.short_description = 'Open Tickets'


class SupportMessageInline(admin.TabularInline):
    model = SupportMessage
    extra = 0
    readonly_fields = ('sender', 'message_type', 'created_at')
    fields = ('sender', 'message', 'message_type', 'is_internal', 'created_at')
    
    def has_delete_permission(self, request, obj=None):
        return False


class SupportAttachmentInline(admin.TabularInline):
    model = SupportAttachment
    extra = 0
    readonly_fields = ('original_filename', 'file_size_formatted', 'uploaded_by', 'uploaded_at')
    fields = ('file', 'original_filename', 'file_size_formatted', 'uploaded_by', 'uploaded_at')
    
    def file_size_formatted(self, obj):
        return obj.file_size_formatted if obj.id else ''
    file_size_formatted.short_description = 'File Size'


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = (
        'ticket_id', 'subject', 'user', 'category', 'status_badge', 
        'priority_badge', 'assigned_to', 'created_at', 'is_overdue_badge'
    )
    list_filter = ('status', 'priority', 'category', 'assigned_to', 'created_at')
    search_fields = ('ticket_id', 'subject', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('ticket_id', 'uuid', 'created_at', 'updated_at', 'ip_address', 'user_agent')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Ticket Information', {
            'fields': ('ticket_id', 'uuid', 'subject', 'description')
        }),
        ('User & Assignment', {
            'fields': ('user', 'category', 'assigned_to')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority', 'resolved_at', 'closed_at')
        }),
        ('Customer Feedback', {
            'fields': ('rating', 'feedback'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [SupportMessageInline, SupportAttachmentInline]
    
    def status_badge(self, obj):
        color = obj.status_color
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def priority_badge(self, obj):
        color = obj.priority_color
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px;">{}</span>',
            color, obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'
    
    def is_overdue_badge(self, obj):
        if obj.is_overdue:
            return format_html('<span style="color: red; font-weight: bold;">⚠️ Overdue</span>')
        return '✅'
    is_overdue_badge.short_description = 'Status'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'category', 'assigned_to')


@admin.register(SupportMessage)
class SupportMessageAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'sender', 'message_preview', 'message_type', 'is_internal', 'created_at')
    list_filter = ('message_type', 'is_internal', 'created_at')
    search_fields = ('ticket__ticket_id', 'sender__email', 'message')
    readonly_fields = ('created_at', 'updated_at')
    
    def message_preview(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message Preview'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('ticket', 'sender')


@admin.register(SupportAttachment)
class SupportAttachmentAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'original_filename', 'file_size_formatted', 'content_type', 'uploaded_by', 'uploaded_at')
    list_filter = ('content_type', 'uploaded_at')
    search_fields = ('ticket__ticket_id', 'original_filename', 'uploaded_by__email')
    readonly_fields = ('file_size_formatted', 'uploaded_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('ticket', 'uploaded_by')