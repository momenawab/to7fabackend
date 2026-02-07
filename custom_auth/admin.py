from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import User, Customer, Artist, Store, OTPVerification
from .address_models import UserAddress

class CustomerInline(admin.StackedInline):
    model = Customer
    can_delete = False
    verbose_name_plural = 'Customer Profile'
    fk_name = 'user'

class ArtistInline(admin.StackedInline):
    model = Artist
    can_delete = False
    verbose_name_plural = 'Artist Profile'
    fk_name = 'user'

class StoreInline(admin.StackedInline):
    model = Store
    can_delete = False
    verbose_name_plural = 'Store Profile'
    fk_name = 'user'

class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'user_type', 'is_staff', 'is_mobile_verified', 'is_locked', 'is_blocked')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'user_type', 'is_mobile_verified', 'is_locked', 'is_blocked')
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')
    ordering = ('email',)

    actions = ['unlock_otp_blocked_users']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'user_type', 'phone_number', 'address')}),
        (_('Mobile Verification'), {'fields': ('is_mobile_verified', 'mobile_verified_at', 'otp_failed_attempts', 'otp_blocked_at')}),
        (_('Lock (BAN)'), {'fields': ('is_locked', 'locked_at', 'locked_reason', 'locked_by')}),
        (_('Block (Business Restriction)'), {'fields': ('is_blocked', 'blocked_capabilities', 'blocked_reason')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    readonly_fields = ('mobile_verified_at', 'locked_at', 'locked_by', 'otp_blocked_at')

    def unlock_otp_blocked_users(self, request, queryset):
        """
        Admin action to unlock users who are blocked due to OTP failures.
        Resets otp_failed_attempts and otp_blocked_at fields.
        """
        updated = queryset.filter(otp_blocked_at__isnull=False).update(
            otp_failed_attempts=0,
            otp_blocked_at=None
        )
        if updated > 0:
            self.message_user(
                request,
                f'Successfully unlocked {updated} user(s) from OTP block.',
                messages.SUCCESS
            )
        else:
            self.message_user(
                request,
                'No OTP-blocked users were selected.',
                messages.WARNING
            )

    unlock_otp_blocked_users.short_description = 'Unlock selected users from OTP block'
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'user_type'),
        }),
    )
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        inline_instances = []
        if obj.user_type == 'customer':
            inline_instances.append(CustomerInline(self.model, self.admin_site))
        elif obj.user_type == 'artist':
            inline_instances.append(ArtistInline(self.model, self.admin_site))
        elif obj.user_type == 'store':
            inline_instances.append(StoreInline(self.model, self.admin_site))
        return inline_instances

class CustomerAdmin(admin.ModelAdmin):
    list_display = ('user', 'date_of_birth', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')

class ArtistAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialty', 'is_verified', 'created_at')
    list_filter = ('is_verified',)
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'specialty')

class StoreAdmin(admin.ModelAdmin):
    list_display = ('user', 'store_name', 'has_physical_store', 'is_verified', 'created_at')
    list_filter = ('is_verified', 'has_physical_store')
    search_fields = ('user__email', 'store_name', 'tax_id')

class UserAddressAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'recipient_name', 'city', 'region', 'is_default', 'created_at')
    list_filter = ('is_default', 'city', 'region')
    search_fields = ('user__email', 'name', 'recipient_name', 'street', 'city', 'region')
    readonly_fields = ('created_at', 'updated_at')

class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'mobile_number', 'created_at', 'expires_at', 'used', 'attempt_count')
    list_filter = ('used', 'created_at', 'expires_at')
    search_fields = ('user__email', 'mobile_number')
    readonly_fields = ('created_at', 'expires_at', 'used', 'attempt_count', 'otp_hash')
    ordering = ('-created_at',)

admin.site.register(User, UserAdmin)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Artist, ArtistAdmin)
admin.site.register(Store, StoreAdmin)
admin.site.register(UserAddress, UserAddressAdmin)
admin.site.register(OTPVerification, OTPVerificationAdmin)
