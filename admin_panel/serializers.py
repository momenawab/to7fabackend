from rest_framework import serializers
from custom_auth.models import User, Artist, Store
from products.models import Product, Category
from orders.models import Order, OrderItem
from .models import SellerApplication, AdminActivity, AdminNotification
from django.utils import timezone

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
    """Serializer for creating seller applications from frontend"""
    subcategories = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        help_text="List of subcategory IDs"
    )
    details = serializers.CharField(required=False, allow_blank=True, default='')
    
    def to_internal_value(self, data):
        # Convert QueryDict to regular dict and handle multipart form data
        from django.http import QueryDict
        if isinstance(data, QueryDict):
            # Convert QueryDict to regular dict, extracting first value from lists
            processed_data = {}
            for key, value_list in data.lists():
                if key in ['id_front', 'id_back']:
                    # Keep file uploads as-is
                    processed_data[key] = value_list[0] if value_list else None
                else:
                    # For other fields, take the first value
                    processed_data[key] = value_list[0] if value_list else None
            data = processed_data
        
        # Handle form data where JSON fields are sent as strings
        if isinstance(data, dict):
            # Parse JSON string fields that come from multipart form data
            json_fields = ['categories', 'subcategories', 'social_media', 'shipping_costs']
            for field in json_fields:
                if field in data and isinstance(data[field], str):
                    try:
                        import json
                        data[field] = json.loads(data[field])
                    except (json.JSONDecodeError, TypeError):
                        pass  # Let the field validator handle the error
            
            # Handle boolean fields that come as strings in form data
            bool_fields = ['terms_accepted', 'has_physical_store']
            for field in bool_fields:
                if field in data and isinstance(data[field], str):
                    data[field] = data[field].lower() in ('true', '1', 'yes', 'on')
        
        return super().to_internal_value(data)
    
    class Meta:
        model = SellerApplication
        fields = (
            'user_type', 'name', 'phone_number', 'email', 'address', 'details',
            'categories', 'subcategories', 'social_media', 'shipping_costs', 
            'id_front', 'id_back', 'terms_accepted', 'bio', 'specialty', 
            'store_name', 'tax_id', 'has_physical_store', 'physical_address'
        )
        
    def create(self, validated_data):
        # Set the user from the request context
        user = self.context['request'].user
        validated_data['user'] = user
        
        # Handle subcategories - they're not a model field, so remove from validated_data
        subcategories = validated_data.pop('subcategories', [])
        
        # Set terms accepted timestamp
        if validated_data.get('terms_accepted'):
            validated_data['terms_accepted_at'] = timezone.now()
            
        # Create the application
        application = super().create(validated_data)
        
        # TODO: Store subcategories if needed (you can add a separate model or field for this)
        # For now, we'll just store them in the details field if they exist
        if subcategories:
            details = application.details or ''
            details += f'\nSelected subcategories: {subcategories}'
            application.details = details
            application.save()
            
        return application
        
    def validate_categories(self, value):
        """Validate that categories exist and are active"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Categories must be a list")
        
        # Check that all category IDs exist and are active
        from products.models import Category
        existing_categories = Category.objects.filter(
            id__in=value, is_active=True
        ).values_list('id', flat=True)
        
        invalid_categories = set(value) - set(existing_categories)
        if invalid_categories:
            raise serializers.ValidationError(
                f"Invalid category IDs: {list(invalid_categories)}"
            )
            
        return value
        
    def validate_subcategories(self, value):
        """Validate that subcategories exist and are active"""
        # Handle empty values
        if not value or value == [] or value == '[]':
            return []
            
        if not isinstance(value, list):
            raise serializers.ValidationError("Subcategories must be a list")
        
        # Ensure all items are integers
        try:
            value = [int(item) for item in value]
        except (ValueError, TypeError):
            raise serializers.ValidationError("All subcategory IDs must be integers")
        
        # Check that all subcategory IDs exist and are active
        from products.models import Category
        existing_subcategories = Category.objects.filter(
            id__in=value, is_active=True, parent__isnull=False
        ).values_list('id', flat=True)
        
        invalid_subcategories = set(value) - set(existing_subcategories)
        if invalid_subcategories:
            raise serializers.ValidationError(
                f"Invalid subcategory IDs: {list(invalid_subcategories)}"
            )
            
        return value
        
    def validate_terms_accepted(self, value):
        """Ensure terms are accepted"""
        if not value:
            raise serializers.ValidationError("Terms must be accepted to submit application")
        return value 