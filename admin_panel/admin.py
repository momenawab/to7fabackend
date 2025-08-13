from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import SellerApplication, AdminActivity, AdminNotification
import json

@admin.register(SellerApplication)
class SellerApplicationAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'user_type', 'user_email', 'phone_number', 'status', 
        'shipping_summary', 'submitted_at', 'processed_at', 'processed_by', 'view_details'
    ]
    list_filter = [
        'status', 'user_type', 'submitted_at', 'processed_at', 
        'has_physical_store', 'terms_accepted'
    ]
    search_fields = ['name', 'email', 'phone_number', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = [
        'user', 'submitted_at', 'terms_accepted_at', 'view_categories', 'view_raw_categories',
        'view_social_media', 'view_shipping_costs', 'shipping_summary', 'id_front_preview', 'id_back_preview'
    ]
    
    fieldsets = (
        ('Application Status & Admin Control', {
            'fields': ('status', 'admin_notes', 'processed_at', 'processed_by'),
            'classes': ('wide',)
        }),
        ('User Information', {
            'fields': ('user', 'user_type', 'name', 'email', 'phone_number'),
            'classes': ('wide',)
        }),
        ('Personal & Business Details', {
            'fields': ('address', 'bio', 'specialty', 'store_name', 'tax_id', 'has_physical_store', 'physical_address'),
            'classes': ('wide',)
        }),
        ('Categories & Subcategories', {
            'fields': ('view_categories', 'view_raw_categories'),
            'classes': ('wide',)
        }),
        ('Social Media Links', {
            'fields': ('view_social_media',),
            'classes': ('wide',)
        }),
        ('Shipping Costs & Coverage', {
            'fields': ('view_shipping_costs', 'shipping_summary'),
            'classes': ('wide',)
        }),
        ('ID Documents', {
            'fields': ('id_front_preview', 'id_back_preview'),
            'classes': ('wide',)
        }),
        ('Terms & Timestamps', {
            'fields': ('terms_accepted', 'terms_accepted_at', 'submitted_at'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('details',),
            'classes': ('collapse',)
        })
    )
    
    actions = ['approve_applications', 'reject_applications', 'reject_permanently']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'
    
    def view_details(self, obj):
        return format_html('<a href="{}">View Full Details</a>', 
                          reverse('admin:admin_panel_sellerapplication_change', args=[obj.id]))
    view_details.short_description = 'Details'
    
    def view_categories(self, obj):
        if not obj.categories:
            return 'No categories selected'
        
        from products.models import Category
        try:
            category_info = []
            
            # Main categories
            main_categories = []
            for cat_id in obj.categories:
                try:
                    category = Category.objects.get(id=cat_id)
                    main_categories.append(f'<strong>{category.name}</strong> (ID: {cat_id})')
                except Category.DoesNotExist:
                    main_categories.append(f'<strong>Unknown Category</strong> (ID: {cat_id})')
            
            category_info.append('<span style="color: blue;">Main Categories:</span> ' + ', '.join(main_categories))
            
            # Try to get subcategories from details
            if obj.details and 'subcategories:' in obj.details.lower():
                lines = obj.details.split('\n')
                for line in lines:
                    if 'subcategories:' in line.lower():
                        try:
                            # Extract subcategories list from the details
                            import re
                            import json
                            match = re.search(r'subcategories:\s*(\[.*?\])', line)
                            if match:
                                subcat_ids = json.loads(match.group(1))
                                subcat_names = []
                                for subcat_id in subcat_ids:
                                    try:
                                        subcategory = Category.objects.get(id=subcat_id)
                                        subcat_names.append(f'{subcategory.name} (ID: {subcat_id})')
                                    except Category.DoesNotExist:
                                        subcat_names.append(f'Unknown Subcategory (ID: {subcat_id})')
                                
                                if subcat_names:
                                    category_info.append('<span style="color: green;">Subcategories:</span> ' + ', '.join(subcat_names))
                        except:
                            pass
            
            return format_html('<br>'.join(category_info))
        except Exception as e:
            return f'Error parsing categories: {str(e)}<br>Raw data: {str(obj.categories)}'
    view_categories.short_description = 'Selected Categories & Subcategories'
    
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
    
    def view_shipping_costs(self, obj):
        if not obj.shipping_costs:
            return 'No shipping costs defined'
        
        # Egyptian governorates mapping
        gov_names = {
            '1': 'القاهرة', '2': 'الجيزة', '3': 'الأقصر', '4': 'أسوان', '5': 'أسيوط',
            '6': 'البحيرة', '7': 'بني سويف', '8': 'البحر الأحمر', '9': 'الدقهلية', '10': 'دمياط',
            '11': 'الفيوم', '12': 'الغربية', '13': 'الإسماعيلية', '14': 'كفر الشيخ', '15': 'مطروح',
            '16': 'المنيا', '17': 'المنوفية', '18': 'الوادي الجديد', '19': 'شمال سيناء', '20': 'بورسعيد',
            '21': 'القليوبية', '22': 'قنا', '23': 'الشرقية', '24': 'سوهاج', '25': 'جنوب سيناء',
            '26': 'السويس', '27': 'الإسكندرية'
        }
        
        # Separate available and unavailable
        available = []
        unavailable = []
        
        for gov_id, cost in obj.shipping_costs.items():
            gov_name = gov_names.get(str(gov_id), f'Governorate {gov_id}')
            if float(cost) > 0:
                available.append(f'{gov_name}: <strong>{cost} EGP</strong>')
            else:
                unavailable.append(gov_name)
        
        html_parts = []
        
        # Summary
        total_count = len(obj.shipping_costs)
        available_count = len(available)
        html_parts.append(f'<div style="background: #f8f9fa; padding: 10px; border-radius: 5px; margin-bottom: 10px;">')
        html_parts.append(f'<strong>Coverage: {available_count}/{total_count} governorates</strong>')
        html_parts.append('</div>')
        
        # Available shipping
        if available:
            html_parts.append('<div style="margin-bottom: 15px;">')
            html_parts.append('<span style="color: green; font-weight: bold;">✓ Available Shipping:</span>')
            html_parts.append('<ul style="margin: 5px 0; padding-left: 20px;">')
            for item in available[:10]:  # Show first 10
                html_parts.append(f'<li style="color: green;">{item}</li>')
            if len(available) > 10:
                html_parts.append(f'<li style="color: #666;"><em>... and {len(available) - 10} more</em></li>')
            html_parts.append('</ul></div>')
        
        # Unavailable shipping (show first few)
        if unavailable:
            html_parts.append('<div>')
            html_parts.append('<span style="color: red; font-weight: bold;">✗ Not Available:</span>')
            if len(unavailable) <= 5:
                html_parts.append('<span style="color: red;"> ' + ', '.join(unavailable) + '</span>')
            else:
                html_parts.append('<span style="color: red;"> ' + ', '.join(unavailable[:5]) + f' and {len(unavailable) - 5} more</span>')
            html_parts.append('</div>')
        
        return format_html(''.join(html_parts))
    view_shipping_costs.short_description = 'Detailed Shipping Costs'
    
    def id_front_preview(self, obj):
        if obj.id_front:
            return format_html('<a href="{}" target="_blank"><img src="{}" style="max-height: 200px; max-width: 300px;"></a>', 
                              obj.id_front.url, obj.id_front.url)
        return 'No ID front image'
    id_front_preview.short_description = 'ID Front'
    
    def id_back_preview(self, obj):
        if obj.id_back:
            return format_html('<a href="{}" target="_blank"><img src="{}" style="max-height: 200px; max-width: 300px;"></a>', 
                              obj.id_back.url, obj.id_back.url)
        return 'No ID back image'
    id_back_preview.short_description = 'ID Back'
    
    def view_raw_categories(self, obj):
        """Show raw categories and subcategories data for debugging"""
        if not obj.categories:
            return 'No categories data'
        
        # Try to parse details to get subcategories if stored there
        subcategories_info = ""
        if obj.details and 'subcategories:' in obj.details:
            lines = obj.details.split('\n')
            for line in lines:
                if 'subcategories:' in line.lower():
                    subcategories_info = f"<br><strong>Subcategories from details:</strong> {line.split(':', 1)[1].strip()}"
        
        return format_html(f"<strong>Categories IDs:</strong> {obj.categories}{subcategories_info}")
    view_raw_categories.short_description = 'Raw Categories Data'
    
    def shipping_summary(self, obj):
        """Show a summary of shipping coverage"""
        if not obj.shipping_costs:
            return 'No shipping data'
        
        available_count = sum(1 for cost in obj.shipping_costs.values() if float(cost) > 0)
        total_count = len(obj.shipping_costs)
        
        if available_count == 0:
            color = 'red'
            status = 'No shipping available'
        elif available_count == total_count:
            color = 'green'
            status = 'Full coverage'
        else:
            color = 'orange'
            status = 'Partial coverage'
        
        return format_html(
            f'<span style="color: {color}; font-weight: bold;">'
            f'{status}: {available_count}/{total_count} governorates</span>'
        )
    shipping_summary.short_description = 'Shipping Coverage Summary'
    
    def approve_applications(self, request, queryset):
        updated = 0
        for application in queryset.filter(status='pending'):
            application.status = 'approved'
            application.processed_at = timezone.now()
            application.processed_by = request.user
            application.save()
            
            # Log admin activity
            AdminActivity.objects.create(
                admin=request.user,
                action='approve',
                description=f'Approved seller application for {application.name} ({application.email})',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            updated += 1
            
        self.message_user(request, f'{updated} application(s) approved successfully.')
    approve_applications.short_description = 'Approve selected applications'
    
    def reject_applications(self, request, queryset):
        updated = 0
        for application in queryset.filter(status='pending'):
            application.status = 'rejected'
            application.processed_at = timezone.now()
            application.processed_by = request.user
            application.save()
            
            # Log admin activity
            AdminActivity.objects.create(
                admin=request.user,
                action='reject',
                description=f'Rejected seller application for {application.name} ({application.email}) - can reapply',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            updated += 1
            
        self.message_user(request, f'{updated} application(s) rejected. Users can reapply with changes.')
    reject_applications.short_description = 'Reject selected applications (can reapply)'
    
    def reject_permanently(self, request, queryset):
        updated = 0
        for application in queryset.filter(status='pending'):
            application.status = 'rejected_permanently'
            application.processed_at = timezone.now()
            application.processed_by = request.user
            if not application.admin_notes:
                application.admin_notes = 'Application permanently rejected. User cannot reapply.'
            application.save()
            
            # Log admin activity
            AdminActivity.objects.create(
                admin=request.user,
                action='reject',
                description=f'Permanently rejected seller application for {application.name} ({application.email})',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            updated += 1
            
        self.message_user(request, f'{updated} application(s) permanently rejected.')
    reject_permanently.short_description = 'Permanently reject selected applications'

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
