"""
Production settings for TO7FA Backend.

Phase 4 (Part 1, production configuration hardening): this file used to override
ALLOWED_HOSTS, CORS_ALLOWED_ORIGINS, and CSRF_TRUSTED_ORIGINS with hardcoded
placeholder lists ('Add your EC2 public IP here', 'Add your domain here') - which
silently defeated settings.py's env-driven, fail-fast configuration for those exact
values (CORS_ALLOWED_ORIGINS in particular: settings.py raises ImproperlyConfigured
if the env var is missing, but the old override here replaced that fail-fast value
with a hardcoded `[]` regardless of what the environment actually specified - the
same class of bug already fixed for SECRET_KEY/DB_PASSWORD in Phase 1). None of those
three are redefined here any more; set them via ALLOWED_HOSTS/CORS_ALLOWED_ORIGINS/
CSRF_TRUSTED_ORIGINS in this environment's .env instead (see PRODUCTION_READINESS.md
for the full variable reference) - no production domain is invented here since none
has been provided. The commented-out HTTPS block (SECURE_SSL_REDIRECT etc.) is
likewise removed: settings.py already sets those correctly whenever DEBUG=False,
which this file sets below, so the commented lines were dead weight, not a real gap.
"""

from .settings import *
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY is already set (and fail-fast validated) by `from .settings import *` above.
# Do NOT reassign it here with a fallback default - that would silently defeat the
# ImproperlyConfigured check in settings.py if the env var is ever missing in production.

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Phase 4 (Part 1) fix: SECURE_SSL_REDIRECT / SESSION_COOKIE_SECURE /
# CSRF_COOKIE_SECURE are computed in settings.py as `not DEBUG`, evaluated once at
# import time using whatever DEBUG the environment's .env actually had *before* the
# `DEBUG = False` line above ever runs (this project's own development .env sets
# DEBUG=True, and both settings modules load the same .env via load_dotenv() - so
# without this fix, deploying with settings_production.py while a shared .env still
# says DEBUG=True would silently inherit insecure, HTTP-only cookie/redirect settings
# despite DEBUG being correctly False for every other purpose). `manage.py check
# --deploy` against this file is what surfaced it (W008/W012/W016). Re-derived here,
# after DEBUG is forced False above, so production is secure regardless of what the
# shared .env's DEBUG value happens to be.
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# ALLOWED_HOSTS / CORS_ALLOWED_ORIGINS / CSRF_TRUSTED_ORIGINS: intentionally NOT
# redefined here - inherited from settings.py, which reads them from the environment
# (ALLOWED_HOSTS has a safe localhost-only default; CORS_ALLOWED_ORIGINS fails fast if
# unset; CSRF_TRUSTED_ORIGINS defaults to empty). Set the real values in this
# environment's .env - see PRODUCTION_READINESS.md.

# Database configuration for production
# DATABASES is already set (and fail-fast validated) by `from .settings import *` above.
# Do NOT redefine it here with fallback defaults (previously included a hardcoded
# 'strongpass' password fallback) - that would silently defeat the ImproperlyConfigured
# check in settings.py if DB_PASSWORD (or any other DB env var) is ever missing.

# Static files configuration for production
STATIC_URL = '/static/'
STATIC_ROOT = os.getenv('STATIC_ROOT', '/var/www/to7fa/static/')

# Media files configuration for production
MEDIA_URL = '/media/'
MEDIA_ROOT = os.getenv('MEDIA_ROOT', '/var/www/to7fa/media/')

# HTTPS / HSTS / CORS-allow-all / security headers: all inherited from settings.py,
# which already derives them correctly from DEBUG (set to False above) and
# SECURE_HSTS_ENABLED (a separate, explicit opt-in - see settings.py's Part 1 note on
# why HSTS is not tied directly to DEBUG). Nothing production-specific to add here.

# Logging configuration - writes to /var/log/to7fa/ instead of settings.py's
# BASE_DIR/logs/ (a real production-vs-development difference: on EC2 this is a
# resource path, not credentials, and pairs with logrotate/journald in the standard
# deployment described in PRODUCTION_READINESS.md).
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
            'filename': os.getenv('DJANGO_LOG_FILE', '/var/log/to7fa/django.log'),
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
        'django.request': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
        # Phase 4 (Part 13, observability): dedicated loggers for the areas most worth
        # operational visibility in production - payments (Payment 2.0, Phase 3) and
        # WebSocket auth (support consumers, Phase 2/3). Neither logger name is
        # special to Django; they exist so these modules' own `logging.getLogger(
        # __name__)` calls (payment.services, payment.views, support.consumers) get
        # routed distinctly rather than only appearing under the generic root logger.
        'payment': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'support': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Email configuration: intentionally NOT redefined here - inherited from settings.py,
# which already reads EMAIL_HOST/EMAIL_PORT/EMAIL_HOST_USER/EMAIL_HOST_PASSWORD/
# DEFAULT_FROM_EMAIL from the environment with no hardcoded credentials. This file
# used to duplicate that logic with a literal 'noreply@yourdomain.com' placeholder
# default for DEFAULT_FROM_EMAIL - removed as exactly the kind of placeholder
# production config Part 6 asks to clear out. Set EMAIL_HOST/EMAIL_HOST_USER/
# EMAIL_HOST_PASSWORD/DEFAULT_FROM_EMAIL in this environment's .env - see
# PRODUCTION_READINESS.md for the full list and which provider (if any) has been
# decided on (none has, as of this phase).
