"""
Cart merge service for merging guest carts into user carts
Implements conflict resolution where user cart quantity wins
"""

import logging
from django.db import transaction
from ..models import Cart, CartItem, get_available_stock

logger = logging.getLogger(__name__)


def merge_guest_cart(user, session_id):
    """
    Merge guest cart items into authenticated user's cart.
    
    Conflict resolution strategy: User cart quantity wins for duplicate products.
    For products with variants, each variant combination is treated separately.
    
    Args:
        user: User object (authenticated user)
        session_id: UUID string of guest session
    
    Returns:
        dict: {
            'success': bool,
            'items_added': int,
            'items_skipped': int,
            'error': str (optional)
        }
    """
    try:
        # Get guest cart
        try:
            guest_cart = Cart.objects.get(session_id=session_id)
        except Cart.DoesNotExist:
            return {
                'success': False,
                'error': 'Guest cart not found'
            }
        
        # Get or create user cart
        user_cart, _ = Cart.objects.get_or_create(user=user)
        
        items_added = 0
        items_skipped = 0
        
        # Use transaction for atomic merge operation
        with transaction.atomic():
            # Iterate through guest cart items
            for guest_item in guest_cart.items.all():
                # Check if user cart has the same product with same variants
                existing_items = user_cart.items.filter(
                    product=guest_item.product
                )
                
                # Check for variant match
                variant_match = None
                for existing_item in existing_items:
                    if existing_item.selected_variants == guest_item.selected_variants:
                        variant_match = existing_item
                        break
                
                if variant_match:
                    # Duplicate found - user cart quantity wins
                    # Skip guest item, keep user's quantity
                    logger.info(
                        f"Skipping duplicate item: user_id={user.id}, "
                        f"product_id={guest_item.product.id}, "
                        f"guest_qty={guest_item.quantity}, "
                        f"user_qty={variant_match.quantity}"
                    )
                    items_skipped += 1
                else:
                    # No duplicate - add guest item to user cart, but only if the
                    # selected variant (or product, if no variant) still has enough
                    # stock. Phase 2 fix: this previously created the CartItem
                    # unconditionally, with no stock check of any kind.
                    try:
                        available_stock = get_available_stock(guest_item.product, guest_item.variant_id)
                    except ValueError:
                        available_stock = 0  # variant no longer exists/active

                    if available_stock < guest_item.quantity:
                        logger.info(
                            f"Skipping guest item on merge - insufficient stock: "
                            f"user_id={user.id}, product_id={guest_item.product.id}, "
                            f"variant_id={guest_item.variant_id}, "
                            f"requested={guest_item.quantity}, available={available_stock}"
                        )
                        items_skipped += 1
                        continue

                    CartItem.objects.create(
                        cart=user_cart,
                        product=guest_item.product,
                        quantity=guest_item.quantity,
                        selected_variants=guest_item.selected_variants,
                        variant_id=guest_item.variant_id
                    )
                    logger.info(
                        f"Added guest item to user cart: user_id={user.id}, "
                        f"product_id={guest_item.product.id}, "
                        f"quantity={guest_item.quantity}"
                    )
                    items_added += 1
            
            # Delete guest cart after successful merge
            guest_cart.delete()
            logger.info(
                f"Deleted guest cart after merge: session_id={session_id}, "
                f"items_added={items_added}, items_skipped={items_skipped}"
            )
        
        return {
            'success': True,
            'items_added': items_added,
            'items_skipped': items_skipped
        }
        
    except Exception as e:
        logger.error(f"Error merging guest cart: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
