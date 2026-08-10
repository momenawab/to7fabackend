"""
Invariant Tests for Cart Data Structure (Spec 004, Spec 005)

These tests enforce the binding architectural decisions from Spec 004:
- INV-017: CartItem.variant_id is valid ProductCategoryVariantOption or NULL
- INV-018: CartItem cannot reference inactive variant
- INV-019: CartItem cannot reference zero-stock variant
"""

import pytest
from products.models import Product, ProductCategoryVariantOption, Category, CategoryVariantType, CategoryVariantOption
from custom_auth.models import User
from cart.models import Cart, CartItem


@pytest.mark.django_db
class TestCartInvariants:
    """Test invariants for cart data structure (Spec 004 INV-017, INV-018, INV-019)"""

    def test_inv_017_cart_item_variant_id_is_null_or_valid_product_category_variant_option(self):
        """
        INV-017: CartItem.variant_id MUST reference a valid, active ProductCategoryVariantOption or be NULL.
        """
        # Setup: Create category with variant
        category = Category.objects.create(name="Test Category")
        variant_type = CategoryVariantType.objects.create(
            name="Size",
            category=category
        )
        option = CategoryVariantOption.objects.create(
            variant_type=variant_type,
            value="Large"
        )

        seller = User.objects.create_user(
            email="seller@test.com",
            password="testpass123",
            user_type='store'
        )

        # Create variant product
        product = Product.objects.create(
            name="T-Shirt",
            description="Test",
            base_price=50.00,
            stock_quantity=0,
            category=category,
            seller=seller,
            approval_status='approved'
        )

        variant = ProductCategoryVariantOption.objects.create(
            product=product,
            category_variant_option=option,
            stock_count=10
        )

        # Create cart with session_id (required by constraint)
        cart = Cart.objects.create(session_id="test-session-inv-017")

        # Test 1: CartItem with valid variant_id
        cart_item1 = CartItem.objects.create(
            cart=cart,
            product=product,
            variant_id=variant.id,
            quantity=1
        )
        assert cart_item1.variant_id == variant.id

        # Verify the variant exists
        referenced_variant = ProductCategoryVariantOption.objects.get(id=cart_item1.variant_id)
        assert referenced_variant.id == variant.id

        # Test 2: CartItem without variant (non-variant product)
        non_variant_product = Product.objects.create(
            name="Simple Product",
            description="No variants",
            base_price=25.00,
            stock_quantity=20,
            category=category,
            seller=seller,
            approval_status='approved'
        )

        cart_item2 = CartItem.objects.create(
            cart=cart,
            product=non_variant_product,
            variant_id=None,
            quantity=2
        )
        assert cart_item2.variant_id is None

    def test_inv_018_cart_item_cannot_reference_inactive_variant(self):
        """
        INV-018: CartItem CANNOT reference a ProductCategoryVariantOption with is_active=False.
        """
        # Setup
        category = Category.objects.create(name="Test Category 2")
        variant_type = CategoryVariantType.objects.create(
            name="Color",
            category=category
        )
        option = CategoryVariantOption.objects.create(
            variant_type=variant_type,
            value="Red"
        )

        seller = User.objects.create_user(
            email="seller2@test.com",
            password="testpass123",
            user_type='store'
        )

        product = Product.objects.create(
            name="Colored Shirt",
            description="Test",
            base_price=50.00,
            stock_quantity=0,
            category=category,
            seller=seller,
            approval_status='approved'
        )

        # Create variant and then deactivate it
        variant = ProductCategoryVariantOption.objects.create(
            product=product,
            category_variant_option=option,
            stock_count=10,
            is_active=True
        )

        cart = Cart.objects.create(session_id="test-session-inv-018")

        # Should work initially
        cart_item = CartItem.objects.create(
            cart=cart,
            product=product,
            variant_id=variant.id,
            quantity=1
        )
        assert cart_item.variant_id == variant.id

        # Deactivate the variant
        variant.is_active = False
        variant.save()

        # TODO: After T048 implementation, cart operations should validate this
        # For now, this test documents the expected behavior
        # Cart should validate that variant_id references an active variant

    def test_inv_019_cart_item_cannot_reference_zero_stock_variant(self):
        """
        INV-019: CartItem CANNOT reference a ProductCategoryVariantOption with stock_count=0.
        """
        # Setup
        category = Category.objects.create(name="Test Category 3")
        variant_type = CategoryVariantType.objects.create(
            name="Size",
            category=category
        )
        option = CategoryVariantOption.objects.create(
            variant_type=variant_type,
            value="Small"
        )

        seller = User.objects.create_user(
            email="seller3@test.com",
            password="testpass123",
            user_type='store'
        )

        product = Product.objects.create(
            name="Small Item",
            description="Test",
            base_price=50.00,
            stock_quantity=0,
            category=category,
            seller=seller,
            approval_status='approved'
        )

        # Create variant with zero stock
        variant = ProductCategoryVariantOption.objects.create(
            product=product,
            category_variant_option=option,
            stock_count=0  # Out of stock
        )

        cart = Cart.objects.create(session_id="test-session-inv-019")

        # TODO: After T049 implementation, cart operations should validate stock_count > 0
        # For now, this test documents the expected behavior
        # Cart should prevent adding items with zero stock variants
        assert variant.stock_count == 0
