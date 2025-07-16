from django.db import models
from django.conf import settings
from django.db.models import Q
from decimal import Decimal

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    shipping_address = models.TextField()
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    payment_method = models.CharField(max_length=50)
    payment_status = models.BooleanField(default=False)
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


class OrderItem(models.Model):
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
