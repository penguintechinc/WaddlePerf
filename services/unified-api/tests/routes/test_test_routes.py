"""Integration tests for test result routes."""
import pytest
from unittest.mock import AsyncMock, patch

from services.test_service import TestService


SAMPLE_TEST_RESULT = {
    'id': 1,
    'test_id': 'test-001',
    'name': 'Throughput Test',
    'organization_id': 10,
    'device_id': 1,
    'status': 'completed',
    'duration_ms': 5000,
    'success': True,
    'error_message': None,
    'metrics': {'throughput': 1000},
    'metadata': {},
    'test_output': 'Test output text',
    'started_at': '2025-01-01T00:00:00',
    'completed_at': '2025-01-01T00:00:05',
}


class TestListTestsRoute:
    """Test GET /api/v1/tests/"""

    async def test_list_requires_org_id(self, client, app):
        """GET / without org_id returns 400."""
        async with client as c:
            resp = await c.get('/api/v1/tests/')

        assert resp.status_code == 400
        data = await resp.get_json()
        assert data['status'] == 'error'
        assert 'org_id' in data['message']

    async def test_list_with_org_id_returns_200(self, client, app):
        """GET /?org_id=10 returns 200 with tests list."""
        with patch.object(TestService, 'list_tests', new=AsyncMock(return_value=[SAMPLE_TEST_RESULT])):
            async with client as c:
                resp = await c.get('/api/v1/tests/?org_id=10')

        assert resp.status_code == 200
        data = await resp.get_json()
        assert data['status'] == 'success'
        assert isinstance(data['data'], list)

    async def test_list_empty_returns_200(self, client, app):
        """GET /?org_id=10 returns 200 with empty list."""
        with patch.object(TestService, 'list_tests', new=AsyncMock(return_value=[])):
            async with client as c:
                resp = await c.get('/api/v1/tests/?org_id=10')

        assert resp.status_code == 200
        data = await resp.get_json()
        assert data['data'] == []

    async def test_list_with_device_id_filter(self, client, app):
        """GET /?org_id=10&device_id=1 is accepted."""
        with patch.object(TestService, 'list_tests', new=AsyncMock(return_value=[])):
            async with client as c:
                resp = await c.get('/api/v1/tests/?org_id=10&device_id=1')

        assert resp.status_code == 200

    async def test_list_with_test_type_filter(self, client, app):
        """GET /?org_id=10&test_type=throughput is accepted."""
        with patch.object(TestService, 'list_tests', new=AsyncMock(return_value=[])):
            async with client as c:
                resp = await c.get('/api/v1/tests/?org_id=10&test_type=throughput')

        assert resp.status_code == 200

    async def test_list_with_status_filter(self, client, app):
        """GET /?org_id=10&status=completed is accepted."""
        with patch.object(TestService, 'list_tests', new=AsyncMock(return_value=[])):
            async with client as c:
                resp = await c.get('/api/v1/tests/?org_id=10&status=completed')

        assert resp.status_code == 200

    async def test_list_with_date_filters(self, client, app):
        """GET /?org_id=10&start_date=...&end_date=... is accepted."""
        with patch.object(TestService, 'list_tests', new=AsyncMock(return_value=[])):
            async with client as c:
                resp = await c.get('/api/v1/tests/?org_id=10&start_date=2025-01-01&end_date=2025-01-31')

        assert resp.status_code == 200

    async def test_list_with_pagination(self, client, app):
        """GET /?org_id=10&limit=50&offset=10 is accepted."""
        with patch.object(TestService, 'list_tests', new=AsyncMock(return_value=[])):
            async with client as c:
                resp = await c.get('/api/v1/tests/?org_id=10&limit=50&offset=10')

        assert resp.status_code == 200


class TestGetTestRoute:
    """Test GET /api/v1/tests/<test_id>"""

    async def test_existing_test_returns_200(self, client, app):
        """GET /<id> returns 200 for existing test."""
        with patch.object(TestService, 'get_test', new=AsyncMock(return_value=SAMPLE_TEST_RESULT)):
            async with client as c:
                resp = await c.get('/api/v1/tests/1')

        assert resp.status_code == 200
        data = await resp.get_json()
        assert data['status'] == 'success'
        assert data['data']['id'] == 1

    async def test_missing_test_returns_404(self, client, app):
        """GET /<id> returns 404 when test not found."""
        with patch.object(TestService, 'get_test', new=AsyncMock(return_value=None)):
            async with client as c:
                resp = await c.get('/api/v1/tests/9999')

        assert resp.status_code == 404
        data = await resp.get_json()
        assert data['status'] == 'error'

    async def test_response_has_data_key(self, client, app):
        """GET /<id> response contains 'data' key."""
        with patch.object(TestService, 'get_test', new=AsyncMock(return_value=SAMPLE_TEST_RESULT)):
            async with client as c:
                resp = await c.get('/api/v1/tests/1')

        data = await resp.get_json()
        assert 'data' in data


class TestCreateTestRoute:
    """Test POST /api/v1/tests/"""

    async def test_create_without_body_returns_400(self, client, app):
        """POST / without body returns 400."""
        async with client as c:
            resp = await c.post('/api/v1/tests/', data=b'')

        assert resp.status_code == 400
        data = await resp.get_json()
        assert data['status'] == 'error'

    async def test_create_missing_test_id_returns_400(self, client, app):
        """POST / without test_id returns 400."""
        async with client as c:
            resp = await c.post(
                '/api/v1/tests/',
                json={'name': 'Test', 'organization_id': 10}
            )

        assert resp.status_code == 400
        data = await resp.get_json()
        assert 'test_id' in data['message']

    async def test_create_missing_name_returns_400(self, client, app):
        """POST / without name returns 400."""
        async with client as c:
            resp = await c.post(
                '/api/v1/tests/',
                json={'test_id': 'test-001', 'organization_id': 10}
            )

        assert resp.status_code == 400
        data = await resp.get_json()
        assert 'name' in data['message']

    async def test_create_missing_org_id_returns_400(self, client, app):
        """POST / without organization_id returns 400."""
        async with client as c:
            resp = await c.post(
                '/api/v1/tests/',
                json={'test_id': 'test-001', 'name': 'Test'}
            )

        assert resp.status_code == 400
        data = await resp.get_json()
        assert 'organization_id' in data['message']

    async def test_create_with_required_fields_returns_201(self, client, app):
        """POST / with required fields returns 201."""
        with patch.object(TestService, 'create_test', new=AsyncMock(return_value=SAMPLE_TEST_RESULT)):
            async with client as c:
                resp = await c.post(
                    '/api/v1/tests/',
                    json={
                        'test_id': 'test-001',
                        'name': 'Throughput Test',
                        'organization_id': 10
                    }
                )

        assert resp.status_code == 201
        data = await resp.get_json()
        assert data['status'] == 'success'
        assert data['data']['id'] == 1

    async def test_create_with_optional_fields(self, client, app):
        """POST / with optional fields is accepted."""
        with patch.object(TestService, 'create_test', new=AsyncMock(return_value=SAMPLE_TEST_RESULT)):
            async with client as c:
                resp = await c.post(
                    '/api/v1/tests/',
                    json={
                        'test_id': 'test-001',
                        'name': 'Throughput Test',
                        'organization_id': 10,
                        'device_id': 1,
                        'status': 'completed',
                        'duration_ms': 5000,
                        'success': True,
                        'metrics': {'throughput': 1000},
                        'metadata': {},
                    }
                )

        assert resp.status_code == 201

    async def test_create_service_returns_none_returns_400(self, client, app):
        """POST / when service returns None returns 400."""
        with patch.object(TestService, 'create_test', new=AsyncMock(return_value=None)):
            async with client as c:
                resp = await c.post(
                    '/api/v1/tests/',
                    json={
                        'test_id': 'test-001',
                        'name': 'Test',
                        'organization_id': 10
                    }
                )

        assert resp.status_code == 400


class TestDeleteTestRoute:
    """Test DELETE /api/v1/tests/<test_id>"""

    async def test_delete_existing_test_returns_200(self, client, app):
        """DELETE /<id> for existing test returns 200."""
        with patch.object(TestService, 'delete_test', new=AsyncMock(return_value=True)):
            async with client as c:
                resp = await c.delete('/api/v1/tests/1')

        assert resp.status_code == 200
        data = await resp.get_json()
        assert data['status'] == 'success'

    async def test_delete_missing_test_returns_404(self, client, app):
        """DELETE /<id> for missing test returns 404."""
        with patch.object(TestService, 'delete_test', new=AsyncMock(return_value=False)):
            async with client as c:
                resp = await c.delete('/api/v1/tests/9999')

        assert resp.status_code == 404
        data = await resp.get_json()
        assert data['status'] == 'error'
