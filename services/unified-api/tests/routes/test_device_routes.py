"""Integration-style tests for device routes using the Quart test client."""
import pytest
from unittest.mock import AsyncMock, patch

from services.device_service import DeviceService


SAMPLE_DEVICE = {
    'id': 1,
    'device_id': 'abc123',
    'organization_id': 10,
    'device_name': 'Test Device',
    'device_type': 'laptop',
    'os_type': 'linux',
    'status': 'active',
}

SAMPLE_SECRET = {
    'id': 1,
    'secret_token': 'tok-abc123',
    'organization_id': 10,
    'is_active': True,
}


class TestListDevicesRoute:
    """Test GET /api/v1/devices/"""

    async def test_list_returns_200(self, client, app):
        """GET / returns 200 with devices list."""
        with patch.object(DeviceService, 'list_devices', new=AsyncMock(return_value=[SAMPLE_DEVICE])):
            async with client as c:
                resp = await c.get('/api/v1/devices/')

        assert resp.status_code == 200
        data = await resp.get_json()
        assert data['status'] == 'success'
        assert isinstance(data['data'], list)

    async def test_list_empty_returns_200(self, client, app):
        """GET / returns 200 with empty list when no devices."""
        with patch.object(DeviceService, 'list_devices', new=AsyncMock(return_value=[])):
            async with client as c:
                resp = await c.get('/api/v1/devices/')

        assert resp.status_code == 200
        data = await resp.get_json()
        assert data['data'] == []

    async def test_list_with_org_id_filter(self, client, app):
        """GET /?org_id=10 is accepted."""
        with patch.object(DeviceService, 'list_devices', new=AsyncMock(return_value=[])):
            async with client as c:
                resp = await c.get('/api/v1/devices/?org_id=10')

        assert resp.status_code == 200

    async def test_list_with_pagination(self, client, app):
        """GET /?limit=5&offset=10 is accepted."""
        with patch.object(DeviceService, 'list_devices', new=AsyncMock(return_value=[])):
            async with client as c:
                resp = await c.get('/api/v1/devices/?limit=5&offset=10')

        assert resp.status_code == 200


class TestGetDeviceRoute:
    """Test GET /api/v1/devices/<device_id>"""

    async def test_existing_device_returns_200(self, client, app):
        """GET /<id> returns 200 for existing device."""
        with patch.object(DeviceService, 'get_device', new=AsyncMock(return_value=SAMPLE_DEVICE)):
            async with client as c:
                resp = await c.get('/api/v1/devices/1')

        assert resp.status_code == 200
        data = await resp.get_json()
        assert data['status'] == 'success'
        assert data['data']['id'] == 1

    async def test_missing_device_returns_404(self, client, app):
        """GET /<id> returns 404 when device not found."""
        with patch.object(DeviceService, 'get_device', new=AsyncMock(return_value=None)):
            async with client as c:
                resp = await c.get('/api/v1/devices/9999')

        assert resp.status_code == 404
        data = await resp.get_json()
        assert data['status'] == 'error'

    async def test_response_has_data_key(self, client, app):
        """GET /<id> response contains 'data' key."""
        with patch.object(DeviceService, 'get_device', new=AsyncMock(return_value=SAMPLE_DEVICE)):
            async with client as c:
                resp = await c.get('/api/v1/devices/1')

        data = await resp.get_json()
        assert 'data' in data


class TestEnrollDeviceRoute:
    """Test POST /api/v1/devices/enroll"""

    async def test_valid_enrollment_returns_201(self, client, app):
        """Valid enrollment body returns 201."""
        with patch.object(DeviceService, 'enroll_device', new=AsyncMock(return_value=SAMPLE_DEVICE)):
            async with client as c:
                resp = await c.post(
                    '/api/v1/devices/enroll',
                    json={
                        'enrollment_secret': 'valid-secret',
                        'org_id': 10,
                        'device_name': 'My Device',
                    },
                )

        assert resp.status_code == 201
        data = await resp.get_json()
        assert data['status'] == 'success'

    async def test_invalid_secret_returns_400(self, client, app):
        """Invalid/expired enrollment secret returns 400."""
        with patch.object(DeviceService, 'enroll_device', new=AsyncMock(return_value=None)):
            async with client as c:
                resp = await c.post(
                    '/api/v1/devices/enroll',
                    json={
                        'enrollment_secret': 'bad-secret',
                        'org_id': 10,
                        'device_name': 'Device',
                    },
                )

        assert resp.status_code == 400

    async def test_missing_enrollment_secret_returns_400(self, client, app):
        """Missing enrollment_secret returns 400."""
        async with client as c:
            resp = await c.post(
                '/api/v1/devices/enroll',
                json={'org_id': 10, 'device_name': 'Device'},
            )

        assert resp.status_code == 400

    async def test_missing_org_id_returns_400(self, client, app):
        """Missing org_id returns 400."""
        async with client as c:
            resp = await c.post(
                '/api/v1/devices/enroll',
                json={'enrollment_secret': 'secret', 'device_name': 'Device'},
            )

        assert resp.status_code == 400

    async def test_missing_device_name_returns_400(self, client, app):
        """Missing device_name returns 400."""
        async with client as c:
            resp = await c.post(
                '/api/v1/devices/enroll',
                json={'enrollment_secret': 'secret', 'org_id': 10},
            )

        assert resp.status_code == 400

    async def test_no_body_returns_400(self, client, app):
        """Missing request body returns 400."""
        async with client as c:
            resp = await c.post('/api/v1/devices/enroll')

        assert resp.status_code == 400


class TestUpdateDeviceRoute:
    """Test PUT /api/v1/devices/<device_id>"""

    async def test_update_existing_device_returns_200(self, client, app):
        """PUT /<id> returns 200 with updated device."""
        updated = {**SAMPLE_DEVICE, 'device_name': 'Renamed Device'}
        with patch.object(DeviceService, 'update_device', new=AsyncMock(return_value=updated)):
            async with client as c:
                resp = await c.put(
                    '/api/v1/devices/1',
                    json={'device_name': 'Renamed Device'},
                )

        assert resp.status_code == 200
        data = await resp.get_json()
        assert data['status'] == 'success'

    async def test_update_missing_device_returns_404(self, client, app):
        """PUT /<id> returns 404 when device not found."""
        with patch.object(DeviceService, 'update_device', new=AsyncMock(return_value=None)):
            async with client as c:
                resp = await c.put(
                    '/api/v1/devices/9999',
                    json={'device_name': 'X'},
                )

        assert resp.status_code == 404

    async def test_update_no_body_returns_400(self, client, app):
        """PUT /<id> without body returns 400."""
        async with client as c:
            resp = await c.put('/api/v1/devices/1')

        assert resp.status_code == 400


class TestDeleteDeviceRoute:
    """Test DELETE /api/v1/devices/<device_id>"""

    async def test_delete_existing_device_returns_200(self, client, app):
        """DELETE /<id> returns 200 for existing device."""
        with patch.object(DeviceService, 'delete_device', new=AsyncMock(return_value=True)):
            async with client as c:
                resp = await c.delete('/api/v1/devices/1')

        assert resp.status_code == 200
        data = await resp.get_json()
        assert data['status'] == 'success'

    async def test_delete_missing_device_returns_404(self, client, app):
        """DELETE /<id> returns 404 when device not found."""
        with patch.object(DeviceService, 'delete_device', new=AsyncMock(return_value=False)):
            async with client as c:
                resp = await c.delete('/api/v1/devices/9999')

        assert resp.status_code == 404


class TestEnrollmentSecretsRoutes:
    """Test enrollment secret endpoints."""

    async def test_create_enrollment_secret_returns_201(self, client, app):
        """POST /enrollment-secrets returns 201."""
        with patch.object(
            DeviceService, 'create_enrollment_secret', new=AsyncMock(return_value=SAMPLE_SECRET)
        ):
            async with client as c:
                resp = await c.post(
                    '/api/v1/devices/enrollment-secrets',
                    json={'org_id': 10, 'secret_name': 'Test Secret'},
                )

        assert resp.status_code == 201
        data = await resp.get_json()
        assert data['status'] == 'success'

    async def test_create_enrollment_secret_missing_org_id_returns_400(self, client, app):
        """POST /enrollment-secrets without org_id returns 400."""
        async with client as c:
            resp = await c.post(
                '/api/v1/devices/enrollment-secrets',
                json={'secret_name': 'No Org'},
            )

        assert resp.status_code == 400

    async def test_list_enrollment_secrets_returns_200(self, client, app):
        """GET /enrollment-secrets?org_id=10 returns 200."""
        with patch.object(
            DeviceService, 'list_enrollment_secrets', new=AsyncMock(return_value=[SAMPLE_SECRET])
        ):
            async with client as c:
                resp = await c.get('/api/v1/devices/enrollment-secrets?org_id=10')

        assert resp.status_code == 200
        data = await resp.get_json()
        assert data['status'] == 'success'
        assert isinstance(data['data'], list)

    async def test_list_enrollment_secrets_missing_org_id_returns_400(self, client, app):
        """GET /enrollment-secrets without org_id returns 400."""
        async with client as c:
            resp = await c.get('/api/v1/devices/enrollment-secrets')

        assert resp.status_code == 400
