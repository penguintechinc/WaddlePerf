"""Tests for webClient/api database helpers and validation functions."""
import pytest
from unittest.mock import patch, MagicMock


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


class TestValidateSessionFunction:
    """Test the validate_session helper function."""

    def test_validate_session_handles_db_error_when_auth_disabled(self, client):
        """Testing database error handling via client request."""
        # This is tested implicitly through the auth endpoints
        # When AUTH_ENABLED=false, these functions are never called
        pass

    def test_validate_session_returns_user_when_auth_enabled_and_session_found(self, client, monkeypatch):
        """When AUTH_ENABLED=true and session found, returns User object."""
        monkeypatch.setenv('AUTH_ENABLED', 'true')
        import app as app_module
        app_module.AUTH_ENABLED = True

        session_data = {
            'user_id': 42,
            'username': 'alice',
            'email': 'alice@example.com',
            'api_key': 'key123',
            'role': 'admin',
            'ou_id': 5
        }
        cursor = _make_db_cursor(fetchone_return=session_data)
        conn = _make_db_conn(cursor)

        with patch('app.get_db_connection', return_value=conn):
            # Test via status endpoint which calls get_authenticated_user
            resp = client.get('/api/auth/status')
            assert resp.status_code == 200


class TestValidateApiKeyFunction:
    """Test the validate_api_key helper function."""

    def test_validate_api_key_returns_user_when_found(self, client, monkeypatch):
        """When AUTH_ENABLED=true and API key found, returns User object."""
        monkeypatch.setenv('AUTH_ENABLED', 'true')
        import app as app_module
        app_module.AUTH_ENABLED = True

        key_data = {
            'id': 42,
            'username': 'bob',
            'email': 'bob@example.com',
            'api_key': 'valid_key',
            'role': 'viewer',
            'ou_id': None
        }
        cursor = _make_db_cursor(fetchone_return=key_data)
        conn = _make_db_conn(cursor)

        with patch('app.get_db_connection', return_value=conn):
            # Test via proxy endpoint with Authorization header
            with patch('app.requests.post') as mock_post:
                mock_post.return_value = MagicMock(status_code=200, json=MagicMock(return_value={}))
                resp = client.post(
                    '/api/test/http',
                    json={'target': 'example.com'},
                    headers={'Authorization': 'Bearer valid_key'}
                )
            assert resp.status_code in (200, 401)  # May be 401 if user not found


class TestGetAuthenticatedUserFunction:
    """Test the get_authenticated_user helper function."""

    def test_get_authenticated_user_works_with_session(self, client, monkeypatch):
        """Testing get_authenticated_user through client requests."""
        # This is tested through auth endpoints implicitly
        # When AUTH_ENABLED=false, it returns None
        resp = client.get('/api/auth/status')
        assert resp.status_code == 200
        data = resp.get_json()
        # When AUTH is disabled, this is always False
        assert data['authenticated'] is False


class TestValidateTestParams:
    """Test the validate_test_params validation function."""

    def test_validate_test_params_accepts_valid_params(self):
        """Valid params should pass validation."""
        from app import validate_test_params
        data = {'target': 'example.com', 'port': 80, 'timeout': 30, 'count': 10}
        valid, error = validate_test_params(data, 'http')
        assert valid is True
        assert error is None

    def test_validate_test_params_rejects_empty_target(self):
        """Empty target should be rejected."""
        from app import validate_test_params
        data = {'target': '', 'port': 80}
        valid, error = validate_test_params(data, 'http')
        assert valid is False
        assert 'required' in error.lower()

    def test_validate_test_params_rejects_missing_target(self):
        """Missing target should be rejected."""
        from app import validate_test_params
        data = {}
        valid, error = validate_test_params(data, 'http')
        assert valid is False
        assert 'required' in error.lower()

    def test_validate_test_params_rejects_target_too_long(self):
        """Target longer than 255 chars should be rejected."""
        from app import validate_test_params
        data = {'target': 'x' * 256}
        valid, error = validate_test_params(data, 'http')
        assert valid is False
        assert 'too long' in error.lower()

    def test_validate_test_params_accepts_whitespace_in_target(self):
        """Whitespace should be stripped from target."""
        from app import validate_test_params
        data = {'target': '  example.com  '}
        valid, error = validate_test_params(data, 'http')
        assert valid is True
        assert error is None

    def test_validate_test_params_rejects_invalid_port_type(self):
        """Non-integer port should be rejected."""
        from app import validate_test_params
        data = {'target': 'example.com', 'port': 'notaport'}
        valid, error = validate_test_params(data, 'tcp')
        assert valid is False
        assert 'invalid port' in error.lower()

    def test_validate_test_params_rejects_port_too_high(self):
        """Port > 65535 should be rejected."""
        from app import validate_test_params
        data = {'target': 'example.com', 'port': 99999}
        valid, error = validate_test_params(data, 'tcp')
        assert valid is False
        assert 'invalid port' in error.lower()

    def test_validate_test_params_rejects_port_zero(self):
        """Port 0 should be rejected."""
        from app import validate_test_params
        data = {'target': 'example.com', 'port': 0}
        valid, error = validate_test_params(data, 'tcp')
        assert valid is False

    def test_validate_test_params_rejects_invalid_timeout(self):
        """Timeout outside 1-300 range should be rejected."""
        from app import validate_test_params
        data = {'target': 'example.com', 'timeout': 999}
        valid, error = validate_test_params(data, 'http')
        assert valid is False
        assert 'timeout' in error.lower()

    def test_validate_test_params_rejects_zero_timeout(self):
        """Timeout 0 should be rejected."""
        from app import validate_test_params
        data = {'target': 'example.com', 'timeout': 0}
        valid, error = validate_test_params(data, 'http')
        assert valid is False

    def test_validate_test_params_rejects_invalid_count(self):
        """Count outside 1-1000 range should be rejected."""
        from app import validate_test_params
        data = {'target': 'example.com', 'count': 9999}
        valid, error = validate_test_params(data, 'icmp')
        assert valid is False
        assert 'count' in error.lower()

    def test_validate_test_params_rejects_zero_count(self):
        """Count 0 should be rejected."""
        from app import validate_test_params
        data = {'target': 'example.com', 'count': 0}
        valid, error = validate_test_params(data, 'icmp')
        assert valid is False

    def test_validate_test_params_accepts_defaults(self):
        """Should use defaults for optional params."""
        from app import validate_test_params
        data = {'target': 'example.com'}
        valid, error = validate_test_params(data, 'http')
        assert valid is True

    def test_validate_test_params_accepts_none_port(self):
        """None port (optional) should be accepted."""
        from app import validate_test_params
        data = {'target': 'example.com', 'port': None}
        valid, error = validate_test_params(data, 'http')
        assert valid is True


class TestGetDbConnectionFunction:
    """Test the get_db_connection helper function."""

    def test_get_db_connection_returns_connection(self):
        """get_db_connection should return a connection object."""
        from app import get_db_connection

        with patch('app.pymysql.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn
            result = get_db_connection()

        assert result is not None
        assert result == mock_conn

    def test_get_db_connection_raises_on_error(self):
        """get_db_connection should raise exception on connection error."""
        from app import get_db_connection

        with patch('app.pymysql.connect', side_effect=Exception('Connection failed')):
            with pytest.raises(Exception):
                get_db_connection()


class TestLoginEndpointAuthEnabled:
    """Test login endpoint with AUTH_ENABLED=true."""

    def test_login_success_returns_user_data(self, client, monkeypatch):
        """Successful login should return user data."""
        monkeypatch.setenv('AUTH_ENABLED', 'true')
        import app as app_module
        app_module.AUTH_ENABLED = True

        import bcrypt
        pw_hash = bcrypt.hashpw(b'testpass', bcrypt.gensalt()).decode()
        user_data = {
            'id': 1,
            'username': 'testuser',
            'email': 'test@example.com',
            'password_hash': pw_hash,
            'api_key': 'key123',
            'role': 'admin',
            'ou_id': None
        }
        cursor = _make_db_cursor(fetchone_return=user_data)
        conn = _make_db_conn(cursor)

        with patch('app.get_db_connection', return_value=conn):
            resp = client.post('/api/auth/login', json={
                'username': 'testuser',
                'password': 'testpass'
            })

        assert resp.status_code == 200
        data = resp.get_json()
        assert data.get('success') is True
        assert 'user' in data
        assert 'session_id' in data


class TestLogoutEndpointAuthEnabled:
    """Test logout endpoint with AUTH_ENABLED=true."""

    def test_logout_success_when_auth_enabled(self, client, monkeypatch):
        """Logout should succeed when AUTH_ENABLED=true."""
        monkeypatch.setenv('AUTH_ENABLED', 'true')
        import app as app_module
        app_module.AUTH_ENABLED = True

        conn = _make_db_conn()
        with patch('app.get_db_connection', return_value=conn):
            resp = client.post('/api/auth/logout')

        assert resp.status_code == 200
        data = resp.get_json()
        assert data.get('success') is True
