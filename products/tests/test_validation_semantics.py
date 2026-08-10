"""
Phase 2 regression tests: Product.clean() validation semantics (workstream 6).

Proves approved+inactive is accepted as the legitimate state the documented Visibility
Matrix (docs/API_PRODUCT_APPROVAL.md) describes, while other approval_status/is_active
combinations continue to validate cleanly, and that this doesn't affect the actual
visibility query (Product.objects.approved()).
"""
import pytest
from django.contrib.auth import get_user_model

from products.models import Category, Product

User = get_user_model()


@pytest.fixture
def seller(db):
    return User.objects.create_user(
        email='validation_seller@test.com',
        password='testpass123',
        user_type='store',
    )


@pytest.fixture
def category(db):
    return Category.objects.create(name='Validation Semantics Category')


@pytest.mark.django_db
class TestProductCleanValidation:
    def _product(self, seller, category, **overrides):
        defaults = dict(
            name='Validation Product',
            description='d',
            base_price=100,
            stock_quantity=5,
            category=category,
            seller=seller,
        )
        defaults.update(overrides)
        return Product(**defaults)

    def test_approved_and_active_is_valid(self, seller, category):
        product = self._product(seller, category, approval_status='approved', is_active=True)
        product.full_clean(exclude=['seller'])  # seller FK validation needs a saved instance path; exclude is fine here

    def test_approved_and_inactive_is_now_valid(self, seller, category):
        """The Phase 2 fix: this combination is documented as legitimate
        ("Inactive (even if approved)") and must not raise ValidationError."""
        product = self._product(seller, category, approval_status='approved', is_active=False)
        product.full_clean(exclude=['seller'])  # must not raise

    def test_pending_active_is_valid(self, seller, category):
        product = self._product(seller, category, approval_status='pending', is_active=True)
        product.full_clean(exclude=['seller'])

    def test_pending_inactive_is_valid(self, seller, category):
        product = self._product(seller, category, approval_status='pending', is_active=False)
        product.full_clean(exclude=['seller'])

    def test_rejected_active_is_valid(self, seller, category):
        product = self._product(seller, category, approval_status='rejected', is_active=True)
        product.full_clean(exclude=['seller'])

    def test_rejected_inactive_is_valid(self, seller, category):
        product = self._product(seller, category, approval_status='rejected', is_active=False)
        product.full_clean(exclude=['seller'])


@pytest.mark.django_db
class TestSellerPauseAdminApproveTransition:
    """The real-world scenario this fix unblocks: an admin approves a product, the
    seller later pauses it (is_active=False) without needing re-approval, and the
    product correctly disappears from public visibility without failing to save."""

    def test_seller_can_pause_an_approved_product(self, seller, category):
        product = Product.objects.create(
            name='Pausable Product', description='d', base_price=50,
            stock_quantity=3, category=category, seller=seller,
            approval_status='approved', is_active=True,
        )
        assert Product.objects.approved().filter(id=product.id).exists()

        # Seller pauses their own approved listing.
        product.is_active = False
        product.full_clean(exclude=['seller'])  # must not raise
        product.save()

        product.refresh_from_db()
        assert product.approval_status == 'approved'  # admin's approval preserved
        assert product.is_active is False
        # And it correctly disappears from public visibility (query-level enforcement).
        assert not Product.objects.approved().filter(id=product.id).exists()

    def test_admin_can_still_reject_regardless_of_active_state(self, seller, category):
        product = Product.objects.create(
            name='Rejectable Product', description='d', base_price=50,
            stock_quantity=3, category=category, seller=seller,
            approval_status='pending', is_active=True,
        )
        product.approval_status = 'rejected'
        product.rejection_reason = 'Policy violation'
        product.full_clean(exclude=['seller'])
        product.save()

        product.refresh_from_db()
        assert product.approval_status == 'rejected'
