from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Customer, Artist, Store

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
    list_display = ('email', 'first_name', 'last_name', 'user_type', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'user_type')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'user_type', 'phone_number', 'address')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
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

admin.site.register(User, UserAdmin)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Artist, ArtistAdmin)
admin.site.register(Store, StoreAdmin)
