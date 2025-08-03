from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.db.models import Q
from decimal import Decimal
from django.utils.translation import gettext_lazy as _

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = 'Categories'


class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='products',
        limit_choices_to=Q(user_type='artist') | Q(user_type='store')
    )
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
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
    image = models.ImageField(upload_to='advertisements/', verbose_name=_('Image'))
    image_url = models.URLField(blank=True, null=True, verbose_name=_('External Image URL'), 
                               help_text=_('Use this if image is hosted externally'))
    link_url = models.URLField(blank=True, null=True, verbose_name=_('Link URL'), 
                              help_text=_('URL to navigate when ad is clicked'))
    is_active = models.BooleanField(default=True, verbose_name=_('Is Active'))
    order = models.PositiveIntegerField(default=0, verbose_name=_('Display Order'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Advertisement')
        verbose_name_plural = _('Advertisements')
        ordering = ['order', '-created_at']
    
    def __str__(self):
        return self.title
    
    @property
    def image_display_url(self):
        """Return image URL for display (external URL takes precedence)"""
        if self.image_url:
            return self.image_url
        elif self.image:
            return self.image.url
        return None


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
