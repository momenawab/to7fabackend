from rest_framework import serializers
from .ar_models import ARFrameAsset, ProductARSettings, ARPreviewSession
from .models import CategoryVariantOption

class CategoryVariantOptionSerializer(serializers.ModelSerializer):
    """Serializer for variant options used in AR"""
    variant_type_name = serializers.CharField(source='variant_type.name', read_only=True)

    class Meta:
        model = CategoryVariantOption
        fields = ['id', 'value', 'variant_type_name', 'extra_price']

class ARFrameAssetSerializer(serializers.ModelSerializer):
    """Serializer for AR frame assets"""
    frame_type = CategoryVariantOptionSerializer(source='frame_type_variant', read_only=True)
    frame_color = CategoryVariantOptionSerializer(source='frame_color_variant', read_only=True)
    frame_material = CategoryVariantOptionSerializer(source='frame_material_variant', read_only=True)

    # URLs for accessing the files
    frame_3d_model_url = serializers.SerializerMethodField()
    frame_texture_url = serializers.SerializerMethodField()
    frame_preview_image_url = serializers.SerializerMethodField()

    class Meta:
        model = ARFrameAsset
        fields = [
            'id', 'frame_type', 'frame_color', 'frame_material',
            'frame_3d_model_url', 'frame_texture_url', 'frame_preview_image_url',
            'frame_width_cm', 'frame_depth_cm', 'scale_factor',
            'position_offset_x', 'position_offset_y', 'position_offset_z'
        ]

    def get_frame_3d_model_url(self, obj):
        if obj.frame_3d_model:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.frame_3d_model.url)
            return obj.frame_3d_model.url
        return None

    def get_frame_texture_url(self, obj):
        if obj.frame_texture:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.frame_texture.url)
            return obj.frame_texture.url
        return None

    def get_frame_preview_image_url(self, obj):
        if obj.frame_preview_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.frame_preview_image.url)
            return obj.frame_preview_image.url
        return None

class ProductARSettingsSerializer(serializers.ModelSerializer):
    """Serializer for product AR settings"""
    available_frame_combinations = ARFrameAssetSerializer(
        source='get_available_frame_combinations',
        many=True,
        read_only=True
    )

    class Meta:
        model = ProductARSettings
        fields = [
            'ar_enabled', 'artwork_width_cm', 'artwork_height_cm', 'artwork_orientation',
            'min_distance_meters', 'max_distance_meters', 'aspect_ratio',
            'available_frame_combinations'
        ]

class ARPreviewSessionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating AR preview sessions"""

    class Meta:
        model = ARPreviewSession
        fields = [
            'product', 'frame_asset', 'session_duration_seconds',
            'device_model', 'platform', 'photo_saved', 'photo_shared', 'proceeded_to_purchase'
        ]

    def create(self, validated_data):
        # Set the user from request context if authenticated
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user

        return super().create(validated_data)

class ARFrameCombinationRequestSerializer(serializers.Serializer):
    """Serializer for requesting specific frame combinations"""
    frame_type_id = serializers.IntegerField(required=False, allow_null=True)
    frame_color_id = serializers.IntegerField(required=False, allow_null=True)
    frame_material_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_frame_type_id(self, value):
        if value and not CategoryVariantOption.objects.filter(
            id=value,
            variant_type__name__icontains='frame type',
            is_active=True
        ).exists():
            raise serializers.ValidationError("Invalid frame type ID")
        return value

    def validate_frame_color_id(self, value):
        if value and not CategoryVariantOption.objects.filter(
            id=value,
            variant_type__name__icontains='frame color',
            is_active=True
        ).exists():
            raise serializers.ValidationError("Invalid frame color ID")
        return value

    def validate_frame_material_id(self, value):
        if value and not CategoryVariantOption.objects.filter(
            id=value,
            variant_type__name__icontains='frame material',
            is_active=True
        ).exists():
            raise serializers.ValidationError("Invalid frame material ID")
        return value