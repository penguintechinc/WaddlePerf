"""Unit tests for managerServer devices routes.

The devices blueprint uses a session-cookie-based require_auth decorator
(not the JWT-based get_user_from_token). Tests set an X-Session-ID header
and mock the DB session lookup accordingly.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from models import hash_password

# Note: mock_db, app, and client fixtures are inherited from conftest.py


def _make_user_row(role='global_admin', ou_id=None):
    row = MagicMock()
    row.id = 1
    row.username = 'admin'
    row.email = 'admin@test.com'
    row.password_hash = hash_password('pass')
    row.api_key = 'key'
    row.role = role
    row.ou_id = ou_id
    row.mfa_enabled = False
    row.mfa_secret = None
    row.is_active = True
    row.created_at = None
    row.updated_at = None
    return row


def _make_session_row(user_id=1):
    session_row = MagicMock()
    session_row.user_id = user_id
    session_row.expires_at = datetime.utcnow() + timedelta(hours=1)
    return session_row


def _make_device_row(device_id=1, ou_id=2):
    row = MagicMock()
    row.id = device_id
    row.ou_id = ou_id
    row.enrollment_secret_id = 1
    row.device_serial = f'SN-{device_id:04d}'
    row.device_hostname = f'host-{device_id}'
    row.device_os = 'Linux'
    row.device_os_version = '5.15'
    row.client_type = 'container'
    row.client_version = '1.0'
    row.enrolled_ip = '10.0.0.1'
    row.enrolled_at = datetime(2025, 1, 1)
    row.last_seen = datetime(2025, 1, 2)
    row.is_active = True
    # Simulate _mapping for raw SQL result
    row._mapping = {
        'id': device_id, 'ou_id': ou_id,
        'device_serial': f'SN-{device_id:04d}',
        'device_hostname': f'host-{device_id}',
        'device_os': 'Linux', 'device_os_version': '5.15',
        'client_type': 'container', 'client_version': '1.0',
        'enrolled_ip': '10.0.0.1',
        'enrolled_at': datetime(2025, 1, 1),
        'last_seen': datetime(2025, 1, 2),
        'is_active': 1, 'ou_name': 'HQ',
        'minutes_since_last_seen': 2,
    }
    return row


def _configure_session_auth(mock_db, role='global_admin', ou_id=None):
    """Configure mock_db to satisfy the session-based require_auth decorator."""
    session_row = _make_session_row()
    user_row = _make_user_row(role=role, ou_id=ou_id)

    # db(filter).select().first() → session_row (for session lookup)
    mock_db.return_value.select.return_value.first.return_value = session_row
    # db.users[user_id] → user_row
    mock_db.users.__getitem__ = MagicMock(return_value=user_row)
    return session_row, user_row


SESSION_HEADER = {'X-Session-ID': 'test-session-id'}


# ---------------------------------------------------------------------------
# GET /api/v1/devices
# ---------------------------------------------------------------------------

class TestGetDevices:
    def test_get_devices_without_session_returns_401(self, client):
        resp = client.get('/api/v1/devices')
        assert resp.status_code == 401

    def test_get_devices_with_session_executes_query(self, client, mock_db):
        _configure_session_auth(mock_db)

        # Mock the engine.connect() context manager
        mock_conn = MagicMock()
        mock_db.engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_db.engine.connect.return_value.__exit__ = MagicMock(return_value=False)

        # count result
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0
        # data result
        mock_data_result = MagicMock()
        mock_data_result.__iter__ = MagicMock(return_value=iter([]))
        mock_conn.execute.side_effect = [mock_count_result, mock_data_result]

        with patch('routes.devices.get_db', return_value=mock_db):
            resp = client.get('/api/v1/devices', headers=SESSION_HEADER)

        assert resp.status_code == 200
        data = resp.get_json()
        assert 'devices' in data

    def test_get_devices_insufficient_role_returns_403(self, client, mock_db):
        _configure_session_auth(mock_db, role='viewer')

        with patch('routes.devices.get_db', return_value=mock_db):
            resp = client.get('/api/v1/devices', headers=SESSION_HEADER)

        assert resp.status_code == 403

    def test_get_devices_returns_pagination_fields(self, client, mock_db):
        _configure_session_auth(mock_db)
        mock_conn = MagicMock()
        mock_db.engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_db.engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0
        mock_data_result = MagicMock()
        mock_data_result.__iter__ = MagicMock(return_value=iter([]))
        mock_conn.execute.side_effect = [mock_count_result, mock_data_result]

        with patch('routes.devices.get_db', return_value=mock_db):
            resp = client.get('/api/v1/devices', headers=SESSION_HEADER)

        if resp.status_code == 200:
            data = resp.get_json()
            assert 'total' in data
            assert 'page' in data


# ---------------------------------------------------------------------------
# GET /api/v1/devices/<id>
# ---------------------------------------------------------------------------

class TestGetDevice:
    def test_get_device_without_session_returns_401(self, client):
        resp = client.get('/api/v1/devices/1')
        assert resp.status_code == 401

    def test_get_device_not_found_returns_404(self, client, mock_db):
        _configure_session_auth(mock_db)
        # device_enrollments select → None
        mock_db.return_value.select.return_value.first.side_effect = [
            _make_session_row(),  # session check
            None,                 # device not found
        ]

        with patch('routes.devices.get_db', return_value=mock_db):
            resp = client.get('/api/v1/devices/9999', headers=SESSION_HEADER)

        assert resp.status_code == 404

    def test_get_device_found_returns_200(self, client, mock_db):
        _configure_session_auth(mock_db)
        device_row = _make_device_row(device_id=1, ou_id=2)
        mock_db.return_value.select.return_value.first.side_effect = [
            _make_session_row(),  # session
            device_row,           # device
        ]
        # Create mock org unit with name attribute
        ou_mock = MagicMock()
        ou_mock.name = 'HQ'
        mock_db.organization_units.__getitem__ = MagicMock(return_value=ou_mock)
        # Create mock secret with name attribute
        secret_mock = MagicMock()
        secret_mock.name = 'secret'
        mock_db.ou_enrollment_secrets.__getitem__ = MagicMock(return_value=secret_mock)

        with patch('routes.devices.get_db', return_value=mock_db):
            resp = client.get('/api/v1/devices/1', headers=SESSION_HEADER)

        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# POST /api/v1/devices/<id>/deactivate
# ---------------------------------------------------------------------------

class TestDeactivateDevice:
    def test_deactivate_without_session_returns_401(self, client):
        resp = client.post('/api/v1/devices/1/deactivate')
        assert resp.status_code == 401

    def test_deactivate_viewer_role_returns_403(self, client, mock_db):
        _configure_session_auth(mock_db, role='viewer')

        with patch('routes.devices.get_db', return_value=mock_db):
            resp = client.post('/api/v1/devices/1/deactivate', headers=SESSION_HEADER)

        assert resp.status_code == 403

    def test_deactivate_device_not_found_returns_404(self, client, mock_db):
        _configure_session_auth(mock_db, role='global_admin')
        device_select = MagicMock()
        device_select.select.return_value.first.return_value = None
        mock_db.return_value = device_select

        # Need the session row too
        session_row = _make_session_row()
        user_row = _make_user_row(role='global_admin')
        call_count = [0]

        def select_side_effect(*args, **kwargs):
            result = MagicMock()
            if call_count[0] == 0:
                result.first.return_value = session_row
            else:
                result.first.return_value = None
            call_count[0] += 1
            return result

        mock_db.return_value.select = select_side_effect
        mock_db.users.__getitem__ = MagicMock(return_value=user_row)

        with patch('routes.devices.get_db', return_value=mock_db):
            resp = client.post('/api/v1/devices/9999/deactivate', headers=SESSION_HEADER)

        assert resp.status_code == 404

    def test_deactivate_device_success(self, client, mock_db):
        _configure_session_auth(mock_db, role='global_admin')
        device_row = _make_device_row(device_id=1)

        call_count = [0]
        session_row = _make_session_row()
        user_row = _make_user_row(role='global_admin')
        mock_db.users.__getitem__ = MagicMock(return_value=user_row)

        def select_side_effect(*args, **kwargs):
            result = MagicMock()
            if call_count[0] == 0:
                result.first.return_value = session_row
            else:
                result.first.return_value = device_row
            call_count[0] += 1
            return result

        mock_db.return_value.select = select_side_effect
        mock_db.return_value.update = MagicMock()

        with patch('routes.devices.get_db', return_value=mock_db):
            resp = client.post('/api/v1/devices/1/deactivate', headers=SESSION_HEADER)

        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# GET /api/v1/devices/stats
# ---------------------------------------------------------------------------

class TestDeviceStats:
    def test_device_stats_without_session_returns_401(self, client):
        resp = client.get('/api/v1/devices/stats')
        assert resp.status_code == 401

    def test_device_stats_with_valid_session_returns_200(self, client, mock_db):
        _configure_session_auth(mock_db)

        mock_conn = MagicMock()
        mock_db.engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_db.engine.connect.return_value.__exit__ = MagicMock(return_value=False)

        stats_row = MagicMock()
        stats_row._mapping = {
            'total': 10, 'active': 8, 'inactive': 2,
            'online': 3, 'recent': 2, 'offline': 2, 'stale': 1,
        }
        mock_result = MagicMock()
        mock_result.first.return_value = stats_row
        mock_conn.execute.return_value = mock_result

        with patch('routes.devices.get_db', return_value=mock_db):
            resp = client.get('/api/v1/devices/stats', headers=SESSION_HEADER)

        assert resp.status_code == 200

    def test_device_stats_insufficient_role_returns_403(self, client, mock_db):
        _configure_session_auth(mock_db, role='viewer')

        with patch('routes.devices.get_db', return_value=mock_db):
            resp = client.get('/api/v1/devices/stats', headers=SESSION_HEADER)

        assert resp.status_code == 403

    def test_device_stats_ou_admin_scoped_to_ou(self, client, mock_db):
        _configure_session_auth(mock_db, role='ou_admin', ou_id=3)

        mock_conn = MagicMock()
        mock_db.engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_db.engine.connect.return_value.__exit__ = MagicMock(return_value=False)

        stats_row = MagicMock()
        stats_row._mapping = {
            'total': 5, 'active': 4, 'inactive': 1,
            'online': 1, 'recent': 1, 'offline': 1, 'stale': 1,
        }
        mock_result = MagicMock()
        mock_result.first.return_value = stats_row
        mock_conn.execute.return_value = mock_result

        with patch('routes.devices.get_db', return_value=mock_db):
            resp = client.get('/api/v1/devices/stats', headers=SESSION_HEADER)

        assert resp.status_code == 200

    def test_device_stats_no_rows_returns_zeros(self, client, mock_db):
        _configure_session_auth(mock_db)

        mock_conn = MagicMock()
        mock_db.engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_db.engine.connect.return_value.__exit__ = MagicMock(return_value=False)

        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_conn.execute.return_value = mock_result

        with patch('routes.devices.get_db', return_value=mock_db):
            resp = client.get('/api/v1/devices/stats', headers=SESSION_HEADER)

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['total'] == 0


# ---------------------------------------------------------------------------
# POST /api/v1/devices/<id>/reactivate
# ---------------------------------------------------------------------------

class TestReactivateDevice:
    def test_reactivate_without_session_returns_401(self, client):
        resp = client.post('/api/v1/devices/1/reactivate')
        assert resp.status_code == 401

    def test_reactivate_viewer_role_returns_403(self, client, mock_db):
        _configure_session_auth(mock_db, role='viewer')

        with patch('routes.devices.get_db', return_value=mock_db):
            resp = client.post('/api/v1/devices/1/reactivate', headers=SESSION_HEADER)

        assert resp.status_code == 403

    def test_reactivate_device_not_found_returns_404(self, client, mock_db):
        session_row = _make_session_row()
        user_row = _make_user_row(role='global_admin')
        call_count = [0]

        def select_side_effect(*args, **kwargs):
            result = MagicMock()
            if call_count[0] == 0:
                result.first.return_value = session_row
            else:
                result.first.return_value = None
            call_count[0] += 1
            return result

        mock_db.return_value.select = select_side_effect
        mock_db.users.__getitem__ = MagicMock(return_value=user_row)

        with patch('routes.devices.get_db', return_value=mock_db):
            resp = client.post('/api/v1/devices/9999/reactivate', headers=SESSION_HEADER)

        assert resp.status_code == 404

    def test_reactivate_device_success_returns_200(self, client, mock_db):
        device_row = _make_device_row(device_id=1)

        call_count = [0]
        session_row = _make_session_row()
        user_row = _make_user_row(role='global_admin')
        mock_db.users.__getitem__ = MagicMock(return_value=user_row)

        def select_side_effect(*args, **kwargs):
            result = MagicMock()
            if call_count[0] == 0:
                result.first.return_value = session_row
            else:
                result.first.return_value = device_row
            call_count[0] += 1
            return result

        mock_db.return_value.select = select_side_effect
        mock_db.return_value.update = MagicMock()

        with patch('routes.devices.get_db', return_value=mock_db):
            resp = client.post('/api/v1/devices/1/reactivate', headers=SESSION_HEADER)

        assert resp.status_code == 200

    def test_reactivate_ou_admin_wrong_ou_returns_403(self, client, mock_db):
        device_row = _make_device_row(device_id=1, ou_id=10)

        call_count = [0]
        session_row = _make_session_row()
        user_row = _make_user_row(role='ou_admin', ou_id=5)
        mock_db.users.__getitem__ = MagicMock(return_value=user_row)

        def select_side_effect(*args, **kwargs):
            result = MagicMock()
            if call_count[0] == 0:
                result.first.return_value = session_row
            else:
                result.first.return_value = device_row
            call_count[0] += 1
            return result

        mock_db.return_value.select = select_side_effect

        with patch('routes.devices.get_db', return_value=mock_db):
            resp = client.post('/api/v1/devices/1/reactivate', headers=SESSION_HEADER)

        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# GET /api/v1/devices  -- additional role / filter coverage
# ---------------------------------------------------------------------------

class TestGetDevicesExtended:
    def test_get_devices_ou_admin_role_returns_200(self, client, mock_db):
        _configure_session_auth(mock_db, role='ou_admin', ou_id=3)

        mock_conn = MagicMock()
        mock_db.engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_db.engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0
        mock_data_result = MagicMock()
        mock_data_result.__iter__ = MagicMock(return_value=iter([]))
        mock_conn.execute.side_effect = [mock_count_result, mock_data_result]

        with patch('routes.devices.get_db', return_value=mock_db):
            resp = client.get('/api/v1/devices', headers=SESSION_HEADER)

        assert resp.status_code == 200

    def test_get_devices_with_search_filter(self, client, mock_db):
        _configure_session_auth(mock_db)

        mock_conn = MagicMock()
        mock_db.engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_db.engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0
        mock_data_result = MagicMock()
        mock_data_result.__iter__ = MagicMock(return_value=iter([]))
        mock_conn.execute.side_effect = [mock_count_result, mock_data_result]

        with patch('routes.devices.get_db', return_value=mock_db):
            resp = client.get('/api/v1/devices?search=host-1', headers=SESSION_HEADER)

        assert resp.status_code == 200

    def test_get_devices_with_status_online_filter(self, client, mock_db):
        _configure_session_auth(mock_db)

        mock_conn = MagicMock()
        mock_db.engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_db.engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0
        mock_data_result = MagicMock()
        mock_data_result.__iter__ = MagicMock(return_value=iter([]))
        mock_conn.execute.side_effect = [mock_count_result, mock_data_result]

        with patch('routes.devices.get_db', return_value=mock_db):
            resp = client.get('/api/v1/devices?status=online', headers=SESSION_HEADER)

        assert resp.status_code == 200

    def test_get_devices_with_status_offline_filter(self, client, mock_db):
        _configure_session_auth(mock_db)

        mock_conn = MagicMock()
        mock_db.engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_db.engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0
        mock_data_result = MagicMock()
        mock_data_result.__iter__ = MagicMock(return_value=iter([]))
        mock_conn.execute.side_effect = [mock_count_result, mock_data_result]

        with patch('routes.devices.get_db', return_value=mock_db):
            resp = client.get('/api/v1/devices?status=offline', headers=SESSION_HEADER)

        assert resp.status_code == 200

    def test_get_devices_with_rows_returns_device_list(self, client, mock_db):
        _configure_session_auth(mock_db)

        mock_conn = MagicMock()
        mock_db.engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_db.engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        device_row = _make_device_row(device_id=1, ou_id=2)
        mock_data_result = MagicMock()
        mock_data_result.__iter__ = MagicMock(return_value=iter([device_row]))
        mock_conn.execute.side_effect = [mock_count_result, mock_data_result]

        with patch('routes.devices.get_db', return_value=mock_db):
            resp = client.get('/api/v1/devices', headers=SESSION_HEADER)

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['total'] == 1
        assert len(data['devices']) == 1

    def test_get_devices_row_with_no_last_seen_has_status_never(self, client, mock_db):
        _configure_session_auth(mock_db)

        mock_conn = MagicMock()
        mock_db.engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_db.engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1

        device_row = MagicMock()
        device_row._mapping = {
            'id': 1, 'ou_id': 2,
            'device_serial': 'SN-0001',
            'device_hostname': 'host-1',
            'device_os': 'Linux', 'device_os_version': '5.15',
            'client_type': 'container', 'client_version': '1.0',
            'enrolled_ip': '10.0.0.1',
            'enrolled_at': None,
            'last_seen': None,   # no last_seen → status 'never'
            'is_active': 1, 'ou_name': 'HQ',
            'minutes_since_last_seen': None,
        }

        mock_data_result = MagicMock()
        mock_data_result.__iter__ = MagicMock(return_value=iter([device_row]))
        mock_conn.execute.side_effect = [mock_count_result, mock_data_result]

        with patch('routes.devices.get_db', return_value=mock_db):
            resp = client.get('/api/v1/devices', headers=SESSION_HEADER)

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['devices'][0]['status'] == 'never'

    def test_get_devices_with_ou_id_filter_global_admin(self, client, mock_db):
        _configure_session_auth(mock_db, role='global_admin')

        mock_conn = MagicMock()
        mock_db.engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_db.engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0
        mock_data_result = MagicMock()
        mock_data_result.__iter__ = MagicMock(return_value=iter([]))
        mock_conn.execute.side_effect = [mock_count_result, mock_data_result]

        with patch('routes.devices.get_db', return_value=mock_db):
            resp = client.get('/api/v1/devices?ou_id=5', headers=SESSION_HEADER)

        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# GET /api/v1/devices/<id>  -- OU role permission checks
# ---------------------------------------------------------------------------

class TestGetDeviceExtended:
    def test_get_device_ou_admin_same_ou_returns_200(self, client, mock_db):
        _configure_session_auth(mock_db, role='ou_admin', ou_id=2)
        device_row = _make_device_row(device_id=1, ou_id=2)
        mock_db.return_value.select.return_value.first.side_effect = [
            _make_session_row(),
            device_row,
        ]
        ou_mock = MagicMock()
        ou_mock.name = 'HQ'
        mock_db.organization_units.__getitem__ = MagicMock(return_value=ou_mock)
        secret_mock = MagicMock()
        secret_mock.name = 'secret'
        mock_db.ou_enrollment_secrets.__getitem__ = MagicMock(return_value=secret_mock)

        with patch('routes.devices.get_db', return_value=mock_db):
            resp = client.get('/api/v1/devices/1', headers=SESSION_HEADER)

        assert resp.status_code == 200

    def test_get_device_ou_admin_wrong_ou_returns_403(self, client, mock_db):
        _configure_session_auth(mock_db, role='ou_admin', ou_id=5)
        device_row = _make_device_row(device_id=1, ou_id=2)
        # ou_id on device (2) != user ou_id (5)
        device_row.ou_id = 2
        mock_db.return_value.select.return_value.first.side_effect = [
            _make_session_row(),
            device_row,
        ]

        with patch('routes.devices.get_db', return_value=mock_db):
            resp = client.get('/api/v1/devices/1', headers=SESSION_HEADER)

        assert resp.status_code == 403

    def test_get_device_unknown_role_returns_403(self, client, mock_db):
        _configure_session_auth(mock_db, role='viewer')
        device_row = _make_device_row(device_id=1, ou_id=2)
        mock_db.return_value.select.return_value.first.side_effect = [
            _make_session_row(),
            device_row,
        ]

        with patch('routes.devices.get_db', return_value=mock_db):
            resp = client.get('/api/v1/devices/1', headers=SESSION_HEADER)

        assert resp.status_code == 403
