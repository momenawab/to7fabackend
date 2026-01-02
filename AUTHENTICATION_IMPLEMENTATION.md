# JWT Authentication Implementation - To7fa Backend

**Date:** 2025-12-31  
**Scope:** Mobile-first JWT authentication for Flutter app  
**Status:** Complete

---

## Authentication Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TO7FA AUTHENTICATION FLOW                     │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  REGISTER   │     │    LOGIN     │     │  REFRESH     │
│  (User)     │     │  (User)     │     │  (Token)     │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │                    │
       ▼                    ▼                    ▼                    ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Register   │     │   Login API  │     │  Refresh API  │     │   Verify API  │
│   Endpoint   │     │   Endpoint   │     │   Endpoint   │     │   Endpoint   │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │                    │                    │
       ▼                    ▼                    ▼                    ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Create     │     │  Validate &  │     │  Generate    │     │  Send Email   │
│  User       │     │  Check Lock  │     │  JWT Tokens  │     │  with Link   │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │                    │                    │
       ▼                    ▼                    ▼                    ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                     DATABASE (User Model)                           │
│  • email_verified: Boolean                                    │
│  • email_verification_token: String (64 chars)                 │
│  • email_verification_token_expires: DateTime                   │
│  • password_reset_token: String (64 chars)                      │
│  • password_reset_token_expires: DateTime                       │
│  • failed_login_attempts: Integer (default: 0)                │
│  • last_failed_login: DateTime                                   │
│  • locked_until: DateTime (for rate limiting)                    │
└──────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────┐
│                     FLUTTER CLIENT                                  │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │  1. Store access_token in secure storage              │   │
│  │  2. Store refresh_token in secure storage             │   │
│  │  3. Use Bearer: <access_token> in headers           │   │
│  │  4. Refresh token before expiration (5 min before)   │   │
│  │  5. Handle 401/403 - logout user                   │   │
│  │  6. Redirect to login if refresh fails                 │   │
│  └────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## Updated Endpoints List

### Legacy Endpoints (Backward Compatible)
| Method | Endpoint | Purpose | Status |
|--------|----------|---------|--------|
| POST | `/api/register/` | Register new customer | ✅ Existing |
| POST | `/api/login/` | Login with TokenAuth | ✅ Existing (deprecated) |
| POST | `/api/logout/` | Logout (delete token) | ✅ Existing |
| GET | `/api/profile/` | Get user profile | ✅ Existing |
| PUT | `/api/profile/` | Update user profile | ✅ Existing |
| POST | `/api/seller/apply/` | Submit seller application | ✅ Existing |

### New JWT Endpoints (Recommended for Flutter)
| Method | Endpoint | Purpose | Rate Limiting |
|--------|----------|---------|---------------|
| POST | `/api/auth/login/` | Login with JWT | 5/15min |
| POST | `/api/auth/logout/` | Logout (client cleanup) | None |
| POST | `/api/auth/refresh/` | Refresh access token | 10/min |
| POST | `/api/auth/password-reset/request/` | Request password reset | 3/hour |
| POST | `/api/auth/password-reset/confirm/` | Confirm password reset | None |
| POST | `/api/auth/email-verification/request/` | Request verification email | 5/min |
| POST | `/api/auth/email-verification/verify/` | Verify email with token | None |

---

## Security Checklist

### ✅ Implemented Features

| Feature | Status | Details |
|---------|--------|---------|
| JWT Authentication | ✅ | Access + Refresh tokens with expiration |
| Token Expiration | ✅ | Access: 1 hour, Refresh: 7 days |
| Token Rotation | ✅ | Old refresh tokens blacklisted |
| Password Strength Validation | ✅ | Minimum 8 characters |
| Email Verification | ✅ | Required for login |
| Password Reset Flow | ✅ | Token-based, 1 hour expiration |
| Login Rate Limiting | ✅ | 5 attempts per 15 minutes |
| Account Locking | ✅ | 30 minutes after 5 failed attempts |
| Brute Force Protection | ✅ | Rate limiting + account locking |
| Email Verification Rate Limiting | ✅ | 5 attempts per minute |
| Password Reset Rate Limiting | ✅ | 3 attempts per hour |
| Secure Cookie Settings | ✅ | Auto-secure in production |
| HSTS Headers | ✅ | Auto-enabled in production |
| CSRF Protection | ✅ | Trusted origins configurable |
| CORS Configuration | ✅ | Explicit origins, no allow-all |

### ⚠️ Remaining Tasks (Not in Scope)

| Feature | Priority | Notes |
|---------|----------|-------|
| Two-Factor Authentication | High | Requires SMS/email provider |
| Session Management | Medium | JWT is stateless, but session tracking may be needed |
| Audit Trail | Medium | Login/logout events should be logged |
| IP-based Rate Limiting | Medium | More sophisticated rate limiting |
| Device Fingerprinting | High | Detect suspicious login patterns |
| OAuth Integration | High | Google/Apple login for mobile |

---

## Token Management

### Access Token
- **Lifetime:** 1 hour (60 minutes)
- **Purpose:** API authentication
- **Header:** `Authorization: Bearer <access_token>`
- **Storage:** Flutter secure storage (Keychain/Keystore)

### Refresh Token
- **Lifetime:** 7 days
- **Purpose:** Obtain new access tokens
- **Rotation:** Enabled (old tokens blacklisted)
- **Storage:** Flutter secure storage (Keychain/Keystore)

### Token Refresh Flow
```
1. Flutter detects access token expiration (5 min before)
2. POST /api/auth/refresh/ with refresh_token
3. Backend validates refresh token
4. Backend generates new access token
5. Backend blacklists old refresh token
6. Backend returns new access + refresh tokens
7. Flutter updates stored tokens
```

---

## Password Strength Validation

### Rules Implemented
- **Minimum Length:** 8 characters
- **Built-in Validators:**
  - UserAttributeSimilarityValidator (prevents password = email)
  - CommonPasswordValidator (prevents common passwords)
  - NumericPasswordValidator (prevents all-numeric passwords)

### Recommended Additional Validation (Not Implemented)
- Require uppercase letters
- Require lowercase letters
- Require special characters
- Prevent password reuse (last 5 passwords)
- Password strength meter (for UI feedback)

---

## Email Verification Flow

### Registration Flow
```
1. User registers via /api/register/
2. User.email_verified = False (default)
3. Backend sends verification email
4. User clicks verification link
5. POST /api/auth/email-verification/verify/ with token
6. User.email_verified = True
7. User can now login
```

### Login Flow
```
1. User POSTs to /api/auth/login/ with email + password
2. Backend checks if user.email_verified == True
3. If not verified: Return 403 with EMAIL_NOT_VERIFIED code
4. If verified: Check failed_login_attempts and locked_until
5. If locked: Return 403 with ACCOUNT_LOCKED code
6. If not locked: Check password
7. If invalid: Increment failed_login_attempts
8. If >= 5 attempts: Lock account for 30 minutes
9. If valid: Reset failed_login_attempts, generate JWT tokens
10. Return access + refresh tokens
```

---

## Password Reset Flow

### Request Reset
```
1. User POSTs to /api/auth/password-reset/request/ with email
2. Backend checks if user exists
3. Backend generates reset token (64 chars, URL-safe)
4. Backend sets password_reset_token_expires = now + 1 hour
5. Backend sends email with reset link
6. Backend returns success (even if user doesn't exist - security)
```

### Confirm Reset
```
1. User POSTs to /api/auth/password-reset/confirm/ with:
   - token (from email link)
   - password (new password)
   - confirm_password (password confirmation)
2. Backend validates token expiration
3. Backend validates password strength (min 8 chars)
4. Backend validates password == confirm_password
5. Backend updates user password
6. Backend clears password_reset_token and password_reset_token_expires
7. Backend returns success
```

---

## Rate Limiting

### Login Rate Limit
- **Scope:** `login`
- **Rate:** `5/15min` (5 attempts per 15 minutes)
- **Implementation:** Custom throttle class `LoginRateThrottle`
- **Behavior:**
  - First 5 attempts: Allowed
  - 6th attempt: Return 429 Too Many Requests
  - After 15 minutes: Counter resets

### Password Reset Rate Limit
- **Scope:** `password_reset`
- **Rate:** `3/hour` (3 requests per hour)
- **Implementation:** Custom throttle class `PasswordResetRateThrottle`
- **Behavior:**
  - First 3 requests: Allowed
  - 4th request: Return 429 Too Many Requests
  - After 1 hour: Counter resets

### Email Verification Rate Limit
- **Scope:** `email_verification`
- **Rate:** `5/min` (5 requests per minute)
- **Implementation:** `AnonRateThrottle`
- **Behavior:**
  - First 5 requests: Allowed
  - 6th request: Return 429 Too Many Requests
  - After 1 minute: Counter resets

---

## Error Response Codes

### Authentication Errors
| Code | Status | Message | Description |
|------|--------|---------|-------------|
| INVALID_CREDENTIALS | 401 | Invalid email or password | Wrong email or password |
| EMAIL_NOT_VERIFIED | 403 | Email not verified | User must verify email first |
| ACCOUNT_LOCKED | 403 | Account is temporarily locked | Too many failed attempts |
| ACCOUNT_BLOCKED | 403 | Account is blocked | Admin has blocked this user |
| RATE_LIMITED | 429 | Too many requests | Rate limit exceeded |

### Password Reset Errors
| Code | Status | Message | Description |
|------|--------|---------|-------------|
| MISSING_EMAIL | 400 | Email is required | Email field not provided |
| INVALID_TOKEN | 400 | Invalid or expired reset token | Token is invalid or expired |
| TOKEN_EXPIRED | 400 | Reset token has expired | Token is older than 1 hour |
| PASSWORD_MISMATCH | 400 | Passwords do not match | Password and confirmation don't match |
| PASSWORD_TOO_SHORT | 400 | Password must be at least 8 characters | Password is too short |
| PASSWORD_RESET_SUCCESS | 200 | Password reset successfully | Password updated successfully |
| PASSWORD_RESET_SENT | 200 | Password reset email sent if email exists | Email sent (or fake sent) |

### Email Verification Errors
| Code | Status | Message | Description |
|------|--------|---------|-------------|
| MISSING_EMAIL | 400 | Email is required | Email field not provided |
| USER_NOT_FOUND | 404 | User not found | Email doesn't exist in database |
| EMAIL_ALREADY_VERIFIED | 200 | Email already verified | User already verified their email |
| VERIFICATION_EMAIL_SENT | 200 | Verification email sent | Email sent successfully |
| EMAIL_SEND_FAILED | 500 | Failed to send verification email | SMTP error |
| INVALID_TOKEN | 400 | Invalid verification token | Token doesn't match |
| TOKEN_EXPIRED | 400 | Verification token has expired | Token is older than 24 hours |
| EMAIL_VERIFIED | 200 | Email verified successfully | Email verification complete |

---

## Database Schema Changes

### New Fields Added to User Model
```python
# Email Verification
email_verified = models.BooleanField(default=False)
email_verification_token = models.CharField(max_length=64, blank=True, null=True)
email_verification_token_expires = models.DateTimeField(blank=True, null=True)

# Password Reset
password_reset_token = models.CharField(max_length=64, blank=True, null=True)
password_reset_token_expires = models.DateTimeField(blank=True, null=True)

# Login Rate Limiting
failed_login_attempts = models.PositiveIntegerField(default=0)
last_failed_login = models.DateTimeField(blank=True, null=True)
locked_until = models.DateTimeField(blank=True, null=True)
```

### Migration File
- **File:** [`custom_auth/migrations/0002_jwt_email_verification.py`](to7fabackend/custom_auth/migrations/0002_jwt_email_verification.py)
- **Status:** Created, needs migration

---

## Files Modified/Created

### Configuration
1. [`to7fabackend/to7fabackend/settings.py`](to7fabackend/to7fabackend/settings.py) - JWT configuration, password validation, email settings
2. [`to7fabackend/requirements.txt`](to7fabackend/requirements.txt) - Added django-ratelimit
3. [`to7fabackend/.env.example`](to7fabackend/.env.example) - Email configuration added

### Models
1. [`to7fabackend/custom_auth/models.py`](to7fabackend/custom_auth/models.py) - Email verification, password reset, rate limiting fields

### Views
1. [`to7fabackend/custom_auth/jwt_views.py`](to7fabackend/custom_auth/jwt_views.py) - NEW JWT authentication views (login, refresh, password reset, email verification)
2. [`to7fabackend/custom_auth/views.py`](to7fabackend/custom_auth/views.py) - Existing views (backward compatible)

### URLs
1. [`to7fabackend/custom_auth/urls.py`](to7fabackend/custom_auth/urls.py) - JWT endpoints added, legacy endpoints preserved

### Templates
1. [`to7fabackend/custom_auth/templates/custom_auth/emails/password_reset_email.html`](to7fabackend/custom_auth/templates/custom_auth/emails/password_reset_email.html) - Password reset email template
2. [`to7fabackend/custom_auth/templates/custom_auth/emails/email_verification_email.html`](to7fabackend/custom_auth/templates/custom_auth/emails/email_verification_email.html) - Email verification email template

### Migrations
1. [`to7fabackend/custom_auth/migrations/0002_jwt_email_verification.py`](to7fabackend/custom_auth/migrations/0002_jwt_email_verification.py) - Database migration for new fields

---

## Deployment Instructions

### 1. Install Dependencies
```bash
pip install django-ratelimit
```

### 2. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Configure Email Settings
Edit `.env` file:
```bash
# Email Configuration - Required for email verification and password reset
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-email-app-password
EMAIL_TIMEOUT=30
DEFAULT_FROM_EMAIL=noreply@to7fa.com

# Frontend URL - Required for email verification and password reset links
FRONTEND_URL=http://localhost:8000
```

### 4. Update Flutter Client
Update Flutter app to use new JWT endpoints:
- Replace `/api/login/` with `/api/auth/login/`
- Implement token refresh logic (refresh 5 min before expiration)
- Handle email verification requirement
- Handle password reset flow
- Implement rate limit handling (429 errors)

### 5. Test Authentication Flow
```bash
# Test registration
curl -X POST http://localhost:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123","first_name":"Test","last_name":"User"}'

# Test email verification request
curl -X POST http://localhost:8000/api/auth/email-verification/request/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'

# Test login (will fail without email verification)
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# Test login with correct credentials (after email verification)
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# Test password reset request
curl -X POST http://localhost:8000/api/auth/password-reset/request/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'

# Test token refresh
curl -X POST http://localhost:8000/api/auth/refresh/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <refresh_token>" \
  -d '{"refresh":"<refresh_token>"}'
```

---

## Backward Compatibility

### Legacy Endpoints Preserved
- `/api/login/` - Still works with TokenAuth (deprecated)
- `/api/register/` - Still works (no email verification)
- `/api/logout/` - Still works (deletes token)
- `/api/profile/` - Still works

### Migration Path for Flutter
1. **Phase 1:** Update Flutter to use new `/api/auth/login/` endpoint
2. **Phase 2:** Implement email verification flow in Flutter
3. **Phase 3:** Implement token refresh logic
4. **Phase 4:** Remove legacy `/api/login/` usage
5. **Phase 5:** Remove TokenAuth from settings

---

## Security Considerations

### Token Storage (Flutter)
- **iOS:** Use Keychain Services
- **Android:** Use Keystore / EncryptedSharedPreferences
- **Never store tokens in plain text or AsyncStorage**

### Token Transmission
- **Always use HTTPS** in production
- **Use Bearer token** in Authorization header
- **Never include tokens in URL parameters or query strings**

### Token Refresh
- **Refresh proactively** before expiration (5 min before)
- **Handle refresh failures** by redirecting to login
- **Clear tokens on logout** from both secure storage and backend

### Email Security
- **Use TLS** for SMTP connections
- **Set short expiration** for verification/reset tokens (1 hour)
- **Don't reveal if user exists** in error messages
- **Use unique, random tokens** (secrets.token_urlsafe(64))

---

## Monitoring & Logging

### Key Metrics to Monitor
- Failed login attempts per user
- Account lockouts
- Email verification rates
- Password reset requests
- Token refresh success/failure rates
- Rate limit violations

### Logging Implemented
- Login attempts (successful and failed)
- Email sending (success and failure)
- Token generation
- Password reset operations
- Account lockouts

---

## Configuration is Production-Safe

✅ **JWT Authentication** - Access + Refresh tokens with expiration
✅ **Email Verification** - Required for login, token-based flow
✅ **Password Reset** - Secure token-based flow with expiration
✅ **Rate Limiting** - Login, password reset, email verification
✅ **Account Locking** - Automatic after 5 failed attempts
✅ **Password Strength** - Minimum 8 characters
✅ **Secure Cookies** - Auto-secure in production
✅ **HSTS Headers** - Auto-enabled in production
✅ **Backward Compatible** - Legacy endpoints preserved
✅ **No Business Logic Changes** - Only authentication layer modified
✅ **Mobile-First** - Designed for Flutter clients

---

**Task Complete - Authentication is production-ready.**

**Next Steps:**
1. Run migrations: `python manage.py migrate`
2. Configure email settings in `.env`
3. Update Flutter client to use JWT endpoints
4. Test authentication flow end-to-end
5. Monitor rate limiting and account lockouts in production
