"""
Push notification utilities for FCM (Android) and APNs (iOS)
Supports Firebase Cloud Messaging HTTP v1 API and Apple Push Notification service
"""
import json
import requests
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from django.conf import settings

# Firebase Admin SDK imports
try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    FIREBASE_ADMIN_AVAILABLE = True
except ImportError:
    FIREBASE_ADMIN_AVAILABLE = False
from django.utils import timezone
from .models import Device, PushNotificationLog, Notification

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK
firebase_app = None
if FIREBASE_ADMIN_AVAILABLE and hasattr(settings, 'FCM_SERVICE_ACCOUNT_FILE') and settings.FCM_SERVICE_ACCOUNT_FILE:
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(settings.FCM_SERVICE_ACCOUNT_FILE)
            firebase_app = firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK initialized successfully")
        else:
            firebase_app = firebase_admin.get_app()
    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
        firebase_app = None

class PushNotificationError(Exception):
    """Custom exception for push notification errors"""
    pass


class FCMService:
    """Firebase Cloud Messaging service for Android push notifications"""
    
    def __init__(self):
        self.server_key = getattr(settings, 'FCM_SERVER_KEY', None)
        self.project_id = getattr(settings, 'FCM_PROJECT_ID', None)
        
        if not self.server_key:
            logger.warning("FCM_SERVER_KEY not configured in settings")
        if not self.project_id:
            logger.warning("FCM_PROJECT_ID not configured in settings")
    
    def _get_access_token(self) -> str:
        """
        Get access token for FCM HTTP v1 API using service account
        This is a simplified version - in production, use proper OAuth2 flow
        """
        # For now, use the legacy server key
        # In production, implement proper OAuth2 with service account JSON
        return self.server_key
    
    def send_to_device_admin_sdk(self, device_token: str, title: str, 
                                body: str, data: Dict = None) -> Tuple[bool, Dict]:
        """
        Send push notification using Firebase Admin SDK (Modern method)
        """
        if not firebase_app:
            return False, {'error': 'Firebase Admin SDK not initialized'}
        
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data={
                    'title': title,
                    'body': body,
                    'click_action': 'FLUTTER_NOTIFICATION_CLICK',
                    **(data or {})
                },
                token=device_token,
                android=messaging.AndroidConfig(
                    notification=messaging.AndroidNotification(
                        title=title,
                        body=body,
                        icon='ic_notification',
                        color='#072025',
                        sound='default',
                        channel_id='high_importance_channel',
                        default_sound=True,
                        default_vibrate_timings=True,
                        default_light_settings=True,
                    ),
                    priority='high',
                    data={
                        'title': title,
                        'body': body,
                        'click_action': 'FLUTTER_NOTIFICATION_CLICK',
                        **(data or {})
                    }
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            alert=messaging.ApsAlert(
                                title=title,
                                body=body,
                            ),
                            badge=1,
                            sound='default',
                            content_available=True,
                        )
                    ),
                    headers={'apns-priority': '10'}
                )
            )
            
            response = messaging.send(message)
            logger.info(f"FCM notification sent successfully via Admin SDK: {response}")
            return True, {'message_id': response}
            
        except Exception as e:
            logger.error(f"FCM Admin SDK notification failed: {e}")
            return False, {'error': str(e)}

    def send_to_device(self, device_token: str, title: str, body: str, 
                      data: Dict = None, priority: str = 'high') -> Tuple[bool, Dict]:
        """
        Send push notification to a single Android device
        
        Args:
            device_token: FCM device token
            title: Notification title
            body: Notification body
            data: Additional data payload
            priority: Notification priority ('high' or 'normal')
        
        Returns:
            Tuple of (success: bool, response: dict)
        """
        # Try Admin SDK first (preferred method)
        if firebase_app:
            return self.send_to_device_admin_sdk(device_token, title, body, data)
        
        # Fallback to legacy HTTP API
        if not self.server_key:
            return False, {'error': 'FCM server key not configured and Admin SDK not available'}
        
        url = 'https://fcm.googleapis.com/fcm/send'
        
        headers = {
            'Authorization': f'key={self.server_key}',
            'Content-Type': 'application/json',
        }
        
        payload = {
            'to': device_token,
            'priority': priority,
            'notification': {
                'title': title,
                'body': body,
                'sound': 'default',
                'badge': 1,
            },
            'data': data or {},
            'android': {
                'notification': {
                    'icon': 'ic_notification',
                    'color': '#072025',
                    'click_action': 'FLUTTER_NOTIFICATION_CLICK',
                }
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            # Check if response is JSON
            try:
                response_data = response.json()
            except ValueError:
                # Not valid JSON, probably an error page
                logger.error(f"FCM API returned non-JSON response: {response.text[:200]}")
                return False, {'error': 'FCM API error: Invalid response format'}
            
            if response.status_code == 200 and response_data.get('success', 0) > 0:
                logger.info(f"FCM notification sent successfully to {device_token}")
                return True, response_data
            else:
                error_msg = response_data.get('results', [{}])[0].get('error', 'Unknown error')
                logger.error(f"FCM notification failed: {error_msg}")
                return False, response_data
                
        except requests.RequestException as e:
            logger.error(f"FCM request failed: {str(e)}")
            return False, {'error': str(e)}
    
    def send_to_multiple_devices(self, device_tokens: List[str], title: str, 
                               body: str, data: Dict = None) -> Dict:
        """
        Send push notification to multiple Android devices
        
        Args:
            device_tokens: List of FCM device tokens
            title: Notification title
            body: Notification body
            data: Additional data payload
        
        Returns:
            Dict with success/failure counts and details
        """
        if not self.server_key:
            return {'success': 0, 'failure': len(device_tokens), 'results': []}
        
        url = 'https://fcm.googleapis.com/fcm/send'
        
        headers = {
            'Authorization': f'key={self.server_key}',
            'Content-Type': 'application/json',
        }
        
        payload = {
            'registration_ids': device_tokens,
            'priority': 'high',
            'notification': {
                'title': title,
                'body': body,
                'sound': 'default',
                'badge': 1,
            },
            'data': data or {},
            'android': {
                'notification': {
                    'icon': 'ic_notification',
                    'color': '#072025',
                    'click_action': 'FLUTTER_NOTIFICATION_CLICK',
                }
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            # Check if response is JSON
            try:
                response_data = response.json()
            except ValueError:
                # Not valid JSON, probably an error page
                logger.error(f"FCM API returned non-JSON response: {response.text[:200]}")
                return {
                    'success': 0,
                    'failure': len(device_tokens),
                    'results': [{'error': 'FCM API error: Invalid response format'}]
                }
            
            success_count = response_data.get('success', 0)
            failure_count = response_data.get('failure', 0)
            
            logger.info(f"FCM batch notification: {success_count} success, {failure_count} failure")
            return response_data
            
        except requests.RequestException as e:
            logger.error(f"FCM batch request failed: {str(e)}")
            return {'success': 0, 'failure': len(device_tokens), 'error': str(e)}


class APNsService:
    """Apple Push Notification service for iOS push notifications"""
    
    def __init__(self):
        self.key_id = getattr(settings, 'APNS_KEY_ID', None)
        self.team_id = getattr(settings, 'APNS_TEAM_ID', None)
        self.bundle_id = getattr(settings, 'APNS_BUNDLE_ID', None)
        self.key_file = getattr(settings, 'APNS_KEY_FILE', None)
        self.use_sandbox = getattr(settings, 'APNS_USE_SANDBOX', True)
        
        if not all([self.key_id, self.team_id, self.bundle_id]):
            logger.warning("APNs credentials not fully configured in settings")
    
    def send_to_device(self, device_token: str, title: str, body: str, 
                      data: Dict = None, badge: int = 1) -> Tuple[bool, Dict]:
        """
        Send push notification to a single iOS device
        
        Args:
            device_token: APNs device token
            title: Notification title
            body: Notification body
            data: Additional data payload
            badge: Badge number
        
        Returns:
            Tuple of (success: bool, response: dict)
        """
        try:
            # Try to import and use pyapns2 if available
            from apns2.client import APNsClient
            from apns2.payload import Payload
            from apns2.credentials import TokenCredentials
            
            if not self.key_file:
                return False, {'error': 'APNs key file not configured'}
            
            credentials = TokenCredentials(
                auth_key_path=self.key_file,
                auth_key_id=self.key_id,
                team_id=self.team_id
            )
            
            client = APNsClient(credentials, use_sandbox=self.use_sandbox)
            
            payload = Payload(
                alert={'title': title, 'body': body},
                badge=badge,
                sound='default',
                custom=data or {}
            )
            
            client.send_notification(device_token, payload, self.bundle_id)
            
            logger.info(f"APNs notification sent successfully to {device_token}")
            return True, {'status': 'success'}
            
        except ImportError:
            logger.error("pyapns2 library not installed. Install with: pip install pyapns2")
            return False, {'error': 'APNs library not available'}
        except Exception as e:
            logger.error(f"APNs notification failed: {str(e)}")
            return False, {'error': str(e)}
    
    def send_to_multiple_devices(self, device_tokens: List[str], title: str, 
                               body: str, data: Dict = None) -> Dict:
        """
        Send push notification to multiple iOS devices
        
        Args:
            device_tokens: List of APNs device tokens
            title: Notification title
            body: Notification body
            data: Additional data payload
        
        Returns:
            Dict with success/failure counts and details
        """
        success_count = 0
        failure_count = 0
        results = []
        
        for token in device_tokens:
            success, result = self.send_to_device(token, title, body, data)
            if success:
                success_count += 1
            else:
                failure_count += 1
            results.append(result)
        
        return {
            'success': success_count,
            'failure': failure_count,
            'results': results
        }


class PushNotificationService:
    """Main service for sending push notifications"""
    
    def __init__(self):
        self.fcm_service = FCMService()
        self.apns_service = APNsService()
    
    def send_to_user(self, user, title: str, body: str, data: Dict = None) -> Dict:
        """
        Send push notification to all active devices of a user
        
        Args:
            user: User instance
            title: Notification title
            body: Notification body
            data: Additional data payload
        
        Returns:
            Dict with results for each platform
        """
        results = {
            'android': {'success': 0, 'failure': 0, 'details': []},
            'ios': {'success': 0, 'failure': 0, 'details': []},
            'total_devices': 0
        }
        
        # Get all active devices for the user
        devices = Device.objects.filter(
            user=user,
            is_active=True,
            notifications_enabled=True
        )
        
        results['total_devices'] = devices.count()
        
        if not devices.exists():
            logger.info(f"No active devices found for user {user.email}")
            return results
        
        # Group devices by platform
        android_devices = devices.filter(platform='android')
        ios_devices = devices.filter(platform='ios')
        
        # Send to Android devices
        if android_devices.exists():
            android_tokens = list(android_devices.values_list('device_token', flat=True))
            
            # Use Admin SDK for single device, or multiple device method for batch
            if len(android_tokens) == 1:
                success, result = self.fcm_service.send_to_device_admin_sdk(
                    android_tokens[0], title, body, data
                )
                android_result = {
                    'success': 1 if success else 0,
                    'failure': 0 if success else 1,
                    'results': [result]
                }
            else:
                android_result = self.fcm_service.send_to_multiple_devices(
                    android_tokens, title, body, data
                )
            
            results['android']['success'] = android_result.get('success', 0)
            results['android']['failure'] = android_result.get('failure', 0)
            results['android']['details'] = android_result
        
        # Send to iOS devices
        if ios_devices.exists():
            ios_tokens = list(ios_devices.values_list('device_token', flat=True))
            ios_result = self.apns_service.send_to_multiple_devices(
                ios_tokens, title, body, data
            )
            results['ios']['success'] = ios_result.get('success', 0)
            results['ios']['failure'] = ios_result.get('failure', 0)
            results['ios']['details'] = ios_result
        
        logger.info(f"Push notification sent to user {user.email}: "
                   f"Android {results['android']['success']}/{len(android_devices) if android_devices else 0}, "
                   f"iOS {results['ios']['success']}/{len(ios_devices) if ios_devices else 0}")
        
        return results
    
    def send_notification_push(self, notification: Notification) -> bool:
        """
        Send push notification for a Notification instance
        
        Args:
            notification: Notification instance
        
        Returns:
            bool: Success status
        """
        if not notification.send_push or notification.push_sent:
            return True
        
        data = {
            'notification_id': str(notification.id),
            'type': notification.notification_type,
            'action_url': notification.action_url or '',
        }
        
        results = self.send_to_user(
            notification.user,
            notification.title,
            notification.message,
            data
        )
        
        # Log results for each device
        devices = Device.objects.filter(
            user=notification.user,
            is_active=True,
            notifications_enabled=True
        )
        
        for device in devices:
            status = 'success'
            error_message = None
            response_data = None
            
            if device.platform == 'android':
                android_details = results['android']['details']
                if results['android']['failure'] > 0:
                    status = 'failed'
                    error_message = str(android_details.get('error', 'Unknown error'))
                response_data = android_details
            elif device.platform == 'ios':
                ios_details = results['ios']['details']
                if results['ios']['failure'] > 0:
                    status = 'failed'
                    error_message = 'iOS push failed'
                response_data = ios_details
            
            # Create log entry
            PushNotificationLog.objects.create(
                notification=notification,
                device=device,
                status=status,
                response_data=response_data,
                error_message=error_message
            )
        
        # Update notification status
        total_success = results['android']['success'] + results['ios']['success']
        if total_success > 0:
            notification.push_sent = True
            notification.push_sent_at = timezone.now()
            notification.save(update_fields=['push_sent', 'push_sent_at'])
            return True
        
        return False
    
    def send_bulk_notification_push(self, bulk_notification) -> Dict:
        """
        Send push notifications for a BulkNotification instance
        
        Args:
            bulk_notification: BulkNotification instance
        
        Returns:
            Dict with overall results
        """
        from .models import BulkNotification
        
        # First create individual notifications
        success, message = bulk_notification.send_notifications()
        if not success:
            return {'success': False, 'message': message}
        
        # Then send push notifications for all created notifications
        notifications = Notification.objects.filter(
            user__in=bulk_notification.get_target_users(),
            title=bulk_notification.title,
            message=bulk_notification.message,
            created_at__gte=bulk_notification.sent_at
        )
        
        total_sent = 0
        total_failed = 0
        
        for notification in notifications:
            if self.send_notification_push(notification):
                total_sent += 1
            else:
                total_failed += 1
        
        return {
            'success': True,
            'total_notifications': notifications.count(),
            'push_sent': total_sent,
            'push_failed': total_failed,
            'message': f"Sent push notifications to {total_sent} users"
        }


# Global instance
push_service = PushNotificationService()


def send_push_notification(user, title: str, body: str, data: Dict = None) -> Dict:
    """
    Convenience function to send push notification to a user
    
    Args:
        user: User instance or user ID
        title: Notification title
        body: Notification body
        data: Additional data payload
    
    Returns:
        Dict with results
    """
    if isinstance(user, int):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(id=user)
        except User.DoesNotExist:
            return {'success': False, 'error': 'User not found'}
    
    return push_service.send_to_user(user, title, body, data)


def send_notification_with_push(user, title: str, message: str, 
                              notification_type: str, **kwargs) -> Notification:
    """
    Create a notification and send push notification
    
    Args:
        user: User instance
        title: Notification title
        message: Notification message
        notification_type: Type of notification
        **kwargs: Additional notification fields
    
    Returns:
        Created Notification instance
    """
    # Create notification
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        **kwargs
    )
    
    # Send push notification
    push_service.send_notification_push(notification)
    
    return notification