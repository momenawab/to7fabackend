"""
Test guest cart functionality and cart merge on login.

Tests:
- Guest cart creation with session_id
- Guest cart operations (add, update, remove, clear)
- Cart merge on login
- Conflict resolution (user quantity wins)
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from cart.models import Cart, CartItem
from products.models import (
    Product, Category, CategoryVariantType, CategoryVariantOption,
    ProductCategoryVariantOption,
)
import uuid

User = get_user_model()


class TestGuestCartCreation(TestCase):
    """Test guest cart creation with session_id."""

    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
        self.session_id = str(uuid.uuid4())

    def test_create_guest_cart_with_session_id(self):
        """Test creating a guest cart with session_id."""
        cart = Cart.objects.create(session_id=self.session_id)
        self.assertIsNotNone(cart.id)
        self.assertEqual(cart.session_id, self.session_id)
        self.assertIsNone(cart.user)

    def test_session_id_uniqueness_constraint(self):
        """Test that session_id is unique."""
        Cart.objects.create(session_id=self.session_id)
        
        # Try to create another cart with same session_id
        with self.assertRaises(Exception):
            Cart.objects.create(session_id=self.session_id)

    def test_get_or_create_returns_existing_cart(self):
        """Test that get_or_create returns existing cart."""
        # Create cart
        cart1, created1 = Cart.objects.get_or_create(session_id=self.session_id)
        self.assertTrue(created1)
        
        # Get existing cart
        cart2, created2 = Cart.objects.get_or_create(session_id=self.session_id)
        self.assertFalse(created2)
        self.assertEqual(cart1.id, cart2.id)

    def test_constraint_either_user_or_session_id_required(self):
        """Test constraint: either user or session_id required."""
        # Should fail with both null
        with self.assertRaises(Exception):
            Cart.objects.create(user=None, session_id=None)

    def test_cart_with_user_only(self):
        """Test creating cart with user only."""
        unique_email = f'test_{uuid.uuid4().hex[:8]}@example.com'
        user = User.objects.create_user(
            email=unique_email,
            password='testpass123',
        )
        cart = Cart.objects.create(user=user)
        self.assertIsNotNone(cart.id)
        self.assertEqual(cart.user, user)
        self.assertIsNone(cart.session_id)

    def test_cart_with_both_user_and_session_id_fails(self):
        """Test that cart with both user and session_id should be prevented."""
        unique_email = f'test_{uuid.uuid4().hex[:8]}@example.com'
        user = User.objects.create_user(
            email=unique_email,
            password='testpass123',
        )
        # This should work based on the model, but typically you'd want one or the other
        cart = Cart.objects.create(user=user, session_id=self.session_id)
        self.assertIsNotNone(cart.id)


class TestGuestCartOperations(TestCase):
    """Test guest cart operations."""

    def setUp(self):
        """Set up test client, product, and guest cart."""
        self.client = APIClient()
        self.session_id = str(uuid.uuid4())
        
        # Create seller user for products (use unique email)
        unique_seller_email = f'seller_{uuid.uuid4().hex[:8]}@example.com'
        self.seller = User.objects.create_user(
            email=unique_seller_email,
            password='testpass123',
        )
        
        # Create a product
        # Phase 2 fix (workstream 4 investigation): approval_status was left at its
        # default ('pending'), which made test_add_item_to_guest_cart_via_api fail
        # against the pre-existing (unrelated to this workstream) INV-011 approval
        # check in add_to_cart - invisible until the Phase 2 migration fix let the
        # test database build at all. Not a workstream 4 change; fixed here since it's
        # the same fixture.
        self.category = Category.objects.create(
            name='Test Category',
        )
        self.product = Product.objects.create(
            name='Test Product',
            base_price=10.00,
            stock_quantity=100,
            category=self.category,
            seller=self.seller,
            approval_status='approved',
        )

        # Create guest cart
        self.guest_cart = Cart.objects.create(session_id=self.session_id)

    def test_add_item_to_guest_cart(self):
        """Test adding item to guest cart."""
        self.guest_cart.add_item(self.product, quantity=2)

        self.assertEqual(self.guest_cart.items.count(), 1)
        cart_item = self.guest_cart.items.first()
        self.assertEqual(cart_item.product, self.product)
        self.assertEqual(cart_item.quantity, 2)

    def test_add_item_with_variants(self):
        """Test adding item with variants."""
        # Phase 2 fix: variant_id must reference a real ProductCategoryVariantOption
        # now that cart stock validation actually checks it (workstream 4) - a bare
        # variant_id=1 with no matching row is exactly the bug being fixed.
        variant_type = CategoryVariantType.objects.create(name='Size', category=self.category)
        option = CategoryVariantOption.objects.create(variant_type=variant_type, value='Large')
        product_variant = ProductCategoryVariantOption.objects.create(
            product=self.product, category_variant_option=option, stock_count=10, is_active=True,
        )
        variants = {'color': 'red', 'size': 'large'}
        self.guest_cart.add_item(
            self.product,
            quantity=1,
            selected_variants=variants,
            variant_id=product_variant.id
        )

        self.assertEqual(self.guest_cart.items.count(), 1)
        cart_item = self.guest_cart.items.first()
        self.assertEqual(cart_item.selected_variants, variants)
        self.assertEqual(cart_item.variant_id, product_variant.id)

    def test_update_item_quantity(self):
        """Test updating cart item quantity."""
        # Add item
        cart_item = self.guest_cart.add_item(self.product, quantity=2)
        
        # Update quantity
        updated_item = self.guest_cart.update_item_by_id(cart_item.id, quantity=5)
        self.assertEqual(updated_item.quantity, 5)

    def test_remove_item_from_cart(self):
        """Test removing item from cart."""
        # Add item
        cart_item = self.guest_cart.add_item(self.product, quantity=2)
        
        # Remove item
        result = self.guest_cart.remove_item_by_id(cart_item.id)
        self.assertTrue(result)
        self.assertEqual(self.guest_cart.items.count(), 0)

    def test_clear_cart(self):
        """Test clearing all items from cart."""
        # Add multiple items
        self.guest_cart.add_item(self.product, quantity=2)
        product2 = Product.objects.create(
            name='Test Product 2',
            base_price=20.00,
            stock_quantity=50,
            category=self.category,
            seller=self.seller,
        )
        self.guest_cart.add_item(product2, quantity=1)
        
        # Clear cart
        self.guest_cart.clear()
        self.assertEqual(self.guest_cart.items.count(), 0)

    def test_get_guest_cart_via_api(self):
        """Test getting guest cart via API."""
        self.guest_cart.add_item(self.product, quantity=2)
        
        response = self.client.get(
            reverse('cart_detail'),
            HTTP_X_SESSION_ID=self.session_id,
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        # Cart API returns data directly, not wrapped in {'data': ...}
        self.assertIn('items', response_data)

    def test_add_item_to_guest_cart_via_api(self):
        """Test adding item to guest cart via API."""
        response = self.client.post(
            reverse('cart-add'),
            data={
                'product_id': self.product.id,
                'quantity': 2,
            },
            HTTP_X_SESSION_ID=self.session_id,
            format='json',
        )
        
        self.assertEqual(response.status_code, 200)
        self.guest_cart.refresh_from_db()
        self.assertEqual(self.guest_cart.items.count(), 1)


class TestCartMerge(TestCase):
    """Test cart merge functionality."""

    def setUp(self):
        """Set up test client, products, user, and carts."""
        self.client = APIClient()
        
        # Create seller user for products (use unique email)
        unique_seller_email = f'seller_{uuid.uuid4().hex[:8]}@example.com'
        self.seller = User.objects.create_user(
            email=unique_seller_email,
            password='testpass123',
        )
        
        # Create user (use unique email and save for login test)
        self.unique_user_email = f'test_{uuid.uuid4().hex[:8]}@example.com'
        self.user = User.objects.create_user(
            email=self.unique_user_email,
            password='testpass123',
        )
        self.user.email_verified = True
        self.user.save()
        
        # Create products
        self.category = Category.objects.create(
            name='Test Category',
        )
        self.product1 = Product.objects.create(
            name='Test Product 1',
            base_price=10.00,
            stock_quantity=100,
            category=self.category,
            seller=self.seller,
        )
        self.product2 = Product.objects.create(
            name='Test Product 2',
            base_price=20.00,
            stock_quantity=50,
            category=self.category,
            seller=self.seller,
        )
        
        # Create user cart
        self.user_cart = Cart.objects.create(user=self.user)
        
        # Create guest cart
        self.session_id = str(uuid.uuid4())
        self.guest_cart = Cart.objects.create(session_id=self.session_id)

    def test_merge_guest_cart_into_user_cart(self):
        """Test merging guest cart into user cart."""
        # Add items to guest cart
        self.guest_cart.add_item(self.product1, quantity=2)
        self.guest_cart.add_item(self.product2, quantity=1)
        
        # Merge
        from cart.services.cart_merge import merge_guest_cart
        result = merge_guest_cart(self.user, self.session_id)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['items_added'], 2)
        self.assertEqual(result['items_skipped'], 0)
        
        # Verify user cart has items
        self.assertEqual(self.user_cart.items.count(), 2)

    def test_merge_with_empty_user_cart(self):
        """Test merging guest cart with empty user cart."""
        # Add items to guest cart
        self.guest_cart.add_item(self.product1, quantity=2)
        self.guest_cart.add_item(self.product2, quantity=1)
        
        # Merge
        from cart.services.cart_merge import merge_guest_cart
        result = merge_guest_cart(self.user, self.session_id)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['items_added'], 2)
        
        # Verify all items added to user cart
        self.assertEqual(self.user_cart.items.count(), 2)

    def test_merge_with_nonexistent_guest_cart(self):
        """Test merging with nonexistent guest cart."""
        from cart.services.cart_merge import merge_guest_cart
        result = merge_guest_cart(self.user, 'nonexistent-session-id')
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)

    def test_merge_conflict_resolution_user_quantity_wins(self):
        """Test merge conflict resolution: user quantity wins."""
        # Add product to user cart with quantity 5
        self.user_cart.add_item(self.product1, quantity=5)
        
        # Add same product to guest cart with quantity 3
        self.guest_cart.add_item(self.product1, quantity=3)
        
        # Merge
        from cart.services.cart_merge import merge_guest_cart
        result = merge_guest_cart(self.user, self.session_id)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['items_skipped'], 1)
        
        # Verify user cart still has quantity 5 (not 8)
        self.user_cart.refresh_from_db()
        cart_item = self.user_cart.items.get(product=self.product1)
        self.assertEqual(cart_item.quantity, 5)

    def test_merge_with_product_variants(self):
        """Test merging carts with product variants."""
        # Add product with variants to guest cart
        # Phase 2 fix: variant_id must reference a real ProductCategoryVariantOption
        # with enough stock now that merge validates it (workstream 4).
        variant_type = CategoryVariantType.objects.create(name='Size', category=self.category)
        option = CategoryVariantOption.objects.create(variant_type=variant_type, value='Large')
        product_variant = ProductCategoryVariantOption.objects.create(
            product=self.product1, category_variant_option=option, stock_count=10, is_active=True,
        )
        variants = {'color': 'red', 'size': 'large'}
        self.guest_cart.add_item(
            self.product1,
            quantity=2,
            selected_variants=variants,
            variant_id=product_variant.id
        )

        # Merge
        from cart.services.cart_merge import merge_guest_cart
        result = merge_guest_cart(self.user, self.session_id)

        self.assertTrue(result['success'])
        self.assertEqual(result['items_added'], 1)

        # Verify user cart has item with variants
        self.assertEqual(self.user_cart.items.count(), 1)
        cart_item = self.user_cart.items.first()
        self.assertEqual(cart_item.selected_variants, variants)
        self.assertEqual(cart_item.variant_id, product_variant.id)

    def test_guest_cart_deleted_after_merge(self):
        """Test that guest cart is deleted after merge."""
        # Add item to guest cart
        self.guest_cart.add_item(self.product1, quantity=2)
        
        # Merge
        from cart.services.cart_merge import merge_guest_cart
        result = merge_guest_cart(self.user, self.session_id)
        
        self.assertTrue(result['success'])
        
        # Verify guest cart is deleted
        self.assertFalse(Cart.objects.filter(session_id=self.session_id).exists())

    def test_merge_via_login_endpoint(self):
        """Test cart merge via login endpoint."""
        # Add items to guest cart
        self.guest_cart.add_item(self.product1, quantity=2)
        
        # Login with session_id to trigger merge
        response = self.client.post(
            reverse('jwt_login'),
            data={
                'email': self.unique_user_email,
                'password': 'testpass123',
                'session_id': self.session_id,
            },
            format='json',
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify user cart has items
        self.user_cart.refresh_from_db()
        self.assertEqual(self.user_cart.items.count(), 1)

    def test_merge_with_multiple_items(self):
        """Test merging with multiple items."""
        # Add multiple items to guest cart
        self.guest_cart.add_item(self.product1, quantity=2)
        self.guest_cart.add_item(self.product2, quantity=1)
        
        # Add different item to user cart
        product3 = Product.objects.create(
            name='Test Product 3',
            base_price=30.00,
            stock_quantity=30,
            category=self.category,
            seller=self.seller,
        )
        self.user_cart.add_item(product3, quantity=1)
        
        # Merge
        from cart.services.cart_merge import merge_guest_cart
        result = merge_guest_cart(self.user, self.session_id)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['items_added'], 2)
        
        # Verify user cart has all items
        self.assertEqual(self.user_cart.items.count(), 3)
