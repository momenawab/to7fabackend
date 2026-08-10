"""
Phase 2 regression test: ProductVisibilityError reaches the client (workstream 7).

Proves ProductVisibilityError.unapproved_products is no longer swallowed by the
generic ValueError handler in create_order - the documented error code and payload
(docs/API_PRODUCT_APPROVAL.md) must actually reach the client.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from products.models import Category, Product

User = get_user_model()


@pytest.mark.django_db
class TestProductVisibilityErrorReachesClient:
    def setup_method(self):
        self.client = APIClient()
        self.client.defaults['HTTP_HOST'] = 'localhost'
        self.seller = User.objects.create_user(
            email='pve_seller@test.com',
            password='testpass123',
            phone_number='+201444444441',
            is_mobile_verified=True,
            user_type='store',
        )
        self.customer = User.objects.create_user(
            email='pve_customer@test.com',
            password='testpass123',
            phone_number='+201444444442',
            is_mobile_verified=True,
            user_type='customer',
        )
        self.category = Category.objects.create(name='PVE Category')
        self.pending_product = Product.objects.create(
            name='Unapproved Product',
            description='d',
            base_price=50,
            stock_quantity=5,
            category=self.category,
            seller=self.seller,
            approval_status='pending',
        )

    def test_order_with_unapproved_product_returns_structured_error(self):
        refresh = RefreshToken.for_user(self.customer)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

        response = self.client.post(
            '/api/orders/create/',
            {
                'items_data': [
                    {'product_id': self.pending_product.id, 'quantity': 1},
                ],
                'shipping_address': '123 Test St',
                'shipping_cost': '0.00',
                'payment_method': 'cod',
                'idempotency_key': 'pve-test-order-1',
            },
            format='json',
        )

        assert response.status_code == 400, response.content
        body = response.json()

        # The specific error code must be surfaced, not the generic VALIDATION_ERROR
        # this was previously collapsed into.
        assert body['error']['code'] == 'PRODUCT_VISIBILITY_ERROR'

        # And the documented unapproved_products payload must actually reach the client.
        unapproved = body['error']['details']['unapproved_products']
        assert len(unapproved) == 1
        assert unapproved[0]['product_id'] == self.pending_product.id
        assert unapproved[0]['approval_status'] == 'pending'
