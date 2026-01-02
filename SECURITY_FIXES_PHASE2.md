# Security Fixes - Phase 2: Production-Safe Configuration

**Date:** 2025-12-31  
**Scope:** Django settings.py - Production-safe configuration only  
**Rules Followed:** No business logic changes, no app refactoring, no API behavior changes

---

## Summary of Changes

This phase addresses critical configuration flaws that could allow insecure defaults in production. All changes enforce **fail-fast** behavior - the application will not start with missing or insecure configuration.

---

## Exact Code Changes

### 1. Import ImproperlyConfigured Exception

**File:** [`to7fabackend/to7fabackend/settings.py:16`](to7fabackend/to7fabackend/settings.py:16)

**Change:**
```python
# Added import
from django.core.exceptions import ImproperlyConfigured
```

**Why Required:** Needed to raise proper Django exceptions for configuration errors.

---

### 2. SECRET_KEY - No Fallback, Fail-Fast

**File:** [`to7fabackend/to7fabackend/settings.py:29-35`](to7fabackend/to7fabackend/settings.py:29-35)

**Before:**
```python
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-q2(^inryyn2zv9pky+rr+us=!bn2tph!^m&5bx2hiie)zreg4y')
```

**After:**
```python
SECRET_KEY = os.getenv('SECRET_KEY')
if SECRET_KEY is None:
    raise ImproperlyConfigured(
        "SECRET_KEY environment variable is required. "
        "Set it in your .env file or environment."
    )
```

**Why Required:**
- **Before:** If SECRET_KEY was missing, a known insecure key was used. This is a **critical security vulnerability** - anyone who knows the default key can forge sessions, CSRF tokens, and password reset links.
- **After:** Application fails immediately with clear error if SECRET_KEY is not set. No insecure fallback.
- **Fail-fast:** Prevents accidental deployment with default/missing secret key.

---

### 3. DEBUG - Safe Default (False)

**File:** [`to7fabackend/to7fabackend/settings.py:38-39`](to7fabackend/to7fabackend/settings.py:38-39)

**Before:**
```python
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
```

**After:**
```python
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
```

**Why Required:**
- **Before:** If DEBUG environment variable was missing, default was `True`. This means production could accidentally run with debug mode enabled, exposing stack traces and sensitive information.
- **After:** Default is `False`. Production is safe by default. Development requires explicitly setting `DEBUG=True`.
- **Fail-safe:** Accidental production deployment is secure by default.

---

### 4. Database Configuration - No Insecure Defaults

**File:** [`to7fabackend/to7fabackend/settings.py:108-123`](to7fabackend/to7fabackend/settings.py:108-123)

**Before:**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME', 'to7fa_db'),
        'USER': os.getenv('DB_USER', 'django_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'strongpass'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '3306'),
        ...
    }
}
```

**After:**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
        ...
    }
}

# Validate database configuration
if not all([
    DATABASES['default']['NAME'],
    DATABASES['default']['USER'],
    DATABASES['default']['PASSWORD'],
    DATABASES['default']['HOST'],
    DATABASES['default']['PORT']
]):
    raise ImproperlyConfigured(
        "Database configuration is incomplete. "
        "Set DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, and DB_PORT in your .env file."
    )
```

**Why Required:**
- **Before:** Insecure default password `strongpass` was used if DB_PASSWORD was missing.
- **After:** Application fails if any database credential is missing. No insecure defaults.
- **Fail-fast:** Prevents accidental deployment with default/missing database credentials.

---

### 5. CORS_ALLOWED_ORIGINS - No Fallback, Fail-Fast

**File:** [`to7fabackend/to7fabackend/settings.py:192-200`](to7fabackend/to7fabackend/settings.py:192-200)

**Before:**
```python
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:8000,http://127.0.0.1:8000').split(',')
```

**After:**
```python
cors_origins = os.getenv('CORS_ALLOWED_ORIGINS')
if cors_origins is None:
    raise ImproperlyConfigured(
        "CORS_ALLOWED_ORIGINS environment variable is required. "
        "Set it in your .env file (comma-separated list of allowed origins)."
    )
CORS_ALLOWED_ORIGINS = cors_origins.split(',')
```

**Why Required:**
- **Before:** Default allowed localhost origins. If deployed to production without setting this, any localhost request could access the API (though unlikely to be exploited, it's still a misconfiguration).
- **After:** Application fails if CORS_ALLOWED_ORIGINS is not set. No insecure defaults.
- **Fail-fast:** Forces explicit configuration of allowed origins.

---

### 6. CSRF_COOKIE_SECURE - Automatic Based on DEBUG

**File:** [`to7fabackend/to7fabackend/settings.py:247`](to7fabackend/to7fabackend/settings.py:247)

**Before:**
```python
CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', 'False').lower() == 'true'
```

**After:**
```python
CSRF_COOKIE_SECURE = not DEBUG
```

**Why Required:**
- **Before:** Default was `False`. Production could run with insecure CSRF cookies even if HTTPS was configured.
- **After:** Automatically `True` when `DEBUG=False` (production), automatically `False` when `DEBUG=True` (development).
- **Fail-safe:** Production deployment automatically gets secure cookies without manual configuration.

---

### 7. CSRF_TRUSTED_ORIGINS - Safe Default (Empty)

**File:** [`to7fabackend/to7fabackend/settings.py:251`](to7fabackend/to7fabackend/settings.py:251)

**Before:**
```python
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost:8000,http://127.0.0.1:8000').split(',')
```

**After:**
```python
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',')
```

**Why Required:**
- **Before:** Default trusted localhost origins. This could allow CSRF bypass from localhost in production.
- **After:** Default is empty list. No origins are trusted by default.
- **Fail-safe:** Explicit configuration required to trust any origins.

---

### 8. Security Headers - Conditional Based on DEBUG

**File:** [`to7fabackend/to7fabackend/settings.py:258-275`](to7fabackend/to7fabackend/settings.py:258-275)

**Before:**
```python
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False').lower() == 'true'
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_X_FRAME_OPTIONS = 'DENY'
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
```

**After:**
```python
# Security Headers - Enable in production (when DEBUG=False)
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG

# HSTS headers - Only enabled in production (when DEBUG=False)
# HSTS should NOT be enabled in development as it breaks HTTP access
if not DEBUG:
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
else:
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False

# These security headers are safe in both development and production
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_X_FRAME_OPTIONS = 'DENY'
```

**Why Required:**
- **Before:** HSTS headers were always enabled, even in development. This breaks HTTP access during development.
- **Before:** SSL redirect and secure cookies defaulted to `False`, requiring manual configuration.
- **After:** SSL redirect and secure cookies automatically enabled in production (`DEBUG=False`).
- **After:** HSTS headers only enabled in production to avoid breaking development.
- **Fail-safe:** Production deployment automatically gets full security headers.

---

### 9. Firebase/APNs Configuration - Removed Fallback

**File:** [`to7fabackend/to7fabackend/settings.py:281-287`](to7fabackend/to7fabackend/settings.py:281-287)

**Before:**
```python
FCM_PROJECT_ID = os.getenv('FCM_PROJECT_ID', 'to7fa-5c012')
```

**After:**
```python
FCM_PROJECT_ID = os.getenv('FCM_PROJECT_ID')
```

**Why Required:**
- **Before:** Default Firebase project ID was hardcoded. This is not a security risk per se, but is a misconfiguration risk.
- **After:** No fallback. Application will use `None` if not set, which is acceptable for optional settings.

---

## Configuration is Production-Safe

### Security Guarantees

1. **SECRET_KEY** - Application will NOT start if missing. No insecure fallback.
2. **DEBUG** - Defaults to `False`. Production is secure by default.
3. **Database Credentials** - Application will NOT start if any credential is missing. No insecure password fallback.
4. **CORS** - Application will NOT start if allowed origins are not configured.
5. **SSL/HTTPS** - Automatically enabled when `DEBUG=False`.
6. **Secure Cookies** - Automatically enabled when `DEBUG=False`.
7. **HSTS** - Automatically enabled when `DEBUG=False` (disabled in development to avoid breaking HTTP).

### Fail-Fast Behavior

The application will **fail immediately** with clear error messages if:
- `SECRET_KEY` is not set
- Database credentials are incomplete
- `CORS_ALLOWED_ORIGINS` is not set

This prevents accidental deployment with insecure or incomplete configuration.

---

## Deployment Instructions

### 1. Create .env File
```bash
cd to7fabackend
cp .env.example .env
```

### 2. Configure Required Settings

Edit `.env` file and set ALL required values:

```bash
# ============================================================================
# REQUIRED SETTINGS - Application will fail if not set
# ============================================================================

# Generate a strong random key:
# python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY=your-generated-secret-key-here

# Set to 'true' ONLY for development
DEBUG=False

# Set your production domains
ALLOWED_HOSTS=to7fa.com,www.to7fa.com

# Set your production frontend URLs (REQUIRED)
CORS_ALLOWED_ORIGINS=https://to7fa.com,https://www.to7fa.com

# Set your database credentials (ALL REQUIRED)
DB_NAME=to7fa_db
DB_USER=django_user
DB_PASSWORD=your-strong-database-password
DB_HOST=localhost
DB_PORT=3306
```

### 3. Optional Settings

```bash
# ============================================================================
# OPTIONAL SETTINGS - Have safe defaults or are conditional
# ============================================================================

# CSRF Trusted Origins - Optional, defaults to empty
# Only set if you need to bypass CSRF for specific origins
# CSRF_TRUSTED_ORIGINS=https://to7fa.com,https://www.to7fa.com

# Push Notification Settings - Optional
FCM_PROJECT_ID=to7fa-5c012

# APNs Configuration - Optional
APNS_KEY_ID=your-apns-key-id
APNS_TEAM_ID=your-apple-team-id
APNS_BUNDLE_ID=com.to7fa.app
APNS_KEY_FILE=/path/to/your/apns-key.p8
APNS_USE_SANDBOX=False
```

### 4. Verify Configuration
```bash
python manage.py check --deploy
```

This command will fail if any required configuration is missing.

### 5. Run Migrations
```bash
python manage.py migrate
```

### 6. Collect Static Files
```bash
python manage.py collectstatic
```

### 7. Start Server
```bash
python manage.py runserver
```

---

## Verification Checklist

Before deploying to production, verify:

- [ ] `.env` file exists and is **NOT** committed to version control
- [ ] `SECRET_KEY` is set to a strong, random value (use `get_random_secret_key()`)
- [ ] `DEBUG=False` in `.env`
- [ ] `ALLOWED_HOSTS` contains only production domains
- [ ] `CORS_ALLOWED_ORIGINS` contains only production frontend URLs
- [ ] All database credentials are set (DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)
- [ ] Database password is strong and not the default `strongpass`
- [ ] HTTPS is configured on the server
- [ ] SSL/TLS certificate is valid
- [ ] Application starts without errors: `python manage.py check --deploy`

---

## Files Modified

1. [`to7fabackend/to7fabackend/settings.py`](to7fabackend/to7fabackend/settings.py) - Production-safe configuration
2. [`to7fabackend/.env.example`](to7fabackend/.env.example) - Updated with clear required/optional sections

---

## Security Risks Fixed

| Risk | Severity | Before | After |
|-------|-----------|--------|-------|
| SECRET_KEY insecure fallback | Critical | ❌ Insecure default | ✅ No fallback, fail-fast |
| DEBUG defaults to True | Critical | ❌ Insecure default | ✅ Safe default (False) |
| Database password insecure fallback | High | ❌ Default 'strongpass' | ✅ No fallback, fail-fast |
| CORS insecure default | High | ❌ Default localhost | ✅ No fallback, fail-fast |
| CSRF_COOKIE_SECURE insecure default | High | ❌ Default False | ✅ Auto-secure in production |
| CSRF_TRUSTED_ORIGINS insecure default | Medium | ❌ Default localhost | ✅ Safe default (empty) |
| HSTS enabled in development | Medium | ❌ Breaks HTTP access | ✅ Conditional on DEBUG |
| SSL redirect insecure default | High | ❌ Default False | ✅ Auto-secure in production |

---

## Remaining Security Risks (Not Addressed - Require Business Logic Changes)

### Critical
- No rate limiting (requires middleware implementation)
- Weak token authentication (requires migration to JWT)
- No password strength validation (requires custom validators)
- No email verification (requires business logic changes)
- No password reset flow (requires business logic changes)

### High
- No two-factor authentication (requires business logic changes)
- No input validation (requires serializer changes)
- @csrf_exempt usage (requires view changes)
- No HTTPS enforcement in code (requires deployment configuration)

### Medium
- No audit trail review (requires admin panel changes)
- No admin permission enforcement (requires business logic changes)

---

## Confirmation

✅ **Task Complete and Safe to Proceed**

The configuration is now **production-safe**:
- All critical settings have safe defaults or fail-fast behavior
- No insecure fallback values remain
- Security headers automatically enabled in production
- Application will fail immediately with clear errors if required configuration is missing
- No business logic was modified
- No app refactoring was performed
- No API behavior was changed

**Ready to proceed to Prompt 1 (authentication changes).**

---

**Report End**
