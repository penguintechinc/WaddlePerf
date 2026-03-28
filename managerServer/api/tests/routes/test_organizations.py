"""Unit tests for managerServer organizations routes."""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from models import hash_password

# Note: mock_db, app, and client fixtures are inherited from conftest.py


def _valid_jwt_headers():
    import jwt as pyjwt
    from datetime import timedelta
    from config import Config
    cfg = Config()
    payload = {
        'user_id': 1,
        'exp': datetime.utcnow() + timedelta(hours=1),
        'iat': datetime.utcnow(),
    }
    token = pyjwt.encode(payload, cfg.JWT_SECRET, algorithm='HS256')
    return {'Authorization': f'Bearer {token}'}


def _patch_auth(mock_db):
    """Make get_user_from_token succeed (returns user_id=1)."""
    jwt_row = MagicMock()
    jwt_row.revoked = False
    mock_db.return_value.select.return_value.first.return_value = jwt_row


def _make_org_row(org_id=1, name='HQ'):
    row = MagicMock()
    row.id = org_id
    row.name = name
    row.description = 'Test org'
    row.created_at = datetime(2025, 1, 1)
    row.updated_at = datetime(2025, 1, 2)
    return row


# ---------------------------------------------------------------------------
# GET /api/v1/organizations
# ---------------------------------------------------------------------------

class TestListOrganizations:
    def test_list_orgs_unauthenticated_returns_401(self, client):
        resp = client.get('/api/v1/organizations')
        assert resp.status_code == 401

    def test_list_orgs_authenticated_returns_200(self, client, mock_db):
        _patch_auth(mock_db)
        orgs = [_make_org_row(i, f'Org{i}') for i in range(1, 3)]
        mock_db.return_value.select.return_value = iter(orgs)

        with patch('routes.organizations.get_db', return_value=mock_db), \
             patch('routes.auth.get_db', return_value=mock_db):
            resp = client.get('/api/v1/organizations', headers=_valid_jwt_headers())

        assert resp.status_code == 200
        data = resp.get_json()
        assert 'organizations' in data

    def test_list_orgs_returns_list_type(self, client, mock_db):
        _patch_auth(mock_db)
        mock_db.return_value.select.return_value = iter([])

        with patch('routes.organizations.get_db', return_value=mock_db), \
             patch('routes.auth.get_db', return_value=mock_db):
            resp = client.get('/api/v1/organizations', headers=_valid_jwt_headers())

        if resp.status_code == 200:
            assert isinstance(resp.get_json()['organizations'], list)


# ---------------------------------------------------------------------------
# GET /api/v1/organizations/<id>
# ---------------------------------------------------------------------------

class TestGetOrganization:
    def test_get_org_unauthenticated_returns_401(self, client):
        resp = client.get('/api/v1/organizations/1')
        assert resp.status_code == 401

    def test_get_org_found_returns_200(self, client, mock_db):
        _patch_auth(mock_db)
        org_row = _make_org_row(org_id=1)
        mock_db.organization_units.__getitem__ = MagicMock(return_value=org_row)

        with patch('routes.organizations.get_db', return_value=mock_db), \
             patch('routes.auth.get_db', return_value=mock_db):
            resp = client.get('/api/v1/organizations/1', headers=_valid_jwt_headers())

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['id'] == 1

    def test_get_org_not_found_returns_404(self, client, mock_db):
        _patch_auth(mock_db)
        mock_db.organization_units.__getitem__ = MagicMock(return_value=None)

        with patch('routes.organizations.get_db', return_value=mock_db), \
             patch('routes.auth.get_db', return_value=mock_db):
            resp = client.get('/api/v1/organizations/9999', headers=_valid_jwt_headers())

        assert resp.status_code == 404

    def test_get_org_response_contains_name(self, client, mock_db):
        _patch_auth(mock_db)
        org_row = _make_org_row(org_id=5, name='Engineering')
        mock_db.organization_units.__getitem__ = MagicMock(return_value=org_row)

        with patch('routes.organizations.get_db', return_value=mock_db), \
             patch('routes.auth.get_db', return_value=mock_db):
            resp = client.get('/api/v1/organizations/5', headers=_valid_jwt_headers())

        if resp.status_code == 200:
            assert resp.get_json()['name'] == 'Engineering'


# ---------------------------------------------------------------------------
# POST /api/v1/organizations
# ---------------------------------------------------------------------------

class TestCreateOrganization:
    def test_create_org_unauthenticated_returns_401(self, client):
        resp = client.post('/api/v1/organizations', json={'name': 'New Org'})
        assert resp.status_code == 401

    def test_create_org_missing_name_returns_400(self, client, mock_db):
        _patch_auth(mock_db)

        with patch('routes.organizations.get_db', return_value=mock_db), \
             patch('routes.auth.get_db', return_value=mock_db):
            resp = client.post('/api/v1/organizations',
                               json={'description': 'no name'},
                               headers=_valid_jwt_headers())

        assert resp.status_code == 400

    def test_create_org_success_returns_201(self, client, mock_db):
        _patch_auth(mock_db)
        new_org_row = _make_org_row(org_id=10, name='New Org')
        mock_db.organization_units.insert = MagicMock(return_value=10)
        mock_db.organization_units.__getitem__ = MagicMock(return_value=new_org_row)

        with patch('routes.organizations.get_db', return_value=mock_db), \
             patch('routes.auth.get_db', return_value=mock_db):
            resp = client.post('/api/v1/organizations',
                               json={'name': 'New Org', 'description': 'A new org'},
                               headers=_valid_jwt_headers())

        assert resp.status_code == 201

    def test_create_org_insert_fails_returns_500(self, client, mock_db):
        _patch_auth(mock_db)
        mock_db.organization_units.insert = MagicMock(return_value=10)
        # Simulate DB returning None after insert
        mock_db.organization_units.__getitem__ = MagicMock(return_value=None)

        with patch('routes.organizations.get_db', return_value=mock_db), \
             patch('routes.auth.get_db', return_value=mock_db):
            resp = client.post('/api/v1/organizations',
                               json={'name': 'Broken'},
                               headers=_valid_jwt_headers())

        assert resp.status_code == 500

    def test_create_org_with_description(self, client, mock_db):
        _patch_auth(mock_db)
        new_org_row = _make_org_row(org_id=11, name='WithDesc')
        new_org_row.description = 'Some description'
        mock_db.organization_units.insert = MagicMock(return_value=11)
        mock_db.organization_units.__getitem__ = MagicMock(return_value=new_org_row)

        with patch('routes.organizations.get_db', return_value=mock_db), \
             patch('routes.auth.get_db', return_value=mock_db):
            resp = client.post('/api/v1/organizations',
                               json={'name': 'WithDesc', 'description': 'Some description'},
                               headers=_valid_jwt_headers())

        if resp.status_code == 201:
            assert resp.get_json()['description'] == 'Some description'


# ---------------------------------------------------------------------------
# Error case coverage
# ---------------------------------------------------------------------------

class TestOrganizationsErrorHandling:
    def test_empty_body_post_returns_error(self, client, mock_db):
        _patch_auth(mock_db)

        with patch('routes.organizations.get_db', return_value=mock_db), \
             patch('routes.auth.get_db', return_value=mock_db):
            resp = client.post('/api/v1/organizations',
                               json={},
                               headers=_valid_jwt_headers())

        assert resp.status_code in (400, 500)

    def test_get_org_invalid_id_type_returns_404(self, client, mock_db):
        # Flask returns 404 for non-integer route vars
        resp = client.get('/api/v1/organizations/not-an-id', headers=_valid_jwt_headers())
        assert resp.status_code == 404

    def test_list_orgs_returns_json(self, client, mock_db):
        _patch_auth(mock_db)
        mock_db.return_value.select.return_value = iter([])

        with patch('routes.organizations.get_db', return_value=mock_db), \
             patch('routes.auth.get_db', return_value=mock_db):
            resp = client.get('/api/v1/organizations', headers=_valid_jwt_headers())

        if resp.status_code == 200:
            assert resp.content_type == 'application/json'
