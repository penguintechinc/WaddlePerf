"""Unit tests for managerServer config routes.

The config blueprint uses JWT-based get_user_from_token() for auth.
Admin check: require_admin() looks up db.users[user_id] and checks role == 'global_admin'.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

# Note: mock_db, app, and client fixtures are inherited from conftest.py


class MockField:
    """Mock database field that supports comparison operations."""
    def __init__(self, name="field"):
        self.name = name

    def __eq__(self, other):
        return MagicMock()

    def __ne__(self, other):
        return MagicMock()

    def __gt__(self, other):
        return MagicMock()

    def __lt__(self, other):
        return MagicMock()

    def __and__(self, other):
        return MagicMock()

    def __or__(self, other):
        return MagicMock()


def _setup_config_fields(mock_db):
    """Add MockField instances for system_config table fields."""
    mock_db.system_config.id = MockField('system_config.id')
    mock_db.system_config.config_key = MockField('system_config.config_key')


def _make_user_row(role='global_admin', user_id=1):
    row = MagicMock()
    row.id = user_id
    row.username = 'admin'
    row.email = 'admin@test.com'
    row.role = role
    row.ou_id = None
    row.is_active = True
    row.password_hash = 'hashed'
    row.api_key = 'key'
    row.mfa_enabled = False
    row.mfa_secret = None
    row.created_at = None
    row.updated_at = None
    return row


def _make_config_row(key='max_devices', value='100', config_type='integer',
                     description='Max devices', updated_at=None):
    row = MagicMock()
    row.id = 1
    row.config_key = key
    row.config_value = value
    row.config_type = config_type
    row.description = description
    row.updated_by = None
    row.created_at = None
    row.updated_at = updated_at
    return row


def _setup_admin_auth(mock_db, role='global_admin', user_id=1):
    """Configure mock_db for JWT admin auth: db.users[user_id] -> user_row."""
    user_row = _make_user_row(role=role, user_id=user_id)
    mock_db.users.__getitem__ = MagicMock(return_value=user_row)
    return user_row


# ---------------------------------------------------------------------------
# GET /api/v1/config  (admin only)
# ---------------------------------------------------------------------------

class TestGetAllConfig:
    def test_get_all_config_no_token_returns_401(self, client):
        with patch('routes.config.get_user_from_token', return_value=None):
            resp = client.get('/api/v1/config')
        assert resp.status_code == 401

    def test_get_all_config_non_admin_returns_403(self, client, mock_db):
        _setup_admin_auth(mock_db, role='viewer')
        _setup_config_fields(mock_db)
        with patch('routes.config.get_user_from_token', return_value=1):
            with patch('routes.config.get_db', return_value=mock_db):
                resp = client.get('/api/v1/config')
        assert resp.status_code == 403

    def test_get_all_config_admin_returns_200(self, client, mock_db):
        _setup_admin_auth(mock_db, role='global_admin')
        _setup_config_fields(mock_db)

        # Simulate iteration over config rows
        config_row = _make_config_row(config_type='string')
        mock_db.return_value.select._dual_select._iter_value = [config_row]

        with patch('routes.config.get_user_from_token', return_value=1):
            with patch('routes.config.get_db', return_value=mock_db):
                resp = client.get('/api/v1/config')

        assert resp.status_code == 200
        data = resp.get_json()
        assert 'config' in data

    def test_get_all_config_empty_returns_200(self, client, mock_db):
        _setup_admin_auth(mock_db, role='global_admin')
        _setup_config_fields(mock_db)
        mock_db.return_value.select._dual_select._iter_value = []

        with patch('routes.config.get_user_from_token', return_value=1):
            with patch('routes.config.get_db', return_value=mock_db):
                resp = client.get('/api/v1/config')

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['config'] == {}

    def test_get_all_config_json_type_parsed(self, client, mock_db):
        _setup_admin_auth(mock_db, role='global_admin')
        _setup_config_fields(mock_db)
        config_row = _make_config_row(key='my_json', value='{"a": 1}', config_type='json')
        mock_db.return_value.select._dual_select._iter_value = [config_row]

        with patch('routes.config.get_user_from_token', return_value=1):
            with patch('routes.config.get_db', return_value=mock_db):
                resp = client.get('/api/v1/config')

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['config']['my_json']['value'] == {'a': 1}

    def test_get_all_config_boolean_type_parsed(self, client, mock_db):
        _setup_admin_auth(mock_db, role='global_admin')
        _setup_config_fields(mock_db)
        config_row = _make_config_row(key='flag', value='true', config_type='boolean')
        mock_db.return_value.select._dual_select._iter_value = [config_row]

        with patch('routes.config.get_user_from_token', return_value=1):
            with patch('routes.config.get_db', return_value=mock_db):
                resp = client.get('/api/v1/config')

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['config']['flag']['value'] is True

    def test_get_all_config_integer_type_parsed(self, client, mock_db):
        _setup_admin_auth(mock_db, role='global_admin')
        _setup_config_fields(mock_db)
        config_row = _make_config_row(key='count', value='42', config_type='integer')
        mock_db.return_value.select._dual_select._iter_value = [config_row]

        with patch('routes.config.get_user_from_token', return_value=1):
            with patch('routes.config.get_db', return_value=mock_db):
                resp = client.get('/api/v1/config')

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['config']['count']['value'] == 42

    def test_get_all_config_updated_at_included(self, client, mock_db):
        _setup_admin_auth(mock_db, role='global_admin')
        _setup_config_fields(mock_db)
        updated_at = datetime(2025, 1, 15, 12, 0, 0)
        config_row = _make_config_row(updated_at=updated_at)
        mock_db.return_value.select._dual_select._iter_value = [config_row]

        with patch('routes.config.get_user_from_token', return_value=1):
            with patch('routes.config.get_db', return_value=mock_db):
                resp = client.get('/api/v1/config')

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['config']['max_devices']['updated_at'] is not None


# ---------------------------------------------------------------------------
# GET /api/v1/config/<key>
# ---------------------------------------------------------------------------

class TestGetConfigKey:
    def test_get_config_no_token_returns_401(self, client):
        with patch('routes.config.get_user_from_token', return_value=None):
            resp = client.get('/api/v1/config/max_devices')
        assert resp.status_code == 401

    def test_get_config_key_not_found_returns_404(self, client, mock_db):
        mock_db.return_value.select.return_value.first.return_value = None

        with patch('routes.config.get_user_from_token', return_value=1):
            with patch('routes.config.get_db', return_value=mock_db):
                resp = client.get('/api/v1/config/nonexistent')

        assert resp.status_code == 404

    def test_get_config_key_found_returns_200(self, client, mock_db):
        config_row = _make_config_row(key='max_devices', value='100', config_type='integer')
        mock_db.return_value.select.return_value.first.return_value = config_row

        with patch('routes.config.get_user_from_token', return_value=1):
            with patch('routes.config.get_db', return_value=mock_db):
                resp = client.get('/api/v1/config/max_devices')

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['config_key'] == 'max_devices'
        assert data['value'] == 100

    def test_get_config_key_json_type(self, client, mock_db):
        config_row = _make_config_row(key='settings', value='{"x": 5}', config_type='json')
        mock_db.return_value.select.return_value.first.return_value = config_row

        with patch('routes.config.get_user_from_token', return_value=1):
            with patch('routes.config.get_db', return_value=mock_db):
                resp = client.get('/api/v1/config/settings')

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['value'] == {'x': 5}

    def test_get_config_key_boolean_false(self, client, mock_db):
        config_row = _make_config_row(key='enable_x', value='false', config_type='boolean')
        mock_db.return_value.select.return_value.first.return_value = config_row

        with patch('routes.config.get_user_from_token', return_value=1):
            with patch('routes.config.get_db', return_value=mock_db):
                resp = client.get('/api/v1/config/enable_x')

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['value'] is False

    def test_get_config_key_string_type(self, client, mock_db):
        config_row = _make_config_row(key='site_name', value='WaddlePerf', config_type='string')
        mock_db.return_value.select.return_value.first.return_value = config_row

        with patch('routes.config.get_user_from_token', return_value=1):
            with patch('routes.config.get_db', return_value=mock_db):
                resp = client.get('/api/v1/config/site_name')

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['value'] == 'WaddlePerf'


# ---------------------------------------------------------------------------
# PATCH /api/v1/config  (bulk update, admin only)
# ---------------------------------------------------------------------------

class TestUpdateConfig:
    def test_patch_config_no_token_returns_401(self, client):
        with patch('routes.config.get_user_from_token', return_value=None):
            resp = client.patch('/api/v1/config', json={'max_devices': 50})
        assert resp.status_code == 401

    def test_patch_config_non_admin_returns_403(self, client, mock_db):
        _setup_admin_auth(mock_db, role='viewer')

        with patch('routes.config.get_user_from_token', return_value=1):
            with patch('routes.config.get_db', return_value=mock_db):
                resp = client.patch('/api/v1/config', json={'max_devices': 50})

        assert resp.status_code == 403

    def test_patch_config_no_data_returns_400(self, client, mock_db):
        _setup_admin_auth(mock_db, role='global_admin')

        with patch('routes.config.get_user_from_token', return_value=1):
            with patch('routes.config.get_db', return_value=mock_db):
                resp = client.patch('/api/v1/config', data='', content_type='application/json')

        assert resp.status_code == 400

    def test_patch_config_key_not_found_adds_error(self, client, mock_db):
        _setup_admin_auth(mock_db, role='global_admin')
        # first() returns None for the missing key
        mock_db.return_value.select.return_value.first.return_value = None

        with patch('routes.config.get_user_from_token', return_value=1):
            with patch('routes.config.get_db', return_value=mock_db):
                resp = client.patch('/api/v1/config', json={'missing_key': 'val'})

        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data['errors']) > 0
        assert data['updated'] == []

    def test_patch_config_success_integer(self, client, mock_db):
        _setup_admin_auth(mock_db, role='global_admin')
        config_row = _make_config_row(key='max_devices', value='100', config_type='integer')
        mock_db.return_value.select.return_value.first.return_value = config_row

        with patch('routes.config.get_user_from_token', return_value=1):
            with patch('routes.config.get_db', return_value=mock_db):
                resp = client.patch('/api/v1/config', json={'max_devices': 50})

        assert resp.status_code == 200
        data = resp.get_json()
        assert 'max_devices' in data['updated']

    def test_patch_config_success_json(self, client, mock_db):
        _setup_admin_auth(mock_db, role='global_admin')
        config_row = _make_config_row(key='schedule', value='{}', config_type='json')
        mock_db.return_value.select.return_value.first.return_value = config_row

        with patch('routes.config.get_user_from_token', return_value=1):
            with patch('routes.config.get_db', return_value=mock_db):
                resp = client.patch('/api/v1/config', json={'schedule': {'interval': 60}})

        assert resp.status_code == 200
        data = resp.get_json()
        assert 'schedule' in data['updated']

    def test_patch_config_success_boolean(self, client, mock_db):
        _setup_admin_auth(mock_db, role='global_admin')
        config_row = _make_config_row(key='enable_x', value='false', config_type='boolean')
        mock_db.return_value.select.return_value.first.return_value = config_row

        with patch('routes.config.get_user_from_token', return_value=1):
            with patch('routes.config.get_db', return_value=mock_db):
                resp = client.patch('/api/v1/config', json={'enable_x': True})

        assert resp.status_code == 200
        data = resp.get_json()
        assert 'enable_x' in data['updated']


# ---------------------------------------------------------------------------
# PUT /api/v1/config/<key>  (set single key, admin only)
# ---------------------------------------------------------------------------

class TestSetConfig:
    def test_put_config_no_token_returns_401(self, client):
        with patch('routes.config.get_user_from_token', return_value=None):
            resp = client.put('/api/v1/config/max_devices', json={'value': 99})
        assert resp.status_code == 401

    def test_put_config_non_admin_returns_403(self, client, mock_db):
        _setup_admin_auth(mock_db, role='viewer')

        with patch('routes.config.get_user_from_token', return_value=1):
            with patch('routes.config.get_db', return_value=mock_db):
                resp = client.put('/api/v1/config/max_devices', json={'value': 99})

        assert resp.status_code == 403

    def test_put_config_missing_value_returns_400(self, client, mock_db):
        _setup_admin_auth(mock_db, role='global_admin')

        with patch('routes.config.get_user_from_token', return_value=1):
            with patch('routes.config.get_db', return_value=mock_db):
                resp = client.put('/api/v1/config/max_devices', json={})

        assert resp.status_code == 400

    def test_put_config_key_not_found_returns_404(self, client, mock_db):
        _setup_admin_auth(mock_db, role='global_admin')
        mock_db.return_value.select.return_value.first.return_value = None

        with patch('routes.config.get_user_from_token', return_value=1):
            with patch('routes.config.get_db', return_value=mock_db):
                resp = client.put('/api/v1/config/nonexistent', json={'value': 'x'})

        assert resp.status_code == 404

    def test_put_config_success_integer(self, client, mock_db):
        _setup_admin_auth(mock_db, role='global_admin')
        config_row = _make_config_row(key='max_devices', value='100', config_type='integer')
        mock_db.return_value.select.return_value.first.return_value = config_row

        with patch('routes.config.get_user_from_token', return_value=1):
            with patch('routes.config.get_db', return_value=mock_db):
                resp = client.put('/api/v1/config/max_devices', json={'value': 200})

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['updated'] is True
        assert data['config_key'] == 'max_devices'

    def test_put_config_success_json(self, client, mock_db):
        _setup_admin_auth(mock_db, role='global_admin')
        config_row = _make_config_row(key='sched', value='{}', config_type='json')
        mock_db.return_value.select.return_value.first.return_value = config_row

        with patch('routes.config.get_user_from_token', return_value=1):
            with patch('routes.config.get_db', return_value=mock_db):
                resp = client.put('/api/v1/config/sched', json={'value': {'sec': 30}})

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['updated'] is True

    def test_put_config_success_boolean_false(self, client, mock_db):
        _setup_admin_auth(mock_db, role='global_admin')
        config_row = _make_config_row(key='flag', value='true', config_type='boolean')
        mock_db.return_value.select.return_value.first.return_value = config_row

        with patch('routes.config.get_user_from_token', return_value=1):
            with patch('routes.config.get_db', return_value=mock_db):
                resp = client.put('/api/v1/config/flag', json={'value': False})

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['updated'] is True

    def test_put_config_success_string(self, client, mock_db):
        _setup_admin_auth(mock_db, role='global_admin')
        config_row = _make_config_row(key='site_name', value='Old', config_type='string')
        mock_db.return_value.select.return_value.first.return_value = config_row

        with patch('routes.config.get_user_from_token', return_value=1):
            with patch('routes.config.get_db', return_value=mock_db):
                resp = client.put('/api/v1/config/site_name', json={'value': 'New'})

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['updated'] is True
