#!/usr/bin/env python3

import os
import sys
import django

# Add the parent directory to the path so we can import Django settings
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'to7fabackend.settings')
django.setup()

from admin_panel.models import AdminRole, AdminPermission

def create_permissions():
    """Create all admin permissions"""
    permissions_data = [
        ('products_management', 'Products Management', 'Full access to manage products including add, edit, delete'),
        ('products_add', 'Add Products', 'Can add new products to the system'),
        ('product_approval', 'Product Approval', 'Can approve or reject product submissions'),
        ('categories_management', 'Categories Management', 'Manage product categories and variants'),
        ('variants_management', 'Variants Management', 'Manage category variants and variant types'),
        ('orders_view', 'Orders View', 'View and manage customer orders'),
        ('advertising_management', 'Advertising Management', 'Manage advertisements and promotional content'),
        ('support_tickets', 'Support Tickets', 'Handle customer support tickets and inquiries'),
        ('seller_applications', 'Seller Applications', 'Review and approve seller applications'),
        ('users_management', 'Users Management', 'Manage regular users and sellers'),
        ('admin_management', 'Admin Management', 'Manage admin users, roles and permissions'),
        ('analytics_view', 'Analytics View', 'View system analytics and reports'),
    ]
    
    created_permissions = []
    for name, display_name, description in permissions_data:
        permission, created = AdminPermission.objects.get_or_create(
            name=name,
            defaults={
                'display_name': display_name,
                'description': description
            }
        )
        created_permissions.append(permission)
        print(f"{'Created' if created else 'Updated'} permission: {display_name}")
    
    return created_permissions

def create_roles(permissions):
    """Create admin roles with appropriate permissions"""
    
    # Create Super Admin role (all permissions)
    super_admin_role, created = AdminRole.objects.get_or_create(
        name='super_admin',
        defaults={
            'display_name': 'Super Administrator',
            'description': 'Full system access with all permissions'
        }
    )
    if created:
        super_admin_role.permissions.set(permissions)
    print(f"{'Created' if created else 'Updated'} role: Super Administrator")
    
    # Create Content Manager role
    content_permissions = [p for p in permissions if p.name in [
        'products_management', 'products_add', 'product_approval', 
        'categories_management', 'variants_management', 'analytics_view'
    ]]
    content_manager_role, created = AdminRole.objects.get_or_create(
        name='content_manager',
        defaults={
            'display_name': 'Content Manager',
            'description': 'Manages products, categories, and content approval'
        }
    )
    if created:
        content_manager_role.permissions.set(content_permissions)
    print(f"{'Created' if created else 'Updated'} role: Content Manager")
    
    # Create Support Manager role
    support_permissions = [p for p in permissions if p.name in [
        'support_tickets', 'orders_view', 'users_management', 'analytics_view'
    ]]
    support_manager_role, created = AdminRole.objects.get_or_create(
        name='support_manager',
        defaults={
            'display_name': 'Support Manager',
            'description': 'Handles customer support and user management'
        }
    )
    if created:
        support_manager_role.permissions.set(support_permissions)
    print(f"{'Created' if created else 'Updated'} role: Support Manager")
    
    # Create Sales Manager role
    sales_permissions = [p for p in permissions if p.name in [
        'seller_applications', 'orders_view', 'advertising_management', 'analytics_view'
    ]]
    sales_manager_role, created = AdminRole.objects.get_or_create(
        name='sales_manager',
        defaults={
            'display_name': 'Sales Manager',
            'description': 'Manages sellers, orders, and advertising'
        }
    )
    if created:
        sales_manager_role.permissions.set(sales_permissions)
    print(f"{'Created' if created else 'Updated'} role: Sales Manager")
    
    # Create Moderator role (limited permissions)
    moderator_permissions = [p for p in permissions if p.name in [
        'product_approval', 'support_tickets', 'orders_view'
    ]]
    moderator_role, created = AdminRole.objects.get_or_create(
        name='moderator',
        defaults={
            'display_name': 'Moderator',
            'description': 'Limited access for content moderation and support'
        }
    )
    if created:
        moderator_role.permissions.set(moderator_permissions)
    print(f"{'Created' if created else 'Updated'} role: Moderator")

def main():
    print("Setting up admin system...")
    
    # Create permissions
    print("\n=== Creating Permissions ===")
    permissions = create_permissions()
    
    # Create roles
    print("\n=== Creating Roles ===")
    create_roles(permissions)
    
    print("\n=== Setup Complete ===")
    print(f"Created {len(permissions)} permissions")
    print(f"Created {AdminRole.objects.count()} roles")
    
    print("\nAvailable roles and their capabilities:")
    for role in AdminRole.objects.all().order_by('display_name'):
        print(f"\n{role.display_name}:")
        print(f"  Description: {role.description}")
        print("  Permissions:")
        for perm in role.permissions.all():
            print(f"    - {perm.display_name}")

if __name__ == '__main__':
    main()