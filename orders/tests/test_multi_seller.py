"""
Tests for Multi-Seller Order Support - User Story 5

Tests per-item fulfillment status tracking and order-level state aggregation
for multi-seller orders.
"""
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model

from orders.models import Order, OrderItem
from orders.atomic_order_system import OrderStateMachine

User = get_user_model()


@pytest.fixture
def seller_a(db):
    """Create first seller user."""
    import uuid
    return User.objects.create_user(
        email=f'seller_a_{str(uuid.uuid4())[:8]}@example.com',
        password='testpass123',
        user_type='artist'
    )


@pytest.fixture
def seller_b(db):
    """Create second seller user."""
    import uuid
    return User.objects.create_user(
        email=f'seller_b_{str(uuid.uuid4())[:8]}@example.com',
        password='testpass123',
        user_type='store'
    )


@pytest.fixture
def product_from_seller_a(seller_a, db):
    """Create a product from seller A."""
    from products.models import Product
    import uuid
    
    return Product.objects.create(
        seller=seller_a,
        name=f'Product A {str(uuid.uuid4())[:8]}',
        description='Product from seller A',
        base_price=Decimal('100.00'),
        stock_quantity=50,
        is_active=True
    )


@pytest.fixture
def product_from_seller_b(seller_b, db):
    """Create a product from seller B."""
    from products.models import Product
    import uuid
    
    return Product.objects.create(
        seller=seller_b,
        name=f'Product B {str(uuid.uuid4())[:8]}',
        description='Product from seller B',
        base_price=Decimal('75.00'),
        stock_quantity=75,
        is_active=True
    )


@pytest.fixture
def multi_seller_order(user, product_from_seller_a, product_from_seller_b, db):
    """Create an order with items from two different sellers."""
    order = Order.objects.create(
        user=user,
        total_amount=Decimal('175.00'),
        shipping_address='123 Test St, Test City',
        shipping_cost=Decimal('0.00'),
        payment_method='wallet',
        status='paid',
        payment_status=True,
        idempotency_key='test_multi_seller_123'
    )
    
    # Create items from both sellers
    OrderItem.objects.create(
        order=order,
        product=product_from_seller_a,
        quantity=1,
        price=Decimal('100.00'),
        seller=seller_a,
        item_status='pending',
        reservation_status='reserved'
    )
    
    OrderItem.objects.create(
        order=order,
        product=product_from_seller_b,
        quantity=1,
        price=Decimal('75.00'),
        seller=seller_b,
        item_status='pending',
        reservation_status='reserved'
    )
    
    return order


class TestPerItemStatusTracking:
    """Test per-item status tracking for multi-seller orders."""

    def test_initial_item_status_is_pending(self, multi_seller_order):
        """Order items should start with 'pending' status."""
        items = multi_seller_order.items.all()
        assert items.count() == 2
        for item in items:
            assert item.item_status == 'pending'
            assert item.reservation_status == 'reserved'

    def test_item_status_independent_of_other_items(self, multi_seller_order):
        """Each item's status should be independent of other items."""
        items = list(multi_seller_order.items.all())
        
        # Update first item to processing
        items[0].item_status = 'processing'
        items[0].save()
        
        # Second item should remain pending
        items[1].refresh_from_db()
        assert items[1].item_status == 'pending'
        
        # First item should be processing
        items[0].refresh_from_db()
        assert items[0].item_status == 'processing'


class TestOrderStatusAggregation:
    """Test order-level state aggregation from item statuses."""

    def test_all_shipped_aggregates_to_shipped(self, multi_seller_order):
        """When all items are shipped, order should be shipped."""
        from orders.services.multi_seller import aggregate_order_status
        
        items = multi_seller_order.items.all()
        for item in items:
            item.item_status = 'shipped'
            item.save()
        
        aggregated_status = aggregate_order_status(multi_seller_order)
        assert aggregated_status == 'shipped'

    def test_all_delivered_aggregates_to_delivered(self, multi_seller_order):
        """When all items are delivered, order should be delivered."""
        from orders.services.multi_seller import aggregate_order_status
        
        items = multi_seller_order.items.all()
        for item in items:
            item.item_status = 'delivered'
            item.save()
        
        aggregated_status = aggregate_order_status(multi_seller_order)
        assert aggregated_status == 'delivered'

    def test_all_completed_aggregates_to_completed(self, multi_seller_order):
        """When all items are completed, order should be completed."""
        from orders.services.multi_seller import aggregate_order_status
        
        items = multi_seller_order.items.all()
        for item in items:
            item.item_status = 'completed'
            item.save()
        
        aggregated_status = aggregate_order_status(multi_seller_order)
        assert aggregated_status == 'completed'

    def test_all_cancelled_aggregates_to_cancelled(self, multi_seller_order):
        """When all items are cancelled, order should be cancelled."""
        from orders.services.multi_seller import aggregate_order_status
        
        items = multi_seller_order.items.all()
        for item in items:
            item.item_status = 'cancelled'
            item.save()
        
        aggregated_status = aggregate_order_status(multi_seller_order)
        assert aggregated_status == 'cancelled'


class TestPartialShipping:
    """Test partial shipping scenarios in multi-seller orders."""

    def test_some_shipped_keeps_order_in_processing(self, multi_seller_order):
        """When only some items are shipped, order should stay in processing."""
        from orders.services.multi_seller import aggregate_order_status
        
        items = list(multi_seller_order.items.all())
        
        # Ship first item only
        items[0].item_status = 'shipped'
        items[0].save()
        
        # Second item remains pending
        items[1].item_status = 'pending'
        items[1].save()
        
        aggregated_status = aggregate_order_status(multi_seller_order)
        assert aggregated_status == 'processing'

    def test_one_processing_one_pending_keeps_order_in_processing(self, multi_seller_order):
        """When one item is processing and one pending, order should be processing."""
        from orders.services.multi_seller import aggregate_order_status
        
        items = list(multi_seller_order.items.all())
        
        items[0].item_status = 'processing'
        items[0].save()
        
        items[1].item_status = 'pending'
        items[1].save()
        
        aggregated_status = aggregate_order_status(multi_seller_order)
        assert aggregated_status == 'processing'

    def test_one_shipped_one_processing_keeps_order_in_processing(self, multi_seller_order):
        """When one item is shipped and one processing, order should be processing."""
        from orders.services.multi_seller import aggregate_order_status
        
        items = list(multi_seller_order.items.all())
        
        items[0].item_status = 'shipped'
        items[0].save()
        
        items[1].item_status = 'processing'
        items[1].save()
        
        aggregated_status = aggregate_order_status(multi_seller_order)
        assert aggregated_status == 'processing'

    def test_order_transitions_to_shipped_when_last_item_shipped(self, multi_seller_order):
        """Order should transition to shipped when the last item is shipped."""
        from orders.services.multi_seller import aggregate_order_status
        
        items = list(multi_seller_order.items.all())
        
        # Ship first item
        items[0].item_status = 'shipped'
        items[0].save()
        
        # Order should be processing
        aggregated_status = aggregate_order_status(multi_seller_order)
        assert aggregated_status == 'processing'
        
        # Ship second item
        items[1].item_status = 'shipped'
        items[1].save()
        
        # Order should now be shipped
        aggregated_status = aggregate_order_status(multi_seller_order)
        assert aggregated_status == 'shipped'


class TestSellerIsolation:
    """Test that sellers can only view and update their own items."""

    def test_get_seller_items_returns_only_own_items(self, multi_seller_order, seller_a, seller_b):
        """get_seller_items should return only items belonging to the seller."""
        from orders.services.multi_seller import get_seller_items
        
        # Get items for seller A
        seller_a_items = get_seller_items(multi_seller_order, seller_a)
        assert seller_a_items.count() == 1
        assert seller_a_items[0].seller == seller_a
        
        # Get items for seller B
        seller_b_items = get_seller_items(multi_seller_order, seller_b)
        assert seller_b_items.count() == 1
        assert seller_b_items[0].seller == seller_b

    def test_seller_cannot_update_other_seller_items(self, multi_seller_order, seller_a):
        """Sellers should not be able to update items from other sellers."""
        from orders.services.multi_seller import update_item_status
        
        items = list(multi_seller_order.items.all())
        other_seller_item = None
        own_item = None
        
        for item in items:
            if item.seller == seller_a:
                own_item = item
            else:
                other_seller_item = item
        
        # Seller A should be able to update their own item
        success, error = update_item_status(
            item_id=own_item.id,
            seller=seller_a,
            new_status='processing'
        )
        assert success is True
        assert error is None
        
        # Seller A should NOT be able to update other seller's item
        success, error = update_item_status(
            item_id=other_seller_item.id,
            seller=seller_a,
            new_status='processing'
        )
        assert success is False
        assert 'permission' in error.lower() or 'not found' in error.lower()

    def test_update_item_status_validates_status_transition(self, multi_seller_order, seller_a):
        """update_item_status should validate status transitions."""
        from orders.services.multi_seller import update_item_status
        
        # Get seller A's item
        seller_a_item = multi_seller_order.items.filter(seller=seller_a).first()
        
        # Invalid transition: pending -> delivered
        success, error = update_item_status(
            item_id=seller_a_item.id,
            seller=seller_a,
            new_status='delivered'
        )
        assert success is False
        assert 'invalid' in error.lower() or 'transition' in error.lower()

    def test_update_item_status_valid_transitions(self, multi_seller_order, seller_a):
        """update_item_status should allow valid status transitions."""
        from orders.services.multi_seller import update_item_status
        
        # Get seller A's item
        seller_a_item = multi_seller_order.items.filter(seller=seller_a).first()
        
        # Valid transitions
        valid_transitions = [
            ('pending', 'processing'),
            ('processing', 'shipped'),
            ('shipped', 'delivered'),
            ('delivered', 'completed'),
        ]
        
        for from_status, to_status in valid_transitions:
            # Set initial status
            seller_a_item.item_status = from_status
            seller_a_item.save()
            
            # Attempt transition
            success, error = update_item_status(
                item_id=seller_a_item.id,
                seller=seller_a,
                new_status=to_status
            )
            assert success is True, f"Failed transition: {from_status} -> {to_status}, error: {error}"
            assert error is None


class TestOrderStateMachineIntegration:
    """Test integration of multi-seller aggregation with order state machine."""

    def test_paid_order_remains_paid_until_first_item_processed(self, multi_seller_order):
        """Paid order should remain in 'paid' until first item is processed."""
        from orders.services.multi_seller import aggregate_order_status
        
        # All items are pending
        aggregated_status = aggregate_order_status(multi_seller_order)
        assert aggregated_status == 'paid'
        
        # First item becomes processing
        items = list(multi_seller_order.items.all())
        items[0].item_status = 'processing'
        items[0].save()
        
        # Order should now be processing
        aggregated_status = aggregate_order_status(multi_seller_order)
        assert aggregated_status == 'processing'

    def test_order_status_respects_state_machine_valid_transitions(self, multi_seller_order):
        """Aggregated status should respect state machine valid transitions."""
        from orders.services.multi_seller import aggregate_order_status
        
        # Start with paid status
        assert multi_seller_order.status == 'paid'
        
        # All items become processing - order should transition to processing
        items = multi_seller_order.items.all()
        for item in items:
            item.item_status = 'processing'
            item.save()
        
        aggregated_status = aggregate_order_status(multi_seller_order)
        assert OrderStateMachine.validate_transition('paid', aggregated_status)
        assert aggregated_status == 'processing'
