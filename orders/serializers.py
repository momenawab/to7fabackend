from rest_framework import serializers
from .models import Order, OrderItem
from products.models import Product
from products.serializers import ProductSerializer
from django.db import transaction
from decimal import Decimal

class OrderItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(write_only=True)
    product = ProductSerializer(read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ('id', 'product_id', 'product', 'quantity', 'price', 'seller', 'commission_rate', 'commission_amount')
        read_only_fields = ('price', 'seller', 'commission_rate', 'commission_amount')
    
    def validate_product_id(self, value):
        try:
            product = Product.objects.get(pk=value)
            return value
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product does not exist")

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    items_data = serializers.ListField(
        child=serializers.DictField(),
        write_only=True
    )
    shipping_cost = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    
    class Meta:
        model = Order
        fields = ('id', 'user', 'total_amount', 'status', 'shipping_address', 'shipping_cost', 
                 'payment_method', 'payment_status', 'created_at', 'updated_at', 'items', 'items_data')
        read_only_fields = ('user', 'total_amount', 'status', 'payment_status', 'created_at', 'updated_at')
    
    def validate_items_data(self, value):
        if not value:
            raise serializers.ValidationError("At least one item is required")
        
        for item in value:
            if 'product_id' not in item:
                raise serializers.ValidationError("product_id is required for each item")
            if 'quantity' not in item:
                raise serializers.ValidationError("quantity is required for each item")
            
            try:
                product = Product.objects.get(pk=item['product_id'])
                available_stock = product.stock  # This uses the @property method that handles variants
                if available_stock < item['quantity']:
                    raise serializers.ValidationError(f"Not enough stock for {product.name}. Available: {available_stock}")
            except Product.DoesNotExist:
                raise serializers.ValidationError(f"Product with ID {item['product_id']} does not exist")
                
        return value
    
    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items_data')
        user = self.context['request'].user
        
        # Calculate total amount
        total_amount = Decimal('0')
        for item_data in items_data:
            product = Product.objects.get(pk=item_data['product_id'])
            total_amount += product.price * item_data['quantity']
        
        # Add shipping cost
        shipping_cost = validated_data.get('shipping_cost', Decimal('0'))
        total_amount += shipping_cost
        
        # Create order
        order = Order.objects.create(
            user=user,
            total_amount=total_amount,
            **validated_data
        )
        
        # Create order items
        for item_data in items_data:
            product = Product.objects.get(pk=item_data['product_id'])
            
            # Update product stock - handle both variant and non-variant products
            if product.has_variants:
                # For variant products, we would need specific variant ID to reduce stock
                # For now, reduce the base stock as fallback
                if hasattr(product, 'stock_quantity'):
                    product.stock_quantity = max(0, product.stock_quantity - item_data['quantity'])
                    product.save()
            else:
                # For non-variant products, reduce stock_quantity directly
                product.stock_quantity = max(0, product.stock_quantity - item_data['quantity'])
                product.save()
            
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item_data['quantity'],
                price=product.price,
                seller=product.seller
            )
            
        return order

class OrderDetailSerializer(OrderSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta(OrderSerializer.Meta):
        fields = OrderSerializer.Meta.fields 