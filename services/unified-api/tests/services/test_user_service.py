"""Unit tests for UserService"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock
import bcrypt

from services.user_service import UserService
from tests.conftest import make_mock_row, make_mock_rowset


@pytest.fixture
def user_service(mock_db):
    """Provide a UserService wired to a mock DB."""
    return UserService(db=mock_db)


def _make_user_row(
    user_id: int = 1,
    email: str = 'user@example.com',
    username: str = 'testuser',
    active: bool = True,
) -> MagicMock:
    """Build a mock auth_user row."""
    return make_mock_row({
        'id': user_id,
        'email': email,
        'username': username,
        'first_name': 'Test',
        'last_name': 'User',
        'active': active,
        'confirmed_at': None,
        'last_login_at': None,
        'login_count': 0,
        'created_at': datetime(2025, 1, 1),
        'updated_at': datetime(2025, 1, 1),
    })


class TestListUsers:
    """Test UserService.list_users()."""

    async def test_returns_dict_structure(self, user_service, mock_db):
        """list_users returns dict with users, total, page, limit, pages."""
        user_row = _make_user_row()
        rowset = make_mock_rowset([user_row])
        # count and select are on query proxy
        mock_db.return_value.count = AsyncMock(return_value=1)
        mock_db.return_value.select = AsyncMock(return_value=rowset)

        # _serialize_user also queries roles
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        result = await user_service.list_users()

        assert 'users' in result
        assert 'total' in result
        assert 'page' in result
        assert 'limit' in result
        assert 'pages' in result

    async def test_page_defaults_to_1(self, user_service, mock_db):
        """Default page is 1."""
        mock_db.return_value.count = AsyncMock(return_value=0)
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        result = await user_service.list_users()

        assert result['page'] == 1

    async def test_limit_cap_at_100(self, user_service, mock_db):
        """Limit is capped at 100."""
        mock_db.return_value.count = AsyncMock(return_value=0)
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        result = await user_service.list_users(limit=9999)

        assert result['limit'] == 100

    async def test_pages_calculation(self, user_service, mock_db):
        """pages field is ceiling division of total / limit."""
        mock_db.return_value.count = AsyncMock(return_value=25)
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        result = await user_service.list_users(limit=10)

        assert result['pages'] == 3  # ceil(25 / 10)

    async def test_empty_result(self, user_service, mock_db):
        """Empty database returns empty users list."""
        mock_db.return_value.count = AsyncMock(return_value=0)
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        result = await user_service.list_users()

        assert result['users'] == []
        assert result['total'] == 0


class TestGetUser:
    """Test UserService.get_user()."""

    async def test_returns_user_when_found(self, user_service, mock_db):
        """Returns serialized user dict when user exists."""
        user_row = _make_user_row(user_id=1)
        user_rowset = make_mock_rowset([user_row])
        empty_rowset = make_mock_rowset([])
        # First call gets user, subsequent calls get roles
        mock_db.return_value.select = AsyncMock(side_effect=[user_rowset, empty_rowset])

        result = await user_service.get_user(1)

        assert result is not None
        assert result['id'] == 1
        assert result['email'] == 'user@example.com'

    async def test_returns_none_when_not_found(self, user_service, mock_db):
        """Returns None when user ID doesn't exist."""
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        result = await user_service.get_user(9999)

        assert result is None

    async def test_user_dict_has_roles_key(self, user_service, mock_db):
        """Serialized user has a 'roles' list."""
        user_row = _make_user_row()
        mock_db.return_value.select = AsyncMock(
            side_effect=[make_mock_rowset([user_row]), make_mock_rowset([])]
        )

        result = await user_service.get_user(1)

        assert 'roles' in result
        assert isinstance(result['roles'], list)


class TestCreateUser:
    """Test UserService.create_user()."""

    async def test_create_user_success(self, user_service, mock_db):
        """Successfully creates user and returns serialized dict."""
        new_user_row = _make_user_row()
        mock_db.return_value.count = AsyncMock(return_value=0)
        mock_db.auth_user.async_insert = AsyncMock(return_value=1)
        mock_db.return_value.select = AsyncMock(
            side_effect=[make_mock_rowset([new_user_row]), make_mock_rowset([])]
        )

        result = await user_service.create_user({
            'email': 'new@example.com',
            'username': 'newuser',
            'password': 'password123',
        })

        assert result['email'] == 'user@example.com'
        mock_db.auth_user.async_insert.assert_called_once()

    async def test_password_is_hashed(self, user_service, mock_db):
        """Password stored is not the plaintext."""
        new_user_row = _make_user_row()
        mock_db.return_value.count = AsyncMock(return_value=0)
        mock_db.auth_user.async_insert = AsyncMock(return_value=1)
        mock_db.return_value.select = AsyncMock(
            side_effect=[make_mock_rowset([new_user_row]), make_mock_rowset([])]
        )

        await user_service.create_user({
            'email': 'new@example.com',
            'username': 'newuser',
            'password': 'plaintext123',
        })

        call_kwargs = mock_db.auth_user.async_insert.call_args.kwargs
        stored_password = call_kwargs['password']
        assert stored_password != 'plaintext123'
        assert bcrypt.checkpw('plaintext123'.encode(), stored_password.encode())

    async def test_duplicate_email_raises_value_error(self, user_service, mock_db):
        """Duplicate email raises ValueError."""
        mock_db.return_value.count = AsyncMock(return_value=1)

        with pytest.raises(ValueError, match='already exists'):
            await user_service.create_user({
                'email': 'existing@example.com',
                'username': 'newuser',
                'password': 'password123',
            })

    async def test_missing_email_raises_value_error(self, user_service, mock_db):
        """Missing email raises ValueError."""
        with pytest.raises(ValueError, match='required'):
            await user_service.create_user({
                'email': '',
                'username': 'user',
                'password': 'password123',
            })

    async def test_missing_password_raises_value_error(self, user_service, mock_db):
        """Missing password raises ValueError."""
        with pytest.raises(ValueError, match='required'):
            await user_service.create_user({
                'email': 'user@example.com',
                'username': 'user',
                'password': '',
            })

    async def test_role_ids_assigned(self, user_service, mock_db):
        """Role IDs are inserted into auth_user_role table."""
        new_user_row = _make_user_row()
        mock_db.return_value.count = AsyncMock(return_value=0)
        mock_db.auth_user.async_insert = AsyncMock(return_value=1)
        mock_db.auth_user_role.async_insert = AsyncMock(return_value=1)
        mock_db.return_value.select = AsyncMock(
            side_effect=[make_mock_rowset([new_user_row]), make_mock_rowset([])]
        )

        await user_service.create_user({
            'email': 'r@example.com',
            'username': 'ruser',
            'password': 'pass123',
            'role_ids': [1, 2],
        })

        assert mock_db.auth_user_role.async_insert.call_count == 2


class TestUpdateUser:
    """Test UserService.update_user()."""

    async def test_returns_none_when_not_found(self, user_service, mock_db):
        """Returns None if user doesn't exist."""
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        result = await user_service.update_user(9999, {'first_name': 'X'})

        assert result is None

    async def test_updates_first_name(self, user_service, mock_db):
        """First name is included in update call."""
        user_row = _make_user_row()
        mock_db.return_value.select = AsyncMock(
            side_effect=[
                make_mock_rowset([user_row]),   # existence check
                make_mock_rowset([user_row]),   # fetch updated
                make_mock_rowset([]),            # roles
            ]
        )
        mock_db.return_value.update = AsyncMock(return_value=None)

        result = await user_service.update_user(1, {'first_name': 'NewName'})

        mock_db.return_value.update.assert_called()
        call_kwargs = mock_db.return_value.update.call_args.kwargs
        assert 'first_name' in call_kwargs

    async def test_password_in_update_is_hashed(self, user_service, mock_db):
        """Password update stores bcrypt hash, not plaintext."""
        user_row = _make_user_row()
        mock_db.return_value.select = AsyncMock(
            side_effect=[
                make_mock_rowset([user_row]),
                make_mock_rowset([user_row]),
                make_mock_rowset([]),
            ]
        )
        mock_db.return_value.update = AsyncMock(return_value=None)

        await user_service.update_user(1, {'password': 'newpass123'})

        call_kwargs = mock_db.return_value.update.call_args.kwargs
        stored = call_kwargs.get('password', '')
        assert stored != 'newpass123'

    async def test_role_update_deletes_then_inserts(self, user_service, mock_db):
        """Role update deletes old roles then inserts new ones."""
        user_row = _make_user_row()
        mock_db.return_value.select = AsyncMock(
            side_effect=[
                make_mock_rowset([user_row]),
                make_mock_rowset([user_row]),
                make_mock_rowset([]),
            ]
        )
        mock_db.return_value.update = AsyncMock(return_value=None)
        mock_db.return_value.delete = AsyncMock(return_value=None)
        mock_db.auth_user_role.async_insert = AsyncMock(return_value=1)

        await user_service.update_user(1, {'role_ids': [3]})

        mock_db.return_value.delete.assert_called_once()
        mock_db.auth_user_role.async_insert.assert_called_once()


class TestDeleteUser:
    """Test UserService.delete_user()."""

    async def test_returns_true_when_deleted(self, user_service, mock_db):
        """Returns True when user is found and deleted."""
        user_row = _make_user_row()
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([user_row]))
        mock_db.return_value.delete = AsyncMock(return_value=None)

        result = await user_service.delete_user(1)

        assert result is True
        mock_db.return_value.delete.assert_called_once()

    async def test_returns_false_when_not_found(self, user_service, mock_db):
        """Returns False when user doesn't exist."""
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        result = await user_service.delete_user(999)

        assert result is False


class TestHashPasswordStatic:
    """Test UserService._hash_password static method."""

    def test_produces_bcrypt_hash(self):
        """_hash_password returns bcrypt-verifiable hash."""
        hashed = UserService._hash_password('test123')
        assert bcrypt.checkpw('test123'.encode(), hashed.encode())

    def test_not_plaintext(self):
        """_hash_password does not return plain text."""
        hashed = UserService._hash_password('my_password')
        assert hashed != 'my_password'
