"""
Celery Tasks for Orders App

This module defines asynchronous tasks for order-related operations,
including payment timeout handling and periodic maintenance tasks.
"""

from celery import shared_task
from django.utils import timezone
from django.db import transaction, models as django_models
import logging

from orders.models import Order, OrderItem
from orders.atomic_order_system import AtomicOrderCreator

logger = logging.getLogger(__name__)


@shared_task(bind=True, name='orders.tasks.check_payment_timeouts')
def check_payment_timeouts(self):
    """
    Check for and cancel orders that have exceeded their payment timeout.
    
    This task runs periodically (every 60 seconds via Celery beat) to find
    orders in 'pending_payment' status whose payment_timeout_at has passed.
    It cancels these orders and releases any held stock and wallet funds.
    
    Uses select_for_update(skip_locked=True) to handle concurrent execution
    safely without blocking other workers.
    
    Returns:
        dict: Summary of processed orders
    """
    logger.info("Starting payment timeout check...")
    
    # Find orders that have timed out
    # Use select_for_update(skip_locked=True) to handle concurrent workers
    expired_orders = Order.objects.filter(
        status='pending_payment',
        payment_timeout_at__lte=timezone.now()
    ).select_for_update(skip_locked=True)
    
    cancelled_count = 0
    failed_count = 0
    
    for order in expired_orders:
        try:
            with transaction.atomic():
                # Cancel the order using the atomic order creator
                # This will release stock and wallet holds atomically
                AtomicOrderCreator.cancel_order(
                    order_id=order.id,
                    user=None,  # System-initiated cancellation
                    reason='Payment timeout - order expired'
                )
                
                cancelled_count += 1
                logger.info(
                    f"Cancelled order {order.id} due to payment timeout. "
                    f"Timeout was: {order.payment_timeout_at}"
                )
                
        except Exception as e:
            failed_count += 1
            logger.error(
                f"Failed to cancel order {order.id} due to payment timeout: {str(e)}",
                exc_info=True
            )
    
    logger.info(
        f"Payment timeout check completed. "
        f"Cancelled: {cancelled_count}, Failed: {failed_count}"
    )
    
    return {
        'cancelled': cancelled_count,
        'failed': failed_count,
        'processed': cancelled_count + failed_count
    }


@shared_task(bind=True, name='orders.tasks.cleanup_cancelled_orders')
def cleanup_cancelled_orders(self, days_old=30):
    """
    Archive or clean up cancelled orders older than specified days.
    
    This is a maintenance task to keep the database clean by
    archiving or soft-deleting old cancelled orders.
    
    Args:
        days_old (int): Number of days old for orders to be cleaned up (default: 30)
    
    Returns:
        dict: Summary of cleaned up orders
    """
    logger.info(f"Starting cleanup of cancelled orders older than {days_old} days...")
    
    cutoff_date = timezone.now() - timezone.timedelta(days=days_old)
    
    # Find cancelled orders older than cutoff date
    old_cancelled_orders = Order.objects.filter(
        status='cancelled',
        updated_at__lt=cutoff_date
    )
    
    count = old_cancelled_orders.count()
    
    # In production, you might want to archive these instead of deleting
    # For now, we'll just log the count
    logger.info(
        f"Found {count} cancelled orders older than {days_old} days. "
        f"Consider archiving or soft-deleting."
    )
    
    return {
        'found': count,
        'cutoff_date': cutoff_date.isoformat()
    }


@shared_task(bind=True, name='orders.tasks.update_order_aggregations')
def update_order_aggregations(self):
    """
    Update order-level status based on item-level statuses for multi-seller orders.
    
    This task ensures that order status correctly reflects the aggregated
    status of all items in multi-seller orders.
    
    Returns:
        dict: Summary of updated orders
    """
    logger.info("Starting order aggregation update...")
    
    # Find orders with multiple items (potential multi-seller)
    multi_item_orders = Order.objects.annotate(
        item_count=django_models.Count('items')
    ).filter(item_count__gt=1)
    
    updated_count = 0
    
    for order in multi_item_orders:
        try:
            # Import here to avoid circular dependency
            from orders.services.multi_seller import aggregate_order_status
            
            new_status = aggregate_order_status(order)
            
            if new_status != order.status:
                order.status = new_status
                order.save(update_fields=['status'])
                updated_count += 1
                logger.info(
                    f"Updated order {order.id} status to {new_status} "
                    f"based on item aggregation"
                )
                
        except Exception as e:
            logger.error(
                f"Failed to update aggregation for order {order.id}: {str(e)}",
                exc_info=True
            )
    
    logger.info(
        f"Order aggregation update completed. "
        f"Updated: {updated_count}"
    )
    
    return {
        'updated': updated_count,
        'processed': multi_item_orders.count()
    }
