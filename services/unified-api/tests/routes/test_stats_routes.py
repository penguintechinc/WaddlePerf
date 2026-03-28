"""Integration tests for statistics routes."""
import pytest
from unittest.mock import AsyncMock, patch

from services.stats_service import StatsService


SAMPLE_SUMMARY = {
    'total_tests': 100,
    'success_count': 95,
    'failure_count': 5,
    'success_rate': 95.0,
    'avg_duration_ms': 5000,
    'avg_latency_ms': 50,
}

SAMPLE_DEVICE_STATS = [
    {
        'device_id': 1,
        'device_name': 'Device 1',
        'total_tests': 50,
        'success_count': 48,
        'success_rate': 96.0,
        'avg_duration_ms': 4800,
    },
    {
        'device_id': 2,
        'device_name': 'Device 2',
        'total_tests': 50,
        'success_count': 47,
        'success_rate': 94.0,
        'avg_duration_ms': 5200,
    },
]

SAMPLE_TYPE_STATS = [
    {
        'test_type': 'throughput',
        'total_tests': 50,
        'success_count': 49,
        'success_rate': 98.0,
        'avg_duration_ms': 3000,
    },
    {
        'test_type': 'latency',
        'total_tests': 50,
        'success_count': 46,
        'success_rate': 92.0,
        'avg_duration_ms': 7000,
    },
]

SAMPLE_TRENDS = {
    'timestamps': ['2025-01-01', '2025-01-02', '2025-01-03'],
    'values': [95.0, 94.5, 96.0],
    'metric': 'success_rate',
    'interval': 'daily',
}


class TestGetSummaryRoute:
    """Test GET /api/v1/stats/summary"""

    async def test_summary_requires_org_id(self, client, app):
        """GET /summary without org_id returns 400."""
        async with client as c:
            resp = await c.get('/api/v1/stats/summary')

        assert resp.status_code == 400
        data = await resp.get_json()
        assert data['status'] == 'error'

    async def test_summary_with_org_id_returns_200(self, client, app):
        """GET /summary?org_id=10 returns 200."""
        with patch.object(StatsService, 'get_summary', new=AsyncMock(return_value=SAMPLE_SUMMARY)):
            async with client as c:
                resp = await c.get('/api/v1/stats/summary?org_id=10')

        assert resp.status_code == 200
        data = await resp.get_json()
        assert data['status'] == 'success'
        assert data['data']['total_tests'] == 100

    async def test_summary_with_date_filters(self, client, app):
        """GET /summary?org_id=10&start_date=...&end_date=... is accepted."""
        with patch.object(StatsService, 'get_summary', new=AsyncMock(return_value=SAMPLE_SUMMARY)):
            async with client as c:
                resp = await c.get(
                    '/api/v1/stats/summary?org_id=10&start_date=2025-01-01&end_date=2025-01-31'
                )

        assert resp.status_code == 200


class TestGetByDeviceRoute:
    """Test GET /api/v1/stats/by-device"""

    async def test_by_device_requires_org_id(self, client, app):
        """GET /by-device without org_id returns 400."""
        async with client as c:
            resp = await c.get('/api/v1/stats/by-device')

        assert resp.status_code == 400
        data = await resp.get_json()
        assert data['status'] == 'error'

    async def test_by_device_with_org_id_returns_200(self, client, app):
        """GET /by-device?org_id=10 returns 200."""
        with patch.object(StatsService, 'get_by_device', new=AsyncMock(return_value=SAMPLE_DEVICE_STATS)):
            async with client as c:
                resp = await c.get('/api/v1/stats/by-device?org_id=10')

        assert resp.status_code == 200
        data = await resp.get_json()
        assert data['status'] == 'success'
        assert isinstance(data['data'], list)
        assert len(data['data']) == 2

    async def test_by_device_with_date_filters(self, client, app):
        """GET /by-device?org_id=10&start_date=...&end_date=... is accepted."""
        with patch.object(StatsService, 'get_by_device', new=AsyncMock(return_value=[])):
            async with client as c:
                resp = await c.get(
                    '/api/v1/stats/by-device?org_id=10&start_date=2025-01-01&end_date=2025-01-31'
                )

        assert resp.status_code == 200

    async def test_by_device_with_limit(self, client, app):
        """GET /by-device?org_id=10&limit=10 is accepted."""
        with patch.object(StatsService, 'get_by_device', new=AsyncMock(return_value=[])):
            async with client as c:
                resp = await c.get('/api/v1/stats/by-device?org_id=10&limit=10')

        assert resp.status_code == 200


class TestGetByTypeRoute:
    """Test GET /api/v1/stats/by-type"""

    async def test_by_type_requires_org_id(self, client, app):
        """GET /by-type without org_id returns 400."""
        async with client as c:
            resp = await c.get('/api/v1/stats/by-type')

        assert resp.status_code == 400
        data = await resp.get_json()
        assert data['status'] == 'error'

    async def test_by_type_with_org_id_returns_200(self, client, app):
        """GET /by-type?org_id=10 returns 200."""
        with patch.object(StatsService, 'get_by_type', new=AsyncMock(return_value=SAMPLE_TYPE_STATS)):
            async with client as c:
                resp = await c.get('/api/v1/stats/by-type?org_id=10')

        assert resp.status_code == 200
        data = await resp.get_json()
        assert data['status'] == 'success'
        assert isinstance(data['data'], list)

    async def test_by_type_with_date_filters(self, client, app):
        """GET /by-type?org_id=10&start_date=...&end_date=... is accepted."""
        with patch.object(StatsService, 'get_by_type', new=AsyncMock(return_value=[])):
            async with client as c:
                resp = await c.get(
                    '/api/v1/stats/by-type?org_id=10&start_date=2025-01-01&end_date=2025-01-31'
                )

        assert resp.status_code == 200

    async def test_by_type_with_limit(self, client, app):
        """GET /by-type?org_id=10&limit=10 is accepted."""
        with patch.object(StatsService, 'get_by_type', new=AsyncMock(return_value=[])):
            async with client as c:
                resp = await c.get('/api/v1/stats/by-type?org_id=10&limit=10')

        assert resp.status_code == 200


class TestGetTrendsRoute:
    """Test GET /api/v1/stats/trends"""

    async def test_trends_requires_org_id(self, client, app):
        """GET /trends without org_id returns 400."""
        async with client as c:
            resp = await c.get('/api/v1/stats/trends')

        assert resp.status_code == 400
        data = await resp.get_json()
        assert data['status'] == 'error'

    async def test_trends_with_org_id_returns_200(self, client, app):
        """GET /trends?org_id=10 returns 200."""
        with patch.object(StatsService, 'get_trends', new=AsyncMock(return_value=SAMPLE_TRENDS)):
            async with client as c:
                resp = await c.get('/api/v1/stats/trends?org_id=10')

        assert resp.status_code == 200
        data = await resp.get_json()
        assert data['status'] == 'success'

    async def test_trends_with_invalid_interval_returns_400(self, client, app):
        """GET /trends?org_id=10&interval=invalid returns 400."""
        async with client as c:
            resp = await c.get('/api/v1/stats/trends?org_id=10&interval=invalid')

        assert resp.status_code == 400
        data = await resp.get_json()
        assert 'interval' in data['message']

    async def test_trends_with_valid_intervals(self, client, app):
        """GET /trends with hourly, daily, weekly intervals is accepted."""
        with patch.object(StatsService, 'get_trends', new=AsyncMock(return_value=SAMPLE_TRENDS)):
            async with client as c:
                for interval in ['hourly', 'daily', 'weekly']:
                    resp = await c.get(f'/api/v1/stats/trends?org_id=10&interval={interval}')
                    assert resp.status_code == 200

    async def test_trends_with_invalid_metric_returns_400(self, client, app):
        """GET /trends?org_id=10&metric=invalid returns 400."""
        async with client as c:
            resp = await c.get('/api/v1/stats/trends?org_id=10&metric=invalid')

        assert resp.status_code == 400
        data = await resp.get_json()
        assert 'metric' in data['message']

    async def test_trends_with_valid_metrics(self, client, app):
        """GET /trends with success_rate, avg_duration, count metrics is accepted."""
        with patch.object(StatsService, 'get_trends', new=AsyncMock(return_value=SAMPLE_TRENDS)):
            async with client as c:
                for metric in ['success_rate', 'avg_duration', 'count']:
                    resp = await c.get(f'/api/v1/stats/trends?org_id=10&metric={metric}')
                    assert resp.status_code == 200

    async def test_trends_with_date_filters(self, client, app):
        """GET /trends?org_id=10&start_date=...&end_date=... is accepted."""
        with patch.object(StatsService, 'get_trends', new=AsyncMock(return_value=SAMPLE_TRENDS)):
            async with client as c:
                resp = await c.get(
                    '/api/v1/stats/trends?org_id=10&start_date=2025-01-01&end_date=2025-01-31'
                )

        assert resp.status_code == 200
