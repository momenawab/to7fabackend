"""
Multi-Seller Order Support

Provides functionality for managing per-item fulfillment status
and aggregating order-level state from item statuses.

This module implements:
- Per-item status tracking for multi-seller orders
- Order-level state aggregation from item statuses
- Seller isolation (sellers can only update their own items)
"""

import logging
from typing import Tuple, Optional

from orders.models import Order, OrderItem
from orders.atomic_order_system import OrderStateMachine

logger = logging.getLogger(__name__)


def aggregate_order_status(order: Order) -> str:
    """
    Derive order status from line item statuses.
    
    This function implements the aggregation logic defined in the specification:
    - All items cancelled -> order cancelled
    - All items completed -> order completed
    - All items delivered -> order delivered
    - All items shipped -> order shipped
    - Any item processing -> order processing
    - Otherwise, keep current order status
    
    Args:
        order: Order object to aggregate status for
        
    Returns:
        Aggregated order status string
        
    Raises:
        ValueError: If order has no items
    """
    # Get all item statuses
    item_statuses = list(order.items.values_list('item_status', flat=True))
    
    if not item_statuses:
        raise ValueError(f"Order {order.id} has no items")
    
    # Check all items cancelled
    if all(status == 'cancelled' for status in item_statuses):
        return 'cancelled'
    
    # Check all items completed
    if all(status == 'completed' for status in item_statuses):
        return 'completed'
    
    # Check all items delivered
    if all(status == 'delivered' for status in item_statuses):
        return 'delivered'
    
    # Check all items shipped
    if all(status == 'shipped' for status in item_statuses):
        return 'shipped'
    
    # Check if any item is in processing
    if any(status == 'processing' for status in item_statuses):
        return 'processing'
    
    # Default: keep current order status
    return order.status


def update_item_status(
    item_id: int,
    seller,
    new_status: str
) -> Tuple[bool, Optional[str]]:
    """
    Update the status of an order item with seller validation.
    
    This function:
    1. Validates the item belongs to the seller
    2. Validates the status transition is allowed
    3. Updates the item status atomically
    4. Returns success/error tuple
    
    Valid item status transitions:
    - pending -> processing
    - processing -> shipped
    - shipped -> delivered
    - delivered -> completed
    - pending/processing/shipped/delivered -> cancelled (admin only)
    
    Args:
        item_id: ID of the order item to update
        seller: User object of the seller attempting the update
        new_status: New status to set for the item
        
    Returns:
        Tuple of (success: bool, error: Optional[str])
        - success: True if update succeeded, False otherwise
        - error: Error message if failed, None if succeeded
    """
    from django.db import transaction
    
    try:
        with transaction.atomic():
            # Get the item with lock
            try:
                item = OrderItem.objects.select_for_update().get(id=item_id)
            except OrderItem.DoesNotExist:
                return (False, f"Order item {item_id} not found")
            
            # Validate seller ownership
            if item.seller != seller:
                return (False, "You don't have permission to update this item")
            
            # Validate status transition
            current_status = item.item_status
            
            # Allow same status (no-op)
            if current_status == new_status:
                return (True, None)
            
            # Define valid item status transitions
            VALID_ITEM_TRANSITIONS = {
                'pending': ['processing', 'cancelled'],
                'processing': ['shipped', 'cancelled'],
                'shipped': ['delivered', 'cancelled'],
                'delivered': ['completed', 'cancelled'],
                'completed': [],
                'cancelled': [],
            }
            
            valid_next_states = VALID_ITEM_TRANSITIONS.get(current_status, [])
            
            if new_status not in valid_next_states:
                return (
                    False,
                    f"Invalid item status transition from '{current_status}' to '{new_status}'. "
                    f"Valid transitions: {valid_next_states}"
                )
            
            # Update the item status
            item.item_status = new_status
            item.save()
            
            logger.info(
                f"Updated item {item_id} status from '{current_status}' to '{new_status}' "
                f"by seller {seller.id}"
            )
            
            return (True, None)
            
    except Exception as e:
        logger.error(f"Failed to update item {item_id} status: {e}")
        return (False, f"Failed to update item status: {str(e)}")


def get_seller_items(order: Order, seller) -> list:
    """
    Get all order items belonging to a specific seller.
    
    This function enforces seller isolation by returning only items
    that belong to the specified seller.
    
    Args:
        order: Order object to get items from
        seller: User object of the seller
        
    Returns:
        QuerySet of OrderItem objects belonging to the seller
    """
    return order.items.filter(seller=seller)
