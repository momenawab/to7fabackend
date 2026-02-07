# Quickstart: User State & Authorization Logic

**Feature**: 001-user-state-logic  
**Branch**: `001-user-state-logic`

---

## Prerequisites

- Python 3.9+
- MySQL running locally
- Redis running locally (for OTP caching)
- Virtual environment activated

---

## Setup

```bash
# Navigate to project
cd "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend"

# Activate virtual environment
source .venv/bin/activate

# Install dependencies (pytest-django to be added)
pip install -r requirements.txt
pip install pytest-django==4.5.2

# Apply migrations after implementing model changes
python manage.py makemigrations custom_auth cart
python manage.py migrate
```

---

## Key Files to Modify

| File | Purpose |
|------|---------|
| `custom_auth/models.py` | Add user state fields |
| `custom_auth/services/verification.py` | OTP send/verify logic |
| `custom_auth/services/user_state.py` | State derivation |
| `custom_auth/middleware.py` | Lock enforcement |
| `custom_auth/jwt_views.py` | Login modifications |
| `cart/models.py` | Guest cart support |
| `cart/services/cart_merge.py` | Merge logic |

---

## Running Tests

```bash
# Run all feature tests
python manage.py test custom_auth.tests cart.tests --verbosity=2

# Run specific test file
python manage.py test custom_auth.tests.test_verification

# With pytest (after setup)
pytest custom_auth/tests/ cart/tests/ -v
```

---

## Manual Testing

### 1. Lock Enforcement

```bash
# Login as admin
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@to7fa.com", "password": "adminpass"}'

# Lock a user via Django admin or shell
python manage.py shell
>>> from custom_auth.models import User
>>> user = User.objects.get(email="test@example.com")
>>> user.is_locked = True
>>> user.locked_reason = "Test ban"
>>> user.save()

# Attempt login as locked user - should fail with 403
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "userpass"}'
# Expected: {"error": "USER_LOCKED", "message": "You are banned"}
```

### 2. OTP Verification Flow

```bash
# Login as unverified user
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "unverified@example.com", "password": "pass123"}' | jq -r '.access_token')

# Send OTP
curl -X POST http://localhost:8000/api/v1/auth/send-otp/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"mobile_number": "+201234567890"}'

# Check Redis for OTP (dev only)
redis-cli GET "otp:${user_id}:*"

# Verify OTP
curl -X POST http://localhost:8000/api/v1/auth/verify-otp/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"otp_code": "123456"}'
```

### 3. Cart Merge

```bash
# Add items as guest
curl -X POST http://localhost:8000/api/v1/cart/add/ \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -d '{"product_id": 1, "quantity": 2}'

# Login with session_id
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "pass", "session_id": "550e8400-e29b-41d4-a716-446655440000"}'

# Verify cart merged
curl http://localhost:8000/api/v1/cart/ \
  -H "Authorization: Bearer $TOKEN"
```

---

## API Contracts

See [contracts/openapi.yaml](file:///Users/momen/untitled%20folder/To7fa/TO7FAA/to7fabackend/specs/001-user-state-logic/contracts/openapi.yaml) for full API specification.

---

## Error Codes Reference

| Code | HTTP | Meaning |
|------|------|---------|
| `USER_LOCKED` | 403 | User is banned |
| `MOBILE_VERIFICATION_REQUIRED` | 403 | OTP required for this action |
| `OTP_BLOCKED` | 403 | 3 failed attempts, contact support |
| `OTP_EXPIRED` | 400 | OTP has expired, request new one |
| `OTP_INVALID` | 400 | Wrong OTP code |
| `OTP_COOLDOWN` | 400 | Wait 60s before new request |
| `CAPABILITY_BLOCKED` | 403 | Seller/artist capability blocked |
