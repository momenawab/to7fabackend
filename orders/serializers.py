from rest_framework import serializers
from .models import Order, OrderItem
from products.models import Product
from products.serializers import ProductSerializer
from django.db import transaction
from decimal import Decimal

class OrderItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(write_only=True)
    product = ProductSerializer(read_only=True)
    variant_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = OrderItem
        fields = ('id', 'product_id', 'product', 'quantity', 'price', 'seller', 
                  'commission_rate', 'commission_amount', 'variant_id')
        read_only_fields = ('price', 'seller', 'commission_rate', 'commission_amount')
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Pass request context to nested ProductSerializer
        if self.context.get('request'):
            product_serializer = ProductSerializer(instance.product, context=self.context)
            representation['product'] = product_serializer.data
        return representation
    
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
    idempotency_key = serializers.CharField(max_length=255, required=False, allow_null=True)
    use_wallet_payment = serializers.BooleanField(required=False, default=False)
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Pass request context to nested OrderItemSerializer
        if self.context.get('request'):
            items_serializer = OrderItemSerializer(instance.items.all(), many=True, context=self.context)
            representation['items'] = items_serializer.data
        return representation
    
    class Meta:
        model = Order
        fields = ('id', 'user', 'total_amount', 'status', 'shipping_address', 'shipping_cost', 
                 'payment_method', 'payment_status', 'created_at', 'updated_at', 'items', 'items_data',
                 'idempotency_key', 'use_wallet_payment')
        read_only_fields = ('user', 'total_amount', 'status', 'payment_status', 'created_at', 'updated_at')
    
    def validate_items_data(self, value):
        """Validate items data structure"""
        if not value:
            raise serializers.ValidationError("At least one item is required")
        
        for item in value:
            if 'product_id' not in item:
                raise serializers.ValidationError("product_id is required for each item")
            if 'quantity' not in item:
                raise serializers.ValidationError("quantity is required for each item")
            if item['quantity'] <= 0:
                raise serializers.ValidationError("quantity must be positive")
                
        return value
    
    def validate_idempotency_key(self, value):
        """Validate idempotency key format"""
        if value:
            # Check if order already exists with this key
            from .models import Order
            if Order.objects.filter(idempotency_key=value).exists():
                raise serializers.ValidationError("An order with this idempotency key already exists")
        return value
    
    def create(self, validated_data):
        """
        Create order using atomic transaction system.
        
        This delegates to AtomicOrderCreator which handles:
        - Idempotency checks
        - Stock locking and reservation
        - Wallet payment coordination
        - Complete rollback on failure
        """
        from .atomic_order_system import AtomicOrderCreator
        from .models import Order
        
        items_data = validated_data.pop('items_data')
        user = self.context['request'].user
        shipping_address = validated_data.get('shipping_address', '')
        shipping_cost = validated_data.get('shipping_cost', Decimal('0'))
        payment_method = validated_data.get('payment_method', 'wallet')
        idempotency_key = validated_data.get('idempotency_key')
        use_wallet_payment = validated_data.get('use_wallet_payment', False)
        
        # Validate required fields
        if not shipping_address:
            raise serializers.ValidationError("shipping_address is required")
        
        if not idempotency_key:
            raise serializers.ValidationError("idempotency_key is required for order creation")
        
        # Use atomic order creator
        success, order, error = AtomicOrderCreator.create_order(
            user=user,
            items_data=items_data,
            shipping_address=shipping_address,
            shipping_cost=shipping_cost,
            payment_method=payment_method,
            idempotency_key=idempotency_key,
            use_wallet_payment=use_wallet_payment
        )
        
        if not success:
            raise serializers.ValidationError(error or "Failed to create order")
        
        return order


class OrderDetailSerializer(OrderSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta(OrderSerializer.Meta):
        fields = OrderSerializer.Meta.fields
