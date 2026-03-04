# Repository Guidelines

## Project Structure & Module Organization
This repository is a Django monolith split into domain apps:
- `to7fabackend/`: project settings, URL routing, ASGI/WSGI, Celery config.
- `custom_auth/`: user model, JWT/auth APIs, OTP/verification, addresses.
- `products/`, `cart/`, `orders/`, `wallet/`, `payment/`, `notifications/`, `support/`: core commerce domains.
- `admin_panel/`: admin dashboard views, APIs, templates, middleware.
- `api/`: shared API helpers, exception handler, request-id middleware.
- Tests are colocated in app-level `tests/` directories (for example `orders/tests/`, `cart/tests/`, `wallet/tests/`).
- Documentation and specs: `docs/`, `specs/`.

## Build, Test, and Development Commands
Use project-local virtualenv where available.
- `python manage.py runserver`: run local API server.
- `python manage.py migrate`: apply database migrations.
- `python manage.py check`: run Django system checks.
- `pytest`: run full test suite.
- `pytest orders/tests/test_checkout.py -q`: run a focused test file.
- `python manage.py test`: run Django test runner (legacy path).

## Coding Style & Naming Conventions
- Follow PEP 8, 4-space indentation, and explicit imports.
- Keep views thin; place reusable business logic in `services/` modules.
- Naming patterns:
  - models: `PascalCase` (`SellerApplication`)
  - functions/vars: `snake_case` (`create_order`, `payment_timeout_at`)
  - constants: `UPPER_SNAKE_CASE`.
- Prefer structured logging (`logger`) over `print`.
- Keep API responses consistent using helpers in `api/helpers.py`.

## Testing Guidelines
- Primary framework: `pytest` with `pytest-django`.
- Add tests in app-local `tests/` folders; name files `test_*.py` and test functions `test_*`.
- Cover serializers, permissions, state transitions, and concurrency-sensitive paths (orders/wallet).
- Use `to7fabackend.test_settings` for isolated test execution when needed.

## Commit & Pull Request Guidelines
- Use concise, imperative commit subjects (for example: `orders: enforce valid status transition`).
- One logical change per commit; include migrations with model changes.
- PRs should include:
  - clear scope and rationale
  - affected apps/files
  - test evidence (`pytest` output summary)
  - migration notes and rollback considerations.

## Security & Configuration Tips
- Do not commit secrets; use `.env` for `SECRET_KEY`, DB, CORS, email, and Redis/Celery settings.
- Validate permissions on all mutable endpoints (`IsAuthenticated` is not enough for admin actions).
- Avoid exposing stack traces or sensitive internals in API responses.

## Active Technologies
- Python 3.14.2 + Django 4.2.13, Django REST Framework 3.16.0, pytest-django 4.5.2 (005-variant-system-implementation)
- PostgreSQL (005-variant-system-implementation)

## Recent Changes
- 005-variant-system-implementation: Added Python 3.14.2 + Django 4.2.13, Django REST Framework 3.16.0, pytest-django 4.5.2
