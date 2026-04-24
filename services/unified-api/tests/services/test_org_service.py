"""Unit tests for OrganizationService"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock

from services.org_service import OrganizationService
from tests.conftest import make_mock_row, make_mock_rowset


@pytest.fixture
def org_service(mock_db):
    """Provide an OrganizationService wired to a mock DB."""
    return OrganizationService(db=mock_db)


def _make_org_row(org_id: int = 1, name: str = 'Acme Corp') -> MagicMock:
    """Build a mock organization row."""
    row = make_mock_row({
        'id': org_id,
        'name': name,
        'description': 'A test organization',
        'status': 'active',
        'created_at': datetime(2025, 1, 1),
        'updated_at': datetime(2025, 1, 1),
    })
    row.as_dict.return_value = {
        'id': org_id,
        'name': name,
        'description': 'A test organization',
        'status': 'active',
    }
    return row


def _make_ou_row(ou_id: int = 1, org_id: int = 1, name: str = 'Engineering') -> MagicMock:
    """Build a mock organizational_units row."""
    row = make_mock_row({
        'id': ou_id,
        'organization_id': org_id,
        'name': name,
        'description': '',
        'status': 'active',
    })
    row.as_dict.return_value = {
        'id': ou_id,
        'organization_id': org_id,
        'name': name,
    }
    return row


class TestListOrganizations:
    """Test OrganizationService.list_organizations()."""

    async def test_returns_list(self, org_service, mock_db):
        """Returns a list of organization dicts."""
        org_row = _make_org_row()
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([org_row]))

        result = await org_service.list_organizations()

        assert isinstance(result, list)
        assert len(result) == 1

    async def test_empty_returns_empty_list(self, org_service, mock_db):
        """Returns empty list when no organizations."""
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        result = await org_service.list_organizations()

        assert result == []

    async def test_multiple_orgs_returned(self, org_service, mock_db):
        """Multiple organizations are all returned."""
        orgs = [_make_org_row(i, f'Org {i}') for i in range(1, 4)]
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset(orgs))

        result = await org_service.list_organizations()

        assert len(result) == 3

    async def test_as_dict_called_on_rows(self, org_service, mock_db):
        """as_dict() is called on each row."""
        org_row = _make_org_row()
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([org_row]))

        await org_service.list_organizations()

        org_row.as_dict.assert_called()


class TestGetOrganization:
    """Test OrganizationService.get_organization()."""

    async def test_returns_org_dict(self, org_service, mock_db):
        """Returns organization dict when found."""
        org_row = _make_org_row(5)
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([org_row]))

        result = await org_service.get_organization(5)

        assert result is not None
        assert result['id'] == 5

    async def test_returns_none_when_not_found(self, org_service, mock_db):
        """Returns None when organization not found."""
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        result = await org_service.get_organization(9999)

        assert result is None


class TestCreateOrganization:
    """Test OrganizationService.create_organization()."""

    async def test_inserts_and_returns_org(self, org_service, mock_db):
        """Inserts organization and returns created record."""
        org_row = _make_org_row(1)
        mock_db.organizations.async_insert = AsyncMock(return_value=1)
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([org_row]))

        result = await org_service.create_organization({'name': 'New Corp'})

        assert result is not None
        mock_db.organizations.async_insert.assert_called_once_with(name='New Corp')

    async def test_returned_id_matches_insert(self, org_service, mock_db):
        """Returned organization has the ID from async_insert."""
        org_row = _make_org_row(42)
        mock_db.organizations.async_insert = AsyncMock(return_value=42)
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([org_row]))

        result = await org_service.create_organization({'name': 'Acme'})

        assert result['id'] == 42


class TestUpdateOrganization:
    """Test OrganizationService.update_organization()."""

    async def test_updates_existing_org(self, org_service, mock_db):
        """Update succeeds when organization exists."""
        org_row = _make_org_row(1)
        mock_db.return_value.select = AsyncMock(
            side_effect=[
                make_mock_rowset([org_row]),  # existence check
                make_mock_rowset([org_row]),  # fetch updated
            ]
        )
        mock_db.return_value.update = AsyncMock(return_value=None)

        result = await org_service.update_organization(1, {'name': 'Updated Corp'})

        assert result is not None
        mock_db.return_value.update.assert_called_once()

    async def test_returns_none_when_not_found(self, org_service, mock_db):
        """Returns None when organization not found."""
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        result = await org_service.update_organization(9999, {'name': 'X'})

        assert result is None

    async def test_updated_at_is_set(self, org_service, mock_db):
        """updated_at timestamp is added to data dict."""
        org_row = _make_org_row(1)
        mock_db.return_value.select = AsyncMock(
            side_effect=[make_mock_rowset([org_row]), make_mock_rowset([org_row])]
        )
        mock_db.return_value.update = AsyncMock(return_value=None)

        data = {'name': 'X'}
        await org_service.update_organization(1, data)

        assert 'updated_at' in data


class TestDeleteOrganization:
    """Test OrganizationService.delete_organization()."""

    async def test_returns_true_when_deleted(self, org_service, mock_db):
        """Returns True when org is found and deleted."""
        org_row = _make_org_row(1)
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([org_row]))
        mock_db.return_value.delete = AsyncMock(return_value=None)

        result = await org_service.delete_organization(1)

        assert result is True
        mock_db.return_value.delete.assert_called_once()

    async def test_returns_false_when_not_found(self, org_service, mock_db):
        """Returns False when org not found."""
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        result = await org_service.delete_organization(999)

        assert result is False


class TestListOrganizationalUnits:
    """Test OrganizationService.list_organizational_units()."""

    async def test_returns_list(self, org_service, mock_db):
        """Returns list of OU dicts."""
        ou_row = _make_ou_row()
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([ou_row]))

        result = await org_service.list_organizational_units(org_id=1)

        assert isinstance(result, list)

    async def test_empty_list(self, org_service, mock_db):
        """Returns empty list when no OUs."""
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        result = await org_service.list_organizational_units(org_id=1)

        assert result == []


class TestGetOrganizationalUnit:
    """Test OrganizationService.get_organizational_unit()."""

    async def test_returns_ou_when_found(self, org_service, mock_db):
        """Returns OU dict when found."""
        ou_row = _make_ou_row(ou_id=5, org_id=1)
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([ou_row]))

        result = await org_service.get_organizational_unit(org_id=1, ou_id=5)

        assert result is not None
        assert result['id'] == 5

    async def test_returns_none_when_not_found(self, org_service, mock_db):
        """Returns None when OU not found."""
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        result = await org_service.get_organizational_unit(org_id=1, ou_id=999)

        assert result is None


class TestCreateOrganizationalUnit:
    """Test OrganizationService.create_organizational_unit()."""

    async def test_inserts_and_returns_ou(self, org_service, mock_db):
        """Inserts OU with org_id attached and returns record."""
        ou_row = _make_ou_row()
        mock_db.organizational_units.async_insert = AsyncMock(return_value=1)
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([ou_row]))

        data = {'name': 'Engineering'}
        result = await org_service.create_organizational_unit(org_id=1, data=data)

        assert result is not None
        assert data['organization_id'] == 1
        mock_db.organizational_units.async_insert.assert_called_once()


class TestUpdateOrganizationalUnit:
    """Test OrganizationService.update_organizational_unit()."""

    async def test_updates_existing_ou(self, org_service, mock_db):
        """Update succeeds when OU exists."""
        ou_row = _make_ou_row()
        mock_db.return_value.select = AsyncMock(
            side_effect=[make_mock_rowset([ou_row]), make_mock_rowset([ou_row])]
        )
        mock_db.return_value.update = AsyncMock(return_value=None)

        result = await org_service.update_organizational_unit(1, 1, {'name': 'HR'})

        assert result is not None

    async def test_returns_none_when_not_found(self, org_service, mock_db):
        """Returns None when OU doesn't exist."""
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        result = await org_service.update_organizational_unit(1, 9999, {'name': 'X'})

        assert result is None


class TestDeleteOrganizationalUnit:
    """Test OrganizationService.delete_organizational_unit()."""

    async def test_returns_true_on_success(self, org_service, mock_db):
        """Returns True when OU found and deleted."""
        ou_row = _make_ou_row()
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([ou_row]))
        mock_db.return_value.delete = AsyncMock(return_value=None)

        result = await org_service.delete_organizational_unit(1, 1)

        assert result is True

    async def test_returns_false_when_not_found(self, org_service, mock_db):
        """Returns False when OU not found."""
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        result = await org_service.delete_organizational_unit(1, 999)

        assert result is False
