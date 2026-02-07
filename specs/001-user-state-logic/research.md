# Research: User State & Authorization Logic

**Feature**: 001-user-state-logic  
**Date**: 2026-01-15

---

## 1. OTP Implementation Strategy

**Decision**: Use Redis for OTP storage with database fallback

**Rationale**:
- Redis TTL feature handles expiration automatically
- Sub-millisecond read/write for validation
- Existing django-redis infrastructure in project
- 60-second cooldown trivially enforced with Redis key expiry

**Alternatives Considered**:
- Database-only: Rejected due to cleanup overhead and slower queries
- In-memory: Rejected due to multi-worker inconsistency

**Implementation Notes**:
- Key format: `otp:{user_id}:{mobile_hash}`
- TTL: 300 seconds (5 minutes)
- Cooldown key: `otp_cooldown:{user_id}` with 60s TTL
- OTP hashed with PBKDF2 before storage (security)

---

## 2. Guest Cart Session Strategy

**Decision**: Use UUID session_id in request header/cookie

**Rationale**:
- Stateless backend - no server-side session required
- UUID collision probability negligible
- Works across browser refresh within session
- Simple merge on login

**Alternatives Considered**:
- Django sessions: Rejected - adds server-side session dependency
- Device fingerprinting: Rejected - privacy concerns, unreliable

**Implementation Notes**:
- Client generates UUID on first cart action
- Stored in secure local storage (Flutter side)
- Passed as `X-Session-ID` header or `session_id` body param
- Cart model stores session_id for guest carts

---

## 3. Lock Enforcement Architecture

**Decision**: Middleware-based global enforcement

**Rationale**:
- Single point of enforcement (DRY principle)
- Cannot be bypassed by individual views
- Minimal per-request overhead (single DB lookup, cacheable)
- Consistent error response format

**Alternatives Considered**:
- Decorator per view: Rejected - easy to forget, duplication
- JWT claim expiry: Rejected - async ban wouldn't work mid-session

**Implementation Notes**:
- Middleware checks `request.user.is_locked` for authenticated requests
- Returns 403 with `{"error": "USER_LOCKED", "message": "You are banned"}`
- Can cache lock status in Redis for 60s to reduce DB hits

---

## 4. Mobile vs Email Verification Distinction

**Decision**: Separate boolean fields for mobile and email verification

**Rationale**:
- Different purposes: mobile gates transactions, email gates nothing critical
- Independent verification flows
- Clear business logic separation

**Alternatives Considered**:
- Combined `is_verified` field: Rejected - conflates two concerns
- Verification bitmap: Rejected - over-engineered, harder to query

**Implementation Notes**:
- `is_mobile_verified` (new) vs existing `email_verified`
- Mobile verification timestamp tracked separately
- Login allows both verified and unverified mobile

---

## 5. Block Capability Storage

**Decision**: JSONField array of blocked capability codes

**Rationale**:
- Flexible - new capabilities can be added without migration
- Simple contains-check in Python
- Matches Flutter integration spec (`blocked_capabilities: List<String>`)

**Alternatives Considered**:
- Separate boolean per capability: Rejected - migration required for new capability
- Separate BlockRecord table: Rejected - over-normalized for current scope

**Implementation Notes**:
- `blocked_capabilities = ["SELL", "WITHDRAW"]` format
- Canonical capability codes: `SELL`, `WITHDRAW`, `CREATE_PRODUCT`, `MANAGE_ORDERS`
- Empty array = no blocks

---

## 6. OTP 3-Attempt Permanent Block

**Decision**: Permanent block requiring admin reset

**Rationale**:
- User explicitly chose stricter security (Option A in clarification)
- Prevents brute-force attacks effectively
- Admin intervention provides manual fraud review opportunity

**Alternatives Considered**:
- Time-based temporary block: User rejected this option
- Unlimited attempts with expiry: User rejected this option

**Implementation Notes**:
- `otp_failed_attempts` counter on User model
- `otp_blocked_at` timestamp when threshold reached
- Admin action clears both fields
- Check `otp_blocked_at IS NOT NULL` before allowing OTP request

---

## 7. Cart Merge Conflict Resolution

**Decision**: User cart quantity wins, guest quantity discarded

**Rationale**:
- User explicitly chose this strategy (Option A in clarification)
- Preserves user's "deliberate" cart over guest browsing additions
- Simpler than sum or UI-based resolution

**Alternatives Considered**:
- Sum quantities: User rejected
- Show conflict UI: User rejected

**Implementation Notes**:
- On merge, for each guest item:
  - If product exists in user cart: skip (keep user qty)
  - If product not in user cart: add guest item
- Log discarded quantities for analytics

---

## 8. Testing Framework

**Decision**: pytest-django for all tests

**Rationale**:
- Industry standard for Django testing
- Fixtures support for test data
- Parallel test execution support
- Better assertion messages than unittest

**Alternatives Considered**:
- Built-in Django TestCase: Less feature-rich
- pytest + factory_boy: Factory_boy adds complexity not needed now

**Implementation Notes**:
- Add `pytest-django==4.5.2` to requirements.txt
- Create `pytest.ini` in project root
- Test files follow `test_*.py` pattern in `tests/` subdirectories
