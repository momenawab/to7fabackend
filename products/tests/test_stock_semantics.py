"""
Phase 2 regression tests: Product.stock / combination_stocks (workstream 5).

Proves Product.stock correctly ignores stale/legacy combination_stocks data and only
reflects ProductCategoryVariantOption.stock_count (the canonical field per Spec 004
C.1/C.2), and that the deprecated combination-stock write endpoint no longer returns a
false "success" for a write that has no effect on real, enforced stock.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from products.models import Category, CategoryVariantOption, CategoryVariantType, Product, ProductCategoryVariantOption

User = get_user_model()


@pytest.mark.django_db
class TestProductStockIgnoresLegacyCombinationStocks:
    def setup_method(self):
        self.seller = User.objects.create_user(
            email='stock_semantics_seller@test.com',
            password='testpass123',
            phone_number='+201333333331',
            is_mobile_verified=True,
            user_type='store',
        )
        self.category = Category.objects.create(name='Stock Semantics Category')
        self.variant_type = CategoryVariantType.objects.create(name='Size', category=self.category)

    def test_stale_combination_stocks_does_not_affect_canonical_stock(self):
        """Mirrors the real product found during investigation (id=1265 locally):
        stale combination_stocks data with an unrelated value must not leak into
        Product.stock, which must reflect only ProductCategoryVariantOption."""
        product = Product.objects.create(
            name='Legacy Combination Product',
            description='d',
            base_price=100,
            stock_quantity=0,
            category=self.category,
            seller=self.seller,
            approval_status='approved',
            combination_stocks={'29_27': 10},  # stale, unrelated legacy value
        )
        option = CategoryVariantOption.objects.create(variant_type=self.variant_type, value='L')
        ProductCategoryVariantOption.objects.create(
            product=product, category_variant_option=option, stock_count=25, is_active=True,
        )

        # Canonical stock (25) must win, not the unrelated legacy value (10).
        assert product.stock == 25

    def test_empty_combination_stocks_non_variant_product_uses_stock_quantity(self):
        product = Product.objects.create(
            name='Non Variant Product',
            description='d',
            base_price=50,
            stock_quantity=8,
            category=self.category,
            seller=self.seller,
            approval_status='approved',
        )
        assert product.stock == 8


@pytest.mark.django_db
class TestDeprecatedCombinationStockEndpoint:
    def setup_method(self):
        self.client = APIClient()
        self.client.defaults['HTTP_HOST'] = 'localhost'
        self.seller = User.objects.create_user(
            email='stock_semantics_seller2@test.com',
            password='testpass123',
            phone_number='+201333333332',
            is_mobile_verified=True,
            user_type='store',
        )
        self.category = Category.objects.create(name='Deprecated Endpoint Category')
        self.product = Product.objects.create(
            name='Deprecated Endpoint Product',
            description='d',
            base_price=100,
            stock_quantity=0,
            category=self.category,
            seller=self.seller,
            approval_status='approved',
        )

    def test_combination_stock_endpoint_no_longer_returns_false_success(self):
        """Phase 2 fix: this endpoint used to accept the write, save it into
        combination_stocks, and return 200 "success" - while having zero effect on
        real stock. It must now fail loudly instead of lying about success."""
        refresh = RefreshToken.for_user(self.seller)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        response = self.client.put(
            f'/api/admin/seller/dashboard/products/{self.product.id}/combination-stocks/',
            {'combination_id': '1_2', 'stock_count': 50},
            format='json',
        )
        assert response.status_code == 410
        # And, critically, the write must not have silently happened either.
        self.product.refresh_from_db()
        assert not self.product.combination_stocks

    def test_variant_stock_endpoint_still_works(self):
        """Sanity check: the correct, canonical sibling endpoint is unaffected."""
        variant_type = CategoryVariantType.objects.create(name='Size', category=self.category)
        option = CategoryVariantOption.objects.create(variant_type=variant_type, value='M')
        variant = ProductCategoryVariantOption.objects.create(
            product=self.product, category_variant_option=option, stock_count=5, is_active=True,
        )
        refresh = RefreshToken.for_user(self.seller)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        response = self.client.put(
            f'/api/admin/seller/dashboard/products/{self.product.id}/variants/{variant.id}/stock/',
            {'stock_count': 15},
            format='json',
        )
        assert response.status_code == 200, response.content
        variant.refresh_from_db()
        assert variant.stock_count == 15
