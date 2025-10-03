from rest_framework import serializers
from decimal import Decimal, ROUND_HALF_UP
from .address_models import UserAddress

class UserAddressSerializer(serializers.ModelSerializer):
    full_address = serializers.ReadOnlyField()
    
    class Meta:
        model = UserAddress
        fields = [
            'id', 'name', 'recipient_name', 'street', 'building', 'apartment',
            'city', 'region', 'postal_code', 'phone_number', 'latitude', 'longitude',
            'location_notes', 'is_default', 'full_address', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'full_address']

    def validate(self, data):
        """Validate address data"""
        user = self.context['request'].user
        
        # If setting as default, ensure no duplicate defaults
        if data.get('is_default', False):
            # This will be handled in the model's save method
            pass
        
        return data

class AddressCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = [
            'name', 'recipient_name', 'street', 'building', 'apartment',
            'city', 'region', 'postal_code', 'phone_number', 'latitude', 
            'longitude', 'location_notes', 'is_default'
        ]

    def validate_latitude(self, value):
        """Ensure latitude has max 8 decimal places"""
        if value is not None:
            # Round to 8 decimal places using Decimal for precision
            rounded_value = Decimal(str(value)).quantize(Decimal('0.00000001'), rounding=ROUND_HALF_UP)
            return float(rounded_value)
        return value

    def validate_longitude(self, value):
        """Ensure longitude has max 8 decimal places"""
        if value is not None:
            # Round to 8 decimal places using Decimal for precision
            rounded_value = Decimal(str(value)).quantize(Decimal('0.00000001'), rounding=ROUND_HALF_UP)
            return float(rounded_value)
        return value

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class AddressUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = [
            'name', 'recipient_name', 'street', 'building', 'apartment',
            'city', 'region', 'postal_code', 'phone_number', 'latitude', 
            'longitude', 'location_notes', 'is_default'
        ]

    def validate_latitude(self, value):
        """Ensure latitude has max 8 decimal places"""
        if value is not None:
            # Round to 8 decimal places using Decimal for precision
            rounded_value = Decimal(str(value)).quantize(Decimal('0.00000001'), rounding=ROUND_HALF_UP)
            return float(rounded_value)
        return value

    def validate_longitude(self, value):
        """Ensure longitude has max 8 decimal places"""
        if value is not None:
            # Round to 8 decimal places using Decimal for precision
            rounded_value = Decimal(str(value)).quantize(Decimal('0.00000001'), rounding=ROUND_HALF_UP)
            return float(rounded_value)
        return value