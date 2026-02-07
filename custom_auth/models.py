from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import secrets
import string

class CustomUserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    def _create_user(self, email, password=None, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)

        # Support both 'mobile' and 'phone_number' parameters
        # 'mobile' is the spec-preferred name, 'phone_number' is the db field
        if 'mobile' in extra_fields:
            extra_fields['phone_number'] = extra_fields.pop('mobile')

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
    
    # Email verification fields
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=64, blank=True, null=True)
    email_verification_token_expires = models.DateTimeField(blank=True, null=True)
    
    # Password reset fields
    password_reset_token = models.CharField(max_length=64, blank=True, null=True)
    password_reset_token_expires = models.DateTimeField(blank=True, null=True)
    
    # Failed login attempts (for rate limiting)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    last_failed_login = models.DateTimeField(blank=True, null=True)
    locked_until = models.DateTimeField(blank=True, null=True)
    
    # Mobile verification fields (T007)
    is_mobile_verified = models.BooleanField(default=False)
    mobile_verified_at = models.DateTimeField(blank=True, null=True)
    
    # Lock (BAN) fields (T008)
    is_locked = models.BooleanField(default=False)
    locked_at = models.DateTimeField(blank=True, null=True)
    locked_reason = models.TextField(blank=True, null=True)
    locked_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='locked_users')
    
    # Block (business restriction) fields (T009)
    is_blocked = models.BooleanField(default=False)
    blocked_capabilities = models.JSONField(default=list, blank=True)
    blocked_reason = models.TextField(blank=True, null=True)
    
    # OTP verification fields (T010)
    otp_failed_attempts = models.PositiveIntegerField(default=0)
    otp_blocked_at = models.DateTimeField(blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        """
        Override save to reset mobile verification when phone number changes.
        """
        # Check if this is an update and phone_number is changing
        if self.pk is not None:
            try:
                old_user = User.objects.get(pk=self.pk)
                if old_user.phone_number != self.phone_number:
                    # Phone number changed, reset verification
                    self.is_mobile_verified = False
                    self.mobile_verified_at = None
                    self.otp_failed_attempts = 0
                    self.otp_blocked_at = None
            except User.DoesNotExist:
                # New user, no reset needed
                pass

        super().save(*args, **kwargs)


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
    profile_picture = models.ImageField(upload_to='profile_pictures/artists/', blank=True, null=True, help_text="Profile picture (required for new artists)")
    specialty = models.CharField(max_length=100, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    social_media = models.JSONField(default=dict, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    is_featured_on_homepage = models.BooleanField(default=False, help_text="Show this artist in 'اشطر فنانين' section")
    homepage_priority = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first (0 = highest priority)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Artist: {self.user.email}"


class Store(models.Model):
    """Store profile model"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='store_profile')
    store_name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='profile_pictures/stores/', blank=True, null=True, help_text="Store logo (required for new stores)")
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    has_physical_store = models.BooleanField(default=False)
    physical_address = models.TextField(blank=True, null=True)
    social_media = models.JSONField(default=dict, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    is_featured_on_homepage = models.BooleanField(default=False, help_text="Show this store in 'المتاجر الأكثر مبيعاً' section")
    homepage_priority = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first (0 = highest priority)")
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
    
    # Documents and Images
    profile_picture = models.ImageField(upload_to='seller_applications/profiles/', blank=True, null=True, help_text="Profile picture for artists/stores (required for new applications)")
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
    
    def save(self, *args, **kwargs):
        """
        Override save to update user block status based on application status.
        - Pending: Block SELL capability
        - Approved: Unblock user and set user_type
        - Rejected: Block SELL capability
        """
        # Check if this is an update and status is changing
        if self.pk is not None:
            try:
                old_application = SellerApplication.objects.get(pk=self.pk)
                old_status = old_application.status
                new_status = self.status

                # Update user based on status change
                if old_status != new_status:
                    if new_status == 'approved':
                        # Approved: Unblock user and set user_type
                        self.user.is_blocked = False
                        self.user.blocked_capabilities = []
                        self.user.blocked_reason = None
                        self.user.user_type = self.seller_type
                        self.user.save(update_fields=['is_blocked', 'blocked_capabilities', 'blocked_reason', 'user_type'])
                    elif new_status == 'pending':
                        # Pending: Block SELL capability
                        self.user.is_blocked = True
                        self.user.blocked_capabilities = ['SELL']
                        self.user.blocked_reason = 'Seller application pending approval'
                        self.user.save(update_fields=['is_blocked', 'blocked_capabilities', 'blocked_reason'])
                    elif new_status == 'rejected':
                        # Rejected: Block SELL capability
                        self.user.is_blocked = True
                        self.user.blocked_capabilities = ['SELL']
                        self.user.blocked_reason = self.rejection_reason or 'Seller application rejected'
                        self.user.save(update_fields=['is_blocked', 'blocked_capabilities', 'blocked_reason'])
            except SellerApplication.DoesNotExist:
                # New application, set initial block status
                if self.status == 'pending':
                    self.user.is_blocked = True
                    self.user.blocked_capabilities = ['SELL']
                    self.user.blocked_reason = 'Seller application pending approval'
                    self.user.save(update_fields=['is_blocked', 'blocked_capabilities', 'blocked_reason'])
        else:
            # New application, set initial block status
            if self.status == 'pending':
                self.user.is_blocked = True
                self.user.blocked_capabilities = ['SELL']
                self.user.blocked_reason = 'Seller application pending approval'
                self.user.save(update_fields=['is_blocked', 'blocked_capabilities', 'blocked_reason'])

        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.seller_type.title()} Application: {self.business_name} ({self.user.email}) - {self.status}"


class OTPVerification(models.Model):
    """Model for tracking OTP verification requests"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otp_verifications')
    mobile_number = models.CharField(max_length=20)
    otp_hash = models.CharField(max_length=128)  # PBKDF2 hash of OTP
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    attempt_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'used']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"OTP for {self.mobile_number} - {'Used' if self.used else 'Active'}"
