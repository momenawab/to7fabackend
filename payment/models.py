from django.db import models
from django.conf import settings

# Create your models here.

class PaymentMethod(models.Model):
    METHOD_CHOICES = (
        ('credit_card', 'Credit Card'),
        ('wallet', 'Wallet'),
        ('cash_on_delivery', 'Cash on Delivery'),
        ('bank_transfer', 'Bank Transfer'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payment_methods')
    method_type = models.CharField(max_length=20, choices=METHOD_CHOICES)
    is_default = models.BooleanField(default=False)
    details = models.JSONField(default=dict)  # Store method-specific details
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_method_type_display()} for {self.user.email}"
    
    def save(self, *args, **kwargs):
        # If this is set as default, unset default for other payment methods
        if self.is_default:
            PaymentMethod.objects.filter(
                user=self.user, 
                is_default=True
            ).exclude(id=self.id).update(is_default=False)
        super().save(*args, **kwargs)


class Payment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    order = models.OneToOneField('orders.Order', on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True)
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    gateway_response = models.JSONField(default=dict, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Payment of {self.amount} for Order #{self.order.id}"
    
    def process_payment(self):
        """Process the payment through the appropriate gateway"""
        # This would integrate with Paymob or other payment gateway
        # For now, we'll just mark it as completed
        self.status = 'completed'
        self.save()
        
        # Update order payment status
        self.order.payment_status = True
        self.order.save()
        
        return True
    
    def refund_payment(self, amount=None):
        """Process a refund for this payment"""
        refund_amount = amount or self.amount
        
        # This would integrate with payment gateway's refund API
        # For now, we'll just mark it as refunded
        self.status = 'refunded'
        self.save()
        
        return True
