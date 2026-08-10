"""
Phase 2 regression tests: cart/variant stock correctness (BACKEND_AUDIT.md, workstream 4).

Proves cart operations validate against the SELECTED VARIANT's stock (the authoritative
inventory source per Spec 004 C.6) rather than the product's aggregate stock across all
variants, across add_item, update_item_by_id, the AddToCartSerializer/UpdateCartItemSerializer
validation layers, and cart merge.
"""
import pytest
from django.contrib.auth import get_user_model

from cart.models import Cart, CartItem, get_available_stock
from cart.services.cart_merge import merge_guest_cart
from products.models import (
    Category, CategoryVariantOption, CategoryVariantType, Product,
    ProductCategoryVariantOption,
)

User = get_user_model()


@pytest.fixture
def seller(db):
    return User.objects.create_user(
        email='cart_stock_seller@test.com',
        password='testpass123',
        user_type='store',
    )


@pytest.fixture
def category(db):
    return Category.objects.create(name='Cart Stock Category')


@pytest.fixture
def size_type(category):
    return CategoryVariantType.objects.create(name='Size', category=category, priority=1)


def _make_variant_product(seller, category, size_type, size_stocks):
    """Create a variant product where `size_stocks` maps option value -> stock_count.
    Returns (product, {value: ProductCategoryVariantOption})."""
    product = Product.objects.create(
        name='Variant Product',
        description='d',
        base_price=100,
        stock_quantity=0,
        category=category,
        seller=seller,
        approval_status='approved',
    )
    variants = {}
    for value, stock in size_stocks.items():
        option = CategoryVariantOption.objects.create(variant_type=size_type, value=value)
        variants[value] = ProductCategoryVariantOption.objects.create(
            product=product, category_variant_option=option, stock_count=stock, is_active=True,
        )
    return product, variants


@pytest.mark.django_db
class TestGetAvailableStockHelper:
    def test_product_without_variants_uses_stock_quantity(self, seller, category):
        product = Product.objects.create(
            name='Simple Product', description='d', base_price=50,
            stock_quantity=7, category=category, seller=seller, approval_status='approved',
        )
        assert get_available_stock(product) == 7
        assert get_available_stock(product, variant_id=None) == 7

    def test_variant_with_sufficient_stock(self, seller, category, size_type):
        product, variants = _make_variant_product(seller, category, size_type, {'M': 10, 'S': 0})
        assert get_available_stock(product, variants['M'].id) == 10

    def test_variant_with_zero_stock(self, seller, category, size_type):
        product, variants = _make_variant_product(seller, category, size_type, {'M': 10, 'S': 0})
        assert get_available_stock(product, variants['S'].id) == 0

    def test_multiple_variants_only_one_has_stock_does_not_leak_aggregate(self, seller, category, size_type):
        """The bug this fixes: aggregate product.stock (10) must NOT be used when a
        specific zero-stock variant is selected."""
        product, variants = _make_variant_product(seller, category, size_type, {'M': 10, 'S': 0})
        assert product.stock == 10  # aggregate, for sanity
        assert get_available_stock(product, variants['S'].id) == 0  # but S itself has none

    def test_nonexistent_variant_id_raises(self, seller, category):
        product = Product.objects.create(
            name='No Variants Here', description='d', base_price=50,
            stock_quantity=5, category=category, seller=seller, approval_status='approved',
        )
        with pytest.raises(ValueError):
            get_available_stock(product, variant_id=999999)


@pytest.mark.django_db
class TestCartAddItemVariantStock:
    def test_add_item_product_without_variants(self, seller, category):
        product = Product.objects.create(
            name='Simple', description='d', base_price=50,
            stock_quantity=3, category=category, seller=seller, approval_status='approved',
        )
        cart = Cart.objects.create(user=User.objects.create_user(
            email='buyer1@test.com', password='x', user_type='customer'))
        item = cart.add_item(product, quantity=3)
        assert item.quantity == 3

    def test_add_item_rejects_over_stock_for_non_variant_product(self, seller, category):
        product = Product.objects.create(
            name='Simple', description='d', base_price=50,
            stock_quantity=3, category=category, seller=seller, approval_status='approved',
        )
        cart = Cart.objects.create(user=User.objects.create_user(
            email='buyer2@test.com', password='x', user_type='customer'))
        with pytest.raises(ValueError):
            cart.add_item(product, quantity=4)

    def test_add_item_variant_with_sufficient_stock_succeeds(self, seller, category, size_type):
        product, variants = _make_variant_product(seller, category, size_type, {'M': 10, 'S': 0})
        cart = Cart.objects.create(user=User.objects.create_user(
            email='buyer3@test.com', password='x', user_type='customer'))
        item = cart.add_item(product, quantity=5, variant_id=variants['M'].id)
        assert item.quantity == 5

    def test_add_item_zero_stock_variant_rejected_even_though_other_variant_has_stock(
        self, seller, category, size_type,
    ):
        """The core bug: adding 10 x Size-S must fail when only Size-M has stock,
        even though product.stock (aggregate) would say 10 are available."""
        product, variants = _make_variant_product(seller, category, size_type, {'M': 10, 'S': 0})
        cart = Cart.objects.create(user=User.objects.create_user(
            email='buyer4@test.com', password='x', user_type='customer'))
        with pytest.raises(ValueError, match='Not enough stock'):
            cart.add_item(product, quantity=10, variant_id=variants['S'].id)

    def test_add_item_over_specific_variant_stock_rejected(self, seller, category, size_type):
        product, variants = _make_variant_product(seller, category, size_type, {'M': 5})
        cart = Cart.objects.create(user=User.objects.create_user(
            email='buyer5@test.com', password='x', user_type='customer'))
        with pytest.raises(ValueError):
            cart.add_item(product, quantity=6, variant_id=variants['M'].id)


@pytest.mark.django_db
class TestCartUpdateItemVariantStock:
    def test_update_item_quantity_respects_variant_stock(self, seller, category, size_type):
        product, variants = _make_variant_product(seller, category, size_type, {'M': 10, 'S': 2})
        cart = Cart.objects.create(user=User.objects.create_user(
            email='buyer6@test.com', password='x', user_type='customer'))
        item = cart.add_item(product, quantity=2, variant_id=variants['S'].id)

        # Bumping to 3 exceeds Size-S's own stock (2), even though Size-M has 10.
        with pytest.raises(ValueError, match='Not enough stock'):
            cart.update_item_by_id(item.id, 3)

        # But bumping to exactly 2 (its own limit) is fine.
        updated = cart.update_item_by_id(item.id, 2)
        assert updated.quantity == 2


@pytest.mark.django_db
class TestCartMergeVariantStock:
    def test_merge_skips_item_that_exceeds_variant_stock(self, seller, category, size_type):
        product, variants = _make_variant_product(seller, category, size_type, {'M': 10, 'S': 1})

        guest_cart = Cart.objects.create(session_id='11111111-1111-1111-1111-111111111111')
        # Guest cart has 5 x Size-S, but only 1 is in stock.
        CartItem.objects.create(cart=guest_cart, product=product, quantity=5, variant_id=variants['S'].id)

        user = User.objects.create_user(email='merge_buyer@test.com', password='x', user_type='customer')
        result = merge_guest_cart(user, guest_cart.session_id)

        assert result['success'] is True
        assert result['items_added'] == 0
        assert result['items_skipped'] == 1
        user_cart = Cart.objects.get(user=user)
        assert user_cart.items.count() == 0

    def test_merge_adds_item_within_variant_stock(self, seller, category, size_type):
        product, variants = _make_variant_product(seller, category, size_type, {'M': 10, 'S': 1})

        guest_cart = Cart.objects.create(session_id='22222222-2222-2222-2222-222222222222')
        CartItem.objects.create(cart=guest_cart, product=product, quantity=1, variant_id=variants['S'].id)

        user = User.objects.create_user(email='merge_buyer2@test.com', password='x', user_type='customer')
        result = merge_guest_cart(user, guest_cart.session_id)

        assert result['success'] is True
        assert result['items_added'] == 1
        assert result['items_skipped'] == 0
