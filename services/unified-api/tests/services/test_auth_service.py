"""Unit tests for AuthService"""
import sys
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, AsyncMock, patch
import jwt
import bcrypt

# qrcode may not be installed in test environments; mock it before import
if 'qrcode' not in sys.modules:
    sys.modules['qrcode'] = MagicMock()

from services.auth_service import AuthService, AuthResponse, UserInfo  # noqa: E402
from tests.conftest import make_mock_row, make_mock_rowset  # noqa: E402


JWT_SECRET = 'test-jwt-secret-for-testing-only'
JWT_EXPIRATION_HOURS = 24


@pytest.fixture
def auth_service(mock_db, mock_config):
    """Provide an AuthService instance wired to a mock DB."""
    return AuthService(mock_db, mock_config)


def _make_active_user(user_id: int = 1, password: str = 'correct_password') -> MagicMock:
    """Create a mock user row with a hashed password."""
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user = make_mock_row({
        'id': user_id,
        'email': 'user@example.com',
        'username': 'testuser',
        'password_hash': hashed,
        'is_active': True,
        'mfa_enabled': False,
        'mfa_secret': None,
        'role': 'user',
    })
    return user


def _make_refresh_token_row(expires_future: bool = True, is_revoked: bool = False) -> MagicMock:
    """Create a mock refresh token row."""
    if expires_future:
        expires_at = datetime.now(timezone.utc) + timedelta(days=15)
    else:
        expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    return make_mock_row({
        'id': 10,
        'user_id': 1,
        'token': 'some-refresh-token',
        'expires_at': expires_at,
        'is_revoked': is_revoked,
    })


class TestHashPassword:
    """Test _hash_password and _verify_password methods."""

    def test_hash_produces_non_plaintext(self, auth_service):
        """Hashed password differs from plaintext."""
        hashed = auth_service._hash_password('mypassword')
        assert hashed != 'mypassword'

    def test_hash_is_bcrypt(self, auth_service):
        """Hashed password is valid bcrypt."""
        hashed = auth_service._hash_password('secret')
        assert bcrypt.checkpw('secret'.encode(), hashed.encode())

    def test_verify_password_correct(self, auth_service):
        """Correct password verifies successfully."""
        hashed = auth_service._hash_password('correct')
        assert auth_service._verify_password('correct', hashed) is True

    def test_verify_password_wrong(self, auth_service):
        """Wrong password fails verification."""
        hashed = auth_service._hash_password('correct')
        assert auth_service._verify_password('wrong', hashed) is False

    def test_verify_password_invalid_hash(self, auth_service):
        """Invalid hash string returns False instead of raising."""
        assert auth_service._verify_password('password', 'not-a-hash') is False


class TestGenerateAndVerifyJwt:
    """Test _generate_jwt and _verify_jwt."""

    def test_generate_access_token(self, auth_service):
        """Access token is a non-empty string."""
        token = auth_service._generate_jwt(user_id=42, token_type='access')
        assert isinstance(token, str)
        assert len(token) > 0

    def test_access_token_payload(self, auth_service):
        """Access token contains expected claims."""
        token = auth_service._generate_jwt(user_id=7, token_type='access')
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        assert payload['user_id'] == 7
        assert payload['token_type'] == 'access'

    def test_refresh_token_type(self, auth_service):
        """Refresh token has token_type=refresh."""
        token = auth_service._generate_jwt(user_id=3, token_type='refresh')
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        assert payload['token_type'] == 'refresh'

    def test_verify_valid_token(self, auth_service):
        """Valid token returns decoded payload."""
        token = auth_service._generate_jwt(user_id=5, token_type='access')
        payload = auth_service._verify_jwt(token)
        assert payload is not None
        assert payload['user_id'] == 5

    def test_verify_invalid_token_returns_none(self, auth_service):
        """Invalid/tampered token returns None."""
        result = auth_service._verify_jwt('definitely.not.a.valid.token')
        assert result is None

    def test_verify_expired_token_returns_none(self, auth_service):
        """Expired token returns None."""
        past = datetime.now(timezone.utc) - timedelta(hours=2)
        payload = {
            'user_id': 1,
            'token_type': 'access',
            'iat': past,
            'exp': past + timedelta(seconds=1),
        }
        expired_token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
        result = auth_service._verify_jwt(expired_token)
        assert result is None


class TestAuthenticate:
    """Test AuthService.authenticate()."""

    async def test_login_success(self, auth_service, mock_db):
        """Valid credentials return success with tokens."""
        user = _make_active_user(user_id=1)
        rowset = make_mock_rowset([user])
        mock_db.return_value.select = AsyncMock(return_value=rowset)

        result = await auth_service.authenticate('user@example.com', 'correct_password')

        assert result.success is True
        assert result.access_token is not None
        assert result.refresh_token is not None
        assert result.user_id == 1

    async def test_login_wrong_password(self, auth_service, mock_db):
        """Wrong password returns failure."""
        user = _make_active_user(user_id=1)
        rowset = make_mock_rowset([user])
        mock_db.return_value.select = AsyncMock(return_value=rowset)

        result = await auth_service.authenticate('user@example.com', 'wrong_password')

        assert result.success is False
        assert result.error is not None

    async def test_login_unknown_email(self, auth_service, mock_db):
        """Unknown email/username returns failure."""
        empty_rowset = make_mock_rowset([])
        mock_db.return_value.select = AsyncMock(return_value=empty_rowset)

        result = await auth_service.authenticate('nobody@example.com', 'anypassword')

        assert result.success is False
        assert 'Invalid' in result.error

    async def test_login_inactive_user(self, auth_service, mock_db):
        """Inactive user cannot authenticate."""
        user = _make_active_user(user_id=2)
        user.is_active = False
        rowset = make_mock_rowset([user])
        mock_db.return_value.select = AsyncMock(return_value=rowset)

        result = await auth_service.authenticate('user@example.com', 'correct_password')

        assert result.success is False
        assert 'inactive' in result.error.lower()

    async def test_login_mfa_required_when_not_provided(self, auth_service, mock_db):
        """MFA-enabled user needs mfa_token."""
        user = _make_active_user(user_id=3)
        user.mfa_enabled = True
        user.mfa_secret = 'JBSWY3DPEHPK3PXP'
        rowset = make_mock_rowset([user])
        mock_db.return_value.select = AsyncMock(return_value=rowset)

        result = await auth_service.authenticate('user@example.com', 'correct_password')

        assert result.success is False
        assert result.mfa_required is True

    async def test_login_stores_refresh_token(self, auth_service, mock_db):
        """Successful login stores refresh token in DB."""
        user = _make_active_user(user_id=1)
        rowset = make_mock_rowset([user])
        mock_db.return_value.select = AsyncMock(return_value=rowset)

        await auth_service.authenticate('user@example.com', 'correct_password')

        mock_db.refresh_tokens.async_insert.assert_called_once()


class TestRefreshAccessToken:
    """Test AuthService.refresh_access_token()."""

    async def test_valid_refresh_token(self, auth_service, mock_db):
        """Valid refresh token returns new access token."""
        refresh_token = auth_service._generate_jwt(user_id=1, token_type='refresh')
        token_row = _make_refresh_token_row(expires_future=True)
        rowset = make_mock_rowset([token_row])
        mock_db.return_value.select = AsyncMock(return_value=rowset)

        result = await auth_service.refresh_access_token(refresh_token)

        assert result.success is True
        assert result.access_token is not None

    async def test_invalid_refresh_token(self, auth_service, mock_db):
        """Invalid/malformed token returns failure."""
        result = await auth_service.refresh_access_token('not-a-jwt')

        assert result.success is False
        assert 'Invalid' in result.error

    async def test_wrong_token_type(self, auth_service, mock_db):
        """Access token used as refresh token returns failure."""
        access_token = auth_service._generate_jwt(user_id=1, token_type='access')
        result = await auth_service.refresh_access_token(access_token)

        assert result.success is False

    async def test_revoked_refresh_token(self, auth_service, mock_db):
        """Revoked refresh token returns failure."""
        refresh_token = auth_service._generate_jwt(user_id=1, token_type='refresh')
        empty_rowset = make_mock_rowset([])
        mock_db.return_value.select = AsyncMock(return_value=empty_rowset)

        result = await auth_service.refresh_access_token(refresh_token)

        assert result.success is False

    async def test_expired_token_record(self, auth_service, mock_db):
        """Expired token record in DB returns failure."""
        refresh_token = auth_service._generate_jwt(user_id=1, token_type='refresh')
        expired_row = _make_refresh_token_row(expires_future=False)
        rowset = make_mock_rowset([expired_row])
        mock_db.return_value.select = AsyncMock(return_value=rowset)

        result = await auth_service.refresh_access_token(refresh_token)

        assert result.success is False
        assert 'expired' in result.error.lower()


class TestRevokeTokens:
    """Test AuthService.revoke_tokens()."""

    async def test_revoke_tokens_success(self, auth_service, mock_db):
        """Token revocation succeeds and returns success."""
        mock_db.return_value.update = AsyncMock(return_value=None)

        result = await auth_service.revoke_tokens(user_id=1)

        assert result.success is True
        mock_db.return_value.update.assert_called_once()

    async def test_revoke_marks_is_revoked(self, auth_service, mock_db):
        """Update is called with is_revoked=True."""
        mock_db.return_value.update = AsyncMock(return_value=None)

        await auth_service.revoke_tokens(user_id=5)

        mock_db.return_value.update.assert_called_once_with(is_revoked=True)


class TestSendPasswordResetEmail:
    """Test AuthService.send_password_reset_email()."""

    async def test_known_email_returns_success(self, auth_service, mock_db):
        """Existing email triggers token creation and returns success."""
        user = _make_active_user()
        rowset = make_mock_rowset([user])
        mock_db.return_value.select = AsyncMock(return_value=rowset)

        result = await auth_service.send_password_reset_email('user@example.com')

        assert result.success is True
        mock_db.password_reset_tokens.async_insert.assert_called_once()

    async def test_unknown_email_still_returns_success(self, auth_service, mock_db):
        """Unknown email returns success (no disclosure)."""
        empty_rowset = make_mock_rowset([])
        mock_db.return_value.select = AsyncMock(return_value=empty_rowset)

        result = await auth_service.send_password_reset_email('ghost@example.com')

        assert result.success is True


class TestResetPassword:
    """Test AuthService.reset_password()."""

    async def test_valid_reset_token(self, auth_service, mock_db):
        """Valid reset token updates password and returns success."""
        reset_token = auth_service._generate_jwt(user_id=1, token_type='reset')
        token_row = make_mock_row({
            'id': 20,
            'user_id': 1,
            'token': reset_token,
            'expires_at': datetime.now(timezone.utc) + timedelta(hours=1),
            'is_used': False,
        })
        rowset = make_mock_rowset([token_row])
        mock_db.return_value.select = AsyncMock(return_value=rowset)
        mock_db.return_value.update = AsyncMock(return_value=None)

        result = await auth_service.reset_password(reset_token, 'newpassword123')

        assert result.success is True

    async def test_invalid_token_type(self, auth_service, mock_db):
        """Access token used as reset token is rejected."""
        access_token = auth_service._generate_jwt(user_id=1, token_type='access')
        result = await auth_service.reset_password(access_token, 'newpassword123')

        assert result.success is False

    async def test_expired_reset_token(self, auth_service, mock_db):
        """Expired reset token record returns failure."""
        reset_token = auth_service._generate_jwt(user_id=1, token_type='reset')
        expired_row = make_mock_row({
            'id': 20,
            'user_id': 1,
            'token': reset_token,
            'expires_at': datetime.now(timezone.utc) - timedelta(hours=1),
            'is_used': False,
        })
        rowset = make_mock_rowset([expired_row])
        mock_db.return_value.select = AsyncMock(return_value=rowset)

        result = await auth_service.reset_password(reset_token, 'newpassword123')

        assert result.success is False
        assert 'expired' in result.error.lower()


class TestGetUserById:
    """Test AuthService.get_user_by_id()."""

    async def test_existing_user(self, auth_service, mock_db):
        """Returns UserInfo for an existing user."""
        user = make_mock_row({
            'id': 1,
            'username': 'alice',
            'email': 'alice@example.com',
            'role': 'admin',
        })
        rowset = make_mock_rowset([user])
        mock_db.return_value.select = AsyncMock(return_value=rowset)

        result = await auth_service.get_user_by_id(1)

        assert isinstance(result, UserInfo)
        assert result.id == 1
        assert result.email == 'alice@example.com'
        assert result.role == 'admin'

    async def test_nonexistent_user(self, auth_service, mock_db):
        """Returns None when user not found."""
        empty_rowset = make_mock_rowset([])
        mock_db.return_value.select = AsyncMock(return_value=empty_rowset)

        result = await auth_service.get_user_by_id(9999)

        assert result is None

    async def test_user_role_defaults_to_user(self, auth_service, mock_db):
        """Role defaults to 'user' when row.role is None."""
        user = make_mock_row({
            'id': 2,
            'username': 'bob',
            'email': 'bob@example.com',
            'role': None,
        })
        rowset = make_mock_rowset([user])
        mock_db.return_value.select = AsyncMock(return_value=rowset)

        result = await auth_service.get_user_by_id(2)

        assert result.role == 'user'
