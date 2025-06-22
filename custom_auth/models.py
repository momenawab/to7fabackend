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
