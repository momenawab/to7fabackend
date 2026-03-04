When i run this tests pytest --cov=products 
i got this faileds :
====================================================================================================================== tests coverage ======================================================================================================================
_____________________________________________________________________________________________________ coverage: platform darwin, python 3.9.6-final-0 ______________________________________________________________________________________________________

Name                                                   Stmts   Miss  Cover
--------------------------------------------------------------------------
products/__init__.py                                       0      0   100%
products/admin.py                                        504    201    60%
products/apps.py                                           4      0   100%
products/ar_models.py                                     88     31    65%
products/ar_serializers.py                                69     31    55%
products/ar_urls.py                                        3      0   100%
products/ar_views.py                                     107     72    33%
products/migrations/0001_initial.py                        8      8     0%
products/migrations/0002_add_approval_index.py             4      4     0%
products/migrations/0003_add_variant_option_index.py       4      4     0%
products/migrations/__init__.py                            0      0   100%
products/models.py                                       593    167    72%
products/renderers.py                                     16     16     0%
products/serializers.py                                  197     48    76%
products/tests.py                                          1      1     0%
products/tests/__init__.py                                 0      0   100%
products/tests/test_invariants.py                         64     17    73%
products/urls.py                                           3      0   100%
products/views.py                                        975    793    19%
--------------------------------------------------------------------------
TOTAL                                                   2640   1393    47%
================================================================================================================= short test summary info ==================================================================================================================
FAILED custom_auth/tests/test_spec001_login.py::TestLoginAllowsUnverifiedUsers::test_login_succeeds_for_unverified_mobile_user - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_spec001_login.py::TestLoginAllowsUnverifiedUsers::test_login_does_not_check_mobile_verification - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_spec001_login.py::TestLoginBlocksOnlyLockedUsers::test_login_fails_for_locked_user - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_spec001_login.py::TestLoginBlocksOnlyLockedUsers::test_login_succeeds_for_blocked_user - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_spec001_login.py::TestLoginBlocksOnlyLockedUsers::test_login_succeeds_for_verified_user - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_spec001_login.py::TestLockEnforcedBeforePasswordValidation::test_lock_check_before_password - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_spec001_login.py::TestLockEnforcedBeforePasswordValidation::test_locked_user_sees_banned_message - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_spec001_login.py::TestLoginResponseFields::test_login_accepts_email_and_password - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_spec001_login.py::TestLoginResponseFields::test_login_returns_user_state_fields - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_spec001_login.py::TestRegistrationRequirements::test_email_used_for_login_not_verification - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_returns_blocked_capabilities_in_response - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_returns_correct_blocked_capabilities - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_returns_correct_mobile_verified_state - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_returns_is_blocked_in_response - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_returns_is_locked_in_response - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_returns_is_mobile_verified_in_response - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_with_blocked_capabilities_still_works - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_with_nonexistent_user_fails - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_with_unverified_mobile_still_works - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_with_wrong_password_fails - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_without_email_verification_fails - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED cart/tests/test_cart.py::TestGuestCartOperations::test_add_item_to_guest_cart_via_api - AssertionError: 400 != 200
FAILED cart/tests/test_invariants.py::TestCartInvariants::test_inv_017_cart_item_variant_id_is_null_or_valid_product_category_variant_option - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller@test.com' for key 'custom_auth_user.email'")
FAILED cart/tests/test_invariants.py::TestCartInvariants::test_inv_018_cart_item_cannot_reference_inactive_variant - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller2@test.com' for key 'custom_auth_user.email'")
FAILED cart/tests/test_invariants.py::TestCartInvariants::test_inv_019_cart_item_cannot_reference_zero_stock_variant - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller3@test.com' for key 'custom_auth_user.email'")
FAILED cart/tests/test_spec001_cart.py::TestGuestCartSessionBased::test_guest_cart_created_with_session_id - cart.models.Cart.DoesNotExist: Cart matching query does not exist.
FAILED cart/tests/test_spec001_cart.py::TestCartMergeOnLogin::test_cart_merge_triggered_on_login - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED cart/tests/test_spec001_cart.py::TestCartMergeOnLogin::test_cart_merge_preserves_all_guest_items - TypeError: Direct assignment to the reverse side of a related set is prohibited. Use items.set() instead.
FAILED cart/tests/test_spec001_cart.py::TestCartMergeOnLogin::test_user_cart_quantity_wins_on_conflict - TypeError: Direct assignment to the reverse side of a related set is prohibited. Use items.set() instead.
FAILED cart/tests/test_spec001_cart.py::TestCartMergeOnLogin::test_guest_only_items_added_to_user_cart - TypeError: Direct assignment to the reverse side of a related set is prohibited. Use items.set() instead.
FAILED cart/tests/test_spec001_cart.py::TestCartMergeOnLogin::test_guest_cart_removed_after_merge - TypeError: merge_guest_cart() takes 2 positional arguments but 3 were given
FAILED cart/tests/test_spec001_cart.py::TestCheckoutVerificationRequirement::test_checkout_requires_authentication - assert 404 == 401
FAILED cart/tests/test_spec001_cart.py::TestCheckoutVerificationRequirement::test_checkout_requires_mobile_verification - assert 404 == 403
FAILED cart/tests/test_spec001_cart.py::TestCheckoutVerificationRequirement::test_checkout_triggers_otp_for_unverified - ValueError: Content-Type header is "text/html; charset=utf-8", not "application/json"
FAILED cart/tests/test_spec001_cart.py::TestCheckoutVerificationRequirement::test_checkout_proceeds_for_verified_user - TypeError: Direct assignment to the reverse side of a related set is prohibited. Use items.set() instead.
FAILED orders/tests/test_checkout.py::CheckoutVerificationTests::test_unverified_user_blocked_from_checkout - AssertionError: 404 != 403
FAILED orders/tests/test_checkout.py::CheckoutVerificationTests::test_verified_user_can_checkout - AssertionError: 404 not found in [200, 201]
FAILED orders/tests/test_cod_flow.py::TestCODOrderCreation::test_cod_order_creates_with_cod_pending_status - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_cod_flow.py::TestCODOrderCreation::test_non_cod_order_creates_with_pending_payment_status - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_cod_flow.py::TestCODLifecycle::test_cod_transition_to_processing - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_cod_flow.py::TestCODLifecycle::test_cod_transition_to_shipped - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_cod_flow.py::TestCODLifecycle::test_cod_transition_to_delivered - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_cod_flow.py::TestCODLifecycle::test_cod_transition_to_completed - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_cod_flow.py::TestCODLifecycle::test_cod_full_lifecycle - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_cod_flow.py::TestCODCancellation::test_cod_order_can_be_cancelled - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_cod_flow.py::TestCODCancellation::test_cod_order_cannot_be_cancelled_after_shipped - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_cod_flow.py::TestCODCancellation::test_cod_cancellation_from_processing - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_cod_flow.py::TestCODCancellation::test_cod_cancellation_does_not_require_refund - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_invariants.py::TestStockInvariants::test_inv_001_stock_only_mutated_via_stock_lock_manager_in_atomic_blocks - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller@test.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_invariants.py::TestStockInvariants::test_inv_002_stock_checks_after_select_for_update_lock - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller2@test.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_invariants.py::TestStockInvariants::test_inv_003_cancelled_order_restores_stock_to_exact_variant - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller3@test.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_invariants.py::TestStockInvariants::test_inv_004_stock_never_goes_negative - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller4@test.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_invariants.py::TestStockInvariants::test_inv_005_product_stock_quantity_not_used_for_variant_products - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller5@test.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_invariants.py::TestOrderInvariants::test_inv_006_order_item_always_has_valid_product_id - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller6@test.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_invariants.py::TestOrderInvariants::test_inv_007_order_item_variant_id_is_null_or_valid_product_category_variant_option_id - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller7@test.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_invariants.py::TestOrderInvariants::test_inv_008_reservation_status_transitions_follow_rules - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller8@test.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_invariants.py::TestOrderInvariants::test_inv_009_order_with_released_item_cannot_transition_to_paid - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller9@test.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_payment_timeout.py::TestPaymentTimeoutCalculation::test_wallet_order_has_payment_timeout - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_payment_timeout.py::TestPaymentTimeoutCalculation::test_instapay_order_has_payment_timeout - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_payment_timeout.py::TestPaymentTimeoutCalculation::test_credit_card_order_has_payment_timeout - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_payment_timeout.py::TestPaymentTimeoutCalculation::test_cod_order_has_no_payment_timeout - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_payment_timeout.py::TestTimeoutTaskCancelsExpiredOrders::test_timeout_task_cancels_expired_order - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_payment_timeout.py::TestTimeoutTaskCancelsExpiredOrders::test_timeout_task_does_not_cancel_future_orders - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_payment_timeout.py::TestTimeoutTaskCancelsExpiredOrders::test_timeout_task_skips_non_pending_orders - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_payment_timeout.py::TestTimeoutTaskCancelsExpiredOrders::test_timeout_task_handles_multiple_expired_orders - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_payment_timeout.py::TestStockReleaseOnTimeoutCancellation::test_timeout_cancellation_releases_stock - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_payment_timeout.py::TestStockReleaseOnTimeoutCancellation::test_timeout_cancellation_updates_reservation_status - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_payment_timeout.py::TestWalletHoldReleaseOnTimeoutCancellation::test_timeout_cancellation_releases_wallet_hold - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_payment_timeout.py::TestWalletHoldReleaseOnTimeoutCancellation::test_timeout_cancellation_creates_refund_transaction - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_payment_timeout.py::TestWalletHoldReleaseOnTimeoutCancellation::test_timeout_cancellation_for_non_wallet_orders - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_refund.py::TestRefundFlow::test_refund_transitions_order_to_refunded_state - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_refund.py::TestRefundFlow::test_wallet_credit_on_refund - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_refund.py::TestRefundFlow::test_stock_release_on_refund - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_refund.py::TestRefundFlow::test_refund_prevention_on_unpaid_orders - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_refund.py::TestRefundFlow::test_refund_prevention_on_cod_orders - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_refund.py::TestRefundFlow::test_refund_from_delivered_state - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_refund.py::TestRefundFlow::test_refund_idempotency - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_refund.py::TestRefundFlow::test_refund_from_processing_state - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_refund.py::TestRefundFlow::test_refund_from_shipped_state - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_spec002_cancellation.py::TestCancellationEligibility::test_customer_cannot_cancel_shipped_order - assert 400 in [200, 201, 403]
FAILED orders/tests/test_spec002_cancellation.py::TestCancellationEligibility::test_seller_cannot_cancel_order - assert 400 in [403, 404, 405]
FAILED orders/tests/test_spec002_cancellation.py::TestCancellationEligibility::test_admin_can_cancel_any_order - assert 400 in [200, 201, 403, 405]
FAILED orders/tests/test_spec002_cancellation.py::TestPartialCancellationPolicy::test_partial_cancellation_not_supported - assert 405 in [400, 200, 201]
FAILED orders/tests/test_spec002_cancellation.py::TestRefundTiming::test_wallet_refund_processed_immediately - django.db.utils.IntegrityError: (1062, "Duplicate entry '5626' for key 'wallet_wallet.user_id'")
FAILED orders/tests/test_spec002_cancellation.py::TestRefundTiming::test_refund_completion_triggers_refunded_state - django.db.utils.IntegrityError: (1062, "Duplicate entry '5627' for key 'wallet_wallet.user_id'")
FAILED orders/tests/test_spec002_cancellation.py::TestRefundTiming::test_failed_refund_does_not_change_order_state - django.db.utils.IntegrityError: (1062, "Duplicate entry '5628' for key 'wallet_wallet.user_id'")
FAILED orders/tests/test_spec002_idempotency.py::TestOrderCreationIdempotency::test_duplicate_order_request_returns_existing_order - AssertionError: Expected a `Response`, `HttpResponse` or `StreamingHttpResponse` to be returned from the view, but received a `<class 'tuple'>`
FAILED orders/tests/test_spec002_idempotency.py::TestOrderCreationIdempotency::test_idempotency_key_based_on_user_and_cart - AssertionError: Expected a `Response`, `HttpResponse` or `StreamingHttpResponse` to be returned from the view, but received a `<class 'tuple'>`
FAILED orders/tests/test_spec002_idempotency.py::TestOrderCreationIdempotency::test_idempotency_window_at_least_60_seconds - AssertionError: Expected a `Response`, `HttpResponse` or `StreamingHttpResponse` to be returned from the view, but received a `<class 'tuple'>`
FAILED orders/tests/test_spec002_inventory.py::TestStockReservationRules::test_stock_reserved_on_order_creation - django.db.utils.IntegrityError: (1048, "Column 'seller_id' cannot be null")
FAILED orders/tests/test_spec002_inventory.py::TestStockReservationRules::test_stock_reservation_specific_to_variant - TypeError: ProductVariant() got unexpected keyword arguments: 'stock_quantity'
FAILED orders/tests/test_spec002_inventory.py::TestStockReservationRules::test_reserved_stock_decremented_from_available_not_total - django.db.utils.IntegrityError: (1048, "Column 'category_id' cannot be null")
FAILED orders/tests/test_spec002_inventory.py::TestVariantSpecificStockHandling::test_each_variant_has_independent_stock - TypeError: ProductVariant() got unexpected keyword arguments: 'stock_quantity'
FAILED orders/tests/test_spec002_inventory.py::TestVariantSpecificStockHandling::test_stock_reservation_references_variant_id - TypeError: ProductVariant() got unexpected keyword arguments: 'stock_quantity'
FAILED orders/tests/test_spec002_inventory.py::TestVariantSpecificStockHandling::test_order_line_item_stores_variant_id - TypeError: ProductVariant() got unexpected keyword arguments: 'stock_quantity'
FAILED orders/tests/test_spec002_inventory.py::TestOrderDataForStockRelease::test_order_item_contains_sufficient_data - TypeError: ProductVariant() got unexpected keyword arguments: 'stock_quantity'
FAILED orders/tests/test_spec002_inventory.py::TestOrderDataForStockRelease::test_stock_release_uses_historical_snapshot - django.db.utils.IntegrityError: (1048, "Column 'seller_id' cannot be null")
FAILED orders/tests/test_spec002_order_creation.py::TestOrderCreationPreconditions::test_order_creation_requires_mobile_verification - AssertionError: Expected a `Response`, `HttpResponse` or `StreamingHttpResponse` to be returned from the view, but received a `<class 'tuple'>`
FAILED orders/tests/test_spec002_order_creation.py::TestOrderCreationPreconditions::test_order_creation_allows_verified_user - AssertionError: Expected a `Response`, `HttpResponse` or `StreamingHttpResponse` to be returned from the view, but received a `<class 'tuple'>`
FAILED orders/tests/test_spec002_order_creation.py::TestOrderCreationPreconditions::test_order_creation_blocks_locked_users - AssertionError: Expected a `Response`, `HttpResponse` or `StreamingHttpResponse` to be returned from the view, but received a `<class 'tuple'>`
FAILED orders/tests/test_spec002_order_creation.py::TestOrderCreationPreconditions::test_order_creation_requires_nonempty_cart - AssertionError: Expected a `Response`, `HttpResponse` or `StreamingHttpResponse` to be returned from the view, but received a `<class 'tuple'>`
FAILED orders/tests/test_spec002_order_creation.py::TestOrderCreationPreconditions::test_order_creation_validates_stock_availability - ValueError: Not enough stock available. Only 0 items left.
FAILED orders/tests/test_spec002_order_creation.py::TestIdempotencyBehavior::test_duplicate_order_request_returns_existing_order - AssertionError: Expected a `Response`, `HttpResponse` or `StreamingHttpResponse` to be returned from the view, but received a `<class 'tuple'>`
FAILED orders/tests/test_spec002_order_creation.py::TestPartialFailureHandling::test_stock_reservation_failure_rolls_back_all - ValueError: Not enough stock available. Only 0 items left.
FAILED orders/tests/test_spec002_order_creation.py::TestPartialFailureHandling::test_payment_failure_releases_stock - AssertionError: Expected a `Response`, `HttpResponse` or `StreamingHttpResponse` to be returned from the view, but received a `<class 'tuple'>`
FAILED orders/tests/test_spec002_order_creation.py::TestPartialFailureHandling::test_order_creation_error_indicates_failed_item - ValueError: Not enough stock available. Only 0 items left.
FAILED orders/tests/test_spec002_payment.py::TestWalletPaymentRules::test_wallet_balance_verified_before_payment - django.db.utils.IntegrityError: (1062, "Duplicate entry '5686' for key 'wallet_wallet.user_id'")
FAILED orders/tests/test_spec002_payment.py::TestWalletPaymentRules::test_wallet_balance_held_on_payment_initiation - django.db.utils.IntegrityError: (1062, "Duplicate entry '5687' for key 'wallet_wallet.user_id'")
FAILED orders/tests/test_spec002_payment.py::TestWalletPaymentRules::test_wallet_hold_converted_to_debit_on_payment - django.db.utils.IntegrityError: (1062, "Duplicate entry '5688' for key 'wallet_wallet.user_id'")
FAILED orders/tests/test_spec002_payment.py::TestWalletPaymentRules::test_wallet_hold_released_on_cancellation - django.db.utils.IntegrityError: (1062, "Duplicate entry '5689' for key 'wallet_wallet.user_id'")
FAILED orders/tests/test_spec002_payment.py::TestWalletPaymentRules::test_wallet_transaction_has_order_reference - django.db.utils.IntegrityError: (1062, "Duplicate entry '5690' for key 'wallet_wallet.user_id'")
FAILED orders/tests/test_spec002_payment.py::TestOrderPaymentStateCoordination::test_order_state_matches_payment_state - django.db.utils.IntegrityError: (1062, "Duplicate entry '5691' for key 'wallet_wallet.user_id'")
FAILED orders/tests/test_spec002_payment.py::TestPendingPaymentTimeout::test_pending_payment_has_15_minute_timeout - assert None is not None
FAILED orders/tests/test_spec002_payment.py::TestPaymentStateTransitions::test_paid_order_has_captured_payment - django.db.utils.IntegrityError: (1062, "Duplicate entry '5696' for key 'wallet_wallet.user_id'")
FAILED orders/tests/test_spec002_payment.py::TestPaymentStateTransitions::test_refunded_order_has_refunded_payment - django.db.utils.IntegrityError: (1062, "Duplicate entry '5697' for key 'wallet_wallet.user_id'")
FAILED orders/tests/test_views.py::OrderLifecycleTests::test_acknowledge_order_by_non_seller_fails - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_views.py::OrderLifecycleTests::test_acknowledge_order_by_seller - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_views.py::OrderLifecycleTests::test_acknowledge_order_invalid_state - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_views.py::OrderLifecycleTests::test_complete_order - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_views.py::OrderLifecycleTests::test_complete_order_invalid_state - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_views.py::OrderLifecycleTests::test_deliver_order - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_views.py::OrderLifecycleTests::test_deliver_order_invalid_state - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_views.py::OrderLifecycleTests::test_refund_order_by_admin - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_views.py::OrderLifecycleTests::test_refund_order_by_non_admin_fails - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_views.py::OrderLifecycleTests::test_refund_order_invalid_state - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_views.py::OrderLifecycleTests::test_ship_order_by_non_seller_fails - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_views.py::OrderLifecycleTests::test_ship_order_by_seller - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_views.py::OrderStatesEndpointTests::test_order_states_endpoint - django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
FAILED wallet/tests/test_spec002_wallet.py::TestWalletRefundBehavior::test_refund_credits_wallet - AssertionError: assert Decimal('100.00') > Decimal('100.00')
FAILED products/tests/test_invariants.py::TestVariantSystemInvariants::test_inv_015_new_products_use_product_category_variant_option - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller2@test.com' for key 'custom_auth_user.email'")
FAILED products/tests/test_invariants.py::TestVisibilityInvariants::test_inv_010_unapproved_products_not_in_public_listings - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller4@test.com' for key 'custom_auth_user.email'")
FAILED products/tests/test_invariants.py::TestVisibilityInvariants::test_inv_011_unapproved_products_cannot_be_added_to_cart - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller5@test.com' for key 'custom_auth_user.email'")
FAILED products/tests/test_invariants.py::TestVisibilityInvariants::test_inv_012_unapproved_products_cannot_be_in_orders - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller6@test.com' for key 'custom_auth_user.email'")
FAILED products/tests/test_invariants.py::TestVisibilityInvariants::test_inv_013_approval_requires_is_active_true - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller7@test.com' for key 'custom_auth_user.email'")
ERROR orders/tests/test_multi_seller.py::TestPerItemStatusTracking::test_initial_item_status_is_pending - django.db.utils.IntegrityError: (1048, "Column 'category_id' cannot be null")
ERROR orders/tests/test_multi_seller.py::TestPerItemStatusTracking::test_item_status_independent_of_other_items - django.db.utils.IntegrityError: (1048, "Column 'category_id' cannot be null")
ERROR orders/tests/test_multi_seller.py::TestOrderStatusAggregation::test_all_shipped_aggregates_to_shipped - django.db.utils.IntegrityError: (1048, "Column 'category_id' cannot be null")
ERROR orders/tests/test_multi_seller.py::TestOrderStatusAggregation::test_all_delivered_aggregates_to_delivered - django.db.utils.IntegrityError: (1048, "Column 'category_id' cannot be null")
ERROR orders/tests/test_multi_seller.py::TestOrderStatusAggregation::test_all_completed_aggregates_to_completed - django.db.utils.IntegrityError: (1048, "Column 'category_id' cannot be null")
ERROR orders/tests/test_multi_seller.py::TestOrderStatusAggregation::test_all_cancelled_aggregates_to_cancelled - django.db.utils.IntegrityError: (1048, "Column 'category_id' cannot be null")
ERROR orders/tests/test_multi_seller.py::TestPartialShipping::test_some_shipped_keeps_order_in_processing - django.db.utils.IntegrityError: (1048, "Column 'category_id' cannot be null")
ERROR orders/tests/test_multi_seller.py::TestPartialShipping::test_one_processing_one_pending_keeps_order_in_processing - django.db.utils.IntegrityError: (1048, "Column 'category_id' cannot be null")
ERROR orders/tests/test_multi_seller.py::TestPartialShipping::test_one_shipped_one_processing_keeps_order_in_processing - django.db.utils.IntegrityError: (1048, "Column 'category_id' cannot be null")
ERROR orders/tests/test_multi_seller.py::TestPartialShipping::test_order_transitions_to_shipped_when_last_item_shipped - django.db.utils.IntegrityError: (1048, "Column 'category_id' cannot be null")
ERROR orders/tests/test_multi_seller.py::TestSellerIsolation::test_get_seller_items_returns_only_own_items - django.db.utils.IntegrityError: (1048, "Column 'category_id' cannot be null")
ERROR orders/tests/test_multi_seller.py::TestSellerIsolation::test_seller_cannot_update_other_seller_items - django.db.utils.IntegrityError: (1048, "Column 'category_id' cannot be null")
ERROR orders/tests/test_multi_seller.py::TestSellerIsolation::test_update_item_status_validates_status_transition - django.db.utils.IntegrityError: (1048, "Column 'category_id' cannot be null")
ERROR orders/tests/test_multi_seller.py::TestSellerIsolation::test_update_item_status_valid_transitions - django.db.utils.IntegrityError: (1048, "Column 'category_id' cannot be null")
ERROR orders/tests/test_multi_seller.py::TestOrderStateMachineIntegration::test_paid_order_remains_paid_until_first_item_processed - django.db.utils.IntegrityError: (1048, "Column 'category_id' cannot be null")
ERROR orders/tests/test_multi_seller.py::TestOrderStateMachineIntegration::test_order_status_respects_state_machine_valid_transitions - django.db.utils.IntegrityError: (1048, "Column 'category_id' cannot be null")
ERROR orders/tests/test_stock_reservation.py::TestStockReservationInitialStatus::test_reservation_status_reserved_on_order_creation_wallet_payment - NameError: name 'Category' is not defined
ERROR orders/tests/test_stock_reservation.py::TestStockReservationInitialStatus::test_reservation_status_reserved_on_order_creation_cod_payment - NameError: name 'Category' is not defined
ERROR orders/tests/test_stock_reservation.py::TestStockReservationInitialStatus::test_reservation_status_reserved_for_multiple_items - NameError: name 'Category' is not defined
ERROR orders/tests/test_stock_reservation.py::TestStockReservationReleasedOnCancellation::test_reservation_status_released_on_cancellation_pending_payment - NameError: name 'Category' is not defined
ERROR orders/tests/test_stock_reservation.py::TestStockReservationReleasedOnCancellation::test_reservation_status_released_on_cancellation_cod_order - NameError: name 'Category' is not defined
ERROR orders/tests/test_stock_reservation.py::TestStockReservationReleasedOnCancellation::test_reservation_status_released_on_payment_timeout - NameError: name 'Category' is not defined
ERROR orders/tests/test_stock_reservation.py::TestStockReservationCommittedOnCompletion::test_reservation_status_committed_on_cod_order_completion - NameError: name 'Category' is not defined
ERROR orders/tests/test_stock_reservation.py::TestStockReservationCommittedOnCompletion::test_reservation_status_committed_for_multiple_items - NameError: name 'Category' is not defined
ERROR orders/tests/test_stock_reservation.py::TestStockReservationLifecycle::test_full_lifecycle_reserved_to_released - NameError: name 'Category' is not defined
ERROR orders/tests/test_stock_reservation.py::TestStockReservationLifecycle::test_full_lifecycle_reserved_to_committed - NameError: name 'Category' is not defined
====================================================================================== 134 failed, 232 passed, 37 skipped, 2 warnings, 26 errors in 87.27s (0:01:27) =======================================================================================
(venv) momen@Momens-Mac-mini to7fabackend % 

====================================================================================================================== tests coverage ======================================================================================================================
_____________________________________________________________________________________________________ coverage: platform darwin, python 3.9.6-final-0 ______________________________________________________________________________________________________

Name                                                                                                        Stmts   Miss  Cover
-------------------------------------------------------------------------------------------------------------------------------
orders/__init__.py                                                                                              0      0   100%
orders/admin.py                                                                                                19      2    89%
orders/apps.py                                                                                                  4      0   100%
orders/atomic_order_system.py                                                                                 376    218    42%
orders/migrations/0001_initial.py                                                                               8      8     0%
orders/migrations/0002_add_atomic_order_fields.py                                                               5      5     0%
orders/migrations/0003_add_order_indexes.py                                                                     4      4     0%
orders/migrations/0004_rename_orders_order_user_created_at_idx_orders_orde_user_id_0ae59f_idx_and_more.py       4      4     0%
orders/migrations/0005_remove_order_orders_orde_user_id_0ae59f_idx.py                                           4      4     0%
orders/migrations/0006_order_orders_orde_user_id_0ae59f_idx.py                                                  4      4     0%
orders/migrations/0007_order_payment_timeout_at_orderitem_item_status_and_more.py                               4      4     0%
orders/migrations/0008_add_variant_id_index.py                                                                  4      4     0%
orders/migrations/__init__.py                                                                                   0      0   100%
orders/models.py                                                                                               63     14    78%
orders/serializers.py                                                                                          81     42    48%
orders/services/__init__.py                                                                                     4      4     0%
orders/services/multi_seller.py                                                                                46     46     0%
orders/tasks.py                                                                                                50     25    50%
orders/tests/__init__.py                                                                                        0      0   100%
orders/tests/test_checkout.py                                                                                  46     12    74%
orders/tests/test_cod_flow.py                                                                                 139     79    43%
orders/tests/test_invariants.py                                                                               122     76    38%
orders/tests/test_multi_seller.py                                                                             177    135    24%
orders/tests/test_payment_timeout.py                                                                          180     94    48%
orders/tests/test_refund.py                                                                                   144    103    28%
orders/tests/test_spec002_cancellation.py                                                                     224     22    90%
orders/tests/test_spec002_idempotency.py                                                                      187     65    65%
orders/tests/test_spec002_inventory.py                                                                        147     36    76%
orders/tests/test_spec002_lifecycle.py                                                                        126      0   100%
orders/tests/test_spec002_order_creation.py                                                                   162     43    73%
orders/tests/test_spec002_payment.py                                                                          140     73    48%
orders/tests/test_state_machine.py                                                                            142      0   100%
orders/tests/test_stock_reservation.py                                                                        184    158    14%
orders/tests/test_views.py                                                                                    141    108    23%
orders/urls.py                                                                                                  3      0   100%
orders/views.py                                                                                               257    188    27%
-------------------------------------------------------------------------------------------------------------------------------
TOTAL                                                                                                        3201   1580    51%
================================================================================================================= short test summary info ==================================================================================================================
FAILED custom_auth/tests/test_spec001_login.py::TestLoginAllowsUnverifiedUsers::test_login_succeeds_for_unverified_mobile_user - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_spec001_login.py::TestLoginAllowsUnverifiedUsers::test_login_does_not_check_mobile_verification - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_spec001_login.py::TestLoginBlocksOnlyLockedUsers::test_login_fails_for_locked_user - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_spec001_login.py::TestLoginBlocksOnlyLockedUsers::test_login_succeeds_for_blocked_user - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_spec001_login.py::TestLoginBlocksOnlyLockedUsers::test_login_succeeds_for_verified_user - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_spec001_login.py::TestLockEnforcedBeforePasswordValidation::test_lock_check_before_password - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_spec001_login.py::TestLockEnforcedBeforePasswordValidation::test_locked_user_sees_banned_message - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_spec001_login.py::TestLoginResponseFields::test_login_accepts_email_and_password - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_spec001_login.py::TestLoginResponseFields::test_login_returns_user_state_fields - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_spec001_login.py::TestRegistrationRequirements::test_email_used_for_login_not_verification - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_returns_blocked_capabilities_in_response - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_returns_correct_blocked_capabilities - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_returns_correct_mobile_verified_state - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_returns_is_blocked_in_response - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_returns_is_locked_in_response - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_returns_is_mobile_verified_in_response - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_with_blocked_capabilities_still_works - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_with_nonexistent_user_fails - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_with_unverified_mobile_still_works - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_with_wrong_password_fails - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED custom_auth/tests/test_user_state.py::TestLoginUserState::test_login_without_email_verification_fails - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED cart/tests/test_cart.py::TestGuestCartOperations::test_add_item_to_guest_cart_via_api - AssertionError: 400 != 200
FAILED cart/tests/test_invariants.py::TestCartInvariants::test_inv_017_cart_item_variant_id_is_null_or_valid_product_category_variant_option - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller@test.com' for key 'custom_auth_user.email'")
FAILED cart/tests/test_invariants.py::TestCartInvariants::test_inv_018_cart_item_cannot_reference_inactive_variant - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller2@test.com' for key 'custom_auth_user.email'")
FAILED cart/tests/test_invariants.py::TestCartInvariants::test_inv_019_cart_item_cannot_reference_zero_stock_variant - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller3@test.com' for key 'custom_auth_user.email'")
FAILED cart/tests/test_spec001_cart.py::TestGuestCartSessionBased::test_guest_cart_created_with_session_id - cart.models.Cart.DoesNotExist: Cart matching query does not exist.
FAILED cart/tests/test_spec001_cart.py::TestCartMergeOnLogin::test_cart_merge_triggered_on_login - redis.exceptions.ConnectionError: Error 61 connecting to 127.0.0.1:6379. Connection refused.
FAILED cart/tests/test_spec001_cart.py::TestCartMergeOnLogin::test_cart_merge_preserves_all_guest_items - TypeError: Direct assignment to the reverse side of a related set is prohibited. Use items.set() instead.
FAILED cart/tests/test_spec001_cart.py::TestCartMergeOnLogin::test_user_cart_quantity_wins_on_conflict - TypeError: Direct assignment to the reverse side of a related set is prohibited. Use items.set() instead.
FAILED cart/tests/test_spec001_cart.py::TestCartMergeOnLogin::test_guest_only_items_added_to_user_cart - TypeError: Direct assignment to the reverse side of a related set is prohibited. Use items.set() instead.
FAILED cart/tests/test_spec001_cart.py::TestCartMergeOnLogin::test_guest_cart_removed_after_merge - TypeError: merge_guest_cart() takes 2 positional arguments but 3 were given
FAILED cart/tests/test_spec001_cart.py::TestCheckoutVerificationRequirement::test_checkout_requires_authentication - assert 404 == 401
FAILED cart/tests/test_spec001_cart.py::TestCheckoutVerificationRequirement::test_checkout_requires_mobile_verification - assert 404 == 403
FAILED cart/tests/test_spec001_cart.py::TestCheckoutVerificationRequirement::test_checkout_triggers_otp_for_unverified - ValueError: Content-Type header is "text/html; charset=utf-8", not "application/json"
FAILED cart/tests/test_spec001_cart.py::TestCheckoutVerificationRequirement::test_checkout_proceeds_for_verified_user - TypeError: Direct assignment to the reverse side of a related set is prohibited. Use items.set() instead.
FAILED orders/tests/test_checkout.py::CheckoutVerificationTests::test_unverified_user_blocked_from_checkout - AssertionError: 404 != 403
FAILED orders/tests/test_checkout.py::CheckoutVerificationTests::test_verified_user_can_checkout - AssertionError: 404 not found in [200, 201]
FAILED orders/tests/test_cod_flow.py::TestCODOrderCreation::test_cod_order_creates_with_cod_pending_status - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_cod_flow.py::TestCODOrderCreation::test_non_cod_order_creates_with_pending_payment_status - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_cod_flow.py::TestCODLifecycle::test_cod_transition_to_processing - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_cod_flow.py::TestCODLifecycle::test_cod_transition_to_shipped - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_cod_flow.py::TestCODLifecycle::test_cod_transition_to_delivered - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_cod_flow.py::TestCODLifecycle::test_cod_transition_to_completed - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_cod_flow.py::TestCODLifecycle::test_cod_full_lifecycle - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_cod_flow.py::TestCODCancellation::test_cod_order_can_be_cancelled - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_cod_flow.py::TestCODCancellation::test_cod_order_cannot_be_cancelled_after_shipped - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_cod_flow.py::TestCODCancellation::test_cod_cancellation_from_processing - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_cod_flow.py::TestCODCancellation::test_cod_cancellation_does_not_require_refund - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_invariants.py::TestStockInvariants::test_inv_001_stock_only_mutated_via_stock_lock_manager_in_atomic_blocks - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller@test.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_invariants.py::TestStockInvariants::test_inv_002_stock_checks_after_select_for_update_lock - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller2@test.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_invariants.py::TestStockInvariants::test_inv_003_cancelled_order_restores_stock_to_exact_variant - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller3@test.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_invariants.py::TestStockInvariants::test_inv_004_stock_never_goes_negative - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller4@test.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_invariants.py::TestStockInvariants::test_inv_005_product_stock_quantity_not_used_for_variant_products - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller5@test.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_invariants.py::TestOrderInvariants::test_inv_006_order_item_always_has_valid_product_id - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller6@test.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_invariants.py::TestOrderInvariants::test_inv_007_order_item_variant_id_is_null_or_valid_product_category_variant_option_id - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller7@test.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_invariants.py::TestOrderInvariants::test_inv_008_reservation_status_transitions_follow_rules - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller8@test.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_invariants.py::TestOrderInvariants::test_inv_009_order_with_released_item_cannot_transition_to_paid - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller9@test.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_payment_timeout.py::TestPaymentTimeoutCalculation::test_wallet_order_has_payment_timeout - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_payment_timeout.py::TestPaymentTimeoutCalculation::test_instapay_order_has_payment_timeout - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_payment_timeout.py::TestPaymentTimeoutCalculation::test_credit_card_order_has_payment_timeout - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_payment_timeout.py::TestPaymentTimeoutCalculation::test_cod_order_has_no_payment_timeout - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_payment_timeout.py::TestTimeoutTaskCancelsExpiredOrders::test_timeout_task_cancels_expired_order - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_payment_timeout.py::TestTimeoutTaskCancelsExpiredOrders::test_timeout_task_does_not_cancel_future_orders - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_payment_timeout.py::TestTimeoutTaskCancelsExpiredOrders::test_timeout_task_skips_non_pending_orders - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_payment_timeout.py::TestTimeoutTaskCancelsExpiredOrders::test_timeout_task_handles_multiple_expired_orders - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_payment_timeout.py::TestStockReleaseOnTimeoutCancellation::test_timeout_cancellation_releases_stock - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_payment_timeout.py::TestStockReleaseOnTimeoutCancellation::test_timeout_cancellation_updates_reservation_status - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_payment_timeout.py::TestWalletHoldReleaseOnTimeoutCancellation::test_timeout_cancellation_releases_wallet_hold - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_payment_timeout.py::TestWalletHoldReleaseOnTimeoutCancellation::test_timeout_cancellation_creates_refund_transaction - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_payment_timeout.py::TestWalletHoldReleaseOnTimeoutCancellation::test_timeout_cancellation_for_non_wallet_orders - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_refund.py::TestRefundFlow::test_refund_transitions_order_to_refunded_state - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_refund.py::TestRefundFlow::test_wallet_credit_on_refund - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_refund.py::TestRefundFlow::test_stock_release_on_refund - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_refund.py::TestRefundFlow::test_refund_prevention_on_unpaid_orders - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_refund.py::TestRefundFlow::test_refund_prevention_on_cod_orders - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_refund.py::TestRefundFlow::test_refund_from_delivered_state - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_refund.py::TestRefundFlow::test_refund_idempotency - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_refund.py::TestRefundFlow::test_refund_from_processing_state - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_refund.py::TestRefundFlow::test_refund_from_shipped_state - orders.atomic_order_system.ProductVisibilityError: Order contains 1 product(s) that are not approved. All products must be approved before ordering.
FAILED orders/tests/test_spec002_cancellation.py::TestCancellationEligibility::test_customer_cannot_cancel_shipped_order - assert 400 in [200, 201, 403]
FAILED orders/tests/test_spec002_cancellation.py::TestCancellationEligibility::test_seller_cannot_cancel_order - assert 400 in [403, 404, 405]
FAILED orders/tests/test_spec002_cancellation.py::TestCancellationEligibility::test_admin_can_cancel_any_order - assert 400 in [200, 201, 403, 405]
FAILED orders/tests/test_spec002_cancellation.py::TestPartialCancellationPolicy::test_partial_cancellation_not_supported - assert 405 in [400, 200, 201]
FAILED orders/tests/test_spec002_cancellation.py::TestRefundTiming::test_wallet_refund_processed_immediately - django.db.utils.IntegrityError: (1062, "Duplicate entry '6046' for key 'wallet_wallet.user_id'")
FAILED orders/tests/test_spec002_cancellation.py::TestRefundTiming::test_refund_completion_triggers_refunded_state - django.db.utils.IntegrityError: (1062, "Duplicate entry '6047' for key 'wallet_wallet.user_id'")
FAILED orders/tests/test_spec002_cancellation.py::TestRefundTiming::test_failed_refund_does_not_change_order_state - django.db.utils.IntegrityError: (1062, "Duplicate entry '6048' for key 'wallet_wallet.user_id'")
FAILED orders/tests/test_spec002_idempotency.py::TestOrderCreationIdempotency::test_duplicate_order_request_returns_existing_order - AssertionError: Expected a `Response`, `HttpResponse` or `StreamingHttpResponse` to be returned from the view, but received a `<class 'tuple'>`
FAILED orders/tests/test_spec002_idempotency.py::TestOrderCreationIdempotency::test_idempotency_key_based_on_user_and_cart - AssertionError: Expected a `Response`, `HttpResponse` or `StreamingHttpResponse` to be returned from the view, but received a `<class 'tuple'>`
FAILED orders/tests/test_spec002_idempotency.py::TestOrderCreationIdempotency::test_idempotency_window_at_least_60_seconds - AssertionError: Expected a `Response`, `HttpResponse` or `StreamingHttpResponse` to be returned from the view, but received a `<class 'tuple'>`
FAILED orders/tests/test_spec002_inventory.py::TestStockReservationRules::test_stock_reserved_on_order_creation - django.db.utils.IntegrityError: (1048, "Column 'seller_id' cannot be null")
FAILED orders/tests/test_spec002_inventory.py::TestStockReservationRules::test_stock_reservation_specific_to_variant - TypeError: ProductVariant() got unexpected keyword arguments: 'stock_quantity'
FAILED orders/tests/test_spec002_inventory.py::TestStockReservationRules::test_reserved_stock_decremented_from_available_not_total - django.db.utils.IntegrityError: (1048, "Column 'category_id' cannot be null")
FAILED orders/tests/test_spec002_inventory.py::TestVariantSpecificStockHandling::test_each_variant_has_independent_stock - TypeError: ProductVariant() got unexpected keyword arguments: 'stock_quantity'
FAILED orders/tests/test_spec002_inventory.py::TestVariantSpecificStockHandling::test_stock_reservation_references_variant_id - TypeError: ProductVariant() got unexpected keyword arguments: 'stock_quantity'
FAILED orders/tests/test_spec002_inventory.py::TestVariantSpecificStockHandling::test_order_line_item_stores_variant_id - TypeError: ProductVariant() got unexpected keyword arguments: 'stock_quantity'
FAILED orders/tests/test_spec002_inventory.py::TestOrderDataForStockRelease::test_order_item_contains_sufficient_data - TypeError: ProductVariant() got unexpected keyword arguments: 'stock_quantity'
FAILED orders/tests/test_spec002_inventory.py::TestOrderDataForStockRelease::test_stock_release_uses_historical_snapshot - django.db.utils.IntegrityError: (1048, "Column 'seller_id' cannot be null")
FAILED orders/tests/test_spec002_order_creation.py::TestOrderCreationPreconditions::test_order_creation_requires_mobile_verification - AssertionError: Expected a `Response`, `HttpResponse` or `StreamingHttpResponse` to be returned from the view, but received a `<class 'tuple'>`
FAILED orders/tests/test_spec002_order_creation.py::TestOrderCreationPreconditions::test_order_creation_allows_verified_user - AssertionError: Expected a `Response`, `HttpResponse` or `StreamingHttpResponse` to be returned from the view, but received a `<class 'tuple'>`
FAILED orders/tests/test_spec002_order_creation.py::TestOrderCreationPreconditions::test_order_creation_blocks_locked_users - AssertionError: Expected a `Response`, `HttpResponse` or `StreamingHttpResponse` to be returned from the view, but received a `<class 'tuple'>`
FAILED orders/tests/test_spec002_order_creation.py::TestOrderCreationPreconditions::test_order_creation_requires_nonempty_cart - AssertionError: Expected a `Response`, `HttpResponse` or `StreamingHttpResponse` to be returned from the view, but received a `<class 'tuple'>`
FAILED orders/tests/test_spec002_order_creation.py::TestOrderCreationPreconditions::test_order_creation_validates_stock_availability - ValueError: Not enough stock available. Only 0 items left.
FAILED orders/tests/test_spec002_order_creation.py::TestIdempotencyBehavior::test_duplicate_order_request_returns_existing_order - AssertionError: Expected a `Response`, `HttpResponse` or `StreamingHttpResponse` to be returned from the view, but received a `<class 'tuple'>`
FAILED orders/tests/test_spec002_order_creation.py::TestPartialFailureHandling::test_stock_reservation_failure_rolls_back_all - ValueError: Not enough stock available. Only 0 items left.
FAILED orders/tests/test_spec002_order_creation.py::TestPartialFailureHandling::test_payment_failure_releases_stock - AssertionError: Expected a `Response`, `HttpResponse` or `StreamingHttpResponse` to be returned from the view, but received a `<class 'tuple'>`
FAILED orders/tests/test_spec002_order_creation.py::TestPartialFailureHandling::test_order_creation_error_indicates_failed_item - ValueError: Not enough stock available. Only 0 items left.
FAILED orders/tests/test_spec002_payment.py::TestWalletPaymentRules::test_wallet_balance_verified_before_payment - django.db.utils.IntegrityError: (1062, "Duplicate entry '6106' for key 'wallet_wallet.user_id'")
FAILED orders/tests/test_spec002_payment.py::TestWalletPaymentRules::test_wallet_balance_held_on_payment_initiation - django.db.utils.IntegrityError: (1062, "Duplicate entry '6107' for key 'wallet_wallet.user_id'")
FAILED orders/tests/test_spec002_payment.py::TestWalletPaymentRules::test_wallet_hold_converted_to_debit_on_payment - django.db.utils.IntegrityError: (1062, "Duplicate entry '6108' for key 'wallet_wallet.user_id'")
FAILED orders/tests/test_spec002_payment.py::TestWalletPaymentRules::test_wallet_hold_released_on_cancellation - django.db.utils.IntegrityError: (1062, "Duplicate entry '6109' for key 'wallet_wallet.user_id'")
FAILED orders/tests/test_spec002_payment.py::TestWalletPaymentRules::test_wallet_transaction_has_order_reference - django.db.utils.IntegrityError: (1062, "Duplicate entry '6110' for key 'wallet_wallet.user_id'")
FAILED orders/tests/test_spec002_payment.py::TestOrderPaymentStateCoordination::test_order_state_matches_payment_state - django.db.utils.IntegrityError: (1062, "Duplicate entry '6111' for key 'wallet_wallet.user_id'")
FAILED orders/tests/test_spec002_payment.py::TestPendingPaymentTimeout::test_pending_payment_has_15_minute_timeout - assert None is not None
FAILED orders/tests/test_spec002_payment.py::TestPaymentStateTransitions::test_paid_order_has_captured_payment - django.db.utils.IntegrityError: (1062, "Duplicate entry '6116' for key 'wallet_wallet.user_id'")
FAILED orders/tests/test_spec002_payment.py::TestPaymentStateTransitions::test_refunded_order_has_refunded_payment - django.db.utils.IntegrityError: (1062, "Duplicate entry '6117' for key 'wallet_wallet.user_id'")
FAILED orders/tests/test_views.py::OrderLifecycleTests::test_acknowledge_order_by_non_seller_fails - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_views.py::OrderLifecycleTests::test_acknowledge_order_by_seller - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_views.py::OrderLifecycleTests::test_acknowledge_order_invalid_state - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_views.py::OrderLifecycleTests::test_complete_order - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_views.py::OrderLifecycleTests::test_complete_order_invalid_state - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_views.py::OrderLifecycleTests::test_deliver_order - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_views.py::OrderLifecycleTests::test_deliver_order_invalid_state - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_views.py::OrderLifecycleTests::test_refund_order_by_admin - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_views.py::OrderLifecycleTests::test_refund_order_by_non_admin_fails - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_views.py::OrderLifecycleTests::test_refund_order_invalid_state - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_views.py::OrderLifecycleTests::test_ship_order_by_non_seller_fails - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_views.py::OrderLifecycleTests::test_ship_order_by_seller - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller@example.com' for key 'custom_auth_user.email'")
FAILED orders/tests/test_views.py::OrderStatesEndpointTests::test_order_states_endpoint - django.db.utils.IntegrityError: (1062, "Duplicate entry 'test@example.com' for key 'custom_auth_user.email'")
FAILED wallet/tests/test_spec002_wallet.py::TestWalletRefundBehavior::test_refund_credits_wallet - AssertionError: assert Decimal('100.00') > Decimal('100.00')
FAILED products/tests/test_invariants.py::TestVariantSystemInvariants::test_inv_014_only_product_category_variant_option_owns_stock - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller122@test.com' for key 'custom_auth_user.email'")
FAILED products/tests/test_invariants.py::TestVariantSystemInvariants::test_inv_015_new_products_use_product_category_variant_option - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller2@test.com' for key 'custom_auth_user.email'")
FAILED products/tests/test_invariants.py::TestVariantSystemInvariants::test_inv_016_combination_stocks_not_used_for_stock - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller123@test.com' for key 'custom_auth_user.email'")
FAILED products/tests/test_invariants.py::TestVisibilityInvariants::test_inv_010_unapproved_products_not_in_public_listings - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller4@test.com' for key 'custom_auth_user.email'")
FAILED products/tests/test_invariants.py::TestVisibilityInvariants::test_inv_011_unapproved_products_cannot_be_added_to_cart - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller5@test.com' for key 'custom_auth_user.email'")
FAILED products/tests/test_invariants.py::TestVisibilityInvariants::test_inv_012_unapproved_products_cannot_be_in_orders - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller6@test.com' for key 'custom_auth_user.email'")
FAILED products/tests/test_invariants.py::TestVisibilityInvariants::test_inv_013_approval_requires_is_active_true - django.db.utils.IntegrityError: (1062, "Duplicate entry 'seller7@test.com' for key 'custom_auth_user.email'")
ERROR orders/tests/test_multi_seller.py::TestPerItemStatusTracking::test_initial_item_status_is_pending - django.db.utils.IntegrityError: (1048, "Column 'category_id' cannot be null")
ERROR orders/tests/test_multi_seller.py::TestPerItemStatusTracking::test_item_status_independent_of_other_items - django.db.utils.IntegrityError: (1048, "Column 'category_id' cannot be null")
ERROR orders/tests/test_multi_seller.py::TestOrderStatusAggregation::test_all_shipped_aggregates_to_shipped - django.db.utils.IntegrityError: (1048, "Column 'category_id' cannot be null")
ERROR orders/tests/test_multi_seller.py::TestOrderStatusAggregation::test_all_delivered_aggregates_to_delivered - django.db.utils.IntegrityError: (1048, "Column 'category_id' cannot be null")
ERROR orders/tests/test_multi_seller.py::TestOrderStatusAggregation::test_all_completed_aggregates_to_completed - django.db.utils.IntegrityError: (1048, "Column 'category_id' cannot be null")
ERROR orders/tests/test_multi_seller.py::TestOrderStatusAggregation::test_all_cancelled_aggregates_to_cancelled - django.db.utils.IntegrityError: (1048, "Column 'category_id' cannot be null")
ERROR orders/tests/test_multi_seller.py::TestPartialShipping::test_some_shipped_keeps_order_in_processing - django.db.utils.IntegrityError: (1048, "Column 'category_id' cannot be null")
ERROR orders/tests/test_multi_seller.py::TestPartialShipping::test_one_processing_one_pending_keeps_order_in_processing - django.db.utils.IntegrityError: (1048, "Column 'category_id' cannot be null")
ERROR orders/tests/test_multi_seller.py::TestPartialShipping::test_one_shipped_one_processing_keeps_order_in_processing - django.db.utils.IntegrityError: (1048, "Column 'category_id' cannot be null")
ERROR orders/tests/test_multi_seller.py::TestPartialShipping::test_order_transitions_to_shipped_when_last_item_shipped - django.db.utils.IntegrityError: (1048, "Column 'category_id' cannot be null")
ERROR orders/tests/test_multi_seller.py::TestSellerIsolation::test_get_seller_items_returns_only_own_items - django.db.utils.IntegrityError: (1048, "Column 'category_id' cannot be null")
ERROR orders/tests/test_multi_seller.py::TestSellerIsolation::test_seller_cannot_update_other_seller_items - django.db.utils.IntegrityError: (1048, "Column 'category_id' cannot be null")
ERROR orders/tests/test_multi_seller.py::TestSellerIsolation::test_update_item_status_validates_status_transition - django.db.utils.IntegrityError: (1048, "Column 'category_id' cannot be null")
ERROR orders/tests/test_multi_seller.py::TestSellerIsolation::test_update_item_status_valid_transitions - django.db.utils.IntegrityError: (1048, "Column 'category_id' cannot be null")
ERROR orders/tests/test_multi_seller.py::TestOrderStateMachineIntegration::test_paid_order_remains_paid_until_first_item_processed - django.db.utils.IntegrityError: (1048, "Column 'category_id' cannot be null")
ERROR orders/tests/test_multi_seller.py::TestOrderStateMachineIntegration::test_order_status_respects_state_machine_valid_transitions - django.db.utils.IntegrityError: (1048, "Column 'category_id' cannot be null")
ERROR orders/tests/test_stock_reservation.py::TestStockReservationInitialStatus::test_reservation_status_reserved_on_order_creation_wallet_payment - NameError: name 'Category' is not defined
ERROR orders/tests/test_stock_reservation.py::TestStockReservationInitialStatus::test_reservation_status_reserved_on_order_creation_cod_payment - NameError: name 'Category' is not defined
ERROR orders/tests/test_stock_reservation.py::TestStockReservationInitialStatus::test_reservation_status_reserved_for_multiple_items - NameError: name 'Category' is not defined
ERROR orders/tests/test_stock_reservation.py::TestStockReservationReleasedOnCancellation::test_reservation_status_released_on_cancellation_pending_payment - NameError: name 'Category' is not defined
ERROR orders/tests/test_stock_reservation.py::TestStockReservationReleasedOnCancellation::test_reservation_status_released_on_cancellation_cod_order - NameError: name 'Category' is not defined
ERROR orders/tests/test_stock_reservation.py::TestStockReservationReleasedOnCancellation::test_reservation_status_released_on_payment_timeout - NameError: name 'Category' is not defined
ERROR orders/tests/test_stock_reservation.py::TestStockReservationCommittedOnCompletion::test_reservation_status_committed_on_cod_order_completion - NameError: name 'Category' is not defined
ERROR orders/tests/test_stock_reservation.py::TestStockReservationCommittedOnCompletion::test_reservation_status_committed_for_multiple_items - NameError: name 'Category' is not defined
ERROR orders/tests/test_stock_reservation.py::TestStockReservationLifecycle::test_full_lifecycle_reserved_to_released - NameError: name 'Category' is not defined
ERROR orders/tests/test_stock_reservation.py::TestStockReservationLifecycle::test_full_lifecycle_reserved_to_committed - NameError: name 'Category' is not defined
======================================================================================= 136 failed, 230 passed, 37 skipped, 1 warning, 26 errors in 87.91s (0:01:27) =======================================================================================
(venv) momen@Momens-Mac-mini to7fabackend % 