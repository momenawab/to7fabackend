from rest_framework import serializers
from custom_auth.models import User, Artist, Store
from products.models import Product, Category
from orders.models import Order, OrderItem
from .models import AdminActivity, AdminNotification
from custom_auth.models import SellerApplication
from django.utils import timezone

class SellerApplicationSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    seller_type_display = serializers.CharField(source='get_seller_type_display', read_only=True)
    reviewed_by_email = serializers.EmailField(source='reviewed_by.email', read_only=True)
    
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
                  'category_name', 'approval_status', 'rejection_reason', 'created_at', 'updated_at')
    
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
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    items = OrderItemSerializer(source='items', many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = ('id', 'user', 'user_email', 'user_name',
                  'status', 'status_display', 'shipping_address',
                  'shipping_cost', 'total_amount', 'payment_method',
                  'items', 'created_at', 'updated_at')
    
    def get_user_name(self, obj):
        user = obj.user
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

class SellerApplicationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating seller applications from frontend with backward compatibility"""
    
    # Accept both old and new field names for backward compatibility
    user_type = serializers.CharField(write_only=True, required=False, help_text="Legacy field name for seller_type")
    name = serializers.CharField(write_only=True, required=False, help_text="Legacy field name for business_name")
    email = serializers.EmailField(write_only=True, required=False, help_text="Legacy field - user email")
    bio = serializers.CharField(write_only=True, required=False, help_text="Legacy field name for description")
    store_name = serializers.CharField(write_only=True, required=False, help_text="Legacy field name for business_name")
    
    # File upload fields with legacy names
    id_front = serializers.FileField(write_only=True, required=False, help_text="Legacy field name for id_document_front")
    id_back = serializers.FileField(write_only=True, required=False, help_text="Legacy field name for id_document_back")
    
    class Meta:
        model = SellerApplication
        fields = (
            # New model fields
            'seller_type', 'business_name', 'phone_number', 'description', 'address',
            'social_media', 'business_license', 'specialty', 'portfolio_link', 
            'tax_id', 'has_physical_store', 'physical_address',
            'categories', 'subcategories', 'shipping_costs', 'terms_accepted',
            'id_document_front', 'id_document_back',
            # Legacy fields for backward compatibility  
            'user_type', 'name', 'email', 'bio', 'store_name', 'id_front', 'id_back'
        )
        extra_kwargs = {
            'seller_type': {'required': False},
            'business_name': {'required': False},
            'description': {'required': False},
        }
        
    def validate(self, data):
        """Handle field mapping from old to new field names"""
        
        # Map user_type to seller_type
        if 'user_type' in data:
            data['seller_type'] = data.pop('user_type')
        
        # Map name to business_name (primary mapping)
        if 'name' in data:
            data['business_name'] = data.pop('name')
        
        # Map store_name to business_name (for store types, override name if provided)
        if 'store_name' in data and data['store_name']:
            data['business_name'] = data.pop('store_name')
        
        # Map bio to description
        if 'bio' in data:
            data['description'] = data.pop('bio')
        
        # Map ID document files
        if 'id_front' in data:
            data['id_document_front'] = data.pop('id_front')
        
        if 'id_back' in data:
            data['id_document_back'] = data.pop('id_back')
        
        # Remove email field (comes from user)
        if 'email' in data:
            data.pop('email')
        
        # Ensure required fields are present with defaults
        if 'seller_type' not in data:
            raise serializers.ValidationError({'seller_type': 'This field is required.'})
        
        if 'business_name' not in data or not data['business_name']:
            raise serializers.ValidationError({'business_name': 'This field is required.'})
        
        if 'description' not in data:
            data['description'] = ''  # Set default empty description
        
        return data
        
    def create(self, validated_data):
        # Set the user from the request context
        user = self.context['request'].user
        validated_data['user'] = user
        
        # Set terms accepted timestamp if terms were accepted
        if validated_data.get('terms_accepted'):
            from django.utils import timezone
            validated_data['terms_accepted_at'] = timezone.now()
        
        # Create the application
        application = super().create(validated_data)
        
        return application 