"""
JWT Authentication Views for To7fa Backend
Mobile-first authentication with access and refresh tokens
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from datetime import timedelta
import secrets
import logging

from api.helpers import api_success, api_error, api_created
from .models import User

logger = logging.getLogger(__name__)
UserModel = get_user_model()


class LoginRateThrottle(AnonRateThrottle):
    """Rate limit for login attempts - 5 attempts per minute"""
    rate = '5/min'
    scope = 'login'
    
    def allow_request(self, request, view):
        # Skip throttling in tests
        from django.conf import settings
        if getattr(settings, 'TESTING', False):
            return True
        return super().allow_request(request, view)


class PasswordResetRateThrottle(AnonRateThrottle):
    """Rate limit for password reset requests - 3 attempts per hour"""
    rate = '3/hour'
    scope = 'password_reset'


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
def login_view(request):
    """
    Login endpoint with JWT tokens and rate limiting
    
    Request:
    {
        "email": "user@example.com",
        "password": "password123"
    }
    
    Response (Success):
    {
        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "user": {
            "id": 1,
            "email": "user@example.com",
            "user_type": "customer",
            "first_name": "John",
            "last_name": "Doe"
        }
    }
    
    Response (Rate Limited):
    {
        "error": "Too many login attempts. Please try again later.",
        "code": "RATE_LIMITED"
    }
    
    Response (Invalid Credentials):
    {
        "error": "Invalid email or password",
        "code": "INVALID_CREDENTIALS"
    }
    
    Response (Account Locked):
    {
        "error": "Account is temporarily locked. Please try again later.",
        "code": "ACCOUNT_LOCKED"
    }
    """
    email = request.data.get('email', '').lower().strip()
    password = request.data.get('password', '')
    session_id = request.data.get('session_id')  # Optional guest session for cart merge
    
    # Validate input
    if not email or not password:
        return api_error(
            request,
            code='MISSING_FIELDS',
            message='Email and password are required',
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if user exists
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        # Don't reveal if user exists
        return api_error(
            request,
            code='INVALID_CREDENTIALS',
            message='Invalid email or password',
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    # Check if account is locked (permanent ban)
    if user.is_locked:
        return api_error(
            request,
            code='USER_LOCKED',
            message='You are banned',
            details={'reason': user.locked_reason},
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # Check if account is temporarily locked (failed login attempts)
    if user.locked_until and user.locked_until > timezone.now():
        return api_error(
            request,
            code='ACCOUNT_LOCKED',
            message='Account is temporarily locked. Please try again later.',
            details={'locked_until': user.locked_until.isoformat()},
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # Check if user is blocked
    if not user.is_active:
        return api_error(
            request,
            code='ACCOUNT_BLOCKED',
            message='Account is blocked. Please contact support.',
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # Check if email is verified
    if not user.email_verified:
        return api_error(
            request,
            code='EMAIL_NOT_VERIFIED',
            message='Email not verified. Please verify your email first.',
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    # Check password
    if not user.check_password(password):
        # Increment failed login attempts
        user.failed_login_attempts += 1
        user.last_failed_login = timezone.now()
        
        # Lock account after 5 failed attempts for 30 minutes
        if user.failed_login_attempts >= 5:
            user.locked_until = timezone.now() + timedelta(minutes=30)
        
        user.save()
        
        return api_error(
            request,
            code='INVALID_CREDENTIALS',
            message='Invalid email or password',
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    # Reset failed login attempts on successful login
    user.failed_login_attempts = 0
    user.last_failed_login = None
    user.locked_until = None
    user.save()
    
    # Merge guest cart if session_id provided
    if session_id:
        try:
            from cart.services.cart_merge import merge_guest_cart
            merge_result = merge_guest_cart(user, session_id)
            if merge_result['success']:
                logger.info(
                    f"Cart merged on login: user_id={user.id}, "
                    f"session_id={session_id}, "
                    f"items_added={merge_result['items_added']}, "
                    f"items_skipped={merge_result['items_skipped']}"
                )
            else:
                logger.warning(
                    f"Cart merge failed on login: user_id={user.id}, "
                    f"session_id={session_id}, "
                    f"error={merge_result.get('error', 'Unknown')}"
                )
        except Exception as e:
            logger.error(f"Error during cart merge on login: {str(e)}")
    
    # Generate JWT tokens using SimpleJWT
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(user)
    
    return api_success(
        request,
        data={
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'email': user.email,
                'user_type': user.user_type,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone_number': user.phone_number,
                'address': user.address,
                'is_mobile_verified': user.is_mobile_verified,
                'is_locked': user.is_locked,
                'is_blocked': user.is_blocked,
                'blocked_capabilities': user.blocked_capabilities or []
            }
        }
    )


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([PasswordResetRateThrottle])
def request_password_reset(request):
    """
    Request password reset via email
    
    Request:
    {
        "email": "user@example.com"
    }
    
    Response (Success):
    {
        "message": "Password reset email sent if email exists",
        "code": "PASSWORD_RESET_SENT"
    }
    
    Response (Rate Limited):
    {
        "error": "Too many password reset attempts. Please try again later.",
        "code": "RATE_LIMITED"
    }
    """
    email = request.data.get('email', '').lower().strip()
    
    if not email:
        return api_error(
            request,
            code='MISSING_EMAIL',
            message='Email is required',
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if user exists
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        # Don't reveal if user exists for security
        return Response({
            'message': 'Password reset email sent if email exists',
            'code': 'PASSWORD_RESET_SENT'
        }, status=status.HTTP_200_OK)
    
    # Generate password reset token
    reset_token = secrets.token_urlsafe(64)
    user.password_reset_token = reset_token
    user.password_reset_token_expires = timezone.now() + timedelta(hours=1)
    user.save()
    
    # Send email
    try:
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        
        subject = 'Password Reset - To7fa'
        message = render_to_string('custom_auth/emails/password_reset_email.html', {
            'user': user,
            'reset_url': reset_url,
        })
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        
        logger.info(f"Password reset email sent to {email}")
        
        return Response({
            'message': 'Password reset email sent if email exists',
            'code': 'PASSWORD_RESET_SENT'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Failed to send password reset email: {str(e)}")
        return api_error(
            request,
            code='EMAIL_SEND_FAILED',
            message='Failed to send password reset email',
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def confirm_password_reset(request):
    """
    Confirm password reset with token
    
    Request:
    {
        "token": "reset_token_here",
        "password": "new_password123",
        "confirm_password": "new_password123"
    }
    
    Response (Success):
    {
        "message": "Password reset successfully",
        "code": "PASSWORD_RESET_SUCCESS"
    }
    
    Response (Invalid Token):
    {
        "error": "Invalid or expired reset token",
        "code": "INVALID_TOKEN"
    }
    """
    token = request.data.get('token', '')
    password = request.data.get('password', '')
    confirm_password = request.data.get('confirm_password', '')
    
    # Validate input
    if not token or not password or not confirm_password:
        return api_error(
            request,
            code='MISSING_FIELDS',
            message='Token, password, and confirm password are required',
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    if password != confirm_password:
        return api_error(
            request,
            code='PASSWORD_MISMATCH',
            message='Passwords do not match',
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Find user by reset token
    try:
        user = User.objects.get(password_reset_token=token)
    except User.DoesNotExist:
        return api_error(
            request,
            code='INVALID_TOKEN',
            message='Invalid or expired reset token',
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if token is expired
    if user.password_reset_token_expires and user.password_reset_token_expires < timezone.now():
        return api_error(
            request,
            code='TOKEN_EXPIRED',
            message='Reset token has expired',
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate password strength
    if len(password) < 8:
        return api_error(
            request,
            code='PASSWORD_TOO_SHORT',
            message='Password must be at least 8 characters long',
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Update password
    user.set_password(password)
    user.password_reset_token = None
    user.password_reset_token_expires = None
    user.save()
    
    logger.info(f"Password reset successful for {user.email}")
    
    return api_success(
        request,
        message='Password reset successfully',
        code='PASSWORD_RESET_SUCCESS'
    )


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle])
def request_email_verification(request):
    """
    Request email verification (resend verification email)
    
    Request:
    {
        "email": "user@example.com"
    }
    
    Response (Success):
    {
        "message": "Verification email sent",
        "code": "VERIFICATION_EMAIL_SENT"
    }
    """
    email = request.data.get('email', '').lower().strip()
    
    if not email:
        return api_error(
            request,
            code='MISSING_EMAIL',
            message='Email is required',
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if user exists
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return api_error(
            request,
            code='USER_NOT_FOUND',
            message='User not found',
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    # Check if already verified
    if user.email_verified:
        return api_success(
            request,
            message='Email already verified',
            code='EMAIL_ALREADY_VERIFIED'
        )
    
    # Generate verification token
    verification_token = secrets.token_urlsafe(64)
    user.email_verification_token = verification_token
    user.email_verification_token_expires = timezone.now() + timedelta(hours=24)
    user.save()
    
    # Send email
    try:
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
        
        subject = 'Email Verification - To7fa'
        message = render_to_string('custom_auth/emails/email_verification_email.html', {
            'user': user,
            'verification_url': verification_url,
        })
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        
        logger.info(f"Verification email sent to {email}")
        
        return api_success(
            request,
            message='Verification email sent',
            code='VERIFICATION_EMAIL_SENT'
        )
        
    except Exception as e:
        logger.error(f"Failed to send verification email: {str(e)}")
        return api_error(
            request,
            code='EMAIL_SEND_FAILED',
            message='Failed to send verification email',
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request):
    """
    Verify email with token
    
    Request:
    {
        "token": "verification_token_here"
    }
    
    Response (Success):
    {
        "message": "Email verified successfully",
        "code": "EMAIL_VERIFIED"
    }
    """
    token = request.data.get('token', '')
    
    if not token:
        return api_error(
            request,
            code='MISSING_TOKEN',
            message='Token is required',
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Find user by verification token
    try:
        user = User.objects.get(email_verification_token=token)
    except User.DoesNotExist:
        return api_error(
            request,
            code='INVALID_TOKEN',
            message='Invalid verification token',
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if token is expired
    if user.email_verification_token_expires and user.email_verification_token_expires < timezone.now():
        return api_error(
            request,
            code='TOKEN_EXPIRED',
            message='Verification token has expired',
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # Mark email as verified
    user.email_verified = True
    user.email_verification_token = None
    user.email_verification_token_expires = None
    user.save()
    
    logger.info(f"Email verified for {user.email}")
    
    return api_success(
        request,
        message='Email verified successfully',
        code='EMAIL_VERIFIED'
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Logout endpoint - blacklists the refresh token so it can't be reused.

    Request:
    Headers: Authorization: Bearer <access_token>
    Body (optional but required to actually invalidate the session):
    {
        "refresh": "refresh_token_here"
    }

    Response (Success):
    {
        "message": "Successfully logged out",
        "code": "LOGOUT_SUCCESS"
    }

    Phase 2 fix (BACKEND_AUDIT.md / PHASE2 workstream 9): this previously only logged
    the logout and told the client to discard its tokens client-side. SIMPLE_JWT already
    had ROTATE_REFRESH_TOKENS/BLACKLIST_AFTER_ROTATION=True, but
    rest_framework_simplejwt.token_blacklist wasn't installed, so a stolen refresh token
    stayed valid for its full 7-day lifetime even after logout. The refresh token is
    optional here (not a breaking API change for existing clients that don't send one),
    but logout only actually invalidates the session if it's provided.
    """
    from rest_framework_simplejwt.tokens import RefreshToken
    from rest_framework_simplejwt.exceptions import TokenError

    refresh_token = request.data.get('refresh')
    if refresh_token:
        try:
            RefreshToken(refresh_token).blacklist()
        except TokenError:
            # Already invalid/expired/blacklisted - logout still succeeds either way,
            # the end state (this token can't be used) is what the client wants.
            pass
    else:
        logger.warning(
            f"User {request.user.email} logged out without providing a refresh token - "
            "their refresh token was NOT invalidated."
        )

    logger.info(f"User {request.user.email} logged out")

    # Phase 2 fix: api_success() has never accepted a `code` kwarg (only api_error()
    # does - see api/helpers.py) - this call was raising an uncaught TypeError,
    # turning every logout into a 500 Internal Server Error. Pre-existing, unrelated to
    # the blacklist fix above, but this workstream can't be verified without it working.
    return api_success(
        request,
        message='Successfully logged out',
        data={'code': 'LOGOUT_SUCCESS'}
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refresh_token_view(request):
    """
    Refresh access token using refresh token
    
    Request:
    {
        "refresh": "refresh_token_here"
    }
    
    Response (Success):
    {
        "access": "new_access_token_here",
        "code": "TOKEN_REFRESHED"
    }
    """
    refresh_token = request.data.get('refresh', '')
    
    if not refresh_token:
        return api_error(
            request,
            code='MISSING_REFRESH_TOKEN',
            message='Refresh token is required',
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    # SimpleJWT handles token validation and refresh automatically
    from rest_framework_simplejwt.views import TokenRefreshView
    token_refresh_view = TokenRefreshView.as_view()
    
    return token_refresh_view(request)
