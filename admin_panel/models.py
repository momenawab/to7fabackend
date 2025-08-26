from django.db import models
from django.utils.translation import gettext_lazy as _
from custom_auth.models import User

class AdminActivity(models.Model):
    """Model to track admin activities in the admin panel"""
    ACTION_CHOICES = (
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('other', 'Other'),
    )
    
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_activities')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Admin Activity'
        verbose_name_plural = 'Admin Activities'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.admin.email} - {self.action} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

class AdminNotification(models.Model):
    """Model for admin notifications"""
    TYPE_CHOICES = (
        ('new_application', 'New Seller Application'),
        ('system', 'System Notification'),
        ('report', 'User Report'),
        ('other', 'Other'),
    )
    
    title = models.CharField(max_length=100)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    is_read = models.BooleanField(default=False)
    link = models.CharField(max_length=255, blank=True, null=True)  # Link to relevant page
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.notification_type}: {self.title}"


class AdminPermission(models.Model):
    """Model for defining specific admin permissions"""
    PERMISSION_CHOICES = (
        ('products_management', 'Products Management'),
        ('products_add', 'Add Products'),
        ('product_approval', 'Product Approval'),
        ('categories_management', 'Categories Management'),
        ('variants_management', 'Variants Management'),
        ('orders_view', 'Orders View'),
        ('advertising_management', 'Advertising Management'),
        ('support_tickets', 'Support Tickets'),
        ('seller_applications', 'Seller Applications'),
        ('users_management', 'Users Management'),
        ('admin_management', 'Admin Management'),
        ('analytics_view', 'Analytics View'),
    )
    
    name = models.CharField(max_length=50, choices=PERMISSION_CHOICES, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Admin Permission'
        verbose_name_plural = 'Admin Permissions'
        ordering = ['display_name']
    
    def __str__(self):
        return self.display_name


class AdminRole(models.Model):
    """Model for admin roles with specific permissions"""
    name = models.CharField(max_length=50, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(AdminPermission, related_name='roles')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_roles')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Admin Role'
        verbose_name_plural = 'Admin Roles'
        ordering = ['display_name']
    
    def __str__(self):
        return self.display_name
    
    def get_permission_names(self):
        """Get list of permission names for this role"""
        return list(self.permissions.values_list('name', flat=True))


class AdminUser(models.Model):
    """Model for admin users with roles and permissions"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    role = models.ForeignKey(AdminRole, on_delete=models.CASCADE, related_name='admin_users')
    additional_permissions = models.ManyToManyField(
        AdminPermission, 
        blank=True, 
        related_name='additional_users',
        help_text="Additional permissions beyond the role"
    )
    is_active = models.BooleanField(default=True)
    can_login = models.BooleanField(default=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_admins')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Admin User'
        verbose_name_plural = 'Admin Users'
        ordering = ['user__email']
    
    def __str__(self):
        return f"{self.user.email} ({self.role.display_name})"
    
    def get_all_permissions(self):
        """Get all permissions for this admin user (role + additional)"""
        role_permissions = set(self.role.get_permission_names())
        additional_permissions = set(self.additional_permissions.values_list('name', flat=True))
        return role_permissions.union(additional_permissions)
    
    def has_permission(self, permission_name):
        """Check if admin user has a specific permission"""
        return permission_name in self.get_all_permissions()
    
    def is_super_admin(self):
        """Check if this is a super admin with all permissions"""
        return self.role.name == 'super_admin' or self.has_permission('admin_management')
