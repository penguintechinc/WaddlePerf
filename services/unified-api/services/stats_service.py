"""Statistics service for WaddlePerf Unified API"""
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from penguin_dal import AsyncDB


class StatsService:
    """Handle statistics and aggregation with penguin-dal AsyncDB"""

    def __init__(self, db: AsyncDB) -> None:
        """Initialize service with database instance.

        Args:
            db: penguin-dal AsyncDB instance
        """
        self.db = db

    async def get_summary(
        self,
        org_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get overall statistics summary.

        Args:
            org_id: Organization ID
            start_date: Filter by start date (ISO format)
            end_date: Filter by end date (ISO format)

        Returns:
            Dictionary with overall statistics
        """
        query = self.db.test_result.organization_id == org_id

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

        rows = await self.db(query).select()
        total = len(rows)

        if total == 0:
            return {
                'total_tests': 0,
                'success_count': 0,
                'failure_count': 0,
                'success_rate': 0.0,
                'avg_duration_ms': 0,
                'avg_latency_ms': 0
            }

        success_count = sum(1 for row in rows if row.success)
        failure_count = total - success_count
        success_rate = (success_count / total * 100) if total > 0 else 0

        # Calculate averages
        total_duration = sum(row.duration_ms or 0 for row in rows)
        avg_duration = total_duration / total if total > 0 else 0

        # Calculate average latency from metrics
        latencies = []
        for row in rows:
            try:
                metrics = json.loads(row.metrics or '{}')
                if 'latency_ms' in metrics:
                    latencies.append(metrics['latency_ms'])
            except (json.JSONDecodeError, TypeError):
                pass

        avg_latency = sum(latencies) / len(latencies) if latencies else 0

        return {
            'total_tests': total,
            'success_count': success_count,
            'failure_count': failure_count,
            'success_rate': round(success_rate, 2),
            'avg_duration_ms': round(avg_duration, 2),
            'avg_latency_ms': round(avg_latency, 2)
        }

    async def get_by_device(
        self,
        org_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get statistics aggregated by device.

        Args:
            org_id: Organization ID
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of devices

        Returns:
            List of per-device statistics
        """
        query = self.db.test_result.organization_id == org_id

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

        rows = await self.db(query).select()

        # Aggregate by device_id
        device_stats: Dict[Any, Dict[str, Any]] = {}
        for row in rows:
            device_id = row.device_id
            if device_id not in device_stats:
                device_stats[device_id] = {
                    'total': 0,
                    'success': 0,
                    'durations': []
                }

            device_stats[device_id]['total'] += 1
            if row.success:
                device_stats[device_id]['success'] += 1
            device_stats[device_id]['durations'].append(row.duration_ms or 0)

        # Build results
        results = []
        for device_id, stats in sorted(
            device_stats.items(), key=lambda x: x[1]['total'], reverse=True
        )[:limit]:
            total = stats['total']
            success_count = stats['success']
            success_rate = (success_count / total * 100) if total > 0 else 0
            avg_duration = sum(stats['durations']) / total if total > 0 else 0

            # Get device details if available
            device_name = f"Device {device_id}" if device_id else "Unknown"
            if device_id:
                device_rows = await self.db(self.db.devices.id == device_id).select()
                device_row = device_rows.first()
                if device_row:
                    device_name = device_row.device_name or device_name

            results.append({
                'device_id': device_id,
                'device_name': device_name,
                'total_tests': total,
                'success_count': success_count,
                'success_rate': round(success_rate, 2),
                'avg_duration_ms': round(avg_duration, 2)
            })

        return results

    async def get_by_type(
        self,
        org_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get statistics aggregated by test type.

        Args:
            org_id: Organization ID
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of test types

        Returns:
            List of per-test-type statistics
        """
        query = self.db.test_result.organization_id == org_id

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

        rows = await self.db(query).select()

        # Aggregate by test_type from metadata
        type_stats: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            try:
                metadata = json.loads(row.metadata or '{}')
                test_type = metadata.get('test_type', 'unknown')
            except (json.JSONDecodeError, TypeError):
                test_type = 'unknown'

            if test_type not in type_stats:
                type_stats[test_type] = {
                    'total': 0,
                    'success': 0,
                    'durations': []
                }

            type_stats[test_type]['total'] += 1
            if row.success:
                type_stats[test_type]['success'] += 1
            type_stats[test_type]['durations'].append(row.duration_ms or 0)

        # Build results
        results = []
        for test_type, stats in sorted(
            type_stats.items(), key=lambda x: x[1]['total'], reverse=True
        )[:limit]:
            total = stats['total']
            success_count = stats['success']
            success_rate = (success_count / total * 100) if total > 0 else 0
            avg_duration = sum(stats['durations']) / total if total > 0 else 0

            results.append({
                'test_type': test_type,
                'total_tests': total,
                'success_count': success_count,
                'success_rate': round(success_rate, 2),
                'avg_duration_ms': round(avg_duration, 2)
            })

        return results

    async def get_trends(
        self,
        org_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        interval: str = 'daily',
        metric: str = 'success_rate'
    ) -> Dict[str, Any]:
        """Get time-series data for trends.

        Args:
            org_id: Organization ID
            start_date: Filter by start date
            end_date: Filter by end date
            interval: Time interval (hourly, daily, weekly)
            metric: Metric to trend (success_rate, avg_duration, count)

        Returns:
            Dictionary with time-series data
        """
        query = self.db.test_result.organization_id == org_id

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
            orderby=self.db.test_result.created_at
        )

        # Aggregate by time interval
        time_buckets: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            dt = row.created_at
            if interval == 'hourly':
                key = dt.replace(minute=0, second=0, microsecond=0)
            elif interval == 'weekly':
                key = dt.replace(hour=0, minute=0, second=0, microsecond=0)
                # Round down to Monday
                days_since_monday = key.weekday()
                key = key - timedelta(days=days_since_monday)
            else:  # daily
                key = dt.replace(hour=0, minute=0, second=0, microsecond=0)

            key_str = key.isoformat()
            if key_str not in time_buckets:
                time_buckets[key_str] = {
                    'total': 0,
                    'success': 0,
                    'durations': []
                }

            time_buckets[key_str]['total'] += 1
            if row.success:
                time_buckets[key_str]['success'] += 1
            time_buckets[key_str]['durations'].append(row.duration_ms or 0)

        # Calculate metric for each bucket
        timestamps = []
        values = []
        for key_str in sorted(time_buckets.keys()):
            timestamps.append(key_str)
            bucket = time_buckets[key_str]
            total = bucket['total']

            if metric == 'success_rate':
                value = (bucket['success'] / total * 100) if total > 0 else 0
            elif metric == 'avg_duration':
                value = sum(bucket['durations']) / total if total > 0 else 0
            else:  # count
                value = total

            values.append(round(value, 2))

        return {
            'timestamps': timestamps,
            'values': values,
            'metric': metric,
            'interval': interval
        }

    async def get_recent(
        self,
        org_id: int,
        device_id: Optional[int] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get recent test results.

        Args:
            org_id: Organization ID
            device_id: Filter by device ID
            limit: Number of recent tests

        Returns:
            List of recent test results
        """
        query = self.db.test_result.organization_id == org_id

        if device_id:
            query = query & (self.db.test_result.device_id == device_id)

        rows = await self.db(query).select(
            limitby=(0, limit),
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

            results.append(result)

        return results
