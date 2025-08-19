from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import AdminActivity, AdminNotification
from custom_auth.models import SellerApplication
import json

@admin.register(SellerApplication)
class SellerApplicationAdmin(admin.ModelAdmin):
    list_display = [
        'business_name', 'seller_type', 'user_email', 'phone_number', 'status', 
        'created_at', 'reviewed_at', 'reviewed_by'
    ]
    list_filter = [
        'status', 'seller_type', 'created_at', 'reviewed_at', 
        'has_physical_store'
    ]
    search_fields = ['business_name', 'user__email', 'phone_number', 'description']
    readonly_fields = [
        'user', 'created_at', 'reviewed_at', 'view_social_media'
    ]
    
    fieldsets = (
        ('Application Status & Admin Control', {
            'fields': ('status', 'admin_notes', 'rejection_reason', 'reviewed_at', 'reviewed_by'),
            'classes': ('wide',)
        }),
        ('User Information', {
            'fields': ('user', 'seller_type', 'business_name', 'phone_number'),
            'classes': ('wide',)
        }),
        ('Business Details', {
            'fields': ('description', 'specialty', 'portfolio_link', 'tax_id', 'has_physical_store', 'physical_address'),
            'classes': ('wide',)
        }),
        ('Social Media Links', {
            'fields': ('view_social_media',),
            'classes': ('wide',)
        }),
        ('Documents', {
            'fields': ('business_license', 'id_document'),
            'classes': ('wide',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    actions = ['approve_applications', 'reject_applications']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'
    
    def view_social_media(self, obj):
        if not obj.social_media:
            return 'No social media provided'
        
        html_parts = []
        for platform, url in obj.social_media.items():
            if url:
                html_parts.append(f'<strong>{platform.capitalize()}:</strong> <a href="{url}" target="_blank">{url}</a>')
            else:
                html_parts.append(f'<strong>{platform.capitalize()}:</strong> Not provided')
        
        return format_html('<br>'.join(html_parts)) if html_parts else 'No social media provided'
    view_social_media.short_description = 'Social Media Links'
    
    def approve_applications(self, request, queryset):
        updated = 0
        for application in queryset.filter(status='pending'):
            application.status = 'approved'
            application.reviewed_at = timezone.now()
            application.reviewed_by = request.user
            application.save()
            
            # Log admin activity
            AdminActivity.objects.create(
                admin=request.user,
                action='approve',
                description=f'Approved seller application for {application.business_name}',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            updated += 1
            
        self.message_user(request, f'{updated} application(s) approved successfully.')
    approve_applications.short_description = 'Approve selected applications'
    
    def reject_applications(self, request, queryset):
        updated = 0
        for application in queryset.filter(status='pending'):
            application.status = 'rejected'
            application.reviewed_at = timezone.now()
            application.reviewed_by = request.user
            application.save()
            
            # Log admin activity
            AdminActivity.objects.create(
                admin=request.user,
                action='reject',
                description=f'Rejected seller application for {application.business_name}',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            updated += 1
            
        self.message_user(request, f'{updated} application(s) rejected.')
    reject_applications.short_description = 'Reject selected applications'

@admin.register(AdminActivity)
class AdminActivityAdmin(admin.ModelAdmin):
    list_display = ['admin', 'action', 'description', 'ip_address', 'timestamp']
    list_filter = ['action', 'timestamp']
    search_fields = ['admin__email', 'description']
    readonly_fields = ['admin', 'action', 'description', 'ip_address', 'timestamp']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

@admin.register(AdminNotification)
class AdminNotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title', 'message']
    readonly_fields = ['created_at']