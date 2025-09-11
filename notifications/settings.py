# Push Notification Settings Configuration

# Add these settings to your Django settings.py file:

# Firebase Cloud Messaging (FCM) Settings for Android
FCM_SERVER_KEY = 'your-fcm-server-key-here'  # Legacy server key
FCM_PROJECT_ID = 'your-firebase-project-id'  # Firebase project ID

# For FCM HTTP v1 API (recommended):
# FCM_SERVICE_ACCOUNT_FILE = 'path/to/your-firebase-service-account.json'

# Apple Push Notification Service (APNs) Settings for iOS
APNS_KEY_ID = 'your-apns-key-id'  # APNs Auth Key ID
APNS_TEAM_ID = 'your-apple-team-id'  # Apple Developer Team ID
APNS_BUNDLE_ID = 'com.yourapp.bundleid'  # iOS app bundle ID
APNS_KEY_FILE = 'path/to/your-apns-auth-key.p8'  # Path to APNs auth key file
APNS_USE_SANDBOX = True  # Set to False for production

# Add to INSTALLED_APPS if not already added
# INSTALLED_APPS = [
#     # ... other apps
#     'notifications',
# ]

# Logging configuration for push notifications
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'push_notifications.log',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'notifications.push_utils': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Required packages (add to requirements.txt):
# requests>=2.25.1
# pyapns2>=0.7.2  # For iOS push notifications