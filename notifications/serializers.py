from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    created_at_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'message', 'notification_type', 
            'is_read', 'related_object_id', 'related_object_type',
            'created_at', 'created_at_formatted'
        ]
        read_only_fields = ['id', 'created_at', 'created_at_formatted']
    
    def get_created_at_formatted(self, obj):
        """Return a human-readable date format"""
        return obj.created_at.strftime("%b %d, %Y %H:%M") 