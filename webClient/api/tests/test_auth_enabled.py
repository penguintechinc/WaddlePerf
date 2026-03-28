"""Tests for webClient/api with AUTH_ENABLED=true (auth-enabled tests)."""
import pytest
from unittest.mock import patch, MagicMock
import sys


def _make_db_cursor(fetchone_return=None):
    """Helper to create mock database cursor."""
    cursor = MagicMock()
    cursor.fetchone.return_value = fetchone_return
    cursor.__enter__ = MagicMock(return_value=cursor)
    cursor.__exit__ = MagicMock(return_value=False)
    return cursor


def _make_db_conn(cursor=None):
    """Helper to create mock database connection."""
    if cursor is None:
        cursor = _make_db_cursor()
    conn = MagicMock()
    conn.cursor.return_value = cursor
    conn.__enter__ = MagicMock(return_value=conn)
    conn.__exit__ = MagicMock(return_value=False)
    return conn


@pytest.fixture
def app_with_auth(monkeypatch):
    """Create a Flask app with AUTH_ENABLED=true."""
    # Clear module cache and set env BEFORE importing
    if 'app' in sys.modules:
        del sys.modules['app']

    monkeypatch.setenv('AUTH_ENABLED', 'true')

    import app as app_module
    flask_app = app_module.app
    flask_app.config['TESTING'] = True
    flask_app.config['SECRET_KEY'] = 'test-secret'
    flask_app.config['SESSION_COOKIE_SECURE'] = False
    return flask_app


@pytest.fixture
def client_with_auth(app_with_auth):
    """Flask test client with AUTH_ENABLED=true."""
    with app_with_auth.test_client() as c:
        yield c


class TestLoginWithAuthEnabled:
    """Test login endpoint with AUTH_ENABLED=true."""

    def test_login_with_valid_credentials(self, client_with_auth):
        """Login with valid credentials should succeed."""
        import bcrypt
        pw_hash = bcrypt.hashpw(b'correctpass', bcrypt.gensalt()).decode()
        user_data = {
            'id': 1,
            'username': 'admin',
            'email': 'admin@example.com',
            'password_hash': pw_hash,
            'api_key': 'apikey123',
            'role': 'admin',
            'ou_id': None
        }
        cursor = _make_db_cursor(fetchone_return=user_data)
        conn = _make_db_conn(cursor)

        with patch('app.get_db_connection', return_value=conn):
            resp = client_with_auth.post('/api/auth/login', json={
                'username': 'admin',
                'password': 'correctpass'
            })

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert data['user']['username'] == 'admin'
        assert 'session_id' in data

    def test_login_missing_username(self, client_with_auth):
        """Login without username should fail with 400."""
        resp = client_with_auth.post('/api/auth/login', json={
            'password': 'pass'
        })
        assert resp.status_code == 400

    def test_login_missing_password(self, client_with_auth):
        """Login without password should fail with 400."""
        resp = client_with_auth.post('/api/auth/login', json={
            'username': 'user'
        })
        assert resp.status_code == 400

    def test_login_with_whitespace_username(self, client_with_auth):
        """Username with only whitespace should fail."""
        resp = client_with_auth.post('/api/auth/login', json={
            'username': '   ',
            'password': 'pass'
        })
        assert resp.status_code == 400

    def test_login_user_not_found(self, client_with_auth):
        """Login with nonexistent user should fail with 401."""
        cursor = _make_db_cursor(fetchone_return=None)
        conn = _make_db_conn(cursor)

        with patch('app.get_db_connection', return_value=conn):
            resp = client_with_auth.post('/api/auth/login', json={
                'username': 'nonexistent',
                'password': 'pass'
            })

        assert resp.status_code == 401

    def test_login_wrong_password(self, client_with_auth):
        """Login with wrong password should fail with 401."""
        import bcrypt
        pw_hash = bcrypt.hashpw(b'correct', bcrypt.gensalt()).decode()
        user_data = {
            'id': 1,
            'username': 'admin',
            'email': 'admin@example.com',
            'password_hash': pw_hash,
            'api_key': 'key',
            'role': 'admin',
            'ou_id': None
        }
        cursor = _make_db_cursor(fetchone_return=user_data)
        conn = _make_db_conn(cursor)

        with patch('app.get_db_connection', return_value=conn):
            resp = client_with_auth.post('/api/auth/login', json={
                'username': 'admin',
                'password': 'wrong'
            })

        assert resp.status_code == 401


class TestLogoutWithAuthEnabled:
    """Test logout endpoint with AUTH_ENABLED=true."""

    def test_logout_success(self, client_with_auth):
        """Logout should succeed."""
        conn = _make_db_conn()
        with patch('app.get_db_connection', return_value=conn):
            resp = client_with_auth.post('/api/auth/logout')

        assert resp.status_code == 200
        data = resp.get_json()
        assert data.get('success') is True


class TestAuthStatusWithAuthEnabled:
    """Test auth status endpoint with AUTH_ENABLED=true."""

    def test_status_when_no_authentication(self, client_with_auth):
        """Status should show unauthenticated when no session/API key provided."""
        with patch('app.get_authenticated_user', return_value=None):
            resp = client_with_auth.get('/api/auth/status')

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['authenticated'] is False
        assert data['auth_enabled'] is True

    def test_status_when_authenticated(self, client_with_auth):
        """Status should show authenticated when user is logged in."""
        from app import User
        mock_user = User(
            id=1,
            username='alice',
            email='alice@example.com',
            api_key='key123',
            role='admin'
        )

        with patch('app.get_authenticated_user', return_value=mock_user):
            resp = client_with_auth.get('/api/auth/status')

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['authenticated'] is True
        assert data['auth_enabled'] is True
        assert data['user']['username'] == 'alice'


class TestProxyEndpointWithAuthEnabled:
    """Test proxy endpoint with AUTH_ENABLED=true."""

    def test_proxy_requires_auth(self, client_with_auth):
        """Test request should fail with 401 if no auth when AUTH_ENABLED=true."""
        with patch('app.requests.post') as mock_post:
            mock_post.return_value = MagicMock(status_code=200, json=MagicMock(return_value={}))
            resp = client_with_auth.post('/api/test/http', json={'target': 'example.com'})

        # Should get 401 since no session/API key provided
        assert resp.status_code == 401

    def test_proxy_with_api_key_header(self, client_with_auth):
        """Test request with valid API key should succeed."""
        key_data = {
            'id': 1,
            'username': 'user',
            'email': 'user@example.com',
            'api_key': 'valid_key',
            'role': 'viewer',
            'ou_id': None
        }
        cursor = _make_db_cursor(fetchone_return=key_data)
        conn = _make_db_conn(cursor)

        with patch('app.get_db_connection', return_value=conn):
            with patch('app.requests.post') as mock_post:
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_resp.json.return_value = {'success': True}
                mock_post.return_value = mock_resp

                resp = client_with_auth.post(
                    '/api/test/http',
                    json={'target': 'example.com'},
                    headers={'Authorization': 'Bearer valid_key'}
                )

        assert resp.status_code == 200
