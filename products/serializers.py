from rest_framework import serializers
from .models import (
    Category, Product, ProductImage, Review, ProductAttribute, 
    ProductAttributeOption, CategoryAttribute, ProductVariant, ProductVariantAttribute
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

# Serializers for Product Variants
class ProductVariantAttributeSerializer(serializers.ModelSerializer):
    attribute = ProductAttributeSerializer(read_only=True)
    option = ProductAttributeOptionSerializer(read_only=True)
    
    class Meta:
        model = ProductVariantAttribute
        fields = ('id', 'attribute', 'option')

class ProductVariantSerializer(serializers.ModelSerializer):
    variant_attributes = ProductVariantAttributeSerializer(many=True, read_only=True)
    final_price = serializers.ReadOnlyField()
    stock_status = serializers.ReadOnlyField()
    
    class Meta:
        model = ProductVariant
        fields = ('id', 'sku', 'stock_count', 'price_adjustment', 'final_price', 
                 'stock_status', 'is_active', 'variant_attributes')

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    seller_name = serializers.ReadOnlyField()
    images = ProductImageSerializer(many=True, read_only=True)
    average_rating = serializers.ReadOnlyField()
    
    # Variant-related fields
    variants = ProductVariantSerializer(many=True, read_only=True)
    available_attributes = serializers.SerializerMethodField()
    price_range = serializers.SerializerMethodField()
    stock_status = serializers.ReadOnlyField()
    has_variants = serializers.ReadOnlyField()
    
    # Backward compatibility fields
    price = serializers.ReadOnlyField()  # Returns base_price
    stock = serializers.ReadOnlyField()  # Returns total stock
    
    # Legacy fields for Flutter compatibility
    colors = serializers.SerializerMethodField()
    sizes = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ('id', 'name', 'description', 'base_price', 'price', 'stock', 'category', 'category_name', 
                 'seller', 'seller_name', 'is_featured', 'is_active', 'created_at', 
                 'updated_at', 'images', 'average_rating', 'variants', 'available_attributes',
                 'price_range', 'stock_status', 'has_variants', 'colors', 'sizes')
        read_only_fields = ('seller',)
    
    def get_available_attributes(self, obj):
        """Get available attributes for this product's category"""
        category_attributes = obj.category.category_attributes.filter(attribute__is_active=True).order_by('sort_order')
        return CategoryAttributeSerializer(category_attributes, many=True).data
    
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
        for attr in obj.get_available_attributes():
            if attr.attribute.attribute_type in ['color', 'frame_color']:
                colors.extend([option.value for option in attr.attribute.options.filter(is_active=True)])
        return colors if colors else ['أبيض', 'أسود', 'ذهبي']  # Default fallback
    
    def get_sizes(self, obj):
        """Get available sizes for backward compatibility"""
        sizes = []
        for attr in obj.get_available_attributes():
            if attr.attribute.attribute_type == 'size':
                sizes.extend([option.value for option in attr.attribute.options.filter(is_active=True)])
        return sizes if sizes else ['20x30cm', '30x40cm', '40x50cm']  # Default fallback
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['seller'] = user
        return super().create(validated_data)

class ProductDetailSerializer(ProductSerializer):
    category = CategorySerializer(read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    
    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + ('reviews',) 