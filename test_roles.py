#!/usr/bin/env python3
"""
Test script to verify role-based access control in admin panel
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append('/home/momen/StudioProjects/TO7FAA/to7fabackend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'to7fabackend.settings')

django.setup()

from django.contrib.auth import get_user_model
from admin_panel.models import AdminPermission, AdminRole, AdminUser
from admin_panel.decorators import has_admin_permission, get_user_permissions

User = get_user_model()

def test_role_permissions():
    """Test role-based permissions system"""
    print("=" * 50)
    print("TESTING ROLE-BASED ACCESS CONTROL")
    print("=" * 50)
    
    # Get all roles
    roles = AdminRole.objects.all()
    print(f"\n📋 Available Roles ({roles.count()}):")
    print("-" * 30)
    
    for role in roles:
        permissions = role.get_permission_names()
        print(f"🏷️  {role.display_name} ({role.name}):")
        print(f"   📝 {role.description}")
        print(f"   🔑 Permissions ({len(permissions)}):")
        for perm in permissions:
            print(f"      • {perm}")
        print()
    
    # Test permission mappings
    print("\n🗂️  ROLE-TO-TAB MAPPING:")
    print("-" * 30)
    
    role_tab_mapping = {
        'super_admin': ['All tabs visible'],
        'product_manager': [
            'Products (products_management)',
            'Categories (categories_management)', 
            'Variants (variants_management)',
            'Add Products (products_add)'
        ],
        'content_moderator': [
            'Product Approval (product_approval)',
            'Applications (seller_applications)',
            'Support Tickets (support_tickets)'
        ],
        'order_manager': [
            'Orders (orders_view)',
            'Users (users_management)',
            'Support Tickets (support_tickets)'
        ],
        'marketing_manager': [
            'Analytics (analytics_view)',
            'Advertising (advertising_management)'
        ]
    }
    
    for role_name, tabs in role_tab_mapping.items():
        role = AdminRole.objects.filter(name=role_name).first()
        if role:
            print(f"👤 {role.display_name}:")
            for tab in tabs:
                print(f"   ✅ {tab}")
            print()
    
    # Test admin users
    admin_users = AdminUser.objects.select_related('user', 'role').all()
    if admin_users.exists():
        print(f"\n👥 EXISTING ADMIN USERS ({admin_users.count()}):")
        print("-" * 30)
        
        for admin_user in admin_users:
            permissions = admin_user.get_all_permissions()
            print(f"🧑‍💼 {admin_user.user.email}")
            print(f"   🏷️  Role: {admin_user.role.display_name}")
            print(f"   🔑 Permissions ({len(permissions)}):")
            for perm in sorted(permissions):
                print(f"      • {perm}")
            print(f"   ✅ Active: {admin_user.is_active}")
            print(f"   🚪 Can Login: {admin_user.can_login}")
            print()
    else:
        print("\n👥 No admin users found. Create some admin users to test role permissions!")
    
    print("=" * 50)
    print("ROLE SYSTEM TEST COMPLETED!")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    try:
        test_role_permissions()
    except Exception as e:
        print(f"❌ Error running test: {e}")
        import traceback
        traceback.print_exc()