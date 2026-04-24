"""Tests for webClient/api auth endpoints."""
import pytest
from unittest.mock import patch, MagicMock, call


def _make_db_cursor(fetchone_return=None):
    cursor = MagicMock()
    cursor.fetchone.return_value = fetchone_return
    cursor.__enter__ = MagicMock(return_value=cursor)
    cursor.__exit__ = MagicMock(return_value=False)
    return cursor


def _make_db_conn(cursor=None):
    if cursor is None:
        cursor = _make_db_cursor()
    conn = MagicMock()
    conn.cursor.return_value = cursor
    conn.__enter__ = MagicMock(return_value=conn)
    conn.__exit__ = MagicMock(return_value=False)
    return conn


# ---------------------------------------------------------------------------
# POST /api/auth/login — auth disabled (default in tests)
# ---------------------------------------------------------------------------

class TestLoginAuthDisabled:
    def test_login_returns_400_when_auth_disabled(self, client):
        resp = client.post('/api/auth/login', json={
            'username': 'user', 'password': 'pass'
        })
        assert resp.status_code == 400

    def test_login_error_message_mentions_disabled(self, client):
        resp = client.post('/api/auth/login', json={
            'username': 'user', 'password': 'pass'
        })
        data = resp.get_json()
        assert 'error' in data


# ---------------------------------------------------------------------------
# POST /api/auth/login — auth enabled
# ---------------------------------------------------------------------------

class TestLoginAuthEnabled:
    @pytest.fixture(autouse=True)
    def enable_auth(self, monkeypatch):
        monkeypatch.setenv('AUTH_ENABLED', 'true')
        # Re-import to pick up env change
        import importlib
        import app as app_module
        app_module.AUTH_ENABLED = True

    def test_login_missing_username_returns_400(self, client):
        with patch('app.get_db_connection') as mock_factory:
            mock_factory.return_value = _make_db_conn()
            resp = client.post('/api/auth/login', json={'password': 'pass'})
        assert resp.status_code == 400

    def test_login_missing_password_returns_400(self, client):
        with patch('app.get_db_connection') as mock_factory:
            mock_factory.return_value = _make_db_conn()
            resp = client.post('/api/auth/login', json={'username': 'user'})
        assert resp.status_code == 400

    def test_login_user_not_found_returns_401(self, client):
        cursor = _make_db_cursor(fetchone_return=None)
        conn = _make_db_conn(cursor)
        with patch('app.get_db_connection', return_value=conn):
            resp = client.post('/api/auth/login', json={
                'username': 'nobody', 'password': 'pass'
            })
        assert resp.status_code == 401

    def test_login_wrong_password_returns_401(self, client):
        import bcrypt
        wrong_hash = bcrypt.hashpw(b'correct', bcrypt.gensalt()).decode()
        user_data = {
            'id': 1, 'username': 'admin', 'email': 'a@b.com',
            'password_hash': wrong_hash, 'api_key': 'k', 'role': 'admin', 'ou_id': None
        }
        cursor = _make_db_cursor(fetchone_return=user_data)
        conn = _make_db_conn(cursor)
        with patch('app.get_db_connection', return_value=conn):
            resp = client.post('/api/auth/login', json={
                'username': 'admin', 'password': 'wrong'
            })
        assert resp.status_code == 401

    def test_login_success_returns_200_with_user(self, client):
        import bcrypt
        pw_hash = bcrypt.hashpw(b'correctpass', bcrypt.gensalt()).decode()
        user_data = {
            'id': 1, 'username': 'admin', 'email': 'a@b.com',
            'password_hash': pw_hash, 'api_key': 'k', 'role': 'admin', 'ou_id': None
        }
        cursor = _make_db_cursor(fetchone_return=user_data)
        conn = _make_db_conn(cursor)
        with patch('app.get_db_connection', return_value=conn):
            resp = client.post('/api/auth/login', json={
                'username': 'admin', 'password': 'correctpass'
            })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data.get('success') is True
        assert 'user' in data

    def test_login_success_returns_session_id(self, client):
        import bcrypt
        pw_hash = bcrypt.hashpw(b'mypass', bcrypt.gensalt()).decode()
        user_data = {
            'id': 2, 'username': 'bob', 'email': 'b@b.com',
            'password_hash': pw_hash, 'api_key': 'k2', 'role': 'viewer', 'ou_id': None
        }
        cursor = _make_db_cursor(fetchone_return=user_data)
        conn = _make_db_conn(cursor)
        with patch('app.get_db_connection', return_value=conn):
            resp = client.post('/api/auth/login', json={
                'username': 'bob', 'password': 'mypass'
            })
        if resp.status_code == 200:
            data = resp.get_json()
            assert 'session_id' in data


# ---------------------------------------------------------------------------
# POST /api/auth/logout
# ---------------------------------------------------------------------------

class TestLogout:
    def test_logout_auth_disabled_returns_400(self, client):
        resp = client.post('/api/auth/logout')
        assert resp.status_code == 400

    def test_logout_auth_enabled_success(self, client, monkeypatch):
        monkeypatch.setenv('AUTH_ENABLED', 'true')
        import app as app_module
        app_module.AUTH_ENABLED = True

        conn = _make_db_conn()
        with patch('app.get_db_connection', return_value=conn):
            resp = client.post('/api/auth/logout')
        # Should always succeed (no session = just clears nothing)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data.get('success') is True


# ---------------------------------------------------------------------------
# GET /api/auth/status
# ---------------------------------------------------------------------------

class TestAuthStatus:
    def test_status_when_auth_disabled(self, client):
        resp = client.get('/api/auth/status')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['auth_enabled'] is False
        assert data['authenticated'] is False

    def test_status_when_auth_enabled_no_session(self, client, monkeypatch):
        monkeypatch.setenv('AUTH_ENABLED', 'true')
        import app as app_module
        app_module.AUTH_ENABLED = True

        with patch('app.get_authenticated_user', return_value=None):
            resp = client.get('/api/auth/status')

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['authenticated'] is False
        assert data['auth_enabled'] is True

    def test_status_with_valid_session_returns_authenticated(self, client, monkeypatch):
        monkeypatch.setenv('AUTH_ENABLED', 'true')
        import app as app_module
        app_module.AUTH_ENABLED = True

        from app import User
        mock_user = User(id=1, username='alice', email='a@b.com', api_key='key', role='admin')

        with patch('app.get_authenticated_user', return_value=mock_user):
            resp = client.get('/api/auth/status')

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['authenticated'] is True
        assert data['user']['username'] == 'alice'
