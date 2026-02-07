# Test Summary

This document provides an overview of all test classes and methods for the Django backend user state logic implementation.

## Test Configuration

All tests use the following configuration:
- **Database**: SQLite in-memory (`:memory:`)
- **Password Hashing**: MD5 (for fast test execution)
- **Migrations**: Disabled
- **CSRF**: Disabled for API testing
- **Throttling**: Disabled for tests

Configuration file: [`test_settings.py`](../test_settings.py)

## Test Files Overview

### 1. User Model Tests
**File**: [`custom_auth/tests/test_user_model.py`](../custom_auth/tests/test_user_model.py)

**Class**: `TestUserModelExtensions`

Tests all new fields added to the User model for user state management.

| Test Method | Description |
|-------------|-------------|
| `test_default_is_mobile_verified_is_false` | Verifies `is_mobile_verified` defaults to False |
| `test_default_is_locked_is_false` | Verifies `is_locked` defaults to False |
| `test_default_locked_reason_is_none` | Verifies `locked_reason` defaults to None |
| `test_default_locked_at_is_none` | Verifies `locked_at` defaults to None |
| `test_default_is_blocked_is_false` | Verifies `is_blocked` defaults to False |
| `test_default_blocked_reason_is_none` | Verifies `blocked_reason` defaults to None |
| `test_default_blocked_capabilities_is_empty_list` | Verifies `blocked_capabilities` defaults to empty list |
| `test_default_email_verified_is_false` | Verifies `email_verified` defaults to False |
| `test_default_failed_login_attempts_is_zero` | Verifies `failed_login_attempts` defaults to 0 |
| `test_default_locked_until_is_none` | Verifies `locked_until` defaults to None |
| `test_can_set_is_mobile_verified_to_true` | Tests setting `is_mobile_verified` to True |
| `test_can_set_is_locked_to_true` | Tests setting `is_locked` to True with reason and timestamp |
| `test_can_set_is_blocked_to_true` | Tests setting `is_blocked` to True with reason and capabilities |
| `test_can_set_email_verified_to_true` | Tests setting `email_verified` to True |
| `test_can_increment_failed_login_attempts` | Tests incrementing `failed_login_attempts` |
| `test_can_set_locked_until` | Tests setting `locked_until` timestamp |
| `test_blocked_capabilities_accepts_list` | Tests that `blocked_capabilities` accepts a list |
| `test_blocked_capabilities_can_be_empty_list` | Tests that `blocked_capabilities` can be empty |
| `test_multiple_users_have_independent_state` | Tests that multiple users have independent state fields |

**Total Tests**: 18

---

### 2. Login User State Tests
**File**: [`custom_auth/tests/test_user_state.py`](../custom_auth/tests/test_user_state.py)

**Class**: `TestLoginUserState`

Tests that the login endpoint returns user state fields in the response.

| Test Method | Description |
|-------------|-------------|
| `test_login_returns_is_mobile_verified_in_response` | Verifies login response includes `is_mobile_verified` field |
| `test_login_returns_is_locked_in_response` | Verifies login response includes `is_locked` field |
| `test_login_returns_is_blocked_in_response` | Verifies login response includes `is_blocked` field |
| `test_login_returns_blocked_capabilities_in_response` | Verifies login response includes `blocked_capabilities` field |
| `test_login_with_unverified_mobile_still_works` | Tests that user with unverified mobile can still login |
| `test_login_with_blocked_capabilities_still_works` | Tests that user with blocked capabilities can still login |
| `test_login_returns_correct_mobile_verified_state` | Tests that login returns correct mobile verification state |
| `test_login_returns_correct_blocked_capabilities` | Tests that login returns correct blocked capabilities |
| `test_login_without_email_verification_fails` | Tests that login fails when email is not verified |
| `test_login_with_wrong_password_fails` | Tests that login fails with wrong password |
| `test_login_with_nonexistent_user_fails` | Tests that login fails with nonexistent user |

**Total Tests**: 11

---

### 3. Lock Enforcement Tests
**File**: [`custom_auth/tests/test_lock_block.py`](../custom_auth/tests/test_lock_block.py)

**Class**: `TestLockEnforcement`

Tests that locked users cannot login and that lock check happens before password check.

| Test Method | Description |
|-------------|-------------|
| `test_locked_user_cannot_login` | Verifies locked user cannot login (403 USER_LOCKED) |
| `test_locked_user_with_correct_password_still_blocked` | Verifies locked user with correct password is still blocked |
| `test_unlocked_user_can_login_normally` | Verifies unlocked user can login normally |
| `test_lock_check_happens_before_password_check` | Verifies lock check happens before password check |
| `test_locked_user_with_wrong_password_still_gets_locked_error` | Verifies locked user with wrong password gets locked error |
| `test_unlocked_user_with_wrong_password_fails_with_auth_error` | Verifies unlocked user with wrong password fails with auth error |
| `test_locked_user_response_includes_locked_reason` | Verifies locked user error response includes locked reason |
| `test_user_can_be_unlocked_and_login` | Tests that user can be unlocked and then login |
| `test_locked_user_without_email_verified_still_blocked` | Tests that locked user without email verified is still blocked |

**Total Tests**: 9

---

### 4. OTP Verification Tests
**File**: [`custom_auth/tests/test_verification.py`](../custom_auth/tests/test_verification.py)

**Class**: `TestOTPSend`

Tests OTP send functionality.

| Test Method | Description |
|-------------|-------------|
| `test_send_otp_creates_otp_verification_record` | Verifies send OTP creates OTPVerification record |
| `test_send_otp_returns_expiration_time` | Verifies send OTP returns expiration time |
| `test_send_otp_to_different_mobile_number` | Tests sending OTP to different mobile number |
| `test_send_otp_rate_limiting_max_three_per_hour` | Tests that send OTP is rate limited to max 3 per hour |

**Total Tests**: 4

**Class**: `TestOTPVerify`

Tests OTP verify functionality.

| Test Method | Description |
|-------------|-------------|
| `test_verify_correct_otp_sets_mobile_verified_true` | Verifies correct OTP sets `is_mobile_verified=True` |
| `test_verify_expired_otp_fails` | Verifies expired OTP fails |
| `test_verify_wrong_otp_increments_attempts` | Verifies wrong OTP increments attempts |
| `test_verify_max_attempts_lockout` | Verifies max attempts results in lockout |
| `test_verify_already_verified_user` | Tests verify for already verified user |
| `test_verify_nonexistent_otp_fails` | Tests verify with nonexistent OTP fails |
| `test_verify_without_authentication_fails` | Tests verify without authentication fails |
| `test_verify_resets_attempts_on_success` | Tests verify resets attempts on success |

**Total Tests**: 8

**Total OTP Tests**: 12

---

### 5. Cart Tests
**File**: [`cart/tests/test_cart.py`](../cart/tests/test_cart.py)

**Class**: `TestGuestCartCreation`

Tests guest cart creation with session_id.

| Test Method | Description |
|-------------|-------------|
| `test_create_guest_cart_with_session_id` | Tests creating a guest cart with session_id |
| `test_session_id_uniqueness_constraint` | Tests that session_id is unique |
| `test_get_or_create_returns_existing_cart` | Tests that get_or_create returns existing cart |
| `test_constraint_either_user_or_session_id_required` | Tests constraint: either user or session_id required |
| `test_cart_with_user_only` | Tests creating cart with user only |
| `test_cart_with_both_user_and_session_id_fails` | Tests cart with both user and session_id |

**Total Tests**: 6

**Class**: `TestGuestCartOperations`

Tests guest cart operations.

| Test Method | Description |
|-------------|-------------|
| `test_add_item_to_guest_cart` | Tests adding item to guest cart |
| `test_add_item_with_variants` | Tests adding item with variants |
| `test_update_item_quantity` | Tests updating cart item quantity |
| `test_remove_item_from_cart` | Tests removing item from cart |
| `test_clear_cart` | Tests clearing all items from cart |
| `test_get_guest_cart_via_api` | Tests getting guest cart via API |
| `test_add_item_to_guest_cart_via_api` | Tests adding item to guest cart via API |

**Total Tests**: 7

**Class**: `TestCartMerge`

Tests cart merge functionality.

| Test Method | Description |
|-------------|-------------|
| `test_merge_guest_cart_into_user_cart` | Tests merging guest cart into user cart |
| `test_merge_with_empty_user_cart` | Tests merging guest cart with empty user cart |
| `test_merge_with_nonexistent_guest_cart` | Tests merging with nonexistent guest cart |
| `test_merge_conflict_resolution_user_quantity_wins` | Tests merge conflict resolution: user quantity wins |
| `test_merge_with_product_variants` | Tests merging carts with product variants |
| `test_guest_cart_deleted_after_merge` | Tests that guest cart is deleted after merge |
| `test_merge_via_login_endpoint` | Tests cart merge via login endpoint |
| `test_merge_with_multiple_items` | Tests merging with multiple items |

**Total Tests**: 8

**Total Cart Tests**: 21

---

## Test Statistics

| Category | Test Classes | Test Methods |
|-----------|--------------|--------------|
| User Model | 1 | 18 |
| Login User State | 1 | 11 |
| Lock Enforcement | 1 | 9 |
| OTP Verification | 2 | 12 |
| Cart | 3 | 21 |
| **Total** | **8** | **71** |

## Test Execution Order

Tests are organized by feature area and can be run independently:

1. **User Model Tests** - Test all User model extensions
2. **Login User State Tests** - Test login endpoint user state response
3. **Lock Enforcement Tests** - Test lock enforcement on login
4. **OTP Verification Tests** - Test OTP send and verify
5. **Cart Tests** - Test guest cart and merge functionality

## Key Test Patterns

### Isolation
Each test method is isolated and independent:
- Uses `setUp()` to create fresh test data
- Does not depend on other test methods
- Can run in any order

### Assertions
Tests use clear assertions:
- `self.assertEqual()` for value comparison
- `self.assertTrue()` / `self.assertFalse()` for boolean checks
- `self.assertIn()` for membership checks
- `self.assertIsNone()` for null checks

### API Testing
API tests follow a consistent pattern:
1. Create test client (`APIClient()`)
2. Authenticate if needed
3. Make request with appropriate headers
4. Parse response with `.json()`
5. Assert on status code and response structure

### Error Handling
Error tests verify:
- Correct HTTP status codes (400, 401, 403, 429)
- Error response structure with `error` key
- Error codes match expected values
- Error messages are appropriate

## Running Tests

See [`RUN_TESTS.md`](RUN_TESTS.md) for detailed instructions on running tests.
