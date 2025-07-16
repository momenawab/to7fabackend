#!/usr/bin/env python3

import os
import sys
import django

# Add the Backend directory to the path
sys.path.append('/home/momen/CurrentProjects/to7fa/Backend')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'to7fabackend.settings')
django.setup()

from custom_auth.models import User
from products.models import Category, Product
from decimal import Decimal

def create_test_data():
    print("🔄 Creating test data...")
    
    # Create or get an artist user
    artist_user, created = User.objects.get_or_create(
        email='artist@example.com',
        defaults={
            'first_name': 'Test',
            'last_name': 'Artist',
            'user_type': 'artist',
            'is_active': True
        }
    )
    
    if created:
        artist_user.set_password('testpass123')
        artist_user.save()
        print(f"✅ Created artist user: {artist_user.email}")
    else:
        print(f"✅ Artist user already exists: {artist_user.email}")
    
    # Create a category
    category, created = Category.objects.get_or_create(
        name='Test Category',
        defaults={
            'description': 'Test category for cart testing',
            'is_active': True
        }
    )
    
    if created:
        print(f"✅ Created category: {category.name}")
    else:
        print(f"✅ Category already exists: {category.name}")
    
    # Create some test products
    test_products = [
        {
            'name': 'Test Product 1',
            'description': 'First test product for cart API testing',
            'price': Decimal('29.99'),
            'stock': 10,
        },
        {
            'name': 'Test Product 2', 
            'description': 'Second test product for cart API testing',
            'price': Decimal('19.99'),
            'stock': 5,
        },
        {
            'name': 'Test Product 3',
            'description': 'Third test product for cart API testing',
            'price': Decimal('39.99'),
            'stock': 15,
        }
    ]
    
    for product_data in test_products:
        product, created = Product.objects.get_or_create(
            name=product_data['name'],
            defaults={
                'description': product_data['description'],
                'price': product_data['price'],
                'stock': product_data['stock'],
                'category': category,
                'seller': artist_user,
                'is_active': True,
                'is_featured': False
            }
        )
        
        if created:
            print(f"✅ Created product: {product.name} (ID: {product.id})")
        else:
            print(f"✅ Product already exists: {product.name} (ID: {product.id})")
    
    print("\n🎉 Test data creation complete!")
    print("\nAvailable products:")
    for product in Product.objects.filter(is_active=True):
        print(f"  - ID: {product.id}, Name: {product.name}, Stock: {product.stock}, Price: ${product.price}")

if __name__ == '__main__':
    create_test_data()