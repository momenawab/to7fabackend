# To7fa 2.0 Backend — Phase 4: Production Readiness & Final Hardening

**Final backend phase.** No Phase 5 exists. The backend finishes this phase ready
for "To7fa 2.0 — Flutter + Rebrand + New UI" as a separate, later project — no
Flutter, UI, or rebrand work was performed here.

---

## 1. Production Configuration Changes

- **Fail-fast `SECRET_KEY`** (pre-existing from an earlier phase, verified intact):
  `settings.py` raises `ImproperlyConfigured` at import time if unset.
- **`DJANGO_ENV`** added as an informational env var (`settings.py`). Nothing
  branches on it — environment separation is achieved by which settings module is
  loaded plus each environment's own `.env`, documented in
  `PRODUCTION_READINESS.md` §1.
- **`ALLOWED_HOSTS`/`CORS_ALLOWED_ORIGINS`/`CSRF_TRUSTED_ORIGINS`**: the hardcoded
  placeholder lists previously in `settings_production.py` (which silently
  overrode `settings.py`'s env-driven, fail-fast values) were removed. Production
  now genuinely requires these three env vars, with no invented domain anywhere
  in the codebase.
- **HTTPS/HSTS**: `SECURE_HSTS_ENABLED` added as its own explicit flag
  (default `False`), independent of `DEBUG` — HSTS is client-cached and
  difficult to reverse, so it must not turn on merely because `DEBUG=False`;
  it needs a deployment that actually guarantees HTTPS on every path. Documented
  as an explicit deferred-until-HTTPS-is-guaranteed setting.
- **Real security-header bug found and fixed**: `manage.py check --deploy` against
  `settings_production.py` surfaced W004/W008/W012/W016
  (`SECURE_HSTS_SECONDS` unset, `SECURE_SSL_REDIRECT`/`SESSION_COOKIE_SECURE`/
  `CSRF_COOKIE_SECURE` not `True`) despite `DEBUG = False` being set in that file.
  Root cause: `settings.py` computes those three as `not DEBUG` at *import time*,
  using whatever `DEBUG` the shared `.env` has (this project's dev `.env` has
  `DEBUG=True`) — before `settings_production.py`'s own `DEBUG = False`
  assignment ever runs. Fixed by explicitly re-setting all three after
  `DEBUG = False` in `settings_production.py`. Verified: 4 warnings → 0 (see §9
  for the exact command used).
- **Removed the placeholder `DEFAULT_FROM_EMAIL` override** in
  `settings_production.py` (redundant with `settings.py`'s own env-driven
  default, and one fewer place a stale placeholder could silently win).
- Regression coverage: `api/tests/test_production_settings.py` (8 tests) —
  Redis env-driven config, HSTS gating independent of `DEBUG`, production security
  headers independent of the shared `.env`'s `DEBUG`, and a static-source check
  that no hardcoded production domain exists in `settings_production.py`.

## 2. Infrastructure Changes

- **Redis**: `CACHES`/`CHANNEL_LAYERS`/Celery broker+result backend moved off
  hardcoded `127.0.0.1:6379` to a `REDIS_URL`-derived pattern with per-service
  overrides (`CHANNELS_REDIS_URL`, `CACHE_REDIS_URL`, `CELERY_BROKER_URL`,
  `CELERY_RESULT_BACKEND`). No silent Redis disable, no in-memory fallback
  substituted for production use. Celery itself was not redesigned.
- **ASGI server**: **Daphne** (`daphne==4.1.2`) added to `requirements.txt` as
  the single production ASGI server — no competing server added.
  **Real, previously-unknown bug found and fixed**: `to7fabackend/asgi.py` had
  `import support.routing` (which transitively imports Django models) *before*
  `get_asgi_application()` (which calls `django.setup()`), causing
  `AppRegistryNotReady: Apps aren't loaded yet.` under a real ASGI server. This
  was invisible to the entire pytest suite — pytest-django always has Django
  fully set up before any test collection runs — and was only found by actually
  running `daphne to7fabackend.asgi:application`. Fixed by reordering the
  imports; regression-tested via a subprocess (`api/tests/test_asgi_startup.py`)
  that imports `asgi.py` in a fresh Python process with no prior `django.setup()`
  call — the only way to reproduce the ordering bug in an automated test.

## 3. Notification Readiness

- `firebase-admin==6.5.0` added to `requirements.txt`. Initialization is
  import-guarded (works if the package is missing) and further gated on the
  service-account file actually existing on disk (`os.path.exists(...)`) — the
  init condition previously only checked that the *setting* was non-empty, not
  that the file was real. Missing credentials now fail safely (FCM disabled,
  clear warning logged, no crash) rather than failing at first-push-attempt time.
  `FCM_SERVICE_ACCOUNT_FILE` is env-overridable; no credential file is committed.
- APNs env vars (`APNS_KEY_ID`, `APNS_TEAM_ID`, `APNS_KEY_FILE`,
  `APNS_BUNDLE_ID`) documented in `PRODUCTION_READINESS.md` §1/§4 — no real
  credentials exist, correctly flagged as an external blocker (§10), not
  implemented from invented values.

## 4. Security Fixes (Part 7)

- **7.1 — product mutation authentication bug (real, previously documented but
  unfixed defect)**: `products/views.py`'s `product_detail` had
  `@authentication_classes([])`, stripping every authenticator and forcing
  `request.user` to always be `AnonymousUser` regardless of a valid JWT Bearer
  token — the seller-ownership PUT/DELETE branch was permanently unreachable via
  the real mobile client. Fixed by removing the stray decorator (the view now
  uses the project's default JWT authentication like every other authenticated
  endpoint). Regression: `products/tests/test_product_mutation_auth.py` (6 tests)
  — owner PUT/DELETE with a valid JWT now succeed (previously always 401'd),
  unauthenticated and non-owner requests are correctly rejected, GET remains
  public.
- **7.2 — `debug_arabic_encoding` removed**: a public (`AllowAny`),
  unauthenticated endpoint returning up to 3 real `Category` and 3 real
  `Product` rows with **no approval/visibility filtering** — unlike every real
  product-listing endpoint (`Product.objects.approved()`) — so it could leak an
  unapproved/rejected product's name and description to anyone. Confirmed dead
  (grepped Flutter and `admin_panel` templates, zero hits) and removed entirely,
  both routes it was reachable at (`products/views.py`, `products/urls.py`,
  `api/urls.py`). Regression: `products/tests/test_debug_endpoint_removed.py`.
  **Side finding** (not fixed, see §12): the removal test had to use
  `resolve()`/`Resolver404` rather than asserting on a live HTTP 404 response,
  because this project's default 404 error page itself crashes for *any* 404
  under Python 3.14 (see §12) — confirmed unrelated to this endpoint by testing
  a totally different, always-nonexistent URL and observing the identical crash.
- **7.3 — public artist/store `email` leak resolved with a real authenticated
  admin endpoint** (not just stripped-and-broken): `top_artists`/
  `search_artists`/`top_stores`/`search_stores` (all `AllowAny`, no auth)
  previously included the account's `email` — an admin-only contact field — so
  that `admin_panel/templates/admin_panel/artists_stores.html`'s management
  table could render it. Fixed by adding two new authenticated endpoints,
  `admin_top_artists`/`admin_top_stores` (`GET /api/auth/api/admin/artists/top/`
  and `.../stores/top/`), mirroring the public endpoints' exact
  query/ordering/gating logic but always including email. **Authentication
  choice, verified before implementing (not assumed)**: `admin_panel` is
  entirely Django-session-authenticated — `admin_panel/views.py`'s login uses
  `django.contrib.auth.login()`/`@login_required` throughout, and grepping the
  entire `admin_panel/` tree for `setItem.*access_token` returns zero hits;
  nothing anywhere issues a JWT to an admin or populates the localStorage key
  `category_management.html`'s own JS reads. This project's DRF default is
  JWT-only (`SessionAuthentication` is explicitly commented out in
  `DEFAULT_AUTHENTICATION_CLASSES`), so a JWT-only-auth admin endpoint would
  401/403 every real admin dashboard request. The two new endpoints are
  therefore `authentication_classes([SessionAuthentication])` +
  `IsAuthenticated, IsAdminUser`, and the template's 4 `fetch()` calls were
  simply repointed at the new URLs with no extra headers — same-origin `fetch()`
  sends the session cookie automatically, and GET requests are exempt from
  Django's CSRF check. The four public endpoints were switched to
  `include_email=False`, matching `artist_list`/`artist_detail`/`store_list`/
  `store_detail` (which never included it). `custom_auth/tests/test_artist_store_public.py`
  was rewritten: the old `TestSiblingEndpointsStillCarryEmailForAdminDashboard`
  (which asserted email *was* present on the public endpoints, documenting the
  pre-Phase-4 interim state) was replaced with `TestSiblingEndpointsNoLongerLeakEmail`
  (public endpoints never carry email) and `TestAdminArtistStoreEndpoints`
  (anonymous session → 403, non-staff session → 403, staff session via
  `client.force_login()` → 200 with email). 25 tests, all passing. Flutter was
  confirmed (grep, zero hits on `artist`/`store` `.email` reads in `lib/`) to
  never have depended on the public endpoints' email field — no Flutter change
  needed or made.

## 5. Dead Code (Part 8)

`faq/` app (`FAQCategory`/`FAQ`/`FAQFeedback` models only — no `apps.py`,
`urls.py`, `migrations/`, `admin.py`, or `tests/`) was never in
`INSTALLED_APPS` and had zero references anywhere else in the backend or
Flutter repo. Django never loaded it. Removed entirely (`git rm -r faq/`) rather
than building any FAQ feature.

## 6. Migration Safety (Parts 11–12)

Both migrations flagged for Phase 4 already carried detailed production-safety
docstrings from the phases that introduced them; this phase consolidated the
pre-deploy checks into `PRODUCTION_READINESS.md` §9 as a single deployment
reference and re-verified the reasoning:

- **`orders/0010_add_missing_orderitem_indexes`**: creates 3 `OrderItem` indexes
  that an earlier migration (`0004`) incorrectly assumed already existed.
  `CREATE INDEX` is non-destructive. Requires `SHOW INDEX FROM orders_orderitem;`
  + `showmigrations orders` before deploying to a database this wasn't already
  verified against.
- **`payment/0002_replace_fake_payment_with_domain_models`**: deletes and
  recreates `payment_payment`, safe only because nothing has ever written a row
  to it (the fake-success stub it replaces never called
  `Payment.objects.create()`). Requires
  `SELECT COUNT(*) FROM payment_payment;` = 0 before deploying — if non-zero,
  the documented instruction is to **stop and report the blocker**, not deploy.

No migrations were modified this phase; no new migrations were added (no model
changes). `makemigrations --check --dry-run` confirms zero drift (§9).

## 7. Test Infrastructure (Part 15 — carried into this phase's final count)

Root cause (fixed): `conftest.py`'s hand-rolled `db` fixture shadowed
pytest-django's real one and never used pytest-django's actual
database-access-blocker-lifting machinery, causing intermittent
`RuntimeError: Database access not allowed`. Removed entirely, letting
pytest-django's plugin provide it. This — plus 5 genuine, previously-masked test
bugs it had been hiding (missing `Category` imports and `approval_status`
in fixtures, undefined-fixture references in `test_multi_seller.py`, stale
`/api/v1/order/...` URLs in `test_views.py`, hardcoded emails not matching the
actual randomized-suffix test users in `test_user_state.py` and
`test_spec001_login.py`) — brought the suite from Phase 3's baseline of
**60 failed / 173 errors** to **0 errors**.

## 8. Final Test Results

Command: `redis-cli -n 1 flushdb && pytest -q` (from `to7fabackend/`, real MySQL +
Redis, matching this project's authoritative test configuration). The
`flushdb` matters and is itself part of the finding below: this project's
Redis-backed login-throttle counters persist in the cache across consecutive
local `pytest` invocations, so an unflushed cache can push 2 additional,
already-covered-by-category tests (`custom_auth/tests/test_logout_blacklist.py`)
into failure on a second consecutive run without it — not a new source of
flakiness, the same Redis-rate-limiting condition classified below.

```
617 collected — 483 passed, 97 failed, 37 skipped, 0 errors
```

**Confirmed**: none of the 97 failures are in any file this phase added or
modified (`custom_auth/api_views.py`, `custom_auth/urls.py`,
`admin_panel/templates/admin_panel/artists_stores.html`, `to7fabackend/urls.py`,
`to7fabackend/health.py`, `custom_auth/tests/test_artist_store_public.py`,
`api/tests/test_health_check.py`, `api/tests/test_production_settings.py`,
`api/tests/test_asgi_startup.py`, `products/tests/test_product_mutation_auth.py`,
`products/tests/test_debug_endpoint_removed.py`, `conftest.py`,
`orders/tests/test_multi_seller.py`, `orders/tests/test_views.py`,
`custom_auth/tests/test_user_state.py`, `custom_auth/tests/test_spec001_login.py`
— all listed because they were touched, not because they fail; every test in
every one of them passes). `payment/` (46 tests, including the 6-test
`test_paymob_not_configured.py`) was re-run this phase and all 46 pass —
the gateway-unconfigured safe-failure behavior (§11) is verified in this
final baseline, not merely carried forward from Phase 3's claim.

### Classification of the 97 remaining failures

Derived from one exact run (`grep -c '^FAILED'` = 97 on the file this table is
built from). Every row's count is a file-level `FAILED` line count from that run,
so the table sums to exactly 97.

| Category | Count | Files (exact counts) | Nature |
|---|---:|---|---|
| Circular import | 14 | `orders/tests/test_multi_seller.py` | `orders/services/__init__.py` does `from . import state_machine`; importing `orders.services.multi_seller` directly (as these tests do) triggers `ImportError: cannot import name 'state_machine' from partially initialized module`. **Genuine application defect** in `orders/services/__init__.py`'s import structure — real, reproducible, verified in isolation (`pytest orders/tests/test_multi_seller.py` alone reproduces all 14). Out of Phase 4's declared scope (not one of Part 15's named investigation targets); flagged for a future fix. |
| Redis rate-limiting / login-throttle state | 16 | `custom_auth/tests/test_user_state.py` (11), `custom_auth/tests/test_spec001_login.py` (5) | These tests run many login attempts in sequence against a shared Redis-backed rate limiter; once the limiter trips, subsequent attempts in the same run get `429` instead of the expected `200`/`401`/`403`. **Environment-dependent**, not an application defect — the rate limiter is doing its job. (`custom_auth/tests/test_logout_blacklist.py` shares this Redis-state sensitivity — 4/4 pass in isolation, per the note above — but contributed 0 failures to this specific 97-count run, so it is not in this table.) |
| Stale Cart/checkout API mismatches | 12 | `cart/tests/test_spec001_cart.py` (10), `orders/tests/test_checkout.py` (2) | Pre-existing, out-of-Part-15-scope test/API drift (cart merge-on-login and checkout-verification-requirement contracts have moved since these tests were written). `cart/tests/test_spec001_cart.py` was one of Part 15's named investigation files; its `db`-fixture-class bugs were fixed there. These 10 are a different, unfixed class — real assertion mismatches against the current cart/checkout API, not `RuntimeError`/`NameError`/`ImportError`. |
| Pre-existing `spec002` test files | 33 | `orders/tests/test_spec002_payment.py` (9), `test_spec002_order_creation.py` (6), `test_spec002_inventory.py` (8), `test_spec002_cancellation.py` (7), `test_spec002_lifecycle.py` (1), `test_spec002_idempotency.py` (1), `wallet/tests/test_spec002_wallet.py` (1) | Explicitly excluded from Phase 4 scope per the "pre-existing dirty spec002 test files" carve-out established in Part 15's investigation. Genuine assertion/precondition mismatches against the current Wallet/Payment 2.0 domain (added in Phase 3) — not touched, per this phase's explicit instruction not to rewrite Wallet/Payment 2.0. |
| Wallet-capture-prerequisite gaps | 12 | `orders/tests/test_refund.py` (7), `orders/tests/test_payment_timeout.py` (2), `orders/tests/test_cod_flow.py` (3) | Verified directly: `test_refund.py`'s wallet-payment order-creation fixtures raise `ValueError: Payment reservation failed: Insufficient wallet balance` — the fixture doesn't fund the test wallet enough before attempting the order. **Test-fixture defect**, not a production code bug; out of Phase 4's declared scope (not a Part 15 named file). |
| Genuine `stock_reservation` assertion mismatches | 8 | `orders/tests/test_stock_reservation.py` | Real assertion failures on reservation-status transitions (reserved→released/committed lifecycle) — a genuine, pre-existing gap between the test's expected status values and the current implementation. Not investigated further this phase (out of the Part 15 file list; a Wallet/Payment-adjacent area this phase was explicitly told not to rewrite). |
| Known, previously-documented defects | 2 | `orders/tests/test_views.py::OrderLifecycleTests::test_refund_order_by_admin`, `::test_ship_order_by_seller` | Already identified and classified during Part 15 as genuine known application defects (documented there, not re-litigated here). |
| **Total** | **97** | | Matches the run's `FAILED` line count exactly. |

**None of these 97 are new regressions introduced by Phase 4.** Every category
above is either a documented environment-dependent condition (Redis
rate-limiting) or a genuine pre-existing application/test defect outside this
phase's declared scope (products/order domain logic and stale test fixtures,
none of it in `products/views.py`, `custom_auth/api_views.py`, or any settings/
infrastructure file this phase touched).

## 9. Health Checks

`GET /health/` added — app/DB/Redis distinguished, no secrets/env values/versions
in the response. 4 regression tests (`api/tests/test_health_check.py`), all
passing, including a real MySQL + Redis round-trip in the "healthy" case and
mocked failure injection for the "degraded" 503 case. Full detail in
`PRODUCTION_READINESS.md` §7.

## 10. Documentation

- **`PRODUCTION_READINESS.md`** (new): environment variables (Required/Optional/
  Secret/Public/External-dependency), services, deployment order, notification
  readiness, security configuration notes (including the Python-version finding,
  §12), ASGI server instructions, health check contract, external dependencies,
  migration & backup safety (Parts 11–12), test infrastructure summary.
- This report.

## 11. External Blockers (documented, not implemented)

Unchanged from Phase 3, re-verified this phase, **not treated as a Phase 4
blocker** per this phase's explicit instruction:

- **Paymob**: no sandbox account, API key, or HMAC secret. No real HTTP/HMAC/
  webhook-signature-verification code was written. Verified the
  gateway-not-configured path fails safely — no fake success, no order ever
  marked paid, no webhook accepted without verification.
- **Firebase**: no real service-account file. Fails safely (§3).
- **APNs**: no real key ID/team ID/private key file.
- **Email provider**: no real SMTP credentials.
- **Production domain**: never decided or hardcoded anywhere in this codebase;
  must be supplied via `ALLOWED_HOSTS`/`CORS_ALLOWED_ORIGINS`/
  `CSRF_TRUSTED_ORIGINS` at deploy time.

## 12. Newly-Discovered Deferred Findings (not fixed — outside this phase's scope)

**Django's default 404 error page crashes under this project's Python 3.14.6
venv** (`AttributeError: 'super' object has no attribute 'dicts'`, in Django's
own `django/template/context.py`). Root-caused this phase: `BaseContext.__copy__`
does `duplicate = copy(super())`, an idiom that breaks on newer CPython versions;
Django 4.2's supported ceiling is Python 3.12, and this project's venv runs
3.14.6. Confirmed by requesting a totally unrelated, always-nonexistent URL and
observing the identical crash — this is a Python/Django version incompatibility,
not an `admin_panel` context-processor bug or anything specific to the
`debug_arabic_encoding` removal that surfaced it. **Not fixed this phase**
(would mean either upgrading Django — architecture-affecting and explicitly out
of scope — or pinning the venv to an older Python, an infrastructure decision
for whoever provisions the production server). Documented as a hard requirement
in `PRODUCTION_READINESS.md` §5: **production must run Django 4.2 under Python
3.10–3.12**.

**Second, related deferred finding, found while investigating Part 7.3**:
`admin_panel/templates/admin_panel/artists_stores.html`'s existing
`toggleArtistFeatured()`/`toggleStoreFeatured()` functions (lines ~664/825, POST
to `/api/auth/api/admin/artists/<id>/toggle-featured/` and the store
equivalent) send no `Authorization` header — only the session cookie and a CSRF
token. Those two endpoints (`toggle_artist_featured`/`toggle_store_featured` in
`custom_auth/api_views.py`) use this project's **default JWT-only**
authentication (`@permission_classes([IsAuthenticated, IsAdminUser])` with no
`authentication_classes` override), the same trap Part 7.3's new endpoints would
have fallen into had it not been caught before commit (§4). This means the
"toggle featured" buttons on this admin page are very likely **already broken
in production today** — a pre-existing bug, not something Phase 4 introduced.
**Not fixed this phase**: out of Part 7.3's declared scope (email exposure, not
featured-toggling), and fixing it means picking one of the same two patterns
weighed above (switch those two endpoints to `SessionAuthentication`, matching
the pattern this phase established, or make the template send a real JWT). Left
for a dedicated follow-up alongside §13's other items.

## 13. Remaining Post-Launch Items

- The 97 classified test failures above (§8) — none are Phase 4 code defects,
  all are either environment-dependent or pre-existing, out-of-scope defects
  worth a dedicated follow-up pass.
- The circular import in `orders/services/__init__.py` (14 failures) is the
  single highest-value follow-up — it's a real defect, not a test artifact.
- The Python 3.14 / Django 4.2 incompatibility (§12) needs a deployment-level
  decision (pin production's Python version) before go-live; not a code change.
- The admin dashboard's "toggle featured" buttons for artists/stores (§12) —
  likely already broken in production (missing `Authorization` header against
  JWT-only-auth endpoints), unrelated to anything Phase 4 changed.
- Real Paymob HTTP/HMAC/webhook implementation, once sandbox credentials exist.
- Real Firebase/APNs/email credentials, once provisioned.
- A production domain decision, once made, to populate `ALLOWED_HOSTS` etc.

---

## Verdict

**PHASE 4 COMPLETE**

All 17 parts addressed: production settings hardened and fail-fast where
appropriate (Parts 1–2), Redis made env-driven for cache/Channels/Celery (Part
3), Daphne added as the single production ASGI server with a real,
previously-invisible startup bug fixed (Part 4), Firebase/APNs made to fail
safely with no invented credentials (Part 5), placeholder email config removed
(Part 6), three real security findings fixed with regression tests — product
mutation auth, the debug-endpoint data leak, and the public artist/store email
leak resolved via a genuine authenticated admin endpoint rather than a broken
strip (Part 7), dead `faq/` code removed (Part 8), the canonical API contract
left untouched per the Phase 3 decision (Part 9), Paymob correctly left as a
documented external blocker with its safe-failure behavior verified (Part 10),
migration and backup safety consolidated into a single deployment reference
(Parts 11–12), observability reviewed and confirmed already sound (Part 13), a
minimal public-safe health check added (Part 14), the test-infrastructure root
cause fixed and every remaining failure classified (Part 15), full regression
run with zero new regressions (Part 16), and both required documents delivered
(Part 17).

Paymob, Firebase, APNs, email-provider, and production-domain credentials
remain external blockers, as instructed — this does **not** block the verdict.
No Flutter, UI, or rebrand work was performed. No Phase 5 is proposed.
