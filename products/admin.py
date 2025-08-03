from django.contrib import admin
from .models import Category, Product, ProductImage, Review, Advertisement, ContentSettings, ProductOffer, FeaturedProduct

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

admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(Advertisement, AdvertisementAdmin)
admin.site.register(ContentSettings, ContentSettingsAdmin)
admin.site.register(ProductOffer, ProductOfferAdmin)
admin.site.register(FeaturedProduct, FeaturedProductAdmin)
