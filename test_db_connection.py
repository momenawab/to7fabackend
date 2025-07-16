#!/usr/bin/env python
"""
Test script to verify PyMySQL configuration works
"""
import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'to7fabackend.settings')
django.setup()

def test_pymysql_import():
    """Test that PyMySQL can be imported and configured"""
    try:
        import pymysql
        pymysql.install_as_MySQLdb()
        print("✅ PyMySQL imported and configured successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import PyMySQL: {e}")
        return False

def test_django_db_connection():
    """Test Django database connection"""
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print(f"✅ Database connection successful: {result}")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_django_settings():
    """Test Django settings configuration"""
    try:
        from django.conf import settings
        print(f"✅ Django settings loaded")
        print(f"   Database ENGINE: {settings.DATABASES['default']['ENGINE']}")
        print(f"   Database NAME: {settings.DATABASES['default']['NAME']}")
        return True
    except Exception as e:
        print(f"❌ Django settings error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing PyMySQL and Django configuration...")
    print("=" * 50)
    
    success = True
    success &= test_pymysql_import()
    success &= test_django_settings()
    
    # Only test DB connection if we have a database configured
    if os.environ.get('DATABASE_URL') or 'localhost' in str(os.environ.get('DATABASE_HOST', '')):
        success &= test_django_db_connection()
    else:
        print("ℹ️  Skipping database connection test (no DATABASE_URL set)")
    
    print("=" * 50)
    if success:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed!")
    
    sys.exit(0 if success else 1) 