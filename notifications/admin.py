from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Notification, BulkNotification, Device, PushNotificationLog

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'title', 'notification_type', 'priority', 
        'is_read', 'created_at', 'push_sent'
    )
    list_filter = (
        'notification_type', 'is_read', 'priority', 
        'push_sent', 'created_at'
    )
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'title', 'message')
    readonly_fields = (
        'created_at', 'read_at', 'push_sent_at', 
        'related_object_id', 'related_object_type'
    )
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'title', 'message', 'notification_type', 'priority')
        }),
        ('Content & Actions', {
            'fields': ('action_url', 'image_url'),
            'classes': ('collapse',)
        }),
        ('Related Object', {
            'fields': ('content_type', 'object_id'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_read', 'read_at', 'send_push', 'push_sent', 'push_sent_at'),
            'classes': ('collapse',)
        }),
        ('Legacy Fields', {
            'fields': ('related_object_id', 'related_object_type'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
        })
    )
    
    actions = ['mark_as_read', 'mark_as_unread', 'send_push_notification']
    
    def mark_as_read(self, request, queryset):
        count = queryset.filter(is_read=False).count()
        queryset.update(is_read=True, read_at=timezone.now())
        self.message_user(request, f"{count} notifications marked as read.")
    mark_as_read.short_description = "Mark selected notifications as read"
    
    def mark_as_unread(self, request, queryset):
        count = queryset.filter(is_read=True).count()
        queryset.update(is_read=False, read_at=None)
        self.message_user(request, f"{count} notifications marked as unread.")
    mark_as_unread.short_description = "Mark selected notifications as unread"
    
    def send_push_notification(self, request, queryset):
        from .push_utils import push_service
        
        sent_count = 0
        failed_count = 0
        
        for notification in queryset.filter(push_sent=False):
            if push_service.send_notification_push(notification):
                sent_count += 1
            else:
                failed_count += 1
        
        if sent_count > 0:
            self.message_user(request, f"Push notifications sent to {sent_count} users.")
        if failed_count > 0:
            self.message_user(request, f"Failed to send push notifications to {failed_count} users.", level='WARNING')
    
    send_push_notification.short_description = "Send push notifications now"
    
    def save_model(self, request, obj, form, change):
        # Call parent save first
        super().save_model(request, obj, form, change)
        
        # Automatically send push notification for new notifications
        if not change and obj.send_push:
            from .push_utils import push_service
            import time
            # Small delay to ensure the object is fully saved
            time.sleep(0.1)
            
            try:
                # Reset push_sent to False to ensure it gets sent
                obj.push_sent = False
                obj.push_sent_at = None
                obj.save()
                
                # Send the push notification
                if push_service.send_notification_push(obj):
                    self.message_user(request, f"✅ Push notification sent successfully to {obj.user.email}")
                else:
                    self.message_user(request, f"❌ Failed to send push notification to {obj.user.email}", level='WARNING')
            except Exception as e:
                self.message_user(request, f"❌ Error sending push notification: {str(e)}", level='ERROR')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'content_type')


@admin.register(BulkNotification)
class BulkNotificationAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'target_audience', 'notification_type', 'priority',
        'is_sent', 'recipient_count', 'created_at', 'send_action'
    )
    list_filter = (
        'target_audience', 'notification_type', 'priority', 
        'is_sent', 'created_at'
    )
    search_fields = ('title', 'message')
    readonly_fields = (
        'is_sent', 'sent_at', 'recipient_count', 
        'created_at', 'updated_at'
    )
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Content', {
            'fields': ('title', 'message', 'notification_type', 'priority')
        }),
        ('Targeting', {
            'fields': ('target_audience', 'specific_users'),
            'description': 'Choose who will receive this notification'
        }),
        ('Optional Settings', {
            'fields': ('action_url', 'image_url', 'schedule_for'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_sent', 'sent_at', 'recipient_count'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    filter_horizontal = ['specific_users']
    actions = ['send_bulk_notifications', 'duplicate_notification']
    
    def send_action(self, obj):
        if obj.is_sent:
            return format_html(
                '<span style="color: green;">✓ Sent to {} users</span>',
                obj.recipient_count
            )
        else:
            return format_html(
                '<a href="{}?action=send_bulk&ids={}" style="color: blue;">Send Now</a>',
                reverse('admin:notifications_bulknotification_changelist'),
                obj.id
            )
    send_action.short_description = 'Action'
    
    def send_bulk_notifications(self, request, queryset):
        from .push_utils import push_service
        
        sent_count = 0
        error_count = 0
        
        for bulk_notification in queryset.filter(is_sent=False):
            try:
                # Send notifications and push notifications
                result = push_service.send_bulk_notification_push(bulk_notification)
                if result.get('success'):
                    sent_count += 1
                else:
                    error_count += 1
            except Exception as e:
                error_count += 1
        
        if sent_count > 0:
            self.message_user(request, f"Successfully sent {sent_count} bulk notifications with push notifications.")
        if error_count > 0:
            self.message_user(request, f"Failed to send {error_count} bulk notifications.", level='ERROR')
    
    send_bulk_notifications.short_description = "Send selected bulk notifications with push"
    
    def duplicate_notification(self, request, queryset):
        for bulk_notification in queryset:
            bulk_notification.pk = None
            bulk_notification.is_sent = False
            bulk_notification.sent_at = None
            bulk_notification.recipient_count = 0
            bulk_notification.created_by = request.user
            bulk_notification.title = f"Copy of {bulk_notification.title}"
            bulk_notification.save()
        
        self.message_user(request, f"Created {queryset.count()} duplicate notifications.")
    duplicate_notification.short_description = "Duplicate selected notifications"
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'platform', 'device_model', 'app_version', 
        'is_active', 'notifications_enabled', 'last_used'
    )
    list_filter = (
        'platform', 'is_active', 'notifications_enabled', 
        'created_at', 'last_used'
    )
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'device_id')
    readonly_fields = ('device_token', 'created_at', 'updated_at', 'last_used')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Device Information', {
            'fields': ('user', 'platform', 'device_id', 'device_token')
        }),
        ('Device Details', {
            'fields': ('device_model', 'os_version', 'app_version'),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('is_active', 'notifications_enabled')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_used'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['enable_notifications', 'disable_notifications', 'deactivate_devices']
    
    def enable_notifications(self, request, queryset):
        count = queryset.update(notifications_enabled=True)
        self.message_user(request, f"Enabled notifications for {count} devices.")
    enable_notifications.short_description = "Enable notifications for selected devices"
    
    def disable_notifications(self, request, queryset):
        count = queryset.update(notifications_enabled=False)
        self.message_user(request, f"Disabled notifications for {count} devices.")
    disable_notifications.short_description = "Disable notifications for selected devices"
    
    def deactivate_devices(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {count} devices.")
    deactivate_devices.short_description = "Deactivate selected devices"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(PushNotificationLog)
class PushNotificationLogAdmin(admin.ModelAdmin):
    list_display = (
        'notification_title', 'user_email', 'device_platform', 
        'status', 'sent_at'
    )
    list_filter = ('status', 'device__platform', 'sent_at')
    search_fields = (
        'notification__title', 'notification__message',
        'device__user__email', 'device__user__first_name', 'device__user__last_name'
    )
    readonly_fields = (
        'notification', 'device', 'status', 'response_data', 
        'error_message', 'sent_at'
    )
    date_hierarchy = 'sent_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('notification', 'device', 'status')
        }),
        ('Response Details', {
            'fields': ('response_data', 'error_message'),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('sent_at',)
        })
    )
    
    def notification_title(self, obj):
        return obj.notification.title[:50]
    notification_title.short_description = 'Notification'
    
    def user_email(self, obj):
        return obj.device.user.email
    user_email.short_description = 'User'
    
    def device_platform(self, obj):
        return obj.device.platform.upper()
    device_platform.short_description = 'Platform'
    
    def has_add_permission(self, request):
        return False  # Don't allow manual creation
    
    def has_change_permission(self, request, obj=None):
        return False  # Don't allow editing
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('notification', 'device', 'device__user')
