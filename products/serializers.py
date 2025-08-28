from rest_framework import serializers
from .models import (
    Category, Product, ProductImage, Review, ProductAttribute, 
    ProductAttributeOption, CategoryAttribute, CategoryVariantType, 
    CategoryVariantOption, ProductCategoryVariantOption, SubcategorySectionControl
)
from django.contrib.auth import get_user_model

User = get_user_model()

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'description', 'parent', 'image', 'is_active')

class ProductImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductImage
        fields = ('id', 'image', 'is_primary')
    
    def get_image(self, obj):
        if obj.image and hasattr(obj.image, 'url'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = ('id', 'user', 'user_name', 'rating', 'comment', 'created_at')
        read_only_fields = ('user',)
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

# Serializers for Product Attributes
class ProductAttributeOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductAttributeOption
        fields = ('id', 'value', 'display_name', 'color_code', 'is_active', 'sort_order')

class ProductAttributeSerializer(serializers.ModelSerializer):
    options = ProductAttributeOptionSerializer(many=True, read_only=True)
    
    class Meta:
        model = ProductAttribute
        fields = ('id', 'name', 'attribute_type', 'is_required', 'is_active', 'options')

class CategoryAttributeSerializer(serializers.ModelSerializer):
    attribute = ProductAttributeSerializer(read_only=True)
    
    class Meta:
        model = CategoryAttribute
        fields = ('id', 'attribute', 'is_required', 'sort_order')

# Serializers for Category Variants
class CategoryVariantTypeBasicSerializer(serializers.ModelSerializer):
    """Basic variant type serializer without options to avoid circular reference"""
    class Meta:
        model = CategoryVariantType
        fields = ('id', 'name', 'is_required')

class CategoryVariantOptionSerializer(serializers.ModelSerializer):
    variant_type = CategoryVariantTypeBasicSerializer(read_only=True)
    variant_type_name = serializers.ReadOnlyField(source='variant_type.name')
    
    class Meta:
        model = CategoryVariantOption
        fields = ('id', 'value', 'extra_price', 'is_active', 'variant_type', 'variant_type_name')

class CategoryVariantTypeSerializer(serializers.ModelSerializer):
    options = CategoryVariantOptionSerializer(many=True, read_only=True)
    
    class Meta:
        model = CategoryVariantType
        fields = ('id', 'name', 'is_required', 'priority', 'options')

class ProductCategoryVariantSelectionSerializer(serializers.ModelSerializer):
    category_variant_option = CategoryVariantOptionSerializer(read_only=True)
    final_price = serializers.ReadOnlyField()
    variant_type_name = serializers.ReadOnlyField()
    variant_option_value = serializers.ReadOnlyField()
    stock_status = serializers.ReadOnlyField()
    
    class Meta:
        model = ProductCategoryVariantOption
        fields = ('id', 'category_variant_option', 'stock_count', 'price_adjustment', 
                 'final_price', 'is_active', 'variant_type_name', 'variant_option_value', 'stock_status')

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    seller_name = serializers.ReadOnlyField()
    images = ProductImageSerializer(many=True, read_only=True)
    average_rating = serializers.ReadOnlyField()
    
    # CategoryVariant-related fields
    selected_variants = ProductCategoryVariantSelectionSerializer(many=True, read_only=True)
    available_variant_types = serializers.SerializerMethodField()
    price_range = serializers.SerializerMethodField()
    stock_status = serializers.SerializerMethodField()
    has_variants = serializers.ReadOnlyField()
    
    # Backward compatibility fields
    price = serializers.ReadOnlyField()  # Returns base_price
    stock = serializers.ReadOnlyField()  # Returns total stock
    
    # Legacy fields for Flutter compatibility
    colors = serializers.SerializerMethodField()
    sizes = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ('id', 'name', 'description', 'base_price', 'price', 'stock', 'stock_quantity', 'category', 'category_name', 
                 'seller', 'seller_name', 'is_featured', 'is_active', 'approval_status', 'rejection_reason', 'created_at', 
                 'updated_at', 'images', 'average_rating', 'selected_variants', 'available_variant_types',
                 'price_range', 'stock_status', 'has_variants', 'colors', 'sizes', 'combination_stocks',
                 'featured_request_pending', 'offers_request_pending', 'featured_requested_at', 'offers_requested_at')
        read_only_fields = ('seller',)
    
    def get_stock_status(self, obj):
        """Get stock status for this product"""
        return obj.get_stock_status()
    
    def get_available_variant_types(self, obj):
        """Get available variant types with inheritance"""
        variant_types = obj.available_variant_types
        return CategoryVariantTypeSerializer(variant_types, many=True, context=self.context).data
    
    def get_price_range(self, obj):
        """Get price range for this product"""
        min_price, max_price = obj.get_price_range()
        return {
            'min_price': float(min_price),
            'max_price': float(max_price)
        }
    
    def get_colors(self, obj):
        """Get available colors for backward compatibility"""
        colors = []
        for variant_type in obj.available_variant_types:
            if variant_type.name.lower() in ['لون', 'color', 'لون الإطار', 'frame_color']:
                colors.extend([option.value for option in variant_type.options.filter(is_active=True)])
        return colors if colors else ['أبيض', 'أسود', 'ذهبي']  # Default fallback
    
    def get_sizes(self, obj):
        """Get available sizes for backward compatibility"""
        sizes = []
        for variant_type in obj.available_variant_types:
            if variant_type.name.lower() in ['حجم', 'size', 'الحجم']:
                sizes.extend([option.value for option in variant_type.options.filter(is_active=True)])
        return sizes if sizes else ['20x30cm', '30x40cm', '40x50cm']  # Default fallback
    
    def create(self, validated_data):
        from django.utils import timezone
        
        user = self.context['request'].user
        validated_data['seller'] = user
        
        # Handle featured request timestamp
        if validated_data.get('featured_request_pending', False):
            validated_data['featured_requested_at'] = timezone.now()
        
        # Handle offers request timestamp  
        if validated_data.get('offers_request_pending', False):
            validated_data['offers_requested_at'] = timezone.now()
            
        return super().create(validated_data)

class ProductDetailSerializer(ProductSerializer):
    category = CategorySerializer(read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    
    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + ('reviews',)


# Serializer for Subcategory Section Control
class SubcategorySectionControlSerializer(serializers.ModelSerializer):
    subcategory = serializers.SerializerMethodField()
    products_to_display = serializers.SerializerMethodField()
    products_count = serializers.SerializerMethodField()
    parent_category_id = serializers.SerializerMethodField()
    parent_category_name = serializers.SerializerMethodField()
    
    class Meta:
        model = SubcategorySectionControl
        fields = (
            'id', 'subcategory', 'parent_category_id', 'parent_category_name',
            'is_section_enabled', 'max_products_to_show', 'section_priority',
            'products_to_display', 'products_count', 'created_at', 'updated_at'
        )
    
    def get_subcategory(self, obj):
        try:
            if obj.subcategory:
                return CategorySerializer(obj.subcategory, context=self.context).data
        except Exception as e:
            print(f"Error getting subcategory for section {obj.id}: {e}")
        return None
    
    def get_products_to_display(self, obj):
        try:
            products = obj.get_products_to_display()
            return ProductSerializer(products, many=True, context=self.context).data
        except Exception as e:
            print(f"Error getting products for section {obj.id}: {e}")
            return []
    
    def get_products_count(self, obj):
        try:
            return obj.products_count
        except Exception as e:
            print(f"Error getting products count for section {obj.id}: {e}")
            return 0
    
    def get_parent_category_id(self, obj):
        try:
            if obj.subcategory and obj.subcategory.parent:
                return obj.subcategory.parent.id
        except Exception as e:
            print(f"Error getting parent category id for section {obj.id}: {e}")
        return None
    
    def get_parent_category_name(self, obj):
        try:
            if obj.subcategory and obj.subcategory.parent:
                return obj.subcategory.parent.name
        except Exception as e:
            print(f"Error getting parent category name for section {obj.id}: {e}")
        return None 