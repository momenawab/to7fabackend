from rest_framework import serializers
from .models import Notification, BulkNotification, Device

class NotificationSerializer(serializers.ModelSerializer):
    created_at_formatted = serializers.SerializerMethodField()
    read_at_formatted = serializers.SerializerMethodField()
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'message', 'notification_type', 'priority',
            'is_read', 'action_url', 'image_url',
            'related_object_id', 'related_object_type',  # Legacy fields
            'content_type', 'object_id',  # New fields
            'created_at', 'created_at_formatted', 'read_at', 'read_at_formatted',
            'time_ago'
        ]
        read_only_fields = [
            'id', 'created_at', 'created_at_formatted', 
            'read_at', 'read_at_formatted', 'time_ago'
        ]
    
    def get_created_at_formatted(self, obj):
        """Return a human-readable date format"""
        return obj.created_at.strftime("%b %d, %Y %H:%M")
    
    def get_read_at_formatted(self, obj):
        """Return a human-readable read date format"""
        if obj.read_at:
            return obj.read_at.strftime("%b %d, %Y %H:%M")
        return None
    
    def get_time_ago(self, obj):
        """Return time ago string"""
        from django.utils import timezone
        from django.utils.timesince import timesince
        
        now = timezone.now()
        time_diff = now - obj.created_at
        
        if time_diff.seconds < 60:
            return "Just now"
        elif time_diff.seconds < 3600:
            minutes = time_diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif time_diff.days < 1:
            hours = time_diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif time_diff.days < 7:
            return f"{time_diff.days} day{'s' if time_diff.days != 1 else ''} ago"
        else:
            return timesince(obj.created_at, now).split(',')[0] + " ago"


class NotificationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating notification status"""
    
    class Meta:
        model = Notification
        fields = ['is_read']
    
    def update(self, instance, validated_data):
        if 'is_read' in validated_data and validated_data['is_read'] and not instance.is_read:
            # Mark as read with timestamp
            instance.mark_as_read()
        elif 'is_read' in validated_data and not validated_data['is_read']:
            # Mark as unread
            instance.is_read = False
            instance.read_at = None
            instance.save()
        return instance


class BulkNotificationSerializer(serializers.ModelSerializer):
    """Serializer for bulk notifications (admin use)"""
    target_users_count = serializers.SerializerMethodField()
    
    class Meta:
        model = BulkNotification
        fields = [
            'id', 'title', 'message', 'notification_type', 'target_audience',
            'priority', 'action_url', 'image_url', 'schedule_for',
            'is_sent', 'sent_at', 'recipient_count', 'target_users_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'is_sent', 'sent_at', 'recipient_count', 
            'created_at', 'updated_at', 'target_users_count'
        ]
    
    def get_target_users_count(self, obj):
        """Return the number of users that would be targeted"""
        return obj.get_target_users().count()


class DeviceSerializer(serializers.ModelSerializer):
    """Serializer for device registration and management"""
    user_email = serializers.SerializerMethodField()
    last_used_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = Device
        fields = [
            'id', 'device_token', 'platform', 'device_id',
            'app_version', 'device_model', 'os_version',
            'is_active', 'notifications_enabled',
            'last_used', 'last_used_formatted', 'created_at',
            'user_email'
        ]
        read_only_fields = [
            'id', 'last_used', 'last_used_formatted', 'created_at', 'user_email'
        ]
    
    def get_user_email(self, obj):
        """Return user email for admin purposes"""
        return obj.user.email if obj.user else None
    
    def get_last_used_formatted(self, obj):
        """Return formatted last used date"""
        return obj.last_used.strftime("%b %d, %Y %H:%M") if obj.last_used else None
    
    def validate_platform(self, value):
        """Validate platform choice"""
        valid_platforms = ['ios', 'android', 'web']
        if value not in valid_platforms:
            raise serializers.ValidationError(f"Platform must be one of: {', '.join(valid_platforms)}")
        return value
    
    def validate_device_token(self, value):
        """Validate device token length"""
        if len(value) < 10:
            raise serializers.ValidationError("Device token appears to be too short")
        if len(value) > 500:
            raise serializers.ValidationError("Device token is too long")
        return value 