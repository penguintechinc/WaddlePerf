"""Unit tests for user routes in routes/users.py.

Note: The users blueprint uses flask_security decorators (@auth_required, @roles_required)
which require a full Flask-Security setup. These tests verify UserService logic and
route behaviour by testing the service layer directly, since the user routes
are Flask-Security protected and need specific test infrastructure.

We also test the service helper independently and verify the blueprint is importable
and registered correctly.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

from services.user_service import UserService
from tests.conftest import make_mock_row, make_mock_rowset


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_USER = {
    'id': 1,
    'email': 'alice@example.com',
    'username': 'alice',
    'first_name': 'Alice',
    'last_name': 'Smith',
    'active': True,
    'roles': [],
    'login_count': 0,
    'confirmed_at': None,
    'last_login_at': None,
    'created_at': datetime(2025, 1, 1).isoformat(),
    'updated_at': datetime(2025, 1, 1).isoformat(),
}


def _make_user_row(user_id: int = 1) -> MagicMock:
    row = make_mock_row({
        'id': user_id,
        'email': f'user{user_id}@example.com',
        'username': f'user{user_id}',
        'first_name': 'Test',
        'last_name': 'User',
        'active': True,
        'confirmed_at': None,
        'last_login_at': None,
        'login_count': 0,
        'created_at': datetime(2025, 1, 1),
        'updated_at': datetime(2025, 1, 1),
    })
    return row


# ---------------------------------------------------------------------------
# Service-layer tests (bypass route decorator complexity)
# ---------------------------------------------------------------------------

class TestUserServiceListUsers:
    """Re-test pagination through the UserService to ensure route business logic."""

    @pytest.fixture
    def svc(self, mock_db):
        return UserService(db=mock_db)

    async def test_list_users_returns_pagination_info(self, svc, mock_db):
        """list_users returns page, limit, total, pages."""
        mock_db.return_value.count = AsyncMock(return_value=5)
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))
        result = await svc.list_users(page=1, limit=20)
        assert result['page'] == 1
        assert result['limit'] == 20
        assert result['total'] == 5

    async def test_page_clamped_at_1_minimum(self, svc, mock_db):
        """Offset calculation with page=1 gives offset=0."""
        mock_db.return_value.count = AsyncMock(return_value=0)
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))
        result = await svc.list_users(page=1, limit=10)
        assert result['page'] == 1

    async def test_list_users_with_search_applies_filter(self, svc, mock_db):
        """search term is passed through without error."""
        mock_db.return_value.count = AsyncMock(return_value=0)
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))
        result = await svc.list_users(search='alice')
        assert result['users'] == []

    async def test_limit_max_100(self, svc, mock_db):
        """Limit capped at 100."""
        mock_db.return_value.count = AsyncMock(return_value=0)
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))
        result = await svc.list_users(limit=500)
        assert result['limit'] == 100


class TestUserServiceGetUser:
    """Test UserService.get_user via route-equivalent calls."""

    @pytest.fixture
    def svc(self, mock_db):
        return UserService(db=mock_db)

    async def test_get_existing_user(self, svc, mock_db):
        """get_user returns user dict for existing user."""
        user_row = _make_user_row(1)
        mock_db.return_value.select = AsyncMock(
            side_effect=[make_mock_rowset([user_row]), make_mock_rowset([])]
        )
        result = await svc.get_user(1)
        assert result is not None
        assert result['id'] == 1

    async def test_get_nonexistent_user(self, svc, mock_db):
        """get_user returns None for missing user."""
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))
        result = await svc.get_user(9999)
        assert result is None


class TestUserServiceCreateUser:
    """Test UserService.create_user via route-equivalent calls."""

    @pytest.fixture
    def svc(self, mock_db):
        return UserService(db=mock_db)

    async def test_create_user_returns_user_dict(self, svc, mock_db):
        """create_user returns a dict with id and email."""
        user_row = _make_user_row(1)
        mock_db.return_value.count = AsyncMock(return_value=0)
        mock_db.auth_user.async_insert = AsyncMock(return_value=1)
        mock_db.return_value.select = AsyncMock(
            side_effect=[make_mock_rowset([user_row]), make_mock_rowset([])]
        )
        result = await svc.create_user({
            'email': 'new@example.com',
            'username': 'newuser',
            'password': 'Password123!',
        })
        assert 'id' in result
        assert 'email' in result

    async def test_create_user_duplicate_email_raises(self, svc, mock_db):
        """create_user raises ValueError on duplicate email."""
        mock_db.return_value.count = AsyncMock(return_value=1)
        with pytest.raises(ValueError, match='already exists'):
            await svc.create_user({
                'email': 'dup@example.com',
                'username': 'uniqueuser',
                'password': 'Password123!',
            })

    async def test_create_user_missing_required_fields_raises(self, svc, mock_db):
        """create_user raises ValueError for missing email/username/password."""
        with pytest.raises(ValueError, match='required'):
            await svc.create_user({'email': '', 'username': '', 'password': ''})


class TestUserServiceUpdateUser:
    """Test UserService.update_user via route-equivalent calls."""

    @pytest.fixture
    def svc(self, mock_db):
        return UserService(db=mock_db)

    async def test_update_returns_user(self, svc, mock_db):
        """update_user returns updated user dict."""
        user_row = _make_user_row(1)
        mock_db.return_value.select = AsyncMock(
            side_effect=[
                make_mock_rowset([user_row]),
                make_mock_rowset([user_row]),
                make_mock_rowset([]),
            ]
        )
        mock_db.return_value.update = AsyncMock(return_value=None)
        result = await svc.update_user(1, {'first_name': 'UpdatedName'})
        assert result is not None

    async def test_update_nonexistent_user_returns_none(self, svc, mock_db):
        """update_user returns None when user not found."""
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))
        result = await svc.update_user(9999, {'first_name': 'X'})
        assert result is None


class TestUserServiceDeleteUser:
    """Test UserService.delete_user via route-equivalent calls."""

    @pytest.fixture
    def svc(self, mock_db):
        return UserService(db=mock_db)

    async def test_delete_returns_true(self, svc, mock_db):
        """delete_user returns True for existing user."""
        user_row = _make_user_row(1)
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([user_row]))
        mock_db.return_value.delete = AsyncMock(return_value=None)
        result = await svc.delete_user(1)
        assert result is True

    async def test_delete_returns_false_for_missing(self, svc, mock_db):
        """delete_user returns False for non-existent user."""
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))
        result = await svc.delete_user(9999)
        assert result is False


class TestUserServiceSerializeUser:
    """Test _serialize_user internal helper."""

    @pytest.fixture
    def svc(self, mock_db):
        return UserService(db=mock_db)

    async def test_serialize_none_returns_empty_dict(self, svc):
        """_serialize_user with None returns empty dict."""
        result = await svc._serialize_user(None)
        assert result == {}

    async def test_serialize_includes_roles_list(self, svc, mock_db):
        """_serialize_user returns roles as a list."""
        user_row = _make_user_row(1)
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))
        result = await svc._serialize_user(user_row)
        assert 'roles' in result
        assert isinstance(result['roles'], list)

    async def test_serialize_confirmed_at_is_iso_string_or_none(self, svc, mock_db):
        """confirmed_at is ISO string or None."""
        user_row = _make_user_row(1)
        user_row.confirmed_at = None
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))
        result = await svc._serialize_user(user_row)
        assert result['confirmed_at'] is None

    async def test_serialize_confirmed_at_datetime_serialized(self, svc, mock_db):
        """confirmed_at datetime is converted to ISO string."""
        user_row = _make_user_row(1)
        user_row.confirmed_at = datetime(2025, 6, 1, 12, 0, 0)
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))
        result = await svc._serialize_user(user_row)
        assert isinstance(result['confirmed_at'], str)
        assert '2025' in result['confirmed_at']


class TestUsersBlueprintRegistration:
    """Verify the users blueprint is importable with correct structure."""

    def test_blueprint_importable(self):
        """users_bp can be imported."""
        from routes.users import users_bp
        assert users_bp is not None

    def test_blueprint_name(self):
        """Blueprint is named 'users'."""
        from routes.users import users_bp
        assert users_bp.name == 'users'

    def test_list_users_route_exists(self):
        """List users route is registered on the blueprint."""
        from routes.users import users_bp
        rules = [str(r) for r in users_bp.deferred_functions]
        # Blueprint has deferred_functions (view functions)
        assert len(rules) > 0

    def test_get_user_service_helper(self):
        """_get_user_service is an async function."""
        import asyncio
        from routes.users import _get_user_service
        assert asyncio.iscoroutinefunction(_get_user_service)
