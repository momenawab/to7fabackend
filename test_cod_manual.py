#!/usr/bin/env python
"""
Simple test to verify COD order creation works.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'to7fabackend.settings')
os.environ.setdefault('ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver')
django.setup()

from orders.atomic_order_system import AtomicOrderCreator
from django.contrib.auth import get_user_model

User = get_user_model()

# Create a test user
from django.db import transaction
with transaction.atomic():
    user = User.objects.create_user(
        email='test_cod_user@example.com',
        password='testpass123',
        user_type='customer'
    )
    
    # Create a test product
    from products.models import Product
    from decimal import Decimal
    
    seller = User.objects.create_user(
        email=f'seller_test@example.com',
        password='testpass123',
        user_type='artist'
    )
    
    product = Product.objects.create(
        seller=seller,
        name='Test Product for COD',
        description='A test product for COD orders',
        base_price=Decimal('100.00'),
        stock_quantity=50,
        is_active=True
    )
    
    # Test COD order creation
    print("Creating COD order...")
    items_data = [
        {
            'product_id': product.id,
            'quantity': 1,
        }
    ]
    
    success, order, error = AtomicOrderCreator.create_order(
        user=user,
        items_data=items_data,
        shipping_address="123 Test St, Cairo, Egypt",
        shipping_cost=Decimal('10.00'),
        payment_method='cod',
        idempotency_key='test_cod_manual_001',
        use_wallet_payment=False
    )
    
    if success:
        print(f"✓ COD order created successfully!")
        print(f"  Order ID: {order.id}")
        print(f"  Status: {order.status}")
        print(f" Payment Method: {order.payment_method}")
        print(f" Payment Timeout: {order.payment_timeout_at}")
        print(f" Payment Status: {order.payment_status}")
    else:
        print(f"✗ Failed to create COD order: {error}")
        sys.exit(1)
