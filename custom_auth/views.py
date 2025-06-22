from django.shortcuts import render, redirect
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import User, Customer, Artist, Store
from .serializers import UserRegistrationSerializer, UserProfileSerializer, CustomerProfileSerializer, ArtistRegistrationSerializer, StoreRegistrationSerializer
from django.db import IntegrityError, transaction
import logging
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.utils import timezone
from admin_panel.models import SellerApplication, AdminNotification
from django.contrib import messages
from products.models import Category

logger = logging.getLogger(__name__)
User = get_user_model()

# Create your views here.

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """Register a new user (customer)"""
    # Log the request data for debugging
    logger.debug(f"Registration attempt with data: {request.data}")
    
    # First check if the email already exists to provide a clearer error message
    email = request.data.get('email', '').lower().strip()
    if email and User.objects.filter(email__iexact=email).exists():
        return Response({
            "email": [f"A user with the email '{email}' already exists."]
        }, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        try:
            with transaction.atomic():
                user = serializer.save()
                
                # Prepare response data
                response_data = {
                    "message": "User registered successfully",
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "user_type": user.user_type,
                        "phone_number": user.phone_number,
                        "address": user.address
                    }
                }
                
                return Response(response_data, status=status.HTTP_201_CREATED)
        except IntegrityError as e:
            logger.error(f"IntegrityError during registration: {str(e)}")
            error_msg = str(e)
            if "custom_auth_customer.user_id" in error_msg:
                # Handle the specific case where a customer profile already exists
                return Response({
                    "error": "This user already has a customer profile. Please try logging in instead."
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    "email": [f"Registration failed due to a database constraint: {str(e)}"]
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error during registration: {str(e)}")
            return Response({
                "error": f"An unexpected error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Log validation errors
    logger.debug(f"Validation errors: {serializer.errors}")
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """Get or update user profile based on user_type"""
    user = request.user
    
    if request.method == 'GET':
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_seller(request):
    """Redirect to the seller application form"""
    # Instead of directly changing user type, redirect to the application form
    return Response({
        "message": "Please complete the seller application form",
        "redirect": "/seller/apply/"
    }, status=status.HTTP_302_FOUND)

@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    """Request password reset"""
    # This will be implemented with serializers
    return Response({"message": "Password reset email sent successfully"}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    """Confirm password reset"""
    # This will be implemented with serializers
    return Response({"message": "Password reset successfully"}, status=status.HTTP_200_OK)

class LoginView(ObtainAuthToken):
    """
    Custom login view that returns the token and user information
    """
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email,
            'user_type': user.user_type,
            'first_name': user.first_name,
            'last_name': user.last_name
        })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Logout the user by deleting their token
    """
    try:
        request.user.auth_token.delete()
        return Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SellerApplicationView(APIView):
    """View for handling seller applications (artist or store)"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Render the seller application form"""
        # Check if user already has a pending application
        has_pending = SellerApplication.objects.filter(
            user=request.user, 
            status='pending'
        ).exists()
        
        if has_pending:
            messages.warning(request, "You already have a pending seller application. Please wait for it to be processed.")
            return redirect('application_status')
        
        # Check if user is already a seller
        if request.user.user_type in ['artist', 'store']:
            messages.info(request, "You are already registered as a seller.")
            return redirect('user_profile')
        
        # Get categories for the form
        categories = Category.objects.filter(is_active=True).order_by('name')
        
        # List of Egyptian governorates
        governorates = [
            'Cairo', 'Alexandria', 'Giza', 'Qalyubia', 'Sharqia',
            'Dakahlia', 'Gharbia', 'Menoufia', 'Beheira', 'Kafr El Sheikh',
            'Damietta', 'Port Said', 'Ismailia', 'Suez', 'North Sinai',
            'South Sinai', 'Beni Suef', 'Fayoum', 'Minya', 'Assiut',
            'Sohag', 'Qena', 'Luxor', 'Aswan', 'Red Sea',
            'New Valley', 'Matrouh'
        ]
        
        context = {
            'categories': categories,
            'governorates': governorates
        }
        
        return render(request, 'custom_auth/seller_application.html', context)
    
    def post(self, request):
        """Process the seller application form submission"""
        try:
            with transaction.atomic():
                user_type = request.POST.get('user_type')
                
                if user_type not in ['artist', 'store']:
                    messages.error(request, "Invalid seller type selected.")
                    return redirect('seller_apply')
                
                # Create application object
                application = SellerApplication(
                    user=request.user,
                    user_type=user_type,
                    name=request.POST.get('name'),
                    email=request.POST.get('email'),
                    phone_number=request.POST.get('phone_number'),
                    address=request.POST.get('address'),
                    shipping_company=request.POST.get('shipping_company'),
                    details=request.POST.get('details')
                )
                
                # Handle photo upload
                if 'photo' in request.FILES:
                    application.photo = request.FILES['photo']
                
                # Process shipping costs
                shipping_costs = {}
                for key, value in request.POST.items():
                    if key.startswith('governorate_name_'):
                        index = key.split('_')[-1]
                        cost_key = f'governorate_cost_{index}'
                        if cost_key in request.POST:
                            governorate = request.POST[key]
                            cost = request.POST[cost_key]
                            shipping_costs[governorate] = float(cost)
                
                application.shipping_costs = shipping_costs
                
                # Process categories
                categories = request.POST.getlist('categories')
                application.categories = categories
                
                # Handle artist specific fields
                if user_type == 'artist':
                    application.specialty = request.POST.get('specialty')
                    application.bio = request.POST.get('bio')
                
                # Handle store specific fields
                elif user_type == 'store':
                    application.store_name = request.POST.get('store_name')
                    application.tax_id = request.POST.get('tax_id')
                    application.has_physical_store = 'has_physical_store' in request.POST
                    
                    if application.has_physical_store:
                        application.physical_address = request.POST.get('physical_address')
                
                application.save()
                
                # Create admin notification
                AdminNotification.objects.create(
                    title="New Seller Application",
                    message=f"New {user_type} application submitted by {request.user.email}",
                    notification_type="new_application",
                    link=f"/dashboard/applications/{application.id}/"
                )
                
                messages.success(request, "Your seller application has been submitted successfully. We will review it shortly.")
                return redirect('application_status')
                
        except Exception as e:
            logger.error(f"Error processing seller application: {str(e)}")
            messages.error(request, "There was an error processing your application. Please try again.")
            return redirect('seller_apply')

class ApplicationStatusView(APIView):
    """View for checking seller application status"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Render the application status page"""
        # Get the user's most recent application
        application = SellerApplication.objects.filter(
            user=request.user
        ).order_by('-submitted_at').first()
        
        context = {
            'application': application
        }
        
        return render(request, 'custom_auth/application_status.html', context)
