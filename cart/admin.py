from django.contrib import admin
from .models import Cart, CartItem

class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('line_total',)

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_items', 'subtotal', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('total_items', 'subtotal')
    inlines = [CartItemInline]
    date_hierarchy = 'created_at'

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart', 'product', 'quantity', 'line_total', 'added_at', 'updated_at')
    list_filter = ('added_at', 'updated_at')
    search_fields = ('cart__user__email', 'product__name')
    readonly_fields = ('line_total',)
    raw_id_fields = ('cart', 'product')
    date_hierarchy = 'added_at'
