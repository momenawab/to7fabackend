"""
Phase 4 regression tests: production settings hardening (Part 1: HSTS gating,
security headers; Part 3: Redis env-driven configuration).

These import to7fabackend.settings/settings_production as plain Python modules with
importlib rather than via Django's settings machinery, since Django only allows one
active settings module per process and this suite already runs under
to7fabackend.settings.
"""
import importlib
import os

import pytest


def _reimport(module_name, env_overrides):
    """Import (or re-import) a settings module with specific env vars set, then
    restore the previous environment. Needed because settings.py/settings_production.py
    read os.environ at import time, not lazily."""
    original_env = {k: os.environ.get(k) for k in env_overrides}
    try:
        os.environ.update(env_overrides)
        if module_name in list(__import__('sys').modules):
            del __import__('sys').modules[module_name]
        return importlib.import_module(module_name)
    finally:
        for k, v in original_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        if module_name in list(__import__('sys').modules):
            del __import__('sys').modules[module_name]


class TestRedisEnvDrivenConfig:
    """Part 3: CACHES/CHANNEL_LAYERS/Celery must be configurable via REDIS_URL
    without a source change, and must default to the same 127.0.0.1:6379 (dbs 0/1/2)
    this project always used, so local development needs no new configuration."""

    def test_default_matches_previous_hardcoded_values(self):
        settings = _reimport('to7fabackend.settings', {})
        assert settings.CACHES['default']['LOCATION'] == 'redis://127.0.0.1:6379/1'
        assert settings.CHANNEL_LAYERS['default']['CONFIG']['hosts'] == ['redis://127.0.0.1:6379/0']
        assert settings.CELERY_BROKER_URL == 'redis://127.0.0.1:6379/2'
        assert settings.CELERY_RESULT_BACKEND == 'redis://127.0.0.1:6379/2'

    def test_redis_url_override_propagates_to_all_three(self):
        settings = _reimport('to7fabackend.settings', {'REDIS_URL': 'redis://prod-redis:6380'})
        assert settings.CACHES['default']['LOCATION'] == 'redis://prod-redis:6380/1'
        assert settings.CHANNEL_LAYERS['default']['CONFIG']['hosts'] == ['redis://prod-redis:6380/0']
        assert settings.CELERY_BROKER_URL == 'redis://prod-redis:6380/2'

    def test_per_service_override_takes_precedence_over_redis_url(self):
        settings = _reimport('to7fabackend.settings', {
            'REDIS_URL': 'redis://prod-redis:6380',
            'CACHE_REDIS_URL': 'redis://cache-only-redis:6379/5',
        })
        assert settings.CACHES['default']['LOCATION'] == 'redis://cache-only-redis:6379/5'
        # Unaffected services still derive from REDIS_URL.
        assert settings.CELERY_BROKER_URL == 'redis://prod-redis:6380/2'


class TestHstsGating:
    """Part 1: HSTS must not be tied directly to DEBUG - it needs its own explicit
    opt-in, since (unlike SECURE_SSL_REDIRECT) it's client-cached and can lock users
    out of a deployment that isn't actually HTTPS-ready yet."""

    def test_hsts_disabled_by_default_even_when_debug_false(self):
        settings = _reimport('to7fabackend.settings', {'DEBUG': 'False'})
        assert settings.SECURE_HSTS_SECONDS == 0

    def test_hsts_enabled_only_via_explicit_flag(self):
        settings = _reimport('to7fabackend.settings', {
            'DEBUG': 'False', 'SECURE_HSTS_ENABLED': 'true',
        })
        assert settings.SECURE_HSTS_SECONDS == 31536000
        assert settings.SECURE_HSTS_INCLUDE_SUBDOMAINS is True
        assert settings.SECURE_HSTS_PRELOAD is True

    def test_hsts_flag_ignored_in_debug_mode_is_not_assumed(self):
        """Setting the flag without also setting DEBUG=False still enables HSTS -
        the flag is genuinely independent of DEBUG, not a secondary gate on top of
        it. Documents the actual (intentional) behavior rather than assuming a
        DEBUG-AND-flag combination."""
        settings = _reimport('to7fabackend.settings', {
            'DEBUG': 'True', 'SECURE_HSTS_ENABLED': 'true',
        })
        assert settings.SECURE_HSTS_SECONDS == 31536000


class TestProductionSecurityHeadersIndependentOfSharedDotenv:
    """Part 1 fix: settings_production.py's DEBUG=False must make
    SECURE_SSL_REDIRECT/SESSION_COOKIE_SECURE/CSRF_COOKIE_SECURE True regardless of
    what DEBUG happens to be in a .env shared with settings.py (this project's own
    development .env sets DEBUG=True) - these must not be silently inherited as
    insecure. This is the exact gap `manage.py check --deploy` surfaced during this
    phase."""

    def test_production_settings_force_secure_cookies_even_if_dotenv_says_debug_true(self):
        settings = _reimport('to7fabackend.settings_production', {
            'DEBUG': 'True',  # simulates this project's actual development .env
            'CORS_ALLOWED_ORIGINS': 'https://example.test',
            'STATIC_ROOT': '/tmp/to7fa_test_static',
            'MEDIA_ROOT': '/tmp/to7fa_test_media',
            'DJANGO_LOG_FILE': '/tmp/to7fa_test_logs_pytest/django.log',
        })
        assert settings.DEBUG is False
        assert settings.SECURE_SSL_REDIRECT is True
        assert settings.SESSION_COOKIE_SECURE is True
        assert settings.CSRF_COOKIE_SECURE is True


class TestNoHardcodedProductionDomains:
    """Part 1: settings_production.py must not hardcode ALLOWED_HOSTS/
    CORS_ALLOWED_ORIGINS/CSRF_TRUSTED_ORIGINS placeholder values that would silently
    override the environment - it must inherit settings.py's env-driven values."""

    def test_settings_production_does_not_override_allowed_hosts(self):
        # Read the source file directly rather than importing (importing requires
        # env vars this test doesn't want to manage) - a static check that the
        # dangerous override pattern hasn't been reintroduced.
        import pathlib
        path = pathlib.Path(__file__).resolve().parents[2] / 'to7fabackend' / 'settings_production.py'
        text = path.read_text()
        assert "ALLOWED_HOSTS = [" not in text
        assert "CORS_ALLOWED_ORIGINS = [" not in text
        # 'yourdomain.com' is fine to mention in an explanatory comment (this test
        # file does too) - what matters is it's not the value of a live assignment.
        assert "DEFAULT_FROM_EMAIL = " not in text
