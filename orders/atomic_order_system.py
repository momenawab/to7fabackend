"""
ATOMIC ORDER SYSTEM
==================

This module implements a robust, atomic order creation system that prevents:
1. Overselling through proper row-level locking
2. Duplicate orders through idempotency keys
3. Financial inconsistencies through wallet-order atomicity
4. Race conditions through proper transaction management

CORE PRINCIPLES:
- All operations are wrapped in @transaction.atomic
- Stock checks happen AFTER acquiring row locks
- Wallet operations are atomic with order creation
- Idempotency keys prevent duplicate operations
- Explicit rollback on any failure

SPEC 004 COMPLIANCE:
- ProductCategoryVariantOption is the canonical variant system (Spec 004 C.1, C.2)
- ProductVariant fallback is deprecated (Spec 004 C.1)
- variant_id references ProductCategoryVariantOption.id (Spec 004 C.3)
"""

from django.db import transaction
from decimal import Decimal
from typing import Dict, List, Tuple, Optional
import logging
import warnings

logger = logging.getLogger(__name__)


class ProductVisibilityError(ValueError):
    """
    Exception raised when attempting to order products that are not approved.

    Spec 004 INV-012: Unapproved products cannot be included in an order.
    """
    def __init__(self, message: str, unapproved_products: List[Dict] = None):
        self.unapproved_products = unapproved_products or []
        super().__init__(message)


def _log_deprecated_variant_usage(variant_id: int, context: str = "stock operation"):
    """
    Log deprecation warning when ProductVariant is accessed.

    Spec 004 C.1: ProductVariant is deprecated. Use ProductCategoryVariantOption instead.

    Args:
        variant_id: The ID of the variant being accessed
        context: Description of the operation triggering the deprecation
    """
    warnings.warn(
        f"ProductVariant (id={variant_id}) is DEPRECATED per Spec 004 C.1. "
        f"Use ProductCategoryVariantOption for {context}. "
        f"ProductVariant will be removed in a future release. "
        f"Variant data should be migrated to ProductCategoryVariantOption.",
        DeprecationWarning,
        stacklevel=3
    )
    logger.warning(
        f"Deprecated ProductVariant accessed (id={variant_id}) during {context}. "
        f"Use ProductCategoryVariantOption instead. "
        f"See Spec 004 C.1 for details."
    )


class OrderStateMachine:
    """
    Enforces strict order state transitions.

    VALID TRANSITIONS (Extended):
    - pending_payment -> paid (payment captured)
    - pending_payment -> cancelled (user cancelled, payment timeout)
    - pending_payment -> failed (payment failed)
    - cod_pending -> processing (seller acknowledged)
    - cod_pending -> cancelled (user cancelled)
    - paid -> processing (seller acknowledged)
    - paid -> cancelled (refund required)
    - paid -> refunded (refund processed)
    - processing -> shipped (order dispatched)
    - processing -> cancelled (refund required)
    - processing -> refunded (refund processed)
    - shipped -> delivered (delivery confirmed)
    - shipped -> refunded (return/dispute refund)
    - delivered -> completed (order fulfilled)
    - delivered -> refunded (return/dispute refund)
    - Terminal states (no transitions): completed, cancelled, refunded, failed
    """

    VALID_TRANSITIONS = {
        'pending_payment': ['paid', 'cancelled', 'failed'],
        'cod_pending': ['processing', 'cancelled'],
        'paid': ['processing', 'cancelled', 'refunded'],
        'processing': ['shipped', 'cancelled', 'refunded'],
        'shipped': ['delivered', 'refunded'],
        'delivered': ['completed', 'refunded'],
        'cancelled': [],
        'completed': [],
        'refunded': [],
        'failed': [],
    }

    @classmethod
    def validate_transition(cls, current_status: str, new_status: str) -> bool:
        """
        Validate if a state transition is allowed.

        Args:
            current_status: Current order status
            new_status: Desired new status

        Returns:
            True if transition is valid, False otherwise

        Raises:
            ValueError: If transition is invalid
        """
        if current_status == new_status:
            return True  # No-op transition is allowed

        valid_next_states = cls.VALID_TRANSITIONS.get(current_status, [])

        if new_status not in valid_next_states:
            raise ValueError(
                f"Invalid state transition from '{current_status}' to '{new_status}'. "
                f"Valid transitions: {valid_next_states}"
            )

        return True

    @classmethod
    def is_terminal(cls, status: str) -> bool:
        """
        Check if a state is terminal (cannot transition further).

        Args:
            status: Order status to check

        Returns:
            True if status is terminal, False otherwise
        """
        return status in ['completed', 'cancelled', 'refunded', 'failed']

    @classmethod
    def get_initial_state(cls, payment_method: str) -> str:
        """
        Get the initial order state based on payment method.

        Args:
            payment_method: Payment method (cod, wallet, instapay, credit_card)

        Returns:
            Initial order status string
        """
        if payment_method == 'cod':
            return 'cod_pending'
        return 'pending_payment'

    @classmethod
    def can_cancel(cls, status: str) -> bool:
        """
        Check if order can be cancelled.

        Args:
            status: Current order status

        Returns:
            True if order can be cancelled, False otherwise
        """
        return status in ['pending_payment', 'cod_pending', 'paid', 'processing']

    @classmethod
    def requires_refund(cls, status: str) -> bool:
        """
        Check if cancelling this status requires refund.

        Args:
            status: Current order status

        Returns:
            True if refund is required, False otherwise
        """
        return status in ['paid', 'processing', 'shipped', 'delivered']


class StockLockManager:
    """
    Manages stock locking and atomic stock operations.
    
    Uses select_for_update() to lock product rows before stock checks,
    preventing race conditions and overselling.
    """
    
    @staticmethod
    @transaction.atomic
    def reserve_stock(product_id: int, quantity: int, variant_id: Optional[int] = None) -> bool:
        """
        Reserve stock for a product (or variant) atomically.
        
        This method:
        1. Locks the product row
        2. Checks stock availability AFTER lock
        3. Decrements stock atomically
        4. Returns True on success, raises exception on failure
        
        Args:
            product_id: ID of product to reserve stock from
            quantity: Quantity to reserve
            variant_id: Optional variant ID for variant products
            
        Returns:
            True if stock was successfully reserved
            
        Raises:
            ValueError: If insufficient stock
            Exception: If product not found
        """
        from products.models import Product, ProductCategoryVariantOption, ProductVariant
        
        if variant_id:
            # Variant product stock reservation
            try:
                variant = ProductCategoryVariantOption.objects.select_for_update().get(
                    id=variant_id,
                    product_id=product_id,
                    is_active=True
                )
                
                if variant.stock_count < quantity:
                    raise ValueError(
                        f"Insufficient stock for variant. Available: {variant.stock_count}, Requested: {quantity}"
                    )
                
                # Decrement stock
                variant.stock_count -= quantity
                variant.save()
                
                logger.info(f"Reserved {quantity} units of variant {variant_id} for product {product_id}")
                return True
                
            except ProductCategoryVariantOption.DoesNotExist:
                # Try ProductVariant as fallback (DEPRECATED per Spec 004 C.1)
                _log_deprecated_variant_usage(variant_id, "stock reservation (fallback)")
                try:
                    variant = ProductVariant.objects.select_for_update().get(
                        id=variant_id,
                        product_id=product_id,
                        is_active=True
                    )

                    if variant.stock_count < quantity:
                        raise ValueError(
                            f"Insufficient stock for variant. Available: {variant.stock_count}, Requested: {quantity}"
                        )
                    
                    variant.stock_count -= quantity
                    variant.save()
                    
                    logger.info(f"Reserved {quantity} units of variant {variant_id} for product {product_id}")
                    return True
                    
                except ProductVariant.DoesNotExist:
                    raise ValueError(f"Variant {variant_id} not found for product {product_id}")
        else:
            # Non-variant product stock reservation
            try:
                product = Product.objects.select_for_update().get(id=product_id, is_active=True)
                
                # Check stock AFTER acquiring lock
                available_stock = product.stock_quantity
                
                if available_stock < quantity:
                    raise ValueError(
                        f"Insufficient stock for product '{product.name}'. "
                        f"Available: {available_stock}, Requested: {quantity}"
                    )
                
                # Decrement stock
                product.stock_quantity = available_stock - quantity
                product.save()
                
                logger.info(f"Reserved {quantity} units of product {product_id}")
                return True
                
            except Product.DoesNotExist:
                raise ValueError(f"Product {product_id} not found")
    
    @staticmethod
    @transaction.atomic
    def release_stock(product_id: int, quantity: int, variant_id: Optional[int] = None) -> bool:
        """
        Release reserved stock back to product (for cancellations).
        
        Args:
            product_id: ID of product to release stock to
            quantity: Quantity to release
            variant_id: Optional variant ID for variant products
            
        Returns:
            True if stock was successfully released
        """
        from products.models import Product, ProductCategoryVariantOption, ProductVariant
        
        if variant_id:
            # Spec 004 C.3: variant_id references ProductCategoryVariantOption.id (canonical)
            # Stock restoration uses the stored variant_id to release to the exact variant
            try:
                variant = ProductCategoryVariantOption.objects.select_for_update().get(
                    id=variant_id,
                    product_id=product_id
                )
                variant.stock_count += quantity
                variant.save()

                logger.info(f"Released {quantity} units of variant {variant_id} for product {product_id}")
                return True
                
            except ProductCategoryVariantOption.DoesNotExist:
                # Try ProductVariant as fallback (DEPRECATED per Spec 004 C.1)
                _log_deprecated_variant_usage(variant_id, "stock release (fallback)")
                try:
                    variant = ProductVariant.objects.select_for_update().get(
                        id=variant_id,
                        product_id=product_id
                    )
                    variant.stock_count += quantity
                    variant.save()
                    
                    logger.info(f"Released {quantity} units of variant {variant_id} for product {product_id}")
                    return True
                    
                except ProductVariant.DoesNotExist:
                    logger.error(f"Variant {variant_id} not found for product {product_id}")
                    return False
        else:
            # Non-variant product stock release
            try:
                product = Product.objects.select_for_update().get(id=product_id)
                product.stock_quantity += quantity
                product.save()
                
                logger.info(f"Released {quantity} units of product {product_id}")
                return True
                
            except Product.DoesNotExist:
                logger.error(f"Product {product_id} not found")
                return False
    
    @staticmethod
    @transaction.atomic
    def commit_stock(order_id: int) -> bool:
        """
        Commit reserved stock for an order (mark as permanently decremented).
        
        This method:
        1. Updates reservation_status to 'committed' for all order items
        2. No stock quantity changes (stock already decremented during reservation)
        
        Args:
            order_id: ID of the order to commit stock for
            
        Returns:
            True if stock was successfully committed
        """
        from .models import OrderItem
        
        try:
            # Get all order items and update their reservation status
            order_items = OrderItem.objects.filter(order_id=order_id)
            
            for item in order_items:
                item.reservation_status = 'committed'
                item.save()
            
            logger.info(f"Committed stock for order {order_id} - {order_items.count()} items marked as committed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to commit stock for order {order_id}: {e}")
            return False


class WalletOrderCoordinator:
    """
    Coordinates wallet and order operations atomically.
    
    Ensures that:
    - Money is never taken without an order
    - Orders never exist without payment reservation
    - Wallet and order states are always consistent
    """
    
    @staticmethod
    @transaction.atomic
    def reserve_payment(
        wallet,
        amount: Decimal,
        order_id: int,
        idempotency_key: str,
        description: str = None
    ) -> Tuple:
        """
        Reserve payment in wallet for an order.
        
        This creates a 'payment' transaction that holds the funds.
        The order status remains 'pending' until payment is captured.
        
        Args:
            wallet: Wallet object
            amount: Amount to reserve
            order_id: Order ID for reference
            idempotency_key: Unique key for idempotency
            description: Optional description
            
        Returns:
            Tuple of (success: bool, transaction: Transaction, error: str)
        """
        from wallet.models import Wallet, Transaction
        
        # Check idempotency
        if Transaction.objects.filter(idempotency_key=idempotency_key).exists():
            existing_tx = Transaction.objects.get(idempotency_key=idempotency_key)
            return (True, existing_tx, None)
        
        # Lock wallet for update
        locked_wallet = Wallet.objects.select_for_update().get(id=wallet.id)
        
        # Check balance AFTER lock
        if locked_wallet.balance < amount:
            return (False, None, "Insufficient wallet balance")
        
        # Create payment reservation transaction
        tx = Transaction.objects.create(
            wallet=locked_wallet,
            amount=amount,
            transaction_type='payment',
            reference_id=str(order_id),
            description=description or f"Payment reservation for order #{order_id}",
            status='pending',  # Pending until order is confirmed
            balance_before=locked_wallet.balance,
            balance_after=locked_wallet.balance - amount,
            idempotency_key=idempotency_key
        )
        
        # Update wallet balance
        locked_wallet.balance -= amount
        locked_wallet.save()
        
        logger.info(f"Reserved {amount} from wallet {wallet.id} for order {order_id}")
        return (True, tx, None)
    
    @staticmethod
    @transaction.atomic
    def capture_payment(
        order_id: int,
        idempotency_key: str
    ) -> Tuple:
        """
        Capture a previously reserved payment.
        
        Marks the payment transaction as 'completed' and updates order status to 'paid'.
        
        Args:
            order_id: Order ID
            idempotency_key: Unique key for idempotency
            
        Returns:
            Tuple of (success: bool, transaction: Transaction, error: str)
        """
        from wallet.models import Transaction
        from .models import Order
        
        # Get order
        try:
            order = Order.objects.select_for_update().get(id=order_id)
        except Order.DoesNotExist:
            return (False, None, f"Order {order_id} not found")
        
        # Get pending payment transaction
        try:
            tx = Transaction.objects.select_for_update().get(
                reference_id=str(order_id),
                transaction_type='payment',
                status='pending'
            )
        except Transaction.DoesNotExist:
            return (False, None, f"No pending payment found for order {order_id}")
        
        # Mark transaction as completed
        tx.status = 'completed'
        tx.save()
        
        # Update order status
        order.status = 'paid'
        order.payment_status = True
        order.save()
        
        logger.info(f"Captured payment for order {order_id}")
        return (True, tx, None)
    
    @staticmethod
    @transaction.atomic
    def release_payment(
        order_id: int,
        idempotency_key: str,
        refund_reason: str = None
    ) -> Tuple:
        """
        Release a reserved payment (refund) and update order status.
        
        Creates a refund transaction and marks the original payment as failed.
        
        Args:
            order_id: Order ID
            idempotency_key: Unique key for idempotency
            refund_reason: Optional reason for refund
            
        Returns:
            Tuple of (success: bool, refund_tx: Transaction, error: str)
        """
        from wallet.models import Wallet, Transaction
        from .models import Order
        
        # Get order
        try:
            order = Order.objects.select_for_update().get(id=order_id)
        except Order.DoesNotExist:
            return (False, None, f"Order {order_id} not found")
        
        # Get payment transaction
        try:
            payment_tx = Transaction.objects.select_for_update().get(
                reference_id=str(order_id),
                transaction_type='payment',
                status='pending'
            )
        except Transaction.DoesNotExist:
            # Check if already refunded
            if Transaction.objects.filter(
                reference_id=str(order_id),
                transaction_type='refund'
            ).exists():
                return (True, Transaction.objects.filter(reference_id=str(order_id), transaction_type='refund').first(), None)
            return (False, None, f"No pending payment found for order {order_id}")
        
        # Get wallet
        wallet = Wallet.objects.select_for_update().get(id=payment_tx.wallet.id)
        
        # Mark payment as failed
        payment_tx.status = 'failed'
        payment_tx.save()
        
        # Create refund transaction
        refund_tx = Transaction.objects.create(
            wallet=wallet,
            amount=payment_tx.amount,
            transaction_type='refund',
            reference_id=str(order_id),
            description=refund_reason or f"Refund for cancelled order #{order_id}",
            status='completed',
            balance_before=wallet.balance,
            balance_after=wallet.balance + payment_tx.amount,
            idempotency_key=f"refund_{idempotency_key}"
        )
        
        # Update wallet balance
        wallet.balance += payment_tx.amount
        wallet.save()
        
        # Update order status
        order.status = 'cancelled'
        order.save()
        
        logger.info(f"Refunded {payment_tx.amount} to wallet {wallet.id} for order {order_id}")
        return (True, refund_tx, None)

    @staticmethod
    @transaction.atomic
    def refund_payment(
        order_id: int,
        idempotency_key: str,
        refund_reason: str = None
    ) -> Tuple:
        """
        Process refund for paid orders (return/dispute scenario).
        
        Creates a refund transaction, credits wallet, releases stock,
        and marks original payment as refunded.
        
        This is used for refunds (return/dispute), not for cancellations.
        
        Args:
            order_id: Order ID
            idempotency_key: Unique key for idempotency
            refund_reason: Optional reason for refund
            
        Returns:
            Tuple of (success: bool, refund_tx: Transaction, error: str)
        """
        from wallet.models import Wallet, Transaction
        from .models import Order, OrderItem
        
        # Get order
        try:
            order = Order.objects.select_for_update().get(id=order_id)
        except Order.DoesNotExist:
            return (False, None, f"Order {order_id} not found")
        
        # Validate order has been paid (not COD or pending)
        if order.payment_method == 'cod':
            return (False, None, f"Cannot refund COD order {order_id} - no payment was made")
        
        # Get completed payment transaction
        try:
            payment_tx = Transaction.objects.select_for_update().get(
                reference_id=str(order_id),
                transaction_type='payment',
                status='completed'
            )
        except Transaction.DoesNotExist:
            return (False, None, f"No completed payment found for order {order_id}")
        
        # Check idempotency for refund
        if Transaction.objects.filter(
            reference_id=str(order_id),
            transaction_type='refund',
            idempotency_key=idempotency_key
        ).exists():
            existing_refund = Transaction.objects.get(
                reference_id=str(order_id),
                transaction_type='refund',
                idempotency_key=idempotency_key
            )
            return (True, existing_refund, None)
        
        # Get wallet
        wallet = Wallet.objects.select_for_update().get(id=payment_tx.wallet.id)
        
        # Mark original payment as refunded
        payment_tx.status = 'refunded'
        payment_tx.save()
        
        # Create refund transaction
        refund_tx = Transaction.objects.create(
            wallet=wallet,
            amount=payment_tx.amount,
            transaction_type='refund',
            reference_id=str(order_id),
            description=refund_reason or f"Refund for order #{order_id}",
            status='completed',
            balance_before=wallet.balance,
            balance_after=wallet.balance + payment_tx.amount,
            idempotency_key=idempotency_key
        )
        
        # Update wallet balance
        wallet.balance += payment_tx.amount
        wallet.save()
        
        # Release stock for all items and update reservation_status
        for item in OrderItem.objects.filter(order_id=order_id):
            # Get variant_id from OrderItem
            variant_id = item.variant_id
            
            # Release stock
            StockLockManager.release_stock(
                product_id=item.product.id,
                quantity=item.quantity,
                variant_id=variant_id
            )
            
            # Update reservation status to released
            item.reservation_status = 'released'
            item.save()
        
        # Update order status to 'refunded'
        order.status = 'refunded'
        order.save()
        
        logger.info(
            f"Refunded {payment_tx.amount} to wallet {wallet.id} for order {order_id}. "
            f"Reason: {refund_reason or 'Not specified'}. "
            f"Stock released for {OrderItem.objects.filter(order_id=order_id).count()} items."
        )
        return (True, refund_tx, None)


class AtomicOrderCreator:
    """
    Creates orders atomically with proper locking and idempotency.

    This is the main entry point for order creation, ensuring:
    1. No duplicate orders (idempotency)
    2. No overselling (stock locking)
    3. Financial consistency (wallet-order atomicity)
    4. Complete rollback on any failure

    Spec 004 C.3: variant_id ALWAYS references ProductCategoryVariantOption.id
    - Validates variant_id references ProductCategoryVariantOption
    - Falls back to ProductVariant for legacy orders (with deprecation warning)
    """
    
    @staticmethod
    @transaction.atomic
    def create_order(
        user,
        items_data: List[Dict],
        shipping_address: str,
        shipping_cost: Decimal,
        payment_method: str,
        idempotency_key: str,
        use_wallet_payment: bool = False
    ) -> Tuple:
        """
        Create an order atomically with all safety checks.
        
        This method:
        1. Checks idempotency (prevents duplicate orders)
        2. Locks all products involved
        3. Checks stock availability AFTER locks
        4. Reserves stock atomically
        5. Determines initial state based on payment method
        6. Calculates payment timeout for non-COD orders
        7. Creates order with appropriate initial status
        8. Creates order items
        9. Optionally reserves wallet payment
        10. All-or-nothing: rolls back on any failure
        
        Args:
            user: User object
            items_data: List of dicts with product_id, quantity, variant_id
            shipping_address: Shipping address
            shipping_cost: Shipping cost
            payment_method: Payment method
            idempotency_key: Unique key for idempotency
            use_wallet_payment: Whether to use wallet for payment
            
        Returns:
            Tuple of (success: bool, order: Order, error: str)
        """
        from .models import Order, OrderItem
        from products.models import Product
        from wallet.models import Wallet
        
        # Step 1: Check idempotency
        if Order.objects.filter(idempotency_key=idempotency_key).exists():
            existing_order = Order.objects.get(idempotency_key=idempotency_key)
            return (True, existing_order, None)
        
        # Step 2: Validate all items exist and calculate total
        total_amount = Decimal('0')
        validated_items = []
        unapproved_products = []

        for item_data in items_data:
            product_id = item_data['product_id']
            quantity = item_data['quantity']
            variant_id = item_data.get('variant_id')

            try:
                product = Product.objects.get(id=product_id, is_active=True)
            except Product.DoesNotExist:
                raise ValueError(f"Product {product_id} not found or inactive")

            # Spec 004 INV-012: Unapproved products cannot be in orders
            # Check approval_status and collect unapproved products
            if product.approval_status != 'approved':
                unapproved_products.append({
                    'product_id': product_id,
                    'name': product.name,
                    'approval_status': product.approval_status
                })
            
            # Calculate price
            if variant_id:
                # Variant pricing - Spec 004 C.3: variant_id references ProductCategoryVariantOption.id
                from products.models import ProductCategoryVariantOption, ProductVariant
                try:
                    variant = ProductCategoryVariantOption.objects.get(
                        id=variant_id,
                        product_id=product_id,
                        is_active=True
                    )
                    price = variant.final_price
                except ProductCategoryVariantOption.DoesNotExist:
                    # Try ProductVariant as fallback for legacy orders (DEPRECATED)
                    _log_deprecated_variant_usage(variant_id, "order creation (fallback)")
                    try:
                        variant = ProductVariant.objects.get(
                            id=variant_id,
                            product_id=product_id,
                            is_active=True
                        )
                        price = variant.final_price
                    except ProductVariant.DoesNotExist:
                        raise ValueError(f"Variant {variant_id} not found for product {product_id}")
            else:
                # Base product pricing
                price = product.base_price
            
            item_total = price * quantity
            total_amount += item_total
            
            validated_items.append({
                'product': product,
                'quantity': quantity,
                'variant_id': variant_id,
                'price': price,
                'item_total': item_total
            })

        # Spec 004 INV-012: Hard-fail if any products are not approved
        if unapproved_products:
            raise ProductVisibilityError(
                f"Order contains {len(unapproved_products)} product(s) that are not approved. "
                "All products must be approved before ordering.",
                unapproved_products=unapproved_products
            )

        # Add shipping cost
        total_amount += shipping_cost
        
        # Step 3: Reserve stock for all items (with locks)
        # Stock reservation is now done inline to ensure atomicity with order creation
        # We lock products one by one to prevent deadlocks, but all in same transaction
        for item in validated_items:
            if item['variant_id']:
                # Variant product stock reservation (inline, no separate transaction)
                from products.models import ProductCategoryVariantOption, ProductVariant
                try:
                    # Try ProductCategoryVariantOption first
                    variant = ProductCategoryVariantOption.objects.select_for_update().get(
                        id=item['variant_id'],
                        product_id=item['product'].id,
                        is_active=True
                    )
                    
                    if variant.stock_count < item['quantity']:
                        raise ValueError(
                            f"Insufficient stock for variant. Available: {variant.stock_count}, Requested: {item['quantity']}"
                        )
                    
                    # Decrement stock
                    variant.stock_count -= item['quantity']
                    variant.save()
                    
                    logger.info(f"Reserved {item['quantity']} units of variant {item['variant_id']} for product {item['product'].id}")
                    
                except ProductCategoryVariantOption.DoesNotExist:
                    # Try ProductVariant as fallback (DEPRECATED per Spec 004 C.1)
                    _log_deprecated_variant_usage(item['variant_id'], "order creation stock reservation (fallback)")
                    try:
                        variant = ProductVariant.objects.select_for_update().get(
                            id=item['variant_id'],
                            product_id=item['product'].id,
                            is_active=True
                        )

                        if variant.stock_count < item['quantity']:
                            raise ValueError(
                                f"Insufficient stock for variant. Available: {variant.stock_count}, Requested: {item['quantity']}"
                            )

                        variant.stock_count -= item['quantity']
                        variant.save()

                        logger.info(f"Reserved {item['quantity']} units of variant {item['variant_id']} for product {item['product'].id}")

                    except ProductVariant.DoesNotExist:
                        raise ValueError(f"Variant {item['variant_id']} not found for product {item['product'].id}")
            else:
                # Non-variant product stock reservation (inline, no separate transaction)
                try:
                    product = Product.objects.select_for_update().get(
                        id=item['product'].id,
                        is_active=True
                    )
                    
                    # Check stock AFTER acquiring lock
                    available_stock = product.stock_quantity
                    
                    if available_stock < item['quantity']:
                        raise ValueError(
                            f"Insufficient stock for product '{item['product'].name}'. "
                            f"Available: {available_stock}, Requested: {item['quantity']}"
                        )
                    
                    # Decrement stock
                    product.stock_quantity = available_stock - item['quantity']
                    product.save()
                    
                    logger.info(f"Reserved {item['quantity']} units of product {item['product'].id}")
                    
                except Product.DoesNotExist:
                    raise ValueError(f"Product {item['product'].id} not found")
        
        # Step 4: Determine initial state based on payment method
        initial_status = OrderStateMachine.get_initial_state(payment_method)
        
        # Step 5: Calculate payment timeout for non-COD orders
        payment_timeout_at = None
        if payment_method != 'cod':
            from django.utils import timezone
            from datetime import timedelta
            payment_timeout_at = timezone.now() + timedelta(minutes=15)
        
        # Step 6: Create order
        order = Order.objects.create(
            user=user,
            total_amount=total_amount,
            shipping_address=shipping_address,
            shipping_cost=shipping_cost,
            payment_method=payment_method,
            status=initial_status,
            payment_status=False,
            idempotency_key=idempotency_key,
            payment_timeout_at=payment_timeout_at
        )
        
        # Step 7: Create order items
        for item in validated_items:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
                price=item['price'],
                seller=item['product'].seller,
                reservation_status='reserved'
            )

        # Step 8: Reserve wallet payment if requested
        if use_wallet_payment:
            try:
                wallet = Wallet.objects.get(user=user)
                success, tx, error = WalletOrderCoordinator.reserve_payment(
                    wallet=wallet,
                    amount=total_amount,
                    order_id=order.id,
                    idempotency_key=f"payment_{idempotency_key}",
                    description=f"Order #{order.id}"
                )

                if not success:
                    raise ValueError(f"Payment reservation failed: {error}")

            except Wallet.DoesNotExist:
                raise ValueError("Wallet not found for user")
        
        logger.info(f"Created order {order.id} for user {user.id} with idempotency key {idempotency_key}")
        return (True, order, None)
    
    @staticmethod
    @transaction.atomic
    def cancel_order(order_id: int, user=None, reason: str = None) -> Tuple:
        """
        Cancel an order atomically with proper rollback.
        
        This method:
        1. Validates order belongs to user (if user provided)
        2. Validates order can be cancelled
        3. Releases all reserved stock
        4. Refunds payment if order was paid (not for COD orders)
        5. Updates order status to CANCELLED
        6. All-or-nothing: rolls back on any failure
        
        Args:
            order_id: Order ID to cancel
            user: User requesting cancellation (None for system-initiated)
            reason: Optional reason for cancellation
            
        Returns:
            Tuple of (success: bool, order: Order, error: str)
        """
        from .models import Order
        
        # Get order with lock
        try:
            order = Order.objects.select_for_update().get(id=order_id)
        except Order.DoesNotExist:
            return (False, None, f"Order {order_id} not found")
        
        # Validate ownership (skip for system-initiated cancellations)
        if user is not None and order.user != user:
            return (False, None, "You don't have permission to cancel this order")
        
        # Validate state
        if not OrderStateMachine.can_cancel(order.status):
            return (False, None, f"Cannot cancel order with status '{order.status}'")
        
        # Release stock for all items and update reservation_status
        for item in order.items.all():
            # Get variant_id from OrderItem
            variant_id = item.variant_id
            
            # Release stock
            StockLockManager.release_stock(
                product_id=item.product.id,
                quantity=item.quantity,
                variant_id=variant_id
            )
            
            # Update reservation status to released
            item.reservation_status = 'released'
            item.save()
        
        # Refund payment if order was paid (not COD orders)
        if order.status == 'paid':
            refund_reason = reason or f"Order #{order_id} cancelled by user"
            success, refund_tx, error = WalletOrderCoordinator.release_payment(
                order_id=order_id,
                idempotency_key=order.idempotency_key or f"cancel_{order.id}",
                refund_reason=refund_reason
            )
            
            if not success:
                # This shouldn't happen, but log it
                logger.error(f"Failed to refund payment for order {order_id}: {error}")
        elif order.payment_method == 'cod':
            # COD orders don't require refund - no payment was made
            logger.info(f"COD order {order_id} cancelled - no refund needed")
        
        # Update order status
        order.status = 'cancelled'
        order.save()
        
        log_message = f"Cancelled order {order_id}"
        if user is not None:
            log_message += f" by user {user.id}"
        if reason:
            log_message += f". Reason: {reason}"
        logger.info(log_message)
        return (True, order, None)
    
    @staticmethod
    @transaction.atomic
    def confirm_cod_delivery(order_id: int) -> Tuple:
        """
        Confirm COD order delivery and mark as paid.
        
        For COD orders, delivery confirms payment collection.
        This method:
        1. Validates order is a COD order in 'delivered' status
        2. Commits stock (marks reservation_status as 'committed')
        3. Sets payment_status to True
        4. Transitions order to 'completed'
        
        Args:
            order_id: Order ID to confirm delivery for
            
        Returns:
            Tuple of (success: bool, order: Order, error: str)
        """
        from .models import Order
        
        # Get order with lock
        try:
            order = Order.objects.select_for_update().get(id=order_id)
        except Order.DoesNotExist:
            return (False, None, f"Order {order_id} not found")
        
        # Validate order is COD and in delivered status
        if order.payment_method != 'cod':
            return (False, None, f"Order {order_id} is not a COD order")
        
        if order.status != 'delivered':
            return (False, None, f"Order {order_id} must be in 'delivered' status to confirm payment")
        
        # Commit stock (mark reservation_status as 'committed')
        StockLockManager.commit_stock(order_id=order_id)
        
        # Mark as paid
        order.payment_status = True
        order.status = 'completed'
        order.save()
        
        logger.info(f"Confirmed COD delivery for order {order_id}, marked as paid and completed")
        return (True, order, None)

    @staticmethod
    @transaction.atomic
    def update_order_status_from_items(order_id: int) -> Tuple:
        """
        Update order status based on aggregated item statuses.

        This method:
        1. Gets the order with lock
        2. Aggregates status from all item statuses
        3. Validates the transition is allowed
        4. Updates the order status

        Args:
            order_id: Order ID to update

        Returns:
            Tuple of (success: bool, order: Order, error: str)
        """
        from .models import Order
        from .services.multi_seller import aggregate_order_status

        try:
            # Get order with lock
            order = Order.objects.select_for_update().get(id=order_id)

            # Get aggregated status from items
            new_status = aggregate_order_status(order)

            # Validate transition
            OrderStateMachine.validate_transition(order.status, new_status)

            # Update order status
            order.status = new_status
            order.save()

            logger.info(
                f"Updated order {order_id} status from '{order.status}' to '{new_status}' "
                f"based on item aggregation"
            )

            return (True, order, None)

        except Order.DoesNotExist:
            return (False, None, f"Order {order_id} not found")
        except ValueError as e:
            # Invalid state transition
            return (False, None, str(e))
        except Exception as e:
            logger.error(f"Failed to update order {order_id} status from items: {e}")
            return (False, None, f"Failed to update order status: {str(e)}")
