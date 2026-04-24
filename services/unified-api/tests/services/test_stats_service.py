"""Unit tests for StatsService"""
import json
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock

from services.stats_service import StatsService
from tests.conftest import make_mock_row, make_mock_rowset


@pytest.fixture
def stats_service(mock_db):
    """Provide a StatsService wired to a mock DB."""
    return StatsService(db=mock_db)


def _make_result_row(
    result_id: int = 1,
    org_id: int = 10,
    device_id: int = 5,
    success: bool = True,
    duration_ms: int = 200,
    metrics: dict = None,
    metadata: dict = None,
    created_at: datetime = None,
) -> MagicMock:
    """Build a mock test_result row."""
    metrics_str = json.dumps(metrics or {})
    metadata_str = json.dumps(metadata or {'test_type': 'ping'})
    return make_mock_row({
        'id': result_id,
        'organization_id': org_id,
        'device_id': device_id,
        'success': success,
        'duration_ms': duration_ms,
        'metrics': metrics_str,
        'metadata': metadata_str,
        'created_at': created_at or datetime.now(timezone.utc),
    })


class TestGetSummary:
    """Test StatsService.get_summary()."""

    async def test_empty_returns_zeros(self, stats_service, mock_db):
        """No results returns all-zero summary."""
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        result = await stats_service.get_summary(org_id=10)

        assert result['total_tests'] == 0
        assert result['success_count'] == 0
        assert result['failure_count'] == 0
        assert result['success_rate'] == 0.0
        assert result['avg_duration_ms'] == 0
        assert result['avg_latency_ms'] == 0

    async def test_all_success_summary(self, stats_service, mock_db):
        """All-success result set gives 100% success rate."""
        rows = [_make_result_row(i, success=True, duration_ms=100) for i in range(1, 4)]
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset(rows))

        result = await stats_service.get_summary(org_id=10)

        assert result['total_tests'] == 3
        assert result['success_count'] == 3
        assert result['failure_count'] == 0
        assert result['success_rate'] == 100.0

    async def test_mixed_success_failure(self, stats_service, mock_db):
        """Mixed results give correct success/failure counts."""
        rows = [
            _make_result_row(1, success=True),
            _make_result_row(2, success=False),
            _make_result_row(3, success=True),
            _make_result_row(4, success=False),
        ]
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset(rows))

        result = await stats_service.get_summary(org_id=10)

        assert result['success_count'] == 2
        assert result['failure_count'] == 2
        assert result['success_rate'] == 50.0

    async def test_avg_duration_calculated(self, stats_service, mock_db):
        """Average duration is computed correctly."""
        rows = [_make_result_row(i, duration_ms=100 * i) for i in range(1, 4)]
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset(rows))

        result = await stats_service.get_summary(org_id=10)

        # (100 + 200 + 300) / 3 = 200.0
        assert result['avg_duration_ms'] == 200.0

    async def test_avg_latency_from_metrics(self, stats_service, mock_db):
        """avg_latency_ms is extracted from metrics JSON."""
        rows = [
            _make_result_row(1, metrics={'latency_ms': 50}),
            _make_result_row(2, metrics={'latency_ms': 150}),
        ]
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset(rows))

        result = await stats_service.get_summary(org_id=10)

        # (50 + 150) / 2 = 100.0
        assert result['avg_latency_ms'] == 100.0

    async def test_invalid_start_date_gracefully_ignored(self, stats_service, mock_db):
        """Invalid start_date string does not raise."""
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        result = await stats_service.get_summary(org_id=10, start_date='bad-date')

        assert 'total_tests' in result

    async def test_valid_date_range_accepted(self, stats_service, mock_db):
        """Valid ISO date range is accepted without error."""
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        result = await stats_service.get_summary(
            org_id=10,
            start_date='2025-01-01T00:00:00Z',
            end_date='2025-12-31T23:59:59Z',
        )

        assert 'total_tests' in result


class TestGetByDevice:
    """Test StatsService.get_by_device()."""

    async def test_empty_returns_empty_list(self, stats_service, mock_db):
        """No results returns empty list."""
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))
        # device lookup also returns empty
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        result = await stats_service.get_by_device(org_id=10)

        assert result == []

    async def test_aggregates_by_device_id(self, stats_service, mock_db):
        """Results are grouped by device_id."""
        rows = [
            _make_result_row(1, device_id=1, success=True),
            _make_result_row(2, device_id=1, success=False),
            _make_result_row(3, device_id=2, success=True),
        ]
        # First select returns test results; device lookups return empty (no name)
        mock_db.return_value.select = AsyncMock(
            side_effect=[
                make_mock_rowset(rows),
                make_mock_rowset([]),  # device 1 lookup
                make_mock_rowset([]),  # device 2 lookup
            ]
        )

        result = await stats_service.get_by_device(org_id=10)

        assert len(result) == 2

    async def test_result_has_required_keys(self, stats_service, mock_db):
        """Each device result has required summary keys."""
        rows = [_make_result_row(1, device_id=5, success=True, duration_ms=300)]
        mock_db.return_value.select = AsyncMock(
            side_effect=[make_mock_rowset(rows), make_mock_rowset([])]
        )

        result = await stats_service.get_by_device(org_id=10)

        assert len(result) == 1
        device = result[0]
        assert 'device_id' in device
        assert 'total_tests' in device
        assert 'success_count' in device
        assert 'success_rate' in device
        assert 'avg_duration_ms' in device


class TestGetByType:
    """Test StatsService.get_by_type()."""

    async def test_empty_returns_empty_list(self, stats_service, mock_db):
        """No results returns empty list."""
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        result = await stats_service.get_by_type(org_id=10)

        assert result == []

    async def test_aggregates_by_test_type(self, stats_service, mock_db):
        """Results grouped by metadata.test_type."""
        rows = [
            _make_result_row(1, metadata={'test_type': 'ping'}, success=True),
            _make_result_row(2, metadata={'test_type': 'ping'}, success=False),
            _make_result_row(3, metadata={'test_type': 'speed'}, success=True),
        ]
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset(rows))

        result = await stats_service.get_by_type(org_id=10)

        assert len(result) == 2

    async def test_unknown_type_for_invalid_metadata(self, stats_service, mock_db):
        """Rows with invalid metadata JSON get 'unknown' as test_type."""
        row = make_mock_row({
            'id': 1,
            'organization_id': 10,
            'device_id': 1,
            'success': True,
            'duration_ms': 100,
            'metrics': '{}',
            'metadata': 'INVALID_JSON',
            'created_at': datetime.now(timezone.utc),
        })
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([row]))

        result = await stats_service.get_by_type(org_id=10)

        assert len(result) == 1
        assert result[0]['test_type'] == 'unknown'

    async def test_result_has_required_keys(self, stats_service, mock_db):
        """Each type result has required keys."""
        rows = [_make_result_row(1, metadata={'test_type': 'latency'}, success=True)]
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset(rows))

        result = await stats_service.get_by_type(org_id=10)

        assert len(result) == 1
        item = result[0]
        assert 'test_type' in item
        assert 'total_tests' in item
        assert 'success_count' in item
        assert 'success_rate' in item
        assert 'avg_duration_ms' in item


class TestGetTrends:
    """Test StatsService.get_trends()."""

    async def test_empty_returns_structure(self, stats_service, mock_db):
        """No data returns dict with timestamps/values lists."""
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        result = await stats_service.get_trends(org_id=10)

        assert 'timestamps' in result
        assert 'values' in result
        assert 'metric' in result
        assert 'interval' in result
        assert result['timestamps'] == []
        assert result['values'] == []

    async def test_default_metric_is_success_rate(self, stats_service, mock_db):
        """Default metric is 'success_rate'."""
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        result = await stats_service.get_trends(org_id=10)

        assert result['metric'] == 'success_rate'

    async def test_default_interval_is_daily(self, stats_service, mock_db):
        """Default interval is 'daily'."""
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        result = await stats_service.get_trends(org_id=10)

        assert result['interval'] == 'daily'

    async def test_count_metric(self, stats_service, mock_db):
        """count metric produces correct values."""
        row = _make_result_row(1, success=True)
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([row]))

        result = await stats_service.get_trends(org_id=10, metric='count')

        assert len(result['values']) == 1
        assert result['values'][0] == 1.0

    async def test_hourly_interval_accepted(self, stats_service, mock_db):
        """hourly interval is accepted without error."""
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        result = await stats_service.get_trends(org_id=10, interval='hourly')

        assert result['interval'] == 'hourly'

    async def test_weekly_interval_accepted(self, stats_service, mock_db):
        """weekly interval is accepted without error."""
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        result = await stats_service.get_trends(org_id=10, interval='weekly')

        assert result['interval'] == 'weekly'


class TestGetRecent:
    """Test StatsService.get_recent()."""

    async def test_returns_list(self, stats_service, mock_db):
        """Returns a list of recent results."""
        row = _make_result_row(1)
        row.as_dict = MagicMock(return_value={
            'id': 1, 'success': True, 'duration_ms': 100,
            'metrics': '{}', 'metadata': '{}',
        })
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([row]))

        result = await stats_service.get_recent(org_id=10)

        assert isinstance(result, list)

    async def test_empty_result(self, stats_service, mock_db):
        """Returns empty list when no results."""
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        result = await stats_service.get_recent(org_id=10)

        assert result == []

    async def test_device_filter_applied(self, stats_service, mock_db):
        """device_id filter is applied to query."""
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        await stats_service.get_recent(org_id=10, device_id=5)

        mock_db.return_value.select.assert_called_once()

    async def test_metrics_parsed_in_recent(self, stats_service, mock_db):
        """metrics field is parsed from JSON in recent results."""
        row = _make_result_row(1, metrics={'rtt': 10})
        row.as_dict = MagicMock(return_value={
            'id': 1, 'success': True, 'duration_ms': 100,
            'metrics': '{"rtt": 10}', 'metadata': '{}',
        })
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([row]))

        result = await stats_service.get_recent(org_id=10)

        assert isinstance(result[0]['metrics'], dict)
        assert result[0]['metrics']['rtt'] == 10
