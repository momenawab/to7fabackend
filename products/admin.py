from django.contrib import admin
from .models import Category, Product, ProductImage, Review

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'name': ('name',)}

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0
    readonly_fields = ('user', 'rating', 'comment', 'created_at')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'category', 'seller_name_display', 'is_active', 'is_featured', 'average_rating')
    list_filter = ('is_active', 'is_featured', 'category', 'seller__user_type')
    search_fields = ('name', 'description', 'seller__email', 'seller__store_profile__store_name')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ProductImageInline, ReviewInline]
    
    def average_rating(self, obj):
        return obj.average_rating
    average_rating.short_description = 'Avg. Rating'
    
    def seller_name_display(self, obj):
        return obj.seller_name
    seller_name_display.short_description = 'Seller'

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('product__name', 'user__email', 'comment')
    readonly_fields = ('created_at',)

admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Review, ReviewAdmin)
