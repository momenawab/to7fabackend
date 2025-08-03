from rest_framework import serializers
from custom_auth.models import User, Artist, Store
from products.models import Product, Category
from orders.models import Order, OrderItem
from .models import SellerApplication, AdminActivity, AdminNotification

class SellerApplicationSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    user_type_display = serializers.CharField(source='get_user_type_display', read_only=True)
    processed_by_email = serializers.EmailField(source='processed_by.email', read_only=True)
    
    class Meta:
        model = SellerApplication
        fields = '__all__'
    
    def get_user_name(self, obj):
        user = obj.user
        return f"{user.first_name} {user.last_name}".strip() or user.email

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    user_type_display = serializers.CharField(source='get_user_type_display', read_only=True)
    blocked_by_email = serializers.EmailField(source='blocked_by.email', read_only=True, allow_null=True, default=None)
    unblocked_by_email = serializers.EmailField(source='unblocked_by.email', read_only=True, allow_null=True, default=None)
    
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'full_name', 
                  'user_type', 'user_type_display', 'phone_number', 'address',
                  'is_active', 'date_joined', 'last_login', 'blocked_at', 
                  'blocked_by', 'blocked_by_email', 'block_reason', 
                  'unblocked_at', 'unblocked_by', 'unblocked_by_email')
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.email

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name')

class ProductSerializer(serializers.ModelSerializer):
    seller_name = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Product
        fields = ('id', 'name', 'description', 'price', 'stock', 'is_active',
                  'is_featured', 'seller', 'seller_name', 'category', 
                  'category_name', 'created_at', 'updated_at')
    
    def get_seller_name(self, obj):
        user = obj.seller
        if user.user_type == 'artist':
            try:
                return f"Artist: {user.artist_profile.specialty} - {user.email}"
            except:
                return f"Artist: {user.email}"
        elif user.user_type == 'store':
            try:
                return f"Store: {user.store_profile.store_name}"
            except:
                return f"Store: {user.email}"
        return user.email

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ('id', 'product', 'product_name', 'quantity', 'price')

class OrderSerializer(serializers.ModelSerializer):
    customer_email = serializers.EmailField(source='customer.email', read_only=True)
    customer_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    items = OrderItemSerializer(source='orderitem_set', many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = ('id', 'customer', 'customer_email', 'customer_name',
                  'status', 'status_display', 'shipping_address',
                  'shipping_cost', 'total_amount', 'payment_method',
                  'items', 'created_at', 'updated_at')
    
    def get_customer_name(self, obj):
        user = obj.customer
        return f"{user.first_name} {user.last_name}".strip() or user.email

class AdminActivitySerializer(serializers.ModelSerializer):
    admin_email = serializers.EmailField(source='admin.email', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = AdminActivity
        fields = ('id', 'admin', 'admin_email', 'action', 'action_display',
                  'description', 'ip_address', 'timestamp')

class AdminNotificationSerializer(serializers.ModelSerializer):
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    
    class Meta:
        model = AdminNotification
        fields = ('id', 'title', 'message', 'notification_type', 
                  'notification_type_display', 'is_read', 'link', 'created_at') 