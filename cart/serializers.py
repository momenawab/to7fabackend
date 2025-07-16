from rest_framework import serializers
from .models import Cart, CartItem
from products.models import Product

class ProductMinimalSerializer(serializers.ModelSerializer):
    """Minimal product information for cart display"""
    seller_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'stock', 'seller_name']
        read_only_fields = fields


class CartItemSerializer(serializers.ModelSerializer):
    """Serializer for cart items"""
    product = ProductMinimalSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    line_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity', 'line_total', 'added_at', 'updated_at']
        read_only_fields = ['id', 'line_total', 'added_at', 'updated_at']
    
    def validate_product_id(self, value):
        """Validate that the product exists and is active"""
        try:
            product = Product.objects.get(id=value, is_active=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found or inactive")
        return value
    
    def validate_quantity(self, value):
        """Validate that the quantity is positive"""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be positive")
        return value
    
    def validate(self, data):
        """Validate that there's enough stock"""
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)
        
        try:
            product = Product.objects.get(id=product_id)
            if product.stock < quantity:
                raise serializers.ValidationError(
                    {"quantity": f"Not enough stock available. Only {product.stock} items left."}
                )
        except Product.DoesNotExist:
            # This will be caught by validate_product_id
            pass
            
        return data


class CartSerializer(serializers.ModelSerializer):
    """Serializer for shopping cart"""
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total_items', 'subtotal', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class AddToCartSerializer(serializers.Serializer):
    """Serializer for adding items to cart"""
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(default=1, min_value=1)
    
    def validate_product_id(self, value):
        """Validate that the product exists and is active"""
        try:
            product = Product.objects.get(id=value, is_active=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found or inactive")
        return value
    
    def validate(self, data):
        """Validate that there's enough stock"""
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)
        
        try:
            product = Product.objects.get(id=product_id)
            if product.stock < quantity:
                raise serializers.ValidationError(
                    {"quantity": f"Not enough stock available. Only {product.stock} items left."}
                )
        except Product.DoesNotExist:
            # This will be caught by validate_product_id
            pass
            
        return data


class UpdateCartItemSerializer(serializers.Serializer):
    """Serializer for updating cart item quantity"""
    quantity = serializers.IntegerField(min_value=0)
    
    def validate(self, data):
        """Validate that there's enough stock"""
        quantity = data.get('quantity', 0)
        
        # Skip validation if removing item (quantity=0)
        if quantity == 0:
            return data
            
        # Get product from context
        product = self.context.get('product')
        if product and product.stock < quantity:
            raise serializers.ValidationError(
                {"quantity": f"Not enough stock available. Only {product.stock} items left."}
            )
            
        return data 