#!/usr/bin/env python3
"""
🔍 TO7FA Backend Setup Verification Script
Run this script to verify your deployment is configured correctly.
"""

import os
import sys
import subprocess
import json
from datetime import datetime

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'to7fabackend.settings')

try:
    import django
    django.setup()
    from django.core.management import execute_from_command_line
    from django.db import connection
    from django.contrib.auth import get_user_model
    from support.models import ContactRequest
    from django.conf import settings
    DJANGO_AVAILABLE = True
except ImportError as e:
    print(f"❌ Django import error: {e}")
    DJANGO_AVAILABLE = False

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*50}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(50)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*50}{Colors.END}")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version >= (3, 8):
        print_success(f"Python version: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_error(f"Python version too old: {version.major}.{version.minor}.{version.micro}")
        print_error("Required: Python 3.8+")
        return False

def check_virtual_environment():
    """Check if running in virtual environment"""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print_success("Running in virtual environment")
        return True
    else:
        print_warning("Not running in virtual environment")
        return False

def check_dependencies():
    """Check if all required packages are installed"""
    required_packages = [
        'django', 'djangorestframework', 'mysqlclient', 
        'corsheaders', 'pillow', 'channels'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print_success(f"Package installed: {package}")
        except ImportError:
            missing_packages.append(package)
            print_error(f"Package missing: {package}")
    
    return len(missing_packages) == 0

def check_database_connection():
    """Check database connection"""
    if not DJANGO_AVAILABLE:
        print_error("Django not available for database check")
        return False
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result[0] == 1:
                print_success("Database connection successful")
                
                # Get database info
                cursor.execute("SELECT DATABASE(), USER(), VERSION()")
                db_info = cursor.fetchone()
                print_info(f"Database: {db_info[0]}")
                print_info(f"User: {db_info[1]}")
                print_info(f"MySQL Version: {db_info[2]}")
                return True
    except Exception as e:
        print_error(f"Database connection failed: {e}")
        return False

def check_migrations():
    """Check if migrations are applied"""
    if not DJANGO_AVAILABLE:
        print_error("Django not available for migration check")
        return False
    
    try:
        # Check if tables exist
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES LIKE 'django_migrations'")
            if cursor.fetchone():
                cursor.execute("SELECT COUNT(*) FROM django_migrations")
                migration_count = cursor.fetchone()[0]
                print_success(f"Migrations applied: {migration_count} migrations")
                
                # Check key tables
                key_tables = [
                    'auth_user', 'support_contactrequest', 
                    'products_product', 'orders_order'
                ]
                
                for table in key_tables:
                    cursor.execute(f"SHOW TABLES LIKE '{table}'")
                    if cursor.fetchone():
                        print_success(f"Table exists: {table}")
                    else:
                        print_error(f"Table missing: {table}")
                
                return True
            else:
                print_error("Django migrations table not found")
                return False
    except Exception as e:
        print_error(f"Migration check failed: {e}")
        return False

def check_admin_user():
    """Check if admin user exists"""
    if not DJANGO_AVAILABLE:
        print_error("Django not available for admin user check")
        return False
    
    try:
        User = get_user_model()
        admin_users = User.objects.filter(is_superuser=True).count()
        if admin_users > 0:
            print_success(f"Admin users found: {admin_users}")
            return True
        else:
            print_warning("No admin users found")
            print_info("Create one with: python manage.py createsuperuser")
            return False
    except Exception as e:
        print_error(f"Admin user check failed: {e}")
        return False

def check_api_endpoints():
    """Check if API endpoints are accessible"""
    try:
        import requests
    except ImportError:
        print_warning("Requests library not available for API testing")
        return False
    
    try:
        # Start a test server temporarily
        print_info("Testing API endpoints...")
        
        # Test contact creation endpoint (should require auth)
        response = requests.get('http://localhost:8000/api/support/contact/create/', timeout=5)
        if response.status_code in [200, 405, 401, 403]:  # Method not allowed or auth required
            print_success("Contact API endpoint accessible")
        else:
            print_error(f"Contact API endpoint error: {response.status_code}")
            
    except requests.exceptions.RequestException:
        print_warning("API endpoints not tested (server not running)")
        print_info("Start server with: python manage.py runserver")
        return False
    except Exception as e:
        print_error(f"API test error: {e}")
        return False

def check_settings():
    """Check Django settings"""
    if not DJANGO_AVAILABLE:
        print_error("Django not available for settings check")
        return False
    
    issues = []
    
    # Check SECRET_KEY
    if 'django-insecure-' in settings.SECRET_KEY:
        issues.append("Default SECRET_KEY detected - change it!")
    else:
        print_success("SECRET_KEY appears to be customized")
    
    # Check DEBUG setting
    if settings.DEBUG:
        print_warning("DEBUG=True (OK for development, change to False for production)")
    else:
        print_success("DEBUG=False (production ready)")
    
    # Check ALLOWED_HOSTS
    if not settings.ALLOWED_HOSTS or settings.ALLOWED_HOSTS == ['*']:
        issues.append("ALLOWED_HOSTS needs to be configured")
    else:
        print_success(f"ALLOWED_HOSTS configured: {settings.ALLOWED_HOSTS}")
    
    # Check database
    db_engine = settings.DATABASES['default']['ENGINE']
    if 'mysql' in db_engine:
        print_success("Database: MySQL configured")
    else:
        print_warning(f"Database: {db_engine} (expected MySQL)")
    
    return len(issues) == 0

def generate_test_data():
    """Generate test contact request"""
    if not DJANGO_AVAILABLE:
        return False
    
    try:
        # Create test contact
        contact = ContactRequest.objects.create(
            name="Test User",
            phone="01234567890",
            subject="Setup Verification Test",
            message="This is a test contact created during setup verification.",
            ip_address="127.0.0.1",
            user_agent="Setup Verification Script"
        )
        print_success(f"Test contact created: #{contact.contact_number}")
        
        # Show total contacts
        total_contacts = ContactRequest.objects.count()
        print_info(f"Total contacts in database: {total_contacts}")
        
        return True
    except Exception as e:
        print_error(f"Failed to create test contact: {e}")
        return False

def main():
    """Main verification function"""
    print_header("TO7FA Backend Setup Verification")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    checks = [
        ("Python Version", check_python_version),
        ("Virtual Environment", check_virtual_environment),
        ("Dependencies", check_dependencies),
        ("Database Connection", check_database_connection),
        ("Migrations", check_migrations),
        ("Admin User", check_admin_user),
        ("Django Settings", check_settings),
    ]
    
    print_header("Running Checks")
    results = {}
    
    for check_name, check_func in checks:
        print(f"\n{Colors.BOLD}Checking: {check_name}{Colors.END}")
        try:
            results[check_name] = check_func()
        except Exception as e:
            print_error(f"Check failed with error: {e}")
            results[check_name] = False
    
    print_header("Test Data Generation")
    results["Test Data"] = generate_test_data()
    
    print_header("Summary")
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for check_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name:.<30} {status}")
    
    print(f"\n{Colors.BOLD}Overall: {passed}/{total} checks passed{Colors.END}")
    
    if passed == total:
        print_success("🎉 All checks passed! Your TO7FA backend is ready.")
    elif passed >= total * 0.8:  # 80% or more
        print_warning("⚠️ Most checks passed, but some issues need attention.")
    else:
        print_error("❌ Multiple issues detected. Review the failed checks.")
    
    print_header("Next Steps")
    print("1. Fix any failed checks above")
    print("2. Start the server: python manage.py runserver 0.0.0.0:8000")
    print("3. Access admin panel: http://your-ip:8000/dashboard/")
    print("4. Test contact API: http://your-ip:8000/api/support/contact/create/")
    print("5. See DEPLOYMENT_GUIDE.md for production setup")

if __name__ == "__main__":
    main()