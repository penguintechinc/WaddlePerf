"""Unit tests for DeviceService"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock

from services.device_service import DeviceService
from tests.conftest import make_mock_row, make_mock_rowset


@pytest.fixture
def device_service(mock_db):
    """Provide a DeviceService wired to a mock DB."""
    return DeviceService(db=mock_db)


def _make_device_row(device_id: int = 1, org_id: int = 10) -> MagicMock:
    """Build a mock device row."""
    row = make_mock_row({
        'id': device_id,
        'device_id': f'dev-{device_id:04x}',
        'organization_id': org_id,
        'device_name': f'Device {device_id}',
        'device_type': 'laptop',
        'os_type': 'linux',
        'os_version': '22.04',
        'status': 'active',
    })
    row.as_dict.return_value = {
        'id': device_id,
        'device_id': f'dev-{device_id:04x}',
        'organization_id': org_id,
        'device_name': f'Device {device_id}',
    }
    return row


def _make_enrollment_secret_row(
    secret_id: int = 1,
    org_id: int = 10,
    is_active: bool = True,
    expires_future: bool = True,
    max_uses: int = None,
    current_uses: int = 0,
) -> MagicMock:
    """Build a mock enrollment secret row."""
    expires_at = (datetime.utcnow() + timedelta(days=7)) if expires_future else (datetime.utcnow() - timedelta(days=1))
    row = make_mock_row({
        'id': secret_id,
        'organization_id': org_id,
        'secret_token': 'valid-enroll-secret',
        'is_active': is_active,
        'expires_at': expires_at if not expires_future else None,
        'max_uses': max_uses,
        'current_uses': current_uses,
    })
    row.as_dict.return_value = {
        'id': secret_id,
        'secret_token': 'valid-enroll-secret',
        'is_active': is_active,
    }
    return row


class TestListDevices:
    """Test DeviceService.list_devices()."""

    async def test_returns_list(self, device_service, mock_db):
        """Returns a list of device dicts."""
        dev = _make_device_row(1)
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([dev]))

        result = await device_service.list_devices()

        assert isinstance(result, list)
        assert len(result) == 1

    async def test_empty_result(self, device_service, mock_db):
        """Returns empty list when no devices."""
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        result = await device_service.list_devices()

        assert result == []

    async def test_filters_by_org_id(self, device_service, mock_db):
        """Org filter is applied (query built with org_id)."""
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        await device_service.list_devices(org_id=42)

        mock_db.return_value.select.assert_called_once()

    async def test_multiple_devices_returned(self, device_service, mock_db):
        """Multiple devices are all returned."""
        devs = [_make_device_row(i) for i in range(1, 4)]
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset(devs))

        result = await device_service.list_devices()

        assert len(result) == 3


class TestGetDevice:
    """Test DeviceService.get_device()."""

    async def test_returns_device_dict(self, device_service, mock_db):
        """Returns device dict when found."""
        dev = _make_device_row(5)
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([dev]))

        result = await device_service.get_device(5)

        assert result is not None
        assert result['id'] == 5

    async def test_returns_none_when_not_found(self, device_service, mock_db):
        """Returns None when device doesn't exist."""
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        result = await device_service.get_device(9999)

        assert result is None


class TestGetDeviceByDeviceId:
    """Test DeviceService.get_device_by_device_id()."""

    async def test_returns_device_by_string_id(self, device_service, mock_db):
        """Returns device dict when found by string device_id."""
        dev = _make_device_row(1)
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([dev]))

        result = await device_service.get_device_by_device_id('dev-0001')

        assert result is not None

    async def test_returns_none_when_not_found(self, device_service, mock_db):
        """Returns None when no matching string device_id."""
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        result = await device_service.get_device_by_device_id('nonexistent-id')

        assert result is None


class TestEnrollDevice:
    """Test DeviceService.enroll_device()."""

    async def test_valid_secret_creates_device(self, device_service, mock_db):
        """Valid enrollment secret creates device and increments usage."""
        secret_row = _make_enrollment_secret_row(expires_future=True, max_uses=None)
        secret_row.expires_at = None  # no expiry
        dev_row = _make_device_row(1)

        mock_db.return_value.select = AsyncMock(
            side_effect=[
                make_mock_rowset([secret_row]),  # find secret
                make_mock_rowset([dev_row]),     # get_device after insert
            ]
        )
        mock_db.devices.async_insert = AsyncMock(return_value=1)
        mock_db.return_value.update = AsyncMock(return_value=None)

        result = await device_service.enroll_device(
            'valid-enroll-secret', 10, {'device_name': 'New Device'}
        )

        assert result is not None
        mock_db.devices.async_insert.assert_called_once()
        mock_db.return_value.update.assert_called_once()

    async def test_invalid_secret_returns_none(self, device_service, mock_db):
        """Invalid enrollment secret returns None."""
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        result = await device_service.enroll_device(
            'bad-secret', 10, {'device_name': 'Device'}
        )

        assert result is None

    async def test_expired_secret_returns_none(self, device_service, mock_db):
        """Expired secret (expires_at in past) returns None."""
        secret_row = _make_enrollment_secret_row(expires_future=False)
        secret_row.expires_at = datetime.utcnow() - timedelta(hours=1)
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([secret_row]))

        result = await device_service.enroll_device(
            'valid-enroll-secret', 10, {'device_name': 'Device'}
        )

        assert result is None

    async def test_max_uses_exceeded_returns_none(self, device_service, mock_db):
        """Secret at max_uses returns None."""
        secret_row = _make_enrollment_secret_row(max_uses=5, current_uses=5)
        secret_row.expires_at = None
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([secret_row]))

        result = await device_service.enroll_device(
            'valid-enroll-secret', 10, {'device_name': 'Device'}
        )

        assert result is None

    async def test_device_id_auto_generated(self, device_service, mock_db):
        """device_id is auto-generated when not supplied."""
        secret_row = _make_enrollment_secret_row()
        secret_row.expires_at = None
        dev_row = _make_device_row(2)
        mock_db.return_value.select = AsyncMock(
            side_effect=[make_mock_rowset([secret_row]), make_mock_rowset([dev_row])]
        )
        mock_db.devices.async_insert = AsyncMock(return_value=2)
        mock_db.return_value.update = AsyncMock(return_value=None)

        data = {'device_name': 'Auto Device'}
        await device_service.enroll_device('valid-enroll-secret', 10, data)

        assert 'device_id' in data


class TestUpdateDevice:
    """Test DeviceService.update_device()."""

    async def test_updates_existing_device(self, device_service, mock_db):
        """Update succeeds when device exists."""
        dev_row = _make_device_row(1)
        mock_db.return_value.select = AsyncMock(
            side_effect=[
                make_mock_rowset([dev_row]),  # get_device check
                make_mock_rowset([dev_row]),  # get_device after update
            ]
        )
        mock_db.return_value.update = AsyncMock(return_value=None)

        result = await device_service.update_device(1, {'device_name': 'Updated'})

        assert result is not None
        mock_db.return_value.update.assert_called_once()

    async def test_returns_none_when_not_found(self, device_service, mock_db):
        """Returns None when device not found."""
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        result = await device_service.update_device(9999, {'device_name': 'X'})

        assert result is None

    async def test_updated_at_is_set(self, device_service, mock_db):
        """updated_at timestamp is set in update call."""
        dev_row = _make_device_row(1)
        mock_db.return_value.select = AsyncMock(
            side_effect=[make_mock_rowset([dev_row]), make_mock_rowset([dev_row])]
        )
        mock_db.return_value.update = AsyncMock(return_value=None)

        data = {'device_name': 'X'}
        await device_service.update_device(1, data)

        assert 'updated_at' in data


class TestDeleteDevice:
    """Test DeviceService.delete_device()."""

    async def test_returns_true_when_deleted(self, device_service, mock_db):
        """Returns True when device found and deleted."""
        dev_row = _make_device_row(1)
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([dev_row]))
        mock_db.return_value.delete = AsyncMock(return_value=None)

        result = await device_service.delete_device(1)

        assert result is True
        mock_db.return_value.delete.assert_called_once()

    async def test_returns_false_when_not_found(self, device_service, mock_db):
        """Returns False when device not found."""
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        result = await device_service.delete_device(999)

        assert result is False


class TestEnrollmentSecrets:
    """Test enrollment secret CRUD on DeviceService."""

    async def test_create_enrollment_secret(self, device_service, mock_db):
        """create_enrollment_secret inserts and returns the record."""
        secret_row = _make_enrollment_secret_row()
        mock_db.enrollment_secrets.async_insert = AsyncMock(return_value=1)
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([secret_row]))

        result = await device_service.create_enrollment_secret(10, {})

        assert result is not None
        mock_db.enrollment_secrets.async_insert.assert_called_once()

    async def test_create_generates_token(self, device_service, mock_db):
        """secret_token is auto-generated when not supplied."""
        secret_row = _make_enrollment_secret_row()
        mock_db.enrollment_secrets.async_insert = AsyncMock(return_value=1)
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([secret_row]))

        data = {}
        await device_service.create_enrollment_secret(10, data)

        assert 'secret_token' in data

    async def test_list_enrollment_secrets(self, device_service, mock_db):
        """list_enrollment_secrets returns a list."""
        secret_row = _make_enrollment_secret_row()
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([secret_row]))

        result = await device_service.list_enrollment_secrets(org_id=10)

        assert isinstance(result, list)

    async def test_delete_enrollment_secret_returns_true(self, device_service, mock_db):
        """Deleting existing secret returns True."""
        secret_row = _make_enrollment_secret_row()
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([secret_row]))
        mock_db.return_value.delete = AsyncMock(return_value=None)

        result = await device_service.delete_enrollment_secret(1)

        assert result is True

    async def test_delete_enrollment_secret_returns_false_when_missing(self, device_service, mock_db):
        """Deleting non-existent secret returns False."""
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        result = await device_service.delete_enrollment_secret(9999)

        assert result is False
