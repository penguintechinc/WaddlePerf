"""Integration-style tests for auth routes using the Quart test client."""
import sys
import json
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import jwt

# qrcode may not be installed in the test environment; stub it before import
if 'qrcode' not in sys.modules:
    sys.modules['qrcode'] = MagicMock()

from services.auth_service import AuthResponse, UserInfo  # noqa: E402
from tests.conftest import make_mock_row, make_mock_rowset  # noqa: E402

JWT_SECRET = 'test-jwt-secret-for-testing-only'


def _make_access_token(user_id: int = 1) -> str:
    """Generate a valid access JWT for tests."""
    now = datetime.now(timezone.utc)
    payload = {
        'user_id': user_id,
        'token_type': 'access',
        'iat': now,
        'exp': now + timedelta(hours=24),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')


class TestLoginRoute:
    """Test POST /api/v1/auth/login"""

    async def test_login_success_returns_200(self, client, app):
        """Valid credentials return 200 with tokens."""
        success_response = AuthResponse(
            access_token='access.tok.en',
            refresh_token='refresh.tok.en',
            user_id=1,
            success=True,
        )
        app.auth_service.authenticate = AsyncMock(return_value=success_response)

        async with client as c:
            resp = await c.post(
                '/api/v1/auth/login',
                json={'email': 'user@example.com', 'password': 'password123'},
            )

        assert resp.status_code == 200
        data = await resp.get_json()
        assert data['success'] is True
        assert 'access_token' in data
        assert 'refresh_token' in data

    async def test_login_wrong_password_returns_401(self, client, app):
        """Wrong password returns 401."""
        fail_response = AuthResponse(success=False, error='Invalid email or password')
        app.auth_service.authenticate = AsyncMock(return_value=fail_response)

        async with client as c:
            resp = await c.post(
                '/api/v1/auth/login',
                json={'email': 'user@example.com', 'password': 'wrong'},
            )

        assert resp.status_code == 401

    async def test_login_missing_email_returns_400(self, client, app):
        """Missing email returns 400."""
        async with client as c:
            resp = await c.post(
                '/api/v1/auth/login',
                json={'password': 'password123'},
            )

        assert resp.status_code == 400

    async def test_login_missing_password_returns_400(self, client, app):
        """Missing password returns 400."""
        async with client as c:
            resp = await c.post(
                '/api/v1/auth/login',
                json={'email': 'user@example.com'},
            )

        assert resp.status_code == 400

    async def test_login_mfa_required_returns_403(self, client, app):
        """MFA required returns 403."""
        mfa_response = AuthResponse(
            success=False,
            mfa_required=True,
            error='MFA token required',
        )
        app.auth_service.authenticate = AsyncMock(return_value=mfa_response)

        async with client as c:
            resp = await c.post(
                '/api/v1/auth/login',
                json={'email': 'user@example.com', 'password': 'correct'},
            )

        assert resp.status_code == 403
        data = await resp.get_json()
        assert data['mfa_required'] is True

    async def test_login_response_contains_user_id(self, client, app):
        """Successful login response contains user_id."""
        success_response = AuthResponse(
            access_token='tok', refresh_token='ref', user_id=42, success=True
        )
        app.auth_service.authenticate = AsyncMock(return_value=success_response)

        async with client as c:
            resp = await c.post(
                '/api/v1/auth/login',
                json={'email': 'u@example.com', 'password': 'p'},
            )

        data = await resp.get_json()
        assert data['user_id'] == 42

    async def test_login_uses_username_field(self, client, app):
        """username field is also accepted as email_or_username."""
        success_response = AuthResponse(
            access_token='tok', refresh_token='ref', user_id=1, success=True
        )
        app.auth_service.authenticate = AsyncMock(return_value=success_response)

        async with client as c:
            resp = await c.post(
                '/api/v1/auth/login',
                json={'username': 'testuser', 'password': 'password123'},
            )

        assert resp.status_code == 200


class TestRefreshRoute:
    """Test POST /api/v1/auth/refresh"""

    async def test_valid_refresh_token_returns_200(self, client, app):
        """Valid refresh token returns new access token."""
        refresh_response = AuthResponse(
            access_token='new.access.token', user_id=1, success=True
        )
        app.auth_service.refresh_access_token = AsyncMock(return_value=refresh_response)

        async with client as c:
            resp = await c.post(
                '/api/v1/auth/refresh',
                json={'refresh_token': 'valid.refresh.token'},
            )

        assert resp.status_code == 200
        data = await resp.get_json()
        assert data['success'] is True
        assert 'access_token' in data

    async def test_invalid_refresh_token_returns_401(self, client, app):
        """Invalid refresh token returns 401."""
        fail_response = AuthResponse(success=False, error='Invalid refresh token')
        app.auth_service.refresh_access_token = AsyncMock(return_value=fail_response)

        async with client as c:
            resp = await c.post(
                '/api/v1/auth/refresh',
                json={'refresh_token': 'bad-token'},
            )

        assert resp.status_code == 401

    async def test_missing_refresh_token_returns_400(self, client, app):
        """Missing refresh_token field returns 400."""
        async with client as c:
            resp = await c.post('/api/v1/auth/refresh', json={})

        assert resp.status_code == 400


class TestLogoutRoute:
    """Test POST /api/v1/auth/logout"""

    async def test_logout_with_valid_token_returns_200(self, client, app):
        """Authenticated logout returns 200."""
        app.auth_service.revoke_tokens = AsyncMock(
            return_value=AuthResponse(success=True)
        )
        token = _make_access_token(user_id=1)

        async with client as c:
            resp = await c.post(
                '/api/v1/auth/logout',
                headers={'Authorization': f'Bearer {token}'},
            )

        assert resp.status_code == 200
        data = await resp.get_json()
        assert data['success'] is True

    async def test_logout_without_token_returns_401(self, client, app):
        """Logout without auth header returns 401."""
        async with client as c:
            resp = await c.post('/api/v1/auth/logout')

        assert resp.status_code == 401

    async def test_logout_with_invalid_token_returns_401(self, client, app):
        """Invalid JWT returns 401."""
        async with client as c:
            resp = await c.post(
                '/api/v1/auth/logout',
                headers={'Authorization': 'Bearer totally.invalid.token'},
            )

        assert resp.status_code == 401


class TestForgotPasswordRoute:
    """Test POST /api/v1/auth/forgot-password"""

    async def test_returns_200_for_known_email(self, client, app):
        """Known email returns 200 with success message."""
        app.auth_service.send_password_reset_email = AsyncMock(
            return_value=AuthResponse(success=True)
        )

        async with client as c:
            resp = await c.post(
                '/api/v1/auth/forgot-password',
                json={'email': 'user@example.com'},
            )

        assert resp.status_code == 200
        data = await resp.get_json()
        assert data['success'] is True

    async def test_returns_200_for_unknown_email(self, client, app):
        """Unknown email also returns 200 (no disclosure)."""
        app.auth_service.send_password_reset_email = AsyncMock(
            return_value=AuthResponse(success=True)
        )

        async with client as c:
            resp = await c.post(
                '/api/v1/auth/forgot-password',
                json={'email': 'ghost@example.com'},
            )

        assert resp.status_code == 200

    async def test_missing_email_returns_400(self, client, app):
        """Missing email field returns 400."""
        async with client as c:
            resp = await c.post('/api/v1/auth/forgot-password', json={})

        assert resp.status_code == 400


class TestAuthStatusRoute:
    """Test GET /api/v1/auth/status"""

    async def test_authenticated_with_valid_token(self, client, app):
        """Valid access token returns authenticated: true."""
        token = _make_access_token(user_id=5)
        user_info = UserInfo(id=5, username='alice', email='alice@example.com', role='admin')
        app.auth_service.get_user_by_id = AsyncMock(return_value=user_info)

        async with client as c:
            resp = await c.get(
                '/api/v1/auth/status',
                headers={'Authorization': f'Bearer {token}'},
            )

        assert resp.status_code == 200
        data = await resp.get_json()
        assert data['authenticated'] is True
        assert data['user']['id'] == 5

    async def test_unauthenticated_without_token(self, client, app):
        """Missing token returns authenticated: false (not error)."""
        async with client as c:
            resp = await c.get('/api/v1/auth/status')

        assert resp.status_code == 200
        data = await resp.get_json()
        assert data['authenticated'] is False
        assert data['auth_enabled'] is True

    async def test_invalid_token_returns_unauthenticated(self, client, app):
        """Invalid JWT returns authenticated: false."""
        async with client as c:
            resp = await c.get(
                '/api/v1/auth/status',
                headers={'Authorization': 'Bearer bad.jwt.token'},
            )

        assert resp.status_code == 200
        data = await resp.get_json()
        assert data['authenticated'] is False


class TestChangePasswordRoute:
    """Test POST /api/v1/auth/change-password"""

    async def test_change_password_success(self, client, app):
        """Authenticated user can change password."""
        app.auth_service.change_password = AsyncMock(
            return_value=AuthResponse(success=True)
        )
        token = _make_access_token(user_id=1)

        # Patch password validator to pass
        with patch('routes.auth._password_validator') as mock_validator:
            mock_result = MagicMock()
            mock_result.is_valid = True
            mock_validator.return_value = mock_result

            async with client as c:
                resp = await c.post(
                    '/api/v1/auth/change-password',
                    headers={'Authorization': f'Bearer {token}'},
                    json={
                        'current_password': 'OldPass123!',
                        'new_password': 'NewPass456!',
                    },
                )

        assert resp.status_code == 200

    async def test_change_password_missing_fields_returns_400(self, client, app):
        """Missing current or new password returns 400."""
        token = _make_access_token(user_id=1)

        async with client as c:
            resp = await c.post(
                '/api/v1/auth/change-password',
                headers={'Authorization': f'Bearer {token}'},
                json={'current_password': 'OldPass123!'},
            )

        assert resp.status_code == 400

    async def test_change_password_without_auth_returns_401(self, client, app):
        """Unauthenticated request returns 401."""
        async with client as c:
            resp = await c.post(
                '/api/v1/auth/change-password',
                json={'current_password': 'x', 'new_password': 'y'},
            )

        assert resp.status_code == 401
