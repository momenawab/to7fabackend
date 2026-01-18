# Implementation Plan: Backend User State & Authorization Logic

**Branch**: `001-user-state-logic` | **Date**: 2026-01-15 | **Spec**: [spec.md](file:///Users/momen/untitled%20folder/To7fa/TO7FAA/to7fabackend/specs/001-user-state-logic/spec.md)  
**Input**: Feature specification from `/specs/001-user-state-logic/spec.md`

---

## Summary

Implement comprehensive user state management for the To7fa backend including:
- **5 user states**: Guest, Authenticated (Unverified), Authenticated (Verified), Locked (BANNED), Blocked
- **Mobile OTP verification** with 3-attempt limit and 60s cooldown
- **Guest cart** with session-based persistence and cart merge on login
- **Lock/Block enforcement** at API gateway level
- **Seller/Artist capability gating** based on application status

---

## Technical Context

**Language/Version**: Python 3.9+ (Django 4.2.13)  
**Primary Dependencies**: Django REST Framework 3.16.0, SimpleJWT 5.5.0, django-redis 5.4.0  
**Storage**: MySQL (MySQLClient 2.2.7), Redis (for OTP caching)  
**Testing**: pytest-django (to be added)  
**Target Platform**: Linux server (Django backend API)  
**Project Type**: Backend API (Django REST)  
**Performance Goals**: 200ms p50, 500ms p95 per constitution  
**Constraints**: Database queries <100ms, no N+1 patterns  
**Scale/Scope**: E-commerce platform with customer, artist, store user types

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status | Justification |
|-----------|------|--------|---------------|
| **I. Code Quality** | Files ≤300 lines | ✅ PASS | New services split by responsibility |
| **I. Code Quality** | Single Responsibility | ✅ PASS | Separate services for auth, verification, cart merge |
| **II. Testing Standards** | 80% coverage on critical paths | ⚠️ PENDING | Tests to be added in execution phase |
| **II. Testing Standards** | Unit + Integration + Contract tests | ⚠️ PENDING | Test plan defined below |
| **III. UX Consistency** | Error response format | ✅ PASS | Standard error codes defined in spec |
| **III. UX Consistency** | 401/403/404 correct usage | ✅ PASS | Spec defines each error code |
| **IV. Performance** | 200ms p50, 500ms p95 | ✅ PASS | Redis caching for OTP, indexed queries |
| **IV. Performance** | No N+1 queries | ✅ PASS | select_related for user/profile queries |

**Gate Result**: ✅ PASS (Testing to be implemented in execution)

---

## Project Structure

### Documentation (this feature)

```text
specs/001-user-state-logic/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── openapi.yaml     # API contract
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
custom_auth/
├── models.py            # [MODIFY] Add user state fields
├── services/            # [NEW] Business logic layer
│   ├── __init__.py
│   ├── user_state.py    # User state derivation
│   ├── verification.py  # OTP logic
│   └── lock_block.py    # Lock/Block enforcement
├── middleware.py        # [NEW] Lock enforcement middleware
├── serializers.py       # [MODIFY] Add new fields
├── jwt_views.py         # [MODIFY] Lock check on login
└── tests/               # [NEW] Test directory
    ├── __init__.py
    ├── test_user_state.py
    ├── test_verification.py
    ├── test_lock_block.py
    └── test_cart_merge.py

cart/
├── models.py            # [MODIFY] Add session_id for guest cart
├── services/            # [NEW] Business logic
│   ├── __init__.py
│   └── cart_merge.py    # Cart merge logic
├── views.py             # [MODIFY] Add merge endpoint
└── tests/               # [NEW] Test directory
    ├── __init__.py
    └── test_cart.py
```

**Structure Decision**: Existing Django app structure preserved. New `services/` subdirectories for business logic separation per Single Responsibility principle.

---

## Proposed Changes

### Component 1: User Model Extensions

#### [MODIFY] [models.py](file:///Users/momen/untitled%20folder/To7fa/TO7FAA/to7fabackend/custom_auth/models.py)

Add the following fields to `User` model:

| Field | Type | Purpose |
|-------|------|---------|
| `is_mobile_verified` | BooleanField | Distinct from email_verified, gates transactional actions |
| `mobile_verified_at` | DateTimeField | Timestamp of verification |
| `is_locked` | BooleanField | Global ban flag |
| `locked_at` | DateTimeField | When user was locked |
| `locked_reason` | TextField | Admin-provided reason |
| `is_blocked` | BooleanField | Business restriction flag |
| `blocked_capabilities` | JSONField | Array of blocked capability codes |
| `otp_failed_attempts` | PositiveIntegerField | Counter for 3-attempt limit |
| `otp_blocked_at` | DateTimeField | Permanent block timestamp |

#### [NEW] OTPVerification model

Track OTP requests and validation:
- `user`: ForeignKey
- `otp_code`: CharField (6 digits, hashed)
- `created_at`: DateTimeField
- `expires_at`: DateTimeField
- `used`: BooleanField
- `mobile_number`: CharField (the number being verified)

---

### Component 2: Guest Cart Support

#### [MODIFY] [models.py](file:///Users/momen/untitled%20folder/To7fa/TO7FAA/to7fabackend/cart/models.py)

Modify `Cart` model:

| Change | Details |
|--------|---------|
| `user` | Change to nullable (ForeignKey, null=True) |
| `session_id` | Add CharField (UUID, indexed) for guest identification |
| Add constraint | Either user OR session_id must be present |

#### [NEW] [cart_merge.py](file:///Users/momen/untitled%20folder/To7fa/TO7FAA/to7fabackend/cart/services/cart_merge.py)

Cart merge service with:
- `merge_guest_cart(user, session_id)` → merge guest items into user cart
- Conflict resolution: user cart quantity wins for duplicates
- Cleanup: delete guest cart after successful merge

---

### Component 3: Lock Enforcement Middleware

#### [NEW] [middleware.py](file:///Users/momen/untitled%20folder/To7fa/TO7FAA/to7fabackend/custom_auth/middleware.py)

Global middleware to check lock status on every authenticated request:
- Check `user.is_locked` on each request
- Return 403 with `USER_LOCKED` error code immediately
- Applied at API gateway level (before view processing)

---

### Component 4: Verification Service

#### [NEW] [verification.py](file:///Users/momen/untitled%20folder/To7fa/TO7FAA/to7fabackend/custom_auth/services/verification.py)

- `send_otp(user, mobile_number)` → Generate 6-digit OTP, store in Redis with 5min TTL
- `verify_otp(user, otp_code)` → Validate OTP, mark mobile as verified
- `check_otp_blocked(user)` → Check if user has exceeded 3 attempts
- Cooldown: 60 seconds between OTP requests (tracked in Redis)

---

### Component 5: API Endpoint Modifications

#### [MODIFY] [jwt_views.py](file:///Users/momen/untitled%20folder/To7fa/TO7FAA/to7fabackend/custom_auth/jwt_views.py)

Login view changes:
- Add lock check before issuing token
- Include `is_mobile_verified`, `is_locked`, `is_blocked`, `blocked_capabilities` in response
- Trigger cart merge if session_id provided in request

#### [NEW] Endpoints to add:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/auth/send-otp/` | POST | Send OTP to mobile |
| `/api/v1/auth/verify-otp/` | POST | Verify OTP code |
| `/api/v1/cart/merge/` | POST | Merge guest cart into user cart |

---

## Verification Plan

### Automated Tests

**Framework**: pytest-django (to be added to requirements.txt)

**Test Run Command**:
```bash
cd "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend"
python manage.py test custom_auth.tests cart.tests --verbosity=2
```

#### Unit Tests

| Test File | Coverage |
|-----------|----------|
| `custom_auth/tests/test_user_state.py` | User state derivation logic |
| `custom_auth/tests/test_verification.py` | OTP send/verify, 3-attempt block, 60s cooldown |
| `custom_auth/tests/test_lock_block.py` | Lock enforcement, block capability checks |
| `cart/tests/test_cart.py` | Guest cart creation, cart merge, conflict resolution |

#### Integration Tests

| Test | Description |
|------|-------------|
| `test_login_returns_user_state_fields` | Verify login response includes all state fields |
| `test_locked_user_cannot_login` | 403 with USER_LOCKED |
| `test_unverified_user_checkout_blocked` | 403 with MOBILE_VERIFICATION_REQUIRED |
| `test_cart_merge_on_login` | Guest cart items appear in user cart |

### Manual Verification

> **Note**: Request user input on preferred manual testing approach.

Suggested manual tests using API client (Postman/curl):

1. **Lock enforcement test**:
   - Create user, lock via admin panel
   - Attempt login → expect "You are banned" response
   
2. **OTP flow test**:
   - Login as unverified user
   - Attempt checkout endpoint → expect verification required
   - Call send-otp → verify-otp → retry checkout → success

3. **Cart merge test**:
   - Add items to cart as guest (using session_id)
   - Login with existing user cart
   - Verify guest items merged, duplicates resolved

---

## Dependencies & Risk

| Risk | Mitigation |
|------|------------|
| Redis dependency for OTP | Fallback to database if Redis unavailable |
| Migration complexity | Reversible AddField migrations only |
| Cart merge data loss | Comprehensive logging of merge operations |

---

## Complexity Tracking

> No constitution violations requiring justification.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |
