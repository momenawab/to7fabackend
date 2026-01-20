from django.db import models
from django.conf import settings
from django.db.models import Q
from decimal import Decimal

class Order(models.Model):
    """
    Order model with atomic transaction support.
    
    Status transitions are enforced by OrderStateMachine.
    Extended state machine with 10 states:
    - pending_payment -> paid (payment captured)
    - pending_payment -> cancelled/failed (timeout or user cancelled)
    - cod_pending -> processing (seller acknowledged)
    - paid -> processing -> shipped -> delivered -> completed
    - paid/cod_pending/processing/shipped/delivered -> cancelled (refund if paid)
    - paid/processing/shipped/delivered/completed -> refunded
    """
    STATUS_CHOICES = (
        ('pending_payment', 'Pending Payment'),     # Online payment orders awaiting payment
        ('cod_pending', 'COD Pending'),            # COD orders awaiting processing
        ('paid', 'Paid'),                          # Payment captured, awaiting shipping
        ('processing', 'Processing'),              # Seller acknowledged, preparing order
        ('shipped', 'Shipped'),                    # Order shipped by seller
        ('delivered', 'Delivered'),                # Order delivered to customer
        ('completed', 'Completed'),                # Order fulfilled
        ('cancelled', 'Cancelled'),                # Order cancelled, stock refunded
        ('refunded', 'Refunded'),                  # Payment returned to customer
        ('failed', 'Failed'),                      # Payment failed
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_payment')
    shipping_address = models.TextField()
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    payment_method = models.CharField(max_length=50)
    payment_status = models.BooleanField(default=False)
    idempotency_key = models.CharField(max_length=255, unique=True, null=True, blank=True, db_index=True,
                                    help_text="Unique key to prevent duplicate orders from retries")
    payment_timeout_at = models.DateTimeField(null=True, blank=True,
                                         help_text="Auto-cancel deadline for pending payment orders")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Order #{self.id} by {self.user.email}"
    
    @property
    def items_count(self):
        return self.items.count()
    
    @property
    def subtotal(self):
        return sum((item.price * item.quantity) for item in self.items.all())
    
    class Meta:
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['idempotency_key']),
            models.Index(fields=['status', 'payment_timeout_at'], name='order_timeout_idx'),
        ]


class OrderItem(models.Model):
    """
    Order item with variant support.
    
    Tracks individual products in an order, including:
    - Variant information for proper stock management
    - Price at time of purchase
    - Commission calculation
    - Per-item fulfillment status
    - Stock reservation tracking
    """
    ITEM_STATUS_CHOICES = (
        ('pending', 'Pending'),           # Awaiting seller action
        ('processing', 'Processing'),     # Seller preparing
        ('shipped', 'Shipped'),           # Dispatched by seller
        ('delivered', 'Delivered'),       # Received by customer
        ('completed', 'Completed'),       # Fulfilled
        ('cancelled', 'Cancelled'),       # Cancelled
    )

    RESERVATION_STATUS_CHOICES = (
        ('reserved', 'Reserved'),         # Stock held for order
        ('released', 'Released'),         # Stock returned (cancel/fail)
        ('committed', 'Committed'),       # Stock permanently decremented
    )

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of purchase
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sold_items',
        limit_choices_to=Q(user_type='artist') | Q(user_type='store')
    )
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('10.00'))  # Platform commission in percentage
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    # Variant support for proper stock management
    variant_id = models.PositiveIntegerField(null=True, blank=True,
                                     help_text="ID of product variant ordered")

    # Per-item fulfillment status
    item_status = models.CharField(
        max_length=20,
        choices=ITEM_STATUS_CHOICES,
        default='pending',
        help_text="Fulfillment status of this order item"
    )

    # Stock reservation tracking
    reservation_status = models.CharField(
        max_length=20,
        choices=RESERVATION_STATUS_CHOICES,
        default='reserved',
        help_text="Stock reservation state for this item"
    )

    class Meta:
        indexes = [
            models.Index(fields=['order', 'product']),
            models.Index(fields=['seller']),
            models.Index(fields=['variant_id']),
            models.Index(fields=['item_status'], name='orderitem_status_idx'),
        ]
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Order #{self.order.id}"
    
    def save(self, *args, **kwargs):
        # Calculate commission amount before saving
        if not self.commission_amount:
            self.commission_amount = (self.price * self.quantity) * (self.commission_rate / Decimal('100'))
        super().save(*args, **kwargs)
        
    @property
    def seller_name(self):
        if self.seller.user_type == 'artist':
            try:
                return f"Artist: {self.seller.first_name} {self.seller.last_name}"
            except:
                return f"Artist: {self.seller.email}"
        elif self.seller.user_type == 'store':
            try:
                return f"Store: {self.seller.store_profile.store_name}"
            except:
                return f"Store: {self.seller.email}"
        return self.seller.email
