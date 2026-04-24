"""Unit tests for managerServer enrollment routes.

The enrollment blueprint uses JWT-based get_user_from_token() for most endpoints.
Admin check via require_admin() checks role in ['global_admin', 'ou_admin'].
The /enroll endpoint is PUBLIC (no auth).
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

# Note: mock_db, app, and client fixtures are inherited from conftest.py

BASE = '/api/v1/enrollment'


def _make_user_row(role='global_admin', user_id=1, ou_id=None):
    row = MagicMock()
    row.id = user_id
    row.username = 'admin'
    row.email = 'admin@test.com'
    row.role = role
    row.ou_id = ou_id
    row.is_active = True
    row.password_hash = 'hashed'
    row.api_key = 'key'
    row.mfa_enabled = False
    row.mfa_secret = None
    row.created_at = None
    row.updated_at = None
    return row


def _make_secret_row(secret_id=1, ou_id=1):
    row = MagicMock()
    row.id = secret_id
    row.ou_id = ou_id
    row.secret = 'SECRETVAL12345'
    row.name = 'Test Secret'
    row.is_active = True
    row.created_by = 1
    row.created_at = None
    return row


def _make_ou_row(ou_id=1):
    row = MagicMock()
    row.id = ou_id
    row.name = 'HQ'
    row.description = 'Headquarters'
    row.created_at = None
    row.updated_at = None
    return row


def _make_device_row(device_id=1, ou_id=1):
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
    row.enrolled_at = None
    row.last_seen = None
    row.is_active = True
    return row


def _make_client_config_row(config_id=1, ou_id=None, is_default=False):
    row = MagicMock()
    row.id = config_id
    row.user_id = 1
    row.ou_id = ou_id
    row.config_name = 'Test Config'
    row.config_data = {}
    row.is_default = is_default
    row.created_at = None
    row.updated_at = None
    return row


def _setup_admin_auth(mock_db, role='global_admin', user_id=1, ou_id=None):
    """Setup db.users[user_id] for require_admin and list_devices user lookups."""
    user_row = _make_user_row(role=role, user_id=user_id, ou_id=ou_id)
    mock_db.users.__getitem__ = MagicMock(return_value=user_row)
    return user_row


# ---------------------------------------------------------------------------
# GET /api/v1/enrollment/secrets
# ---------------------------------------------------------------------------

class TestListSecrets:
    def test_list_secrets_no_token_returns_401(self, client):
        with patch('routes.enrollment.get_user_from_token', return_value=None):
            resp = client.get(f'{BASE}/secrets')
        assert resp.status_code == 401

    def test_list_secrets_viewer_role_returns_403(self, client, mock_db):
        _setup_admin_auth(mock_db, role='viewer')
        mock_db.return_value.select._dual_select._iter_value = []

        with patch('routes.enrollment.get_user_from_token', return_value=1):
            with patch('routes.enrollment.get_db', return_value=mock_db):
                resp = client.get(f'{BASE}/secrets')

        assert resp.status_code == 403

    def test_list_secrets_global_admin_returns_all(self, client, mock_db):
        _setup_admin_auth(mock_db, role='global_admin')
        secret_row = _make_secret_row()
        mock_db.return_value.select._dual_select._iter_value = [secret_row]

        with patch('routes.enrollment.get_user_from_token', return_value=1):
            with patch('routes.enrollment.get_db', return_value=mock_db):
                resp = client.get(f'{BASE}/secrets')

        assert resp.status_code == 200
        data = resp.get_json()
        assert 'secrets' in data

    def test_list_secrets_ou_admin_returns_ou_secrets(self, client, mock_db):
        _setup_admin_auth(mock_db, role='ou_admin', ou_id=1)
        secret_row = _make_secret_row(ou_id=1)
        mock_db.return_value.select._dual_select._iter_value = [secret_row]

        with patch('routes.enrollment.get_user_from_token', return_value=1):
            with patch('routes.enrollment.get_db', return_value=mock_db):
                resp = client.get(f'{BASE}/secrets')

        assert resp.status_code == 200
        data = resp.get_json()
        assert 'secrets' in data


# ---------------------------------------------------------------------------
# GET /api/v1/enrollment/secrets/<ou_id>
# ---------------------------------------------------------------------------

class TestGetOuSecrets:
    def test_get_ou_secrets_no_token_returns_401(self, client):
        with patch('routes.enrollment.get_user_from_token', return_value=None):
            resp = client.get(f'{BASE}/secrets/1')
        assert resp.status_code == 401

    def test_get_ou_secrets_non_admin_returns_403(self, client, mock_db):
        _setup_admin_auth(mock_db, role='viewer')

        with patch('routes.enrollment.get_user_from_token', return_value=1):
            with patch('routes.enrollment.get_db', return_value=mock_db):
                resp = client.get(f'{BASE}/secrets/1')

        assert resp.status_code == 403

    def test_get_ou_secrets_ou_admin_wrong_ou_returns_403(self, client, mock_db):
        _setup_admin_auth(mock_db, role='ou_admin', ou_id=99)
        mock_db.return_value.select._dual_select._iter_value = []

        with patch('routes.enrollment.get_user_from_token', return_value=1):
            with patch('routes.enrollment.get_db', return_value=mock_db):
                resp = client.get(f'{BASE}/secrets/1')

        assert resp.status_code == 403

    def test_get_ou_secrets_ou_not_found_returns_404(self, client, mock_db):
        _setup_admin_auth(mock_db, role='global_admin')
        mock_db.return_value.select._dual_select._iter_value = []
        mock_db.organization_units.__getitem__ = MagicMock(return_value=None)

        with patch('routes.enrollment.get_user_from_token', return_value=1):
            with patch('routes.enrollment.get_db', return_value=mock_db):
                resp = client.get(f'{BASE}/secrets/1')

        assert resp.status_code == 404

    def test_get_ou_secrets_found_returns_200(self, client, mock_db):
        _setup_admin_auth(mock_db, role='global_admin')
        mock_db.return_value.select._dual_select._iter_value = [_make_secret_row()]
        ou_row = _make_ou_row()
        mock_db.organization_units.__getitem__ = MagicMock(return_value=ou_row)

        with patch('routes.enrollment.get_user_from_token', return_value=1):
            with patch('routes.enrollment.get_db', return_value=mock_db):
                resp = client.get(f'{BASE}/secrets/1')

        assert resp.status_code == 200
        data = resp.get_json()
        assert 'secrets' in data
        assert 'ou' in data


# ---------------------------------------------------------------------------
# POST /api/v1/enrollment/secrets/<ou_id>
# ---------------------------------------------------------------------------

class TestCreateSecret:
    def test_create_secret_no_token_returns_401(self, client):
        with patch('routes.enrollment.get_user_from_token', return_value=None):
            resp = client.post(f'{BASE}/secrets/1', json={})
        assert resp.status_code == 401

    def test_create_secret_non_admin_returns_403(self, client, mock_db):
        _setup_admin_auth(mock_db, role='viewer')

        with patch('routes.enrollment.get_user_from_token', return_value=1):
            with patch('routes.enrollment.get_db', return_value=mock_db):
                resp = client.post(f'{BASE}/secrets/1', json={})

        assert resp.status_code == 403

    def test_create_secret_ou_admin_wrong_ou_returns_403(self, client, mock_db):
        _setup_admin_auth(mock_db, role='ou_admin', ou_id=99)

        with patch('routes.enrollment.get_user_from_token', return_value=1):
            with patch('routes.enrollment.get_db', return_value=mock_db):
                resp = client.post(f'{BASE}/secrets/1', json={})

        assert resp.status_code == 403

    def test_create_secret_ou_not_found_returns_404(self, client, mock_db):
        _setup_admin_auth(mock_db, role='global_admin')
        mock_db.organization_units.__getitem__ = MagicMock(return_value=None)

        with patch('routes.enrollment.get_user_from_token', return_value=1):
            with patch('routes.enrollment.get_db', return_value=mock_db):
                resp = client.post(f'{BASE}/secrets/1', json={})

        assert resp.status_code == 404

    def test_create_secret_success_returns_201(self, client, mock_db):
        _setup_admin_auth(mock_db, role='global_admin')
        ou_row = _make_ou_row()
        mock_db.organization_units.__getitem__ = MagicMock(return_value=ou_row)
        new_secret_row = _make_secret_row(secret_id=10)
        mock_db.ou_enrollment_secrets.insert = MagicMock(return_value=10)
        mock_db.ou_enrollment_secrets.__getitem__ = MagicMock(return_value=new_secret_row)

        with patch('routes.enrollment.get_user_from_token', return_value=1):
            with patch('routes.enrollment.get_db', return_value=mock_db):
                resp = client.post(f'{BASE}/secrets/1', json={'name': 'My Secret'})

        assert resp.status_code == 201
        data = resp.get_json()
        assert 'secret' in data

    def test_create_secret_insert_fails_returns_500(self, client, mock_db):
        _setup_admin_auth(mock_db, role='global_admin')
        ou_row = _make_ou_row()
        mock_db.organization_units.__getitem__ = MagicMock(return_value=ou_row)
        mock_db.ou_enrollment_secrets.insert = MagicMock(return_value=10)
        mock_db.ou_enrollment_secrets.__getitem__ = MagicMock(return_value=None)

        with patch('routes.enrollment.get_user_from_token', return_value=1):
            with patch('routes.enrollment.get_db', return_value=mock_db):
                resp = client.post(f'{BASE}/secrets/1', json={})

        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# DELETE /api/v1/enrollment/secrets/<secret_id>
# ---------------------------------------------------------------------------

class TestDeleteSecret:
    def test_delete_secret_no_token_returns_401(self, client):
        with patch('routes.enrollment.get_user_from_token', return_value=None):
            resp = client.delete(f'{BASE}/secrets/1')
        assert resp.status_code == 401

    def test_delete_secret_non_admin_returns_403(self, client, mock_db):
        _setup_admin_auth(mock_db, role='viewer')

        with patch('routes.enrollment.get_user_from_token', return_value=1):
            with patch('routes.enrollment.get_db', return_value=mock_db):
                resp = client.delete(f'{BASE}/secrets/1')

        assert resp.status_code == 403

    def test_delete_secret_not_found_returns_404(self, client, mock_db):
        _setup_admin_auth(mock_db, role='global_admin')
        mock_db.ou_enrollment_secrets.__getitem__ = MagicMock(return_value=None)

        with patch('routes.enrollment.get_user_from_token', return_value=1):
            with patch('routes.enrollment.get_db', return_value=mock_db):
                resp = client.delete(f'{BASE}/secrets/99')

        assert resp.status_code == 404

    def test_delete_secret_ou_admin_wrong_ou_returns_403(self, client, mock_db):
        _setup_admin_auth(mock_db, role='ou_admin', ou_id=5)
        secret_row = _make_secret_row(secret_id=1, ou_id=10)
        mock_db.ou_enrollment_secrets.__getitem__ = MagicMock(return_value=secret_row)

        with patch('routes.enrollment.get_user_from_token', return_value=1):
            with patch('routes.enrollment.get_db', return_value=mock_db):
                resp = client.delete(f'{BASE}/secrets/1')

        assert resp.status_code == 403

    def test_delete_secret_success_returns_200(self, client, mock_db):
        _setup_admin_auth(mock_db, role='global_admin')
        secret_row = _make_secret_row(secret_id=1, ou_id=1)
        mock_db.ou_enrollment_secrets.__getitem__ = MagicMock(return_value=secret_row)

        with patch('routes.enrollment.get_user_from_token', return_value=1):
            with patch('routes.enrollment.get_db', return_value=mock_db):
                resp = client.delete(f'{BASE}/secrets/1')

        assert resp.status_code == 200
        data = resp.get_json()
        assert 'message' in data


# ---------------------------------------------------------------------------
# POST /api/v1/enrollment/enroll  (PUBLIC endpoint)
# ---------------------------------------------------------------------------

class TestEnrollDevice:
    VALID_PAYLOAD = {
        'secret': 'SECRETVAL12345',
        'device_serial': 'SN-1234',
        'device_hostname': 'my-host',
        'device_os': 'Linux',
        'device_os_version': '5.15',
        'client_type': 'container',
    }

    def test_enroll_missing_field_returns_400(self, client, mock_db):
        bad = dict(self.VALID_PAYLOAD)
        del bad['device_serial']
        with patch('routes.enrollment.get_db', return_value=mock_db):
            resp = client.post(f'{BASE}/enroll', json=bad)
        assert resp.status_code == 400

    def test_enroll_invalid_secret_returns_401(self, client, mock_db):
        mock_db.return_value.select.return_value.first.return_value = None

        with patch('routes.enrollment.get_db', return_value=mock_db):
            resp = client.post(f'{BASE}/enroll', json=self.VALID_PAYLOAD)

        assert resp.status_code == 401

    def test_enroll_new_device_returns_201(self, client, mock_db):
        secret_row = _make_secret_row()
        new_device_row = _make_device_row(device_id=42)

        call_count = [0]

        def first_side():
            val = [secret_row, None][call_count[0]]
            call_count[0] += 1
            return val

        mock_db.return_value.select.return_value.first.side_effect = first_side
        mock_db.device_enrollments.insert = MagicMock(return_value=42)
        mock_db.device_enrollments.__getitem__ = MagicMock(return_value=new_device_row)

        with patch('routes.enrollment.get_db', return_value=mock_db):
            resp = client.post(f'{BASE}/enroll', json=self.VALID_PAYLOAD)

        assert resp.status_code == 201
        data = resp.get_json()
        assert data['device_id'] == 42

    def test_enroll_existing_device_updates_and_returns_200(self, client, mock_db):
        secret_row = _make_secret_row()
        existing_device = _make_device_row(device_id=5)

        call_count = [0]

        def first_side():
            val = [secret_row, existing_device][call_count[0]]
            call_count[0] += 1
            return val

        mock_db.return_value.select.return_value.first.side_effect = first_side

        with patch('routes.enrollment.get_db', return_value=mock_db):
            resp = client.post(f'{BASE}/enroll', json=self.VALID_PAYLOAD)

        assert resp.status_code == 200
        data = resp.get_json()
        assert 'already enrolled' in data['message']

    def test_enroll_missing_all_required_fields_returns_400(self, client, mock_db):
        with patch('routes.enrollment.get_db', return_value=mock_db):
            resp = client.post(f'{BASE}/enroll', json={})
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# GET /api/v1/enrollment/devices
# ---------------------------------------------------------------------------

class TestListDevices:
    def test_list_devices_no_token_returns_401(self, client):
        with patch('routes.enrollment.get_user_from_token', return_value=None):
            resp = client.get(f'{BASE}/devices')
        assert resp.status_code == 401

    def test_list_devices_unknown_role_returns_403(self, client, mock_db):
        _setup_admin_auth(mock_db, role='viewer')

        with patch('routes.enrollment.get_user_from_token', return_value=1):
            with patch('routes.enrollment.get_db', return_value=mock_db):
                resp = client.get(f'{BASE}/devices')

        assert resp.status_code == 403

    def test_list_devices_global_admin_returns_all(self, client, mock_db):
        _setup_admin_auth(mock_db, role='global_admin')
        device_row = _make_device_row()
        mock_db.return_value.select._dual_select._iter_value = [device_row]

        with patch('routes.enrollment.get_user_from_token', return_value=1):
            with patch('routes.enrollment.get_db', return_value=mock_db):
                resp = client.get(f'{BASE}/devices')

        assert resp.status_code == 200
        data = resp.get_json()
        assert 'devices' in data

    def test_list_devices_global_reporter_returns_200(self, client, mock_db):
        _setup_admin_auth(mock_db, role='global_reporter')
        mock_db.return_value.select._dual_select._iter_value = []

        with patch('routes.enrollment.get_user_from_token', return_value=1):
            with patch('routes.enrollment.get_db', return_value=mock_db):
                resp = client.get(f'{BASE}/devices')

        assert resp.status_code == 200

    def test_list_devices_ou_admin_returns_200(self, client, mock_db):
        _setup_admin_auth(mock_db, role='ou_admin', ou_id=1)
        mock_db.return_value.select._dual_select._iter_value = []

        with patch('routes.enrollment.get_user_from_token', return_value=1):
            with patch('routes.enrollment.get_db', return_value=mock_db):
                resp = client.get(f'{BASE}/devices')

        assert resp.status_code == 200

    def test_list_devices_user_not_found_returns_404(self, client, mock_db):
        mock_db.users.__getitem__ = MagicMock(return_value=None)

        with patch('routes.enrollment.get_user_from_token', return_value=1):
            with patch('routes.enrollment.get_db', return_value=mock_db):
                resp = client.get(f'{BASE}/devices')

        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/v1/enrollment/devices/<device_id>
# ---------------------------------------------------------------------------

class TestGetDevice:
    def test_get_device_no_token_returns_401(self, client):
        with patch('routes.enrollment.get_user_from_token', return_value=None):
            resp = client.get(f'{BASE}/devices/1')
        assert resp.status_code == 401

    def test_get_device_not_found_returns_404(self, client, mock_db):
        user_row = _make_user_row(role='global_admin')
        mock_db.users.__getitem__ = MagicMock(return_value=user_row)
        mock_db.device_enrollments.__getitem__ = MagicMock(return_value=None)

        with patch('routes.enrollment.get_user_from_token', return_value=1):
            with patch('routes.enrollment.get_db', return_value=mock_db):
                resp = client.get(f'{BASE}/devices/999')

        assert resp.status_code == 404

    def test_get_device_found_returns_200(self, client, mock_db):
        user_row = _make_user_row(role='global_admin')
        mock_db.users.__getitem__ = MagicMock(return_value=user_row)
        device_row = _make_device_row(device_id=1)
        mock_db.device_enrollments.__getitem__ = MagicMock(return_value=device_row)

        with patch('routes.enrollment.get_user_from_token', return_value=1):
            with patch('routes.enrollment.get_db', return_value=mock_db):
                resp = client.get(f'{BASE}/devices/1')

        assert resp.status_code == 200

    def test_get_device_ou_admin_wrong_ou_returns_403(self, client, mock_db):
        user_row = _make_user_row(role='ou_admin', ou_id=5)
        mock_db.users.__getitem__ = MagicMock(return_value=user_row)
        device_row = _make_device_row(device_id=1, ou_id=10)
        mock_db.device_enrollments.__getitem__ = MagicMock(return_value=device_row)

        with patch('routes.enrollment.get_user_from_token', return_value=1):
            with patch('routes.enrollment.get_db', return_value=mock_db):
                resp = client.get(f'{BASE}/devices/1')

        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# POST /api/v1/enrollment/devices/<device_id>/heartbeat  (no auth)
# ---------------------------------------------------------------------------

class TestDeviceHeartbeat:
    def test_heartbeat_device_not_found_returns_404(self, client, mock_db):
        mock_db.device_enrollments.__getitem__ = MagicMock(return_value=None)

        with patch('routes.enrollment.get_db', return_value=mock_db):
            resp = client.post(f'{BASE}/devices/999/heartbeat')

        assert resp.status_code == 404

    def test_heartbeat_success_returns_200(self, client, mock_db):
        device_row = _make_device_row(device_id=1)
        mock_db.device_enrollments.__getitem__ = MagicMock(return_value=device_row)

        with patch('routes.enrollment.get_db', return_value=mock_db):
            resp = client.post(f'{BASE}/devices/1/heartbeat')

        assert resp.status_code == 200
        data = resp.get_json()
        assert 'message' in data


# ---------------------------------------------------------------------------
# GET /api/v1/enrollment/config
# ---------------------------------------------------------------------------

class TestGetClientConfig:
    def test_get_client_config_with_device_serial_found(self, client, mock_db):
        device_row = _make_device_row()
        config_row = _make_client_config_row(ou_id=1)

        call_count = [0]

        def first_side():
            results = [device_row, config_row, None, None]
            val = results[call_count[0]] if call_count[0] < len(results) else None
            call_count[0] += 1
            return val

        mock_db.return_value.select.return_value.first.side_effect = first_side

        with patch('routes.enrollment.get_db', return_value=mock_db):
            resp = client.get(f'{BASE}/config?device_serial=SN-0001')

        assert resp.status_code == 200
        data = resp.get_json()
        assert 'config' in data

    def test_get_client_config_device_serial_not_found_returns_404(self, client, mock_db):
        mock_db.return_value.select.return_value.first.return_value = None

        with patch('routes.enrollment.get_db', return_value=mock_db):
            resp = client.get(f'{BASE}/config?device_serial=UNKNOWN')

        assert resp.status_code == 404

    def test_get_client_config_no_serial_requires_token(self, client, mock_db):
        """Without device_serial, falls back to JWT auth."""
        with patch('routes.enrollment.get_user_from_token', return_value=None):
            with patch('routes.enrollment.get_db', return_value=mock_db):
                resp = client.get(f'{BASE}/config')

        assert resp.status_code == 401

    def test_get_client_config_no_config_available_returns_404(self, client, mock_db):
        device_row = _make_device_row()
        # device found, but no config
        call_count = [0]

        def first_side():
            results = [device_row, None, None]
            val = results[call_count[0]] if call_count[0] < len(results) else None
            call_count[0] += 1
            return val

        mock_db.return_value.select.return_value.first.side_effect = first_side

        with patch('routes.enrollment.get_db', return_value=mock_db):
            resp = client.get(f'{BASE}/config?device_serial=SN-0001')

        assert resp.status_code == 404

    def test_get_client_config_with_schedule_returns_interval(self, client, mock_db):
        device_row = _make_device_row()
        config_row = _make_client_config_row(ou_id=1)
        config_row.config_data = {'schedule': {'interval_seconds': 300, 'offset_percent': 10}}

        call_count = [0]

        def first_side():
            results = [device_row, config_row, None, None]
            val = results[call_count[0]] if call_count[0] < len(results) else None
            call_count[0] += 1
            return val

        mock_db.return_value.select.return_value.first.side_effect = first_side

        with patch('routes.enrollment.get_db', return_value=mock_db):
            resp = client.get(f'{BASE}/config?device_serial=SN-0001')

        assert resp.status_code == 200
        data = resp.get_json()
        assert 'next_checkin_seconds' in data


# ---------------------------------------------------------------------------
# GET /api/v1/enrollment/configs
# ---------------------------------------------------------------------------

class TestListClientConfigs:
    def test_list_configs_no_token_returns_401(self, client):
        with patch('routes.enrollment.get_user_from_token', return_value=None):
            resp = client.get(f'{BASE}/configs')
        assert resp.status_code == 401

    def test_list_configs_non_admin_returns_403(self, client, mock_db):
        _setup_admin_auth(mock_db, role='viewer')

        with patch('routes.enrollment.get_user_from_token', return_value=1):
            with patch('routes.enrollment.get_db', return_value=mock_db):
                resp = client.get(f'{BASE}/configs')

        assert resp.status_code == 403

    def test_list_configs_global_admin_returns_200(self, client, mock_db):
        _setup_admin_auth(mock_db, role='global_admin')
        mock_db.return_value.select._dual_select._iter_value = []

        with patch('routes.enrollment.get_user_from_token', return_value=1):
            with patch('routes.enrollment.get_db', return_value=mock_db):
                resp = client.get(f'{BASE}/configs')

        assert resp.status_code == 200
        data = resp.get_json()
        assert 'configs' in data

    def test_list_configs_ou_admin_returns_200(self, client, mock_db):
        _setup_admin_auth(mock_db, role='ou_admin', ou_id=1)
        mock_db.return_value.select._dual_select._iter_value = []

        with patch('routes.enrollment.get_user_from_token', return_value=1):
            with patch('routes.enrollment.get_db', return_value=mock_db):
                resp = client.get(f'{BASE}/configs')

        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# GET /api/v1/enrollment/configs/<ou_id>
# ---------------------------------------------------------------------------

class TestGetOuConfig:
    def test_get_ou_config_no_token_returns_401(self, client):
        with patch('routes.enrollment.get_user_from_token', return_value=None):
            resp = client.get(f'{BASE}/configs/1')
        assert resp.status_code == 401

    def test_get_ou_config_non_admin_returns_403(self, client, mock_db):
        _setup_admin_auth(mock_db, role='viewer')

        with patch('routes.enrollment.get_user_from_token', return_value=1):
            with patch('routes.enrollment.get_db', return_value=mock_db):
                resp = client.get(f'{BASE}/configs/1')

        assert resp.status_code == 403

    def test_get_ou_config_ou_admin_wrong_ou_returns_403(self, client, mock_db):
        _setup_admin_auth(mock_db, role='ou_admin', ou_id=99)

        with patch('routes.enrollment.get_user_from_token', return_value=1):
            with patch('routes.enrollment.get_db', return_value=mock_db):
                resp = client.get(f'{BASE}/configs/1')

        assert resp.status_code == 403

    def test_get_ou_config_not_found_returns_404(self, client, mock_db):
        _setup_admin_auth(mock_db, role='global_admin')
        # Both OU-specific and default returns None
        mock_db.return_value.select.return_value.first.return_value = None

        with patch('routes.enrollment.get_user_from_token', return_value=1):
            with patch('routes.enrollment.get_db', return_value=mock_db):
                resp = client.get(f'{BASE}/configs/1')

        assert resp.status_code == 404

    def test_get_ou_config_found_returns_200(self, client, mock_db):
        _setup_admin_auth(mock_db, role='global_admin')
        config_row = _make_client_config_row(ou_id=1)
        mock_db.return_value.select.return_value.first.return_value = config_row

        with patch('routes.enrollment.get_user_from_token', return_value=1):
            with patch('routes.enrollment.get_db', return_value=mock_db):
                resp = client.get(f'{BASE}/configs/1')

        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# PUT /api/v1/enrollment/configs/<ou_id>
# ---------------------------------------------------------------------------

class TestUpdateOuConfig:
    def test_update_ou_config_no_token_returns_401(self, client):
        with patch('routes.enrollment.get_user_from_token', return_value=None):
            resp = client.put(f'{BASE}/configs/1', json={'config_data': {}})
        assert resp.status_code == 401

    def test_update_ou_config_non_admin_returns_403(self, client, mock_db):
        _setup_admin_auth(mock_db, role='viewer')

        with patch('routes.enrollment.get_user_from_token', return_value=1):
            with patch('routes.enrollment.get_db', return_value=mock_db):
                resp = client.put(f'{BASE}/configs/1', json={'config_data': {}})

        assert resp.status_code == 403

    def test_update_ou_config_missing_config_data_returns_400(self, client, mock_db):
        _setup_admin_auth(mock_db, role='global_admin')

        with patch('routes.enrollment.get_user_from_token', return_value=1):
            with patch('routes.enrollment.get_db', return_value=mock_db):
                resp = client.put(f'{BASE}/configs/1', json={})

        assert resp.status_code == 400

    def test_update_ou_config_ou_not_found_returns_404(self, client, mock_db):
        _setup_admin_auth(mock_db, role='global_admin')
        mock_db.organization_units.__getitem__ = MagicMock(return_value=None)

        with patch('routes.enrollment.get_user_from_token', return_value=1):
            with patch('routes.enrollment.get_db', return_value=mock_db):
                resp = client.put(f'{BASE}/configs/1', json={'config_data': {'key': 'val'}})

        assert resp.status_code == 404

    def test_update_ou_config_creates_new_when_missing(self, client, mock_db):
        _setup_admin_auth(mock_db, role='global_admin')
        ou_row = _make_ou_row()
        mock_db.organization_units.__getitem__ = MagicMock(return_value=ou_row)
        config_row = _make_client_config_row(ou_id=1)

        call_count = [0]

        def first_side():
            results = [None, config_row]  # first: no existing; second: newly created
            val = results[call_count[0]] if call_count[0] < len(results) else config_row
            call_count[0] += 1
            return val

        mock_db.return_value.select.return_value.first.side_effect = first_side
        mock_db.client_configs.insert = MagicMock(return_value=5)
        mock_db.client_configs.__getitem__ = MagicMock(return_value=config_row)

        with patch('routes.enrollment.get_user_from_token', return_value=1):
            with patch('routes.enrollment.get_db', return_value=mock_db):
                resp = client.put(f'{BASE}/configs/1', json={'config_data': {'key': 'val'}})

        assert resp.status_code == 200
        data = resp.get_json()
        assert 'config' in data

    def test_update_ou_config_updates_existing(self, client, mock_db):
        _setup_admin_auth(mock_db, role='global_admin')
        ou_row = _make_ou_row()
        mock_db.organization_units.__getitem__ = MagicMock(return_value=ou_row)
        config_row = _make_client_config_row(ou_id=1)
        # Route calls .first() twice: once to check existing, once to return updated
        mock_db.return_value.select.return_value.first.side_effect = [config_row, config_row]

        with patch('routes.enrollment.get_user_from_token', return_value=1):
            with patch('routes.enrollment.get_db', return_value=mock_db):
                resp = client.put(f'{BASE}/configs/1', json={'config_data': {'key': 'val'}})

        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# GET /api/v1/enrollment/configs/default
# ---------------------------------------------------------------------------

class TestGetDefaultConfig:
    def test_get_default_config_not_found_returns_404(self, client, mock_db):
        mock_db.return_value.select.return_value.first.return_value = None

        with patch('routes.enrollment.get_db', return_value=mock_db):
            resp = client.get(f'{BASE}/configs/default')

        assert resp.status_code == 404

    def test_get_default_config_found_returns_200(self, client, mock_db):
        config_row = _make_client_config_row(is_default=True)
        mock_db.return_value.select.return_value.first.return_value = config_row

        with patch('routes.enrollment.get_db', return_value=mock_db):
            resp = client.get(f'{BASE}/configs/default')

        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# PUT /api/v1/enrollment/configs/default
# ---------------------------------------------------------------------------

class TestUpdateDefaultConfig:
    def test_update_default_config_no_token_returns_401(self, client):
        with patch('routes.enrollment.get_user_from_token', return_value=None):
            resp = client.put(f'{BASE}/configs/default', json={'config_data': {}})
        assert resp.status_code == 401

    def test_update_default_config_non_global_admin_returns_403(self, client, mock_db):
        user_row = _make_user_row(role='ou_admin')
        mock_db.users.__getitem__ = MagicMock(return_value=user_row)

        with patch('routes.enrollment.get_user_from_token', return_value=1):
            with patch('routes.enrollment.get_db', return_value=mock_db):
                resp = client.put(f'{BASE}/configs/default', json={'config_data': {}})

        assert resp.status_code == 403

    def test_update_default_config_missing_config_data_returns_400(self, client, mock_db):
        user_row = _make_user_row(role='global_admin')
        mock_db.users.__getitem__ = MagicMock(return_value=user_row)

        with patch('routes.enrollment.get_user_from_token', return_value=1):
            with patch('routes.enrollment.get_db', return_value=mock_db):
                resp = client.put(f'{BASE}/configs/default', json={})

        assert resp.status_code == 400

    def test_update_default_config_not_found_returns_404(self, client, mock_db):
        user_row = _make_user_row(role='global_admin')
        mock_db.users.__getitem__ = MagicMock(return_value=user_row)
        mock_db.return_value.select.return_value.first.return_value = None

        with patch('routes.enrollment.get_user_from_token', return_value=1):
            with patch('routes.enrollment.get_db', return_value=mock_db):
                resp = client.put(f'{BASE}/configs/default', json={'config_data': {}})

        assert resp.status_code == 404

    def test_update_default_config_success_returns_200(self, client, mock_db):
        user_row = _make_user_row(role='global_admin')
        mock_db.users.__getitem__ = MagicMock(return_value=user_row)
        config_row = _make_client_config_row(is_default=True)
        # Route calls .first() twice: once to find, once to return updated
        mock_db.return_value.select.return_value.first.side_effect = [config_row, config_row]

        with patch('routes.enrollment.get_user_from_token', return_value=1):
            with patch('routes.enrollment.get_db', return_value=mock_db):
                resp = client.put(f'{BASE}/configs/default', json={'config_data': {'key': 'val'}})

        assert resp.status_code == 200
        data = resp.get_json()
        assert 'config' in data
