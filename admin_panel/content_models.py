# Content management models for admin panel
from django.db import models
from django.utils.translation import gettext_lazy as _
from custom_auth.models import User
from products.models import Category

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


class AdType(models.Model):
    """Model for managing different types of ads"""
    TYPE_CHOICES = (
        ('home_slider', _('Home Page Slider')),
        ('category_slider', _('Category Slider')),
        ('offer_ad', _('Offer Advertisement')),
        ('featured_product', _('Featured Product')),
    )
    
    name = models.CharField(max_length=50, choices=TYPE_CHOICES, unique=True, verbose_name=_('Ad Type'))
    name_ar = models.CharField(max_length=100, verbose_name=_('Arabic Name'))
    description = models.TextField(blank=True, null=True, verbose_name=_('Description'))
    requires_category = models.BooleanField(default=False, verbose_name=_('Requires Category Selection'))
    is_active = models.BooleanField(default=True, verbose_name=_('Is Active'))
    display_order = models.PositiveIntegerField(default=0, verbose_name=_('Display Order'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Ad Type')
        verbose_name_plural = _('Ad Types')
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.name_ar or self.get_name_display()


class AdPricing(models.Model):
    """Model for managing ad pricing"""
    DURATION_CHOICES = (
        ('daily', _('Daily')),
        ('weekly', _('Weekly')),
        ('monthly', _('Monthly')),
    )
    
    ad_type = models.ForeignKey(AdType, on_delete=models.CASCADE, related_name='pricing')
    duration = models.CharField(max_length=20, choices=DURATION_CHOICES, verbose_name=_('Duration'))
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Price (EGP)'))
    min_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name=_('Minimum Price'))
    max_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name=_('Maximum Price'))
    is_active = models.BooleanField(default=True, verbose_name=_('Is Active'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Ad Pricing')
        verbose_name_plural = _('Ad Pricing')
        unique_together = ['ad_type', 'duration']
        ordering = ['ad_type', 'duration']
    
    def __str__(self):
        return f"{self.ad_type.name_ar} - {self.get_duration_display()} - {self.price} EGP"


class AdBookingRequest(models.Model):
    """Model for managing ad booking requests from sellers"""
    STATUS_CHOICES = (
        ('pending_payment', _('Pending Payment')),
        ('payment_submitted', _('Payment Submitted')),
        ('under_review', _('Under Review')),
        ('approved', _('Approved')),
        ('active', _('Active')),
        ('completed', _('Completed')),
        ('rejected', _('Rejected')),
        ('cancelled', _('Cancelled')),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('instapay', _('Instapay')),
        ('vodafone_cash', _('Vodafone Cash')),
        ('visa', _('Visa/Mastercard')),
    )
    
    # Seller information
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ad_requests')
    
    # Ad details
    ad_type = models.ForeignKey(AdType, on_delete=models.CASCADE, verbose_name=_('Ad Type'))
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, 
                                verbose_name=_('Category'), help_text=_('Required for Category Slider ads'))
    duration = models.CharField(max_length=20, choices=AdPricing.DURATION_CHOICES, verbose_name=_('Duration'))
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Price (EGP)'))
    
    # Payment information
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, verbose_name=_('Payment Method'))
    sender_info = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('Sender Info'),
                                  help_text=_('Phone number or account ID used for payment'))
    payment_screenshot = models.ImageField(upload_to='ad_payments/', blank=True, null=True, 
                                         verbose_name=_('Payment Screenshot'))
    
    # Ad content (to be filled by seller or admin)
    ad_title = models.CharField(max_length=200, blank=True, null=True, verbose_name=_('Ad Title'))
    ad_description = models.TextField(blank=True, null=True, verbose_name=_('Ad Description'))
    ad_image = models.ImageField(upload_to='ad_content/', blank=True, null=True, verbose_name=_('Ad Image'))
    ad_link = models.URLField(blank=True, null=True, verbose_name=_('Ad Link'))
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='payment_submitted', verbose_name=_('Status'))
    admin_notes = models.TextField(blank=True, null=True, verbose_name=_('Admin Notes'))
    
    # Scheduling
    start_date = models.DateTimeField(null=True, blank=True, verbose_name=_('Start Date'))
    end_date = models.DateTimeField(null=True, blank=True, verbose_name=_('End Date'))
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Approved At'))
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Completed At'))
    
    class Meta:
        verbose_name = _('Ad Booking Request')
        verbose_name_plural = _('Ad Booking Requests')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.seller.email} - {self.ad_type.name_ar} - {self.get_status_display()}"
    
    @property
    def is_category_required(self):
        return self.ad_type.requires_category
    
    def can_be_approved(self):
        """Check if request can be approved"""
        return self.status in ['payment_submitted', 'under_review']
    
    def can_be_activated(self):
        """Check if request can be activated"""
        return self.status == 'approved'