"""Device service for WaddlePerf Unified API"""
import secrets
from typing import Dict, List, Optional, Any
from datetime import datetime
from penguin_dal import AsyncDB


class DeviceService:
    """Handle device management with penguin-dal AsyncDB"""

    def __init__(self, db: AsyncDB) -> None:
        """Initialize service with database instance.

        Args:
            db: penguin-dal AsyncDB instance
        """
        self.db = db

    async def list_devices(
        self, org_id: Optional[int] = None, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List devices with optional filtering.

        Args:
            org_id: Filter by organization ID
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of device records
        """
        if org_id:
            query = self.db.devices.organization_id == org_id
        else:
            query = self.db.devices.id > 0

        rows = await self.db(query).select(
            limitby=(offset, offset + limit),
            orderby=self.db.devices.created_at,
        )
        return [row.as_dict() for row in rows]

    async def get_device(self, device_id: int) -> Optional[Dict[str, Any]]:
        """Get device by ID.

        Args:
            device_id: Device ID

        Returns:
            Device record or None
        """
        rows = await self.db(self.db.devices.id == device_id).select()
        row = rows.first()
        return row.as_dict() if row else None

    async def get_device_by_device_id(self, device_id_str: str) -> Optional[Dict[str, Any]]:
        """Get device by device_id string.

        Args:
            device_id_str: Device ID string

        Returns:
            Device record or None
        """
        rows = await self.db(self.db.devices.device_id == device_id_str).select()
        row = rows.first()
        return row.as_dict() if row else None

    async def enroll_device(
        self, enrollment_secret: str, org_id: int, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Enroll device using enrollment secret.

        Args:
            enrollment_secret: Enrollment secret token
            org_id: Organization ID
            data: Device data

        Returns:
            Created device record or None
        """
        # Verify secret is valid
        rows = await self.db(
            (self.db.enrollment_secrets.secret_token == enrollment_secret) &
            (self.db.enrollment_secrets.organization_id == org_id) &
            (self.db.enrollment_secrets.is_active == True)  # noqa: E712
        ).select()
        secret_row = rows.first()

        if not secret_row:
            return None

        # Check if secret is expired
        if secret_row.expires_at and secret_row.expires_at < datetime.utcnow():
            return None

        # Check max uses
        if secret_row.max_uses and secret_row.current_uses >= secret_row.max_uses:
            return None

        # Create device
        data['organization_id'] = org_id
        if 'device_id' not in data:
            data['device_id'] = secrets.token_hex(16)

        device_id = await self.db.devices.async_insert(**data)

        # Increment secret usage
        await self.db(self.db.enrollment_secrets.id == secret_row.id).update(
            current_uses=secret_row.current_uses + 1
        )

        return await self.get_device(device_id)

    async def update_device(
        self, device_id: int, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update device.

        Args:
            device_id: Device ID
            data: Updated device data

        Returns:
            Updated device record or None
        """
        existing = await self.get_device(device_id)
        if not existing:
            return None
        data['updated_at'] = datetime.utcnow()
        await self.db(self.db.devices.id == device_id).update(**data)
        return await self.get_device(device_id)

    async def delete_device(self, device_id: int) -> bool:
        """Delete device.

        Args:
            device_id: Device ID

        Returns:
            True if successful, False otherwise
        """
        existing = await self.get_device(device_id)
        if not existing:
            return False
        await self.db(self.db.devices.id == device_id).delete()
        return True

    async def create_enrollment_secret(
        self, org_id: int, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create enrollment secret.

        Args:
            org_id: Organization ID
            data: Secret data

        Returns:
            Created enrollment secret record
        """
        data['organization_id'] = org_id
        if 'secret_token' not in data:
            data['secret_token'] = secrets.token_urlsafe(32)

        secret_id = await self.db.enrollment_secrets.async_insert(**data)
        return await self.get_enrollment_secret(secret_id)

    async def get_enrollment_secret(self, secret_id: int) -> Optional[Dict[str, Any]]:
        """Get enrollment secret by ID.

        Args:
            secret_id: Secret ID

        Returns:
            Enrollment secret record or None
        """
        rows = await self.db(self.db.enrollment_secrets.id == secret_id).select()
        row = rows.first()
        return row.as_dict() if row else None

    async def list_enrollment_secrets(
        self, org_id: int, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List enrollment secrets for organization.

        Args:
            org_id: Organization ID
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of enrollment secret records
        """
        rows = await self.db(
            self.db.enrollment_secrets.organization_id == org_id
        ).select(
            limitby=(offset, offset + limit),
            orderby=self.db.enrollment_secrets.created_at,
        )
        return [row.as_dict() for row in rows]

    async def update_enrollment_secret(
        self, secret_id: int, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update enrollment secret.

        Args:
            secret_id: Secret ID
            data: Updated secret data

        Returns:
            Updated enrollment secret record or None
        """
        existing = await self.get_enrollment_secret(secret_id)
        if not existing:
            return None
        data['updated_at'] = datetime.utcnow()
        await self.db(self.db.enrollment_secrets.id == secret_id).update(**data)
        return await self.get_enrollment_secret(secret_id)

    async def delete_enrollment_secret(self, secret_id: int) -> bool:
        """Delete enrollment secret.

        Args:
            secret_id: Secret ID

        Returns:
            True if successful, False otherwise
        """
        existing = await self.get_enrollment_secret(secret_id)
        if not existing:
            return False
        await self.db(self.db.enrollment_secrets.id == secret_id).delete()
        return True
