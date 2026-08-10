# Phase 3: API Contract & Payment 2.0 — Report

**Branch:** `005-variant-system-implementation` · **Built on:** Phase 1 (`4960c58`), Phase 2 (`c0ba23e`)

## 1. API Contract

### Canonical API
```text
Canonical API: legacy /api/... per-app prefixes (e.g. /api/products/, /api/orders/, /api/auth/...)
```
**Evidence, not assumption.** Every one of the 22 Flutter service files in
`lib/core/services/*.dart` hardcodes a legacy `/api/...` path literal (`ApiConfig.baseUrl +
'/api/products/'`, etc.) — 25 files reference `ApiConfig.*`, only one (`auth_service.dart`)
references the dead `ApiEndpoints` class at all, and only for auth routes via `getAuthUrl()`.
`/api/v1/` (`api/urls.py`) is comprehensive — it mirrors almost the entire legacy surface — but
nothing in the shipped client ever calls it. This matches the prior audit's recommendation
exactly, so Phase 3 followed it rather than migrating anything.

```text
Deprecated / legacy routes:
/api/v1/... — frozen, not deleted. Stays fully routed (this suite's own Phase 2 tests hit
  /api/v1/auth/login/) for whatever may already depend on it, but receives no new Phase 3
  routes (the two Artist/Store list+detail additions and the payment webhook only exist under
  the legacy prefix — see below).
/api/auth/api/auth/... (and /api/auth/api/artists/..., /api/auth/api/stores/...) — an ugly
  double-nested path produced by custom_auth.urls being mounted at 'api/auth/' while its own
  paths already start with 'api/auth/'/'api/artists/'/'api/stores/'. Confirmed LIVE, not dead:
  Flutter's own source comment (lib/core/config/api_config.dart:107, "JWT login at
  /api/auth/api/auth/login/") and its ArtistService/StoreService
  (_artistsEndpoint = '/api/auth/api/artists/') both target it directly. Left untouched -
  collapsing it would need a coordinated Flutter change, out of scope for a backend-only phase.
```

### Routes added
Confirmed-404 sweep: extracted every hardcoded endpoint literal from `lib/core/services/*.dart`
and `lib/services/*.dart`, resolved each against Django's real URL resolver (not just read from
`urls.py`). Four were genuine 404s, all in the same feature area:

| Route | Flutter caller | Fix |
|---|---|---|
| `GET /api/auth/api/artists/` | `ArtistService.getArtists()` / `.searchArtists()` | New `artist_list` view — paginated (DRF `PageNumberPagination`), `featured`/`search` query params, verified-only |
| `GET /api/auth/api/artists/<id>/` | `ArtistService.getArtistById()` | New `artist_detail` view |
| `GET /api/auth/api/stores/` | `StoreService` (mirrors ArtistService) | New `store_list` view |
| `GET /api/auth/api/stores/<id>/` | `StoreService` | New `store_detail` view |

19 regression tests in `custom_auth/tests/test_artist_store_public.py`, each asserting the
*exact* route Flutter calls now resolves (not just "a" route).

**Adjacent finding, partially fixed:** `top_artists`, `featured_artists`, `search_artists`,
`top_stores`, `search_stores` — all pre-existing, all `AllowAny`/no-auth — put `user.email`
(and, for stores, `tax_id`) directly in the response body. Nothing in Flutter's `Artist`/`Store`
models ever reads `email`, so the two brand-new endpoints this workstream adds
(`artist_list`/`artist_detail`/`store_list`/`store_detail`) never include it — verified via a
regression test, not just omitted by construction.

The four *pre-existing* functions were tried with the same strip, then reverted: grepping
`admin_panel/templates/` (the same check already done before removing the dead `/custom_auth/`
mount, just applied here too on a second pass after an advisor review caught the gap) showed
`admin_panel/templates/admin_panel/artists_stores.html`'s own JS
(`artist.email`/`store.email`) genuinely renders it, reading it from these exact endpoints, for
the admin dashboard's use in identifying/contacting artists and stores. Stripping it would have
broken a real, currently-working admin feature, confirmed by reading the template rather than
assumed. `tax_id` was never read there (grepped for it too) and stays stripped everywhere.

This leaves a genuine, flagged tension: an `AllowAny`/no-auth endpoint still carries an
admin-only field, because the admin dashboard happens to reuse the same public endpoint rather
than having its own authenticated one. The correct fix — a separate authenticated admin
endpoint for `artists_stores.html` to call instead — is real Phase 4 work, not done here (it's
outside "add list/detail", the actual scope of this workstream). Regression tests assert the
two new endpoints never include `email`, and separately assert the four pre-existing ones still
do (locking in the current, imperfect-but-non-regressing state so a future phase can't
accidentally re-break the admin dashboard while eventually fixing this properly).

### Routes removed
`path('custom_auth/', include('custom_auth.urls'))` in `to7fabackend/urls.py` — a second mount
of the same urlconf under the raw Django app name. Confirmed dead before removal:
`grep -rn "custom_auth/" lib/ admin_panel/templates/` — zero hits in Flutter or the admin
templates. The `api/auth/` mount (the live one) is untouched. Regression test confirms
`/custom_auth/register/` now 404s while `/api/auth/register/` still resolves.

### Remaining contract gaps, reviewed per item
| Named gap | Status |
|---|---|
| `order acknowledge/ship/deliver/` | Already existed (`orders/urls.py`), already exposed under `/api/orders/<pk>/{acknowledge,ship,deliver}/`. Confirmed via `resolve()`, not assumed. |
| `seller/<pk>/status/` | Already exists at `/api/orders/seller/<pk>/status/`. |
| `cart/merge/` | Already exists at `/api/cart/merge/` (`cart.views.merge_cart`). |
| `send-otp/`, `verify-otp/` | Already exist at `/api/auth/api/auth/send-otp/` and `.../verify-otp/` (same double-nesting as login, same reason it's left alone). |
| AR endpoints | Already exist under `/api/products/ar/...` (`products/ar_urls.py`), fully implemented (settings, frame combinations, preview sessions, analytics) — legacy-only, never wired into `/api/v1/`, consistent with the freeze-v1 decision. |
| `seller/register/`, `seller/application/status/` | Already exist at `/api/auth/seller/register/` and `/api/auth/seller/application/status/`. |
| `AdminContentConfig` (Flutter) → `/api/admin/content-settings/` | Confirmed dead: `admin_content_service.dart` (the code that actually runs) calls `/api/products/content-settings/`, which exists and works; `AdminContentConfig`'s `content_settings` entry pointing at `/api/admin/content-settings/` is unused dead Flutter config, matching the audit's description exactly. No backend route created for it — would be a fake endpoint satisfying dead code, explicitly forbidden by the brief. |

Every item in the brief's gap list turned out to already exist under the legacy contract; none
needed a new handler, only (for artist/store) genuinely new ones as documented above.

### Route sprawl (workstream 7)
Did not attempt the full 774-route collapse (out of scope). Did: remove the one confirmed-dead
duplicate mount (above), and add 25 regression tests (`api/tests/test_contract_routes.py`)
locking in the canonical-vs-frozen-v1 decision so a future phase can safely continue the
cleanup without re-litigating what's live.

## 2. Payment

```text
Gateway selected: Paymob (confirmed by product owner during this phase)
Gateway configuration: NONE present anywhere in the repository or environment
```
Verified, not assumed: grepped `to7fabackend/settings*.py`, `.env`, `.auto-claude/.env`,
`requirements.txt`, `specs/`, `docs/` for `paymob`/`gateway`/known-provider names — zero hits.
The brief's acceptance gate is conjunctive ("known **and** configured"); knowing the name does
not satisfy it.

```text
Integration: BLOCKED — see "Gateway Blocker" at the end of this report.
```

**What was built anyway** — the gateway-agnostic domain, wired end-to-end and fully tested with
a mocked gateway, ready for a single adapter implementation once real Paymob credentials exist:

### Payment architecture
```text
Order (existing, untouched)
  → Payment (payment/models.py)          — one per order; amount snapshotted from
                                            Order.total_amount at creation, server-side only
      → PaymentAttempt                   — one per try; retries create a new attempt under
                                            the same Payment, not a new Payment
          → GatewayTransaction           — the gateway's own record of money actually moving
      → Refund                            — against a Payment, gateway-confirmed
WebhookEvent                              — every inbound delivery, valid or not (audit +
                                            idempotency)
```
Deliberately does **not** touch `orders/atomic_order_system.py` or wallet's
`WalletOrderCoordinator` (the existing `orders/views.py` `capture_payment`/`release_payment`
already delegate to it) — that's the wallet/COD payment path, unaffected by this phase's "do NOT
rewrite Wallet" rule. `PaymentService` integrates with `Order` only at its public field
boundary (`order.total_amount`, `order.status`, `order.payment_status`), the same shape those
existing flows already use.

Gateway abstraction: `payment/gateways/base.py` defines the interface
(`create_payment`/`verify_payment`/`verify_webhook`/`refund`) and typed result dataclasses.
`payment/gateways/paymob.py` is a real, named adapter — reads
`PAYMOB_API_KEY`/`PAYMOB_INTEGRATION_ID`/`PAYMOB_HMAC_SECRET`/`PAYMOB_IFRAME_ID` from the
environment, and **every method raises `GatewayNotConfigured`** because they're never set. Its
docstring explains explicitly why the real HTTP calls and HMAC verification were *not* written
from general knowledge of Paymob's public API: Paymob has shipped more than one API generation,
there's no sandbox here to verify field names/endpoint paths/HMAC field ordering against, and a
webhook signature check that looks right but was never verified against a real payload is worse
than an honest 503 — it would pass review while silently accepting forged webhooks.

### Payment states
`pending` → `processing` → `paid` | `failed` | `cancelled`; `paid` → `refunded` |
`partially_refunded`. Matches the brief's suggested set exactly; every transition is exercised
by a test.

### Payment creation (workstream 12)
`PaymentService.create_payment(user, order_id, idempotency_key)` — note `amount` is not even a
parameter (a regression test asserts this via `inspect.signature`). Amount always comes from
`Order.total_amount`. Enforces: authenticated user, order ownership (raises
`PaymentAuthorizationError` otherwise), order must be `pending_payment` (raises
`InvalidOrderStateError` otherwise), and idempotency via `Payment`'s `OneToOneField(order)` — a
repeated create call against the same order returns the existing `Payment` rather than creating
a second one, regardless of whether the idempotency key matches.

### Webhooks (workstream 13)
`PaymentService.handle_webhook` — refuses (returns `GATEWAY_NOT_CONFIGURED`, writes nothing to
the DB) while the gateway can't verify a signature; an invalid signature is logged
(`signature_valid=False`) but never processed; a duplicate delivery of the same
`(gateway, event_id)` is recognized and returns `DUPLICATE` without reprocessing. The view
(`payment/views.py::payment_webhook`) returns `503 PAYMENT_GATEWAY_NOT_CONFIGURED` for the first
case, `400` for a bad signature, `200` for processed/duplicate (a webhook sender should not
retry either). `WebhookEvent.event_id` is nullable specifically so MySQL's unique index (which
doesn't support the conditional/partial form) still works: MySQL excludes NULL from uniqueness
checks, so any number of invalid deliveries coexist while real event ids stay deduplicated.

### Verification (workstream 14)
`PaymentService.verify_payment` is the only path (besides a verified webhook) that can mark a
`Payment`/`Order` paid — it always asks the gateway, never the client. The view never accepts a
client "success" flag at all.

### Refunds (workstream 15)
Implemented — staff-only (`PaymentAuthorizationError` otherwise), full or partial, idempotent on
an explicit key (checked *before* the refundability check specifically so a retried request
against an already-refunded payment still returns the original result instead of erroring),
gateway-confirmed, amount validated against remaining refundable balance.

### Idempotency strategy
Three independent mechanisms, matching the layer each protects: `Payment.idempotency_key`
(unique) + `OneToOneField(order)` for payment creation; `Refund.idempotency_key` (unique,
checked first) for refunds; `WebhookEvent`'s `(gateway, event_id)` unique constraint (NULL-safe,
see above) for webhook deliveries.

### Security controls (workstream 16)
- No raw card number/CVV ever accepted: `payment_methods` view rejects any `details` payload
  containing `card_number`/`cvv`/`cvc`/`pan` keys (regression test asserts this).
- Client amounts ignored everywhere (regression test posts `amount: '0.01'` against a real order
  and asserts the stored `Payment.amount` is unaffected).
- No gateway secrets hardcoded — `PaymobGateway` reads only from `os.environ`.
- No sensitive data logged — `GatewayTransaction.raw_response`/`WebhookEvent.payload` store
  gateway responses, which (per the same "no PCI card data" boundary) never contain card data in
  the first place since none is ever sent to this API.

### Fake implementation removed (workstream 8)
Every one of the five original `payment/views.py` functions unconditionally returned a hardcoded
success `Response` (e.g. `{"message": "Payment processed successfully"}`, HTTP 200, no gateway
call, no DB write — confirmed by reading the pre-Phase-3 source, reproduced in
`BACKEND_AUDIT.md`). `Payment.process_payment()`/`refund_payment()` did the model-level version
(`status='completed'`; `order.payment_status = True`) with the same "no gateway call at all".
None of this survives. A regression test (`TestNoFakeSuccessSurvives`) posts to
`/api/payments/process/` against the real (unconfigured) Paymob adapter — no monkeypatched fake
— and asserts a `503`, a `Payment` row that exists with `status='failed'`, and that the string
"processed successfully" appears nowhere in the response body.

**Migration safety for the old→new `Payment` model change:** `payment/migrations/
0002_payment_2_0_domain.py` deletes and recreates the `payment_payment` table rather than
altering it column-by-column. Verified safe before writing it: the old `process_payment()` stub
never called `Payment.objects.create()` anywhere, and `grep -rn "payment\.models\|Payment\.
objects\|PaymentMethod\.objects"` across the repo (excluding `payment/models.py` and
`payment/views.py` themselves) turns up only `payment/admin.py`'s registration — no other app
reads or writes these models. The migration's own docstring repeats this and tells a future
operator to `SELECT COUNT(*) FROM payment_payment` before applying it anywhere this wasn't
verified against. `PaymentMethod` (unaffected by the fake-success bug) is untouched.

### Tests
46 tests, `payment/tests/`, all passing: `test_payment_service.py` (create/duplicate/invalid
order/unauthorized/gateway failure/successful verification/verification failure/refund — full
+ partial + idempotent + non-staff-denied + over-balance-rejected + gateway-failure),
`test_webhook.py` (success/duplicate/invalid signature/unconfigured/unknown-attempt),
`test_paymob_not_configured.py` (proves the **real** `PaymobGateway`, not a mock, raises on
every method against the actual unset environment — the concrete evidence behind the BLOCKED
verdict), `test_payment_views.py` (HTTP layer: fake-success-can't-survive, client-amount-
ignored, card-data-rejected, auth/ownership). All gateway calls in tests use `FakeGateway`
(`payment/tests/fakes.py`), a double against *this codebase's own* gateway interface — never a
guess at Paymob's real wire format, and never a real network call.

## 3. Support / ASGI

### Root cause (recap from Phase 2, now fully resolved)
`support/consumers.py` imported `SupportTicket`/`SupportMessage` from `.models` at module level;
neither exists (`support/models.py` re-exports only `ContactRequest`/`ContactNote`/
`ContactStats`). Since `to7fabackend/asgi.py` → `support.routing` → this module, any real ASGI
server would have crashed on startup. Phase 2 deferred the import into `check_ticket_access()`
to stop the crash, leaving that one method still genuinely broken.

### Fix
`check_ticket_access()` ported for real to `ContactRequest`, keyed on `contact_number` (the
identifier `support/views.create_ticket` already hands clients as `"ticket_id"` — there was
never a separate ticket ID scheme). The module-level comment and deferred-import workaround are
gone; the import is now a normal one inside the method, used for real.

### Second bug found and fixed during this phase (not in the Phase 2 scope, discovered by
reading the actual Flutter client rather than just the backend)
`lib/core/services/websocket_service.dart` connects with
`protocols: ['authorization', token]` — a two-element list, fixed label first. Phase 2's
`connect()` read `subprotocols[0]`, which would have grabbed the literal string `"authorization"`
as the token on every real connection from the app — every WebSocket connection from the shipped
client would have failed authentication. Fixed by extracting the parsing into a standalone,
unit-testable function (`extract_token_and_subprotocol`) that handles both the real
`('authorization', token)` shape and a bare single-token list (kept for any other client). The
`accept(subprotocol=...)` call was also wrong in the same way (echoing the raw token instead of
one of the client's actually-offered subprotocol values, per RFC 6455 §4.2.2) — fixed alongside.

### Authentication
Unchanged mechanism (JWT via `authenticate_user()`, Phase 2), now reaches the token correctly.

### Ticket access rules
Mirrors the REST API's own authorization rather than inventing a new one: `ContactDetailView`
(the only REST endpoint that reads a single contact) is `IsAdminUser`-only, so staff always have
WebSocket access too. A regular user is granted access only if they are the `ContactRequest`'s
own `user` FK — deliberately **not** also matching by phone/name the way
`UserContactListView`'s list *filter* does; that fuzzy matching is fine for "which of my
submissions show up in my list" but is not an identity check, and reusing it here would let one
user read another's support conversation by guessing a phone number.

### Tests
15 tests in `support/tests/test_websocket_auth.py`: `authenticate_user()` (3, unchanged from
Phase 2), `extract_token_and_subprotocol()` (5, the actual regression this phase's WebSocket fix
targets — every real client subprotocol shape it needs to handle), `check_ticket_access()` (5:
owner/other-user/staff/anonymous/nonexistent-contact), plus one proving `to7fabackend/asgi.py`
now imports without error — the direct regression guard for "ASGI starts successfully", needing
no ASGI test server (`daphne` remains not installed — out of scope, same limitation documented
in Phase 2) since it only needs a successful import, which is exactly what was broken.

## 4. Tests

```text
Collected: 589
Passed:    319
Failed:    60
Skipped:   37
Errors:    173
```

Compared with the Phase 2 baseline (484 collected / 214 passed / 60 failed / 37 skipped / 173
errors): **+105 collected, all passing** (25 API contract + 19 artist/store + 46 payment + 15
support, matching Phase 3's new test files exactly), **failed and errors unchanged at 60/173**.
Confirmed by name, not just by count — none of the 60 failing or 173 erroring tests after Phase
3 live in any file this phase touched or added (`grep`'d the full failure/error list against
`payment/`, `api/tests/`, `custom_auth/tests/test_artist_store_public.py`,
`support/tests/test_websocket_auth.py` — zero matches). All 60/173 remain confined to the same
pre-existing files as Phase 2's report documented (`orders/tests/test_spec002_*.py`,
`wallet/tests/test_spec002_wallet.py`, `custom_auth/tests/test_spec001_*.py`,
`cart/tests/test_spec001_cart.py`, and related), traced to the same root cause already on
record: `conftest.py`'s `db` fixture raises `RuntimeError: Database access not allowed` for
tests that don't separately request `transactional_db`/`django_db(transaction=True)` — a
pre-existing test-infrastructure defect, unrelated to any Phase 1/2/3 change, spot-checked again
this phase (identical traceback signature) to confirm it hadn't silently changed shape.

One flaky test observed and resolved during this phase's own iteration, not a real defect:
`custom_auth/tests/test_logout_blacklist.py::test_login_logout_refresh_rejected` hits the real
`/login/` endpoint, which is Redis-backed rate-limited; repeated full-suite runs in the same
session accumulate throttle state. `redis-cli FLUSHALL` between runs produces a stable result
(confirmed via three consecutive clean runs). Also updated `pytest.ini`'s `testpaths` — it only
covered 5 of the app `tests/` directories and had never included `support/tests` (added in
Phase 2!) or the new `api/tests`/`payment/tests`; without this fix, a plain `pytest` run would
silently have collected 0 of this phase's support tests and 0 of Phase 2's, undercounting the
"complete test suite executes" acceptance criterion for both phases.

Every new test in this phase is a genuine regression guard (confirmed-404 route, confirmed
subprotocol-parsing bug, confirmed email leak, confirmed fake-success behavior) — none assert a
made-up requirement.

## 5. Migration Safety

`orders/migrations/0010_add_missing_orderitem_indexes` (Phase 2, still not deployed to
production): before applying anywhere outside this development environment, run against that
target database first:
```sql
SHOW INDEX FROM orders_orderitem;
```
```bash
python manage.py showmigrations orders
```
Confirm no existing index already occupies the names `orderitem_order_product_idx`,
`orderitem_seller_idx`, or `orderitem_variant_id_idx` before migrating. Not run against any
non-development database this phase — no production access exists in this environment.

`payment/migrations/0002_payment_2_0_domain` (new, this phase): before applying anywhere outside
this development environment, confirm the same way — `SELECT COUNT(*) FROM payment_payment;`
must return 0 (see §2's "Migration safety" above for why this migration is safe here
specifically, not in general).

Neither migration was applied to any database this session doesn't own — both were run and
verified only against this environment's own dev MySQL instance.

## 6. Deferred Items (explicitly Phase 4+, not touched)

- **Paymob gateway integration itself** — see the Gateway Blocker below. Real HTTP calls,
  webhook HMAC verification, and gateway-specific tests need real credentials and a sandbox
  account; none exist here.
- **`product_detail`'s PUT/DELETE branch** — pre-existing `@authentication_classes([])` bug
  making it unreachable via JWT auth (Phase 2 finding, not a Part A/B/C workstream).
- **`debug_arabic_encoding` endpoint** — pre-existing, leaks unapproved product data (Phase 2
  finding).
- **The double-nested `/api/auth/api/auth/...` (and artists/stores) paths** — documented as
  live, load-bearing legacy quirk (§1). Cleaning it up needs a coordinated Flutter change
  (removing the redundant `getAuthUrl()` double-prefixing), which is out of scope for a
  backend-only phase.
- **The remaining ~750 routes' full sprawl cleanup** — only the one confirmed-dead duplicate
  mount was removed this phase, per the brief's explicit "do NOT attempt to collapse all 759
  routes in this phase" instruction.
- **`conftest.py`'s broken `db` fixture** (173 errors) and the 5 categories of pre-existing
  `orders`/`wallet`/`custom_auth` spec001/spec002 test failures (60 failures) — unchanged from
  Phase 2, explicitly out of scope ("fix unrelated pre-existing test failures unless directly
  caused by Phase 3 changes" — none of these are).
- **Wallet/COD payment path unification with the new gateway `Payment` domain** — deliberately
  kept separate (`orders/atomic_order_system.py`/`WalletOrderCoordinator` untouched); unifying
  them would be the architecture rewrite this phase's brief forbids.
- **`orders/atomic_order_system.py`** itself — pre-existing uncommitted dirty file in this
  working tree from separate work, not authored or reviewed by this phase; left completely
  untouched and excluded from this phase's commit.

---

## Gateway Blocker

```text
Payment gateway is not sufficiently specified/configured to safely implement the gateway integration.
```
Paymob was named by the product owner during this phase, but no credentials
(`PAYMOB_API_KEY`/`PAYMOB_INTEGRATION_ID`/`PAYMOB_HMAC_SECRET`/`PAYMOB_IFRAME_ID`) exist anywhere
in this repository or environment — verified by grep across settings, `.env`, `requirements.txt`,
`specs/`, and `docs/`, not assumed. The Phase 3 brief's acceptance gate is conjunctive (gateway
must be *known and configured*); naming it satisfies only half. The gateway-agnostic
architecture — domain models, service layer, states, idempotency, webhook handling, refunds, and
46 passing tests against a mocked gateway interface — is fully built and ready for the real
Paymob adapter to be dropped in once credentials exist and can be verified against a live
sandbox account (not implemented from recollection of Paymob's public API — see
`payment/gateways/paymob.py`'s docstring for why that would be actively worse than the current
honest 503).

---

## Phase 3 Verdict

```text
PHASE 3 BLOCKED
```

API Contract and Support/ASGI are complete against every acceptance criterion in the brief.
Payment 2.0's architecture, security controls, and non-gateway logic are complete and tested; the
gateway integration itself is blocked on credentials that do not exist in this environment, per
the brief's own explicit instruction not to declare completion in that circumstance. Not
proceeding to Phase 4 without explicit approval.
