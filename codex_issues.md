
• ISSUE-001
  Category: Architecture
  Severity: Critical
  Problem: SupportConsumer imports SupportTicket and SupportMessage, but support/models.py only exports ContactRequest, ContactNote, and ContactStats.
  Why This Is a Problem: ASGI/Channels import can fail at startup, breaking WebSocket support or whole app boot depending on import path.
  How to Fix: Update consumer to use existing contact models or restore missing models; ensure imports match actual model definitions. Requires code change.

  ISSUE-002
  Category: Bug
  Severity: Critical
  Location: custom_auth, custom_auth/services/verification.py:368-373
  How to Fix: Return Response({...}, status=403) consistently. Requires code change.

  ISSUE-003
  Category: Bug
  Severity: Critical
  Problem: Shipping flow updates OrderItem.tracking_number, but OrderItem model has no tracking_number field.
  Why This Is a Problem: Runtime FieldError on ship endpoint; sellers cannot ship orders.
  How to Fix: Add tracking_number field via migration or remove/update tracking logic. Requires code change + migration (if field is required).

  ISSUE-004
  Category: Bug
  Severity: Critical
  Problem: User block/unblock code writes blocked_at, blocked_by, block_reason, unblocked_at, unblocked_by, but these fields do not exist on User.
  Why This Is a Problem: Admin block/unblock endpoint will throw attribute/database errors and fail.
  How to Fix: Align API with actual model fields (is_locked, locked_at, locked_by, locked_reason, is_blocked, blocked_reason) or add missing fields via migration. Requires code change + migration (if adding fields).

  ISSUE-005
  Category: Bug
  Severity: Critical
  Problem: Serializer references nonexistent fields (blocked_at, block_reason, unblocked_at, unblocked_by).
  Why This Is a Problem: Serialization fails for user management APIs using this serializer.
  How to Fix: Remove/replace invalid fields with existing schema fields; update serializer methods accordingly. Requires code change.

  ISSUE-006
  Category: Bug
  Severity: Critical
  Problem: Admin serializer references nonexistent user fields (blocked_at, block_reason, unblocked_at, unblocked_by).
  Why This Is a Problem: Admin user APIs can fail serialization at runtime.
  How to Fix: Use actual lock/block fields or introduce matching fields via migration. Requires code change + migration (if adding fields).

  ISSUE-007
  Category: Config
  Severity: Critical
  Problem: Production settings include a hardcoded fallback SECRET_KEY.
  Why This Is a Problem: Predictable signing key enables token/session forgery if deployed with default.
  How to Fix: Remove fallback; fail fast when SECRET_KEY is missing. Requires config change.

  ISSUE-008
  Category: Config
  Severity: Critical
  Problem: Production DB settings use insecure fallback credentials (django_user / strongpass).
  Why This Is a Problem: Weak/default credentials can lead to immediate DB compromise in misconfigured deployments.
  How to Fix: Remove default DB credentials and require env vars. Requires config change.

  ISSUE-009
  Category: Data Model
  Severity: Critical
  Problem: Duplicate domain models (Advertisement, ContentSettings) are defined in multiple apps.
  Why This Is a Problem: Data divergence risk, ambiguous source of truth, and inconsistent behavior across endpoints.
  How to Fix: Consolidate to one model set and migrate data; update all imports and queries. Requires code change + migration + data cleanup.

  ISSUE-010
  Category: Missing Feature
  Severity: Critical
  Why This Is a Problem: Core commerce payment flows are non-functional while APIs claim success.
  How to Fix: Implement real payment method CRUD, processing, verification, and refund workflows with validations and persistence. Requires code change.

  ISSUE-011
  Category: Security
  Severity: Critical
  Problem: manage_offer_detail allows PUT/DELETE for any authenticated user; no admin/staff authorization check.
  Why This Is a Problem: Privilege escalation allows unauthorized users to modify/delete offers.
  How to Fix: Enforce IsAdminUser or explicit request.user.is_staff guard on all non-GET methods. Requires code change.

  ISSUE-012
  Category: Security
  Severity: Critical
  Location: products, products/views.py:980-1020
  How to Fix: Require admin/staff permission for non-read operations. Requires code change.

  ISSUE-013
  Category: Security
  Problem: manage_advertisements allows any authenticated user to create/manage ads; no staff check.
  Why This Is a Problem: Non-admin users can inject or alter platform ads.
  How to Fix: Restrict endpoint to admin/staff users with IsAdminUser or explicit checks. Requires code change.

  ISSUE-014
  Category: Security
  Severity: Critical
  Problem: manage_advertisement_detail lacks admin/staff authorization for PUT/DELETE.
  Why This Is a Problem: Unauthorized ad modification/deletion by non-admin users.
  How to Fix: Add admin/staff authorization checks on mutable methods. Requires code change.

  ISSUE-015
  Category: Security
  Severity: Critical
  Location: custom_auth, custom_auth/services/verification.py:149-155
  Problem: OTP code is returned in API response payload.
  Why This Is a Problem: OTP bypass; anyone intercepting API response can verify without SMS possession.
  How to Fix: Never return OTP in non-test environments; gate test-only behavior with explicit TESTING/debug flags. Requires code change + config change.

  ISSUE-016
  Category: Security
  Severity: Critical
  Why This Is a Problem: DB read exposure immediately compromises all active reset flows.
  How to Fix: Store token hash only, compare hashed input token, rotate/expire securely. Requires code change + data cleanup for existing tokens.

  ISSUE-017
  Category: Security
  Severity: Critical
  Problem: Email verification tokens are stored and queried in plaintext.
  Why This Is a Problem: DB compromise allows account verification takeover.
  How to Fix: Store hash digest only and verify by hash; expire and rotate tokens. Requires code change + data cleanup.

  ISSUE-018
  Category: Security
  Severity: Critical
  Why This Is a Problem: Auth middleware is bypassed for this view, making authorization logic unreliable and endpoint behavior broken/unsafe.
  How to Fix: Remove @authentication_classes([]) and use standard JWT auth. Requires code change.

  ISSUE-019
  Category: Architecture
  Severity: High
  Problem: Product/admin/seller management logic is duplicated across multiple large modules with inconsistent rules.
  Why This Is a Problem: Behavior drift and bug reintroduction across parallel implementations.
  How to Fix: Centralize domain operations in shared service layer and make endpoints thin wrappers. Requires code change.

  ISSUE-020
  Category: Bug
  Severity: High
  Problem: capture_payment checks for status 'pending', but model uses 'pending_payment'.
  Why This Is a Problem: Valid orders cannot be captured; payment flow breaks.
  How to Fix: Replace status checks with canonical enum values. Requires code change.

  ISSUE-021
  Category: Bug
  Severity: High
  Location: orders, orders/views.py:318; orders, orders/models.py:15-24
  How to Fix: Use canonical order statuses. Requires code change.

  ISSUE-022
  Category: Bug
  Severity: High
  Location: orders, orders/views.py:219-221
  Problem: Audit log message claims “updated from X to Y” after status already overwritten, so old/new values are wrong.
  Why This Is a Problem: Incorrect operational audit trail.
  How to Fix: Capture old status before assignment and log both accurately. Requires code change.

  ISSUE-023
  Category: Bug
  Severity: High
  Why This Is a Problem: Unexpected endpoint behavior and dead code.
  How to Fix: Use unique paths or merge behavior in one view. Requires code change.

  ISSUE-024
  Category: Bug
  Severity: High
  Why This Is a Problem: Runtime AttributeError when dates are null.
  How to Fix: Use conditional serialization (x.isoformat() if x else None). Requires code change.

  ISSUE-025
  Category: Bug
  Severity: High
  Location: notifications, notifications/models.py:149-154; custom_auth, custom_auth/models.py:46-50
  How to Fix: Map to actual user types or derived seller/customer predicates. Requires code change.

  ISSUE-026
  Category: Bug
  Severity: High
  Why This Is a Problem: Seller/customer targeting logic is incorrect.
  How to Fix: Use user_type__in=['artist','store'] for sellers and customer for customers. Requires code change.

  ISSUE-027
  Category: Bug
  Severity: High
  Problem: Shipping uses line-item tracking updates but model lacks support and API accepts uncontrolled tracking_number input without serializer validation.
  Why This Is a Problem: Runtime failure and unvalidated logistics data.
  How to Fix: Add serializer + model field + constraints (max length/index if needed). Requires code change + migration.

  ISSUE-028
  Category: Bug
  Severity: High
  Problem: api_success/api_error are called with unsupported code keyword in several paths.
  Why This Is a Problem: Runtime TypeError on those response paths.
  How to Fix: Pass error code through api_error only; avoid unsupported kwargs on success helper. Requires code change.

  ISSUE-029
  Category: Config
  Problem: Settings file indicates Django 5.2 generation while dependency pins Django 4.2.13.
  How to Fix: Align framework version and regenerate/validate settings accordingly. Requires config change.
  Category: Config
  Severity: High
  Location: to7fabackend, to7fabackend/settings.py:234-236; INSTALLED_APPS section
  How to Fix: Add rest_framework_simplejwt.token_blacklist app and migrate, or disable blacklist settings. Requires config change + migration.

  ISSUE-031
  Category: Data Model
  Problem: Singleton enforcement for ContentSettings uses non-atomic existence check before save.
  Why This Is a Problem: Race condition can create multiple rows under concurrent writes.
  How to Fix: Enforce singleton with DB constraint (fixed PK row + transaction lock) and migration cleanup. Requires code change + migration + data cleanup.

  ISSUE-032
  Category: Data Model
  Severity: High
  Location: products, products/models.py:421-440; admin_panel, admin_panel/models.py:180-224; admin_panel, admin_panel/content_models.py:38-82
  Problem: Same singleton settings concept exists in three model definitions.
  Why This Is a Problem: Multiple singleton tables with overlapping semantics cause inconsistent reads/writes.
  How to Fix: Keep one canonical settings model and migrate references/data. Requires code change + migration + data cleanup.

  ISSUE-033
  Category: Missing Feature
  Severity: High
  Problem: No real gateway webhook verification/reconciliation despite order and wallet state transitions depending on payment events.
  Why This Is a Problem: Payment/order divergence risk and no external source-of-truth reconciliation.
  How to Fix: Implement signed webhooks, idempotent event handlers, and reconciliation jobs. Requires code change + config change.

  ISSUE-034
  Category: Performance
  Severity: High
  Problem: List endpoints return unpaginated full datasets.
  Why This Is a Problem: Large payloads, DB load spikes, memory pressure, and poor mobile latency.
  How to Fix: Apply pagination with max page size and indexed sort columns. Requires code change.

  ISSUE-035
  Category: Performance
  Severity: High
  Problem: Per-object offer queries in serializer methods create N+1 query patterns.
  Why This Is a Problem: Query explosion on product lists.
  How to Fix: Prefetch/annotate active offer data in queryset and read precomputed fields in serializer. Requires code change.

  ISSUE-036
  Category: Security
  Severity: High
  Problem: Email verification request endpoint reveals account existence (USER_NOT_FOUND).
  Why This Is a Problem: User enumeration vector.
  How to Fix: Return generic success response regardless of account existence. Requires code change.

  ISSUE-037
  Category: Security
  Severity: High
  Problem: Error responses expose raw exception text and optional tracebacks.
  How to Fix: Return generic client-safe errors; log details server-side only. Requires code change.

  ISSUE-038
  Category: Security
  Severity: High
  Problem: Extensive @csrf_exempt usage on authenticated mutable endpoints.
  Why This Is a Problem: If session auth/cookies are ever enabled or reused, CSRF protections are bypassed.
  How to Fix: Remove csrf_exempt from API views and rely on token auth with proper CSRF posture for session-based endpoints only. Requires code change.

  ISSUE-039
  Category: Security
  Severity: High
  Problem: Capability decorator permits unauthenticated pass-through for non-mutating methods and returns custom non-standard error payloads for auth failures.
  Why This Is a Problem: Inconsistent auth contract and bypass-prone policy composition with per-view manual checks.
  How to Fix: Move capability checks into DRF permission classes layered after authentication. Requires code change.

  ISSUE-040
  Category: Security
  Severity: High
  Why This Is a Problem: Unauthorized scraping/intelligence leakage; endpoint policy inconsistency.
  How to Fix: Set explicit AllowAny only if intended and reduce exposed admin metadata, otherwise require auth. Requires code change.

  ISSUE-041
  Category: Security
  Severity: High
  Problem: Pending checkout payload is cached without integrity/signature and may include sensitive order fields.
  Why This Is a Problem: Cache poisoning/tampering risks if cache access is compromised; data confidentiality concerns.
  How to Fix: Store minimal signed reference token instead of raw payload; encrypt/sign sensitive cached blobs. Requires code change + config hardening.

  ISSUE-042
  Category: Architecture
  Severity: Medium
  Problem: Mixed response contracts (api_success/api_error vs raw Response) across similar endpoints.
  Why This Is a Problem: Mobile client integration complexity and inconsistent error handling.
  How to Fix: Standardize all APIs on one response schema middleware/helper. Requires code change.

  ISSUE-043
  Category: Architecture
  Severity: Medium
  Problem: Very large controller files with mixed concerns (admin, seller, public, catalog, ads, moderation).
  Why This Is a Problem: High change-coupling and low testability.
  How to Fix: Split by bounded context and move business logic to service modules. Requires code change.

  ISSUE-044
  Category: Bug
  Severity: Medium
  Problem: top_rated_products orders by -created_at rather than rating metric.
  Why This Is a Problem: Endpoint semantics are incorrect.
  How to Fix: Annotate with average rating and order by it (with tie-breakers). Requires code change.

  ISSUE-045
  Category: Bug
  Severity: Medium
  Problem: Idempotency read-before-lock can race under concurrent identical requests.
  Why This Is a Problem: Potential duplicate execution window before unique constraint conflict.
  How to Fix: Use lock-first strategy or catch IntegrityError and fetch existing transaction deterministically. Requires code change.

  ISSUE-046
  Category: Bug
  Severity: Medium
  Problem: Both signal and serializer create customer profiles for new users.
  Why This Is a Problem: Duplicate profile creation race and unnecessary write churn (partially masked by checks).
  How to Fix: Keep profile creation in one place only (signal or service). Requires code change.

  ISSUE-047
  Category: Bug
  Problem: Guest cart identity depends solely on caller-provided X-Session-ID without server-side ownership verification.
  Why This Is a Problem: Session ID guessing/reuse can expose/modify other guest carts.
  How to Fix: Bind guest cart session to signed server token/cookie and validate ownership. Requires code change.

  ISSUE-048
  Category: Bug
  Severity: Medium
  Problem: Artist/store search endpoints expose emails publicly.
  Why This Is a Problem: PII leakage and scraping risk.
  How to Fix: Remove direct email from public payloads or gate behind authorization. Requires code change.

  ISSUE-049
  Category: Config
  Severity: Medium
  Problem: Redis host/ports for cache/channels are hardcoded, not environment-driven.
  Why This Is a Problem: Deployment inflexibility and accidental environment coupling.
  How to Fix: Move Redis endpoints to env vars with strict validation. Requires config change.

  ISSUE-050
  Category: Config
  Severity: Medium
  Problem: SECURE_SSL_REDIRECT = not DEBUG can break environments behind TLS-terminating proxies if proxy headers are not configured.
  Why This Is a Problem: Redirect loops and availability outages in production.
  How to Fix: Configure SECURE_PROXY_SSL_HEADER and deployment-specific SSL settings. Requires config change.

  ISSUE-051
  Category: Data Model
  Severity: Medium
  Problem: unique_together = ['product', 'seller'] blocks historical multiple requests across time/status.

  ISSUE-052
  Category: Data Model
  Severity: Medium
  Problem: Singleton enforcement via raise ValueError in model save is not database-enforced.
  Why This Is a Problem: Direct DB writes/admin operations can bypass assumptions.
  How to Fix: Enforce unique fixed primary key constraint and transactional lock. Requires code change + migration.

  ISSUE-053
  Category: Missing Feature
  Severity: Medium
  Problem: Payment model methods are mock implementations that mark completed/refunded without gateway checks.
  Why This Is a Problem: False financial state and reconciliation gaps.
  How to Fix: Integrate gateway SDK/API, store provider transaction refs, verify signatures/statuses. Requires code change.

  ISSUE-054
  Category: Missing Feature
  Severity: Medium
  Problem: No explicit shipment tracking entity or status history/audit model for order timeline events.
  Why This Is a Problem: Limited traceability and support operations for disputes/delivery issues.
  How to Fix: Add order event history + shipment tracking models/endpoints. Requires code change + migration.

  ISSUE-055
  Category: Missing Feature
  Severity: Medium
  Problem: No refresh-token revocation/blacklist flow in logout despite rotating refresh tokens.
  Why This Is a Problem: Stolen refresh tokens remain valid until expiry.
  How to Fix: Implement token blacklist/revocation on logout and compromise workflows. Requires code change + migration/config.

  ISSUE-056
  Category: Performance
  Severity: Medium
  Problem: Public catalog endpoints serialize large object graphs with no field-level optimization/selective projections.
  Why This Is a Problem: Increased response size and serializer CPU cost on mobile traffic.
  How to Fix: Use lightweight list serializers and sparse fields for list endpoints. Requires code change.

  ISSUE-057
  Category: Performance
  Severity: Medium
  Location: support, support/contact_views.py:406-410
  How to Fix: Restrict to user=request.user or verified identifiers only, add indexed criteria. Requires code change.

  ISSUE-058
  Category: Performance
  Severity: Medium
  Problem: Pagination parameters are unbounded/unsanitized (limit, offset), enabling heavy queries.
  Why This Is a Problem: Potential DoS through very large page requests.
  How to Fix: Clamp max limits and validate non-negative offsets. Requires code change.

  ISSUE-059
  Category: Security
  Severity: Medium
  Problem: FRONTEND_URL default points to localhost and is used to build security URLs.
  Why This Is a Problem: Misconfiguration can send users to wrong domains/phishing-like reset links.
  How to Fix: Require explicit trusted frontend URL in production; validate allowed host/scheme. Requires config change.

  ISSUE-060
  Category: Security
  Severity: Medium
  Problem: Error responses return raw exception strings on public/support endpoints.
  How to Fix: Return generic user-safe errors; log full details server-side. Requires code change.

  Severity: Medium
  Problem: debug_arabic_encoding is publicly accessible and returns internal sample category/product content.
  Why This Is a Problem: Unnecessary information disclosure endpoint in production API surface.
  How to Fix: Remove endpoint or protect behind staff/debug-only guard. Requires code change + config change.

  ISSUE-062
  Category: Code Quality
  Severity: Medium
  Location: products, products/views.py:1309-1311,1453-1455; custom_auth, custom_auth/address_views.py:29,35; admin_panel, admin_panel/api_views.py (multiple print)
  How to Fix: Replace with structured logger calls and sanitize sensitive fields. Requires code change.

  ISSUE-063
  Category: Code Quality
  Severity: Medium
  Problem: Broad except Exception blocks used widely with mixed response semantics.
  Why This Is a Problem: Masks real errors and complicates observability and safe error handling.
  How to Fix: Catch specific exception classes and centralize exception mapping. Requires code change.

  ISSUE-064
  Category: Code Quality
  Severity: Medium
  Problem: Repeated inline auth/permission checks instead of declarative DRF permission classes.
  Why This Is a Problem: Inconsistent enforcement and maintainability risks.
  How to Fix: Implement dedicated permission classes and reuse consistently. Requires code change.

  ISSUE-065
  Category: Bug
  Severity: Low
  Problem: OTP generation uses token_hex(3)[:6].zfill(6) producing hex characters, not numeric-only OTP.
  Why This Is a Problem: UX mismatch with “6-digit” expectation and client validation assumptions.
  How to Fix: Generate numeric OTP (secrets.randbelow(10**6)). Requires code change.

  ISSUE-066
  Category: Config
  Severity: Low
  Problem: sslserver is included in installed apps unconditionally.
  Why This Is a Problem: Unnecessary dependency/surface in non-development environments.
  How to Fix: Include only in development settings. Requires config change.

  ISSUE-067
  Category: Data Model
  Severity: Low
  ISSUE-068
  Category: Performance
  Severity: Low
  Location: products, products/models.py:170-174
  Problem: average_rating property loads all reviews in Python and sums manually.
  Why This Is a Problem: Inefficient for products with many reviews.
  How to Fix: Use DB aggregation (Avg) and annotate in querysets. Requires code change.

  ISSUE-069
  Category: Security
  Severity: Low
  Location: support, support/contact_models.py:104-111
  Problem: Contact number generation uses repeated random checks without transaction retry/DB-level sequence strategy.
  Why This Is a Problem: Collision race possible under concurrency (rare but real).
  How to Fix: Use DB sequence/unique generator with atomic retry on IntegrityError. Requires code change.

  ISSUE-070
  Category: Code Quality
  Severity: Low
  Location: custom_auth, custom_auth/views.py:130-171; products, products/views.py; payment, payment/views.py
  Problem: Legacy and JWT auth flows coexist with partially disabled/placeholder endpoints and mixed semantics.
  Why This Is a Problem: Increases confusion, dead paths, and accidental client misuse.
  How to Fix: Explicitly deprecate/remove unused legacy endpoints and document one canonical auth flow. Requires code change + API contract cleanup.

  ISSUE-071
  Category: Security
  Severity: High
  Location: Unverified but highly suspicious: admin_panel, admin_panel/api_views.py (multiple seller dashboard/product mutation endpoints under @permission_classes([IsAuthenticated]))
  Problem: Several mutable admin/seller-related endpoints appear to rely only on IsAuthenticated and ad-hoc runtime checks, with inconsistent role validation patterns.
  Why This Is a Problem: Inconsistent role gating can lead to privilege bypass in edge paths not covered by explicit checks.
  How to Fix: Audit each mutable endpoint and enforce explicit role-based permission classes (IsAdminUser / seller-only custom permission). Requires code change.

  ISSUE-072
  Category: Performance
  Severity: Medium
  Location: Unverified but highly suspicious: admin_panel, admin_panel/api_views.py
  Problem: Large response-building loops appear to compute counts/revenue per item without consistent pre-annotation/prefetch.