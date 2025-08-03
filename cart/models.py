from django.db import models
from django.conf import settings
from products.models import Product
from decimal import Decimal

class Cart(models.Model):
    """Shopping cart model"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Cart for {self.user.email}"
    
    @property
    def total_items(self):
        """Get the total number of items in the cart"""
        return sum(item.quantity for item in self.items.all())
    
    @property
    def subtotal(self):
        """Calculate the subtotal of all items in the cart"""
        return sum(item.line_total for item in self.items.all())
    
    def add_item(self, product, quantity=1):
        """Add a product to the cart or update quantity if already exists"""
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
            
        if product.stock < quantity:
            raise ValueError(f"Not enough stock available. Only {product.stock} items left.")
            
        cart_item, created = CartItem.objects.get_or_create(
            cart=self,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            # Item already exists, update quantity
            cart_item.quantity += quantity
            if cart_item.quantity > product.stock:
                raise ValueError(f"Not enough stock available. Only {product.stock} items left.")
            cart_item.save()
            
        self.save()  # Update cart timestamp
        return cart_item
    
    def update_item(self, product, quantity):
        """Update the quantity of a product in the cart"""
        if quantity <= 0:
            return self.remove_item(product)
            
        try:
            cart_item = self.items.get(product=product)
            
            if product.stock < quantity:
                raise ValueError(f"Not enough stock available. Only {product.stock} items left.")
                
            cart_item.quantity = quantity
            cart_item.save()
            self.save()  # Update cart timestamp
            return cart_item
        except CartItem.DoesNotExist:
            return self.add_item(product, quantity)
    
    def remove_item(self, product):
        """Remove a product from the cart"""
        try:
            cart_item = self.items.get(product=product)
            cart_item.delete()
            self.save()  # Update cart timestamp
            return True
        except CartItem.DoesNotExist:
            return False
    
    def clear(self):
        """Remove all items from the cart"""
        self.items.all().delete()
        self.save()  # Update cart timestamp
        return True


class CartItem(models.Model):
    """Individual item in a cart"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('cart', 'product')
        
    def __str__(self):
        return f"{self.quantity} x {self.product.name} in {self.cart}"
    
    @property
    def line_total(self):
        """Calculate the total price for this item"""
        return Decimal(self.quantity) * self.product.price
