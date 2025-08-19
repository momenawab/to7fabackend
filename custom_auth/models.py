from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _

class CustomUserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    def _create_user(self, email, password=None, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom User model that uses email as the unique identifier instead of username."""
    USER_TYPE_CHOICES = (
        ('customer', 'Customer'),
        ('artist', 'Artist'),
        ('store', 'Store'),
    )
    
    username = None
    email = models.EmailField(_('email address'), unique=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='customer')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    # Blocking related fields
    blocked_at = models.DateTimeField(blank=True, null=True)
    blocked_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='blocked_users')
    block_reason = models.TextField(blank=True, null=True)
    unblocked_at = models.DateTimeField(blank=True, null=True)
    unblocked_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='unblocked_users')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email


class Customer(models.Model):
    """Customer profile model"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile')
    profile_picture = models.ImageField(upload_to='profile_pictures/customers/', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    preferences = models.JSONField(default=dict, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Customer: {self.user.email}"


class Artist(models.Model):
    """Artist profile model"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='artist_profile')
    profile_picture = models.ImageField(upload_to='profile_pictures/artists/', blank=True, null=True)
    specialty = models.CharField(max_length=100, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    social_media = models.JSONField(default=dict, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Artist: {self.user.email}"


class Store(models.Model):
    """Store profile model"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='store_profile')
    store_name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='profile_pictures/stores/', blank=True, null=True)
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    has_physical_store = models.BooleanField(default=False)
    physical_address = models.TextField(blank=True, null=True)
    social_media = models.JSONField(default=dict, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Store: {self.store_name} ({self.user.email})"


class SellerApplication(models.Model):
    """Model for seller applications (artists and stores)"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    SELLER_TYPE_CHOICES = [
        ('artist', 'Artist'),
        ('store', 'Store'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seller_applications')
    seller_type = models.CharField(max_length=10, choices=SELLER_TYPE_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    # Common fields
    business_name = models.CharField(max_length=100)
    description = models.TextField()
    phone_number = models.CharField(max_length=20)
    address = models.TextField(blank=True, null=True)  # User's address
    
    # Store-specific fields
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    has_physical_store = models.BooleanField(default=False)
    physical_address = models.TextField(blank=True, null=True)
    
    # Artist-specific fields
    specialty = models.CharField(max_length=100, blank=True, null=True)
    portfolio_link = models.URLField(blank=True, null=True)
    
    # Social media
    social_media = models.JSONField(default=dict, blank=True)
    
    # Categories and business details
    categories = models.JSONField(default=list, blank=True)  # List of category IDs
    subcategories = models.JSONField(default=list, blank=True)  # List of subcategory IDs
    shipping_costs = models.JSONField(default=dict, blank=True)  # Shipping costs per governorate
    
    # Terms and conditions
    terms_accepted = models.BooleanField(default=False)
    terms_accepted_at = models.DateTimeField(blank=True, null=True)
    
    # Documents
    business_license = models.FileField(upload_to='seller_applications/documents/', blank=True, null=True)
    id_document_front = models.FileField(upload_to='seller_applications/ids/', blank=True, null=True)
    id_document_back = models.FileField(upload_to='seller_applications/ids/', blank=True, null=True)
    portfolio_images = models.JSONField(default=list, blank=True)  # List of image URLs/paths
    
    # Admin actions
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_applications')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)
    admin_notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.seller_type.title()} Application: {self.business_name} ({self.user.email}) - {self.status}"
