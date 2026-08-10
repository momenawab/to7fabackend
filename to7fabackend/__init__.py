# Pre-Flutter remediation (final backend audit C1): this file used to also do
# `import pymysql; pymysql.install_as_MySQLdb()` - a compatibility shim making the
# pure-Python pymysql package masquerade as the MySQLdb module Django's mysql backend
# imports by default. requirements.txt dropped pymysql as a declared dependency
# (Phase 2), on the correct basis that mysqlclient (still listed, still installed)
# provides the real MySQLdb module directly with no shim needed - but this import
# survived that cleanup untouched. Because this module-level import runs before
# Django settings, before celery.py, before anything else, a genuinely fresh
# `pip install -r requirements.txt` (any new deployment, CI runner, or clean
# checkout) crashed at startup with `ModuleNotFoundError: No module named 'pymysql'`.
# Invisible in every dev venv that happened to still have pymysql installed as an
# orphan package from before the Phase 2 manifest cleanup - exactly why the final
# audit could only find this by reading the diff, not by running the existing checks.
# Removed here; verified against a genuinely clean venv (no orphan pymysql) - see
# FINAL_PRE_FLUTTER_REMEDIATION_REPORT.md.

# This will make sure the Celery app is always imported when
# Django starts so that shared_task will use this app.
from .celery import app as celery_app

__all__ = ('celery_app',)
