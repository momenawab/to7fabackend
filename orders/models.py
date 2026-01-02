from django.db import models
from django.conf import settings
from django.db.models import Q
from decimal import Decimal

class Order(models.Model):
    """
    Order model with atomic transaction support.
    
    Status transitions are enforced by OrderStateMachine:
    - PENDING -> PAID (payment captured)
    - PENDING -> CANCELLED (user cancelled)
    - PAID -> SHIPPED (seller shipped)
    - PAID -> CANCELLED (refund required)
    - SHIPPED -> COMPLETED (delivery confirmed)
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),      # Stock reserved, awaiting payment
        ('paid', 'Paid'),            # Payment captured, awaiting shipping
        ('shipped', 'Shipped'),      # Order shipped by seller
        ('completed', 'Completed'),    # Order delivered and confirmed
        ('cancelled', 'Cancelled'),   # Order cancelled, stock refunded
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    shipping_address = models.TextField()
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    payment_method = models.CharField(max_length=50)
    payment_status = models.BooleanField(default=False)
    idempotency_key = models.CharField(max_length=255, unique=True, null=True, blank=True, db_index=True,
                                    help_text="Unique key to prevent duplicate orders from retries")
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
        ]


class OrderItem(models.Model):
    """
    Order item with variant support.
    
    Tracks individual products in an order, including:
    - Variant information for proper stock management
    - Price at time of purchase
    - Commission calculation
    """
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
                                     help_text="ID of the product variant ordered")
    
    class Meta:
        indexes = [
            models.Index(fields=['order', 'product']),
            models.Index(fields=['seller']),
            models.Index(fields=['variant_id']),
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
