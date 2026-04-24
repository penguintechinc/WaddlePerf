"""Test service for WaddlePerf Unified API"""
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from penguin_dal import AsyncDB

logger = logging.getLogger(__name__)


class TestService:
    """Handle test result management with penguin-dal AsyncDB"""

    def __init__(self, db: AsyncDB) -> None:
        """Initialize service with database instance.

        Args:
            db: penguin-dal AsyncDB instance
        """
        self.db = db

    async def list_tests(
        self,
        org_id: int,
        device_id: Optional[int] = None,
        test_type: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List test results with optional filtering.

        Args:
            org_id: Organization ID (required)
            device_id: Filter by device ID
            test_type: Filter by test type
            status: Filter by status
            start_date: Filter by start date (ISO format)
            end_date: Filter by end date (ISO format)
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of test result records
        """
        query = self.db.test_result.organization_id == org_id

        if device_id:
            query = query & (self.db.test_result.device_id == device_id)

        if status:
            query = query & (self.db.test_result.status == status)

        # Parse dates if provided
        if start_date:
            try:
                start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query = query & (self.db.test_result.created_at >= start)
            except ValueError:
                pass

        if end_date:
            try:
                end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                query = query & (self.db.test_result.created_at <= end)
            except ValueError:
                pass

        rows = await self.db(query).select(
            limitby=(offset, offset + limit),
            orderby=~self.db.test_result.created_at
        )

        results = []
        for row in rows:
            result = row.as_dict()
            # Parse JSON fields
            try:
                result['metrics'] = json.loads(result.get('metrics', '{}'))
            except (json.JSONDecodeError, TypeError):
                result['metrics'] = {}

            try:
                result['metadata'] = json.loads(result.get('metadata', '{}'))
            except (json.JSONDecodeError, TypeError):
                result['metadata'] = {}

            # Filter by test_type if provided (from metadata)
            if test_type:
                if result['metadata'].get('test_type') != test_type:
                    continue

            results.append(result)

        return results

    async def get_test(self, test_id: int) -> Optional[Dict[str, Any]]:
        """Get test result by ID.

        Args:
            test_id: Test result ID

        Returns:
            Test result record or None
        """
        rows = await self.db(self.db.test_result.id == test_id).select()
        row = rows.first()
        if not row:
            return None

        result = row.as_dict()
        # Parse JSON fields
        try:
            result['metrics'] = json.loads(result.get('metrics', '{}'))
        except (json.JSONDecodeError, TypeError):
            result['metrics'] = {}

        try:
            result['metadata'] = json.loads(result.get('metadata', '{}'))
        except (json.JSONDecodeError, TypeError):
            result['metadata'] = {}

        return result

    async def create_test(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create test result.

        Args:
            data: Test result data

        Returns:
            Created test result record or None
        """
        # Prepare data
        test_data = {
            'test_id': data.get('test_id'),
            'name': data.get('name'),
            'organization_id': data.get('organization_id'),
            'device_id': data.get('device_id'),
            'organization_unit_id': data.get('organization_unit_id'),
            'status': data.get('status', 'pending'),
            'duration_ms': data.get('duration_ms', 0),
            'success': data.get('success', False),
            'error_message': data.get('error_message', ''),
            'test_output': data.get('test_output', ''),
            'started_at': data.get('started_at'),
            'completed_at': data.get('completed_at'),
        }

        # Serialize JSON fields
        metrics = data.get('metrics', {})
        if isinstance(metrics, dict):
            test_data['metrics'] = json.dumps(metrics)
        else:
            test_data['metrics'] = metrics if isinstance(metrics, str) else '{}'

        metadata = data.get('metadata', {})
        if isinstance(metadata, dict):
            test_data['metadata'] = json.dumps(metadata)
        else:
            test_data['metadata'] = metadata if isinstance(metadata, str) else '{}'

        try:
            test_result_id = await self.db.test_result.async_insert(**test_data)
            return await self.get_test(test_result_id)
        except Exception as e:
            logger.error(f"Error creating test result: {e}")
            return None

    async def delete_test(self, test_id: int) -> bool:
        """Delete test result.

        Args:
            test_id: Test result ID

        Returns:
            True if deleted, False if not found
        """
        existing = await self.get_test(test_id)
        if not existing:
            return False

        await self.db(self.db.test_result.id == test_id).delete()
        return True
