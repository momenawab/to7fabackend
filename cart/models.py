from django.db import models
from django.conf import settings
from products.models import Product
from decimal import Decimal


def get_available_stock(product, variant_id=None):
    """
    Resolve the authoritative available stock for a cart operation.

    Phase 2 fix (BACKEND_AUDIT.md #cart-variant-stock): cart operations previously
    checked `product.stock` - the SUM across all of a product's variants - even when a
    specific variant_id was selected. That let a customer add more of one variant than
    that variant actually had in stock, as long as some OTHER variant's stock made the
    aggregate look sufficient.

    Spec 004 C.6: variant_id (when present) references ProductCategoryVariantOption.id
    and is the source of truth for inventory - not the product's aggregate stock.
    """
    if variant_id:
        from products.models import ProductCategoryVariantOption
        try:
            variant = ProductCategoryVariantOption.objects.get(
                id=variant_id, product=product, is_active=True
            )
        except ProductCategoryVariantOption.DoesNotExist:
            raise ValueError(f"Variant {variant_id} not found for this product")
        return variant.stock_count
    return product.stock


class Cart(models.Model):
    """Shopping cart model"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart', null=True, blank=True)
    session_id = models.CharField(max_length=36, null=True, blank=True, db_index=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(user__isnull=False) | models.Q(session_id__isnull=False),
                name='cart_user_or_session_required'
            )
        ]
    
    def __str__(self):
        if self.user:
            return f"Cart for {self.user.email}"
        return f"Guest cart (session: {self.session_id})"
    
    @property
    def total_items(self):
        """Get the total number of items in the cart"""
        return sum(item.quantity for item in self.items.all())
    
    @property
    def subtotal(self):
        """Calculate the subtotal of all items in the cart"""
        return sum(item.line_total for item in self.items.all())
    
    def add_item(self, product, quantity=1, selected_variants=None, variant_id=None):
        """Add a product to the cart or update quantity if already exists"""
        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        available_stock = get_available_stock(product, variant_id)
        if available_stock < quantity:
            raise ValueError(f"Not enough stock available. Only {available_stock} items left.")

        # For variant products, check if exact variant combination already exists
        if selected_variants or variant_id:
            existing_items = self.items.filter(
                product=product,
                selected_variants=selected_variants,
                variant_id=variant_id
            )
            if existing_items.exists():
                cart_item = existing_items.first()
                cart_item.quantity += quantity
                if cart_item.quantity > available_stock:
                    raise ValueError(f"Not enough stock available. Only {available_stock} items left.")
                cart_item.save()
            else:
                cart_item = CartItem.objects.create(
                    cart=self,
                    product=product,
                    quantity=quantity,
                    selected_variants=selected_variants,
                    variant_id=variant_id
                )
        else:
            # Regular product without variants
            cart_item, created = CartItem.objects.get_or_create(
                cart=self,
                product=product,
                selected_variants=None,
                variant_id=None,
                defaults={'quantity': quantity}
            )

            if not created:
                # Item already exists, update quantity
                cart_item.quantity += quantity
                if cart_item.quantity > available_stock:
                    raise ValueError(f"Not enough stock available. Only {available_stock} items left.")
                cart_item.save()

        self.save()  # Update cart timestamp
        return cart_item
    
    def update_item_by_id(self, cart_item_id, quantity):
        """Update the quantity of a specific cart item by ID"""
        if quantity <= 0:
            return self.remove_item_by_id(cart_item_id)
            
        try:
            cart_item = self.items.get(id=cart_item_id)

            available_stock = get_available_stock(cart_item.product, cart_item.variant_id)
            if available_stock < quantity:
                raise ValueError(f"Not enough stock available. Only {available_stock} items left.")

            cart_item.quantity = quantity
            cart_item.save()
            self.save()  # Update cart timestamp
            return cart_item
        except CartItem.DoesNotExist:
            raise ValueError("Cart item not found")
    
    def remove_item_by_id(self, cart_item_id):
        """Remove a specific cart item by ID"""
        try:
            cart_item = self.items.get(id=cart_item_id)
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
    """
    Individual item in a cart.

    Spec 004 C.6: variant_id is the source of truth for inventory operations.
    selected_variants is DEPRECATED for display/UI purposes only (not for inventory).
    """
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    selected_variants = models.JSONField(null=True, blank=True, help_text="DEPRECATED: Display only. Use variant_id for inventory (Spec 004 C.6)")
    variant_id = models.IntegerField(null=True, blank=True, help_text="ProductCategoryVariantOption.id for inventory operations (Spec 004 C.6)")
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        # Remove unique_together since we now allow same product with different variants
        pass
        
    def __str__(self):
        return f"{self.quantity} x {self.product.name} in {self.cart}"
    
    @property
    def line_total(self):
        """Calculate the total price for this item"""
        # Check if product has an active offer
        from django.utils import timezone
        now = timezone.now()
        
        # Get active offer for this product
        active_offer = self.product.offers.filter(
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        ).first()
        
        if active_offer:
            # Use offer price if available
            price_per_item = active_offer.offer_price
        else:
            # Use regular price
            price_per_item = self.product.price
            
        return Decimal(self.quantity) * Decimal(price_per_item)
    
    @property
    def current_price(self):
        """Get the current price per item (offer price if available, regular price otherwise)"""
        from django.utils import timezone
        now = timezone.now()
        
        # Get active offer for this product
        active_offer = self.product.offers.filter(
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        ).first()
        
        if active_offer:
            return active_offer.offer_price
        else:
            return self.product.price
