"""Integration tests for organization routes."""
import pytest
from unittest.mock import AsyncMock, patch

from services.org_service import OrganizationService


SAMPLE_ORG = {
    'id': 10,
    'name': 'Test Organization',
    'description': 'Test org description',
    'contact_email': 'contact@example.com',
    'contact_phone': '+1234567890',
    'address': '123 Main St',
    'status': 'active',
}

SAMPLE_OU = {
    'id': 1,
    'organization_id': 10,
    'name': 'Engineering',
    'description': 'Engineering team',
    'parent_id': None,
    'policy_data': '{}',
    'status': 'active',
}


class TestListOrganizationsRoute:
    """Test GET /api/v1/organizations/"""

    async def test_list_returns_200(self, client, app):
        """GET / returns 200 with organizations list."""
        with patch.object(OrganizationService, 'list_organizations', new=AsyncMock(return_value=[SAMPLE_ORG])):
            async with client as c:
                resp = await c.get('/api/v1/organizations/')

        assert resp.status_code == 200
        data = await resp.get_json()
        assert data['status'] == 'success'
        assert isinstance(data['data'], list)

    async def test_list_empty_returns_200(self, client, app):
        """GET / returns 200 with empty list."""
        with patch.object(OrganizationService, 'list_organizations', new=AsyncMock(return_value=[])):
            async with client as c:
                resp = await c.get('/api/v1/organizations/')

        assert resp.status_code == 200
        data = await resp.get_json()
        assert data['data'] == []

    async def test_list_with_pagination(self, client, app):
        """GET /?limit=10&offset=5 is accepted."""
        with patch.object(OrganizationService, 'list_organizations', new=AsyncMock(return_value=[])):
            async with client as c:
                resp = await c.get('/api/v1/organizations/?limit=10&offset=5')

        assert resp.status_code == 200


class TestGetOrganizationRoute:
    """Test GET /api/v1/organizations/<org_id>"""

    async def test_existing_org_returns_200(self, client, app):
        """GET /<id> returns 200 for existing org."""
        with patch.object(OrganizationService, 'get_organization', new=AsyncMock(return_value=SAMPLE_ORG)):
            async with client as c:
                resp = await c.get('/api/v1/organizations/10')

        assert resp.status_code == 200
        data = await resp.get_json()
        assert data['status'] == 'success'
        assert data['data']['id'] == 10

    async def test_missing_org_returns_404(self, client, app):
        """GET /<id> returns 404 when org not found."""
        with patch.object(OrganizationService, 'get_organization', new=AsyncMock(return_value=None)):
            async with client as c:
                resp = await c.get('/api/v1/organizations/9999')

        assert resp.status_code == 404
        data = await resp.get_json()
        assert data['status'] == 'error'


class TestCreateOrganizationRoute:
    """Test POST /api/v1/organizations/"""

    async def test_create_without_body_returns_400(self, client, app):
        """POST / without body returns 400."""
        async with client as c:
            resp = await c.post('/api/v1/organizations/', data=b'')

        assert resp.status_code == 400
        data = await resp.get_json()
        assert 'name' in data['message']

    async def test_create_without_name_returns_400(self, client, app):
        """POST / without name returns 400."""
        async with client as c:
            resp = await c.post(
                '/api/v1/organizations/',
                json={'description': 'Test org'}
            )

        assert resp.status_code == 400
        data = await resp.get_json()
        assert 'name' in data['message']

    async def test_create_with_name_returns_201(self, client, app):
        """POST / with name returns 201."""
        with patch.object(OrganizationService, 'create_organization', new=AsyncMock(return_value=SAMPLE_ORG)):
            async with client as c:
                resp = await c.post(
                    '/api/v1/organizations/',
                    json={'name': 'Test Organization'}
                )

        assert resp.status_code == 201
        data = await resp.get_json()
        assert data['status'] == 'success'

    async def test_create_with_optional_fields(self, client, app):
        """POST / with optional fields is accepted."""
        with patch.object(OrganizationService, 'create_organization', new=AsyncMock(return_value=SAMPLE_ORG)):
            async with client as c:
                resp = await c.post(
                    '/api/v1/organizations/',
                    json={
                        'name': 'Test Organization',
                        'description': 'Test description',
                        'contact_email': 'contact@example.com',
                        'contact_phone': '+1234567890',
                        'address': '123 Main St',
                        'status': 'active',
                    }
                )

        assert resp.status_code == 201


class TestUpdateOrganizationRoute:
    """Test PUT /api/v1/organizations/<org_id>"""

    async def test_update_without_body_returns_400(self, client, app):
        """PUT /<id> without body returns 400."""
        async with client as c:
            resp = await c.put('/api/v1/organizations/10', data=b'')

        assert resp.status_code == 400
        data = await resp.get_json()
        assert data['status'] == 'error'

    async def test_update_existing_org_returns_200(self, client, app):
        """PUT /<id> for existing org returns 200."""
        updated_org = {**SAMPLE_ORG, 'status': 'inactive'}
        with patch.object(OrganizationService, 'update_organization', new=AsyncMock(return_value=updated_org)):
            async with client as c:
                resp = await c.put(
                    '/api/v1/organizations/10',
                    json={'status': 'inactive'}
                )

        assert resp.status_code == 200
        data = await resp.get_json()
        assert data['status'] == 'success'

    async def test_update_missing_org_returns_404(self, client, app):
        """PUT /<id> for missing org returns 404."""
        with patch.object(OrganizationService, 'update_organization', new=AsyncMock(return_value=None)):
            async with client as c:
                resp = await c.put(
                    '/api/v1/organizations/9999',
                    json={'name': 'New Name'}
                )

        assert resp.status_code == 404
        data = await resp.get_json()
        assert data['status'] == 'error'


class TestDeleteOrganizationRoute:
    """Test DELETE /api/v1/organizations/<org_id>"""

    async def test_delete_existing_org_returns_200(self, client, app):
        """DELETE /<id> for existing org returns 200."""
        with patch.object(OrganizationService, 'delete_organization', new=AsyncMock(return_value=True)):
            async with client as c:
                resp = await c.delete('/api/v1/organizations/10')

        assert resp.status_code == 200
        data = await resp.get_json()
        assert data['status'] == 'success'

    async def test_delete_missing_org_returns_404(self, client, app):
        """DELETE /<id> for missing org returns 404."""
        with patch.object(OrganizationService, 'delete_organization', new=AsyncMock(return_value=False)):
            async with client as c:
                resp = await c.delete('/api/v1/organizations/9999')

        assert resp.status_code == 404
        data = await resp.get_json()
        assert data['status'] == 'error'


class TestListOrganizationalUnitsRoute:
    """Test GET /api/v1/organizations/<org_id>/units"""

    async def test_list_units_returns_200(self, client, app):
        """GET /<org_id>/units returns 200."""
        with patch.object(OrganizationService, 'list_organizational_units', new=AsyncMock(return_value=[SAMPLE_OU])):
            async with client as c:
                resp = await c.get('/api/v1/organizations/10/units')

        assert resp.status_code == 200
        data = await resp.get_json()
        assert data['status'] == 'success'
        assert isinstance(data['data'], list)

    async def test_list_units_empty_returns_200(self, client, app):
        """GET /<org_id>/units returns 200 with empty list."""
        with patch.object(OrganizationService, 'list_organizational_units', new=AsyncMock(return_value=[])):
            async with client as c:
                resp = await c.get('/api/v1/organizations/10/units')

        assert resp.status_code == 200
        data = await resp.get_json()
        assert data['data'] == []

    async def test_list_units_with_pagination(self, client, app):
        """GET /<org_id>/units?limit=10&offset=5 is accepted."""
        with patch.object(OrganizationService, 'list_organizational_units', new=AsyncMock(return_value=[])):
            async with client as c:
                resp = await c.get('/api/v1/organizations/10/units?limit=10&offset=5')

        assert resp.status_code == 200


class TestCreateOrganizationalUnitRoute:
    """Test POST /api/v1/organizations/<org_id>/units"""

    async def test_create_unit_without_name_returns_400(self, client, app):
        """POST /<org_id>/units without name returns 400."""
        async with client as c:
            resp = await c.post(
                '/api/v1/organizations/10/units',
                json={'description': 'Test OU'}
            )

        assert resp.status_code == 400
        data = await resp.get_json()
        assert 'name' in data['message']

    async def test_create_unit_with_name_returns_201(self, client, app):
        """POST /<org_id>/units with name returns 201."""
        with patch.object(OrganizationService, 'create_organizational_unit', new=AsyncMock(return_value=SAMPLE_OU)):
            async with client as c:
                resp = await c.post(
                    '/api/v1/organizations/10/units',
                    json={'name': 'Engineering'}
                )

        assert resp.status_code == 201
        data = await resp.get_json()
        assert data['status'] == 'success'

    async def test_create_unit_with_optional_fields(self, client, app):
        """POST /<org_id>/units with optional fields is accepted."""
        with patch.object(OrganizationService, 'create_organizational_unit', new=AsyncMock(return_value=SAMPLE_OU)):
            async with client as c:
                resp = await c.post(
                    '/api/v1/organizations/10/units',
                    json={
                        'name': 'Engineering',
                        'description': 'Engineering team',
                        'parent_id': None,
                        'policy_data': '{}',
                        'status': 'active',
                    }
                )

        assert resp.status_code == 201


class TestUpdateOrganizationalUnitRoute:
    """Test PUT /api/v1/organizations/<org_id>/units/<ou_id>"""

    async def test_update_unit_without_body_returns_400(self, client, app):
        """PUT /<org_id>/units/<ou_id> without body returns 400."""
        async with client as c:
            resp = await c.put('/api/v1/organizations/10/units/1', data=b'')

        assert resp.status_code == 400
        data = await resp.get_json()
        assert data['status'] == 'error'

    async def test_update_unit_returns_200(self, client, app):
        """PUT /<org_id>/units/<ou_id> returns 200."""
        updated_ou = {**SAMPLE_OU, 'status': 'inactive'}
        with patch.object(OrganizationService, 'update_organizational_unit', new=AsyncMock(return_value=updated_ou)):
            async with client as c:
                resp = await c.put(
                    '/api/v1/organizations/10/units/1',
                    json={'status': 'inactive'}
                )

        assert resp.status_code == 200
        data = await resp.get_json()
        assert data['status'] == 'success'

    async def test_update_missing_unit_returns_404(self, client, app):
        """PUT /<org_id>/units/<ou_id> for missing unit returns 404."""
        with patch.object(OrganizationService, 'update_organizational_unit', new=AsyncMock(return_value=None)):
            async with client as c:
                resp = await c.put(
                    '/api/v1/organizations/10/units/9999',
                    json={'name': 'New Name'}
                )

        assert resp.status_code == 404
        data = await resp.get_json()
        assert data['status'] == 'error'


class TestDeleteOrganizationalUnitRoute:
    """Test DELETE /api/v1/organizations/<org_id>/units/<ou_id>"""

    async def test_delete_unit_returns_200(self, client, app):
        """DELETE /<org_id>/units/<ou_id> returns 200."""
        with patch.object(OrganizationService, 'delete_organizational_unit', new=AsyncMock(return_value=True)):
            async with client as c:
                resp = await c.delete('/api/v1/organizations/10/units/1')

        assert resp.status_code == 200
        data = await resp.get_json()
        assert data['status'] == 'success'

    async def test_delete_missing_unit_returns_404(self, client, app):
        """DELETE /<org_id>/units/<ou_id> for missing unit returns 404."""
        with patch.object(OrganizationService, 'delete_organizational_unit', new=AsyncMock(return_value=False)):
            async with client as c:
                resp = await c.delete('/api/v1/organizations/10/units/9999')

        assert resp.status_code == 404
        data = await resp.get_json()
        assert data['status'] == 'error'
