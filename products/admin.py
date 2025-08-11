from django.contrib import admin
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from .models import (
    Category, Product, ProductImage, Review, Advertisement, ContentSettings, 
    ProductOffer, FeaturedProduct, ProductAttribute, ProductAttributeOption, 
    CategoryAttribute, ProductVariant, ProductVariantAttribute
)

# Custom forms for better product management
class ProductForm(forms.ModelForm):
    """Custom form for products with attribute selection"""
    
    # Add fields for variant generation
    generate_variants = forms.BooleanField(
        required=False,
        initial=False,
        help_text="Check this to automatically generate variants based on selected attributes"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add dynamic fields for all available attributes
        if hasattr(self, 'instance') and self.instance and hasattr(self.instance, 'category') and self.instance.category:
            category_attributes = self.instance.category.category_attributes.filter(
                attribute__is_active=True
            ).select_related('attribute')
            
            for cat_attr in category_attributes:
                attribute = cat_attr.attribute
                field_name = f"selected_{attribute.attribute_type}_options"
                
                self.fields[field_name] = forms.ModelMultipleChoiceField(
                    queryset=attribute.options.filter(is_active=True),
                    widget=forms.CheckboxSelectMultiple,
                    required=cat_attr.is_required,
                    label=f"Available {attribute.name}",
                    help_text=f"Select {attribute.name} options for this product variants"
                )
        
        # Add category field to trigger attribute loading
        self.fields['category'].widget.attrs['onchange'] = 'loadCategoryAttributes(this.value);'
    
    def save(self, commit=True):
        instance = super().save(commit)
        
        # If generate_variants is checked and we have a saved instance
        if commit and self.cleaned_data.get('generate_variants', False) and instance.pk:
            self._generate_variants_for_product(instance)
        
        return instance
    
    def _generate_variants_for_product(self, product):
        """Generate variants based on selected attributes"""
        import itertools
        
        # Get selected attribute options
        selected_combinations = []
        for field_name, value in self.cleaned_data.items():
            if field_name.startswith('selected_') and field_name.endswith('_options') and value:
                selected_combinations.append(list(value))
        
        if not selected_combinations:
            return
        
        # Generate all combinations
        all_combinations = list(itertools.product(*selected_combinations))
        
        for combination in all_combinations:
            # Check if variant already exists
            existing_variant = product.variants.filter(
                variant_attributes__option__in=combination
            ).first()
            
            if existing_variant:
                continue
            
            # Create new variant
            variant = ProductVariant.objects.create(
                product=product,
                stock_count=0,  # Default stock
                price_adjustment=0,  # Default price adjustment
                is_active=True
            )
            
            # Add variant attributes
            for option in combination:
                ProductVariantAttribute.objects.create(
                    variant=variant,
                    attribute=option.attribute,
                    option=option
                )
    
    class Meta:
        model = Product
        fields = '__all__'


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
    readonly_fields = ('sku', 'final_price', 'stock_status', 'variant_display')
    fields = ('variant_display', 'stock_count', 'price_adjustment', 'final_price', 'stock_status', 'is_active')
    
    def variant_display(self, obj):
        if obj.pk:
            attributes = obj.variant_attributes.all()
            if attributes:
                attr_display = ", ".join([f"{attr.attribute.name}: {attr.option.display_name}" for attr in attributes])
                return attr_display
        return "New Variant"
    variant_display.short_description = 'Variant Attributes'

class ProductAdmin(admin.ModelAdmin):
    form = ProductForm
    list_display = ('name', 'base_price', 'total_stock', 'variant_count', 'category', 'seller_name_display', 'is_active', 'is_featured', 'average_rating')
    list_filter = ('is_active', 'is_featured', 'category', 'seller__user_type')
    search_fields = ('name', 'description', 'seller__email', 'seller__store_profile__store_name')
    readonly_fields = ('created_at', 'updated_at', 'total_stock', 'variant_count')
    inlines = [ProductImageInline, ProductVariantInline, ReviewInline]
    actions = ['generate_variants']
    
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
    
    def generate_variants(self, request, queryset):
        """Generate all possible variants for selected products based on their category attributes"""
        import itertools
        
        for product in queryset:
            # Get available attributes for this product's category
            category_attributes = product.category.category_attributes.filter(
                attribute__is_active=True
            ).select_related('attribute')
            
            if not category_attributes.exists():
                continue
            
            # Collect all attribute options
            attribute_combinations = []
            for cat_attr in category_attributes:
                attribute = cat_attr.attribute
                options = list(attribute.options.filter(is_active=True))
                if options:
                    attribute_combinations.append({
                        'attribute': attribute,
                        'options': options,
                        'is_required': cat_attr.is_required
                    })
            
            if not attribute_combinations:
                continue
            
            # Generate all possible combinations
            option_lists = [combo['options'] for combo in attribute_combinations]
            all_combinations = list(itertools.product(*option_lists))
            
            created_count = 0
            for combination in all_combinations:
                # Check if variant already exists
                variant_exists = product.variants.filter(
                    variant_attributes__attribute__in=[combo['attribute'] for combo in attribute_combinations],
                    variant_attributes__option__in=combination
                ).exists()
                
                if variant_exists:
                    continue
                
                # Create variant
                variant = ProductVariant.objects.create(
                    product=product,
                    stock_count=0,  # Admin will need to set this
                    price_adjustment=0,  # Admin will need to set this
                    is_active=True
                )
                
                # Create variant attributes
                for i, option in enumerate(combination):
                    attribute = attribute_combinations[i]['attribute']
                    ProductVariantAttribute.objects.create(
                        variant=variant,
                        attribute=attribute,
                        option=option
                    )
                
                created_count += 1
            
            if created_count > 0:
                self.message_user(request, f'Generated {created_count} variants for {product.name}')
        
        self.message_user(request, 'Variant generation complete. Remember to set stock counts and prices.')
    
    generate_variants.short_description = "Generate variants for selected products"

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('product__name', 'user__email', 'comment')
    readonly_fields = ('created_at',)

class AdvertisementAdminForm(forms.ModelForm):
    class Meta:
        model = Advertisement
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove required attribute from image field to prevent browser validation
        self.fields['image'].required = False
        self.fields['image_url'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        image = cleaned_data.get('image')
        image_url = cleaned_data.get('image_url')
        
        if not image and not image_url:
            # Raise specific field errors instead of general form error
            raise forms.ValidationError({
                'image_url': 'Please provide either an image file or an external image URL.',
            })
        
        return cleaned_data

class AdvertisementAdmin(admin.ModelAdmin):
    form = AdvertisementAdminForm
    list_display = ('title', 'display_location', 'is_active', 'order', 'created_at')
    list_filter = ('is_active', 'category', 'show_on_main', 'created_at')
    search_fields = ('title', 'description', 'category__name')
    readonly_fields = ('created_at', 'updated_at', 'display_location')
    ordering = ('category', 'order', '-created_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'is_active', 'order')
        }),
        ('Display Location', {
            'fields': ('category', 'show_on_main', 'display_location'),
            'description': 'Select a category to show ads on category pages, or leave empty and check "Show on Main" for main page ads. You can also show the same ad in both locations.'
        }),
        ('Image', {
            'fields': ('image', 'image_url'),
            'description': 'You must provide EITHER an uploaded image file OR an external image URL (not both). External URL takes precedence if both are provided.'
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
    
    def display_location(self, obj):
        return obj.display_location
    display_location.short_description = 'Display Location'

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
