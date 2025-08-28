from rest_framework import serializers
from .models import Cart, CartItem
from products.models import Product

class ProductMinimalSerializer(serializers.ModelSerializer):
    """Minimal product information for cart display"""
    seller_name = serializers.CharField(read_only=True)
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'stock', 'seller_name', 'image']
        read_only_fields = fields
        
    def get_image(self, obj):
        """Get primary product image URL"""
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(primary_image.image.url)
            return primary_image.image.url
        
        # Fallback to first image if no primary
        first_image = obj.images.first()
        if first_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(first_image.image.url)
            return first_image.image.url
        
        return None


class CartItemSerializer(serializers.ModelSerializer):
    """Serializer for cart items"""
    product = ProductMinimalSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    line_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    current_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    has_offer = serializers.SerializerMethodField()
    original_price = serializers.SerializerMethodField()
    
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity', 'selected_variants', 'variant_id', 'line_total', 'current_price', 'has_offer', 'original_price', 'added_at', 'updated_at']
        read_only_fields = ['id', 'line_total', 'current_price', 'has_offer', 'original_price', 'added_at', 'updated_at']
        
    def get_has_offer(self, obj):
        """Check if the product has an active offer"""
        from django.utils import timezone
        now = timezone.now()
        
        active_offer = obj.product.offers.filter(
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        ).exists()
        
        return active_offer
    
    def get_original_price(self, obj):
        """Get the original price (before offer) if product has an offer"""
        from django.utils import timezone
        now = timezone.now()
        
        active_offer = obj.product.offers.filter(
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        ).first()
        
        if active_offer:
            return obj.product.price
        return None
    
    def to_representation(self, instance):
        """Override to pass context to nested serializers"""
        representation = super().to_representation(instance)
        if self.context:
            # Pass context to nested ProductMinimalSerializer
            product_serializer = ProductMinimalSerializer(instance.product, context=self.context)
            representation['product'] = product_serializer.data
        return representation
    
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
        
    def to_representation(self, instance):
        """Override to pass context to nested serializers"""
        representation = super().to_representation(instance)
        if self.context:
            # Pass context to nested CartItemSerializer
            items_serializer = CartItemSerializer(instance.items.all(), many=True, context=self.context)
            representation['items'] = items_serializer.data
        return representation


class AddToCartSerializer(serializers.Serializer):
    """Serializer for adding items to cart"""
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(default=1, min_value=1)
    selected_variants = serializers.JSONField(required=False, allow_null=True)
    variant_id = serializers.IntegerField(required=False, allow_null=True)
    
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