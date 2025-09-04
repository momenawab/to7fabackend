from rest_framework import serializers
from django.contrib.auth import get_user_model
from .contact_models import ContactRequest, ContactNote, ContactStats

User = get_user_model()


class SimpleUserSerializer(serializers.ModelSerializer):
    """Simple user serializer for contact requests"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.email


class ContactRequestSerializer(serializers.ModelSerializer):
    """Serializer for contact requests"""
    user_details = SimpleUserSerializer(source='user', read_only=True)
    assigned_to_details = SimpleUserSerializer(source='assigned_to', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_color = serializers.ReadOnlyField()
    priority_color = serializers.ReadOnlyField()
    whatsapp_url = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    response_time = serializers.ReadOnlyField()
    
    class Meta:
        model = ContactRequest
        fields = [
            'id', 'contact_number', 'name', 'phone', 'subject', 'message',
            'status', 'status_display', 'status_color',
            'priority', 'priority_display', 'priority_color',
            'user', 'user_details', 'assigned_to', 'assigned_to_details',
            'admin_notes', 'whatsapp_conversation_id',
            'created_at', 'contacted_at', 'resolved_at', 'closed_at',
            'whatsapp_url', 'is_overdue', 'response_time',
            'ip_address', 'user_agent'
        ]
        read_only_fields = [
            'id', 'contact_number', 'created_at', 'contacted_at', 
            'resolved_at', 'closed_at', 'whatsapp_url', 'is_overdue', 
            'response_time', 'status_color', 'priority_color',
            'status_display', 'priority_display'
        ]
    
    def validate_phone(self, value):
        """Validate phone number"""
        if not value:
            raise serializers.ValidationError("Phone number is required.")
        
        # Clean phone number (remove non-digits)
        clean_phone = ''.join(filter(str.isdigit, value))
        
        if len(clean_phone) < 10:
            raise serializers.ValidationError("Please enter a valid phone number.")
        
        return value
    
    def validate_name(self, value):
        """Validate name"""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("Please enter a valid name (at least 2 characters).")
        return value.strip()
    
    def validate_subject(self, value):
        """Validate subject"""
        if not value or len(value.strip()) < 5:
            raise serializers.ValidationError("Subject must be at least 5 characters long.")
        return value.strip()
    
    def validate_message(self, value):
        """Validate message"""
        if not value or len(value.strip()) < 10:
            raise serializers.ValidationError("Message must be at least 10 characters long.")
        return value.strip()


class ContactNoteSerializer(serializers.ModelSerializer):
    """Serializer for contact notes"""
    author_details = SimpleUserSerializer(source='author', read_only=True)
    note_type_display = serializers.CharField(source='get_note_type_display', read_only=True)
    
    class Meta:
        model = ContactNote
        fields = [
            'id', 'contact', 'note', 'note_type', 'note_type_display',
            'author', 'author_details', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'author_details', 'note_type_display']
    
    def validate_note(self, value):
        """Validate note content"""
        if not value or len(value.strip()) < 3:
            raise serializers.ValidationError("Note must be at least 3 characters long.")
        return value.strip()


class ContactStatsSerializer(serializers.ModelSerializer):
    """Serializer for contact statistics"""
    
    class Meta:
        model = ContactStats
        fields = [
            'date', 'total_requests', 'new_requests', 'contacted_requests',
            'resolved_requests', 'closed_requests', 'overdue_requests',
            'avg_response_time_minutes', 'avg_resolution_time_hours'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ContactDashboardSerializer(serializers.Serializer):
    """Serializer for dashboard statistics"""
    total_contacts = serializers.IntegerField()
    new_contacts = serializers.IntegerField()
    contacted_contacts = serializers.IntegerField()
    resolved_contacts = serializers.IntegerField()
    closed_contacts = serializers.IntegerField()
    overdue_contacts = serializers.IntegerField()
    
    priority_breakdown = serializers.DictField()
    daily_stats = serializers.ListField()
    
    avg_response_time_hours = serializers.FloatField(required=False)
    min_response_time_hours = serializers.FloatField(required=False)
    max_response_time_hours = serializers.FloatField(required=False)


class BulkContactActionSerializer(serializers.Serializer):
    """Serializer for bulk actions on contacts"""
    action = serializers.ChoiceField(choices=[
        ('mark_contacted', 'Mark as Contacted'),
        ('mark_resolved', 'Mark as Resolved'), 
        ('mark_closed', 'Mark as Closed'),
        ('assign', 'Assign'),
        ('set_priority', 'Set Priority'),
    ])
    contact_numbers = serializers.ListField(
        child=serializers.CharField(),
        min_length=1
    )
    
    # Optional fields based on action
    assigned_to = serializers.IntegerField(required=False)
    priority = serializers.ChoiceField(
        choices=['low', 'normal', 'high', 'urgent'],
        required=False
    )
    
    def validate(self, data):
        """Validate based on action type"""
        action = data.get('action')
        
        if action == 'assign' and 'assigned_to' not in data:
            raise serializers.ValidationError({
                'assigned_to': 'assigned_to is required for assign action'
            })
        
        if action == 'set_priority' and 'priority' not in data:
            raise serializers.ValidationError({
                'priority': 'priority is required for set_priority action'
            })
        
        return data


class ContactFilterSerializer(serializers.Serializer):
    """Serializer for contact filtering"""
    status = serializers.ChoiceField(
        choices=['all', 'new', 'contacted', 'resolved', 'closed'],
        default='all',
        required=False
    )
    priority = serializers.ChoiceField(
        choices=['all', 'low', 'normal', 'high', 'urgent'],
        default='all',
        required=False
    )
    assigned_to = serializers.CharField(required=False)
    search = serializers.CharField(required=False)
    page = serializers.IntegerField(min_value=1, default=1, required=False)
    page_size = serializers.IntegerField(min_value=1, max_value=100, default=20, required=False)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    
    def validate(self, data):
        """Validate date range"""
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise serializers.ValidationError({
                'date_from': 'Start date cannot be after end date'
            })
        
        return data


class WhatsAppLinkSerializer(serializers.Serializer):
    """Serializer for WhatsApp link response"""
    whatsapp_url = serializers.URLField()
    phone = serializers.CharField()
    name = serializers.CharField()
    
    
class ContactSummarySerializer(serializers.Serializer):
    """Serializer for contact summary in lists"""
    id = serializers.UUIDField()
    contact_number = serializers.CharField()
    name = serializers.CharField()
    subject = serializers.CharField()
    phone = serializers.CharField()
    status = serializers.CharField()
    status_display = serializers.CharField()
    status_color = serializers.CharField()
    priority = serializers.CharField()
    priority_display = serializers.CharField()
    priority_color = serializers.CharField()
    is_overdue = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    whatsapp_url = serializers.CharField()
    assigned_to_name = serializers.SerializerMethodField()
    
    def get_assigned_to_name(self, obj):
        if hasattr(obj, 'assigned_to') and obj.assigned_to:
            return obj.assigned_to.get_full_name() or obj.assigned_to.email
        return None