"""
Production settings for TO7FA Backend on EC2
"""

from .settings import *
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-q2(^inryyn2zv9pky+rr+us=!bn2tph!^m&5bx2hiie)zreg4y')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Add your EC2 instance IP and domain here
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    # Add your EC2 public IP here
    # 'your-ec2-public-ip',
    # Add your domain if you have one
    # 'yourdomain.com',
    # 'www.yourdomain.com',
]

# Database configuration for production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME', 'to7fa_db'),
        'USER': os.getenv('DB_USER', 'django_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'strongpass'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
    }
}

# Static files configuration for production
STATIC_URL = '/static/'
STATIC_ROOT = '/var/www/to7fa/static/'

# Media files configuration for production
MEDIA_URL = '/media/'
MEDIA_ROOT = '/var/www/to7fa/media/'

# Security settings for production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HTTPS settings (uncomment when you have SSL certificate)
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True

# CORS settings for production
CORS_ALLOW_ALL_ORIGINS = False  # Changed from True for security
CORS_ALLOWED_ORIGINS = [
    # Add your frontend URLs here
    # "http://localhost:3000",  # React development
    # "https://yourdomain.com",
]

# CSRF trusted origins
CSRF_TRUSTED_ORIGINS = [
    # Add your domain here when you have SSL
    # 'https://yourdomain.com',
    # For development/testing without SSL
    'http://localhost',
    'http://127.0.0.1',
]

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/to7fa/django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file', 'console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Email configuration (configure based on your email service)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@yourdomain.com')