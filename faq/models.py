from django.db import models
from django.utils.translation import gettext_lazy as _

class FAQCategory(models.Model):
    """FAQ Categories for organizing questions"""
    name = models.CharField(max_length=100, verbose_name=_('Category Name'))
    description = models.TextField(blank=True, null=True, verbose_name=_('Description'))
    icon = models.CharField(max_length=50, blank=True, null=True, help_text="Icon name (e.g., 'help', 'account', 'payment')")
    order = models.PositiveIntegerField(default=0, verbose_name=_('Display Order'))
    is_active = models.BooleanField(default=True, verbose_name=_('Is Active'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('FAQ Category')
        verbose_name_plural = _('FAQ Categories')
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    @property
    def faq_count(self):
        """Get count of active FAQs in this category"""
        return self.faqs.filter(is_active=True).count()


class FAQ(models.Model):
    """Frequently Asked Questions"""
    category = models.ForeignKey(
        FAQCategory, 
        on_delete=models.CASCADE, 
        related_name='faqs',
        verbose_name=_('Category')
    )
    question = models.TextField(verbose_name=_('Question'))
    answer = models.TextField(verbose_name=_('Answer'))
    
    # For different user types
    USER_TYPES = [
        ('all', _('All Users')),
        ('customer', _('Customers')),
        ('seller', _('Sellers')),
        ('artist', _('Artists')),
    ]
    target_audience = models.CharField(
        max_length=20, 
        choices=USER_TYPES, 
        default='all',
        verbose_name=_('Target Audience')
    )
    
    # SEO and search
    keywords = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        help_text=_('Keywords for search (comma separated)')
    )
    
    order = models.PositiveIntegerField(default=0, verbose_name=_('Display Order'))
    is_active = models.BooleanField(default=True, verbose_name=_('Is Active'))
    view_count = models.PositiveIntegerField(default=0, verbose_name=_('View Count'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('FAQ')
        verbose_name_plural = _('FAQs')
        ordering = ['category__order', 'order', '-created_at']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['target_audience', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.category.name} - {self.question[:50]}..."
    
    def increment_view_count(self):
        """Increment view count when FAQ is viewed"""
        self.view_count += 1
        self.save(update_fields=['view_count'])


class FAQFeedback(models.Model):
    """User feedback on FAQ helpfulness"""
    faq = models.ForeignKey(FAQ, on_delete=models.CASCADE, related_name='feedback')
    user = models.ForeignKey('custom_auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    is_helpful = models.BooleanField(verbose_name=_('Is Helpful'))
    comment = models.TextField(blank=True, null=True, verbose_name=_('Additional Comment'))
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('FAQ Feedback')
        verbose_name_plural = _('FAQ Feedback')
        unique_together = ['faq', 'user']  # One feedback per user per FAQ
    
    def __str__(self):
        helpful = "👍" if self.is_helpful else "👎"
        return f"{helpful} {self.faq.question[:30]}... - {self.user}"