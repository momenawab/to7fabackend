# Data Model: User State & Authorization Logic

**Feature**: 001-user-state-logic  
**Date**: 2026-01-15

---

## Entity: User (Modifications)

Extended fields for the existing `custom_auth.User` model.

### New Fields

| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `is_mobile_verified` | Boolean | No | False | Mobile OTP verification status |
| `mobile_verified_at` | DateTime | Yes | NULL | When mobile was verified |
| `is_locked` | Boolean | No | False | Global ban status |
| `locked_at` | DateTime | Yes | NULL | When user was locked |
| `locked_reason` | Text | Yes | NULL | Admin-provided reason |
| `locked_by_id` | FK(User) | Yes | NULL | Admin who locked |
| `is_blocked` | Boolean | No | False | Business restriction active |
| `blocked_capabilities` | JSON | No | `[]` | Array of blocked capability codes |
| `blocked_reason` | Text | Yes | NULL | Reason for block |
| `otp_failed_attempts` | PositiveInt | No | 0 | Consecutive OTP failures |
| `otp_blocked_at` | DateTime | Yes | NULL | Permanent OTP block timestamp |

### Validation Rules

- `is_locked` = True implies ALL access denied
- `is_blocked` = True implies capability-level restriction only
- `blocked_capabilities` validated against enum: `SELL`, `WITHDRAW`, `CREATE_PRODUCT`, `MANAGE_ORDERS`
- `otp_failed_attempts` resets to 0 on successful verification

### State Derivation Logic

```python
def get_user_state(user):
    if user is None or not user.is_authenticated:
        return "GUEST"
    if user.is_locked:
        return "LOCKED"
    if user.is_blocked:
        return "BLOCKED"
    if user.is_mobile_verified:
        return "AUTHENTICATED_VERIFIED"
    return "AUTHENTICATED_UNVERIFIED"
```

---

## Entity: OTPVerification (New)

Track OTP requests for mobile verification.

### Fields

| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | AutoField | No | - | Primary key |
| `user_id` | FK(User) | No | - | User requesting verification |
| `mobile_number` | CharField(20) | No | - | Number being verified |
| `otp_hash` | CharField(128) | No | - | PBKDF2 hash of OTP |
| `created_at` | DateTime | No | auto_now_add | Request timestamp |
| `expires_at` | DateTime | No | - | created_at + 5 minutes |
| `used` | Boolean | No | False | Has been successfully verified |
| `attempt_count` | PositiveInt | No | 0 | Failed attempts for this OTP |

### Validation Rules

- OTP code is 6 numeric digits
- `expires_at` must be > `created_at`
- Only one active (unused, unexpired) OTP per user at a time

### State Transitions

```
Created → [verify success] → Used
        → [verify fail 3x] → User.otp_blocked_at set
        → [expired] → Expired (soft state via expires_at)
```

---

## Entity: Cart (Modifications)

Extend existing `cart.Cart` model for guest support.

### Field Changes

| Field | Change | New Definition |
|-------|--------|----------------|
| `user` | Modify | ForeignKey(User, null=True, on_delete=CASCADE) |
| `session_id` | Add | CharField(36, null=True, db_index=True) |

### Validation Rules

- Constraint: `user IS NOT NULL OR session_id IS NOT NULL`
- `session_id` format: UUID v4 (36 chars with hyphens)
- Unique constraint on `session_id` when not null

### Relationships

- User → Cart: OneToOne for authenticated users
- Session → Cart: OneToOne for guest carts (via session_id)

---

## Entity: BlockRecord (Optional - Future)

> **Note**: For MVP, `blocked_capabilities` on User is sufficient. This model is for audit trail if needed later.

### Fields (Deferred)

| Field | Type | Description |
|-------|------|-------------|
| `user_id` | FK(User) | Blocked user |
| `capability` | CharField | Blocked capability code |
| `blocked_at` | DateTime | When block applied |
| `blocked_by_id` | FK(User) | Admin who blocked |
| `block_reason` | Text | Reason for block |
| `unblocked_at` | DateTime | When block removed (null if active) |

---

## Capability Codes Enum

```python
class CapabilityCode:
    SELL = "SELL"
    WITHDRAW = "WITHDRAW"
    CREATE_PRODUCT = "CREATE_PRODUCT"
    MANAGE_ORDERS = "MANAGE_ORDERS"
    CREATE_CONSULTATION = "CREATE_CONSULTATION"
```

---

## Database Migration Plan

### Migration 1: User state fields
- Add all new User fields with defaults
- Safe, additive migration

### Migration 2: OTPVerification model
- Create new table
- No existing data to migrate

### Migration 3: Cart session support
- Make `user` nullable
- Add `session_id` column
- Add check constraint

### Rollback Strategy

All migrations are additive:
- Fields can be dropped without data loss
- New table can be dropped
- No column renames or type changes
