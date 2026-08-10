"""
Phase 4 Part 14 regression test: GET /health/.
"""
import pytest
from django.test import Client


@pytest.mark.django_db
class TestHealthCheck:
    def test_returns_200_when_healthy(self):
        response = Client().get('/health/')
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'ok'
        assert data['checks']['database'] == 'ok'
        assert data['checks']['cache'] == 'ok'

    def test_response_has_no_secrets_or_env_details(self):
        """Public-safe: no version numbers, hostnames, or env var names/values."""
        response = Client().get('/health/')
        body = response.json()
        assert set(body.keys()) == {'status', 'checks'}
        assert set(body['checks'].keys()) == {'database', 'cache'}

    def test_returns_503_when_database_unreachable(self, monkeypatch):
        from to7fabackend import health as health_module

        monkeypatch.setattr(health_module, '_check_database', lambda: False)
        response = Client().get('/health/')
        assert response.status_code == 503
        assert response.json()['status'] == 'degraded'
        assert response.json()['checks']['database'] == 'error'

    def test_returns_503_when_cache_unreachable(self, monkeypatch):
        from to7fabackend import health as health_module

        monkeypatch.setattr(health_module, '_check_cache', lambda: False)
        response = Client().get('/health/')
        assert response.status_code == 503
        assert response.json()['checks']['cache'] == 'error'
