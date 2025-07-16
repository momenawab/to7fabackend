from rest_framework import serializers
from .models import Category, Product, ProductImage, Review
from django.contrib.auth import get_user_model

User = get_user_model()

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'description', 'parent', 'image', 'is_active')

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('id', 'image', 'is_primary')

class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = ('id', 'user', 'user_name', 'rating', 'comment', 'created_at')
        read_only_fields = ('user',)
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    seller_name = serializers.ReadOnlyField()
    images = ProductImageSerializer(many=True, read_only=True)
    average_rating = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = ('id', 'name', 'description', 'price', 'stock', 'category', 'category_name', 
                 'seller', 'seller_name', 'is_featured', 'is_active', 'created_at', 
                 'updated_at', 'images', 'average_rating')
        read_only_fields = ('seller',)
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['seller'] = user
        return super().create(validated_data)

class ProductDetailSerializer(ProductSerializer):
    category = CategorySerializer(read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    
    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + ('reviews',) 