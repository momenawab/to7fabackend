from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import User, Customer, Artist, Store
from django.db.models import Q
from django.db import transaction

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    
    class Meta:
        model = User
        fields = ('email', 'password', 'confirm_password', 'first_name', 'last_name', 'phone_number', 'address')
        extra_kwargs = {
            'phone_number': {'required': False},
            'address': {'required': False}
        }
    
    def validate_email(self, value):
        # Case-insensitive email check
        normalized_email = value.lower().strip()
        if User.objects.filter(email__iexact=normalized_email).exists():
            raise serializers.ValidationError(f"A user with the email '{value}' already exists.")
        return normalized_email
    
    def validate(self, data):
        if data['password'] != data.pop('confirm_password'):
            raise serializers.ValidationError({"confirm_password": "Passwords do not match"})
        return data
    
    def create(self, validated_data):
        with transaction.atomic():
            # Check if user already exists
            email = validated_data['email']
            if User.objects.filter(email__iexact=email).exists():
                raise serializers.ValidationError({"email": f"A user with the email '{email}' already exists."})
                
            # Create user
            user = User.objects.create_user(
                email=validated_data['email'],
                password=validated_data['password'],
                first_name=validated_data['first_name'],
                last_name=validated_data['last_name'],
                phone_number=validated_data.get('phone_number', ''),
                address=validated_data.get('address', '')
            )
            
            # Check if customer profile already exists
            if Customer.objects.filter(user=user).exists():
                # If it exists, don't create a new one
                pass
            else:
                # Create customer profile
                Customer.objects.create(user=user)
            
            return user

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'phone_number', 'address', 'user_type')
        read_only_fields = ('email', 'user_type')

class CustomerProfileSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = Customer
        fields = ('user', 'profile_picture', 'date_of_birth', 'preferences')

class ArtistRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artist
        fields = ('specialty', 'bio', 'social_media')

class StoreRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ('store_name', 'tax_id', 'has_physical_store', 'physical_address', 'social_media')

class UserSerializer(serializers.ModelSerializer):
    blocked_by_email = serializers.SerializerMethodField()
    blocked_status = serializers.SerializerMethodField()
    unblocked_by_email = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'user_type', 
                  'is_active', 'blocked_at', 'blocked_by', 'blocked_by_email',
                  'block_reason', 'unblocked_at', 'unblocked_by', 'unblocked_by_email',
                  'blocked_status', 'date_joined']
        read_only_fields = ['id', 'email', 'blocked_at', 'blocked_by', 'unblocked_at', 'unblocked_by']
    
    def get_blocked_by_email(self, obj):
        if obj.blocked_by:
            return obj.blocked_by.email
        return None
    
    def get_unblocked_by_email(self, obj):
        if obj.unblocked_by:
            return obj.unblocked_by.email
        return None
    
    def get_blocked_status(self, obj):
        if not obj.is_active and obj.blocked_at:
            return "Blocked"
        return "Active" 