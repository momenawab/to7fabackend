from django.contrib import admin
from .models import (
    Category, Product, ProductImage, Review, Advertisement, ContentSettings, 
    ProductOffer, FeaturedProduct, ProductAttribute, ProductAttributeOption, 
    CategoryAttribute, ProductVariant, ProductVariantAttribute
)

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

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    readonly_fields = ('sku', 'final_price', 'stock_status')
    fields = ('sku', 'stock_count', 'price_adjustment', 'final_price', 'stock_status', 'is_active')

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_price', 'total_stock', 'variant_count', 'category', 'seller_name_display', 'is_active', 'is_featured', 'average_rating')
    list_filter = ('is_active', 'is_featured', 'category', 'seller__user_type')
    search_fields = ('name', 'description', 'seller__email', 'seller__store_profile__store_name')
    readonly_fields = ('created_at', 'updated_at', 'total_stock', 'variant_count')
    inlines = [ProductImageInline, ProductVariantInline, ReviewInline]
    
    def average_rating(self, obj):
        return obj.average_rating
    average_rating.short_description = 'Avg. Rating'
    
    def seller_name_display(self, obj):
        return obj.seller_name
    seller_name_display.short_description = 'Seller'
    
    def total_stock(self, obj):
        return obj.stock
    total_stock.short_description = 'Total Stock'
    
    def variant_count(self, obj):
        return obj.variants.filter(is_active=True).count()
    variant_count.short_description = 'Variants'

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('product__name', 'user__email', 'comment')
    readonly_fields = ('created_at',)

class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'order', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('order', '-created_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'is_active', 'order')
        }),
        ('Image', {
            'fields': ('image', 'image_url'),
            'description': 'You can either upload an image or provide an external URL. External URL takes precedence.'
        }),
        ('Link', {
            'fields': ('link_url',),
            'description': 'Optional URL to navigate to when the ad is clicked.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

class ContentSettingsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'show_latest_offers', 'show_featured_products', 'show_top_artists', 'show_top_stores', 'show_ads_slider')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Section Visibility', {
            'fields': ('show_latest_offers', 'show_featured_products', 'show_top_artists', 'show_top_stores', 'show_ads_slider')
        }),
        ('Content Limits', {
            'fields': ('max_products_per_section', 'max_artists_to_show', 'max_stores_to_show', 'max_ads_to_show')
        }),
        ('Auto-refresh Settings', {
            'fields': ('ads_rotation_interval', 'content_refresh_interval'),
            'description': 'Intervals in seconds/minutes for automatic content updates in the app.'
        }),
        ('Cache Settings', {
            'fields': ('enable_content_cache', 'cache_duration'),
            'description': 'Content caching settings to improve app performance.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one instance
        return not ContentSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of settings
        return False

class ProductOfferAdmin(admin.ModelAdmin):
    list_display = ('product', 'discount_percentage', 'offer_price', 'start_date', 'end_date', 'is_active', 'is_valid')
    list_filter = ('is_active', 'start_date', 'end_date', 'product__category')
    search_fields = ('product__name', 'description')
    readonly_fields = ('offer_price', 'savings_amount', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Product & Discount', {
            'fields': ('product', 'discount_percentage', 'offer_price', 'savings_amount')
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date', 'is_active')
        }),
        ('Details', {
            'fields': ('description',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_valid(self, obj):
        return obj.is_valid
    is_valid.boolean = True
    is_valid.short_description = 'Currently Valid'

class FeaturedProductAdmin(admin.ModelAdmin):
    list_display = ('product', 'priority', 'featured_since', 'featured_until', 'is_active', 'is_valid')
    list_filter = ('is_active', 'featured_since', 'featured_until', 'product__category')
    search_fields = ('product__name', 'reason')
    ordering = ('priority', '-featured_since')
    
    fieldsets = (
        ('Product & Priority', {
            'fields': ('product', 'priority', 'reason')
        }),
        ('Schedule', {
            'fields': ('featured_until', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('featured_since',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('featured_since',)
    
    def is_valid(self, obj):
        return obj.is_valid
    is_valid.boolean = True
    is_valid.short_description = 'Currently Valid'

# Product Attribute Management
class ProductAttributeOptionInline(admin.TabularInline):
    model = ProductAttributeOption
    extra = 1
    fields = ('value', 'display_name', 'color_code', 'is_active', 'sort_order')

class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ('name', 'attribute_type', 'is_required', 'is_active', 'option_count')
    list_filter = ('attribute_type', 'is_required', 'is_active')
    search_fields = ('name',)
    inlines = [ProductAttributeOptionInline]
    
    def option_count(self, obj):
        return obj.options.filter(is_active=True).count()
    option_count.short_description = 'Active Options'

class ProductAttributeOptionAdmin(admin.ModelAdmin):
    list_display = ('attribute', 'value', 'display_name', 'color_code', 'is_active', 'sort_order')
    list_filter = ('attribute', 'is_active')
    search_fields = ('value', 'display_name')
    list_editable = ('is_active', 'sort_order')

# Category Attribute Management
class CategoryAttributeInline(admin.TabularInline):
    model = CategoryAttribute
    extra = 1
    fields = ('attribute', 'is_required', 'sort_order')

class CategoryAttributeAdmin(admin.ModelAdmin):
    list_display = ('category', 'attribute', 'is_required', 'sort_order')
    list_filter = ('category', 'attribute', 'is_required')
    search_fields = ('category__name', 'attribute__name')

# Enhanced Category Admin with attributes
class EnhancedCategoryAdmin(CategoryAdmin):
    inlines = [CategoryAttributeInline]

# Product Variant Management
class ProductVariantAttributeInline(admin.TabularInline):
    model = ProductVariantAttribute
    extra = 0
    fields = ('attribute', 'option')

class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'sku', 'variant_attributes_display', 'stock_count', 'final_price', 'is_active')
    list_filter = ('is_active', 'product__category')
    search_fields = ('product__name', 'sku')
    readonly_fields = ('sku', 'final_price', 'stock_status')
    inlines = [ProductVariantAttributeInline]
    
    def variant_attributes_display(self, obj):
        attributes = obj.variant_attributes.all()
        return ", ".join([f"{attr.attribute.name}: {attr.option.value}" for attr in attributes])
    variant_attributes_display.short_description = 'Attributes'

# Register all models
admin.site.register(Category, EnhancedCategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(Advertisement, AdvertisementAdmin)
admin.site.register(ContentSettings, ContentSettingsAdmin)
admin.site.register(ProductOffer, ProductOfferAdmin)
admin.site.register(FeaturedProduct, FeaturedProductAdmin)

# Register new attribute and variant models
admin.site.register(ProductAttribute, ProductAttributeAdmin)
admin.site.register(ProductAttributeOption, ProductAttributeOptionAdmin)
admin.site.register(CategoryAttribute, CategoryAttributeAdmin)
admin.site.register(ProductVariant, ProductVariantAdmin)
