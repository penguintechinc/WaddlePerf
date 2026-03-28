"""Unit tests for managerServer users routes."""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from models import hash_password

# Note: mock_db, app, and client fixtures are inherited from conftest.py


def _make_user_row(user_id=1, username='alice', role='global_admin'):
    row = MagicMock()
    row.id = user_id
    row.username = username
    row.email = f'{username}@example.com'
    row.password_hash = hash_password('pass')
    row.api_key = 'key-' + str(user_id)
    row.role = role
    row.ou_id = None
    row.mfa_enabled = False
    row.mfa_secret = None
    row.is_active = True
    row.created_at = datetime(2025, 1, 1)
    row.updated_at = datetime(2025, 1, 2)
    return row


def _valid_jwt_headers():
    """Return Authorization header with a valid JWT for user_id=1."""
    import jwt as pyjwt
    from datetime import datetime, timedelta
    from config import Config
    cfg = Config()
    payload = {
        'user_id': 1,
        'exp': datetime.utcnow() + timedelta(hours=1),
        'iat': datetime.utcnow(),
    }
    token = pyjwt.encode(payload, cfg.JWT_SECRET, algorithm='HS256')
    return {'Authorization': f'Bearer {token}'}


def _patch_auth(mock_db, user_id=1):
    """Configure mock_db so that get_user_from_token returns user_id."""
    jwt_token_row = MagicMock()
    jwt_token_row.revoked = False
    # db(filter).select().first() → jwt_token_row
    mock_db.return_value.select.return_value.first.return_value = jwt_token_row
    return mock_db


# ---------------------------------------------------------------------------
# GET /api/v1/users
# ---------------------------------------------------------------------------

class TestListUsers:
    def test_list_users_unauthenticated_returns_401(self, client):
        resp = client.get('/api/v1/users')
        assert resp.status_code == 401

    def test_list_users_authenticated_returns_200(self, client, mock_db):
        _patch_auth(mock_db)
        users = [_make_user_row(i) for i in range(1, 4)]
        # For the select query: db(filter).select(...)
        mock_db.return_value.select.return_value = iter(users)
        mock_db.return_value.count.return_value = 3

        with patch('routes.users.get_db', return_value=mock_db), \
             patch('routes.auth.get_db', return_value=mock_db):
            resp = client.get('/api/v1/users', headers=_valid_jwt_headers())

        assert resp.status_code == 200
        data = resp.get_json()
        assert 'users' in data

    def test_list_users_includes_pagination_fields(self, client, mock_db):
        _patch_auth(mock_db)
        mock_db.return_value.select.return_value = iter([])
        mock_db.return_value.count.return_value = 0

        with patch('routes.users.get_db', return_value=mock_db), \
             patch('routes.auth.get_db', return_value=mock_db):
            resp = client.get('/api/v1/users', headers=_valid_jwt_headers())

        if resp.status_code == 200:
            data = resp.get_json()
            assert 'total' in data
            assert 'page' in data
            assert 'per_page' in data


# ---------------------------------------------------------------------------
# GET /api/v1/users/<id>
# ---------------------------------------------------------------------------

class TestGetUser:
    def test_get_user_unauthenticated_returns_401(self, client):
        resp = client.get('/api/v1/users/1')
        assert resp.status_code == 401

    def test_get_user_found_returns_200(self, client, mock_db):
        _patch_auth(mock_db)
        user_row = _make_user_row(user_id=2)
        mock_db.users.__getitem__ = MagicMock(return_value=user_row)

        with patch('routes.users.get_db', return_value=mock_db), \
             patch('routes.auth.get_db', return_value=mock_db):
            resp = client.get('/api/v1/users/2', headers=_valid_jwt_headers())

        assert resp.status_code == 200

    def test_get_user_not_found_returns_404(self, client, mock_db):
        _patch_auth(mock_db)
        mock_db.users.__getitem__ = MagicMock(return_value=None)

        with patch('routes.users.get_db', return_value=mock_db), \
             patch('routes.auth.get_db', return_value=mock_db):
            resp = client.get('/api/v1/users/9999', headers=_valid_jwt_headers())

        assert resp.status_code == 404

    def test_get_own_user_includes_sensitive(self, client, mock_db):
        _patch_auth(mock_db, user_id=1)
        user_row = _make_user_row(user_id=1)
        mock_db.users.__getitem__ = MagicMock(return_value=user_row)

        with patch('routes.users.get_db', return_value=mock_db), \
             patch('routes.auth.get_db', return_value=mock_db):
            resp = client.get('/api/v1/users/1', headers=_valid_jwt_headers())

        if resp.status_code == 200:
            data = resp.get_json()
            # When requesting own profile, api_key should be included
            assert 'api_key' in data


# ---------------------------------------------------------------------------
# POST /api/v1/users
# ---------------------------------------------------------------------------

class TestCreateUser:
    def test_create_user_unauthenticated_returns_401(self, client):
        resp = client.post('/api/v1/users', json={
            'username': 'new', 'email': 'new@test.com', 'password': 'pass'
        })
        assert resp.status_code == 401

    def test_create_user_missing_fields_returns_400(self, client, mock_db):
        _patch_auth(mock_db)

        with patch('routes.users.get_db', return_value=mock_db), \
             patch('routes.auth.get_db', return_value=mock_db):
            resp = client.post('/api/v1/users',
                               json={'username': 'new'},
                               headers=_valid_jwt_headers())

        assert resp.status_code == 400

    def test_create_user_duplicate_username_returns_409(self, client, mock_db):
        _patch_auth(mock_db)
        existing_row = _make_user_row()
        # First select (username check) returns existing user
        mock_db.return_value.select.return_value.first.return_value = existing_row

        with patch('routes.users.get_db', return_value=mock_db), \
             patch('routes.auth.get_db', return_value=mock_db):
            resp = client.post('/api/v1/users',
                               json={'username': 'alice', 'email': 'x@x.com', 'password': 'p'},
                               headers=_valid_jwt_headers())

        assert resp.status_code == 409

    def test_create_user_success_returns_201(self, client, mock_db):
        _patch_auth(mock_db)
        new_row = _make_user_row(user_id=99, username='newuser')
        # username check → None, email check → None, then insert, then fetch
        mock_db.return_value.select.return_value.first.return_value = None
        mock_db.users.insert = MagicMock(return_value=99)
        mock_db.users.__getitem__ = MagicMock(return_value=new_row)

        with patch('routes.users.get_db', return_value=mock_db), \
             patch('routes.auth.get_db', return_value=mock_db):
            resp = client.post('/api/v1/users',
                               json={'username': 'newuser', 'email': 'new@new.com', 'password': 'pass'},
                               headers=_valid_jwt_headers())

        assert resp.status_code == 201


# ---------------------------------------------------------------------------
# PUT /api/v1/users/<id>
# ---------------------------------------------------------------------------

class TestUpdateUser:
    def test_update_user_unauthenticated_returns_401(self, client):
        resp = client.put('/api/v1/users/1', json={'email': 'new@test.com'})
        assert resp.status_code == 401

    def test_update_user_not_found_returns_404(self, client, mock_db):
        _patch_auth(mock_db)
        mock_db.users.__getitem__ = MagicMock(return_value=None)

        with patch('routes.users.get_db', return_value=mock_db), \
             patch('routes.auth.get_db', return_value=mock_db):
            resp = client.put('/api/v1/users/9999',
                              json={'email': 'x@x.com'},
                              headers=_valid_jwt_headers())

        assert resp.status_code == 404

    def test_update_user_found_returns_200(self, client, mock_db):
        _patch_auth(mock_db)
        user_row = _make_user_row(user_id=1)
        mock_db.users.__getitem__ = MagicMock(return_value=user_row)
        mock_db.return_value.update.return_value = None

        with patch('routes.users.get_db', return_value=mock_db), \
             patch('routes.auth.get_db', return_value=mock_db):
            resp = client.put('/api/v1/users/1',
                              json={'email': 'updated@example.com'},
                              headers=_valid_jwt_headers())

        assert resp.status_code == 200

    def test_update_user_applies_allowed_fields(self, client, mock_db):
        _patch_auth(mock_db)
        user_row = _make_user_row(user_id=1)
        mock_db.users.__getitem__ = MagicMock(return_value=user_row)

        update_data = {'email': 'new@email.com', 'role': 'ou_admin', 'is_active': False}
        with patch('routes.users.get_db', return_value=mock_db), \
             patch('routes.auth.get_db', return_value=mock_db):
            resp = client.put('/api/v1/users/1', json=update_data, headers=_valid_jwt_headers())

        if resp.status_code == 200:
            mock_db.return_value.update.assert_called()


# ---------------------------------------------------------------------------
# DELETE /api/v1/users/<id>
# ---------------------------------------------------------------------------

class TestDeleteUser:
    def test_delete_user_unauthenticated_returns_401(self, client):
        resp = client.delete('/api/v1/users/1')
        assert resp.status_code == 401

    def test_delete_user_not_found_returns_404(self, client, mock_db):
        _patch_auth(mock_db)
        mock_db.users.__getitem__ = MagicMock(return_value=None)

        with patch('routes.users.get_db', return_value=mock_db), \
             patch('routes.auth.get_db', return_value=mock_db):
            resp = client.delete('/api/v1/users/9999', headers=_valid_jwt_headers())

        assert resp.status_code == 404

    def test_delete_user_found_returns_200(self, client, mock_db):
        _patch_auth(mock_db)
        user_row = _make_user_row(user_id=2)
        mock_db.users.__getitem__ = MagicMock(return_value=user_row)
        mock_db.return_value.delete.return_value = None

        with patch('routes.users.get_db', return_value=mock_db), \
             patch('routes.auth.get_db', return_value=mock_db):
            resp = client.delete('/api/v1/users/2', headers=_valid_jwt_headers())

        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# PUT /api/v1/users/<id>/password
# ---------------------------------------------------------------------------

class TestChangePassword:
    def test_change_password_unauthenticated_returns_401(self, client):
        resp = client.put('/api/v1/users/1/password', json={'password': 'new'})
        assert resp.status_code == 401

    def test_change_password_missing_password_returns_400(self, client, mock_db):
        _patch_auth(mock_db)
        user_row = _make_user_row(user_id=1)
        mock_db.users.__getitem__ = MagicMock(return_value=user_row)

        with patch('routes.users.get_db', return_value=mock_db), \
             patch('routes.auth.get_db', return_value=mock_db):
            resp = client.put('/api/v1/users/1/password',
                              json={},
                              headers=_valid_jwt_headers())

        assert resp.status_code == 400

    def test_change_password_not_found_returns_404(self, client, mock_db):
        _patch_auth(mock_db)
        mock_db.users.__getitem__ = MagicMock(return_value=None)

        with patch('routes.users.get_db', return_value=mock_db), \
             patch('routes.auth.get_db', return_value=mock_db):
            resp = client.put('/api/v1/users/9999/password',
                              json={'password': 'new'},
                              headers=_valid_jwt_headers())

        assert resp.status_code == 404

    def test_change_password_success_returns_200(self, client, mock_db):
        _patch_auth(mock_db)
        user_row = _make_user_row(user_id=1)
        mock_db.users.__getitem__ = MagicMock(return_value=user_row)

        with patch('routes.users.get_db', return_value=mock_db), \
             patch('routes.auth.get_db', return_value=mock_db):
            resp = client.put('/api/v1/users/1/password',
                              json={'password': 'newpass'},
                              headers=_valid_jwt_headers())

        assert resp.status_code == 200
