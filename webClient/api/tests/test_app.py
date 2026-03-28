"""Tests for webClient/api Flask app — core routes and configuration."""
import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# App initialisation
# ---------------------------------------------------------------------------

class TestAppInit:
    def test_app_creates_successfully(self, app):
        assert app is not None

    def test_app_has_testing_flag(self, app):
        assert app.config['TESTING'] is True

    def test_app_has_secret_key(self, app):
        assert app.config.get('SECRET_KEY') is not None

    def test_app_has_session_cookie_httponly(self, app):
        assert app.config.get('SESSION_COOKIE_HTTPONLY') is True


# ---------------------------------------------------------------------------
# Health check endpoint
# ---------------------------------------------------------------------------

class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        with patch('app.get_db_connection') as mock_conn_factory:
            mock_conn = MagicMock()
            mock_conn_factory.return_value = mock_conn
            resp = client.get('/health')
        assert resp.status_code == 200

    def test_health_returns_json(self, client):
        with patch('app.get_db_connection') as mock_conn_factory:
            mock_conn = MagicMock()
            mock_conn_factory.return_value = mock_conn
            resp = client.get('/health')
        assert resp.content_type == 'application/json'

    def test_health_response_contains_status(self, client):
        with patch('app.get_db_connection') as mock_conn_factory:
            mock_conn = MagicMock()
            mock_conn_factory.return_value = mock_conn
            resp = client.get('/health')
        data = resp.get_json()
        assert 'status' in data

    def test_health_response_contains_auth_enabled(self, client):
        with patch('app.get_db_connection') as mock_conn_factory:
            mock_conn = MagicMock()
            mock_conn_factory.return_value = mock_conn
            resp = client.get('/health')
        data = resp.get_json()
        assert 'auth_enabled' in data

    def test_health_response_contains_timestamp(self, client):
        with patch('app.get_db_connection') as mock_conn_factory:
            mock_conn = MagicMock()
            mock_conn_factory.return_value = mock_conn
            resp = client.get('/health')
        data = resp.get_json()
        assert 'timestamp' in data

    def test_health_db_error_returns_degraded(self, client):
        with patch('app.get_db_connection', side_effect=Exception('db error')):
            resp = client.get('/health')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['database'] == 'unhealthy'

    def test_health_db_ok_returns_healthy_database(self, client):
        with patch('app.get_db_connection') as mock_factory:
            mock_factory.return_value = MagicMock()
            resp = client.get('/health')
        data = resp.get_json()
        assert data['database'] == 'healthy'


# ---------------------------------------------------------------------------
# 404 for unknown routes
# ---------------------------------------------------------------------------

class TestUnknownRoutes:
    def test_unknown_route_returns_404(self, client):
        resp = client.get('/this/does/not/exist')
        assert resp.status_code == 404

    def test_unknown_api_route_returns_404(self, client):
        resp = client.get('/api/v99/unknown')
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Auth status endpoint (does not need real DB when auth disabled)
# ---------------------------------------------------------------------------

class TestAuthStatus:
    def test_auth_status_returns_200_when_auth_disabled(self, client):
        resp = client.get('/api/auth/status')
        assert resp.status_code == 200

    def test_auth_status_auth_disabled_returns_false(self, client):
        resp = client.get('/api/auth/status')
        data = resp.get_json()
        assert data.get('auth_enabled') is False
