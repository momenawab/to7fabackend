from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import SupportCategory, SupportTicket, SupportMessage, SupportAttachment

User = get_user_model()


class SupportCategorySerializer(serializers.ModelSerializer):
    """Serializer for support categories"""
    
    class Meta:
        model = SupportCategory
        fields = ['id', 'name', 'description', 'icon', 'color']


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user info for support tickets"""
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name']


class SupportAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for support attachments"""
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = SupportAttachment
        fields = [
            'id', 'file_url', 'original_filename', 'file_size_formatted', 
            'content_type', 'is_image', 'uploaded_at'
        ]
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class SupportMessageSerializer(serializers.ModelSerializer):
    """Serializer for support messages"""
    sender = UserBasicSerializer(read_only=True)
    attachments = SupportAttachmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = SupportMessage
        fields = [
            'id', 'sender', 'message', 'message_type', 'is_internal',
            'attachments', 'created_at', 'updated_at'
        ]


class SupportTicketSerializer(serializers.ModelSerializer):
    """Serializer for support tickets list view"""
    user = UserBasicSerializer(read_only=True)
    category = SupportCategorySerializer(read_only=True)
    assigned_to = UserBasicSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    status_color = serializers.CharField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    message_count = serializers.SerializerMethodField()
    last_message_at = serializers.SerializerMethodField()
    
    class Meta:
        model = SupportTicket
        fields = [
            'ticket_id', 'uuid', 'subject', 'user', 'category', 'status', 
            'status_display', 'status_color', 'order_id', 'assigned_to', 
            'is_overdue', 'message_count', 'last_message_at', 'created_at', 
            'updated_at', 'rating'
        ]
    
    def get_message_count(self, obj):
        return obj.messages.count()
    
    def get_last_message_at(self, obj):
        last_message = obj.messages.last()
        return last_message.created_at if last_message else obj.created_at


class SupportTicketDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single ticket view"""
    user = UserBasicSerializer(read_only=True)
    category = SupportCategorySerializer(read_only=True)
    assigned_to = UserBasicSerializer(read_only=True)
    messages = SupportMessageSerializer(many=True, read_only=True)
    attachments = SupportAttachmentSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    status_color = serializers.CharField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = SupportTicket
        fields = [
            'ticket_id', 'uuid', 'subject', 'description', 'user', 'category',
            'status', 'status_display', 'status_color', 'order_id', 'assigned_to', 
            'messages', 'attachments', 'is_overdue', 'rating', 'feedback', 
            'created_at', 'updated_at', 'resolved_at', 'closed_at'
        ]


class CreateTicketSerializer(serializers.ModelSerializer):
    """Serializer for creating new support tickets"""
    
    class Meta:
        model = SupportTicket
        fields = ['category', 'subject', 'description', 'order_id']
    
    def validate_subject(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Subject must be at least 5 characters long")
        return value.strip()
    
    def validate_description(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Description must be at least 10 characters long")
        return value.strip()


class CreateMessageSerializer(serializers.ModelSerializer):
    """Serializer for creating new messages"""
    
    class Meta:
        model = SupportMessage
        fields = ['message']
    
    def validate_message(self, value):
        if len(value.strip()) < 1:
            raise serializers.ValidationError("Message cannot be empty")
        return value.strip()


class TicketUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating ticket status/assignment"""
    
    class Meta:
        model = SupportTicket
        fields = ['status', 'assigned_to', 'order_id']
    
    def validate_status(self, value):
        allowed_statuses = ['open', 'in_progress', 'waiting_customer', 'resolved', 'closed']
        if value not in allowed_statuses:
            raise serializers.ValidationError(f"Status must be one of: {', '.join(allowed_statuses)}")
        return value