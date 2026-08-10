"""
Invariant Tests for Product Variant System (Spec 004, Spec 005)

These tests enforce the binding architectural decisions from Spec 004:
- INV-014: Only ProductCategoryVariantOption can own stock
- INV-015: New products use ProductCategoryVariantOption
- INV-016: combination_stocks not used for stock
- INV-010: Unapproved products not in public listings
- INV-011: Unapproved products cannot be added to cart
- INV-012: Unapproved products cannot be in orders
- INV-013: Approval requires is_active=True
"""

import pytest
from django.core.exceptions import ValidationError
from products.models import Product, ProductCategoryVariantOption, ProductVariant, Category, CategoryVariantType, CategoryVariantOption
from custom_auth.models import User


@pytest.mark.django_db
class TestVariantSystemInvariants:
    """Test invariants for variant system canonicalization (Spec 004 C.1, C.2, C.6)"""

    def test_inv_014_only_product_category_variant_option_owns_stock(self):
        """
        INV-014: ProductCategoryVariantOption is the ONLY variant system that can own stock.
        ProductVariant.stock_count is deprecated and should not be used for new operations.
        """
        # Setup: Create category with variant type
        category = Category.objects.create(name="Test Category")
        variant_type = CategoryVariantType.objects.create(
            name="Size",
            category=category,
            priority=1
        )
        variant_option = CategoryVariantOption.objects.create(
            variant_type=variant_type,
            value="Large",
            extra_price=0
        )

        # Create seller
        seller = User.objects.create_user(
            email="seller122@test.com",
            password="testpass123",
            user_type='store'
        )

        # Create product
        product = Product.objects.create(
            name="Test Product",
            description="Test description",
            base_price=100.00,
            stock_quantity=0,
            category=category,
            seller=seller,
            approval_status='approved'
        )

        # Create ProductCategoryVariantOption with stock
        variant = ProductCategoryVariantOption.objects.create(
            product=product,
            category_variant_option=variant_option,
            stock_count=50,
            is_active=True
        )

        # Assert: ProductCategoryVariantOption owns stock
        assert variant.stock_count == 50
        assert variant.is_in_stock is True

        # Create ProductVariant (deprecated) - should have separate stock
        deprecated_variant = ProductVariant.objects.create(
            product=product,
            stock_count=30,
            is_active=True
        )

        # Assert: ProductVariant stock is independent and deprecated
        assert deprecated_variant.stock_count == 30

        # The canonical stock for variant products should come from ProductCategoryVariantOption
        # This test documents that both systems exist but ProductCategoryVariantOption is canonical
        assert ProductCategoryVariantOption.objects.filter(product=product).count() == 1

    def test_inv_015_new_products_use_product_category_variant_option(self):
        """
        INV-015: New product creation MUST use ProductCategoryVariantOption for variant configuration.
        """
        # Setup: Create category with variant types
        category = Category.objects.create(name="Test Category 2")
        size_type = CategoryVariantType.objects.create(
            name="Size",
            category=category,
            priority=1
        )
        color_type = CategoryVariantType.objects.create(
            name="Color",
            category=category,
            priority=2
        )

        large_option = CategoryVariantOption.objects.create(
            variant_type=size_type,
            value="Large",
            extra_price=0
        )
        red_option = CategoryVariantOption.objects.create(
            variant_type=color_type,
            value="Red",
            extra_price=5.00
        )

        seller = User.objects.create_user(
            email="seller2@test.com",
            password="testpass123",
            user_type='store'
        )

        # Create product with variants using canonical system
        product = Product.objects.create(
            name="T-Shirt",
            description="A nice t-shirt",
            base_price=50.00,
            stock_quantity=0,
            category=category,
            seller=seller,
            approval_status='approved'
        )

        # Add variants using ProductCategoryVariantOption (canonical)
        large_red_variant = ProductCategoryVariantOption.objects.create(
            product=product,
            category_variant_option=large_option,
            stock_count=100,
            price_adjustment=0
        )

        # Assert: Variants are properly configured
        assert large_red_variant.product == product
        assert large_red_variant.category_variant_option == large_option
        assert large_red_variant.stock_count == 100
        assert product.has_variants is True

    def test_inv_016_combination_stocks_not_used_for_stock(self):
        """
        INV-016: combination_stocks JSONField MUST NOT be used for any stock operations.
        Stock calculations should use ProductCategoryVariantOption.stock_count only.
        """
        # Setup
        category = Category.objects.create(name="Test Category 3")
        variant_type = CategoryVariantType.objects.create(
            name="Size",
            category=category,
            priority=1
        )
        option_l = CategoryVariantOption.objects.create(
            variant_type=variant_type,
            value="L",
            extra_price=0
        )

        seller = User.objects.create_user(
            email="seller123@test.com",
            password="testpass123",
            user_type='store'
        )

        # Create product with combination_stocks populated (deprecated)
        product = Product.objects.create(
            name="Product with Old Combination Stocks",
            description="Test",
            base_price=100.00,
            stock_quantity=0,
            category=category,
            seller=seller,
            approval_status='approved',
            combination_stocks={'29_27': 10}  # Deprecated format
        )

        # Create canonical variant
        variant = ProductCategoryVariantOption.objects.create(
            product=product,
            category_variant_option=option_l,
            stock_count=25
        )

        # The stock property should return sum of ProductCategoryVariantOption.stock_count
        # NOT the combination_stocks value
        # Note: This test documents current behavior; implementation will change to ignore combination_stocks
        assert variant.stock_count == 25

        # TODO: After T019 implementation, product.stock should ignore combination_stocks
        # For now, this test documents the state that needs to change


@pytest.mark.django_db
class TestVisibilityInvariants:
    """Test invariants for product visibility and approval enforcement (Spec 004 C.4)"""

    def test_inv_010_unapproved_products_not_in_public_listings(self):
        """
        INV-010: A product with approval_status != 'approved' CANNOT appear in public product listings.
        """
        # Setup
        category = Category.objects.create(name="Test Category 4")
        seller = User.objects.create_user(
            email="seller4@test.com",
            password="testpass123",
            user_type='store'
        )

        # Create products with different approval statuses
        pending_product = Product.objects.create(
            name="Pending Product",
            description="Waiting approval",
            base_price=50.00,
            category=category,
            seller=seller,
            approval_status='pending',
            is_active=True
        )

        rejected_product = Product.objects.create(
            name="Rejected Product",
            description="Rejected product",
            base_price=50.00,
            category=category,
            seller=seller,
            approval_status='rejected',
            is_active=True
        )

        approved_product = Product.objects.create(
            name="Approved Product",
            description="Approved product",
            base_price=50.00,
            category=category,
            seller=seller,
            approval_status='approved',
            is_active=True
        )

        # TODO: After T036-T039 implementation, Product.objects.approved() should exist
        # For now, document the expectation
        # approved_products = Product.objects.approved()
        # assert pending_product not in approved_products
        # assert rejected_product not in approved_products
        # assert approved_product in approved_products

    def test_inv_011_unapproved_products_cannot_be_added_to_cart(self):
        """
        INV-011: A product with approval_status != 'approved' CANNOT be added to cart.
        """
        # Setup
        category = Category.objects.create(name="Test Category 5")
        seller = User.objects.create_user(
            email="seller5@test.com",
            password="testpass123",
            user_type='store'
        )

        unapproved_product = Product.objects.create(
            name="Unapproved Product",
            description="Should not be in cart",
            base_price=50.00,
            category=category,
            seller=seller,
            approval_status='pending',
            is_active=True
        )

        # TODO: After T040 implementation, cart operations should validate approval_status
        # This test will verify that adding unapproved products to cart raises an error
        pass

    def test_inv_012_unapproved_products_cannot_be_in_orders(self):
        """
        INV-012: A product with approval_status != 'approved' CANNOT be included in an order.
        """
        # Setup
        category = Category.objects.create(name="Test Category 6")
        seller = User.objects.create_user(
            email="seller6@test.com",
            password="testpass123",
            user_type='store'
        )
        buyer = User.objects.create_user(
            email="buyer@test.com",
            password="testpass123",
            user_type='customer'
        )

        unapproved_product = Product.objects.create(
            name="Unapproved Product",
            description="Should not be ordered",
            base_price=50.00,
            category=category,
            seller=seller,
            approval_status='rejected',
            is_active=True
        )

        # TODO: After T041 implementation, order creation should validate approval_status
        # This test will verify that orders with unapproved products fail
        pass

    def test_inv_013_approval_requires_is_active_true(self):
        """
        INV-013: Setting Product.approval_status='approved' REQUIRES is_active=True.
        Both must be true for public visibility.
        """
        # Setup
        category = Category.objects.create(name="Test Category 7")
        seller = User.objects.create_user(
            email="seller7@test.com",
            password="testpass123",
            user_type='store'
        )

        product = Product.objects.create(
            name="Test Product",
            description="Test",
            base_price=50.00,
            category=category,
            seller=seller,
            approval_status='pending',
            is_active=False
        )

        # TODO: After T038 implementation, Product.clean() should validate this
        # For now, document the expectation
        # product.approval_status = 'approved'
        # product.is_active = False
        # with pytest.raises(ValidationError):
        #     product.clean()

        # Valid case: both True
        product.is_active = True
        product.approval_status = 'approved'
        # Should not raise ValidationError
        # product.clean()
