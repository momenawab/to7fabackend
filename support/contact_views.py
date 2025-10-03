from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator
from .contact_models import ContactRequest, ContactNote, ContactStats
from .contact_serializers import ContactRequestSerializer, ContactNoteSerializer


class CreateContactView(APIView):
    """Create a new contact request"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        try:
            # Get client IP and user agent
            ip_address = self.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Prepare data
            data = request.data.copy()
            
            # Add metadata
            contact_data = {
                'name': data.get('name', '').strip(),
                'phone': data.get('phone', '').strip(),
                'subject': data.get('subject', '').strip(),
                'message': data.get('message', '').strip(),
                'ip_address': ip_address,
                'user_agent': user_agent,
            }
            
            # Add user if authenticated
            if request.user.is_authenticated:
                contact_data['user'] = request.user.id
            
            # Validate required fields
            required_fields = ['name', 'phone', 'subject', 'message']
            missing_fields = [field for field in required_fields if not contact_data.get(field)]
            
            if missing_fields:
                return Response({
                    'success': False,
                    'errors': {field: 'This field is required.' for field in missing_fields}
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate phone number
            phone = contact_data['phone']
            # Remove all non-digit characters
            clean_phone = ''.join(filter(str.isdigit, phone))
            if len(clean_phone) < 10:
                return Response({
                    'success': False,
                    'errors': {'phone': 'Please enter a valid phone number.'}
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create contact request
            serializer = ContactRequestSerializer(data=contact_data)
            if serializer.is_valid():
                contact = serializer.save()
                
                # Update daily stats
                ContactStats.update_daily_stats()
                
                return Response({
                    'success': True,
                    'message': 'Contact request submitted successfully. We will contact you via WhatsApp within 24 hours.',
                    'contact_number': contact.contact_number,
                    'data': ContactRequestSerializer(contact).data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'success': False,
                'message': 'An error occurred while processing your request.',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ContactListView(APIView):
    """List contact requests (admin only)"""
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        try:
            # Filter parameters
            status_filter = request.GET.get('status', '')
            priority_filter = request.GET.get('priority', '')
            assigned_to = request.GET.get('assigned_to', '')
            search = request.GET.get('search', '')
            
            # Base queryset
            queryset = ContactRequest.objects.all().select_related('user', 'assigned_to')
            
            # Apply filters
            if status_filter and status_filter != 'all':
                queryset = queryset.filter(status=status_filter)
            
            if priority_filter and priority_filter != 'all':
                queryset = queryset.filter(priority=priority_filter)
            
            if assigned_to:
                if assigned_to == 'me':
                    queryset = queryset.filter(assigned_to=request.user)
                elif assigned_to == 'unassigned':
                    queryset = queryset.filter(assigned_to__isnull=True)
                else:
                    queryset = queryset.filter(assigned_to_id=assigned_to)
            
            if search:
                queryset = queryset.filter(
                    Q(contact_number__icontains=search) |
                    Q(name__icontains=search) |
                    Q(phone__icontains=search) |
                    Q(subject__icontains=search) |
                    Q(message__icontains=search)
                )
            
            # Pagination
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))
            
            total = queryset.count()
            start = (page - 1) * page_size
            end = start + page_size
            
            contacts = queryset[start:end]
            
            # Serialize data
            serialized_contacts = ContactRequestSerializer(contacts, many=True).data
            
            return Response({
                'success': True,
                'data': {
                    'contacts': serialized_contacts,
                    'pagination': {
                        'current_page': page,
                        'total_pages': (total + page_size - 1) // page_size,
                        'total_contacts': total,
                        'has_next': end < total,
                        'has_previous': page > 1
                    }
                }
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Error fetching contact requests.',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ContactDetailView(APIView):
    """Get, update, or delete a specific contact request"""
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request, contact_number):
        try:
            contact = get_object_or_404(ContactRequest, contact_number=contact_number)
            serializer = ContactRequestSerializer(contact)
            
            # Get notes
            notes = ContactNote.objects.filter(contact=contact).select_related('author')
            notes_data = ContactNoteSerializer(notes, many=True).data
            
            return Response({
                'success': True,
                'data': {
                    'contact': serializer.data,
                    'notes': notes_data
                }
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Error fetching contact details.',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def patch(self, request, contact_number):
        try:
            contact = get_object_or_404(ContactRequest, contact_number=contact_number)
            
            # Update allowed fields
            allowed_fields = ['status', 'priority', 'assigned_to', 'admin_notes', 'whatsapp_conversation_id']
            update_data = {field: request.data[field] for field in allowed_fields if field in request.data}
            
            # Handle status changes
            old_status = contact.status
            new_status = update_data.get('status', old_status)
            
            # Set timestamps based on status changes
            if new_status != old_status:
                if new_status == 'contacted' and not contact.contacted_at:
                    contact.contacted_at = timezone.now()
                elif new_status == 'resolved' and not contact.resolved_at:
                    contact.resolved_at = timezone.now()
                elif new_status == 'closed' and not contact.closed_at:
                    contact.closed_at = timezone.now()
                
                # Create note for status change
                ContactNote.objects.create(
                    contact=contact,
                    author=request.user,
                    note=f"Status changed from '{old_status}' to '{new_status}' by {request.user.get_full_name()}",
                    note_type='update'
                )
            
            # Update contact
            for field, value in update_data.items():
                setattr(contact, field, value)
            
            contact.save()
            
            # Update daily stats
            ContactStats.update_daily_stats()
            
            return Response({
                'success': True,
                'message': 'Contact updated successfully.',
                'data': ContactRequestSerializer(contact).data
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Error updating contact.',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ContactStatsView(APIView):
    """Get contact statistics"""
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        try:
            # Get date range
            from datetime import datetime, timedelta
            
            days = int(request.GET.get('days', 30))
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=days-1)
            
            # Get all contacts in range
            contacts = ContactRequest.objects.filter(created_at__date__gte=start_date)
            
            # Calculate stats
            stats = {
                'total_contacts': contacts.count(),
                'new_contacts': contacts.filter(status='new').count(),
                'contacted_contacts': contacts.filter(status='contacted').count(),
                'resolved_contacts': contacts.filter(status='resolved').count(),
                'closed_contacts': contacts.filter(status='closed').count(),
                'overdue_contacts': sum(1 for c in contacts.filter(status='new') if c.is_overdue),
            }
            
            # Priority breakdown
            stats['priority_breakdown'] = {
                'low': contacts.filter(priority='low').count(),
                'normal': contacts.filter(priority='normal').count(),
                'high': contacts.filter(priority='high').count(),
                'urgent': contacts.filter(priority='urgent').count(),
            }
            
            # Daily stats
            daily_stats = []
            for i in range(days):
                date = start_date + timedelta(days=i)
                day_contacts = contacts.filter(created_at__date=date)
                
                daily_stats.append({
                    'date': date.isoformat(),
                    'total': day_contacts.count(),
                    'new': day_contacts.filter(status='new').count(),
                    'contacted': day_contacts.filter(status='contacted').count(),
                    'resolved': day_contacts.filter(status='resolved').count(),
                })
            
            stats['daily_stats'] = daily_stats
            
            # Response time stats (for contacted requests)
            contacted_requests = contacts.filter(contacted_at__isnull=False)
            if contacted_requests.exists():
                response_times = []
                for contact in contacted_requests:
                    if contact.response_time:
                        delta = contact.contacted_at - contact.created_at
                        response_times.append(delta.total_seconds() / 3600)  # in hours
                
                if response_times:
                    stats['avg_response_time_hours'] = sum(response_times) / len(response_times)
                    stats['min_response_time_hours'] = min(response_times)
                    stats['max_response_time_hours'] = max(response_times)
            
            return Response({
                'success': True,
                'data': stats
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Error fetching statistics.',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def add_contact_note(request, contact_number):
    """Add a note to a contact request"""
    try:
        contact = get_object_or_404(ContactRequest, contact_number=contact_number)
        
        note_data = {
            'contact': contact.id,
            'author': request.user.id,
            'note': request.data.get('note', '').strip(),
            'note_type': request.data.get('note_type', 'internal')
        }
        
        if not note_data['note']:
            return Response({
                'success': False,
                'errors': {'note': 'Note content is required.'}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = ContactNoteSerializer(data=note_data)
        if serializer.is_valid():
            note = serializer.save()
            return Response({
                'success': True,
                'message': 'Note added successfully.',
                'data': ContactNoteSerializer(note).data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response({
            'success': False,
            'message': 'Error adding note.',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def get_whatsapp_link(request, contact_number):
    """Get WhatsApp link for a contact"""
    try:
        contact = get_object_or_404(ContactRequest, contact_number=contact_number)
        
        return Response({
            'success': True,
            'data': {
                'whatsapp_url': contact.whatsapp_url,
                'phone': contact.phone,
                'name': contact.name
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': 'Error generating WhatsApp link.',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserContactListView(APIView):
    """List user's own contact requests"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        try:
            # Filter parameters
            status_filter = request.GET.get('status', '')
            page = int(request.GET.get('page', 1))
            page_size = min(int(request.GET.get('page_size', 20)), 100)  # Max 100 per page
            
            # Get user's contact requests (both authenticated user and phone/email matches)
            queryset = ContactRequest.objects.filter(
                Q(user=request.user) |
                Q(phone=getattr(request.user, 'phone', '')) |
                Q(name__icontains=request.user.get_full_name()) if request.user.get_full_name() else Q()
            ).distinct()
            
            # Apply status filter
            if status_filter and status_filter != 'all':
                queryset = queryset.filter(status=status_filter)
            
            # Order by most recent first
            queryset = queryset.order_by('-created_at')
            
            # Pagination
            paginator = Paginator(queryset, page_size)
            try:
                contacts_page = paginator.page(page)
            except:
                contacts_page = paginator.page(1)
            
            # Serialize data
            serializer = ContactRequestSerializer(contacts_page.object_list, many=True)
            
            return Response({
                'success': True,
                'data': {
                    'contacts': serializer.data,
                    'pagination': {
                        'current_page': contacts_page.number,
                        'total_pages': paginator.num_pages,
                        'total_count': paginator.count,
                        'has_previous': contacts_page.has_previous(),
                        'has_next': contacts_page.has_next(),
                        'page_size': page_size
                    }
                },
                'message': f'Found {paginator.count} contact request(s)'
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Error fetching contact requests.',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)