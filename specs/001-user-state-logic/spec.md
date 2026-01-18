# Feature Specification: Backend User State & Authorization Logic

**Feature Branch**: `001-user-state-logic`  
**Created**: 2026-01-15  
**Status**: Draft  
**Input**: Backend User State, Authentication, Verification, Cart/Checkout, and Seller/Artist Capability Logic Specification

---

## Clarifications

### Session 2026-01-15

- Q: When an OTP expires before the user enters it, what should the system behavior be? → A: OTP expires with explicit error message, user must wait 60 seconds before requesting new OTP
- Q: If a verified user updates their mobile number, should their verification status reset? → A: Reset verification status immediately, require re-verification on next restricted action
- Q: If an admin locks a user while they are in the middle of checkout/payment, what should happen? → A: Immediately abort transaction, show ban screen, payment is forfeited (no refund)
- Q: How many incorrect OTP attempts are allowed before a security response? → A: 3 attempts, then permanent block requiring admin intervention
- Q: What happens if the same product exists in both guest cart and user cart during merge? → A: Keep user cart quantity, discard guest cart quantity for that item

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Guest Browsing Experience (Priority: P1)

A guest user visits the application without authentication. They can browse product catalogs, view product details, and add items to a session-based cart. The cart persists within their browser session.

**Why this priority**: Core e-commerce discovery experience. Without browsing capability, no user engagement occurs.

**Independent Test**: Can be tested by opening the app without login, navigating products, and adding items to cart. Delivers immediate product discovery value.

**Acceptance Scenarios**:

1. **Given** a guest user opens the app, **When** they browse products, **Then** all product listings and details are accessible
2. **Given** a guest user views products, **When** they add items to cart, **Then** items are stored in a session-based cart
3. **Given** a guest user has items in cart, **When** they close and reopen the browser within the same session, **Then** cart items persist

---

### User Story 2 - User Authentication (Priority: P1)

A user can register with email, password, and mobile number. After registration, they can log in using email and password. Login is permitted for both mobile-verified and unverified users. Only Locked (BANNED) users are blocked from login.

**Why this priority**: Authentication is foundational for all personalized user experiences and transactional actions.

**Independent Test**: Can be tested by registering a new account, then logging in. Delivers access to authenticated features.

**Acceptance Scenarios**:

1. **Given** valid email, password, and mobile, **When** user submits registration, **Then** account is created
2. **Given** valid credentials, **When** user submits login form, **Then** user is authenticated and session is created
3. **Given** user has unverified mobile, **When** user logs in with valid credentials, **Then** login succeeds (not blocked by mobile verification)
4. **Given** user is Locked (BANNED), **When** user attempts login, **Then** login is blocked and "You are banned" message is displayed
5. **Given** guest has items in cart, **When** guest logs in, **Then** guest cart merges into user cart automatically

---

### User Story 3 - Mobile OTP Verification (Priority: P2)

A user with unverified mobile attempts a restricted action (checkout, payment, order creation). The system prompts for OTP verification. Upon successful verification, the user gains full transactional capabilities.

**Why this priority**: Verification gate for transactional security. Must work before any purchase flow.

**Independent Test**: Can be tested by attempting checkout without mobile verification, completing OTP flow, then successfully completing checkout.

**Acceptance Scenarios**:

1. **Given** authenticated user with unverified mobile, **When** user attempts checkout, **Then** OTP verification is triggered
2. **Given** OTP is sent, **When** user enters correct OTP, **Then** mobile is marked as verified
3. **Given** mobile verification succeeds, **When** verification flow returns, **Then** user resumes checkout seamlessly
4. **Given** mobile is already verified, **When** user attempts checkout, **Then** checkout proceeds without OTP prompt

---

### User Story 4 - Checkout and Order Creation (Priority: P2)

An authenticated user with verified mobile proceeds through checkout. They can select payment method, confirm order details, and create an order. Payment is processed and order confirmation is displayed.

**Why this priority**: Core revenue-generating flow. Must work reliably for business viability.

**Independent Test**: Can be tested by adding items to cart, completing checkout as verified user, and confirming order creation.

**Acceptance Scenarios**:

1. **Given** verified user with items in cart, **When** user initiates checkout, **Then** checkout process begins
2. **Given** user in checkout, **When** user confirms payment, **Then** payment is processed
3. **Given** payment succeeds, **When** order confirmation displays, **Then** order is persisted in system
4. **Given** unverified user attempts checkout, **When** checkout begins, **Then** mobile verification is enforced first

---

### User Story 5 - Lock (BAN) Enforcement (Priority: P3)

An administrator locks a user for policy violation. The locked user is immediately denied all app access. Upon next app start, the user sees "You are banned" screen. Reinstalling the app does not bypass the lock.

**Why this priority**: Critical security control for policy enforcement and abuse prevention.

**Independent Test**: Can be tested by locking a user via admin, then attempting app access from that account.

**Acceptance Scenarios**:

1. **Given** user is Locked, **When** user attempts any API call, **Then** request is rejected with locked status
2. **Given** user is Locked, **When** user opens app, **Then** "You are banned" screen is displayed
3. **Given** user is Locked, **When** user reinstalls app, **Then** lock persists (account-level, not device-level)

---

### User Story 6 - Block (Business Restriction) Enforcement (Priority: P3)

An administrator blocks a seller/artist from selling capabilities. The blocked user can still log in, browse, and use customer features. Only selling-specific features are restricted.

**Why this priority**: Operational control for managing seller/artist disputes without full account termination.

**Independent Test**: Can be tested by blocking a seller, confirming customer features work, and confirming seller features are restricted.

**Acceptance Scenarios**:

1. **Given** seller is Blocked, **When** seller logs in, **Then** login succeeds
2. **Given** seller is Blocked, **When** seller browses products, **Then** browsing works normally
3. **Given** seller is Blocked, **When** seller attempts to list new product, **Then** action is denied with block reason
4. **Given** seller is Blocked, **When** seller attempts to withdraw funds, **Then** action is denied

---

### User Story 7 - Seller/Artist Application (Priority: P3)

A customer applies to become a seller/artist. Application is submitted for admin review. While pending or rejected, user remains Blocked from seller features but can use all customer features. Upon approval, seller capabilities are unlocked.

**Why this priority**: Growth funnel for seller ecosystem. Must not interfere with customer experience.

**Independent Test**: Can be tested by applying as seller, checking customer features work while pending, then approving and confirming seller features unlock.

**Acceptance Scenarios**:

1. **Given** customer, **When** user submits seller application, **Then** application enters pending state
2. **Given** pending application, **When** user uses customer features, **Then** all customer features work
3. **Given** pending application, **When** user attempts seller features, **Then** seller features are blocked
4. **Given** application approved, **When** user accesses seller features, **Then** seller features are available
5. **Given** application rejected, **When** user uses customer features, **Then** customer features continue working

---

### Edge Cases

- What happens when a user attempts checkout with an empty cart?
- ~~How does the system handle expired OTP codes?~~ → **Resolved**: Expired OTP shows error, 60-second cooldown before retry
- ~~What happens if mobile number is changed after verification?~~ → **Resolved**: Verification status resets immediately, re-verification required on next restricted action
- ~~How does system behave when user is Locked mid-transaction?~~ → **Resolved**: Immediately abort, show ban screen, payment forfeited
- What happens if seller application is approved while user is in customer checkout?

---

## Requirements *(mandatory)*

### 1. User State Definitions

- **FR-001**: System MUST define five distinct user states: Guest, Authenticated (Unverified Mobile), Authenticated (Mobile Verified), Locked (BANNED), Blocked (Business Restriction)

- **FR-002**: Guest state MUST allow: browsing, viewing products, adding to session-based cart

- **FR-003**: Authenticated (Unverified Mobile) state MUST allow: browsing, cart management, profile viewing

- **FR-004**: Authenticated (Unverified Mobile) state MUST NOT allow: checkout, payment, order creation

- **FR-005**: Authenticated (Mobile Verified) state MUST allow: all customer capabilities including checkout, payment, order creation, wallet usage

- **FR-006**: Locked (BANNED) state MUST deny all system access globally

- **FR-007**: Blocked (Business Restriction) state MUST allow login and browsing but MUST restrict specific capabilities (selling, withdrawals)

---

### 2. Authentication Specification

- **FR-008**: User registration MUST require: email, password, mobile number

- **FR-009**: Email is used for login and communication, NOT as verification gate for login

- **FR-010**: Login MUST accept email + password credentials

- **FR-011**: Login MUST succeed for both mobile-verified and mobile-unverified users

- **FR-012**: Login MUST block ONLY if user state is Locked (BANNED)

- **FR-013**: Verification status MUST NOT be enforced at login time

---

### 3. Verification Specification

- **FR-014**: Mobile OTP verification MUST be required for: checkout, payment, order creation

- **FR-015**: Verification MUST be triggered at the moment user attempts a restricted action

- **FR-016**: Successful verification MUST mark mobile as verified permanently

- **FR-017**: Successful verification MUST unlock all transactional capabilities

- **FR-018**: After verification success, system MUST resume the interrupted action (checkout continuation)

- **FR-019**: Email verification is optional and MUST NOT block login or checkout

- **FR-040**: Expired OTP MUST display explicit error message; user MUST wait 60 seconds before requesting new OTP

- **FR-041**: When user changes mobile number, verification status MUST reset immediately; re-verification MUST be required on next restricted action

- **FR-043**: After 3 incorrect OTP attempts, user MUST be permanently blocked from OTP verification until admin intervention

---

### 4. Cart & Checkout Specification

- **FR-020**: Guest cart MUST be session-based (browser session persistence)

- **FR-021**: Upon login, guest cart MUST merge automatically into user cart

- **FR-022**: Cart merge MUST preserve all items from guest session; for duplicate products, user cart quantity takes precedence (guest quantity discarded)

- **FR-023**: Checkout MUST require authentication

- **FR-024**: Checkout MUST require mobile verification

- **FR-025**: If user is not verified at checkout start, OTP flow MUST be triggered, then checkout MUST resume

---

### 5. Lock & Block Enforcement Rules

- **FR-026**: Lock (BANNED) is security/policy based and enforces total system denial

- **FR-027**: Lock MUST be enforced globally at API gateway level

- **FR-028**: Locked users MUST see "You are banned" screen immediately

- **FR-029**: Lock MUST persist across app reinstalls (account-level enforcement)

- **FR-030**: Block is business/operational based and enforces capability-level restriction

- **FR-031**: Block MUST be enforced per feature, not globally

- **FR-032**: Blocked users CAN login, browse, and use customer features

- **FR-033**: Blocked users MUST NOT access blocked capabilities (selling, withdrawals per block type)

- **FR-042**: If user is Locked mid-transaction, system MUST immediately abort transaction, display ban screen, and forfeit any in-progress payment (no refund)

---

### 6. Seller/Artist Capability Rules

- **FR-034**: All users MUST start as customer role

- **FR-035**: Seller/artist role MUST require application submission

- **FR-036**: Seller/artist role MUST require admin approval

- **FR-037**: Until approved, applicant MUST be Blocked from selling capabilities

- **FR-038**: Rejected applicants MUST remain Blocked from selling but CAN use all customer features

- **FR-039**: Pending applicants MUST be able to use all customer features

---

### 7. Global Enforcement Matrix

| User State                        | Browse | Cart | Profile | Checkout | Pay | Order | Sell | Withdraw |
|----------------------------------|--------|------|---------|----------|-----|-------|------|----------|
| Guest                            | ✓      | ✓*   | ✗       | ✗        | ✗   | ✗     | ✗    | ✗        |
| Authenticated (Unverified)       | ✓      | ✓    | ✓       | ✗**      | ✗** | ✗**   | ✗    | ✗        |
| Authenticated (Verified)         | ✓      | ✓    | ✓       | ✓        | ✓   | ✓     | ***  | ***      |
| Locked (BANNED)                  | ✗      | ✗    | ✗       | ✗        | ✗   | ✗     | ✗    | ✗        |
| Blocked (Seller)                 | ✓      | ✓    | ✓       | ✓        | ✓   | ✓     | ✗    | ✗        |

*Cart is session-based for Guest  
**Triggers mobile verification flow, then allowed if verified  
***Requires approved seller/artist status

---

### Key Entities

- **User**: Core identity containing email, password hash, mobile number, verification status, lock status, block status, roles
- **User State**: Enumerated type (GUEST, AUTHENTICATED_UNVERIFIED, AUTHENTICATED_VERIFIED, LOCKED, BLOCKED)
- **Verification Record**: Mobile number, verification status, verification timestamp
- **Lock Record**: User ID, lock reason, lock timestamp, locked by (admin)
- **Block Record**: User ID, blocked capabilities (array), block reason, block timestamp
- **Cart**: User ID (nullable for guest), session ID (for guest), items, timestamps
- **Seller Application**: User ID, application status (PENDING, APPROVED, REJECTED), review notes, timestamps

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete registration in under 60 seconds
- **SC-002**: Login response displays within 2 seconds of credential submission
- **SC-003**: Mobile OTP verification completes within 30 seconds (excluding carrier delays)
- **SC-004**: Guest cart merge completes automatically within 1 second of login
- **SC-005**: 100% of Locked users are denied access on first API attempt (no bypass possible)
- **SC-006**: Blocked sellers can complete customer checkout flow without restriction
- **SC-007**: Verification flow resumes checkout without requiring user to restart checkout
- **SC-008**: Seller application processing does not impact customer feature availability
- **SC-009**: System correctly enforces all 40+ capability matrix combinations
- **SC-010**: No unverified user is able to complete payment (0% bypass rate)

---

## Assumptions

- OTP delivery is handled by external SMS provider; delivery delays are outside system control
- Email verification, while tracked, does not gate any critical user journey
- Cart merge strategy: user cart quantity takes precedence for duplicates; guest-only items are added
- Session persistence for guests uses standard browser session mechanisms
- Lock/Block enforcement is synchronous (no eventual consistency delays acceptable)
- Seller/artist approval is manual admin action; no automated approval flow

---

## Flutter Integration Instructions

> **IMPORTANT**: This section provides detailed integration instructions for the Flutter application. An AI agent will consume these instructions to implement the mobile client integration.

### Required State Variables

```
USER_STATE: Enum
  - GUEST
  - AUTHENTICATED_UNVERIFIED
  - AUTHENTICATED_VERIFIED
  - LOCKED
  - BLOCKED

USER_FLAGS:
  - is_mobile_verified: Boolean
  - is_email_verified: Boolean (optional, non-blocking)
  - is_locked: Boolean
  - is_blocked: Boolean
  - blocked_capabilities: List<String> (e.g., ["SELL", "WITHDRAW"])

SESSION_DATA:
  - access_token: String (nullable for guest)
  - refresh_token: String (nullable for guest)
  - session_id: String (for guest cart persistence)
```

### API Response Handling

**Login Response Must Include**:
```
{
  "access_token": "...",
  "refresh_token": "...",
  "user": {
    "id": "...",
    "email": "...",
    "mobile": "...",
    "is_mobile_verified": true/false,
    "is_locked": true/false,
    "is_blocked": true/false,
    "blocked_capabilities": [],
    "roles": ["CUSTOMER", "SELLER"]
  }
}
```

**Lock Detection**:
- HTTP 403 with error code `USER_LOCKED` → Display "You are banned" screen, clear all local auth state, prevent all navigation

**Verification Required Response**:
- HTTP 403 with error code `MOBILE_VERIFICATION_REQUIRED` → Trigger OTP flow, store pending action, resume after verification

### User State Derivation Logic

```
function deriveUserState():
  if not authenticated:
    return GUEST
  if user.is_locked:
    return LOCKED
  if user.is_blocked:
    return BLOCKED
  if user.is_mobile_verified:
    return AUTHENTICATED_VERIFIED
  else:
    return AUTHENTICATED_UNVERIFIED
```

### Capability Check Logic

```
function canPerformAction(action: String):
  state = deriveUserState()
  
  if state == LOCKED:
    return { allowed: false, reason: "BANNED" }
  
  if state == GUEST:
    if action in ["BROWSE", "VIEW_PRODUCT", "ADD_TO_CART"]:
      return { allowed: true }
    else:
      return { allowed: false, reason: "LOGIN_REQUIRED" }
  
  if action in ["CHECKOUT", "PAY", "CREATE_ORDER"]:
    if state == AUTHENTICATED_UNVERIFIED:
      return { allowed: false, reason: "VERIFICATION_REQUIRED" }
  
  if state == BLOCKED:
    if action in user.blocked_capabilities:
      return { allowed: false, reason: "CAPABILITY_BLOCKED" }
  
  return { allowed: true }
```

### Cart Merge Flow

1. On login success, check if `session_id` exists with guest cart items
2. Call `POST /cart/merge` with `{ session_id: "..." }`
3. Backend merges guest cart into user cart
4. Clear local session cart reference
5. Refresh user cart from server

### Verification Flow Integration

1. User attempts restricted action (checkout)
2. Check `canPerformAction("CHECKOUT")`
3. If result is `VERIFICATION_REQUIRED`:
   a. Store current navigation state / action context
   b. Navigate to OTP verification screen
   c. On OTP success, update local `is_mobile_verified = true`
   d. Pop OTP screen, resume stored action
4. If API returns `MOBILE_VERIFICATION_REQUIRED` mid-request:
   a. Catch error, store pending request context
   b. Show OTP flow
   c. On success, retry original request

### Lock Enforcement in Flutter

- On ANY API response with `USER_LOCKED` error:
  1. Clear all auth tokens
  2. Clear all user state
  3. Navigate to dedicated "You are banned" screen
  4. Block all back navigation
  5. Only option: Close app

- On app start, if stored token exists:
  1. Call `/auth/validate` endpoint
  2. If returns locked status, trigger lock flow above

### Block Enforcement in Flutter

- Store `blocked_capabilities` array locally after login
- Before any seller/artist action, check `blocked_capabilities.contains(action)`
- If blocked, show user-friendly message: "This feature is currently unavailable for your account"
- Allow all non-blocked actions to proceed normally

### Guest Cart Session Management

- Generate `session_id` UUID on first cart action if no auth token
- Store in secure local storage
- Attach to all guest cart requests as header or body param
- On login success, pass to merge endpoint
- Clear after successful merge

### State Persistence Requirements

- `USER_STATE` must persist across app restarts
- `is_mobile_verified` must persist and match server state
- `blocked_capabilities` must refresh on app start and after login
- `session_id` must persist for guests until login or explicit clear

### Error Code Reference

| Error Code | HTTP Status | Action |
|-----------|-------------|--------|
| USER_LOCKED | 403 | Show ban screen, clear auth |
| MOBILE_VERIFICATION_REQUIRED | 403 | Trigger OTP flow |
| CAPABILITY_BLOCKED | 403 | Show block message |
| SESSION_EXPIRED | 401 | Refresh token or re-login |
| OTP_EXPIRED | 400 | Show error, enforce 60-second wait |
| OTP_BLOCKED | 403 | Show "contact support" - 3 failed attempts |

### Testing Checklist for Flutter Integration

- [ ] Guest can browse without login
- [ ] Guest cart persists within session
- [ ] Login succeeds for unverified user
- [ ] Login fails for locked user with ban screen
- [ ] Cart merges on login
- [ ] Checkout triggers verification for unverified user
- [ ] Verified user completes checkout without OTP prompt
- [ ] Blocked seller can use customer features
- [ ] Blocked seller cannot access seller features
- [ ] Lock detection works on any API call
- [ ] App correctly handles mid-request lock detection
