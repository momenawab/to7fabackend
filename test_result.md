(venv) momen@Momens-Mac-mini to7fabackend % pytest custom_auth/tests 
=================================================================================================================== test session starts ====================================================================================================================
platform darwin -- Python 3.9.6, pytest-8.4.2, pluggy-1.6.0 -- /Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/bin/python3
cachedir: .pytest_cache
rootdir: /Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend
configfile: pytest.ini
collected 123 items                                                                                                                                                                                                                                        

custom_auth/tests/test_lock_block.py::TestLockEnforcement::test_lock_check_happens_before_password_check SKIPPED (Tests require Redis connection)                                                                                                    [  0%]
custom_auth/tests/test_lock_block.py::TestLockEnforcement::test_locked_user_cannot_login SKIPPED (Tests require Redis connection)                                                                                                                    [  1%]
custom_auth/tests/test_lock_block.py::TestLockEnforcement::test_locked_user_response_includes_locked_reason SKIPPED (Tests require Redis connection)                                                                                                 [  2%]
custom_auth/tests/test_lock_block.py::TestLockEnforcement::test_locked_user_with_correct_password_still_blocked SKIPPED (Tests require Redis connection)                                                                                             [  3%]
custom_auth/tests/test_lock_block.py::TestLockEnforcement::test_locked_user_with_wrong_password_still_gets_locked_error SKIPPED (Tests require Redis connection)                                                                                     [  4%]
custom_auth/tests/test_lock_block.py::TestLockEnforcement::test_locked_user_without_email_verified_still_blocked SKIPPED (Tests require Redis connection)                                                                                            [  4%]
custom_auth/tests/test_lock_block.py::TestLockEnforcement::test_unlocked_user_can_login_normally SKIPPED (Tests require Redis connection)                                                                                                            [  5%]
custom_auth/tests/test_lock_block.py::TestLockEnforcement::test_unlocked_user_with_wrong_password_fails_with_auth_error SKIPPED (Tests require Redis connection)                                                                                     [  6%]
custom_auth/tests/test_lock_block.py::TestLockEnforcement::test_user_can_be_unlocked_and_login SKIPPED (Tests require Redis connection)                                                                                                              [  7%]
custom_auth/tests/test_lock_block.py::TestLockEnforcementMiddleware::test_middleware_allows_unlocked_user SKIPPED (Middleware tests don't work with JWT auth (auth happens at view level))                                                           [  8%]
custom_auth/tests/test_lock_block.py::TestLockEnforcementMiddleware::test_middleware_blocks_locked_user SKIPPED (Middleware tests don't work with JWT auth (auth happens at view level))                                                             [  8%]
custom_auth/tests/test_lock_block.py::TestLockEnforcementMiddleware::test_middleware_blocks_locked_user_from_all_endpoints SKIPPED (Middleware tests don't work with JWT auth (auth happens at view level))                                          [  9%]
custom_auth/tests/test_lock_block.py::TestLockEnforcementMiddleware::test_middleware_blocks_locked_user_from_post_requests SKIPPED (Middleware tests don't work with JWT auth (auth happens at view level))                                          [ 10%]
custom_auth/tests/test_lock_block.py::TestLockEnforcementMiddleware::test_middleware_blocks_locked_user_mid_transaction SKIPPED (Middleware tests don't work with JWT auth (auth happens at view level))                                             [ 11%]
custom_auth/tests/test_lock_block.py::TestLockEnforcementMiddleware::test_middleware_does_not_block_unauthenticated_requests SKIPPED (Middleware tests don't work with JWT auth (auth happens at view level))                                        [ 12%]
custom_auth/tests/test_lock_block.py::TestLockEnforcementMiddleware::test_middleware_returns_correct_error_message SKIPPED (Middleware tests don't work with JWT auth (auth happens at view level))                                                  [ 13%]
custom_auth/tests/test_lock_block.py::TestBlockEnforcement::test_blocked_capabilities_check PASSED                                                                                                                                                   [ 13%]
custom_auth/tests/test_lock_block.py::TestBlockEnforcement::test_blocked_user_can_access_customer_endpoints PASSED                                                                                                                                   [ 14%]
custom_auth/tests/test_lock_block.py::TestBlockEnforcement::test_blocked_user_denied_from_seller_endpoints PASSED                                                                                                                                    [ 15%]
custom_auth/tests/test_lock_block.py::TestBlockEnforcement::test_invalid_capability_raises_error PASSED                                                                                                                                              [ 16%]
custom_auth/tests/test_lock_block.py::TestBlockEnforcement::test_unblocked_user_can_access_seller_endpoints PASSED                                                                                                                                   [ 17%]
custom_auth/tests/test_lock_block.py::TestSellerApplicationBlockEnforcement::test_approved_application_unlocks_seller_features PASSED                                                                                                                [ 17%]
custom_auth/tests/test_lock_block.py::TestSellerApplicationBlockEnforcement::test_approved_seller_has_no_blocked_capabilities PASSED                                                                                                                 [ 18%]
custom_auth/tests/test_lock_block.py::TestSellerApplicationBlockEnforcement::test_pending_applicant_can_access_customer_features PASSED                                                                                                              [ 19%]
custom_auth/tests/test_lock_block.py::TestSellerApplicationBlockEnforcement::test_pending_applicant_has_blocked_capabilities PASSED                                                                                                                  [ 20%]
custom_auth/tests/test_lock_block.py::TestSellerApplicationBlockEnforcement::test_pending_application_blocks_seller_features PASSED                                                                                                                  [ 21%]
custom_auth/tests/test_lock_block.py::TestSellerApplicationBlockEnforcement::test_rejected_applicant_can_access_customer_features PASSED                                                                                                             [ 21%]
custom_auth/tests/test_lock_block.py::TestSellerApplicationBlockEnforcement::test_rejected_applicant_has_sell_capability_blocked PASSED                                                                                                              [ 22%]
custom_auth/tests/test_lock_block.py::TestSellerApplicationBlockEnforcement::test_rejected_application_blocks_seller_features PASSED                                                                                                                 [ 23%]
custom_auth/tests/test_spec001_capability.py::TestCapabilityBasedBlocking::test_sell_capability_blocked_for_seller FAILED                                                                                                                            [ 24%]
custom_auth/tests/test_spec001_capability.py::TestCapabilityBasedBlocking::test_withdraw_capability_blocked FAILED                                                                                                                                   [ 25%]
custom_auth/tests/test_spec001_capability.py::TestCapabilityBasedBlocking::test_multiple_capabilities_blocked FAILED                                                                                                                                 [ 26%]
custom_auth/tests/test_spec001_capability.py::TestBlockDoesNotAffectUnrelatedFeatures::test_blocked_seller_can_browse FAILED                                                                                                                         [ 26%]
custom_auth/tests/test_spec001_capability.py::TestBlockDoesNotAffectUnrelatedFeatures::test_blocked_seller_can_checkout FAILED                                                                                                                       [ 27%]
custom_auth/tests/test_spec001_capability.py::TestBlockDoesNotAffectUnrelatedFeatures::test_blocked_seller_can_view_profile FAILED                                                                                                                   [ 28%]
custom_auth/tests/test_spec001_capability.py::TestBlockDoesNotAffectUnrelatedFeatures::test_blocked_withdraw_can_still_sell FAILED                                                                                                                   [ 29%]
custom_auth/tests/test_spec001_capability.py::TestGlobalLockEnforcement::test_locked_user_denied_all_capabilities FAILED                                                                                                                             [ 30%]
custom_auth/tests/test_spec001_capability.py::TestGlobalLockEnforcement::test_locked_overrides_blocked_capabilities FAILED                                                                                                                           [ 30%]
custom_auth/tests/test_spec001_capability.py::TestUnblockedCapabilities::test_unblocked_user_can_sell FAILED                                                                                                                                         [ 31%]
custom_auth/tests/test_spec001_capability.py::TestUnblockedCapabilities::test_unblocked_user_can_withdraw FAILED                                                                                                                                     [ 32%]
custom_auth/tests/test_spec001_capability.py::TestUnblockedCapabilities::test_no_blocked_capabilities_allows_all FAILED                                                                                                                              [ 33%]
custom_auth/tests/test_spec001_login.py::TestLoginAllowsUnverifiedUsers::test_login_succeeds_for_unverified_mobile_user FAILED                                                                                                                       [ 34%]
custom_auth/tests/test_spec001_login.py::TestLoginAllowsUnverifiedUsers::test_login_does_not_check_mobile_verification FAILED                                                                                                                        [ 34%]
custom_auth/tests/test_spec001_login.py::TestLoginBlocksOnlyLockedUsers::test_login_fails_for_locked_user FAILED                                                                                                                                     [ 35%]
custom_auth/tests/test_spec001_login.py::TestLoginBlocksOnlyLockedUsers::test_login_succeeds_for_blocked_user FAILED                                                                                                                                 [ 36%]
custom_auth/tests/test_spec001_login.py::TestLoginBlocksOnlyLockedUsers::test_login_succeeds_for_verified_user FAILED                                                                                                                                [ 37%]
custom_auth/tests/test_spec001_login.py::TestLockEnforcedBeforePasswordValidation::test_lock_check_before_password FAILED                                                                                                                            [ 38%]
custom_auth/tests/test_spec001_login.py::TestLockEnforcedBeforePasswordValidation::test_locked_user_sees_banned_message FAILED                                                                                                                       [ 39%]
custom_auth/tests/test_spec001_login.py::TestLoginResponseFields::test_login_accepts_email_and_password FAILED                                                                                                                                       [ 39%]
custom_auth/tests/test_spec001_login.py::TestLoginResponseFields::test_login_returns_user_state_fields FAILED                                                                                                                                        [ 40%]
custom_auth/tests/test_spec001_login.py::TestRegistrationRequirements::test_registration_requires_email_password_mobile PASSED                                                                                                                       [ 41%]
custom_auth/tests/test_spec001_login.py::TestRegistrationRequirements::test_email_used_for_login_not_verification FAILED                                                                                                                             [ 42%]
custom_auth/tests/test_spec001_user_state.py::TestGuestStateDerivation::test_guest_user_has_no_authentication PASSED                                                                                                                                 [ 43%]
custom_auth/tests/test_spec001_user_state.py::TestGuestStateDerivation::test_guest_state_allows_browse FAILED                                                                                                                                        [ 43%]
custom_auth/tests/test_spec001_user_state.py::TestGuestStateDerivation::test_guest_state_allows_view_product FAILED                                                                                                                                  [ 44%]
custom_auth/tests/test_spec001_user_state.py::TestGuestStateDerivation::test_guest_state_allows_add_to_cart FAILED                                                                                                                                   [ 45%]
custom_auth/tests/test_spec001_user_state.py::TestAuthenticatedUnverifiedStateDerivation::test_unverified_user_derives_correct_state PASSED                                                                                                          [ 46%]
custom_auth/tests/test_spec001_user_state.py::TestAuthenticatedUnverifiedStateDerivation::test_unverified_state_allows_browsing FAILED                                                                                                               [ 47%]
custom_auth/tests/test_spec001_user_state.py::TestAuthenticatedUnverifiedStateDerivation::test_unverified_state_allows_cart_management FAILED                                                                                                        [ 47%]
custom_auth/tests/test_spec001_user_state.py::TestAuthenticatedUnverifiedStateDerivation::test_unverified_state_allows_profile_viewing FAILED                                                                                                        [ 48%]
custom_auth/tests/test_spec001_user_state.py::TestAuthenticatedUnverifiedStateDerivation::test_unverified_state_blocks_checkout FAILED                                                                                                               [ 49%]
custom_auth/tests/test_spec001_user_state.py::TestAuthenticatedUnverifiedStateDerivation::test_unverified_state_blocks_payment FAILED                                                                                                                [ 50%]
custom_auth/tests/test_spec001_user_state.py::TestAuthenticatedUnverifiedStateDerivation::test_unverified_state_blocks_order_creation FAILED                                                                                                         [ 51%]
custom_auth/tests/test_spec001_user_state.py::TestAuthenticatedVerifiedStateDerivation::test_verified_user_derives_correct_state PASSED                                                                                                              [ 52%]
custom_auth/tests/test_spec001_user_state.py::TestAuthenticatedVerifiedStateDerivation::test_verified_state_allows_checkout FAILED                                                                                                                   [ 52%]
custom_auth/tests/test_spec001_user_state.py::TestAuthenticatedVerifiedStateDerivation::test_verified_state_allows_payment FAILED                                                                                                                    [ 53%]
custom_auth/tests/test_spec001_user_state.py::TestAuthenticatedVerifiedStateDerivation::test_verified_state_allows_order_creation FAILED                                                                                                             [ 54%]
custom_auth/tests/test_spec001_user_state.py::TestAuthenticatedVerifiedStateDerivation::test_verified_state_allows_wallet_usage FAILED                                                                                                               [ 55%]
custom_auth/tests/test_spec001_user_state.py::TestLockedStateDerivation::test_locked_user_derives_correct_state PASSED                                                                                                                               [ 56%]
custom_auth/tests/test_spec001_user_state.py::TestLockedStateDerivation::test_locked_state_denies_all_access FAILED                                                                                                                                  [ 56%]
custom_auth/tests/test_spec001_user_state.py::TestLockedStateDerivation::test_locked_state_overrides_verification FAILED                                                                                                                             [ 57%]
custom_auth/tests/test_spec001_user_state.py::TestBlockedStateDerivation::test_blocked_user_derives_correct_state PASSED                                                                                                                             [ 58%]
custom_auth/tests/test_spec001_user_state.py::TestBlockedStateDerivation::test_blocked_state_allows_login FAILED                                                                                                                                     [ 59%]
custom_auth/tests/test_spec001_user_state.py::TestBlockedStateDerivation::test_blocked_state_allows_browsing FAILED                                                                                                                                  [ 60%]
custom_auth/tests/test_spec001_user_state.py::TestBlockedStateDerivation::test_blocked_state_allows_customer_features FAILED                                                                                                                         [ 60%]
custom_auth/tests/test_spec001_user_state.py::TestBlockedStateDerivation::test_blocked_state_blocks_specific_capability FAILED                                                                                                                       [ 61%]
custom_auth/tests/test_spec001_user_state.py::TestBlockedStateDerivation::test_blocked_state_allows_unblocked_capabilities FAILED                                                                                                                    [ 62%]
custom_auth/tests/test_spec001_user_state.py::TestStateDerivationPrecedence::test_locked_takes_precedence_over_blocked PASSED                                                                                                                        [ 63%]
custom_auth/tests/test_spec001_user_state.py::TestStateDerivationPrecedence::test_locked_takes_precedence_over_verified PASSED                                                                                                                       [ 64%]
custom_auth/tests/test_spec001_user_state.py::TestStateDerivationPrecedence::test_blocked_takes_precedence_over_unverified PASSED                                                                                                                    [ 65%]
custom_auth/tests/test_spec001_user_state.py::TestStateDerivationPrecedence::test_verified_is_default_when_no_restrictions PASSED                                                                                                                    [ 65%]
custom_auth/tests/test_user_model.py::TestUserModelExtensions::test_blocked_capabilities_accepts_list FAILED                                                                                                                                         [ 66%]
custom_auth/tests/test_user_model.py::TestUserModelExtensions::test_blocked_capabilities_can_be_empty_list FAILED                                                                                                                                    [ 67%]
custom_auth/tests/test_user_model.py::TestUserModelExtensions::test_can_increment_failed_login_attempts FAILED                                                                                                                                       [ 68%]
custom_auth/tests/test_user_model.py::TestUserModelExtensions::test_can_set_email_verified_to_true FAILED                                                                                                                                            [ 69%]
custom_auth/tests/test_user_model.py::TestUserModelExtensions::test_can_set_is_blocked_to_true FAILED                                                                                                                                                [ 69%]
custom_auth/tests/test_user_model.py::TestUserModelExtensions::test_can_set_is_locked_to_true FAILED                                                                                                                                                 [ 70%]
custom_auth/tests/test_user_model.py::TestUserModelExtensions::test_can_set_is_mobile_verified_to_true FAILED                                                                                                                                        [ 71%]
custom_auth/tests/test_user_model.py::TestUserModelExtensions::test_can_set_locked_until FAILED                                                                                                                                                      [ 72%]
custom_auth/tests/test_user_model.py::TestUserModelExtensions::test_default_blocked_capabilities_is_empty_list FAILED                                                                                                                                [ 73%]
custom_auth/tests/test_user_model.py::TestUserModelExtensions::test_default_blocked_reason_is_none FAILED                                                                                                                                            [ 73%]
custom_auth/tests/test_user_model.py::TestUserModelExtensions::test_default_email_verified_is_false FAILED                                                                                                                                           [ 74%]
custom_auth/tests/test_user_model.py::TestUserModelExtensions::test_default_failed_login_attempts_is_zero FAILED                                                                                                                                     [ 75%]
custom_auth/tests/test_user_model.py::TestUserModelExtensions::test_default_is_blocked_is_false FAILED                                                                                                                                               [ 76%]
custom_auth/tests/test_user_model.py::TestUserModelExtensions::test_default_is_locked_is_false FAILED                                                                                                                                                [ 77%]
custom_auth/tests/test_user_model.py::TestUserModelExtensions::test_default_is_mobile_verified_is_false FAILED                                                                                                                                       [ 78%]
custom_auth/tests/test_user_model.py::TestUserModelExtensions::test_default_locked_at_is_none FAILED                                                                                                                                                 [ 78%]
custom_auth/tests/test_user_model.py::TestUserModelExtensions::test_default_locked_reason_is_none FAILED                                                                                                                                             [ 79%]
custom_auth/tests/test_user_model.py::TestUserModelExtensions::test_default_locked_until_is_none FAILED                                                                                                                                              [ 80%]
custom_auth/tests/test_user_model.py::TestUserModelExtensions::test_multiple_users_have_independent_state FAILED                                                                                                                                     [ 81%]
custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_returns_blocked_capabilities_in_response FAILED                                                                                                                                 [ 82%]
custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_returns_correct_blocked_capabilities FAILED                                                                                                                                     [ 82%]
custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_returns_correct_mobile_verified_state FAILED                                                                                                                                    [ 83%]
custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_returns_is_blocked_in_response FAILED                                                                                                                                           [ 84%]
custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_returns_is_locked_in_response FAILED                                                                                                                                            [ 85%]
custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_returns_is_mobile_verified_in_response FAILED                                                                                                                                   [ 86%]
custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_with_blocked_capabilities_still_works FAILED                                                                                                                                    [ 86%]
custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_with_nonexistent_user_fails FAILED                                                                                                                                              [ 87%]
custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_with_unverified_mobile_still_works FAILED                                                                                                                                       [ 88%]
custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_with_wrong_password_fails FAILED                                                                                                                                                [ 89%]
custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_without_email_verification_fails FAILED                                                                                                                                         [ 90%]
custom_auth/tests/test_verification.py::TestOTPSend::test_send_otp_creates_otp_verification_record SKIPPED (OTP tests require SMS integration)                                                                                                       [ 91%]
custom_auth/tests/test_verification.py::TestOTPSend::test_send_otp_rate_limiting_max_three_per_hour SKIPPED (OTP tests require SMS integration)                                                                                                      [ 91%]
custom_auth/tests/test_verification.py::TestOTPSend::test_send_otp_returns_expiration_time SKIPPED (OTP tests require SMS integration)                                                                                                               [ 92%]
custom_auth/tests/test_verification.py::TestOTPSend::test_send_otp_to_different_mobile_number SKIPPED (OTP tests require SMS integration)                                                                                                            [ 93%]
custom_auth/tests/test_verification.py::TestOTPVerify::test_verify_already_verified_user SKIPPED (OTP tests require SMS integration)                                                                                                                 [ 94%]
custom_auth/tests/test_verification.py::TestOTPVerify::test_verify_correct_otp_sets_mobile_verified_true SKIPPED (OTP tests require SMS integration)                                                                                                 [ 95%]
custom_auth/tests/test_verification.py::TestOTPVerify::test_verify_expired_otp_fails SKIPPED (OTP tests require SMS integration)                                                                                                                     [ 95%]
custom_auth/tests/test_verification.py::TestOTPVerify::test_verify_max_attempts_lockout SKIPPED (OTP tests require SMS integration)                                                                                                                  [ 96%]
custom_auth/tests/test_verification.py::TestOTPVerify::test_verify_nonexistent_otp_fails SKIPPED (OTP tests require SMS integration)                                                                                                                 [ 97%]
custom_auth/tests/test_verification.py::TestOTPVerify::test_verify_resets_attempts_on_success SKIPPED (OTP tests require SMS integration)                                                                                                            [ 98%]
custom_auth/tests/test_verification.py::TestOTPVerify::test_verify_without_authentication_fails SKIPPED (OTP tests require SMS integration)                                                                                                          [ 99%]
custom_auth/tests/test_verification.py::TestOTPVerify::test_verify_wrong_otp_increments_attempts SKIPPED (OTP tests require SMS integration)                                                                                                         [100%]

========================================================================================================================= FAILURES =========================================================================================================================
___________________________________________________________________________________________ TestCapabilityBasedBlocking.test_sell_capability_blocked_for_seller ____________________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_spec001_capability.py:21: in test_sell_capability_blocked_for_seller
    user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")
_______________________________________________________________________________________________ TestCapabilityBasedBlocking.test_withdraw_capability_blocked _______________________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'user@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_spec001_capability.py:36: in test_withdraw_capability_blocked
    user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'user@example.com' for key 'custom_auth_user.email'")
______________________________________________________________________________________________ TestCapabilityBasedBlocking.test_multiple_capabilities_blocked ______________________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'user@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_spec001_capability.py:50: in test_multiple_capabilities_blocked
    user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'user@example.com' for key 'custom_auth_user.email'")
__________________________________________________________________________________________ TestBlockDoesNotAffectUnrelatedFeatures.test_blocked_seller_can_browse __________________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_spec001_capability.py:69: in test_blocked_seller_can_browse
    user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")
_________________________________________________________________________________________ TestBlockDoesNotAffectUnrelatedFeatures.test_blocked_seller_can_checkout _________________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_spec001_capability.py:82: in test_blocked_seller_can_checkout
    user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")
_______________________________________________________________________________________ TestBlockDoesNotAffectUnrelatedFeatures.test_blocked_seller_can_view_profile _______________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_spec001_capability.py:95: in test_blocked_seller_can_view_profile
    user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")
_______________________________________________________________________________________ TestBlockDoesNotAffectUnrelatedFeatures.test_blocked_withdraw_can_still_sell _______________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_spec001_capability.py:108: in test_blocked_withdraw_can_still_sell
    user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")
____________________________________________________________________________________________ TestGlobalLockEnforcement.test_locked_user_denied_all_capabilities ____________________________________________________________________________________________
custom_auth/tests/test_spec001_capability.py:134: in test_locked_user_denied_all_capabilities
    result = can_perform_action(user, action)
E   NameError: name 'can_perform_action' is not defined
___________________________________________________________________________________________ TestGlobalLockEnforcement.test_locked_overrides_blocked_capabilities ___________________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'user@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_spec001_capability.py:140: in test_locked_overrides_blocked_capabilities
    user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'user@example.com' for key 'custom_auth_user.email'")
__________________________________________________________________________________________________ TestUnblockedCapabilities.test_unblocked_user_can_sell __________________________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_spec001_capability.py:159: in test_unblocked_user_can_sell
    user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")
________________________________________________________________________________________________ TestUnblockedCapabilities.test_unblocked_user_can_withdraw ________________________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'user@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_spec001_capability.py:171: in test_unblocked_user_can_withdraw
    user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'user@example.com' for key 'custom_auth_user.email'")
____________________________________________________________________________________________ TestUnblockedCapabilities.test_no_blocked_capabilities_allows_all _____________________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'user@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_spec001_capability.py:183: in test_no_blocked_capabilities_allows_all
    user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'user@example.com' for key 'custom_auth_user.email'")
______________________________________________________________________________________ TestLoginAllowsUnverifiedUsers.test_login_succeeds_for_unverified_mobile_user _______________________________________________________________________________________
venv/lib/python3.9/site-packages/redis/connection.py:855: in connect_check_health
    sock = self.retry.call_with_retry(
venv/lib/python3.9/site-packages/redis/retry.py:116: in call_with_retry
    return do()
venv/lib/python3.9/site-packages/redis/connection.py:856: in <lambda>
    lambda: self._connect(), lambda error: self.disconnect(error)
venv/lib/python3.9/site-packages/redis/connection.py:1306: in _connect
    raise err
venv/lib/python3.9/site-packages/redis/connection.py:1290: in _connect
    sock.connect(socket_address)
E   ConnectionRefusedError: [Errno 61] Connection refused

During handling of the above exception, another exception occurred:
custom_auth/tests/test_spec001_login.py:31: in test_login_succeeds_for_unverified_mobile_user
    response = client.post(
venv/lib/python3.9/site-packages/rest_framework/test.py:299: in post
    response = super().post(
venv/lib/python3.9/site-packages/rest_framework/test.py:213: in post
    return self.generic('POST', path, data, content_type, **extra)
venv/lib/python3.9/site-packages/rest_framework/test.py:237: in generic
    return super().generic(
venv/lib/python3.9/site-packages/django/test/client.py:609: in generic
    return self.request(**r)
venv/lib/python3.9/site-packages/rest_framework/test.py:289: in request
    return super().request(**kwargs)
venv/lib/python3.9/site-packages/rest_framework/test.py:241: in request
    request = super().request(**kwargs)
venv/lib/python3.9/site-packages/django/test/client.py:891: in request
    self.check_exception(response)
venv/lib/python3.9/site-packages/django/test/client.py:738: in check_exception
    raise exc_value
venv/lib/python3.9/site-packages/django/core/handlers/exception.py:55: in inner
    response = get_response(request)
venv/lib/python3.9/site-packages/django/core/handlers/base.py:197: in _get_response
    response = wrapped_callback(request, *callback_args, **callback_kwargs)
venv/lib/python3.9/site-packages/django/views/decorators/csrf.py:56: in wrapper_view
    return view_func(*args, **kwargs)
venv/lib/python3.9/site-packages/django/views/generic/base.py:104: in view
    return self.dispatch(request, *args, **kwargs)
venv/lib/python3.9/site-packages/rest_framework/views.py:515: in dispatch
    response = self.handle_exception(exc)
venv/lib/python3.9/site-packages/rest_framework/views.py:475: in handle_exception
    self.raise_uncaught_exception(exc)
venv/lib/python3.9/site-packages/rest_framework/views.py:486: in raise_uncaught_exception
    raise exc
venv/lib/python3.9/site-packages/rest_framework/views.py:503: in dispatch
    self.initial(request, *args, **kwargs)
venv/lib/python3.9/site-packages/rest_framework/views.py:422: in initial
    self.check_throttles(request)
venv/lib/python3.9/site-packages/rest_framework/views.py:365: in check_throttles
    if not throttle.allow_request(request, self):
custom_auth/jwt_views.py:40: in allow_request
    return super().allow_request(request, view)
venv/lib/python3.9/site-packages/rest_framework/throttling.py:123: in allow_request
    self.history = self.cache.get(self.key, [])
venv/lib/python3.9/site-packages/django/core/cache/backends/redis.py:187: in get
    return self._cache.get(key, default)
venv/lib/python3.9/site-packages/django/core/cache/backends/redis.py:99: in get
    value = client.get(key)
venv/lib/python3.9/site-packages/redis/commands/core.py:1834: in get
    return self.execute_command("GET", name, keys=[name])
venv/lib/python3.9/site-packages/redis/client.py:657: in execute_command
    return self._execute_command(*args, **options)
venv/lib/python3.9/site-packages/redis/client.py:663: in _execute_command
    conn = self.connection or pool.get_connection()
venv/lib/python3.9/site-packages/redis/utils.py:196: in wrapper
    return func(*args, **kwargs)
venv/lib/python3.9/site-packages/redis/connection.py:2601: in get_connection
    connection.connect()
venv/lib/python3.9/site-packages/redis/connection.py:846: in connect
    self.connect_check_health(check_health=True)
venv/lib/python3.9/site-packages/redis/connection.py:863: in connect_check_health
    raise ConnectionError(self._error_message(e))
E   redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
------------------------------------------------------------------------------------------------------------------- Captured stderr call -------------------------------------------------------------------------------------------------------------------
Internal Server Error: /custom_auth/api/auth/login/
Traceback (most recent call last):
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 855, in connect_check_health
    sock = self.retry.call_with_retry(
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/retry.py", line 116, in call_with_retry
    return do()
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 856, in <lambda>
    lambda: self._connect(), lambda error: self.disconnect(error)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 1306, in _connect
    raise err
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 1290, in _connect
    sock.connect(socket_address)
ConnectionRefusedError: [Errno 61] Connection refused

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/handlers/exception.py", line 55, in inner
    response = get_response(request)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/handlers/base.py", line 197, in _get_response
    response = wrapped_callback(request, *callback_args, **callback_kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/views/decorators/csrf.py", line 56, in wrapper_view
    return view_func(*args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/views/generic/base.py", line 104, in view
    return self.dispatch(request, *args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 515, in dispatch
    response = self.handle_exception(exc)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 475, in handle_exception
    self.raise_uncaught_exception(exc)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 486, in raise_uncaught_exception
    raise exc
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 503, in dispatch
    self.initial(request, *args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 422, in initial
    self.check_throttles(request)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 365, in check_throttles
    if not throttle.allow_request(request, self):
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/jwt_views.py", line 40, in allow_request
    return super().allow_request(request, view)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/throttling.py", line 123, in allow_request
    self.history = self.cache.get(self.key, [])
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/cache/backends/redis.py", line 187, in get
    return self._cache.get(key, default)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/cache/backends/redis.py", line 99, in get
    value = client.get(key)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/commands/core.py", line 1834, in get
    return self.execute_command("GET", name, keys=[name])
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/client.py", line 657, in execute_command
    return self._execute_command(*args, **options)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/client.py", line 663, in _execute_command
    conn = self.connection or pool.get_connection()
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/utils.py", line 196, in wrapper
    return func(*args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 2601, in get_connection
    connection.connect()
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 846, in connect
    self.connect_check_health(check_health=True)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 863, in connect_check_health
    raise ConnectionError(self._error_message(e))
redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
-------------------------------------------------------------------------------------------------------------------- Captured log call ---------------------------------------------------------------------------------------------------------------------
ERROR    django.request:log.py:241 Internal Server Error: /custom_auth/api/auth/login/
Traceback (most recent call last):
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 855, in connect_check_health
    sock = self.retry.call_with_retry(
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/retry.py", line 116, in call_with_retry
    return do()
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 856, in <lambda>
    lambda: self._connect(), lambda error: self.disconnect(error)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 1306, in _connect
    raise err
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 1290, in _connect
    sock.connect(socket_address)
ConnectionRefusedError: [Errno 61] Connection refused

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/handlers/exception.py", line 55, in inner
    response = get_response(request)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/handlers/base.py", line 197, in _get_response
    response = wrapped_callback(request, *callback_args, **callback_kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/views/decorators/csrf.py", line 56, in wrapper_view
    return view_func(*args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/views/generic/base.py", line 104, in view
    return self.dispatch(request, *args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 515, in dispatch
    response = self.handle_exception(exc)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 475, in handle_exception
    self.raise_uncaught_exception(exc)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 486, in raise_uncaught_exception
    raise exc
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 503, in dispatch
    self.initial(request, *args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 422, in initial
    self.check_throttles(request)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 365, in check_throttles
    if not throttle.allow_request(request, self):
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/jwt_views.py", line 40, in allow_request
    return super().allow_request(request, view)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/throttling.py", line 123, in allow_request
    self.history = self.cache.get(self.key, [])
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/cache/backends/redis.py", line 187, in get
    return self._cache.get(key, default)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/cache/backends/redis.py", line 99, in get
    value = client.get(key)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/commands/core.py", line 1834, in get
    return self.execute_command("GET", name, keys=[name])
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/client.py", line 657, in execute_command
    return self._execute_command(*args, **options)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/client.py", line 663, in _execute_command
    conn = self.connection or pool.get_connection()
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/utils.py", line 196, in wrapper
    return func(*args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 2601, in get_connection
    connection.connect()
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 846, in connect
    self.connect_check_health(check_health=True)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 863, in connect_check_health
    raise ConnectionError(self._error_message(e))
redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
_______________________________________________________________________________________ TestLoginAllowsUnverifiedUsers.test_login_does_not_check_mobile_verification _______________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'user@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_spec001_login.py:44: in test_login_does_not_check_mobile_verification
    user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'user@example.com' for key 'custom_auth_user.email'")
_____________________________________________________________________________________________ TestLoginBlocksOnlyLockedUsers.test_login_fails_for_locked_user ______________________________________________________________________________________________
venv/lib/python3.9/site-packages/redis/connection.py:855: in connect_check_health
    sock = self.retry.call_with_retry(
venv/lib/python3.9/site-packages/redis/retry.py:116: in call_with_retry
    return do()
venv/lib/python3.9/site-packages/redis/connection.py:856: in <lambda>
    lambda: self._connect(), lambda error: self.disconnect(error)
venv/lib/python3.9/site-packages/redis/connection.py:1306: in _connect
    raise err
venv/lib/python3.9/site-packages/redis/connection.py:1290: in _connect
    sock.connect(socket_address)
E   ConnectionRefusedError: [Errno 61] Connection refused

During handling of the above exception, another exception occurred:
custom_auth/tests/test_spec001_login.py:76: in test_login_fails_for_locked_user
    response = client.post(
venv/lib/python3.9/site-packages/rest_framework/test.py:299: in post
    response = super().post(
venv/lib/python3.9/site-packages/rest_framework/test.py:213: in post
    return self.generic('POST', path, data, content_type, **extra)
venv/lib/python3.9/site-packages/rest_framework/test.py:237: in generic
    return super().generic(
venv/lib/python3.9/site-packages/django/test/client.py:609: in generic
    return self.request(**r)
venv/lib/python3.9/site-packages/rest_framework/test.py:289: in request
    return super().request(**kwargs)
venv/lib/python3.9/site-packages/rest_framework/test.py:241: in request
    request = super().request(**kwargs)
venv/lib/python3.9/site-packages/django/test/client.py:891: in request
    self.check_exception(response)
venv/lib/python3.9/site-packages/django/test/client.py:738: in check_exception
    raise exc_value
venv/lib/python3.9/site-packages/django/core/handlers/exception.py:55: in inner
    response = get_response(request)
venv/lib/python3.9/site-packages/django/core/handlers/base.py:197: in _get_response
    response = wrapped_callback(request, *callback_args, **callback_kwargs)
venv/lib/python3.9/site-packages/django/views/decorators/csrf.py:56: in wrapper_view
    return view_func(*args, **kwargs)
venv/lib/python3.9/site-packages/django/views/generic/base.py:104: in view
    return self.dispatch(request, *args, **kwargs)
venv/lib/python3.9/site-packages/rest_framework/views.py:515: in dispatch
    response = self.handle_exception(exc)
venv/lib/python3.9/site-packages/rest_framework/views.py:475: in handle_exception
    self.raise_uncaught_exception(exc)
venv/lib/python3.9/site-packages/rest_framework/views.py:486: in raise_uncaught_exception
    raise exc
venv/lib/python3.9/site-packages/rest_framework/views.py:503: in dispatch
    self.initial(request, *args, **kwargs)
venv/lib/python3.9/site-packages/rest_framework/views.py:422: in initial
    self.check_throttles(request)
venv/lib/python3.9/site-packages/rest_framework/views.py:365: in check_throttles
    if not throttle.allow_request(request, self):
custom_auth/jwt_views.py:40: in allow_request
    return super().allow_request(request, view)
venv/lib/python3.9/site-packages/rest_framework/throttling.py:123: in allow_request
    self.history = self.cache.get(self.key, [])
venv/lib/python3.9/site-packages/django/core/cache/backends/redis.py:187: in get
    return self._cache.get(key, default)
venv/lib/python3.9/site-packages/django/core/cache/backends/redis.py:99: in get
    value = client.get(key)
venv/lib/python3.9/site-packages/redis/commands/core.py:1834: in get
    return self.execute_command("GET", name, keys=[name])
venv/lib/python3.9/site-packages/redis/client.py:657: in execute_command
    return self._execute_command(*args, **options)
venv/lib/python3.9/site-packages/redis/client.py:663: in _execute_command
    conn = self.connection or pool.get_connection()
venv/lib/python3.9/site-packages/redis/utils.py:196: in wrapper
    return func(*args, **kwargs)
venv/lib/python3.9/site-packages/redis/connection.py:2601: in get_connection
    connection.connect()
venv/lib/python3.9/site-packages/redis/connection.py:846: in connect
    self.connect_check_health(check_health=True)
venv/lib/python3.9/site-packages/redis/connection.py:863: in connect_check_health
    raise ConnectionError(self._error_message(e))
E   redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
------------------------------------------------------------------------------------------------------------------- Captured stderr call -------------------------------------------------------------------------------------------------------------------
Internal Server Error: /custom_auth/api/auth/login/
Traceback (most recent call last):
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 855, in connect_check_health
    sock = self.retry.call_with_retry(
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/retry.py", line 116, in call_with_retry
    return do()
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 856, in <lambda>
    lambda: self._connect(), lambda error: self.disconnect(error)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 1306, in _connect
    raise err
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 1290, in _connect
    sock.connect(socket_address)
ConnectionRefusedError: [Errno 61] Connection refused

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/handlers/exception.py", line 55, in inner
    response = get_response(request)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/handlers/base.py", line 197, in _get_response
    response = wrapped_callback(request, *callback_args, **callback_kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/views/decorators/csrf.py", line 56, in wrapper_view
    return view_func(*args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/views/generic/base.py", line 104, in view
    return self.dispatch(request, *args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 515, in dispatch
    response = self.handle_exception(exc)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 475, in handle_exception
    self.raise_uncaught_exception(exc)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 486, in raise_uncaught_exception
    raise exc
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 503, in dispatch
    self.initial(request, *args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 422, in initial
    self.check_throttles(request)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 365, in check_throttles
    if not throttle.allow_request(request, self):
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/jwt_views.py", line 40, in allow_request
    return super().allow_request(request, view)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/throttling.py", line 123, in allow_request
    self.history = self.cache.get(self.key, [])
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/cache/backends/redis.py", line 187, in get
    return self._cache.get(key, default)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/cache/backends/redis.py", line 99, in get
    value = client.get(key)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/commands/core.py", line 1834, in get
    return self.execute_command("GET", name, keys=[name])
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/client.py", line 657, in execute_command
    return self._execute_command(*args, **options)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/client.py", line 663, in _execute_command
    conn = self.connection or pool.get_connection()
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/utils.py", line 196, in wrapper
    return func(*args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 2601, in get_connection
    connection.connect()
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 846, in connect
    self.connect_check_health(check_health=True)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 863, in connect_check_health
    raise ConnectionError(self._error_message(e))
redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
-------------------------------------------------------------------------------------------------------------------- Captured log call ---------------------------------------------------------------------------------------------------------------------
ERROR    django.request:log.py:241 Internal Server Error: /custom_auth/api/auth/login/
Traceback (most recent call last):
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 855, in connect_check_health
    sock = self.retry.call_with_retry(
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/retry.py", line 116, in call_with_retry
    return do()
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 856, in <lambda>
    lambda: self._connect(), lambda error: self.disconnect(error)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 1306, in _connect
    raise err
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 1290, in _connect
    sock.connect(socket_address)
ConnectionRefusedError: [Errno 61] Connection refused

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/handlers/exception.py", line 55, in inner
    response = get_response(request)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/handlers/base.py", line 197, in _get_response
    response = wrapped_callback(request, *callback_args, **callback_kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/views/decorators/csrf.py", line 56, in wrapper_view
    return view_func(*args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/views/generic/base.py", line 104, in view
    return self.dispatch(request, *args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 515, in dispatch
    response = self.handle_exception(exc)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 475, in handle_exception
    self.raise_uncaught_exception(exc)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 486, in raise_uncaught_exception
    raise exc
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 503, in dispatch
    self.initial(request, *args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 422, in initial
    self.check_throttles(request)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 365, in check_throttles
    if not throttle.allow_request(request, self):
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/jwt_views.py", line 40, in allow_request
    return super().allow_request(request, view)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/throttling.py", line 123, in allow_request
    self.history = self.cache.get(self.key, [])
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/cache/backends/redis.py", line 187, in get
    return self._cache.get(key, default)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/cache/backends/redis.py", line 99, in get
    value = client.get(key)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/commands/core.py", line 1834, in get
    return self.execute_command("GET", name, keys=[name])
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/client.py", line 657, in execute_command
    return self._execute_command(*args, **options)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/client.py", line 663, in _execute_command
    conn = self.connection or pool.get_connection()
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/utils.py", line 196, in wrapper
    return func(*args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 2601, in get_connection
    connection.connect()
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 846, in connect
    self.connect_check_health(check_health=True)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 863, in connect_check_health
    raise ConnectionError(self._error_message(e))
redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
___________________________________________________________________________________________ TestLoginBlocksOnlyLockedUsers.test_login_succeeds_for_blocked_user ____________________________________________________________________________________________
venv/lib/python3.9/site-packages/redis/connection.py:855: in connect_check_health
    sock = self.retry.call_with_retry(
venv/lib/python3.9/site-packages/redis/retry.py:116: in call_with_retry
    return do()
venv/lib/python3.9/site-packages/redis/connection.py:856: in <lambda>
    lambda: self._connect(), lambda error: self.disconnect(error)
venv/lib/python3.9/site-packages/redis/connection.py:1306: in _connect
    raise err
venv/lib/python3.9/site-packages/redis/connection.py:1290: in _connect
    sock.connect(socket_address)
E   ConnectionRefusedError: [Errno 61] Connection refused

During handling of the above exception, another exception occurred:
custom_auth/tests/test_spec001_login.py:95: in test_login_succeeds_for_blocked_user
    response = client.post(
venv/lib/python3.9/site-packages/rest_framework/test.py:299: in post
    response = super().post(
venv/lib/python3.9/site-packages/rest_framework/test.py:213: in post
    return self.generic('POST', path, data, content_type, **extra)
venv/lib/python3.9/site-packages/rest_framework/test.py:237: in generic
    return super().generic(
venv/lib/python3.9/site-packages/django/test/client.py:609: in generic
    return self.request(**r)
venv/lib/python3.9/site-packages/rest_framework/test.py:289: in request
    return super().request(**kwargs)
venv/lib/python3.9/site-packages/rest_framework/test.py:241: in request
    request = super().request(**kwargs)
venv/lib/python3.9/site-packages/django/test/client.py:891: in request
    self.check_exception(response)
venv/lib/python3.9/site-packages/django/test/client.py:738: in check_exception
    raise exc_value
venv/lib/python3.9/site-packages/django/core/handlers/exception.py:55: in inner
    response = get_response(request)
venv/lib/python3.9/site-packages/django/core/handlers/base.py:197: in _get_response
    response = wrapped_callback(request, *callback_args, **callback_kwargs)
venv/lib/python3.9/site-packages/django/views/decorators/csrf.py:56: in wrapper_view
    return view_func(*args, **kwargs)
venv/lib/python3.9/site-packages/django/views/generic/base.py:104: in view
    return self.dispatch(request, *args, **kwargs)
venv/lib/python3.9/site-packages/rest_framework/views.py:515: in dispatch
    response = self.handle_exception(exc)
venv/lib/python3.9/site-packages/rest_framework/views.py:475: in handle_exception
    self.raise_uncaught_exception(exc)
venv/lib/python3.9/site-packages/rest_framework/views.py:486: in raise_uncaught_exception
    raise exc
venv/lib/python3.9/site-packages/rest_framework/views.py:503: in dispatch
    self.initial(request, *args, **kwargs)
venv/lib/python3.9/site-packages/rest_framework/views.py:422: in initial
    self.check_throttles(request)
venv/lib/python3.9/site-packages/rest_framework/views.py:365: in check_throttles
    if not throttle.allow_request(request, self):
custom_auth/jwt_views.py:40: in allow_request
    return super().allow_request(request, view)
venv/lib/python3.9/site-packages/rest_framework/throttling.py:123: in allow_request
    self.history = self.cache.get(self.key, [])
venv/lib/python3.9/site-packages/django/core/cache/backends/redis.py:187: in get
    return self._cache.get(key, default)
venv/lib/python3.9/site-packages/django/core/cache/backends/redis.py:99: in get
    value = client.get(key)
venv/lib/python3.9/site-packages/redis/commands/core.py:1834: in get
    return self.execute_command("GET", name, keys=[name])
venv/lib/python3.9/site-packages/redis/client.py:657: in execute_command
    return self._execute_command(*args, **options)
venv/lib/python3.9/site-packages/redis/client.py:663: in _execute_command
    conn = self.connection or pool.get_connection()
venv/lib/python3.9/site-packages/redis/utils.py:196: in wrapper
    return func(*args, **kwargs)
venv/lib/python3.9/site-packages/redis/connection.py:2601: in get_connection
    connection.connect()
venv/lib/python3.9/site-packages/redis/connection.py:846: in connect
    self.connect_check_health(check_health=True)
venv/lib/python3.9/site-packages/redis/connection.py:863: in connect_check_health
    raise ConnectionError(self._error_message(e))
E   redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
------------------------------------------------------------------------------------------------------------------- Captured stderr call -------------------------------------------------------------------------------------------------------------------
Internal Server Error: /custom_auth/api/auth/login/
Traceback (most recent call last):
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 855, in connect_check_health
    sock = self.retry.call_with_retry(
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/retry.py", line 116, in call_with_retry
    return do()
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 856, in <lambda>
    lambda: self._connect(), lambda error: self.disconnect(error)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 1306, in _connect
    raise err
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 1290, in _connect
    sock.connect(socket_address)
ConnectionRefusedError: [Errno 61] Connection refused

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/handlers/exception.py", line 55, in inner
    response = get_response(request)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/handlers/base.py", line 197, in _get_response
    response = wrapped_callback(request, *callback_args, **callback_kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/views/decorators/csrf.py", line 56, in wrapper_view
    return view_func(*args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/views/generic/base.py", line 104, in view
    return self.dispatch(request, *args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 515, in dispatch
    response = self.handle_exception(exc)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 475, in handle_exception
    self.raise_uncaught_exception(exc)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 486, in raise_uncaught_exception
    raise exc
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 503, in dispatch
    self.initial(request, *args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 422, in initial
    self.check_throttles(request)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 365, in check_throttles
    if not throttle.allow_request(request, self):
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/jwt_views.py", line 40, in allow_request
    return super().allow_request(request, view)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/throttling.py", line 123, in allow_request
    self.history = self.cache.get(self.key, [])
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/cache/backends/redis.py", line 187, in get
    return self._cache.get(key, default)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/cache/backends/redis.py", line 99, in get
    value = client.get(key)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/commands/core.py", line 1834, in get
    return self.execute_command("GET", name, keys=[name])
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/client.py", line 657, in execute_command
    return self._execute_command(*args, **options)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/client.py", line 663, in _execute_command
    conn = self.connection or pool.get_connection()
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/utils.py", line 196, in wrapper
    return func(*args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 2601, in get_connection
    connection.connect()
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 846, in connect
    self.connect_check_health(check_health=True)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 863, in connect_check_health
    raise ConnectionError(self._error_message(e))
redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
-------------------------------------------------------------------------------------------------------------------- Captured log call ---------------------------------------------------------------------------------------------------------------------
ERROR    django.request:log.py:241 Internal Server Error: /custom_auth/api/auth/login/
Traceback (most recent call last):
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 855, in connect_check_health
    sock = self.retry.call_with_retry(
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/retry.py", line 116, in call_with_retry
    return do()
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 856, in <lambda>
    lambda: self._connect(), lambda error: self.disconnect(error)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 1306, in _connect
    raise err
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 1290, in _connect
    sock.connect(socket_address)
ConnectionRefusedError: [Errno 61] Connection refused

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/handlers/exception.py", line 55, in inner
    response = get_response(request)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/handlers/base.py", line 197, in _get_response
    response = wrapped_callback(request, *callback_args, **callback_kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/views/decorators/csrf.py", line 56, in wrapper_view
    return view_func(*args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/views/generic/base.py", line 104, in view
    return self.dispatch(request, *args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 515, in dispatch
    response = self.handle_exception(exc)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 475, in handle_exception
    self.raise_uncaught_exception(exc)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 486, in raise_uncaught_exception
    raise exc
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 503, in dispatch
    self.initial(request, *args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 422, in initial
    self.check_throttles(request)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 365, in check_throttles
    if not throttle.allow_request(request, self):
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/jwt_views.py", line 40, in allow_request
    return super().allow_request(request, view)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/throttling.py", line 123, in allow_request
    self.history = self.cache.get(self.key, [])
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/cache/backends/redis.py", line 187, in get
    return self._cache.get(key, default)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/cache/backends/redis.py", line 99, in get
    value = client.get(key)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/commands/core.py", line 1834, in get
    return self.execute_command("GET", name, keys=[name])
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/client.py", line 657, in execute_command
    return self._execute_command(*args, **options)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/client.py", line 663, in _execute_command
    conn = self.connection or pool.get_connection()
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/utils.py", line 196, in wrapper
    return func(*args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 2601, in get_connection
    connection.connect()
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 846, in connect
    self.connect_check_health(check_health=True)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 863, in connect_check_health
    raise ConnectionError(self._error_message(e))
redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
___________________________________________________________________________________________ TestLoginBlocksOnlyLockedUsers.test_login_succeeds_for_verified_user ___________________________________________________________________________________________
venv/lib/python3.9/site-packages/redis/connection.py:855: in connect_check_health
    sock = self.retry.call_with_retry(
venv/lib/python3.9/site-packages/redis/retry.py:116: in call_with_retry
    return do()
venv/lib/python3.9/site-packages/redis/connection.py:856: in <lambda>
    lambda: self._connect(), lambda error: self.disconnect(error)
venv/lib/python3.9/site-packages/redis/connection.py:1306: in _connect
    raise err
venv/lib/python3.9/site-packages/redis/connection.py:1290: in _connect
    sock.connect(socket_address)
E   ConnectionRefusedError: [Errno 61] Connection refused

During handling of the above exception, another exception occurred:
custom_auth/tests/test_spec001_login.py:113: in test_login_succeeds_for_verified_user
    response = client.post(
venv/lib/python3.9/site-packages/rest_framework/test.py:299: in post
    response = super().post(
venv/lib/python3.9/site-packages/rest_framework/test.py:213: in post
    return self.generic('POST', path, data, content_type, **extra)
venv/lib/python3.9/site-packages/rest_framework/test.py:237: in generic
    return super().generic(
venv/lib/python3.9/site-packages/django/test/client.py:609: in generic
    return self.request(**r)
venv/lib/python3.9/site-packages/rest_framework/test.py:289: in request
    return super().request(**kwargs)
venv/lib/python3.9/site-packages/rest_framework/test.py:241: in request
    request = super().request(**kwargs)
venv/lib/python3.9/site-packages/django/test/client.py:891: in request
    self.check_exception(response)
venv/lib/python3.9/site-packages/django/test/client.py:738: in check_exception
    raise exc_value
venv/lib/python3.9/site-packages/django/core/handlers/exception.py:55: in inner
    response = get_response(request)
venv/lib/python3.9/site-packages/django/core/handlers/base.py:197: in _get_response
    response = wrapped_callback(request, *callback_args, **callback_kwargs)
venv/lib/python3.9/site-packages/django/views/decorators/csrf.py:56: in wrapper_view
    return view_func(*args, **kwargs)
venv/lib/python3.9/site-packages/django/views/generic/base.py:104: in view
    return self.dispatch(request, *args, **kwargs)
venv/lib/python3.9/site-packages/rest_framework/views.py:515: in dispatch
    response = self.handle_exception(exc)
venv/lib/python3.9/site-packages/rest_framework/views.py:475: in handle_exception
    self.raise_uncaught_exception(exc)
venv/lib/python3.9/site-packages/rest_framework/views.py:486: in raise_uncaught_exception
    raise exc
venv/lib/python3.9/site-packages/rest_framework/views.py:503: in dispatch
    self.initial(request, *args, **kwargs)
venv/lib/python3.9/site-packages/rest_framework/views.py:422: in initial
    self.check_throttles(request)
venv/lib/python3.9/site-packages/rest_framework/views.py:365: in check_throttles
    if not throttle.allow_request(request, self):
custom_auth/jwt_views.py:40: in allow_request
    return super().allow_request(request, view)
venv/lib/python3.9/site-packages/rest_framework/throttling.py:123: in allow_request
    self.history = self.cache.get(self.key, [])
venv/lib/python3.9/site-packages/django/core/cache/backends/redis.py:187: in get
    return self._cache.get(key, default)
venv/lib/python3.9/site-packages/django/core/cache/backends/redis.py:99: in get
    value = client.get(key)
venv/lib/python3.9/site-packages/redis/commands/core.py:1834: in get
    return self.execute_command("GET", name, keys=[name])
venv/lib/python3.9/site-packages/redis/client.py:657: in execute_command
    return self._execute_command(*args, **options)
venv/lib/python3.9/site-packages/redis/client.py:663: in _execute_command
    conn = self.connection or pool.get_connection()
venv/lib/python3.9/site-packages/redis/utils.py:196: in wrapper
    return func(*args, **kwargs)
venv/lib/python3.9/site-packages/redis/connection.py:2601: in get_connection
    connection.connect()
venv/lib/python3.9/site-packages/redis/connection.py:846: in connect
    self.connect_check_health(check_health=True)
venv/lib/python3.9/site-packages/redis/connection.py:863: in connect_check_health
    raise ConnectionError(self._error_message(e))
E   redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
------------------------------------------------------------------------------------------------------------------- Captured stderr call -------------------------------------------------------------------------------------------------------------------
Internal Server Error: /custom_auth/api/auth/login/
Traceback (most recent call last):
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 855, in connect_check_health
    sock = self.retry.call_with_retry(
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/retry.py", line 116, in call_with_retry
    return do()
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 856, in <lambda>
    lambda: self._connect(), lambda error: self.disconnect(error)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 1306, in _connect
    raise err
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 1290, in _connect
    sock.connect(socket_address)
ConnectionRefusedError: [Errno 61] Connection refused

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/handlers/exception.py", line 55, in inner
    response = get_response(request)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/handlers/base.py", line 197, in _get_response
    response = wrapped_callback(request, *callback_args, **callback_kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/views/decorators/csrf.py", line 56, in wrapper_view
    return view_func(*args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/views/generic/base.py", line 104, in view
    return self.dispatch(request, *args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 515, in dispatch
    response = self.handle_exception(exc)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 475, in handle_exception
    self.raise_uncaught_exception(exc)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 486, in raise_uncaught_exception
    raise exc
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 503, in dispatch
    self.initial(request, *args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 422, in initial
    self.check_throttles(request)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 365, in check_throttles
    if not throttle.allow_request(request, self):
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/jwt_views.py", line 40, in allow_request
    return super().allow_request(request, view)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/throttling.py", line 123, in allow_request
    self.history = self.cache.get(self.key, [])
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/cache/backends/redis.py", line 187, in get
    return self._cache.get(key, default)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/cache/backends/redis.py", line 99, in get
    value = client.get(key)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/commands/core.py", line 1834, in get
    return self.execute_command("GET", name, keys=[name])
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/client.py", line 657, in execute_command
    return self._execute_command(*args, **options)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/client.py", line 663, in _execute_command
    conn = self.connection or pool.get_connection()
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/utils.py", line 196, in wrapper
    return func(*args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 2601, in get_connection
    connection.connect()
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 846, in connect
    self.connect_check_health(check_health=True)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 863, in connect_check_health
    raise ConnectionError(self._error_message(e))
redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
-------------------------------------------------------------------------------------------------------------------- Captured log call ---------------------------------------------------------------------------------------------------------------------
ERROR    django.request:log.py:241 Internal Server Error: /custom_auth/api/auth/login/
Traceback (most recent call last):
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 855, in connect_check_health
    sock = self.retry.call_with_retry(
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/retry.py", line 116, in call_with_retry
    return do()
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 856, in <lambda>
    lambda: self._connect(), lambda error: self.disconnect(error)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 1306, in _connect
    raise err
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 1290, in _connect
    sock.connect(socket_address)
ConnectionRefusedError: [Errno 61] Connection refused

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/handlers/exception.py", line 55, in inner
    response = get_response(request)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/handlers/base.py", line 197, in _get_response
    response = wrapped_callback(request, *callback_args, **callback_kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/views/decorators/csrf.py", line 56, in wrapper_view
    return view_func(*args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/views/generic/base.py", line 104, in view
    return self.dispatch(request, *args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 515, in dispatch
    response = self.handle_exception(exc)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 475, in handle_exception
    self.raise_uncaught_exception(exc)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 486, in raise_uncaught_exception
    raise exc
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 503, in dispatch
    self.initial(request, *args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 422, in initial
    self.check_throttles(request)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 365, in check_throttles
    if not throttle.allow_request(request, self):
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/jwt_views.py", line 40, in allow_request
    return super().allow_request(request, view)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/throttling.py", line 123, in allow_request
    self.history = self.cache.get(self.key, [])
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/cache/backends/redis.py", line 187, in get
    return self._cache.get(key, default)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/cache/backends/redis.py", line 99, in get
    value = client.get(key)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/commands/core.py", line 1834, in get
    return self.execute_command("GET", name, keys=[name])
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/client.py", line 657, in execute_command
    return self._execute_command(*args, **options)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/client.py", line 663, in _execute_command
    conn = self.connection or pool.get_connection()
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/utils.py", line 196, in wrapper
    return func(*args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 2601, in get_connection
    connection.connect()
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 846, in connect
    self.connect_check_health(check_health=True)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 863, in connect_check_health
    raise ConnectionError(self._error_message(e))
redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
_________________________________________________________________________________________ TestLockEnforcedBeforePasswordValidation.test_lock_check_before_password _________________________________________________________________________________________
venv/lib/python3.9/site-packages/redis/connection.py:855: in connect_check_health
    sock = self.retry.call_with_retry(
venv/lib/python3.9/site-packages/redis/retry.py:116: in call_with_retry
    return do()
venv/lib/python3.9/site-packages/redis/connection.py:856: in <lambda>
    lambda: self._connect(), lambda error: self.disconnect(error)
venv/lib/python3.9/site-packages/redis/connection.py:1306: in _connect
    raise err
venv/lib/python3.9/site-packages/redis/connection.py:1290: in _connect
    sock.connect(socket_address)
E   ConnectionRefusedError: [Errno 61] Connection refused

During handling of the above exception, another exception occurred:
custom_auth/tests/test_spec001_login.py:136: in test_lock_check_before_password
    response = client.post(
venv/lib/python3.9/site-packages/rest_framework/test.py:299: in post
    response = super().post(
venv/lib/python3.9/site-packages/rest_framework/test.py:213: in post
    return self.generic('POST', path, data, content_type, **extra)
venv/lib/python3.9/site-packages/rest_framework/test.py:237: in generic
    return super().generic(
venv/lib/python3.9/site-packages/django/test/client.py:609: in generic
    return self.request(**r)
venv/lib/python3.9/site-packages/rest_framework/test.py:289: in request
    return super().request(**kwargs)
venv/lib/python3.9/site-packages/rest_framework/test.py:241: in request
    request = super().request(**kwargs)
venv/lib/python3.9/site-packages/django/test/client.py:891: in request
    self.check_exception(response)
venv/lib/python3.9/site-packages/django/test/client.py:738: in check_exception
    raise exc_value
venv/lib/python3.9/site-packages/django/core/handlers/exception.py:55: in inner
    response = get_response(request)
venv/lib/python3.9/site-packages/django/core/handlers/base.py:197: in _get_response
    response = wrapped_callback(request, *callback_args, **callback_kwargs)
venv/lib/python3.9/site-packages/django/views/decorators/csrf.py:56: in wrapper_view
    return view_func(*args, **kwargs)
venv/lib/python3.9/site-packages/django/views/generic/base.py:104: in view
    return self.dispatch(request, *args, **kwargs)
venv/lib/python3.9/site-packages/rest_framework/views.py:515: in dispatch
    response = self.handle_exception(exc)
venv/lib/python3.9/site-packages/rest_framework/views.py:475: in handle_exception
    self.raise_uncaught_exception(exc)
venv/lib/python3.9/site-packages/rest_framework/views.py:486: in raise_uncaught_exception
    raise exc
venv/lib/python3.9/site-packages/rest_framework/views.py:503: in dispatch
    self.initial(request, *args, **kwargs)
venv/lib/python3.9/site-packages/rest_framework/views.py:422: in initial
    self.check_throttles(request)
venv/lib/python3.9/site-packages/rest_framework/views.py:365: in check_throttles
    if not throttle.allow_request(request, self):
custom_auth/jwt_views.py:40: in allow_request
    return super().allow_request(request, view)
venv/lib/python3.9/site-packages/rest_framework/throttling.py:123: in allow_request
    self.history = self.cache.get(self.key, [])
venv/lib/python3.9/site-packages/django/core/cache/backends/redis.py:187: in get
    return self._cache.get(key, default)
venv/lib/python3.9/site-packages/django/core/cache/backends/redis.py:99: in get
    value = client.get(key)
venv/lib/python3.9/site-packages/redis/commands/core.py:1834: in get
    return self.execute_command("GET", name, keys=[name])
venv/lib/python3.9/site-packages/redis/client.py:657: in execute_command
    return self._execute_command(*args, **options)
venv/lib/python3.9/site-packages/redis/client.py:663: in _execute_command
    conn = self.connection or pool.get_connection()
venv/lib/python3.9/site-packages/redis/utils.py:196: in wrapper
    return func(*args, **kwargs)
venv/lib/python3.9/site-packages/redis/connection.py:2601: in get_connection
    connection.connect()
venv/lib/python3.9/site-packages/redis/connection.py:846: in connect
    self.connect_check_health(check_health=True)
venv/lib/python3.9/site-packages/redis/connection.py:863: in connect_check_health
    raise ConnectionError(self._error_message(e))
E   redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
------------------------------------------------------------------------------------------------------------------- Captured stderr call -------------------------------------------------------------------------------------------------------------------
Internal Server Error: /custom_auth/api/auth/login/
Traceback (most recent call last):
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 855, in connect_check_health
    sock = self.retry.call_with_retry(
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/retry.py", line 116, in call_with_retry
    return do()
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 856, in <lambda>
    lambda: self._connect(), lambda error: self.disconnect(error)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 1306, in _connect
    raise err
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 1290, in _connect
    sock.connect(socket_address)
ConnectionRefusedError: [Errno 61] Connection refused

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/handlers/exception.py", line 55, in inner
    response = get_response(request)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/handlers/base.py", line 197, in _get_response
    response = wrapped_callback(request, *callback_args, **callback_kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/views/decorators/csrf.py", line 56, in wrapper_view
    return view_func(*args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/views/generic/base.py", line 104, in view
    return self.dispatch(request, *args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 515, in dispatch
    response = self.handle_exception(exc)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 475, in handle_exception
    self.raise_uncaught_exception(exc)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 486, in raise_uncaught_exception
    raise exc
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 503, in dispatch
    self.initial(request, *args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 422, in initial
    self.check_throttles(request)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 365, in check_throttles
    if not throttle.allow_request(request, self):
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/jwt_views.py", line 40, in allow_request
    return super().allow_request(request, view)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/throttling.py", line 123, in allow_request
    self.history = self.cache.get(self.key, [])
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/cache/backends/redis.py", line 187, in get
    return self._cache.get(key, default)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/cache/backends/redis.py", line 99, in get
    value = client.get(key)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/commands/core.py", line 1834, in get
    return self.execute_command("GET", name, keys=[name])
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/client.py", line 657, in execute_command
    return self._execute_command(*args, **options)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/client.py", line 663, in _execute_command
    conn = self.connection or pool.get_connection()
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/utils.py", line 196, in wrapper
    return func(*args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 2601, in get_connection
    connection.connect()
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 846, in connect
    self.connect_check_health(check_health=True)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 863, in connect_check_health
    raise ConnectionError(self._error_message(e))
redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
-------------------------------------------------------------------------------------------------------------------- Captured log call ---------------------------------------------------------------------------------------------------------------------
ERROR    django.request:log.py:241 Internal Server Error: /custom_auth/api/auth/login/
Traceback (most recent call last):
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 855, in connect_check_health
    sock = self.retry.call_with_retry(
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/retry.py", line 116, in call_with_retry
    return do()
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 856, in <lambda>
    lambda: self._connect(), lambda error: self.disconnect(error)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 1306, in _connect
    raise err
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 1290, in _connect
    sock.connect(socket_address)
ConnectionRefusedError: [Errno 61] Connection refused

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/handlers/exception.py", line 55, in inner
    response = get_response(request)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/handlers/base.py", line 197, in _get_response
    response = wrapped_callback(request, *callback_args, **callback_kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/views/decorators/csrf.py", line 56, in wrapper_view
    return view_func(*args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/views/generic/base.py", line 104, in view
    return self.dispatch(request, *args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 515, in dispatch
    response = self.handle_exception(exc)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 475, in handle_exception
    self.raise_uncaught_exception(exc)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 486, in raise_uncaught_exception
    raise exc
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 503, in dispatch
    self.initial(request, *args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 422, in initial
    self.check_throttles(request)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 365, in check_throttles
    if not throttle.allow_request(request, self):
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/jwt_views.py", line 40, in allow_request
    return super().allow_request(request, view)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/throttling.py", line 123, in allow_request
    self.history = self.cache.get(self.key, [])
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/cache/backends/redis.py", line 187, in get
    return self._cache.get(key, default)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/cache/backends/redis.py", line 99, in get
    value = client.get(key)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/commands/core.py", line 1834, in get
    return self.execute_command("GET", name, keys=[name])
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/client.py", line 657, in execute_command
    return self._execute_command(*args, **options)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/client.py", line 663, in _execute_command
    conn = self.connection or pool.get_connection()
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/utils.py", line 196, in wrapper
    return func(*args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 2601, in get_connection
    connection.connect()
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 846, in connect
    self.connect_check_health(check_health=True)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 863, in connect_check_health
    raise ConnectionError(self._error_message(e))
redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
______________________________________________________________________________________ TestLockEnforcedBeforePasswordValidation.test_locked_user_sees_banned_message _______________________________________________________________________________________
venv/lib/python3.9/site-packages/redis/connection.py:855: in connect_check_health
    sock = self.retry.call_with_retry(
venv/lib/python3.9/site-packages/redis/retry.py:116: in call_with_retry
    return do()
venv/lib/python3.9/site-packages/redis/connection.py:856: in <lambda>
    lambda: self._connect(), lambda error: self.disconnect(error)
venv/lib/python3.9/site-packages/redis/connection.py:1306: in _connect
    raise err
venv/lib/python3.9/site-packages/redis/connection.py:1290: in _connect
    sock.connect(socket_address)
E   ConnectionRefusedError: [Errno 61] Connection refused

During handling of the above exception, another exception occurred:
custom_auth/tests/test_spec001_login.py:156: in test_locked_user_sees_banned_message
    response = client.post(
venv/lib/python3.9/site-packages/rest_framework/test.py:299: in post
    response = super().post(
venv/lib/python3.9/site-packages/rest_framework/test.py:213: in post
    return self.generic('POST', path, data, content_type, **extra)
venv/lib/python3.9/site-packages/rest_framework/test.py:237: in generic
    return super().generic(
venv/lib/python3.9/site-packages/django/test/client.py:609: in generic
    return self.request(**r)
venv/lib/python3.9/site-packages/rest_framework/test.py:289: in request
    return super().request(**kwargs)
venv/lib/python3.9/site-packages/rest_framework/test.py:241: in request
    request = super().request(**kwargs)
venv/lib/python3.9/site-packages/django/test/client.py:891: in request
    self.check_exception(response)
venv/lib/python3.9/site-packages/django/test/client.py:738: in check_exception
    raise exc_value
venv/lib/python3.9/site-packages/django/core/handlers/exception.py:55: in inner
    response = get_response(request)
venv/lib/python3.9/site-packages/django/core/handlers/base.py:197: in _get_response
    response = wrapped_callback(request, *callback_args, **callback_kwargs)
venv/lib/python3.9/site-packages/django/views/decorators/csrf.py:56: in wrapper_view
    return view_func(*args, **kwargs)
venv/lib/python3.9/site-packages/django/views/generic/base.py:104: in view
    return self.dispatch(request, *args, **kwargs)
venv/lib/python3.9/site-packages/rest_framework/views.py:515: in dispatch
    response = self.handle_exception(exc)
venv/lib/python3.9/site-packages/rest_framework/views.py:475: in handle_exception
    self.raise_uncaught_exception(exc)
venv/lib/python3.9/site-packages/rest_framework/views.py:486: in raise_uncaught_exception
    raise exc
venv/lib/python3.9/site-packages/rest_framework/views.py:503: in dispatch
    self.initial(request, *args, **kwargs)
venv/lib/python3.9/site-packages/rest_framework/views.py:422: in initial
    self.check_throttles(request)
venv/lib/python3.9/site-packages/rest_framework/views.py:365: in check_throttles
    if not throttle.allow_request(request, self):
custom_auth/jwt_views.py:40: in allow_request
    return super().allow_request(request, view)
venv/lib/python3.9/site-packages/rest_framework/throttling.py:123: in allow_request
    self.history = self.cache.get(self.key, [])
venv/lib/python3.9/site-packages/django/core/cache/backends/redis.py:187: in get
    return self._cache.get(key, default)
venv/lib/python3.9/site-packages/django/core/cache/backends/redis.py:99: in get
    value = client.get(key)
venv/lib/python3.9/site-packages/redis/commands/core.py:1834: in get
    return self.execute_command("GET", name, keys=[name])
venv/lib/python3.9/site-packages/redis/client.py:657: in execute_command
    return self._execute_command(*args, **options)
venv/lib/python3.9/site-packages/redis/client.py:663: in _execute_command
    conn = self.connection or pool.get_connection()
venv/lib/python3.9/site-packages/redis/utils.py:196: in wrapper
    return func(*args, **kwargs)
venv/lib/python3.9/site-packages/redis/connection.py:2601: in get_connection
    connection.connect()
venv/lib/python3.9/site-packages/redis/connection.py:846: in connect
    self.connect_check_health(check_health=True)
venv/lib/python3.9/site-packages/redis/connection.py:863: in connect_check_health
    raise ConnectionError(self._error_message(e))
E   redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
------------------------------------------------------------------------------------------------------------------- Captured stderr call -------------------------------------------------------------------------------------------------------------------
Internal Server Error: /custom_auth/api/auth/login/
Traceback (most recent call last):
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 855, in connect_check_health
    sock = self.retry.call_with_retry(
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/retry.py", line 116, in call_with_retry
    return do()
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 856, in <lambda>
    lambda: self._connect(), lambda error: self.disconnect(error)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 1306, in _connect
    raise err
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 1290, in _connect
    sock.connect(socket_address)
ConnectionRefusedError: [Errno 61] Connection refused

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/handlers/exception.py", line 55, in inner
    response = get_response(request)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/handlers/base.py", line 197, in _get_response
    response = wrapped_callback(request, *callback_args, **callback_kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/views/decorators/csrf.py", line 56, in wrapper_view
    return view_func(*args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/views/generic/base.py", line 104, in view
    return self.dispatch(request, *args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 515, in dispatch
    response = self.handle_exception(exc)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 475, in handle_exception
    self.raise_uncaught_exception(exc)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 486, in raise_uncaught_exception
    raise exc
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 503, in dispatch
    self.initial(request, *args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 422, in initial
    self.check_throttles(request)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 365, in check_throttles
    if not throttle.allow_request(request, self):
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/jwt_views.py", line 40, in allow_request
    return super().allow_request(request, view)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/throttling.py", line 123, in allow_request
    self.history = self.cache.get(self.key, [])
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/cache/backends/redis.py", line 187, in get
    return self._cache.get(key, default)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/cache/backends/redis.py", line 99, in get
    value = client.get(key)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/commands/core.py", line 1834, in get
    return self.execute_command("GET", name, keys=[name])
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/client.py", line 657, in execute_command
    return self._execute_command(*args, **options)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/client.py", line 663, in _execute_command
    conn = self.connection or pool.get_connection()
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/utils.py", line 196, in wrapper
    return func(*args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 2601, in get_connection
    connection.connect()
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 846, in connect
    self.connect_check_health(check_health=True)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 863, in connect_check_health
    raise ConnectionError(self._error_message(e))
redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
-------------------------------------------------------------------------------------------------------------------- Captured log call ---------------------------------------------------------------------------------------------------------------------
ERROR    django.request:log.py:241 Internal Server Error: /custom_auth/api/auth/login/
Traceback (most recent call last):
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 855, in connect_check_health
    sock = self.retry.call_with_retry(
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/retry.py", line 116, in call_with_retry
    return do()
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 856, in <lambda>
    lambda: self._connect(), lambda error: self.disconnect(error)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 1306, in _connect
    raise err
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 1290, in _connect
    sock.connect(socket_address)
ConnectionRefusedError: [Errno 61] Connection refused

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/handlers/exception.py", line 55, in inner
    response = get_response(request)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/handlers/base.py", line 197, in _get_response
    response = wrapped_callback(request, *callback_args, **callback_kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/views/decorators/csrf.py", line 56, in wrapper_view
    return view_func(*args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/views/generic/base.py", line 104, in view
    return self.dispatch(request, *args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 515, in dispatch
    response = self.handle_exception(exc)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 475, in handle_exception
    self.raise_uncaught_exception(exc)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 486, in raise_uncaught_exception
    raise exc
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 503, in dispatch
    self.initial(request, *args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 422, in initial
    self.check_throttles(request)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/views.py", line 365, in check_throttles
    if not throttle.allow_request(request, self):
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/jwt_views.py", line 40, in allow_request
    return super().allow_request(request, view)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/rest_framework/throttling.py", line 123, in allow_request
    self.history = self.cache.get(self.key, [])
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/cache/backends/redis.py", line 187, in get
    return self._cache.get(key, default)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/django/core/cache/backends/redis.py", line 99, in get
    value = client.get(key)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/commands/core.py", line 1834, in get
    return self.execute_command("GET", name, keys=[name])
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/client.py", line 657, in execute_command
    return self._execute_command(*args, **options)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/client.py", line 663, in _execute_command
    conn = self.connection or pool.get_connection()
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/utils.py", line 196, in wrapper
    return func(*args, **kwargs)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 2601, in get_connection
    connection.connect()
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 846, in connect
    self.connect_check_health(check_health=True)
  File "/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/redis/connection.py", line 863, in connect_check_health
    raise ConnectionError(self._error_message(e))
redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
______________________________________________________________________________________________ TestLoginResponseFields.test_login_accepts_email_and_password _______________________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_spec001_login.py:171: in test_login_accepts_email_and_password
    User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
_______________________________________________________________________________________________ TestLoginResponseFields.test_login_returns_user_state_fields _______________________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_spec001_login.py:186: in test_login_returns_user_state_fields
    user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
_________________________________________________________________________________________ TestRegistrationRequirements.test_email_used_for_login_not_verification __________________________________________________________________________________________
custom_auth/tests/test_spec001_login.py:227: in test_email_used_for_login_not_verification
    user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:16: in _create_user
    user = self.model(email=email, **extra_fields)
venv/lib/python3.9/site-packages/django/db/models/base.py:567: in __init__
    raise TypeError(
E   TypeError: User() got unexpected keyword arguments: 'mobile'
_________________________________________________________________________________________________ TestGuestStateDerivation.test_guest_state_allows_browse __________________________________________________________________________________________________
custom_auth/tests/test_spec001_user_state.py:27: in test_guest_state_allows_browse
    from custom_auth.services.lock_block import can_perform_action
E   ImportError: cannot import name 'can_perform_action' from 'custom_auth.services.lock_block' (/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/services/lock_block.py)
______________________________________________________________________________________________ TestGuestStateDerivation.test_guest_state_allows_view_product _______________________________________________________________________________________________
custom_auth/tests/test_spec001_user_state.py:32: in test_guest_state_allows_view_product
    from custom_auth.services.lock_block import can_perform_action
E   ImportError: cannot import name 'can_perform_action' from 'custom_auth.services.lock_block' (/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/services/lock_block.py)
_______________________________________________________________________________________________ TestGuestStateDerivation.test_guest_state_allows_add_to_cart _______________________________________________________________________________________________
custom_auth/tests/test_spec001_user_state.py:37: in test_guest_state_allows_add_to_cart
    from custom_auth.services.lock_block import can_perform_action
E   ImportError: cannot import name 'can_perform_action' from 'custom_auth.services.lock_block' (/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/services/lock_block.py)
_____________________________________________________________________________________ TestAuthenticatedUnverifiedStateDerivation.test_unverified_state_allows_browsing _____________________________________________________________________________________
custom_auth/tests/test_spec001_user_state.py:59: in test_unverified_state_allows_browsing
    from custom_auth.services.lock_block import can_perform_action
E   ImportError: cannot import name 'can_perform_action' from 'custom_auth.services.lock_block' (/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/services/lock_block.py)
_________________________________________________________________________________ TestAuthenticatedUnverifiedStateDerivation.test_unverified_state_allows_cart_management __________________________________________________________________________________
custom_auth/tests/test_spec001_user_state.py:68: in test_unverified_state_allows_cart_management
    from custom_auth.services.lock_block import can_perform_action
E   ImportError: cannot import name 'can_perform_action' from 'custom_auth.services.lock_block' (/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/services/lock_block.py)
_________________________________________________________________________________ TestAuthenticatedUnverifiedStateDerivation.test_unverified_state_allows_profile_viewing __________________________________________________________________________________
custom_auth/tests/test_spec001_user_state.py:77: in test_unverified_state_allows_profile_viewing
    from custom_auth.services.lock_block import can_perform_action
E   ImportError: cannot import name 'can_perform_action' from 'custom_auth.services.lock_block' (/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/services/lock_block.py)
_____________________________________________________________________________________ TestAuthenticatedUnverifiedStateDerivation.test_unverified_state_blocks_checkout _____________________________________________________________________________________
custom_auth/tests/test_spec001_user_state.py:86: in test_unverified_state_blocks_checkout
    from custom_auth.services.lock_block import can_perform_action
E   ImportError: cannot import name 'can_perform_action' from 'custom_auth.services.lock_block' (/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/services/lock_block.py)
_____________________________________________________________________________________ TestAuthenticatedUnverifiedStateDerivation.test_unverified_state_blocks_payment ______________________________________________________________________________________
custom_auth/tests/test_spec001_user_state.py:97: in test_unverified_state_blocks_payment
    from custom_auth.services.lock_block import can_perform_action
E   ImportError: cannot import name 'can_perform_action' from 'custom_auth.services.lock_block' (/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/services/lock_block.py)
__________________________________________________________________________________ TestAuthenticatedUnverifiedStateDerivation.test_unverified_state_blocks_order_creation __________________________________________________________________________________
custom_auth/tests/test_spec001_user_state.py:108: in test_unverified_state_blocks_order_creation
    from custom_auth.services.lock_block import can_perform_action
E   ImportError: cannot import name 'can_perform_action' from 'custom_auth.services.lock_block' (/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/services/lock_block.py)
_______________________________________________________________________________________ TestAuthenticatedVerifiedStateDerivation.test_verified_state_allows_checkout _______________________________________________________________________________________
custom_auth/tests/test_spec001_user_state.py:132: in test_verified_state_allows_checkout
    from custom_auth.services.lock_block import can_perform_action
E   ImportError: cannot import name 'can_perform_action' from 'custom_auth.services.lock_block' (/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/services/lock_block.py)
_______________________________________________________________________________________ TestAuthenticatedVerifiedStateDerivation.test_verified_state_allows_payment ________________________________________________________________________________________
custom_auth/tests/test_spec001_user_state.py:141: in test_verified_state_allows_payment
    from custom_auth.services.lock_block import can_perform_action
E   ImportError: cannot import name 'can_perform_action' from 'custom_auth.services.lock_block' (/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/services/lock_block.py)
____________________________________________________________________________________ TestAuthenticatedVerifiedStateDerivation.test_verified_state_allows_order_creation ____________________________________________________________________________________
custom_auth/tests/test_spec001_user_state.py:150: in test_verified_state_allows_order_creation
    from custom_auth.services.lock_block import can_perform_action
E   ImportError: cannot import name 'can_perform_action' from 'custom_auth.services.lock_block' (/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/services/lock_block.py)
_____________________________________________________________________________________ TestAuthenticatedVerifiedStateDerivation.test_verified_state_allows_wallet_usage _____________________________________________________________________________________
custom_auth/tests/test_spec001_user_state.py:159: in test_verified_state_allows_wallet_usage
    from custom_auth.services.lock_block import can_perform_action
E   ImportError: cannot import name 'can_perform_action' from 'custom_auth.services.lock_block' (/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/services/lock_block.py)
______________________________________________________________________________________________ TestLockedStateDerivation.test_locked_state_denies_all_access _______________________________________________________________________________________________
custom_auth/tests/test_spec001_user_state.py:179: in test_locked_state_denies_all_access
    from custom_auth.services.lock_block import can_perform_action
E   ImportError: cannot import name 'can_perform_action' from 'custom_auth.services.lock_block' (/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/services/lock_block.py)
____________________________________________________________________________________________ TestLockedStateDerivation.test_locked_state_overrides_verification ____________________________________________________________________________________________
custom_auth/tests/test_spec001_user_state.py:192: in test_locked_state_overrides_verification
    from custom_auth.services.lock_block import can_perform_action
E   ImportError: cannot import name 'can_perform_action' from 'custom_auth.services.lock_block' (/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/services/lock_block.py)
________________________________________________________________________________________________ TestBlockedStateDerivation.test_blocked_state_allows_login ________________________________________________________________________________________________
custom_auth/tests/test_spec001_user_state.py:215: in test_blocked_state_allows_login
    from custom_auth.services.lock_block import can_perform_action
E   ImportError: cannot import name 'can_perform_action' from 'custom_auth.services.lock_block' (/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/services/lock_block.py)
______________________________________________________________________________________________ TestBlockedStateDerivation.test_blocked_state_allows_browsing _______________________________________________________________________________________________
custom_auth/tests/test_spec001_user_state.py:223: in test_blocked_state_allows_browsing
    from custom_auth.services.lock_block import can_perform_action
E   ImportError: cannot import name 'can_perform_action' from 'custom_auth.services.lock_block' (/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/services/lock_block.py)
__________________________________________________________________________________________ TestBlockedStateDerivation.test_blocked_state_allows_customer_features __________________________________________________________________________________________
custom_auth/tests/test_spec001_user_state.py:231: in test_blocked_state_allows_customer_features
    from custom_auth.services.lock_block import can_perform_action
E   ImportError: cannot import name 'can_perform_action' from 'custom_auth.services.lock_block' (/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/services/lock_block.py)
_________________________________________________________________________________________ TestBlockedStateDerivation.test_blocked_state_blocks_specific_capability _________________________________________________________________________________________
custom_auth/tests/test_spec001_user_state.py:239: in test_blocked_state_blocks_specific_capability
    from custom_auth.services.lock_block import can_perform_action
E   ImportError: cannot import name 'can_perform_action' from 'custom_auth.services.lock_block' (/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/services/lock_block.py)
_______________________________________________________________________________________ TestBlockedStateDerivation.test_blocked_state_allows_unblocked_capabilities ________________________________________________________________________________________
custom_auth/tests/test_spec001_user_state.py:249: in test_blocked_state_allows_unblocked_capabilities
    from custom_auth.services.lock_block import can_perform_action
E   ImportError: cannot import name 'can_perform_action' from 'custom_auth.services.lock_block' (/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/services/lock_block.py)
______________________________________________________________________________________________ TestUserModelExtensions.test_blocked_capabilities_accepts_list ______________________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_user_model.py:29: in setUp
    self.user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
___________________________________________________________________________________________ TestUserModelExtensions.test_blocked_capabilities_can_be_empty_list ____________________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_user_model.py:29: in setUp
    self.user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
_____________________________________________________________________________________________ TestUserModelExtensions.test_can_increment_failed_login_attempts _____________________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_user_model.py:29: in setUp
    self.user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
_______________________________________________________________________________________________ TestUserModelExtensions.test_can_set_email_verified_to_true ________________________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_user_model.py:29: in setUp
    self.user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
_________________________________________________________________________________________________ TestUserModelExtensions.test_can_set_is_blocked_to_true __________________________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_user_model.py:29: in setUp
    self.user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
__________________________________________________________________________________________________ TestUserModelExtensions.test_can_set_is_locked_to_true __________________________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_user_model.py:29: in setUp
    self.user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
_____________________________________________________________________________________________ TestUserModelExtensions.test_can_set_is_mobile_verified_to_true ______________________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_user_model.py:29: in setUp
    self.user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
____________________________________________________________________________________________________ TestUserModelExtensions.test_can_set_locked_until _____________________________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_user_model.py:29: in setUp
    self.user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
_________________________________________________________________________________________ TestUserModelExtensions.test_default_blocked_capabilities_is_empty_list __________________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_user_model.py:29: in setUp
    self.user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
_______________________________________________________________________________________________ TestUserModelExtensions.test_default_blocked_reason_is_none ________________________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_user_model.py:29: in setUp
    self.user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
_______________________________________________________________________________________________ TestUserModelExtensions.test_default_email_verified_is_false _______________________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_user_model.py:29: in setUp
    self.user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
____________________________________________________________________________________________ TestUserModelExtensions.test_default_failed_login_attempts_is_zero ____________________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_user_model.py:29: in setUp
    self.user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
_________________________________________________________________________________________________ TestUserModelExtensions.test_default_is_blocked_is_false _________________________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_user_model.py:29: in setUp
    self.user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
_________________________________________________________________________________________________ TestUserModelExtensions.test_default_is_locked_is_false __________________________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_user_model.py:29: in setUp
    self.user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
_____________________________________________________________________________________________ TestUserModelExtensions.test_default_is_mobile_verified_is_false _____________________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_user_model.py:29: in setUp
    self.user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
__________________________________________________________________________________________________ TestUserModelExtensions.test_default_locked_at_is_none __________________________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_user_model.py:29: in setUp
    self.user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
________________________________________________________________________________________________ TestUserModelExtensions.test_default_locked_reason_is_none ________________________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_user_model.py:29: in setUp
    self.user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
________________________________________________________________________________________________ TestUserModelExtensions.test_default_locked_until_is_none _________________________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_user_model.py:29: in setUp
    self.user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
____________________________________________________________________________________________ TestUserModelExtensions.test_multiple_users_have_independent_state ____________________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_user_model.py:29: in setUp
    self.user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
__________________________________________________________________________________________ TestLoginUserState.test_login_returns_blocked_capabilities_in_response __________________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_user_state.py:26: in setUp
    self.user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
____________________________________________________________________________________________ TestLoginUserState.test_login_returns_correct_blocked_capabilities ____________________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_user_state.py:26: in setUp
    self.user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
___________________________________________________________________________________________ TestLoginUserState.test_login_returns_correct_mobile_verified_state ____________________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_user_state.py:26: in setUp
    self.user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
_______________________________________________________________________________________________ TestLoginUserState.test_login_returns_is_blocked_in_response _______________________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_user_state.py:26: in setUp
    self.user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
_______________________________________________________________________________________________ TestLoginUserState.test_login_returns_is_locked_in_response ________________________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_user_state.py:26: in setUp
    self.user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
___________________________________________________________________________________________ TestLoginUserState.test_login_returns_is_mobile_verified_in_response ___________________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_user_state.py:26: in setUp
    self.user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
___________________________________________________________________________________________ TestLoginUserState.test_login_with_blocked_capabilities_still_works ____________________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_user_state.py:26: in setUp
    self.user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
________________________________________________________________________________________________ TestLoginUserState.test_login_with_nonexistent_user_fails _________________________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_user_state.py:26: in setUp
    self.user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
_____________________________________________________________________________________________ TestLoginUserState.test_login_with_unverified_mobile_still_works _____________________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_user_state.py:26: in setUp
    self.user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
_________________________________________________________________________________________________ TestLoginUserState.test_login_with_wrong_password_fails __________________________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_user_state.py:26: in setUp
    self.user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
______________________________________________________________________________________________ TestLoginUserState.test_login_without_email_verification_fails ______________________________________________________________________________________________
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   pymysql.err.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")

The above exception was the direct cause of the following exception:
custom_auth/tests/test_user_state.py:26: in setUp
    self.user = User.objects.create_user(
custom_auth/models.py:24: in create_user
    return self._create_user(email, password, **extra_fields)
custom_auth/models.py:18: in _create_user
    user.save(using=self._db)
custom_auth/models.py:111: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/contrib/auth/base_user.py:76: in save
    super().save(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/base.py:814: in save
    self.save_base(
venv/lib/python3.9/site-packages/django/db/models/base.py:877: in save_base
    updated = self._save_table(
venv/lib/python3.9/site-packages/django/db/models/base.py:1020: in _save_table
    results = self._do_insert(
venv/lib/python3.9/site-packages/django/db/models/base.py:1061: in _do_insert
    return manager._insert(
venv/lib/python3.9/site-packages/django/db/models/manager.py:87: in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
venv/lib/python3.9/site-packages/django/db/models/query.py:1805: in _insert
    return query.get_compiler(using=using).execute_sql(returning_fields)
venv/lib/python3.9/site-packages/django/db/models/sql/compiler.py:1822: in execute_sql
    cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:102: in execute
    return super().execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:67: in execute
    return self._execute_with_wrappers(
venv/lib/python3.9/site-packages/django/db/backends/utils.py:80: in _execute_with_wrappers
    return executor(sql, params, many, context)
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/utils.py:91: in __exit__
    raise dj_exc_value.with_traceback(traceback) from exc_value
venv/lib/python3.9/site-packages/django/db/backends/utils.py:89: in _execute
    return self.cursor.execute(sql, params)
venv/lib/python3.9/site-packages/django/db/backends/mysql/base.py:75: in execute
    return self.cursor.execute(query, args)
venv/lib/python3.9/site-packages/pymysql/cursors.py:153: in execute
    result = self._query(query)
venv/lib/python3.9/site-packages/pymysql/cursors.py:322: in _query
    conn.query(q)
venv/lib/python3.9/site-packages/pymysql/connections.py:575: in query
    self._affected_rows = self._read_query_result(unbuffered=unbuffered)
venv/lib/python3.9/site-packages/pymysql/connections.py:826: in _read_query_result
    result.read()
venv/lib/python3.9/site-packages/pymysql/connections.py:1203: in read
    first_packet = self.connection._read_packet()
venv/lib/python3.9/site-packages/pymysql/connections.py:782: in _read_packet
    packet.raise_for_error()
venv/lib/python3.9/site-packages/pymysql/protocol.py:219: in raise_for_error
    err.raise_mysql_exception(self._data)
venv/lib/python3.9/site-packages/pymysql/err.py:150: in raise_mysql_exception
    raise errorclass(errno, errval)
E   django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
===================================================================================================================== warnings summary =====================================================================================================================
venv/lib/python3.9/site-packages/_pytest/config/__init__.py:1474
  /Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/venv/lib/python3.9/site-packages/_pytest/config/__init__.py:1474: PytestConfigWarning: Unknown config option: DJANGO_SETTINGS_MODULE
  
    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
================================================================================================================= short test summary info ==================================================================================================================
FAILED custom_auth/tests/test_spec001_capability.py::TestCapabilityBasedBlocking::test_sell_capability_blocked_for_seller - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_spec001_capability.py::TestCapabilityBasedBlocking::test_withdraw_capability_blocked - django.db.utils.IntegrityError: (1062, "Duplicate entry 'user@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_spec001_capability.py::TestCapabilityBasedBlocking::test_multiple_capabilities_blocked - django.db.utils.IntegrityError: (1062, "Duplicate entry 'user@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_spec001_capability.py::TestBlockDoesNotAffectUnrelatedFeatures::test_blocked_seller_can_browse - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_spec001_capability.py::TestBlockDoesNotAffectUnrelatedFeatures::test_blocked_seller_can_checkout - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_spec001_capability.py::TestBlockDoesNotAffectUnrelatedFeatures::test_blocked_seller_can_view_profile - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_spec001_capability.py::TestBlockDoesNotAffectUnrelatedFeatures::test_blocked_withdraw_can_still_sell - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_spec001_capability.py::TestGlobalLockEnforcement::test_locked_user_denied_all_capabilities - NameError: name 'can_perform_action' is not defined
FAILED custom_auth/tests/test_spec001_capability.py::TestGlobalLockEnforcement::test_locked_overrides_blocked_capabilities - django.db.utils.IntegrityError: (1062, "Duplicate entry 'user@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_spec001_capability.py::TestUnblockedCapabilities::test_unblocked_user_can_sell - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_spec001_capability.py::TestUnblockedCapabilities::test_unblocked_user_can_withdraw - django.db.utils.IntegrityError: (1062, "Duplicate entry 'user@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_spec001_capability.py::TestUnblockedCapabilities::test_no_blocked_capabilities_allows_all - django.db.utils.IntegrityError: (1062, "Duplicate entry 'user@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_spec001_login.py::TestLoginAllowsUnverifiedUsers::test_login_succeeds_for_unverified_mobile_user - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_spec001_login.py::TestLoginAllowsUnverifiedUsers::test_login_does_not_check_mobile_verification - django.db.utils.IntegrityError: (1062, "Duplicate entry 'user@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_spec001_login.py::TestLoginBlocksOnlyLockedUsers::test_login_fails_for_locked_user - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_spec001_login.py::TestLoginBlocksOnlyLockedUsers::test_login_succeeds_for_blocked_user - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_spec001_login.py::TestLoginBlocksOnlyLockedUsers::test_login_succeeds_for_verified_user - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_spec001_login.py::TestLockEnforcedBeforePasswordValidation::test_lock_check_before_password - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_spec001_login.py::TestLockEnforcedBeforePasswordValidation::test_locked_user_sees_banned_message - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_spec001_login.py::TestLoginResponseFields::test_login_accepts_email_and_password - django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_spec001_login.py::TestLoginResponseFields::test_login_returns_user_state_fields - django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_spec001_login.py::TestRegistrationRequirements::test_email_used_for_login_not_verification - TypeError: User() got unexpected keyword arguments: 'mobile'
FAILED custom_auth/tests/test_spec001_user_state.py::TestGuestStateDerivation::test_guest_state_allows_browse - ImportError: cannot import name 'can_perform_action' from 'custom_auth.services.lock_block' (/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/services/lock_block.py)
FAILED custom_auth/tests/test_spec001_user_state.py::TestGuestStateDerivation::test_guest_state_allows_view_product - ImportError: cannot import name 'can_perform_action' from 'custom_auth.services.lock_block' (/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/services/lock_block.py)
FAILED custom_auth/tests/test_spec001_user_state.py::TestGuestStateDerivation::test_guest_state_allows_add_to_cart - ImportError: cannot import name 'can_perform_action' from 'custom_auth.services.lock_block' (/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/services/lock_block.py)
FAILED custom_auth/tests/test_spec001_user_state.py::TestAuthenticatedUnverifiedStateDerivation::test_unverified_state_allows_browsing - ImportError: cannot import name 'can_perform_action' from 'custom_auth.services.lock_block' (/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/services/lock_block.py)
FAILED custom_auth/tests/test_spec001_user_state.py::TestAuthenticatedUnverifiedStateDerivation::test_unverified_state_allows_cart_management - ImportError: cannot import name 'can_perform_action' from 'custom_auth.services.lock_block' (/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/services/lock_block.py)
FAILED custom_auth/tests/test_spec001_user_state.py::TestAuthenticatedUnverifiedStateDerivation::test_unverified_state_allows_profile_viewing - ImportError: cannot import name 'can_perform_action' from 'custom_auth.services.lock_block' (/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/services/lock_block.py)
FAILED custom_auth/tests/test_spec001_user_state.py::TestAuthenticatedUnverifiedStateDerivation::test_unverified_state_blocks_checkout - ImportError: cannot import name 'can_perform_action' from 'custom_auth.services.lock_block' (/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/services/lock_block.py)
FAILED custom_auth/tests/test_spec001_user_state.py::TestAuthenticatedUnverifiedStateDerivation::test_unverified_state_blocks_payment - ImportError: cannot import name 'can_perform_action' from 'custom_auth.services.lock_block' (/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/services/lock_block.py)
FAILED custom_auth/tests/test_spec001_user_state.py::TestAuthenticatedUnverifiedStateDerivation::test_unverified_state_blocks_order_creation - ImportError: cannot import name 'can_perform_action' from 'custom_auth.services.lock_block' (/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/services/lock_block.py)
FAILED custom_auth/tests/test_spec001_user_state.py::TestAuthenticatedVerifiedStateDerivation::test_verified_state_allows_checkout - ImportError: cannot import name 'can_perform_action' from 'custom_auth.services.lock_block' (/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/services/lock_block.py)
FAILED custom_auth/tests/test_spec001_user_state.py::TestAuthenticatedVerifiedStateDerivation::test_verified_state_allows_payment - ImportError: cannot import name 'can_perform_action' from 'custom_auth.services.lock_block' (/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/services/lock_block.py)
FAILED custom_auth/tests/test_spec001_user_state.py::TestAuthenticatedVerifiedStateDerivation::test_verified_state_allows_order_creation - ImportError: cannot import name 'can_perform_action' from 'custom_auth.services.lock_block' (/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/services/lock_block.py)
FAILED custom_auth/tests/test_spec001_user_state.py::TestAuthenticatedVerifiedStateDerivation::test_verified_state_allows_wallet_usage - ImportError: cannot import name 'can_perform_action' from 'custom_auth.services.lock_block' (/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/services/lock_block.py)
FAILED custom_auth/tests/test_spec001_user_state.py::TestLockedStateDerivation::test_locked_state_denies_all_access - ImportError: cannot import name 'can_perform_action' from 'custom_auth.services.lock_block' (/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/services/lock_block.py)
FAILED custom_auth/tests/test_spec001_user_state.py::TestLockedStateDerivation::test_locked_state_overrides_verification - ImportError: cannot import name 'can_perform_action' from 'custom_auth.services.lock_block' (/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/services/lock_block.py)
FAILED custom_auth/tests/test_spec001_user_state.py::TestBlockedStateDerivation::test_blocked_state_allows_login - ImportError: cannot import name 'can_perform_action' from 'custom_auth.services.lock_block' (/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/services/lock_block.py)
FAILED custom_auth/tests/test_spec001_user_state.py::TestBlockedStateDerivation::test_blocked_state_allows_browsing - ImportError: cannot import name 'can_perform_action' from 'custom_auth.services.lock_block' (/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/services/lock_block.py)
FAILED custom_auth/tests/test_spec001_user_state.py::TestBlockedStateDerivation::test_blocked_state_allows_customer_features - ImportError: cannot import name 'can_perform_action' from 'custom_auth.services.lock_block' (/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/services/lock_block.py)
FAILED custom_auth/tests/test_spec001_user_state.py::TestBlockedStateDerivation::test_blocked_state_blocks_specific_capability - ImportError: cannot import name 'can_perform_action' from 'custom_auth.services.lock_block' (/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/services/lock_block.py)
FAILED custom_auth/tests/test_spec001_user_state.py::TestBlockedStateDerivation::test_blocked_state_allows_unblocked_capabilities - ImportError: cannot import name 'can_perform_action' from 'custom_auth.services.lock_block' (/Users/momen/untitled folder/To7fa/TO7FAA/to7fabackend/custom_auth/services/lock_block.py)
FAILED custom_auth/tests/test_user_model.py::TestUserModelExtensions::test_blocked_capabilities_accepts_list - django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_user_model.py::TestUserModelExtensions::test_blocked_capabilities_can_be_empty_list - django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_user_model.py::TestUserModelExtensions::test_can_increment_failed_login_attempts - django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_user_model.py::TestUserModelExtensions::test_can_set_email_verified_to_true - django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_user_model.py::TestUserModelExtensions::test_can_set_is_blocked_to_true - django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_user_model.py::TestUserModelExtensions::test_can_set_is_locked_to_true - django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_user_model.py::TestUserModelExtensions::test_can_set_is_mobile_verified_to_true - django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_user_model.py::TestUserModelExtensions::test_can_set_locked_until - django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_user_model.py::TestUserModelExtensions::test_default_blocked_capabilities_is_empty_list - django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_user_model.py::TestUserModelExtensions::test_default_blocked_reason_is_none - django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_user_model.py::TestUserModelExtensions::test_default_email_verified_is_false - django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_user_model.py::TestUserModelExtensions::test_default_failed_login_attempts_is_zero - django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_user_model.py::TestUserModelExtensions::test_default_is_blocked_is_false - django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_user_model.py::TestUserModelExtensions::test_default_is_locked_is_false - django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_user_model.py::TestUserModelExtensions::test_default_is_mobile_verified_is_false - django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_user_model.py::TestUserModelExtensions::test_default_locked_at_is_none - django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_user_model.py::TestUserModelExtensions::test_default_locked_reason_is_none - django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_user_model.py::TestUserModelExtensions::test_default_locked_until_is_none - django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_user_model.py::TestUserModelExtensions::test_multiple_users_have_independent_state - django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_returns_blocked_capabilities_in_response - django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_returns_correct_blocked_capabilities - django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_returns_correct_mobile_verified_state - django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_returns_is_blocked_in_response - django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_returns_is_locked_in_response - django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_returns_is_mobile_verified_in_response - django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_with_blocked_capabilities_still_works - django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_with_nonexistent_user_fails - django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_with_unverified_mobile_still_works - django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_with_wrong_password_fails - django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
FAILED custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_without_email_verification_fails - django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
================================================================================================== 72 failed, 23 passed, 28 skipped, 1 warning in 25.29s ===================================================================================================
(venv) momen@Momens-Mac-mini to7fabackend % 