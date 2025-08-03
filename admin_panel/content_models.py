# Content management models for admin panel
from django.db import models
from django.utils.translation import gettext_lazy as _

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