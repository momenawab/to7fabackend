from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator

class UserAddress(models.Model):
    """Model for user delivery addresses"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='addresses')
    name = models.CharField(max_length=100, help_text="Address nickname (e.g., Home, Work)")
    recipient_name = models.CharField(max_length=100)
    street = models.CharField(max_length=200)
    building = models.CharField(max_length=20)
    apartment = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    phone_number = models.CharField(
        max_length=15,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )]
    )
    # Location coordinates (supports worldwide coordinates with 8 decimal precision)
    latitude = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True, help_text="Latitude coordinate")
    longitude = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True, help_text="Longitude coordinate")
    location_notes = models.TextField(blank=True, null=True, help_text="Additional location notes from user")
    
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Address"
        verbose_name_plural = "User Addresses"
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.user.email}"
    
    @property
    def full_address(self):
        """Get formatted full address"""
        postal_part = f"، {self.postal_code}" if self.postal_code else ""
        return f"{self.street}، مبنى {self.building}، شقة {self.apartment}، {self.city}، {self.region}{postal_part}"
    
    def save(self, *args, **kwargs):
        # If this address is being set as default, remove default from other user addresses
        if self.is_default:
            UserAddress.objects.filter(user=self.user, is_default=True).update(is_default=False)
        
        # If this is the user's first address, make it default
        if not self.pk and not UserAddress.objects.filter(user=self.user).exists():
            self.is_default = True
            
        super().save(*args, **kwargs)