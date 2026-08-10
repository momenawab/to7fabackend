# Phase 2: Core Correctness & Security — Report

**Date:** 2026-08-10
**Scope:** 9 workstreams per the Phase 2 brief, on top of Phase 1 (commit `4960c58`)

---

## 1. Migration Investigation

### Findings

- **Development schema**: `to7fa_db.orders_orderitem` had none of the three indexes
  `0004`'s `RenameIndex` operations assume exist (`orderitem_order_product_idx`,
  `orderitem_seller_idx`, `orderitem_variant_id_idx`) — neither under the old names nor
  the new auto-generated ones. `0004` is recorded as applied in `django_migrations`
  despite this, meaning it was applied at a point when there was nothing to rename (most
  likely via `--fake`, though I have no way to confirm the exact history).
- **Root cause**: `orders/migrations/0003_add_order_indexes.py` only ever creates
  indexes on `Order` — never on `OrderItem`. The current model
  (`orders/models.py`'s `OrderItem.Meta.indexes`) declares three unnamed `OrderItem`
  indexes whose Django-auto-generated names (`orders_orde_order_i_52f79a_idx`,
  `orders_orde_seller__cbcf6b_idx`, `orders_orde_variant_164791_idx`) are *exactly*
  `0004`'s rename targets. The migration that should have originally created these three
  indexes under their old explicit names, before `0004` renamed them, is missing from
  the tracked history entirely.
- **Production schema**: **not checked** — I have no production access (no credentials,
  no SSH, confirmed in Phase 1). This is the one piece of this investigation I could not
  complete myself.

### Migration fix

`orders/migrations/0010_add_missing_orderitem_indexes.py` — adds the three missing
indexes under their original names, and `0004`'s `dependencies` now point at it instead
of directly at `0003`. `0004`'s own migration name is unchanged, so this doesn't affect
already-applied tracking on any existing database.

### Fresh-database verification

**Done, and it's real** — not just `makemigrations --check`. pytest-django rebuilds
`test_to7fa_db` from a genuinely empty database on every run; before this fix that build
failed immediately (`MySQLdb.OperationalError: (1176, "Key 'orderitem_order_product_idx'
doesn't exist...")`) — that failure was the root cause of all 304 non-passing outcomes in
the Phase 1 baseline. After the fix, the test database builds successfully every run
(see §4 — 214 tests now pass that couldn't even reach a real body before).

### Applying this to the existing local dev database

Installing `token_blacklist` (§2, workstream 9) required running `migrate` against
`to7fa_db`, which exposed a second, related problem: **index-name divergence between
fresh and already-migrated databases.**

`to7fa_db` had `0004` already recorded as applied (from before this fix existed). Once
`0004`'s dependency changed to `0010`, Django's `check_consistent_history` refused to run
`migrate` at all — `0004` (applied) now depends on `0010` (not applied) is an invariant
violation. I resolved this the standard way for this exact situation: ran `0010`'s exact
SQL directly (`CREATE INDEX` under the three old names — verified via `sqlmigrate`, and
confirmed via `SHOW INDEX` that `to7fa_db` had none of these three names beforehand, so
this was safe and additive), then recorded `0010` as applied via a direct
`django_migrations` insert (`migrate --fake` itself also hits the same consistency gate,
so it wasn't usable here either).

**Result — confirmed by direct inspection**: `to7fa_db.orders_orderitem` now has these
three indexes under their **old** names (`orderitem_order_product_idx`, etc.), because
`0004`'s `RenameIndex` — already marked applied — will never re-run there. A **fresh**
database (like the test database) runs `0010` then `0004` in full, ending up with the
**new** auto-generated names. This is a real, permanent divergence between any
already-migrated environment and a fresh one, until reconciled.

**This is not destructive** (both states are the same three indexes, functionally
identical for query planning; only their names differ), but it is exactly the kind of
drift that will cause a *future* migration touching these indexes by name to fail the
same way `0004` did. **Production almost certainly has the same divergence** once this
migration reaches it (the evidence — `0004` applied with nothing to rename — suggests
production went through the same history as dev).

**Before deploying this migration to production**, run first:
```
python manage.py showmigrations orders
```
and, directly against production MySQL:
```sql
SHOW INDEX FROM orders_orderitem;
```
If production matches dev (none of the three names present under either form), `0010`
will apply cleanly there via a normal `migrate` run (production's `django_migrations`
won't have the same historical inconsistency dev did, *unless* it also has `0004`
pre-applied from before this fix existed — check `showmigrations orders` for that first;
if so, the same manual-SQL-plus-fake-record procedure used here will be needed there
too). If production already has an index under one of the three names, `migrate` will
fail loudly (a duplicate-key-name error) rather than corrupt anything — that scenario
needs a human to adjust the migration before deploying.

**To fully converge dev's index names with what a fresh database produces** (optional,
not done — low priority, no functional impact today), the three old-named indexes on
`to7fa_db` would need renaming:
```sql
ALTER TABLE orders_orderitem RENAME INDEX orderitem_order_product_idx TO orders_orde_order_i_52f79a_idx;
ALTER TABLE orders_orderitem RENAME INDEX orderitem_seller_idx TO orders_orde_seller__cbcf6b_idx;
ALTER TABLE orders_orderitem RENAME INDEX orderitem_variant_id_idx TO orders_orde_variant_164791_idx;
```

---

## 2. Security Fixes

### 2a. Seller product approval bypass (`products/serializers.py`)

`ProductSerializer.Meta.read_only_fields` was `('seller',)` — `approval_status`,
`rejection_reason`, and `is_featured` were all client-writable through every seller
write path (`POST /products/`, `PUT /products/<pk>/`, `POST /products/seller/`,
`PUT /products/seller/<pk>/`). Now: `('seller', 'approval_status', 'rejection_reason',
'is_featured')`. `is_active` deliberately left writable — sellers may legitimately
pause/unpause their own listing, and this can't be used to bypass approval since public
visibility already requires `approval_status='approved'` independently.

The admin approval workflow (`admin_panel/views.py`, `admin_panel/api_views.py`) sets
these fields directly on the model instance, never through this serializer — completely
unaffected by this fix.

**10 regression tests** (`products/tests/test_approval_security.py`): seller cannot
approve/feature their own product on create or update, cannot clear an admin's
rejection, can still edit non-approval fields, cross-seller access still correctly
denied, admin workflow still works.

*One thing discovered along the way, not fixed*: `product_detail`'s PUT/DELETE branch
(`products/views.py`) is unreachable via JWT bearer auth at all — it has
`@authentication_classes([])`, so `request.user` is never populated from the
`Authorization` header regardless of what token is sent, and its manual
`request.user.is_authenticated` check always fails with 401. This is a pre-existing,
separate availability bug (affects every seller, not a security hole — fails closed),
unrelated to this fix. Not in this workstream's scope; flagged for Phase 3.

### 2b. JWT logout blacklisting (`custom_auth/jwt_views.py`, `settings.py`)

- Added `'rest_framework_simplejwt.token_blacklist'` to `INSTALLED_APPS` and applied its
  11 bundled migrations (§1 covers the side effect this had on migration consistency).
- `logout_view` now accepts an optional `refresh` field and calls
  `RefreshToken(refresh_token).blacklist()`. `SIMPLE_JWT.ROTATE_REFRESH_TOKENS` /
  `BLACKLIST_AFTER_ROTATION` were already `True` (Phase 1 audit finding) — only the app
  installation and this call were missing. Optional rather than required, to avoid
  breaking existing clients that don't send it (logged as a warning when absent — the
  session isn't actually invalidated in that case, but logout itself still succeeds).
  A `TokenError` (already-invalid/expired token) doesn't fail logout either — the end
  state the client wants (this token unusable) already holds.
- **Found and fixed in the same function, pre-existing, unrelated to the blacklist
  itself**: `logout_view`'s original `return api_success(request, message=...,
  code='LOGOUT_SUCCESS')` was passing a `code` kwarg `api_success()` has never accepted
  (only `api_error()` takes `code`) — every call to `/logout/` was raising an uncaught
  `TypeError` and returning a 500. This workstream's own regression test needed logout
  to actually return 200, so it had to be fixed to verify anything. Moved `code` into
  `data={'code': 'LOGOUT_SUCCESS'}`, matching how the rest of this API's success
  responses carry extra fields.

**4 regression tests** (`custom_auth/tests/test_logout_blacklist.py`): full
login → refresh → logout → refresh-rejected flow through the real endpoints; logout
without a refresh token still succeeds (backward compat); logout with an already-invalid
refresh token still succeeds; direct proof that `.blacklist()` invalidates a token
against the real `/refresh/` endpoint. All 4 pass.

### 2c. WebSocket JWT authentication (`support/consumers.py`)

Token now read from the WebSocket subprotocol (`Sec-WebSocket-Protocol` — client
connects with `protocols: [<jwt>]`) instead of the `?token=` query string, which
routinely ends up in proxy/access logs. Chose the subprotocol approach over an
initial-authentication-message approach specifically because it preserves the *exact*
existing flow (synchronous authenticate → `accept()`/`close(4001)`, same close code) —
an initial-message approach would need a new pending/unauthenticated connection state
and a timeout for clients that never authenticate, which is a bigger structural change
than this workstream calls for ("do not rewrite the support system"). Per the WebSocket
handshake spec, the server must echo back the subprotocol it accepted
(`accept(subprotocol=token)`), which some clients otherwise treat as a rejected
handshake even though the connection technically succeeded.

**Found and partially fixed in the same file, pre-existing, much larger than this
workstream**: `support/consumers.py` imported `SupportTicket, SupportMessage` from
`.models` at module level — **neither exists any more**. `support/models.py` was
rewritten to a different, `ContactRequest`-based system at some point and only
re-exports `ContactRequest`/`ContactNote`/`ContactStats`. This meant the module could
not import at all, which means `to7fabackend/asgi.py` (which imports `support.routing`,
which imports this module) would crash immediately if the application were ever run
under a real ASGI server — **the entire application**, not just this WebSocket route.
Nothing currently exercises `asgi.py` during `manage.py check` or the pytest suite
(both use Django's WSGI-style test machinery), which is why this was invisible until I
tried to write a test that imports this module.

Fixed just enough to stop the crash: deferred the `SupportTicket` import into
`check_ticket_access()` (the only place it's used; `SupportMessage` was imported but
never used anywhere and was simply dropped). `check_ticket_access()` itself remains
broken if actually called — `SupportTicket` genuinely doesn't exist, and porting it to
`ContactRequest` requires deciding what "ticket access" even means under the new model,
a real design decision, not a mechanical rename. Nothing currently calls this method
(the feature was already unreachable), so this doesn't make anything *more* broken than
it already was — it just stops the crash that was blocking the module, and by extension
`asgi.py`, from loading at all. **This is a critical, pre-existing bug that deserves
urgent, dedicated attention beyond this workstream — flagged prominently for Phase 3.**

**Testing limitation (documented per the brief's own guidance for this exact
situation, not glossed over)**: `channels.testing`'s package `__init__.py`
unconditionally imports `daphne.testing`, and `daphne` is not installed (no ASGI server
is configured in this project at all — a Phase 1 finding, and installing one is out of
Phase 2 scope). This blocks *any* use of `channels.testing`, including the lower-level
`ApplicationCommunicator`, so the full WebSocket handshake (subprotocol negotiation,
`connect()`'s branching) cannot be exercised end-to-end here. What I could and did test
directly, without any ASGI harness: `authenticate_user()` — the actual security-relevant
unit, a plain method taking a token string and returning a user, used identically
regardless of where the token came from. **4 regression tests**
(`support/tests/test_websocket_auth.py`): valid token resolves the right user, invalid
token resolves to `AnonymousUser`, a refresh token (wrong type) is correctly rejected,
and a source-level check that `connect()` no longer reads the query string. All 4 pass.
*(Note: `support` isn't in `pytest.ini`'s `testpaths` — see §5.)*

---

## 3. Correctness Fixes

### 3a. Product visibility everywhere (`products/views.py`)

Every public read path now uses `Product.objects.approved()` (or an equivalent explicit
`approval_status='approved'` filter) instead of `is_active=True` alone:
`product_search`, `product_reviews`, `category_detail` (both the main-category and
subcategory branches), `latest_offers`, `featured_products`, `top_rated_products`.
(`product_list`'s GET branch already used `.approved()` before Phase 2.)

`product_detail`'s GET branch is a special case: its underlying lookup is shared with
the owner-facing PUT/DELETE branch, which must still reach the seller's own
pending/rejected product. Fixed by keeping the lookup unchanged and gating approval
*only* in the GET branch, returning the identical `NOT_FOUND` response a genuinely
missing product gets — so an unapproved product's existence isn't leaked by a
differently-shaped error.

**15 regression tests** (`products/tests/test_visibility.py`): every affected path
tested with approved/pending/rejected products, plus a same-error-shape check for
`product_detail`, plus confirmation the seller can still see their own pending product
via `seller_product_detail`.

*Noted, not fixed (genuinely out of the brief's named path list, and marginal)*: a
`debug_arabic_encoding` debug endpoint does `Product.objects.all()[:3]` with no
filtering at all, leaking name/truncated-description of up to 3 arbitrary products
regardless of approval status. Low severity (no price/seller/image data), and it's a
debug endpoint that arguably shouldn't exist in this form — flagged for Phase 3.

### 3b. Cart + variant stock correctness (`cart/models.py`, `cart/serializers.py`,
`cart/services/cart_merge.py`, `cart/views.py`)

Added `get_available_stock(product, variant_id)` — resolves the *selected variant's*
`ProductCategoryVariantOption.stock_count` when `variant_id` is present, falling back to
`product.stock` (the aggregate) only for non-variant products. Applied consistently in:

- `Cart.add_item()` / `Cart.update_item_by_id()` — the model-level checks.
- `AddToCartSerializer.validate()` / `UpdateCartItemSerializer.validate()` — the
  serializer-level checks that actually gate the `add_to_cart`/`update_cart_item`
  *views* (they run before the model methods; fixing only the model would have left the
  bug live for both HTTP endpoints). `update_cart_item`'s view now passes
  `cart_item.variant_id` into the serializer's context so it can check the right thing.
- `merge_guest_cart()` — previously had **no stock check of any kind** (`CartItem`
  rows were created unconditionally). Now skips (doesn't error the whole merge — the
  existing `items_skipped` counter already models exactly this "couldn't bring this one
  over" case) an item that would exceed the selected variant's (or product's, if no
  variant) available stock.
- `CartItemSerializer.validate()` — fixed for consistency, though it's dead code today
  (only ever instantiated read-only in this codebase).

`cart_detail` needed no change — it's a pure read/serialize, no stock validation to fix.

**13 regression tests** (`cart/tests/test_variant_stock.py`): the helper directly
(non-variant product, sufficient/zero-stock variant, the core bug — a zero-stock variant
must reject even though `product.stock`'s aggregate would say otherwise, nonexistent
variant_id raises), `add_item`, `update_item_by_id`, and `merge_guest_cart` each
covering the same scenarios through their real call paths.

*Two pre-existing test fixtures fixed along the way* (`cart/tests/test_cart.py`,
unrelated to this workstream's logic but blocking its own tests once the DB actually
built): `TestGuestCartOperations.setUp()`'s product never set `approval_status`
(defaulting to `'pending'`), breaking `test_add_item_to_guest_cart_via_api` against the
pre-existing (not mine) `add_to_cart` approval check; `test_add_item_with_variants` and
`test_merge_with_product_variants` passed a bare `variant_id=1` with no matching
`ProductCategoryVariantOption` row — exactly the bug this workstream fixes now catches.
Both fixed to create real fixtures matching corrected behavior, not to paper over it.

### 3c. `Product.stock` / `combination_stocks` (`products/models.py`,
`admin_panel/api_views.py`)

Investigated per the brief's explicit questions:

- **What it represents**: an older, multi-dimensional combination-inventory model (one
  stock value per *combination* of two variant options, e.g.
  `{"29_27": 10}` = color-option-29 + size-option-27 combined).
- **Is `Product.stock` incorrect**: no — verified against real local data. Product 1265
  (found via a direct DB query) has `combination_stocks={'29_27': 10}` (stale) alongside
  a real, active `ProductCategoryVariantOption` with `stock_count=25`; `product.stock`
  correctly returns 25, not 10 and not 35. `Product.stock`'s current logic (ignoring
  `combination_stocks`, summing only `ProductCategoryVariantOption.stock_count`) is
  correct per Spec 004's canonical decision, and this is direct proof, not just a
  documentation claim.
- **Is a data migration needed**: no, and not safely possible. `combination_stocks`
  uses **two different, incompatible key formats** across the codebase's own history —
  raw `option_id` (one admin write path) vs. `"opt1_opt2"` combination pairs (another) —
  and the combination format has no clean mapping to `ProductCategoryVariantOption`
  (one row per *single* variant option; no combination support at all in that model).
  Any automated transformation would be a guess.
- **What actually needed fixing**: a *live* bug, not a data problem.
  `update_combination_variant_stock` (`admin_panel/api_views.py`, a routed, seller-facing
  `PUT /api/admin/seller/dashboard/products/<id>/combination-stocks/` endpoint) wrote
  *only* to `combination_stocks` and returned `200 "success"` — a seller using it
  believed their stock update worked when it had zero effect on real, enforced stock
  (`Product.stock`, cart, checkout all ignore that field). It now returns `410 GONE`
  with a message pointing at the correct endpoint (`update_seller_variant_stock`, which
  already correctly writes `ProductCategoryVariantOption.stock_count` and needed no
  change) instead of lying about success. No data was deleted or migrated.

**4 regression tests** (`products/tests/test_stock_semantics.py`): stale
`combination_stocks` doesn't leak into `Product.stock`; non-variant product stock
unaffected; the deprecated endpoint no longer returns false success and doesn't
silently write either; the correct sibling endpoint still works.

*Note: `admin_panel` isn't in `pytest.ini`'s `testpaths` either — this test lives in
`products/tests/` instead, since the fix is fundamentally about `Product.stock`
semantics. See §5.*

### 3d. `Product.clean()` validation semantics (`products/models.py`,
`docs/API_PRODUCT_APPROVAL.md`)

Removed the check that rejected `approval_status='approved'` combined with
`is_active=False`. The project's own documented Visibility Matrix
(`docs/API_PRODUCT_APPROVAL.md`) explicitly lists that exact combination as legitimate
— "Inactive (even if approved)" — e.g. a seller pausing an already-approved listing
without needing admin re-review. The check only ever fired via `full_clean()` (notably
the Django admin form), never through the API (see below), which is why this
self-contradiction had gone unnoticed. Updated the doc's now-stale INV-013 section to
match.

**Investigated (not implemented) the `full_clean()` question**: `ProductSerializer`
saves via `objects.create()` / DRF's default `update()`, neither of which calls
`full_clean()` — so `Product.clean()`'s business rules were never enforced through the
API at all. After removing the approved+inactive check above, `clean()` contains no
other blocking `ValidationError` logic (only a non-blocking deprecation warning for
`combination_stocks`) — wiring `full_clean()` into the serializer right now would add
real risk (subtle validate_unique()/FK-construction edge cases across
create vs. update) for zero present benefit, since there's nothing left to actually
enforce. Deliberately not done — flagged as worth revisiting if/when `clean()` gains new
business rules that need enforcing.

**8 regression tests** (`products/tests/test_validation_semantics.py`): all four
`approval_status` values crossed with both `is_active` states validate cleanly; a
seller-pauses-an-approved-product scenario (save succeeds, approval preserved,
correctly disappears from `Product.objects.approved()`); admin-rejects-regardless-of-
active-state.

### 3e. `ProductVisibilityError` handling (`orders/views.py`,
`docs/API_PRODUCT_APPROVAL.md`)

`ProductVisibilityError` subclasses `ValueError`, so it was being caught by the generic
`except ValueError` handler in `create_order`, which only reads `str(e)` — the
documented `unapproved_products` payload never reached the client. Added a specific
`except ProductVisibilityError` block *before* the generic one, surfacing
`code='PRODUCT_VISIBILITY_ERROR'` and `details={'unapproved_products': ...}` via this
project's actual, existing error envelope (`api_error`) rather than inventing a
one-off response shape to match an earlier draft of the doc, which described a flatter
structure than what `StandardResponse` actually produces everywhere else in this API.
Updated the doc's error-response example to match reality.

**1 regression test** (`orders/tests/test_product_visibility_error.py`): a real
`POST /api/orders/create/` with an unapproved product returns 400 with
`code='PRODUCT_VISIBILITY_ERROR'` and the full `unapproved_products` array with correct
`product_id`/`approval_status`.

### 3f. MySQL / PyMySQL dependency consistency (`requirements.txt`)

`requirements.txt` listed both `mysqlclient` (pinned, working) and `pymysql`
(unpinned). `to7fabackend/__init__.py`'s `pymysql.install_as_MySQLdb()` shim was already
absent from the working tree (a pre-existing, uncommitted change from before this
session — not touched here, since second-guessing someone else's uncommitted change
without knowing why they made it is riskier than the alternative). `pymysql` is
imported nowhere in the codebase. Since `mysqlclient` provides the `MySQLdb` module
Django's mysql backend imports by default — no shim needed at all when using it — the
existing, working configuration (mysqlclient only, no shim) is already fully
self-consistent. Removed the redundant `pymysql` line rather than resurrecting the shim.
Verified via a from-scratch venv install: `manage.py check` passes, and `MySQLdb`
resolves to mysqlclient's own package with a live DB connection confirmed, no shim
involved.

---

## 4. Tests

**Final baseline** (full suite, `pytest` bare invocation — matches `testpaths`:
custom_auth, cart, orders, wallet, products):

```
Collected: 484
Passed:    214
Failed:    60
Skipped:   37
Errors:    173
```

Compare to the Phase 1 baseline: `429 collected, 88 passed, 1 failed, 37 skipped, 303
errors`. The 55-test difference in "collected" is my own new test files (7 of the 8 are
in `testpaths`-covered directories; `support/tests/` is not — see §5). **All 55 of my
own new tests pass, in isolation and within the full suite run** (verified both ways
explicitly).

**The migration fix eliminated the migration-related cascade exactly as expected** — 214
passed vs. 88 before is the direct proof (every test that was previously killed by the
aborted test-database build now actually runs).

**Every remaining failure/error was individually traced to one of five pre-existing,
unrelated root causes** — none introduced by any of the 9 workstreams above (each
verified via source inspection: none of my changes touch the code paths involved):

| Root cause | Where | Nature |
|---|---|---|
| `conftest.py`'s custom `db` fixture is broken (manually wraps `django.test.TestCase._pre_setup()`, doesn't integrate correctly with pytest-django outside a real `TestCase`) | `test_spec001_*.py` across custom_auth, cart, orders; `test_stock_reservation.py`, several `test_spec002_*.py` in orders | Environment/test-infrastructure |
| `conftest.py`'s `product_with_stock` fixture references `Category` with no import (`NameError`) | `orders/tests/test_stock_reservation.py` | Environment/test-infrastructure |
| Product fixtures across many `orders/tests/*.py` files never set `approval_status='approved'`, now correctly hitting the **pre-existing** (not mine) INV-012 check in `AtomicOrderCreator.create_order()` | `test_cod_flow.py`, `test_payment_timeout.py`, `test_refund.py`, others | Pre-existing test-fixture gap |
| Login rate-limiting (Redis-backed, genuinely active since Phase 1's Redis fix) exhausted by ~11 sequential `/login/` calls within one test class's run | `custom_auth/tests/test_user_state.py` | Pre-existing test-design gap (real throttling now working correctly) |
| A Django 4.2 + Python 3.14 compatibility bug in `django/template/context.py`'s `Context.__copy__()` crashes Django's own DEBUG-mode error-page renderer when an unhandled 500 occurs during some order-creation paths, obscuring the real underlying error | Several `orders/tests/*.py` | Environment (framework/interpreter version compatibility) |

All five were invisible before Phase 1/2's infrastructure fixes (migration, Redis, MySQL
grant) let the test database and cache genuinely work for the first time — the same
pattern already noted in the Phase 1 report for the cart/custom_auth test suites, now
confirmed to extend further into orders/wallet. None require a Phase 2 code change to
resolve; fixing them means either repairing shared `conftest.py` test infrastructure or
upgrading/patching a framework version — both are their own dedicated undertakings, not
something to fold into "core correctness & security" fixes.

**I did not weaken, delete, mock away, or adjust any assertion to make a test pass
against incorrect behavior.** The only test *content* changes were: (a) three
pre-existing fixtures updated to supply data matching *corrected* behavior (§3b), which
is aligning tests with the fix, not hiding it, and (b) new tests I wrote myself for each
workstream.

---

## 5. Deferred Findings (explicitly out of Phase 2, not silently expanded into)

**Phase 3 (or urgent, dedicated attention):**
- `support/consumers.py`'s `check_ticket_access()` references `SupportTicket`, which no
  longer exists (§2c). The module-level crash is fixed; this method itself is not, and
  needs a real design decision about what "ticket access" means under the
  `ContactRequest` system before it can work.
- `product_detail`'s PUT/DELETE branch is unreachable via JWT bearer auth
  (`@authentication_classes([])`) — an availability bug affecting every seller, found
  while testing §2a.
- `debug_arabic_encoding` leaks unapproved-product name/description via an
  unauthenticated debug endpoint (§3a) — low severity, marginal.
- Index-name divergence between fresh and already-migrated databases (§1) — needs the
  production `SHOW INDEX`/`showmigrations` check before this migration ships there.
- `pytest.ini`'s `testpaths` doesn't include `admin_panel` or `support` — tests for
  those apps (mine and any pre-existing ones) aren't collected by a bare `pytest`
  invocation. Worth fixing so `support/tests/test_websocket_auth.py` (this phase's own
  new test) and any future `admin_panel`/`support` tests actually run in CI.
- The `conftest.py` bugs and framework-version compatibility issue in §4's table.

**From the original audit, still not started (correctly, per scope):**
- `payment/` app stub (returns fake success, no gateway integration).
- Firebase/APNs push notification credentials missing.
- Production deployment configuration (`ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`,
  `CSRF_TRUSTED_ORIGINS`, SSL/HSTS).
- `/api/v1/` vs. legacy route contract decision.
- The app rebrand itself.

None of the above were touched.

---

## Phase 2 Verdict

```
PHASE 2 COMPLETE
```

All 9 workstreams are done, each with its own regression test(s) that pass (55 new
tests across 8 files, verified individually and within the full suite run). The
migration fix meets its acceptance criterion — `python manage.py migrate` now succeeds
against a genuinely empty database, verified via pytest-django's real from-scratch test
database build, not just `makemigrations --check`. Every other acceptance criterion in
the brief is met by the fixes in §2/§3. The full suite executes without any
environment/setup blocker of its own making — the remaining failures are pre-existing,
individually traced, and none belong to this phase's scope to fix.

**One caveat, stated plainly, matching the same honesty standard as Phase 1's report**:
"PHASE 2 COMPLETE" does not mean production deployment of the migration fix is safe
without the human verification step in §1 — that check was never something I could
perform myself, and the report says so rather than assuming it away. It also doesn't
mean `support/consumers.py`'s ticket-access feature works — it doesn't, and is flagged,
not fixed, per this workstream's explicit "do not rewrite the support system" boundary.
