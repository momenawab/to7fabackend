from django.contrib import admin
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from .models import (
    Category, Product, ProductImage, Review, Advertisement, ContentSettings, 
    ProductOffer, FeaturedProduct, ProductAttribute, ProductAttributeOption, 
    CategoryAttribute, ProductVariant, ProductVariantAttribute, Tag, 
    CategoryVariantType, CategoryVariantOption, DiscountRequest, ProductVariantOption,
    SubcategorySectionControl
)

# Custom forms for better product management
class ProductForm(forms.ModelForm):
    """Custom form for products with better category handling"""
    
    # Add fields for variant generation
    generate_variants = forms.BooleanField(
        required=False,
        initial=False,
        help_text="Check this to automatically generate variants based on selected attributes"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Ensure category field is properly configured
        if 'category' in self.fields:
            self.fields['category'].queryset = Category.objects.filter(is_active=True)
            self.fields['category'].empty_label = "Select a category"
        
        # Ensure seller field shows appropriate users
        if 'seller' in self.fields:
            from custom_auth.models import User
            self.fields['seller'].queryset = User.objects.filter(
                user_type__in=['artist', 'store'], is_active=True
            )
            self.fields['seller'].empty_label = "Select a seller"
        
        # Add dynamic fields for all available attributes only for existing products with categories
        if (hasattr(self, 'instance') and self.instance and self.instance.pk and 
            hasattr(self.instance, 'category') and self.instance.category):
            try:
                category_attributes = self.instance.category.category_attributes.filter(
                    attribute__is_active=True
                ).select_related('attribute')
                
                for cat_attr in category_attributes:
                    attribute = cat_attr.attribute
                    field_name = f"selected_{attribute.attribute_type}_options"
                    
                    self.fields[field_name] = forms.ModelMultipleChoiceField(
                        queryset=attribute.options.filter(is_active=True),
                        widget=forms.CheckboxSelectMultiple,
                        required=False,  # Make it optional to avoid form errors
                        label=f"Available {attribute.name}",
                        help_text=f"Select {attribute.name} options for this product variants"
                    )
            except Exception as e:
                # If there's any error with category attributes, just continue
                pass
    
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
        fields = ['name', 'description', 'base_price', 'stock_quantity', 'category', 'seller', 'is_featured', 'is_active', 'generate_variants']


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
    list_display = ('name', 'base_price', 'stock_quantity', 'total_stock', 'variant_count', 'category', 'seller_name_display', 'is_active', 'is_featured')
    list_filter = ('is_active', 'is_featured', 'category', 'seller__user_type')
    search_fields = ('name', 'description', 'seller__email')
    readonly_fields = ('created_at', 'updated_at', 'total_stock', 'variant_count')
    inlines = [ProductImageInline, ProductVariantInline, ReviewInline]
    actions = ['generate_variants']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category')
        }),
        ('Seller', {
            'fields': ('seller',),
            'description': 'Select the seller for this product'
        }),
        ('Pricing & Stock', {
            'fields': ('base_price', 'stock_quantity'),
            'description': 'For products without variants, set the stock quantity here. For products with variants, stock is managed per variant below.'
        }),
        ('Settings', {
            'fields': ('is_active', 'is_featured')
        }),
        ('Variant Generation', {
            'fields': ('generate_variants',),
            'description': 'Check this box to automatically generate variants based on category attributes when saving. Only works after saving the product first.',
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('total_stock', 'variant_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def average_rating(self, obj):
        return obj.average_rating
    average_rating.short_description = 'Avg. Rating'
    
    def seller_name_display(self, obj):
        try:
            return obj.seller_name
        except:
            return obj.seller.email if obj.seller else 'No Seller'
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

# Simple Product Admin for easier management
class SimpleProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_price', 'stock_quantity', 'category', 'seller_email', 'is_active')
    list_filter = ('is_active', 'is_featured', 'category')
    search_fields = ('name', 'description', 'seller__email')
    list_editable = ('stock_quantity', 'is_active')
    
    fields = ('name', 'description', 'base_price', 'stock_quantity', 'category', 'seller', 'is_active', 'is_featured')
    
    def seller_email(self, obj):
        return obj.seller.email if obj.seller else 'No Seller'
    seller_email.short_description = 'Seller Email'
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        
        # Filter categories to active ones
        if 'category' in form.base_fields:
            form.base_fields['category'].queryset = Category.objects.filter(is_active=True)
        
        # Filter sellers to artists and stores only
        if 'seller' in form.base_fields:
            from custom_auth.models import User
            form.base_fields['seller'].queryset = User.objects.filter(
                user_type__in=['artist', 'store'], is_active=True
            )
        
        return form

# Register all models
admin.site.register(Category, EnhancedCategoryAdmin)
admin.site.register(Product, SimpleProductAdmin)  # Use SimpleProductAdmin instead
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


# New Product Wizard Admin Classes

class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_predefined', 'created_by', 'created_at')
    list_filter = ('is_predefined', 'category', 'created_at')
    search_fields = ('name', 'category__name', 'created_by__username')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Tag Information', {
            'fields': ('name', 'category', 'is_predefined', 'created_by')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

class CategoryVariantOptionInline(admin.TabularInline):
    model = CategoryVariantOption
    extra = 1
    fields = ('value', 'extra_price', 'is_active')

class CategoryVariantTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_required', 'option_count')
    list_filter = ('category', 'is_required')
    search_fields = ('name', 'category__name')
    inlines = [CategoryVariantOptionInline]
    
    def option_count(self, obj):
        return obj.options.filter(is_active=True).count()
    option_count.short_description = 'Active Options'

class CategoryVariantOptionAdmin(admin.ModelAdmin):
    list_display = ('variant_type', 'value', 'extra_price', 'is_active')
    list_filter = ('variant_type__category', 'variant_type', 'is_active')
    search_fields = ('variant_type__name', 'value')
    list_editable = ('extra_price', 'is_active')

class DiscountRequestAdmin(admin.ModelAdmin):
    list_display = ('product', 'seller', 'requested_discount_percentage', 'final_price', 'status', 'created_at')
    list_filter = ('status', 'request_featured', 'request_latest_offers', 'created_at')
    search_fields = ('product__name', 'seller__username', 'discount_reason')
    readonly_fields = ('final_price', 'savings_amount', 'created_at', 'updated_at')
    actions = ['approve_discount', 'reject_discount']
    
    fieldsets = (
        ('Request Information', {
            'fields': ('product', 'seller', 'discount_reason')
        }),
        ('Pricing Details', {
            'fields': ('original_price', 'requested_discount_percentage', 'final_price', 'savings_amount')
        }),
        ('Marketing Requests', {
            'fields': ('request_featured', 'request_latest_offers')
        }),
        ('Admin Review', {
            'fields': ('status', 'admin_notes', 'reviewed_by', 'reviewed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def approve_discount(self, request, queryset):
        """Approve selected discount requests"""
        from django.utils import timezone
        
        updated = queryset.filter(status='pending').update(
            status='approved',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        
        self.message_user(request, f'{updated} discount requests approved.')
    
    def reject_discount(self, request, queryset):
        """Reject selected discount requests"""
        from django.utils import timezone
        
        updated = queryset.filter(status='pending').update(
            status='rejected',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        
        self.message_user(request, f'{updated} discount requests rejected.')
    
    approve_discount.short_description = "Approve selected discount requests"
    reject_discount.short_description = "Reject selected discount requests"

class ProductVariantOptionInline(admin.TabularInline):
    model = ProductVariantOption
    extra = 0
    fields = ('category_variant_option', 'variant_type', 'value', 'extra_price')
    readonly_fields = ('variant_type', 'value', 'extra_price')
    
    def variant_type(self, obj):
        return obj.category_variant_option.variant_type.name if obj.category_variant_option else ''
    variant_type.short_description = 'Variant Type'
    
    def value(self, obj):
        return obj.category_variant_option.value if obj.category_variant_option else ''
    value.short_description = 'Value'
    
    def extra_price(self, obj):
        return obj.category_variant_option.extra_price if obj.category_variant_option else 0
    extra_price.short_description = 'Extra Price'

# Enhanced Product Variant Admin with new system
class EnhancedProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'sku', 'variant_options_display', 'stock_count', 'final_price', 'is_active')
    list_filter = ('is_active', 'product__category')
    search_fields = ('product__name', 'sku')
    readonly_fields = ('sku', 'final_price', 'stock_status')
    inlines = [ProductVariantOptionInline]
    
    def variant_options_display(self, obj):
        options = obj.variant_options.all()
        return ", ".join([f"{opt.variant_type.name}: {opt.value}" for opt in options])
    variant_options_display.short_description = 'Variant Options'

# Register new models
admin.site.register(Tag, TagAdmin)
admin.site.register(CategoryVariantType, CategoryVariantTypeAdmin)
admin.site.register(CategoryVariantOption, CategoryVariantOptionAdmin)
admin.site.register(DiscountRequest, DiscountRequestAdmin)

# Re-register ProductVariant with enhanced admin
admin.site.unregister(ProductVariant)
admin.site.register(ProductVariant, EnhancedProductVariantAdmin)

# Subcategory Section Control Admin
class SubcategorySectionControlAdmin(admin.ModelAdmin):
    list_display = ('subcategory', 'parent_category', 'is_section_enabled', 'max_products_to_show', 'section_priority', 'products_count')
    list_filter = ('is_section_enabled', 'subcategory__parent', 'section_priority')
    search_fields = ('subcategory__name', 'subcategory__parent__name')
    list_editable = ('is_section_enabled', 'max_products_to_show', 'section_priority')
    filter_horizontal = ('featured_products',)
    ordering = ('subcategory__parent__name', 'section_priority', 'subcategory__name')
    
    fieldsets = (
        ('Subcategory Section', {
            'fields': ('subcategory', 'is_section_enabled', 'section_priority')
        }),
        ('Display Settings', {
            'fields': ('max_products_to_show',),
            'description': 'Control how many products to show in this subcategory section'
        }),
        ('Featured Products (Optional)', {
            'fields': ('featured_products',),
            'description': 'Select specific products to feature in this section. Leave empty to automatically show latest products from this subcategory.',
            'classes': ('collapse',)
        }),
        ('Information', {
            'fields': ('products_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('products_count', 'created_at', 'updated_at')
    
    def parent_category(self, obj):
        return obj.subcategory.parent.name if obj.subcategory.parent else 'No Parent'
    parent_category.short_description = 'Parent Category'
    
    def products_count(self, obj):
        return obj.products_count
    products_count.short_description = 'Products to Display'
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        
        # Filter subcategories to only show subcategories (those with parents)
        if 'subcategory' in form.base_fields:
            form.base_fields['subcategory'].queryset = Category.objects.filter(
                parent__isnull=False, is_active=True
            ).select_related('parent')
            form.base_fields['subcategory'].empty_label = "Select a subcategory"
        
        # Filter featured products to only show active products
        if 'featured_products' in form.base_fields:
            form.base_fields['featured_products'].queryset = Product.objects.filter(
                is_active=True, approval_status='approved'
            ).select_related('category')
        
        return form
    
    def get_queryset(self, request):
        """Override to show only subcategory section controls"""
        return super().get_queryset(request).select_related(
            'subcategory', 'subcategory__parent'
        ).prefetch_related('featured_products')

# Register the new admin
admin.site.register(SubcategorySectionControl, SubcategorySectionControlAdmin)
