from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.db.models import Q
from decimal import Decimal
from django.utils.translation import gettext_lazy as _

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True, help_text="Description to help sellers understand what products belong in this category")
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = 'Categories'


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    is_predefined = models.BooleanField(default=False, help_text="True if created by admin, False if custom tag by seller")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True, related_name='tags', help_text="Category this tag belongs to (optional)")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        unique_together = ['name', 'category']


class CategoryVariantType(models.Model):
    """Define what types of variants each category can have"""
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='variant_types')
    name = models.CharField(max_length=50, help_text="e.g., 'Size', 'Color', 'Storage', 'Material'")
    is_required = models.BooleanField(default=True, help_text="Whether this variant type is required for products in this category")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.category.name} - {self.name}"
    
    class Meta:
        unique_together = ['category', 'name']


class CategoryVariantOption(models.Model):
    """Define the available options for each variant type"""
    variant_type = models.ForeignKey(CategoryVariantType, on_delete=models.CASCADE, related_name='options')
    value = models.CharField(max_length=50, help_text="e.g., 'Small', 'Red', '64GB', 'Cotton'")
    extra_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Additional price for this variant option")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.variant_type.name}: {self.value}"
    
    class Meta:
        unique_together = ['variant_type', 'value']


class ProductCategoryVariantOption(models.Model):
    """Junction table linking products to selected category variant options with stock/price info"""
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='selected_variants')
    category_variant_option = models.ForeignKey(CategoryVariantOption, on_delete=models.CASCADE)
    stock_count = models.PositiveIntegerField(default=0, help_text="Stock for this variant combination")
    price_adjustment = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, 
        help_text="Price adjustment from base price for this variant option"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.product.name} - {self.category_variant_option.variant_type.name}: {self.category_variant_option.value}"
    
    @property
    def final_price(self):
        """Calculate final price including extra price from variant option and price adjustment"""
        base_price = self.product.base_price
        extra_price = self.category_variant_option.extra_price
        return base_price + extra_price + self.price_adjustment
    
    @property
    def variant_type_name(self):
        return self.category_variant_option.variant_type.name
    
    @property
    def variant_option_value(self):
        return self.category_variant_option.value
    
    @property
    def is_in_stock(self):
        return self.stock_count > 0 and self.is_active
    
    @property
    def stock_status(self):
        if not self.is_active:
            return "Inactive"
        elif self.stock_count > 10:
            return "In stock"
        elif self.stock_count > 0:
            return f"{self.stock_count} left"
        else:
            return "Out of stock"
    
    class Meta:
        unique_together = ['product', 'category_variant_option']
        verbose_name = 'Product Variant Selection'
        verbose_name_plural = 'Product Variant Selections'


class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    base_price = models.DecimalField(max_digits=10, decimal_places=2)  # Base price for the product
    stock_quantity = models.PositiveIntegerField(default=0, help_text="Stock quantity for products without variants")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='products',
        limit_choices_to=Q(user_type='artist') | Q(user_type='store')
    )
    
    # Tags relationship
    tags = models.ManyToManyField(Tag, blank=True, related_name='products')
    
    # Admin moderated fields
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Product approval status
    APPROVAL_STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    approval_status = models.CharField(max_length=20, choices=APPROVAL_STATUS_CHOICES, default='pending')
    rejection_reason = models.TextField(blank=True, null=True, help_text="Reason for rejection if status is rejected")
    
    # Admin request tracking
    featured_request_pending = models.BooleanField(default=False, help_text="Seller has requested featured status")
    offers_request_pending = models.BooleanField(default=False, help_text="Seller has requested to be in latest offers")
    featured_requested_at = models.DateTimeField(null=True, blank=True)
    offers_requested_at = models.DateTimeField(null=True, blank=True)
    
    # Combination variant stock storage (for frontend UX combinations like "29_27")
    combination_stocks = models.JSONField(default=dict, blank=True, help_text="Stock quantities for variant combinations like {'29_27': 10}")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews:
            return Decimal(sum(review.rating for review in reviews)) / Decimal(len(reviews))
        return Decimal('0')
    
    @property
    def seller_name(self):
        if self.seller.user_type == 'artist':
            try:
                return f"Artist: {self.seller.first_name} {self.seller.last_name}"
            except:
                return f"Artist: {self.seller.email}"
        elif self.seller.user_type == 'store':
            try:
                return f"Store: {self.seller.store_profile.store_name}"
            except:
                return f"Store: {self.seller.email}"
        return self.seller.email
    
    # Backward compatibility properties
    @property
    def price(self):
        """Returns base price for backward compatibility"""
        return self.base_price
    
    @property
    def stock(self):
        """Returns stock - either from combination stocks, selected variants, or direct product stock"""
        if self.has_variants:
            # Check if we have combination stock overrides
            if self.combination_stocks and len(self.combination_stocks) > 0:
                # Sum all combination stocks
                total_combination_stock = sum(int(stock) for stock in self.combination_stocks.values())
                return total_combination_stock
            else:
                # Fallback to individual variant stock
                return sum(variant.stock_count for variant in self.selected_variants.filter(is_active=True))
        else:
            # For products without variants, use direct stock
            return self.stock_quantity
    
    # Category Variant management methods
    def get_available_category_variants(self):
        """Get all category variant types available for this product's category"""
        return self.category.variant_types.all().order_by('name')
    
    def get_category_variant_options(self, variant_type):
        """Get available options for a specific category variant type"""
        return variant_type.options.filter(is_active=True).order_by('value')
    
    def get_selected_variants_by_type(self, variant_type_name):
        """Find selected variants matching specific variant type"""
        return self.selected_variants.filter(
            category_variant_option__variant_type__name=variant_type_name,
            is_active=True
        )
    
    @property
    def has_variants(self):
        """Check if product has any selected variants"""
        return self.selected_variants.filter(is_active=True).exists()
    
    @property
    def available_variant_types(self):
        """Get all available variant types for this product's category"""
        return self.category.variant_types.all().order_by('name')
    
    def get_price_range(self):
        """Get min and max price across all selected variants"""
        if not self.has_variants:
            return self.base_price, self.base_price
        
        variants = self.selected_variants.filter(is_active=True)
        prices = [v.final_price for v in variants]
        return min(prices), max(prices)
    
    def get_stock_status(self):
        """Get overall stock status for the product"""
        total_stock = self.stock
        if total_stock > 10:
            return "In stock"
        elif total_stock > 0:
            return f"{total_stock} left"
        else:
            return "Out of stock"
    
    @property
    def has_stock(self):
        """Check if product has any stock"""
        return self.stock > 0


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/')
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Image for {self.product.name}"


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Review by {self.user.email} for {self.product.name}"
    
    class Meta:
        unique_together = ('product', 'user')


class Advertisement(models.Model):
    """Model for managing ads slider in the app"""
    title = models.CharField(max_length=200, verbose_name=_('Title'))
    description = models.TextField(blank=True, null=True, verbose_name=_('Description'))
    image = models.ImageField(upload_to='advertisements/', blank=True, null=True, verbose_name=_('Image'))
    image_url = models.URLField(blank=True, null=True, verbose_name=_('External Image URL'), 
                               help_text=_('Use this if image is hosted externally'))
    link_url = models.URLField(blank=True, null=True, verbose_name=_('Link URL'), 
                              help_text=_('URL to navigate when ad is clicked'))
    
    # Category relationship - null means it shows on main page
    category = models.ForeignKey(
        'Category', 
        on_delete=models.CASCADE, 
        blank=True, 
        null=True,
        verbose_name=_('Category'),
        help_text=_('Leave empty to show on main page, or select a category for category-specific ads')
    )
    
    # Display settings
    is_active = models.BooleanField(default=True, verbose_name=_('Is Active'))
    order = models.PositiveIntegerField(default=0, verbose_name=_('Display Order'))
    show_on_main = models.BooleanField(default=True, verbose_name=_('Show on Main Page'), 
                                     help_text=_('Show this ad on the main page slider'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Advertisement')
        verbose_name_plural = _('Advertisements')
        ordering = ['category', 'order', '-created_at']
        indexes = [
            models.Index(fields=['is_active', 'show_on_main']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['order']),
        ]
    
    def __str__(self):
        category_name = f" ({self.category.name})" if self.category else " (Main Page)"
        return f"{self.title}{category_name}"
    
    def clean(self):
        """Custom validation to ensure either image or image_url is provided"""
        from django.core.exceptions import ValidationError
        
        if not self.image and not self.image_url:
            raise ValidationError({
                'image': _('Please provide either an image file or an external image URL.'),
                'image_url': _('Please provide either an image file or an external image URL.')
            })
    
    @property
    def image_display_url(self):
        """Return image URL for display (external URL takes precedence)"""
        if self.image_url:
            return self.image_url
        elif self.image:
            return self.image.url
        return None
    
    @property
    def display_location(self):
        """Return display location description"""
        locations = []
        if self.show_on_main:
            locations.append("Main Page")
        if self.category:
            locations.append(f"Category: {self.category.name}")
        return " & ".join(locations) if locations else "Inactive"


class ContentSettings(models.Model):
    """Model for managing app content display settings"""
    
    # Section visibility toggles
    show_latest_offers = models.BooleanField(default=True, verbose_name=_('Show Latest Offers'))
    show_featured_products = models.BooleanField(default=True, verbose_name=_('Show Featured Products'))
    show_top_artists = models.BooleanField(default=True, verbose_name=_('Show Top Artists'))
    show_top_stores = models.BooleanField(default=True, verbose_name=_('Show Top Stores'))
    show_ads_slider = models.BooleanField(default=True, verbose_name=_('Show Ads Slider'))
    
    # Content limits
    max_products_per_section = models.PositiveIntegerField(default=10, verbose_name=_('Max Products Per Section'))
    max_artists_to_show = models.PositiveIntegerField(default=8, verbose_name=_('Max Artists to Show'))
    max_stores_to_show = models.PositiveIntegerField(default=6, verbose_name=_('Max Stores to Show'))
    max_ads_to_show = models.PositiveIntegerField(default=6, verbose_name=_('Max Ads to Show'))
    
    # Auto-refresh settings  
    ads_rotation_interval = models.PositiveIntegerField(default=4, verbose_name=_('Ads Rotation Interval (seconds)'))
    content_refresh_interval = models.PositiveIntegerField(default=15, verbose_name=_('Content Refresh Interval (minutes)'))
    
    # Cache settings
    enable_content_cache = models.BooleanField(default=True, verbose_name=_('Enable Content Caching'))
    cache_duration = models.PositiveIntegerField(default=5, verbose_name=_('Cache Duration (minutes)'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Content Settings')
        verbose_name_plural = _('Content Settings')
    
    def __str__(self):
        return f"Content Settings - Updated {self.updated_at.strftime('%Y-%m-%d %H:%M')}"
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and ContentSettings.objects.exists():
            raise ValueError("Only one ContentSettings instance is allowed")
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """Get or create the content settings instance"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings


class ProductOffer(models.Model):
    """Model for managing product offers that appear in ReactiveLatestOffers"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='offers')
    discount_percentage = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(90)],
        help_text="Discount percentage (1-90%)"
    )
    offer_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    description = models.TextField(blank=True, null=True, help_text="Special offer description")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Product Offer')
        verbose_name_plural = _('Product Offers')
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        # Calculate offer price if not provided
        if not self.offer_price:
            original_price = self.product.price
            discount_decimal = Decimal(self.discount_percentage) / Decimal('100')
            self.offer_price = original_price * (Decimal('1') - discount_decimal)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.product.name} - {self.discount_percentage}% OFF"
    
    @property
    def is_valid(self):
        """Check if offer is currently valid"""
        from django.utils import timezone
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date
    
    @property
    def savings_amount(self):
        """Calculate savings amount"""
        return self.product.price - self.offer_price


class FeaturedProduct(models.Model):
    """Model for managing featured products that appear in ReactiveFeaturedProducts"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='featured_entries')
    priority = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first")
    featured_since = models.DateTimeField(auto_now_add=True)
    featured_until = models.DateTimeField(blank=True, null=True, help_text="Leave blank for indefinite featuring")
    reason = models.CharField(max_length=200, blank=True, null=True, help_text="Reason for featuring")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = _('Featured Product')
        verbose_name_plural = _('Featured Products')
        ordering = ['priority', '-featured_since']
    
    def __str__(self):
        return f"Featured: {self.product.name}"
    
    @property
    def is_valid(self):
        """Check if featured status is currently valid"""
        from django.utils import timezone
        if not self.is_active:
            return False
        if self.featured_until:
            return timezone.now() <= self.featured_until
        return True


# New models for flexible product attributes system
class ProductAttribute(models.Model):
    """Defines available attributes for products (e.g., Color, Size, Frame Type)"""
    ATTRIBUTE_TYPES = [
        ('color', 'Color'),
        ('size', 'Size'),
        ('frame_color', 'Frame Color'),
        ('material', 'Material'),
        ('custom', 'Custom'),
    ]
    
    name = models.CharField(max_length=100)  # e.g., "Frame Color", "Size"
    attribute_type = models.CharField(max_length=20, choices=ATTRIBUTE_TYPES)
    is_required = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Product Attribute'
        verbose_name_plural = 'Product Attributes'


class ProductAttributeOption(models.Model):
    """Defines available options for each attribute (e.g., Red, Blue for Color)"""
    attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE, related_name='options')
    value = models.CharField(max_length=100)  # e.g., "Red", "Large", "20x30cm"
    display_name = models.CharField(max_length=100, blank=True)  # For different language display
    color_code = models.CharField(max_length=7, blank=True, null=True)  # For color attributes #FF0000
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"{self.attribute.name}: {self.value}"
    
    def save(self, *args, **kwargs):
        if not self.display_name:
            self.display_name = self.value
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = 'Attribute Option'
        verbose_name_plural = 'Attribute Options'
        ordering = ['sort_order', 'value']


class CategoryAttribute(models.Model):
    """Links categories to their available attributes"""
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='category_attributes')
    attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE)
    is_required = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"{self.category.name} - {self.attribute.name}"
    
    class Meta:
        unique_together = ['category', 'attribute']
        ordering = ['sort_order']


class ProductVariant(models.Model):
    """Individual product variants with specific category variant combinations"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    sku = models.CharField(max_length=100, unique=True, blank=True)  # Auto-generated SKU
    stock_count = models.PositiveIntegerField(default=0)
    price_adjustment = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # +/- from base price
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        variant_options = self.variant_options.all()
        if variant_options:
            options_str = ", ".join([f"{opt.variant_type.name}: {opt.value}" for opt in variant_options])
            return f"{self.product.name} - {options_str}"
        return f"{self.product.name} - No variants"
    
    @property
    def final_price(self):
        # Calculate final price including extra prices from variant options
        base_price = self.product.base_price + self.price_adjustment
        extra_price = sum(option.extra_price for option in self.variant_options.all())
        return base_price + extra_price
    
    @property
    def is_in_stock(self):
        return self.stock_count > 0
    
    @property
    def stock_status(self):
        if self.stock_count > 10:
            return "+10 available"
        elif self.stock_count > 0:
            return f"{self.stock_count} left"
        else:
            return "Out of stock"
    
    def save(self, *args, **kwargs):
        if not self.sku:
            # Generate SKU based on product ID and variant options
            super().save(*args, **kwargs)  # Save first to get ID
            options = self.variant_options.all()
            option_codes = [opt.value[:3].upper() for opt in options]
            self.sku = f"P{self.product.id}V{self.id}-{''.join(option_codes)}"
            super().save(update_fields=['sku'])
        else:
            super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = 'Product Variant'
        verbose_name_plural = 'Product Variants'


class ProductVariantOption(models.Model):
    """Links variants to their specific category variant options"""
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='variant_options')
    category_variant_option = models.ForeignKey(CategoryVariantOption, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.variant} - {self.category_variant_option}"
    
    # Convenience properties for easier access
    @property
    def variant_type(self):
        return self.category_variant_option.variant_type
    
    @property
    def value(self):
        return self.category_variant_option.value
    
    @property
    def extra_price(self):
        return self.category_variant_option.extra_price
    
    class Meta:
        unique_together = ['variant', 'category_variant_option']
        verbose_name = 'Product Variant Option'
        verbose_name_plural = 'Product Variant Options'


# Keep the old models for backward compatibility during migration
class ProductVariantAttribute(models.Model):
    """DEPRECATED: Links variants to their specific attribute values - kept for backward compatibility"""
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='variant_attributes')
    attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE)
    option = models.ForeignKey(ProductAttributeOption, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.variant} - {self.attribute.name}: {self.option.value}"
    
    class Meta:
        unique_together = ['variant', 'attribute']


class DiscountRequest(models.Model):
    """Model for handling seller discount requests that need admin approval"""
    DISCOUNT_STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='discount_requests')
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='discount_requests')
    
    # Discount details
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    requested_discount_percentage = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(90)])
    final_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_reason = models.TextField(help_text="Seller's reason for requesting this discount")
    
    # Admin approval
    status = models.CharField(max_length=20, choices=DISCOUNT_STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True, null=True, help_text="Admin notes about the approval/rejection")
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_discounts')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Offer placement requests
    request_featured = models.BooleanField(default=False, help_text="Request to add to featured products")
    request_latest_offers = models.BooleanField(default=False, help_text="Request to add to latest offers section")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Discount Request: {self.product.name} - {self.requested_discount_percentage}% OFF"
    
    def save(self, *args, **kwargs):
        # Calculate final price if not provided
        if not self.final_price:
            discount_decimal = Decimal(self.requested_discount_percentage) / Decimal('100')
            self.final_price = self.original_price * (Decimal('1') - discount_decimal)
        super().save(*args, **kwargs)
    
    @property
    def savings_amount(self):
        """Calculate savings amount"""
        return self.original_price - self.final_price
    
    class Meta:
        verbose_name = 'Discount Request'
        verbose_name_plural = 'Discount Requests'
        ordering = ['-created_at']
