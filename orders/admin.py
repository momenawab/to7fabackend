from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'price', 'seller_name_display', 'commission_rate', 'commission_amount')
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def seller_name_display(self, obj):
        return obj.seller_name
    seller_name_display.short_description = 'Seller'

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_amount', 'status', 'payment_status', 'created_at')
    list_filter = ('status', 'payment_status')
    search_fields = ('id', 'user__email', 'shipping_address')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('user', 'total_amount', 'status', 'payment_status')
        }),
        ('Shipping Information', {
            'fields': ('shipping_address', 'shipping_cost')
        }),
        ('Payment Information', {
            'fields': ('payment_method',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )

admin.site.register(Order, OrderAdmin)
