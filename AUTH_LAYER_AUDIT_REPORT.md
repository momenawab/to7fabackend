# Auth Layer Audit Report - To7fa Backend

**Date:** 2025-12-31  
**Scope:** JWT authentication implementation review  
**Status:** 🔴 CRITICAL ISSUES FOUND

---

## Executive Summary

| Category | Status | Risk Level |
|----------|--------|------------|
| Security | ⚠️ CRITICAL | High |
| Backward Compatibility | ⚠️ WARNING | Medium |
| Rate Limiting | ❌ BROKEN | High |
| Migrations | ✅ SAFE | Low |
| Overall Decision | 🔴 NO-GO | High |

**Recommendation:** DO NOT deploy to production until critical issues are fixed.

---

## 1. Security Risks

### 🔴 CRITICAL: Legacy Login Endpoint Bypasses Security

**Issue:** The legacy `/api/login/` endpoint (TokenAuth) has no security controls.

**Impact:** Attackers can bypass:
- Email verification requirement
- Account locking mechanism
- Rate limiting
- Failed login tracking

**Evidence:**
```python
# custom_auth/views.py - Line 123-140
class LoginView(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        # No email verification check
        # No account locking check
        # No failed login tracking
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, ...})
```

**Comparison:**
| Feature | Legacy `/api/login/` | New `/api/auth/login/` |
|---------|---------------------|-------------------------|
| Email Verification | ❌ No | ✅ Yes |
| Account Locking | ❌ No | ✅ Yes |
| Rate Limiting | ❌ No | ✅ Yes (5/15min) |
| Failed Login Tracking | ❌ No | ✅ Yes |
| Token Expiration | ❌ No | ✅ Yes (1h access, 7d refresh) |

**Risk:** Users can login without verifying email, bypassing the entire email verification system.

---

### ⚠️ HIGH: Rate Limiting Not Working

**Issue:** DRF throttles require a cache backend, but none is configured.

**Evidence:**
```python
# to7fabackend/settings.py - No CACHES configuration
# jwt_views.py uses AnonRateThrottle and UserRateThrottle
class LoginRateThrottle(AnonRateThrottle):
    rate = '5/15min'
    scope = 'login'
```

**Impact:**
- Login attempts are NOT rate limited
- Password reset requests are NOT rate limited
- Email verification requests are NOT rate limited
- Brute force attacks are possible

**Behavior without cache:**
- DRF throttles fall back to in-memory cache (per-process)
- In production with multiple workers, each worker has its own cache
- Rate limits are not shared across workers
- Attackers can bypass by hitting different workers

---

### ⚠️ MEDIUM: Inconsistent Blocking Logic

**Issue:** Two blocking mechanisms exist but only one is used.

**Evidence:**
```python
# custom_auth/models.py - Lines 67-71
blocked_at = models.DateTimeField(blank=True, null=True)
blocked_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='blocked_users')
block_reason = models.TextField(blank=True, null=True)
unblocked_at = models.DateTimeField(blank=True, null=True)
unblocked_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='unblocked_users')

# jwt_views.py - Line 114-118 (only checks is_active)
if not user.is_active:
    return Response({'error': 'Account is blocked', ...})
```

**Impact:** The `blocked_at`, `blocked_by`, `block_reason`, `unblocked_at`, `unblocked_by` fields are unused.

---

## 2. Backward Compatibility Risks

### ⚠️ WARNING: Dual Authentication Systems Running

**Issue:** Both TokenAuth and JWTAuth are active simultaneously.

**Impact:**
- Confusion for Flutter developers (which endpoint to use?)
- Security bypass via legacy endpoint
- Two token management systems to maintain
- Potential for inconsistent behavior

**Current State:**
```python
# settings.py - Line 193-197
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        # TokenAuth removed from DEFAULT, but still available
    ),
}
```

**Risk:** If TokenAuth is removed from `DEFAULT_AUTHENTICATION_CLASSES`, the legacy `/api/login/` endpoint will still work (it uses `ObtainAuthToken` which doesn't check `DEFAULT_AUTHENTICATION_CLASSES`).

---

## 3. Rate Limiting Approach

### ❌ BROKEN: Mixed Rate Limiting Strategies

**Issue:** Two rate limiting approaches are used inconsistently.

| Approach | Usage | Status |
|----------|--------|--------|
| DRF Throttles (`AnonRateThrottle`) | jwt_views.py | ❌ Not working (no cache) |
| django-ratelimit | Not used | ✅ Installed in requirements.txt |

**Current Implementation:**
```python
# jwt_views.py - Uses DRF throttles
class LoginRateThrottle(AnonRateThrottle):
    rate = '5/15min'
    scope = 'login'

# requirements.txt - django-ratelimit is installed but not used
django-ratelimit==4.1.0
```

**Recommendation:** Use DRF throttles (already implemented) but configure a cache backend.

---

## 4. Migration Safety

### ✅ SAFE: Migrations Are Safe for Existing Users

**Analysis:**
- All new fields have default values
- No existing fields are modified or removed
- No data loss or corruption risk
- Existing users will have default values:
  - `email_verified = False` (new users must verify email)
  - `failed_login_attempts = 0`
  - `locked_until = None`

**Migration File:** [`custom_auth/migrations/0002_jwt_email_verification.py`](to7fabackend/custom_auth/migrations/0002_jwt_email_verification.py)

**Impact on Existing Users:**
- Users registered before migration will have `email_verified = False`
- **CRITICAL:** These users will be unable to login via `/api/auth/login/` until they verify their email
- Users can still login via legacy `/api/login/` (security bypass)

---

## 5. Deprecation Plan for Old Auth Endpoints

### Phase 1: Immediate Actions (Before Production)

| Action | Priority | Risk |
|--------|----------|------|
| Configure cache backend | 🔴 CRITICAL | High |
| Disable legacy `/api/login/` endpoint | 🔴 CRITICAL | High |
| Handle existing users without email verification | 🔴 CRITICAL | High |

### Phase 2: Migration Period (2-4 weeks)

| Action | Timeline | Details |
|--------|----------|---------|
| Monitor legacy endpoint usage | Week 1-2 | Track calls to `/api/login/` |
| Email users about migration | Week 2 | Notify users to update Flutter app |
| Deprecation headers | Week 2-4 | Add `Warning: Deprecated` header to legacy endpoints |
| Force update Flutter app | Week 4 | Require minimum app version |

### Phase 3: Removal (After Migration Period)

| Action | Timeline | Details |
|--------|----------|---------|
| Remove `rest_framework.authtoken` from INSTALLED_APPS | After migration | Clean up unused app |
| Remove legacy endpoints from urls.py | After migration | Clean up unused views |
| Remove Token model | After migration | Clean up database tables |

---

## Minimal Fix List (Required for Go/No-Go Decision)

### 🔴 CRITICAL FIX #1: Configure Cache Backend

**File:** [`to7fabackend/to7fabackend/settings.py`](to7fabackend/to7fabackend/settings.py)

**Add:**
```python
# Cache configuration for rate limiting
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'to7fa_throttle',
        'TIMEOUT': 300,
    }
}
```

**Dependencies:**
```bash
pip install django-redis
```

---

### 🔴 CRITICAL FIX #2: Disable Legacy Login Endpoint

**File:** [`to7fabackend/custom_auth/urls.py`](to7fabackend/custom_auth/urls.py)

**Option A: Comment out legacy endpoint (temporary)**
```python
# Legacy endpoints (DISABLED - security risk)
# path('login/', views.LoginView.as_view(), name='login'),
```

**Option B: Add deprecation warning (recommended for migration)**
```python
# Legacy endpoints (deprecated - use /api/auth/login/ instead)
path('login/', views.DeprecatedLoginView.as_view(), name='login'),
```

**Create DeprecatedLoginView in views.py:**
```python
class DeprecatedLoginView(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        response['X-Deprecated'] = 'true'
        response['X-Use-Instead'] = '/api/auth/login/'
        return response
```

---

### 🔴 CRITICAL FIX #3: Handle Existing Users Without Email Verification

**Option A: Auto-verify existing users (recommended)**
```python
# custom_auth/migrations/0003_auto_verify_existing_users.py
from django.db import migrations

def auto_verify_existing_users(apps, schema_editor):
    User = apps.get_model('custom_auth', 'User')
    User.objects.filter(email_verified=False).update(email_verified=True)

class Migration(migrations.Migration):
    dependencies = [
        ('custom_auth', '0002_jwt_email_verification'),
    ]
    operations = [
        migrations.RunPython(auto_verify_existing_users),
    ]
```

**Option B: Allow login without verification for existing users (temporary)**
```python
# jwt_views.py - Modify login_view
# Check if email is verified (skip for users created before migration)
if not user.email_verified and user.date_joined < migration_date:
    return Response({'error': 'Email not verified', ...})
```

---

### ⚠️ MEDIUM FIX #4: Remove Unused Blocking Fields

**File:** [`to7fabackend/custom_auth/models.py`](to7fabackend/custom_auth/models.py)

**Action:** Either use these fields or remove them in a future migration.

---

### ⚠️ LOW FIX #5: Remove django-ratelimit from requirements.txt

**File:** [`to7fabackend/requirements.txt`](to7fabackend/requirements.txt)

**Action:** Remove `django-ratelimit==4.1.0` (not used, DRF throttles are preferred)

---

## Go/No-Go Decision

### 🔴 NO-GO - Auth Layer is NOT Production-Ready

**Reasons:**
1. **Rate limiting is broken** - No cache backend configured
2. **Security bypass exists** - Legacy login endpoint has no security controls
3. **Existing users locked out** - Users registered before migration cannot login via new endpoint
4. **Dual authentication systems** - Confusing and risky

**Required Actions Before Go:**
1. ✅ Configure cache backend (Redis)
2. ✅ Disable or deprecate legacy `/api/login/` endpoint
3. ✅ Handle existing users without email verification
4. ✅ Test rate limiting with multiple workers
5. ✅ Test migration with production-like data

---

## Decision: Legacy TokenAuth Should Be Restricted

### Recommendation: RESTRICT (not deprecated yet)

**Rationale:**
1. **Security Risk:** Legacy endpoint bypasses all security controls
2. **No Grace Period:** Cannot allow bypass of email verification
3. **Flutter Impact:** Minimal - new endpoints are available

### Implementation Plan:

**Step 1: Immediately (Today)**
- Add cache backend configuration
- Disable legacy `/api/login/` endpoint (return 410 Gone)
- Create migration to auto-verify existing users

**Step 2: Monitor (1 week)**
- Monitor for any 410 errors on `/api/login/`
- Check for any Flutter clients still using legacy endpoint

**Step 3: Remove (After 1 week)**
- Remove legacy endpoint from urls.py
- Remove `rest_framework.authtoken` from INSTALLED_APPS
- Clean up unused code

---

## Summary

| Issue | Severity | Fix Required | Effort |
|-------|----------|---------------|---------|
| Rate limiting broken | 🔴 Critical | Configure cache | 30 min |
| Legacy login bypass | 🔴 Critical | Disable endpoint | 15 min |
| Existing users locked out | 🔴 Critical | Auto-verify migration | 15 min |
| Unused blocking fields | ⚠️ Medium | Remove or use | 1 hour |
| Unused django-ratelimit | ⚠️ Low | Remove from requirements | 5 min |

**Total Effort:** ~2 hours

**Verdict:** Fix critical issues before deploying to production.

---

**Next Steps:**
1. Configure Redis cache backend
2. Disable legacy `/api/login/` endpoint
3. Create auto-verify migration
4. Test rate limiting
5. Re-audit for Go/No-Go decision
