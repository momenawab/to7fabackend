#!/usr/bin/env python
"""
Script to create initial categories for the To7fa backend.
Run this script to populate the database with default categories.
"""

import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'to7fabackend.settings')
django.setup()

from products.models import Category

def create_categories():
    """Create initial categories if they don't exist"""
    
    # Define the categories to create
    categories = [
        {
            'name': 'Art & Collectibles',
            'description': 'Handmade artwork and unique collectible items',
            'is_active': True
        },
        {
            'name': 'Home & Living',
            'description': 'Handmade items for your home and living spaces',
            'is_active': True
        },
        {
            'name': 'Jewelry & Accessories',
            'description': 'Handmade jewelry and fashion accessories',
            'is_active': True
        },
        {
            'name': 'Clothing & Shoes',
            'description': 'Handmade and custom clothing and footwear',
            'is_active': True
        },
        {
            'name': 'Toys & Entertainment',
            'description': 'Handmade toys, games, and entertainment items',
            'is_active': True
        },
        {
            'name': 'Paper & Party Supplies',
            'description': 'Handmade stationery, cards, and party decorations',
            'is_active': True
        }
    ]
    
    # Create each category if it doesn't exist
    created_count = 0
    for category_data in categories:
        category, created = Category.objects.get_or_create(
            name=category_data['name'],
            defaults=category_data
        )
        if created:
            print(f"Created category: {category.name}")
            created_count += 1
        else:
            print(f"Category already exists: {category.name}")
    
    # Create subcategories for Art & Collectibles
    if Category.objects.filter(name='Art & Collectibles').exists():
        parent = Category.objects.get(name='Art & Collectibles')
        subcategories = [
            {
                'name': 'Paintings',
                'description': 'Original paintings and artwork',
                'parent': parent,
                'is_active': True
            },
            {
                'name': 'Sculptures',
                'description': 'Handmade sculptures and 3D artwork',
                'parent': parent,
                'is_active': True
            },
            {
                'name': 'Photography',
                'description': 'Fine art photography prints',
                'parent': parent,
                'is_active': True
            }
        ]
        
        for subcategory_data in subcategories:
            subcategory, created = Category.objects.get_or_create(
                name=subcategory_data['name'],
                defaults=subcategory_data
            )
            if created:
                print(f"Created subcategory: {subcategory.name}")
                created_count += 1
            else:
                print(f"Subcategory already exists: {subcategory.name}")
    
    print(f"\nCreated {created_count} new categories/subcategories")
    print(f"Total categories in database: {Category.objects.count()}")

if __name__ == "__main__":
    print("Creating initial categories...")
    create_categories()
    print("Done!") 