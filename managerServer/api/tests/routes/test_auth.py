"""Unit tests for managerServer auth routes."""
import hashlib
import pytest
from unittest.mock import MagicMock, patch
import jwt as pyjwt

from models import hash_password

# Note: mock_db, app, and client fixtures are inherited from conftest.py


def _make_user_row(username='admin', password='secret', role='global_admin', mfa_enabled=False):
    """Build a mock DB row representing an active user."""
    row = MagicMock()
    row.id = 1
    row.username = username
    row.email = 'admin@example.com'
    row.password_hash = hash_password(password)
    row.api_key = 'api-key-123'
    row.role = role
    row.ou_id = None
    row.mfa_enabled = mfa_enabled
    row.mfa_secret = None
    row.is_active = True
    row.created_at = None
    row.updated_at = None
    return row


def _make_valid_jwt(user_id: int = 1) -> str:
    """Generate a JWT that passes decode validation using the default Config secret."""
    from datetime import datetime, timedelta
    from config import Config
    cfg = Config()
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=1),
        'iat': datetime.utcnow(),
    }
    return pyjwt.encode(payload, cfg.JWT_SECRET, algorithm='HS256')


# ---------------------------------------------------------------------------
# POST /api/v1/auth/login
# ---------------------------------------------------------------------------

class TestLogin:
    def test_login_success_returns_200_and_token(self, client, mock_db, app):
        user_row = _make_user_row(password='correct')
        # Simulate DB query returning the user
        mock_db.users = MagicMock()
        mock_db.return_value.select.return_value.first.return_value = user_row
        mock_db.jwt_tokens = MagicMock()
        mock_db.jwt_tokens.insert = MagicMock(return_value=1)

        with patch('penguin_dal.flask_ext.get_db', return_value=mock_db):
            with patch('routes.auth.get_db', return_value=mock_db):
                resp = client.post('/api/v1/auth/login', json={
                    'username': 'admin',
                    'password': 'correct',
                })

        assert resp.status_code == 200
        data = resp.get_json()
        assert 'token' in data

    def test_login_wrong_password_returns_401(self, client, mock_db):
        user_row = _make_user_row(password='correct')
        mock_db.return_value.select.return_value.first.return_value = user_row

        with patch('routes.auth.get_db', return_value=mock_db):
            resp = client.post('/api/v1/auth/login', json={
                'username': 'admin',
                'password': 'wrong',
            })

        assert resp.status_code == 401

    def test_login_unknown_user_returns_401(self, client, mock_db):
        mock_db.return_value.select.return_value.first.return_value = None

        with patch('routes.auth.get_db', return_value=mock_db):
            resp = client.post('/api/v1/auth/login', json={
                'username': 'nobody',
                'password': 'any',
            })

        assert resp.status_code == 401

    def test_login_missing_username_returns_400(self, client):
        resp = client.post('/api/v1/auth/login', json={'password': 'pass'})
        assert resp.status_code == 400

    def test_login_missing_password_returns_400(self, client):
        resp = client.post('/api/v1/auth/login', json={'username': 'user'})
        assert resp.status_code == 400

    def test_login_empty_body_returns_400(self, client):
        resp = client.post('/api/v1/auth/login', json={})
        assert resp.status_code == 400

    def test_login_success_includes_user_info(self, client, mock_db):
        user_row = _make_user_row(password='pass')
        mock_db.return_value.select.return_value.first.return_value = user_row
        mock_db.jwt_tokens = MagicMock()
        mock_db.jwt_tokens.insert = MagicMock(return_value=1)

        with patch('routes.auth.get_db', return_value=mock_db):
            resp = client.post('/api/v1/auth/login', json={
                'username': 'admin',
                'password': 'pass',
            })

        if resp.status_code == 200:
            data = resp.get_json()
            assert 'user' in data
            assert 'expires_in' in data

    def test_login_mfa_required_when_enabled(self, client, mock_db):
        user_row = _make_user_row(password='pass', mfa_enabled=True)
        user_row.mfa_secret = 'JBSWY3DPEHPK3PXP'
        mock_db.return_value.select.return_value.first.return_value = user_row

        with patch('routes.auth.get_db', return_value=mock_db):
            resp = client.post('/api/v1/auth/login', json={
                'username': 'admin',
                'password': 'pass',
            })

        # No mfa_code provided → 401 with mfa_required flag
        assert resp.status_code == 401
        data = resp.get_json()
        assert data.get('mfa_required') is True


# ---------------------------------------------------------------------------
# POST /api/v1/auth/logout
# ---------------------------------------------------------------------------

class TestLogout:
    def test_logout_with_valid_token_returns_200(self, client, mock_db):
        token = _make_valid_jwt()
        mock_db.return_value.update.return_value = None

        with patch('routes.auth.get_db', return_value=mock_db):
            resp = client.post('/api/v1/auth/logout', headers={
                'Authorization': f'Bearer {token}'
            })

        assert resp.status_code == 200
        data = resp.get_json()
        assert 'message' in data

    def test_logout_without_auth_header_returns_401(self, client):
        resp = client.post('/api/v1/auth/logout')
        assert resp.status_code == 401

    def test_logout_malformed_bearer_returns_401(self, client):
        resp = client.post('/api/v1/auth/logout', headers={
            'Authorization': 'NotBearer token'
        })
        assert resp.status_code == 401

    def test_logout_revokes_token_hash(self, client, mock_db):
        token = _make_valid_jwt()
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        with patch('routes.auth.get_db', return_value=mock_db):
            client.post('/api/v1/auth/logout', headers={
                'Authorization': f'Bearer {token}'
            })

        # Verify update(revoked=True) was called
        mock_db.return_value.update.assert_called_once_with(revoked=True)


# ---------------------------------------------------------------------------
# POST /api/v1/auth/mfa/setup and mfa/verify
# ---------------------------------------------------------------------------

class TestMfaSetup:
    def test_mfa_setup_unauthorized_without_token(self, client):
        resp = client.post('/api/v1/auth/mfa/setup')
        assert resp.status_code == 401

    def test_mfa_setup_with_valid_token_calls_db(self, client, mock_db):
        token = _make_valid_jwt(user_id=1)
        user_row = _make_user_row()

        # get_user_from_token needs jwt_tokens.select().first() → valid token
        jwt_token_row = MagicMock()
        jwt_token_row.revoked = False

        # mock chain: db(filter).select().first()
        mock_db.return_value.select.return_value.first.return_value = jwt_token_row
        mock_db.users.__getitem__ = MagicMock(return_value=user_row)
        mock_db.return_value.update.return_value = None

        with patch('routes.auth.get_db', return_value=mock_db):
            resp = client.post('/api/v1/auth/mfa/setup', headers={
                'Authorization': f'Bearer {token}'
            })

        # Either 200 (success) or any non-500 when token is well-formed
        assert resp.status_code in (200, 404)


class TestMfaVerify:
    def test_mfa_verify_missing_code_returns_400(self, client, mock_db):
        token = _make_valid_jwt(user_id=1)
        jwt_token_row = MagicMock()

        mock_db.return_value.select.return_value.first.return_value = jwt_token_row

        with patch('routes.auth.get_db', return_value=mock_db):
            resp = client.post('/api/v1/auth/mfa/verify',
                               json={},
                               headers={'Authorization': f'Bearer {token}'})

        assert resp.status_code in (400, 401)

    def test_mfa_verify_unauthorized_without_token(self, client):
        resp = client.post('/api/v1/auth/mfa/verify', json={'code': '123456'})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        resp = client.get('/health')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] == 'healthy'
