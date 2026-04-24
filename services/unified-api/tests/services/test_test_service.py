"""Unit tests for TestService"""
import json
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock

from services.test_service import TestService as WaddlePerfTestService
from tests.conftest import make_mock_row, make_mock_rowset


@pytest.fixture
def test_service(mock_db):
    """Provide a TestService wired to a mock DB."""
    return WaddlePerfTestService(db=mock_db)


def _make_test_row(
    test_id: int = 1,
    org_id: int = 10,
    device_id: int = 5,
    status: str = 'completed',
    success: bool = True,
    duration_ms: int = 1500,
    metrics: dict = None,
    metadata: dict = None,
) -> MagicMock:
    """Build a mock test_result row."""
    metrics_str = json.dumps(metrics or {'latency_ms': 42})
    metadata_str = json.dumps(metadata or {'test_type': 'ping'})
    row = make_mock_row({
        'id': test_id,
        'organization_id': org_id,
        'device_id': device_id,
        'name': f'Test {test_id}',
        'status': status,
        'success': success,
        'duration_ms': duration_ms,
        'error_message': '',
        'test_output': '',
        'metrics': metrics_str,
        'metadata': metadata_str,
        'created_at': datetime.now(timezone.utc),
        'started_at': None,
        'completed_at': None,
    })
    row.as_dict.return_value = {
        'id': test_id,
        'organization_id': org_id,
        'device_id': device_id,
        'status': status,
        'success': success,
        'duration_ms': duration_ms,
        'metrics': metrics_str,
        'metadata': metadata_str,
    }
    return row


class TestListTests:
    """Test TestService.list_tests()."""

    async def test_returns_list(self, test_service, mock_db):
        """Returns a list of test result dicts."""
        row = _make_test_row()
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([row]))

        result = await test_service.list_tests(org_id=10)

        assert isinstance(result, list)

    async def test_empty_result(self, test_service, mock_db):
        """Returns empty list when no results."""
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        result = await test_service.list_tests(org_id=10)

        assert result == []

    async def test_metrics_parsed_as_dict(self, test_service, mock_db):
        """metrics field is parsed from JSON string to dict."""
        row = _make_test_row(metrics={'latency_ms': 99})
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([row]))

        result = await test_service.list_tests(org_id=10)

        assert isinstance(result[0]['metrics'], dict)
        assert result[0]['metrics']['latency_ms'] == 99

    async def test_metadata_parsed_as_dict(self, test_service, mock_db):
        """metadata field is parsed from JSON string to dict."""
        row = _make_test_row(metadata={'test_type': 'speed'})
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([row]))

        result = await test_service.list_tests(org_id=10)

        assert isinstance(result[0]['metadata'], dict)

    async def test_filters_by_test_type(self, test_service, mock_db):
        """test_type filter excludes rows with different test_type in metadata."""
        row_ping = _make_test_row(1, metadata={'test_type': 'ping'})
        row_speed = _make_test_row(2, metadata={'test_type': 'speed'})
        mock_db.return_value.select = AsyncMock(
            return_value=make_mock_rowset([row_ping, row_speed])
        )

        result = await test_service.list_tests(org_id=10, test_type='ping')

        assert len(result) == 1
        assert result[0]['metadata']['test_type'] == 'ping'

    async def test_invalid_start_date_is_ignored(self, test_service, mock_db):
        """Invalid start_date string is gracefully ignored."""
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        # Should not raise
        result = await test_service.list_tests(org_id=10, start_date='not-a-date')

        assert result == []

    async def test_valid_start_date_accepted(self, test_service, mock_db):
        """Valid ISO start_date is accepted without error."""
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        result = await test_service.list_tests(
            org_id=10, start_date='2025-01-01T00:00:00Z'
        )

        assert isinstance(result, list)

    async def test_status_filter_applied(self, test_service, mock_db):
        """status parameter filters the query."""
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        await test_service.list_tests(org_id=10, status='completed')

        mock_db.return_value.select.assert_called_once()


class TestGetTest:
    """Test TestService.get_test()."""

    async def test_returns_test_dict(self, test_service, mock_db):
        """Returns test dict when found."""
        row = _make_test_row(test_id=7)
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([row]))

        result = await test_service.get_test(7)

        assert result is not None
        assert result['id'] == 7

    async def test_returns_none_when_not_found(self, test_service, mock_db):
        """Returns None when test not found."""
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        result = await test_service.get_test(9999)

        assert result is None

    async def test_metrics_parsed(self, test_service, mock_db):
        """metrics field is parsed to dict in get_test."""
        row = _make_test_row(metrics={'bandwidth_mbps': 500})
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([row]))

        result = await test_service.get_test(1)

        assert isinstance(result['metrics'], dict)
        assert result['metrics']['bandwidth_mbps'] == 500

    async def test_metadata_parsed(self, test_service, mock_db):
        """metadata field is parsed to dict in get_test."""
        row = _make_test_row(metadata={'env': 'production'})
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([row]))

        result = await test_service.get_test(1)

        assert isinstance(result['metadata'], dict)

    async def test_invalid_metrics_json_defaults_to_empty_dict(self, test_service, mock_db):
        """Invalid metrics JSON defaults to empty dict."""
        row = _make_test_row()
        row.as_dict.return_value['metrics'] = 'not-valid-json{'
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([row]))

        result = await test_service.get_test(1)

        assert result['metrics'] == {}


class TestCreateTest:
    """Test TestService.create_test()."""

    async def test_creates_test_and_returns_record(self, test_service, mock_db):
        """Inserts test result and returns the created record."""
        new_row = _make_test_row(test_id=99)
        mock_db.test_result.async_insert = AsyncMock(return_value=99)
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([new_row]))

        data = {
            'name': 'Ping Test',
            'organization_id': 10,
            'device_id': 5,
            'status': 'completed',
            'success': True,
            'duration_ms': 100,
        }

        result = await test_service.create_test(data)

        assert result is not None
        mock_db.test_result.async_insert.assert_called_once()

    async def test_metrics_dict_serialized_to_json(self, test_service, mock_db):
        """metrics dict is serialized to JSON string before insert."""
        new_row = _make_test_row()
        mock_db.test_result.async_insert = AsyncMock(return_value=1)
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([new_row]))

        await test_service.create_test({
            'name': 'Test',
            'organization_id': 10,
            'metrics': {'rtt_ms': 20},
        })

        call_kwargs = mock_db.test_result.async_insert.call_args.kwargs
        assert isinstance(call_kwargs['metrics'], str)
        parsed = json.loads(call_kwargs['metrics'])
        assert parsed['rtt_ms'] == 20

    async def test_metadata_dict_serialized(self, test_service, mock_db):
        """metadata dict is serialized to JSON string."""
        new_row = _make_test_row()
        mock_db.test_result.async_insert = AsyncMock(return_value=1)
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([new_row]))

        await test_service.create_test({
            'name': 'Test',
            'organization_id': 10,
            'metadata': {'test_type': 'latency'},
        })

        call_kwargs = mock_db.test_result.async_insert.call_args.kwargs
        assert isinstance(call_kwargs['metadata'], str)

    async def test_returns_none_on_insert_exception(self, test_service, mock_db):
        """Returns None when DB insert raises exception."""
        mock_db.test_result.async_insert = AsyncMock(side_effect=Exception('DB error'))

        result = await test_service.create_test({'name': 'Fail Test', 'organization_id': 10})

        assert result is None

    async def test_status_defaults_to_pending(self, test_service, mock_db):
        """status defaults to 'pending' when not provided."""
        new_row = _make_test_row()
        mock_db.test_result.async_insert = AsyncMock(return_value=1)
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([new_row]))

        await test_service.create_test({'name': 'T', 'organization_id': 10})

        call_kwargs = mock_db.test_result.async_insert.call_args.kwargs
        assert call_kwargs['status'] == 'pending'


class TestDeleteTest:
    """Test TestService.delete_test()."""

    async def test_returns_true_when_deleted(self, test_service, mock_db):
        """Returns True when test found and deleted."""
        row = _make_test_row()
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([row]))
        mock_db.return_value.delete = AsyncMock(return_value=None)

        result = await test_service.delete_test(1)

        assert result is True
        mock_db.return_value.delete.assert_called_once()

    async def test_returns_false_when_not_found(self, test_service, mock_db):
        """Returns False when test not found."""
        mock_db.return_value.select = AsyncMock(return_value=make_mock_rowset([]))

        result = await test_service.delete_test(9999)

        assert result is False
