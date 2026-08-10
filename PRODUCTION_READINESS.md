# To7fa Backend — Production Readiness

Written as part of **Phase 4: Production Readiness & Final Hardening** (the final
backend hardening phase before "To7fa 2.0 — Flutter + Rebrand + New UI"). This
document is the operational reference for deploying `to7fabackend` — environment
variables, required services, deployment order, migration/backup safety, and
external dependencies that are not yet configured.

It does not describe new architecture. The backend's design (Django + DRF + Channels
+ Celery + MySQL + Redis) is unchanged; this document makes that design
reproducible and safe to deploy.

---

## 1. Environment Variables

None of these have invented values. Where a default exists in code, it is a
*local-development* fallback only — every `Secret` and every `Required` value below
must be set explicitly in any real deployment; the fallback is not a suggested
production value.

### Required (deployment will misbehave or fail-fast without these)

| Variable | Purpose | Notes |
|---|---|---|
| `SECRET_KEY` | Django cryptographic signing | No fallback — `settings.py` raises `ImproperlyConfigured` at import time if unset. Fail-fast by design. |
| `DEBUG` | Django debug mode | Must be `False` in any deployment reachable by real users. `settings_production.py` also forces `DEBUG = False` and re-derives the cookie/redirect security flags independently (see §5). |
| `ALLOWED_HOSTS` | Django host header validation | Comma-separated. No hardcoded production domain exists anywhere in settings — this project does not know its own production hostname yet; it must be supplied at deploy time. |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | MySQL connection | No fallback values — unset means Django cannot connect. |
| `CORS_ALLOWED_ORIGINS` | Which origins may call the API cross-origin | Comma-separated. `settings.py` raises `ImproperlyConfigured` when `DEBUG=False` and this is unset (fail-fast, same pattern as `SECRET_KEY`). |
| `CSRF_TRUSTED_ORIGINS` | Which origins may submit session-authenticated (admin dashboard) POSTs | Same fail-fast pattern as `CORS_ALLOWED_ORIGINS`. |

### Optional (sensible defaults exist; override only if the deployment differs from the default topology)

| Variable | Purpose | Default |
|---|---|---|
| `DJANGO_ENV` | Informational only — nothing branches on it in code. Environment separation is achieved by *which settings module* is loaded (`settings.py` vs `settings_production.py`) plus each environment's own `.env`, not by this flag. | `development` |
| `REDIS_URL` | Base Redis connection, before per-service overrides | `redis://127.0.0.1:6379` |
| `CHANNELS_REDIS_URL` | Django Channels layer backend | `{REDIS_URL}/0` |
| `CACHE_REDIS_URL` | Django cache backend | `{REDIS_URL}/1` |
| `CELERY_BROKER_URL` | Celery broker | `{REDIS_URL}/2` |
| `CELERY_RESULT_BACKEND` | Celery result store | `{REDIS_URL}/2` |
| `SECURE_HSTS_ENABLED` | Enables `SECURE_HSTS_SECONDS`/preload/subdomains | `False` — see §5, this must only be turned on once the deployment guarantees HTTPS on every path. |
| `STATIC_ROOT` | Collected static files directory (production settings only) | `/var/www/to7fa/static/` |
| `MEDIA_ROOT` | User-uploaded media directory (production settings only) | `/var/www/to7fa/media/` |
| `DJANGO_LOG_FILE` | Production log file path | `/var/log/to7fa/django.log` |
| `FRONTEND_URL` | Used in outgoing email links (password reset, etc.) | `http://localhost:8000` |
| `EMAIL_HOST` / `EMAIL_PORT` / `EMAIL_USE_TLS` | SMTP connection | `smtp.gmail.com` / `587` / `True` — placeholders for *which* provider, not credentials. See §4 (external dependency: no real email credentials configured). |
| `APNS_BUNDLE_ID` | iOS push bundle identifier | `com.to7fa.app` |
| `FCM_SERVICE_ACCOUNT_FILE` | Path to the Firebase service-account JSON | `firebase-service-account.json` (project root) — see §4, no real file is present. |

### Secret (must never be committed, logged, or echoed by any endpoint)

`SECRET_KEY`, `DB_PASSWORD`, `EMAIL_HOST_PASSWORD`, the Firebase service-account
JSON file itself, any future Paymob API key/HMAC secret, any future APNs private
key file. `.gitignore` already excludes `firebase-service-account.json` and `.env`.

### Public (safe to expose, e.g. in a status page)

`DJANGO_ENV` (informational label only), `ALLOWED_HOSTS` (already visible via the
`Host` header contract itself), the `/health/` endpoint's own response body (§7 —
deliberately contains no secrets, versions, or hostnames).

### External dependency (not yet configured — see §8)

`FCM_PROJECT_ID`, a real `FCM_SERVICE_ACCOUNT_FILE`, `APNS_KEY_ID` /
`APNS_TEAM_ID` / `APNS_KEY_FILE`, real `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD`,
and all Paymob credentials (no such env vars exist in code today — Paymob
integration is not implemented; see §8).

---

## 2. Services

| Service | Role | Config source |
|---|---|---|
| **MySQL** | Primary datastore | `DB_*` env vars (§1). `mysqlclient==2.2.7`. |
| **Redis** | Django cache backend, Channels layer, Celery broker+result backend | `REDIS_URL` + per-service overrides (§1). A single Redis instance is used for all three by default (different logical DB numbers: cache=1, channels=0, celery=2) — this is the existing topology, not new for Phase 4; only the *configuration* (env-driven vs. hardcoded `127.0.0.1:6379`) changed this phase. |
| **Celery** | Background task execution (`to7fabackend/celery.py`) | Broker/result backend both derive from `REDIS_URL` unless overridden. Not redesigned this phase — only made env-driven. |
| **ASGI server** | Serves HTTP + WebSocket (Channels) | **Daphne** (`daphne==4.1.2`, added this phase — see §6). Run as: `daphne -b 0.0.0.0 -p 8001 to7fabackend.asgi:application`. Do not use `manage.py runserver` in production — it is Django's development server. |

---

## 3. Deployment Order

1. **Backup** the production database (and, if this is not a first deploy, confirm
   the backup succeeded and is restorable — see §9). Never run migrations against a
   database without a verified-restorable backup.
2. Set all **Required** environment variables (§1). Confirm `DEBUG=False` and that
   `settings_production.py` is the settings module in use
   (`DJANGO_SETTINGS_MODULE=to7fabackend.settings_production`).
3. Install **dependencies**: `pip install -r requirements.txt`.
4. Run **database migrations** — but only after the migration-specific
   pre-deploy checks in §9. `python manage.py migrate`.
5. Collect **static files**: `python manage.py collectstatic --noinput`.
   Media files (`MEDIA_ROOT`) are user-uploaded and are not part of this step —
   ensure the directory exists and is writable by the deploying user. The same
   applies to `DJANGO_LOG_FILE`'s parent directory (default
   `/var/log/to7fa/`) — Django's logging config raises `ValueError: Unable to
   configure handler 'file'` at startup if that directory doesn't already exist;
   create it (and `STATIC_ROOT`/`MEDIA_ROOT`) before step 6.
6. Start the **ASGI server** (Daphne, §2/§6).
7. Start **Celery** worker(s) (and beat, if scheduled tasks are in use) pointed at
   the same `CELERY_BROKER_URL`/`CELERY_RESULT_BACKEND`.
8. Verify **health checks** (§7): `GET /health/` should return `200` with
   `{"status": "ok", "checks": {"database": "ok", "cache": "ok"}}`.
9. Run **smoke tests** against the live deployment: a login, a product list fetch,
   and a WebSocket connection to the support channel are the minimum meaningful
   checks — each exercises a different subsystem (JWT auth + MySQL, MySQL read
   path, Channels + Redis).

---

## 4. Notification Readiness (Firebase / APNs)

Firebase Admin SDK (`firebase-admin==6.5.0`, added this phase) is imported
defensively: if the package or the service-account file is missing,
`notifications/push_utils.py` disables FCM push and logs a clear warning rather than
crashing the app (`manage.py check` confirms this — see the "Firebase service
account file not found ... This is expected in development/CI" warning it emits).
`FCM_SERVICE_ACCOUNT_FILE` is env-overridable (§1); no credential is committed to
the repo.

APNs (`APNS_KEY_ID`, `APNS_TEAM_ID`, `APNS_KEY_FILE`, `APNS_BUNDLE_ID`) follows the
same pattern: `APNS_BUNDLE_ID` has a non-secret default; the key ID/team ID/private
key file have no defaults and are unconfigured until real Apple credentials are
provisioned (§8).

**Never commit** `firebase-service-account.json` or any APNs `.p8` private key file.

---

## 5. Security Configuration Notes

- **HSTS** (`SECURE_HSTS_ENABLED`, §1) defaults to `False` regardless of `DEBUG`.
  HSTS is a client-cached header — a browser that receives it will refuse plain
  HTTP to that host for the declared duration, with no server-side way to
  un-cache it early. Enabling it before HTTPS is guaranteed on every path (i.e.
  before a real TLS-terminating deployment exists) is a real user-facing risk
  (locks users out if HTTPS isn't actually available yet), so it is gated by its
  own explicit flag rather than tied to `DEBUG`.
- **`settings_production.py` re-derives `SECURE_SSL_REDIRECT` /
  `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE`** explicitly after setting
  `DEBUG = False`, rather than relying on `settings.py`'s `not DEBUG`-derived
  values. `settings.py` computes those at import time using whatever `DEBUG` the
  shared `.env` happens to have (this project's dev `.env` has `DEBUG=True`);
  without the explicit re-set, deploying with `settings_production.py` would
  silently inherit insecure cookie/redirect settings. Verified via
  `manage.py check --deploy`: 4 warnings (W004/W008/W012/W016) before the fix,
  0 after.
- **Python version**: this project's venv currently runs **Python 3.14.6**, but
  Django 4.2 officially supports up to **Python 3.12**. A real, reproducible
  incompatibility was found under 3.14: Django's own `BaseContext.__copy__`
  (`django/template/context.py`, `duplicate = copy(super())`) breaks, which
  crashes the *default 404 error page* for any 404 in this app
  (`AttributeError: 'super' object has no attribute 'dicts'`). This was
  discovered during Phase 4 (Part 7.2's debug-endpoint-removal regression test had
  to avoid asserting on a live HTTP 404 because of it) and confirmed unrelated to
  any app code by requesting a completely different, always-nonexistent URL and
  observing the identical crash. **Production must run Django 4.2 under Python
  3.10–3.12**, not 3.14. This is a deployment requirement, not a code fix — no
  Django upgrade was performed this phase (out of scope).

---

## 6. ASGI Server

**Daphne** was chosen as the single production ASGI server (`daphne==4.1.2`,
added to `requirements.txt` this phase) — it is the reference implementation from
the same maintainers as `channels`/`channels-redis`, already dependencies of this
project. No competing ASGI server was added.

`to7fabackend/asgi.py` was reordered this phase: `get_asgi_application()` (which
calls `django.setup()`) must run *before* `import support.routing` (which
transitively imports Django models). The old ordering crashed with
`AppRegistryNotReady: Apps aren't loaded yet.` under a real ASGI server — this was
invisible to the entire pytest suite because pytest-django always has Django fully
set up before any test collection runs. Verified by actually running
`daphne to7fabackend.asgi:application` and, separately, by a subprocess-based
regression test (`api/tests/test_asgi_startup.py`) that imports `asgi.py` in a
fresh Python process with no prior `django.setup()` call.

Run: `daphne -b 0.0.0.0 -p 8001 to7fabackend.asgi:application`
(with a reverse proxy such as nginx terminating TLS and forwarding both HTTP and
WebSocket upgrade requests to it).

---

## 7. Health Checks

`GET /health/` (mounted at the project root, not under the frozen `api/v1/`
contract — it isn't a versioned client-facing resource). Checks:

- **App**: implied by responding at all.
- **Database**: `SELECT 1` against the default MySQL connection.
- **Cache (Redis)**: a set/get round-trip against the Django cache backend.

Returns `200` with `{"status": "ok", "checks": {"database": "ok", "cache": "ok"}}`
when every component is healthy, `503` with `"status": "degraded"` and the specific
failing component(s) marked `"error"` otherwise. The response deliberately never
includes version numbers, hostnames, environment variable names/values, or stack
traces — failures are logged server-side (`logger.warning`) instead.

---

## 8. External Dependencies — Explicitly Unavailable

These require credentials or accounts this project does not have. Each is a
documented **external blocker**, not a Phase 4 code defect:

- **Paymob** (payment gateway): no sandbox account, no API key, no HMAC secret.
  `payment/` app's domain models (Payment/PaymentAttempt/GatewayTransaction/
  Refund/WebhookEvent, added in Phase 3) exist, but real HTTP calls to Paymob and
  real webhook-signature verification are **not implemented** — implementing them
  from memory without real credentials to test against was explicitly out of
  scope for every phase to date, including this one. Verified this phase that the
  gateway-not-configured path fails safely: no fake success, no order ever marked
  paid, no webhook accepted without verification.
- **Firebase**: no real `firebase-service-account.json`, no `FCM_PROJECT_ID`.
  Push notifications are inert (logged warning, no crash) until provisioned.
- **APNs**: no `APNS_KEY_ID`/`APNS_TEAM_ID`/`APNS_KEY_FILE`.
- **Email provider**: no real `EMAIL_HOST_USER`/`EMAIL_HOST_PASSWORD`. Outgoing
  email (password reset, notifications) will fail silently against whatever SMTP
  defaults are configured until real credentials are set.
- **Production domain**: no domain name has ever been decided or hardcoded
  anywhere in this codebase. `ALLOWED_HOSTS`/`CORS_ALLOWED_ORIGINS`/
  `CSRF_TRUSTED_ORIGINS` must all be supplied at deploy time (§1).

---

## 9. Migration & Backup Safety (Phase 4 Parts 11–12)

**General rule: never run `manage.py migrate` against production without a
verified, restorable backup taken immediately before.** MySQL backups
(`mysqldump` or equivalent) should be tested for restorability periodically, not
just taken — a backup that has never been restored is unverified.

**Rollback limitations**: Django migrations are not reliably reversible in this
project (no migration here has a hand-written, tested `reverse` path beyond
Django's auto-generated inverse operations, and several — see below — are
explicitly destructive in the forward direction). The only dependable rollback
path is restoring the pre-migration backup, not `manage.py migrate <app> <prior>`.

**Migration execution order**: standard Django order — `python manage.py migrate`
applies all apps' migrations in dependency order automatically; no manual
per-app ordering is required beyond ensuring the two checks below are run first.

Two migrations carry specific, non-generic pre-deploy verification steps, both
already documented in the migration files themselves (not new for this phase —
consolidated here for a single deployment reference):

### `orders/0010_add_missing_orderitem_indexes`

Restores a missing link in migration history (an earlier migration,
`0004_rename_...`, renames three `OrderItem` indexes that no prior migration ever
actually created under their original names). `CREATE INDEX` is non-destructive.

**Before deploying**, run against production:
```sql
SHOW INDEX FROM orders_orderitem;
```
and check `python manage.py showmigrations orders`.
- If neither the old nor new index names are present (matching this project's dev
  database, where `0004` shows as applied but the indexes it claims to rename
  never existed under any name — evidence it was applied via `--fake` or
  equivalent there): this migration will create them as intended, no action
  needed.
- If an index under one of the three old names (`orderitem_order_product_idx`,
  `orderitem_seller_idx`, `orderitem_variant_id_idx`) already exists: this
  migration will fail loudly with a duplicate-key-name error rather than corrupt
  anything, but it needs a human to adjust the migration before deployment. **Do
  not deploy blind.**

### `payment/0002_replace_fake_payment_with_domain_models`

Deletes and recreates the `payment_payment` table (replacing the Phase-2-era
fake-success stub with the real Payment 2.0 domain). This is only safe because
nothing has ever written a row to that table in this codebase (verified: the old
`process_payment()` stub never called `Payment.objects.create()`; no other app
reads or writes these models).

**Before deploying**, run against production:
```sql
SELECT COUNT(*) FROM payment_payment;
```
- If the count is **0**: safe to proceed, matches every environment this was
  verified against.
- If the count is **not 0**: **STOP.** This means production has real payment
  records this migration was never designed to preserve. Do not apply it. This
  needs a proper column-preserving migration written against production's actual
  data before it can be deployed — report this as a blocker rather than deploying
  a migration that will destroy those rows.

### Production verification (after migrating)

`python manage.py showmigrations` should show every migration applied with no
gaps. Spot-check `SELECT COUNT(*) FROM orders_orderitem;` and
`SELECT COUNT(*) FROM payment_payment;` remain consistent with pre-migration
counts (0 growth expected from these two migrations specifically — they add
indexes and replace an empty table, not rows).

### Restore procedure

Standard MySQL restore from the pre-deploy backup (§ above). No custom restore
tooling exists in this project; none was added this phase (out of scope — no
speculative infrastructure).

---

## 10. Test Infrastructure

The root `conftest.py` previously shadowed pytest-django's real `db` fixture with
a hand-rolled one that never used pytest-django's actual
database-access-blocker-lifting machinery, causing intermittent
`RuntimeError: Database access not allowed` depending on test run order. This was
the root cause of the large majority of the non-passing test counts from earlier
phases. Removing the shadow fixture (Phase 4 Part 15) brought errors to 0; see
`PHASE4_PRODUCTION_READINESS_REPORT.md` §6 for the full before/after numbers and
classification of every remaining failure.

Run the suite: `pytest` (from `to7fabackend/`, using the real MySQL/Redis
services — this project does not use a SQLite/in-memory test configuration for
its authoritative baseline).
