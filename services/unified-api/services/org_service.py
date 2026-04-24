"""Organization service for WaddlePerf Unified API"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from penguin_dal import AsyncDB


class OrganizationService:
    """Handle organization CRUD operations with penguin-dal AsyncDB"""

    def __init__(self, db: AsyncDB) -> None:
        """Initialize service with database instance.

        Args:
            db: penguin-dal AsyncDB instance
        """
        self.db = db

    async def list_organizations(
        self, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List all organizations.

        Args:
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of organization records
        """
        rows = await self.db(self.db.organizations.id > 0).select(
            limitby=(offset, offset + limit),
            orderby=self.db.organizations.created_at,
        )
        return [row.as_dict() for row in rows]

    async def get_organization(self, org_id: int) -> Optional[Dict[str, Any]]:
        """Get organization by ID.

        Args:
            org_id: Organization ID

        Returns:
            Organization record or None
        """
        rows = await self.db(self.db.organizations.id == org_id).select()
        row = rows.first()
        return row.as_dict() if row else None

    async def create_organization(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new organization.

        Args:
            data: Organization data

        Returns:
            Created organization record
        """
        org_id = await self.db.organizations.async_insert(**data)
        return await self.get_organization(org_id)

    async def update_organization(
        self, org_id: int, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update organization.

        Args:
            org_id: Organization ID
            data: Updated organization data

        Returns:
            Updated organization record or None
        """
        existing = await self.get_organization(org_id)
        if not existing:
            return None
        data['updated_at'] = datetime.utcnow()
        await self.db(self.db.organizations.id == org_id).update(**data)
        return await self.get_organization(org_id)

    async def delete_organization(self, org_id: int) -> bool:
        """Delete organization.

        Args:
            org_id: Organization ID

        Returns:
            True if successful, False otherwise
        """
        existing = await self.get_organization(org_id)
        if not existing:
            return False
        await self.db(self.db.organizations.id == org_id).delete()
        return True

    async def list_organizational_units(
        self, org_id: int, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List organizational units for an organization.

        Args:
            org_id: Organization ID
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of organizational unit records
        """
        rows = await self.db(
            self.db.organizational_units.organization_id == org_id
        ).select(
            limitby=(offset, offset + limit),
            orderby=self.db.organizational_units.created_at,
        )
        return [row.as_dict() for row in rows]

    async def get_organizational_unit(
        self, org_id: int, ou_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get organizational unit by ID.

        Args:
            org_id: Organization ID
            ou_id: Organizational unit ID

        Returns:
            Organizational unit record or None
        """
        rows = await self.db(
            (self.db.organizational_units.organization_id == org_id) &
            (self.db.organizational_units.id == ou_id)
        ).select()
        row = rows.first()
        return row.as_dict() if row else None

    async def create_organizational_unit(
        self, org_id: int, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create organizational unit.

        Args:
            org_id: Organization ID
            data: OU data

        Returns:
            Created organizational unit record
        """
        data['organization_id'] = org_id
        ou_id = await self.db.organizational_units.async_insert(**data)
        return await self.get_organizational_unit(org_id, ou_id)

    async def update_organizational_unit(
        self, org_id: int, ou_id: int, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update organizational unit.

        Args:
            org_id: Organization ID
            ou_id: Organizational unit ID
            data: Updated OU data

        Returns:
            Updated organizational unit record or None
        """
        existing = await self.get_organizational_unit(org_id, ou_id)
        if not existing:
            return None
        data['updated_at'] = datetime.utcnow()
        await self.db(
            (self.db.organizational_units.organization_id == org_id) &
            (self.db.organizational_units.id == ou_id)
        ).update(**data)
        return await self.get_organizational_unit(org_id, ou_id)

    async def delete_organizational_unit(self, org_id: int, ou_id: int) -> bool:
        """Delete organizational unit.

        Args:
            org_id: Organization ID
            ou_id: Organizational unit ID

        Returns:
            True if successful, False otherwise
        """
        existing = await self.get_organizational_unit(org_id, ou_id)
        if not existing:
            return False
        await self.db(
            (self.db.organizational_units.organization_id == org_id) &
            (self.db.organizational_units.id == ou_id)
        ).delete()
        return True
