# Contact support views for admin panel

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.core.paginator import Paginator
from support.models import ContactRequest, ContactNote
from custom_auth.models import User
from .decorators import admin_required

def is_admin(user):
    """Check if user is admin"""
    if user.is_staff or user.is_superuser:
        return True
    try:
        admin_profile = user.admin_profile
        return admin_profile.is_active and admin_profile.can_login
    except AttributeError:
        return False

@admin_required('support_contacts')
def support_contacts(request):
    """View for managing contact requests"""
    status_filter = request.GET.get('status', 'all')
    priority_filter = request.GET.get('priority', 'all')
    search_query = request.GET.get('q', '')
    
    # Base queryset
    contacts = ContactRequest.objects.select_related('user').prefetch_related('notes')
    
    # Apply filters
    if status_filter != 'all':
        contacts = contacts.filter(status=status_filter)
    
    if priority_filter != 'all':
        contacts = contacts.filter(priority=priority_filter)
    
    if search_query:
        contacts = contacts.filter(
            Q(contact_number__icontains=search_query) |
            Q(name__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(subject__icontains=search_query) |
            Q(message__icontains=search_query)
        )
    
    contacts = contacts.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(contacts, 15)
    page_number = request.GET.get('page', 1)
    contacts_page = paginator.get_page(page_number)
    
    # Statistics
    stats = {
        'total': ContactRequest.objects.count(),
        'new': ContactRequest.objects.filter(status='new').count(),
        'in_progress': ContactRequest.objects.filter(status='in_progress').count(),
        'contacted': ContactRequest.objects.filter(status='contacted').count(),
        'resolved': ContactRequest.objects.filter(status='resolved').count(),
        'high_priority': ContactRequest.objects.filter(priority='high').count(),
        'medium_priority': ContactRequest.objects.filter(priority='medium').count(),
        'low_priority': ContactRequest.objects.filter(priority='low').count(),
    }
    
    context = {
        'contacts': contacts_page,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'search_query': search_query,
        'stats': stats,
        'active_tab': 'support'
    }
    
    return render(request, 'admin_panel/support_contacts.html', context)

@admin_required('support_contacts')
def support_contact_detail(request, contact_id):
    """View detailed information about a contact request"""
    contact = get_object_or_404(
        ContactRequest.objects.select_related('user').prefetch_related('notes'),
        contact_number=contact_id
    )
    
    context = {
        'contact': contact,
        'active_tab': 'support'
    }
    
    return render(request, 'admin_panel/support_contact_detail.html', context)

@admin_required('support_contacts')
@require_POST
def update_contact_status(request, contact_id):
    """Update contact status and add notes"""
    contact = get_object_or_404(ContactRequest, contact_number=contact_id)
    
    new_status = request.POST.get('status')
    new_priority = request.POST.get('priority')
    note_content = request.POST.get('note', '').strip()
    
    try:
        # Update status if provided
        if new_status and new_status in dict(ContactRequest.STATUS_CHOICES):
            contact.status = new_status
        
        # Update priority if provided  
        if new_priority and new_priority in dict(ContactRequest.PRIORITY_CHOICES):
            contact.priority = new_priority
        
        contact.save()
        
        # Add note if provided
        if note_content:
            ContactNote.objects.create(
                contact=contact,
                admin_user=request.user,
                note=note_content,
                note_type='admin_note'
            )
        
        return JsonResponse({
            'success': True,
            'message': 'Contact updated successfully',
            'status': contact.get_status_display(),
            'priority': contact.get_priority_display()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@admin_required('support_contacts')
def send_typing_indicator(request, contact_id):
    """Legacy typing indicator function - not needed for new contact system"""
    return JsonResponse({'success': True, 'message': 'Typing indicator not needed for contact system'})