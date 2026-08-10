"""
Phase 4 regression test: to7fabackend/asgi.py's import order (Part 4, production
ASGI server).

asgi.py used to `import support.routing` (which imports support.consumers, which
imports django.contrib.auth.models) before get_asgi_application() ever ran - which
raises `AppRegistryNotReady: Apps aren't loaded yet.` under a real ASGI server. This
was invisible to every other test in this suite, including Phase 3's own "asgi.py
imports without error" test (support/tests/test_websocket_auth.py), because
pytest-django (via conftest.py's own django.setup() call) always has Django's app
registry fully loaded before any test module - including that one - is even
collected. Only running `daphne to7fabackend.asgi:application` for real, in a process
where nothing has already called django.setup(), reproduces the bug - which is
exactly what this test does, in a fresh subprocess, rather than importing in-process.
"""
import subprocess
import sys
import textwrap


def test_asgi_module_imports_successfully_with_no_prior_django_setup():
    """Runs in a brand-new Python subprocess (this project's venv interpreter) that
    has never called django.setup() - the same starting condition a real ASGI server
    process is in when it first imports to7fabackend.asgi."""
    script = textwrap.dedent("""
        import os
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'to7fabackend.settings')
        os.environ.setdefault('ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver')
        import to7fabackend.asgi
        assert to7fabackend.asgi.application is not None
        print("ASGI_IMPORT_OK")
    """)
    result = subprocess.run(
        [sys.executable, '-c', script],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, (
        f"asgi.py failed to import in a fresh process (stdout={result.stdout!r}, "
        f"stderr={result.stderr!r})"
    )
    assert 'ASGI_IMPORT_OK' in result.stdout
