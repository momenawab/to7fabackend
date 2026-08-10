# TO7FAA Backend — Pre-Rebrand Completeness Audit

**Date:** 2026-08-10
**Scope:** all 11 Django apps in `to7fabackend/`, plus the Flutter↔backend API contract
**Question asked:** *is the backend complete enough to start a rebrand?*

## Verdict

**No — not yet.** The rebrand itself is mostly mechanical (~330 string sites, inventoried in §5).
What blocks you is that **the backend currently does not boot, and its test suite does not run at
all** — so there is no verified signal about what works. Rebranding on top of an unverified
backend means you won't be able to tell a rebrand regression from a pre-existing bug.

Four things must be true before you touch branding:

1. `manage.py check` passes (§1.1)
2. The database schema is reproducible from the repo (§1.4) — **currently it is not**
3. The test suite actually executes (§1.1, §6)
4. The payment app is either implemented or explicitly disabled (§1.2)

Everything else in this report can be fixed during or after the rebrand.

---

## 1. Blockers

### 1.1 The project does not boot — `sslserver` is not installed

`to7fabackend/settings.py:55` lists `'sslserver'` in `INSTALLED_APPS`, but `django-sslserver`
is **not in `requirements.txt` and not installed**.

```
$ ./venv/bin/python3.14 manage.py check
ModuleNotFoundError: No module named 'sslserver'
```

Consequences:

- `manage.py check`, `migrate`, `runserver` — all fail.
- `pytest.ini` sets `DJANGO_SETTINGS_MODULE = to7fabackend.settings`, so **zero tests collect**.
- `settings_production.py` does `from .settings import *`, so **production fails to boot too**.

I verified this is the *only* boot blocker: with `sslserver` filtered out of `INSTALLED_APPS`,
Django starts cleanly and resolves **759 URL patterns**.

**Fix:** delete `'sslserver'` from `INSTALLED_APPS` (it is referenced nowhere else in the
codebase — it was only ever a local HTTPS dev convenience), or add `django-sslserver` to
requirements. Deleting is the better call.

### 1.2 The `payment` app is a stub that reports success

Every endpoint in `payment/views.py` returns a hardcoded success response and does nothing:

```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_payment(request):
    """Process a payment for an order"""
    # This will be implemented with serializers
    return Response({"message": "Payment processed successfully"}, status=200)
```

The same pattern applies to `payment_methods`, `payment_method_detail`, `verify_payment`, and
`refund_payment`. In `payment/models.py`, `Payment.process_payment()` sets `status='completed'`
and flips `order.payment_status = True` **with no gateway call at all**; `refund_payment()`
sets `status='refunded'` and refunds nothing.

These are routed and publicly reachable at **both** `/api/v1/payments/*` and `/api/payments/*`.
A client that calls `/api/v1/payments/process/` gets HTTP 200 `"Payment processed successfully"`
and no payment occurs.

The real money flow appears to live in `wallet/` (which is genuinely solid — see §3) and in
`orders/atomic_order_system.py`. The `payment` app looks like an abandoned parallel design.

**Fix (pick one):** delete the app and unroute it, or gate every endpoint behind `501 Not
Implemented`. Do **not** leave endpoints that claim success. Note `orders.Order.payment_method`
is `CharField(max_length=50)` with **no `choices`** — free-text payment methods, worth
constraining at the same time.

### 1.3 `settings_production.py` is an unfilled template

`to7fabackend/settings_production.py` was scaffolded and never completed:

| Line | Problem |
|---|---|
| 13 | **Hardcoded fallback `SECRET_KEY`** (`django-insecure-q2(^inryyn...`), committed to the repo. This defeats the fail-fast check in `settings.py:31`. The same key signs all JWTs (`SIMPLE_JWT.SIGNING_KEY`), so anyone with repo access can mint valid tokens if the env var is ever unset. |
| 36 | Hardcoded fallback DB password `'strongpass'`. |
| 19–28 | `ALLOWED_HOSTS` contains only localhost/127.0.0.1/0.0.0.0 — **the real domain is missing**, so production would reject every request. |
| 66–70 | `CORS_ALLOWED_ORIGINS = []` — empty, and it *overrides* the validated value from base settings. |
| 73–79 | `CSRF_TRUSTED_ORIGINS` is localhost-only. |
| 60–62 | `SECURE_SSL_REDIRECT` / `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE` commented out. |
| 124 | `DEFAULT_FROM_EMAIL` placeholder `noreply@yourdomain.com`. |

Ironically the *base* `settings.py` is well-hardened — it fail-fasts on missing `SECRET_KEY`,
`CORS_ALLOWED_ORIGINS`, and DB config. `settings_production.py` undoes that. **Fix:** remove
every hardcoded fallback secret and let the base fail-fast do its job.

### 1.4 Migrations are gitignored — the schema is not reproducible

`.gitignore:24-25`:

```
**/migrations/*
!**/migrations/__init__.py
```

Only the 8 `0001_initial.py` files are tracked. **27 migration files exist on disk; 19 of them
are in no repository.** They live only on this machine.

This is the most dangerous finding in the report:

- A fresh clone gets `0001_initial` and nothing else. `makemigrations` will then generate
  *different* migrations with conflicting names on a teammate's machine or in CI.
- Production has never received the migrations added since `0001` except by whatever manual
  process was used — and there is no record of what that was.
- If the rebrand involves a new environment, a new database, or a new server (likely), the schema
  cannot be rebuilt.

**Fix, in this order:** remove those two `.gitignore` lines, `git add` all 27 migration files,
verify `makemigrations --check --dry-run` reports no changes, then confirm the migration state on
the production DB matches (`showmigrations`). Do this **before** anything else that touches models.

---

## 2. Correctness & security gaps (fix before launch, not necessarily before rebrand)

### 2.0 Sellers can approve and feature their own products

`products/serializers.py:141` sets `read_only_fields = ('seller',)`, but the `fields` tuple
includes `approval_status`, `is_active`, **and** `is_featured`. This serializer backs every
seller-writable path — `POST /products/` (`views.py:59`), `POST /seller/products/`
(`views.py:383`), and both `PUT` handlers (`views.py:107`, `views.py:406`).

A seller can therefore `POST {"approval_status": "approved", "is_featured": true}` — or `PUT
{"approval_status": "approved"}` onto a product an admin just rejected — and it is immediately
listed and featured. This defeats the entire product-approval gate.

**Fix:** `read_only_fields = ('seller', 'approval_status', 'rejection_reason', 'is_featured')`,
and expose approval only through the admin endpoints.

*(Found by the `/code-review` pass; I verified it against the source.)*

### 2.1 Logout does not invalidate anything

`settings.py:234-235` sets `ROTATE_REFRESH_TOKENS = True` and `BLACKLIST_AFTER_ROTATION = True`,
but **`rest_framework_simplejwt.token_blacklist` is not in `INSTALLED_APPS`** — so blacklisting
silently does nothing. `custom_auth/jwt_views.py:556` confirms it:

```python
# JWT tokens are stateless - client should discard tokens
# Optionally, add refresh token to blacklist if using SimpleJWT blacklist
logger.info(f"User {request.user.email} logged out")
return api_success(request, message='Successfully logged out', ...)
```

A stolen refresh token stays valid for **7 days after logout**. Fix: add the `token_blacklist`
app, run its migration, and blacklist the refresh token in `logout_view`.

### 2.2 Push notifications are entirely non-functional

- `settings.py:372` points `FCM_SERVICE_ACCOUNT_FILE` at `firebase-service-account.json` — **the
  file does not exist** in the repo.
- `firebase-admin` is **not in `requirements.txt` and not installed**, so
  `FIREBASE_ADMIN_AVAILABLE` in `notifications/push_utils.py:27` is `False`.
- APNs settings (`APNS_KEY_ID`, `APNS_TEAM_ID`, `APNS_KEY_FILE`) all default to empty strings.

The device-registration endpoints work, but nothing is ever delivered. Since the rebrand will
require new Firebase/APNs projects anyway, this is worth sequencing *with* the rebrand.

### 2.3 Redis is a hard dependency with no fallback and no local install

`CACHES` (`settings.py:329`) and `CHANNEL_LAYERS` (`settings.py:317`) are **hardcoded** to
`127.0.0.1:6379` — not read from env, so they cannot be pointed at a production Redis without a
code change. Celery broker/result backend do read env vars.

Redis is not installed on this machine (`redis-cli` not found), which is the true cause of the
`redis.exceptions.ConnectionError` failures filling `Issues.md` — those are **environment noise,
not code defects**. Fix: move both to `os.getenv(...)`, and add a documented local setup.

### 2.4 WebSocket auth passes the JWT in the query string

`support/consumers.py:19` reads the token from `query_string` (`?token=...`). Tokens in URLs end
up in proxy/access logs. Low severity, but worth moving to a subprotocol or first-message auth.

### 2.5 `faq` app is dead code

`faq/` contains **only `models.py`** — no `__init__.py`, no `apps.py`, no migrations. It is not
in `INSTALLED_APPS` and not routed. The `FAQCategory` / `FAQ` / `FAQFeedback` models are
unusable as written. Either complete the app or delete the directory. (If the mobile app is
meant to have an FAQ screen, this is a genuine missing feature, not just cleanup.)

### 2.6 Defects in the recent approval/variant work

A parallel `/code-review` pass over the last commit + working tree surfaced these. I verified the
two highest-impact ones (§1.4, §2.0) directly; the rest are reported as found and are worth
triaging before launch:

| Where | Issue |
|---|---|
| `products/views.py` | Only `product_list` uses `Product.objects.approved()`. `product_detail`, `product_search`, `category_detail`, `latest_offers`, `featured_products`, `top_rated_products`, `product_reviews` still filter on `is_active` alone — a rejected product stays reachable by direct URL and in search. |
| `cart/views.py` | The approval check was added only to `add_to_cart`. `update_cart_item`, `merge_cart`, and `cart_detail` all skip it. |
| `cart/models.py:36,85` | `add_item` validates against `product.stock` (the sum across all variants) while ignoring the `variant_id` — so 10 × size-S passes when only size-M has stock, and fails later at checkout. |
| `products/models.py:233` | `Product.stock` dropped the `combination_stocks` branch with no data backfill; products whose stock lived only there now report `0`. |
| `products/models.py:364` | `Product.clean()` rejects `approved` + `is_active=False`, which the approval doc lists as legitimate ("inactive even if approved"). It is also never called on any API path, since `ProductSerializer.create` uses `objects.create()` rather than `full_clean()`. |
| `products/models.py:124` | A `DeprecationWarning` was pasted onto the *canonical* `ProductCategoryVariantOption.is_in_stock`, telling callers to use the class they are already on. |
| `orders/views.py:87` | `ProductVisibilityError` subclasses `ValueError` and is swallowed by the generic handler, so its `unapproved_products` payload never reaches clients — contradicting the documented contract. |
| `to7fabackend/__init__.py` | The `pymysql.install_as_MySQLdb()` shim was removed while `ENGINE` is still `django.db.backends.mysql` and `requirements.txt` still lists `pymysql`. Works here because `mysqlclient` is installed; breaks on any image where only `pymysql` builds. |

---

## 3. Per-app status

| App | LOC | Status | Notes |
|---|---:|---|---|
| `wallet` | 1,873 | ✅ **Complete** | Genuinely good. `select_for_update()` before every balance read/write, deterministic lock ordering to avoid deadlock, DB-level idempotency keys, side effects outside transactions. Independently verified in `AUDIT_REPORT.md` (2025-12-31); I spot-checked and agree. |
| `orders` | 9,615 | ✅ Substantial | Atomic order system, stock reservation lifecycle, Celery timeout tasks, own design docs. Largest app; untested right now (§4). |
| `products` | 5,919 | ✅ Substantial | Variants, AR sub-app, approval workflow. `views.py` is 975 lines at **19% coverage**. |
| `custom_auth` | 5,545 | ✅ Substantial | JWT, addresses, artist/store profiles, lock/block capability system. See §2.1. |
| `admin_panel` | 8,988 | ✅ Substantial | Dashboard + `/api/admin/` surface (70 routes). |
| `cart` | 1,675 | ⚠️ Mostly | Guest cart + merge-on-login. `merge/` exists in legacy routes but **not in `/api/v1/`**. |
| `notifications` | 1,901 | ⚠️ Partial | CRUD works; **push delivery dead** (§2.2). |
| `support` | 1,656 | ⚠️ Partial | Contact/ticket CRUD + WebSocket consumer. Only 2 legacy URL routes. |
| `api` | 690 | ⚠️ Incomplete | The `/api/v1/` contract — has real gaps (§4.1). |
| `payment` | 163 | ❌ **Stub** | Returns fake success (§1.2). |
| `faq` | 101 | ❌ **Dead** | Not installed, not routed (§2.5). |

---

## 4. The API contract is the biggest structural problem

### 4.1 `/api/v1/` is advertised as primary but the app doesn't use it

`to7fabackend/urls.py` declares `/api/v1/` the "PRIMARY API CONTRACT" and marks the `/api/*`
routes "deprecated". But the Flutter app **hardcodes the deprecated legacy paths** in its
services — `/api/products/`, `/api/cart/`, `/api/orders/`, `/api/wallet/`, `/api/notifications/`,
`/api/addresses/`, `/api/admin/...`.

Meanwhile `lib/core/config/api_config.dart` defines an `ApiEndpoints` class pointing at v1 paths
that is **almost entirely unused — 12 references in the whole app**, nearly all auth. And many
of its constants don't match any real route (`/products/featured/` vs the real
`/featured-products/`, `/wallet/balance/`, `/addresses/default/`, `/reviews/`, `/admin/products/`
…). It is stale dead config that will mislead whoever does the rebrand.

**These endpoints exist in legacy routes but are missing from `/api/v1/`:**

| Missing from v1 | Exists at |
|---|---|
| order `acknowledge/`, `ship/`, `deliver/` | `/api/orders/<pk>/…` |
| `seller/<pk>/status/` | `/api/orders/seller/<pk>/status/` |
| `cart/merge/` | `/api/cart/merge/` |
| `send-otp/`, `verify-otp/` | `/api/auth/api/auth/…` |
| the entire AR sub-app | `/api/products/ar/…` |
| `seller/register/`, `seller/application/status/` | `/api/auth/…` |

**Decide now, before rebranding:** either finish v1 and migrate the app onto it, or drop the v1
pretence and declare the legacy routes the contract. Doing this *during* a rebrand is how you
get untraceable breakage. My recommendation: **freeze v1 work, declare legacy the contract for
now, delete the dead `ApiEndpoints` class**, and revisit versioning after launch.

### 4.2 Confirmed 404s — the app calls routes that do not exist

I enumerated all 759 backend routes and diffed them against every API path in `lib/`. After
discarding false positives (runtime-composed paths), these are real:

| Flutter call site | Path requested | Reality |
|---|---|---|
| `lib/core/services/artist_service.dart:13,35,158,190` | `/api/auth/api/artists/` and `…/<id>/` | **404** — backend only has `top/`, `featured/`, `search/` |
| `lib/core/services/store_service.dart:14,36,172,204` | `/api/auth/api/stores/` and `…/<id>/` | **404** — same |
| `lib/core/config/admin_content_config.dart:55` | `/api/admin/content-settings/` | Path does not exist (backend has `/api/admin/settings/<type>/`) — but **`AdminContentConfig` is never imported anywhere**, so this is dead config, not a live 404. Delete the class. |

The artist/store ones matter: **there is no "list all artists/stores" and no "artist/store
detail" endpoint anywhere in the backend.** `getArtists()` supports search + pagination + a
featured filter against an endpoint that doesn't exist. For a marketplace with artist and store
profile pages, that is a real missing feature, not a typo.

### 4.3 Route sprawl

The same handlers are mounted at up to four prefixes — e.g. login resolves at
`/api/v1/auth/login/`, `/api/auth/api/auth/login/`, `/custom_auth/api/auth/login/`. The
double-nesting (`/api/auth/api/auth/…`) comes from `custom_auth/urls.py` re-declaring an
`api/auth/` prefix inside an include that already adds one. 759 routes for ~11 apps is roughly
3× what this surface needs. Worth collapsing — but *after* the contract decision in §4.1.

---

## 5. Rebrand inventory

The `to7fa` name appears in **~330 files**: 63 in the backend, 266 in Flutter `lib/`, plus
platform config. Grouped by how risky each is to change:

**Safe — cosmetic strings:**
- `custom_auth/jwt_views.py:282,460` — email subjects `"Password Reset - To7fa"`, `"Email Verification - To7fa"`
- `support/contact_admin.py:311-312` — Django admin site header/title
- `admin_panel/api_views.py:626-658` — default site name, `contact@to7fa.com`, `noreply@to7fa.com`, allowed-origins defaults
- `settings.py:357` — `DEFAULT_FROM_EMAIL` default `noreply@to7fa.com`

**Needs coordination — changes runtime behaviour:**
- `settings.py:331` — `CACHES.KEY_PREFIX = 'to7fa_throttle'` (changing it invalidates throttle/cache state; harmless if planned)
- `settings.py:377` — `APNS_BUNDLE_ID` default `com.to7fa.app` — **must** match the new iOS bundle ID
- `settings_production.py:34,48,52,95` — DB name `to7fa_db`, `/var/www/to7fa/{static,media}/`, `/var/log/to7fa/` — these are deployment paths; renaming needs a server-side migration

**Client identity — a full app-identity change, not a find-and-replace:**
- `pubspec.yaml:1` — package `name: to7fa` (this cascades into every `import 'package:to7fa/...'` across all 266 files)
- `android/app/build.gradle.kts:10,26` — `namespace` + `applicationId` = `com.to7fa.app`
- `ios/.../project.pbxproj:483` — `PRODUCT_BUNDLE_IDENTIFIER = com.to7fa.app`
- `android/.../AndroidManifest.xml:30` — `android:label="to7fa"`; `ios/Runner/Info.plist:10` — `CFBundleDisplayName`
- `google-services.json` / `GoogleService-Info.plist` — **must be regenerated** from a new Firebase project; the bundle ID is baked in
- Changing `applicationId`/bundle ID means a **new store listing** — existing installs will not update. Confirm this is intended.

**Decision item — the Django project module is named `to7fabackend`.** Renaming it touches
`manage.py`, `wsgi.py`, `asgi.py`, `celery.py` (`Celery('to7fabackend')`),
`ROOT_URLCONF`, `WSGI_APPLICATION`, `ASGI_APPLICATION`, `DJANGO_SETTINGS_MODULE` in `pytest.ini`,
and every deployment script/systemd unit. **My recommendation: don't.** It is invisible to users
and carries real deployment risk for zero benefit.

**Domain inconsistency to resolve first:** the backend's defaults reference **`to7fa.com`**
(`admin_panel/api_views.py:649`, email defaults) while the Flutter app points at **`to7fa.app`**
(`api_config.dart:19-21`, all three environments identical). Decide the real domain before
rebranding, and note that all three Flutter "environments" currently hit the same production
host — there is no staging isolation.

---

## 6. Test & environment reality

**There is currently no test signal on this backend.** Both the documented failures and my own
run are dominated by environment problems:

| Symptom | Cause | Verdict |
|---|---|---|
| 0 tests collect | `sslserver` missing (§1.1) | **code/config defect** |
| 303 test errors | `Access denied for user 'django_user'@'localhost' to database 'test_to7fa_db'` — the DB user cannot create the test database | environment |
| ~30 `redis.ConnectionError` in `Issues.md` | Redis not installed | environment |
| `Issues.md` coverage ran on Python 3.9.6 | broken venv, see below | environment |

With `sslserver` filtered out, the tests that don't need a DB give: **88 passed, 37 skipped, 1
failed, 303 errors** — and the single failure is also DB-related (a test writing to the live DB
because test-DB creation failed).

**The venv is broken.** `venv/pyvenv.cfg` declares Python 3.14.4, but `venv/bin/python` and
`venv/bin/python3` are **dangling symlinks** into `/Applications/Xcode.app/...`. Only
`venv/bin/python3.14` works. This is why the old coverage report ran on 3.9.6 — and why
`CLAUDE.md` claiming Python 3.14 disagrees with the recorded output.

**`requirements.txt` is incomplete.** Missing: `django-sslserver` (or drop the app),
`pytest` (only `pytest-django` is listed), `firebase-admin`, and **any production server** —
there is no `gunicorn`, `uvicorn`, or `daphne`, despite `channels` requiring an ASGI server.
`CLAUDE.md` also references `ruff`, which is not a dependency (though `.ruff_cache/` exists).

**Setup to fix (server-side, not code):**
```sql
GRANT ALL PRIVILEGES ON `test_to7fa_db`.* TO 'django_user'@'localhost';
```
plus `brew install redis && brew services start redis`. Both belong in a `README`/`docker-compose`
that does not currently exist.

---

## 7. Recommended order of work

**Before the rebrand — do these first:**
1. **Commit the 19 untracked migrations** and un-ignore `migrations/` (§1.4). Nothing else matters if the schema can't be rebuilt.
2. Remove `'sslserver'` from `INSTALLED_APPS`. *(one line; unblocks everything)*
3. Recreate the venv; fix `requirements.txt` (add `pytest`, a production ASGI server, restore the `pymysql` shim or drop the dep; pin what's actually installed).
4. Grant test-DB privileges; install Redis. Write the setup steps down.
5. Run the suite and **record a real baseline**. Without this you cannot attribute rebrand regressions.
6. Close the approval bypass in `ProductSerializer` (§2.0) and extend the approval filter to the remaining read paths (§2.6).
7. Decide §4.1 (v1 vs legacy) and delete the dead `ApiEndpoints` class.
8. Disable or implement the `payment` app (§1.2).
9. Strip the hardcoded `SECRET_KEY` and DB password from `settings_production.py` (§1.3).

**During the rebrand:**
8. Work §5 group by group, cosmetic strings first, client identity last.
9. Regenerate Firebase/APNs credentials — this also fixes §2.2.
10. Fix the domain inconsistency and give staging its own host.

**After launch:**
11. Add `token_blacklist` and make logout real (§2.1).
12. Move Redis config to env vars (§2.3).
13. Add the missing artist/store list + detail endpoints (§4.2).
14. Delete or finish `faq` (§2.5); collapse route sprawl (§4.3).

---

## Appendix — how this was verified

- All 759 URL patterns enumerated by walking the resolved `URLconf` with `sslserver` filtered out.
- Every `/api/...` path string in `lib/` extracted and regex-matched against those patterns;
  reported 404s were then confirmed by reading each Dart call site (candidates that turned out to
  be composed at runtime were discarded).
- `pytest` executed against a settings shim that only removes `sslserver`.
- Findings deduplicated against the existing `AUDIT_REPORT.md`, `STABILIZATION_SUMMARY.md`,
  `Issues.md`, and `codex_issues.md`. The wallet audit's conclusions were spot-checked and stand.
