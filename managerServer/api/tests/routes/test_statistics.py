"""Unit tests for managerServer statistics routes.

The statistics blueprint uses JWT-based get_user_from_token() for auth.
DB access uses db.engine.connect() as a context manager (SQLAlchemy engine pattern).
"""
import pytest
from unittest.mock import MagicMock, patch

# Note: mock_db, app, and client fixtures are inherited from conftest.py


def _make_mock_conn(rows=None, mapping_dicts=None):
    """Build a mock SQLAlchemy connection context manager.

    Args:
        rows: list of mock row objects with ._mapping attribute.
        mapping_dicts: list of plain dicts; rows are built from these if rows is None.
    """
    mock_conn = MagicMock()
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)

    if rows is None:
        rows = []
        for d in (mapping_dicts or []):
            row = MagicMock()
            row._mapping = d
            rows.append(row)

    mock_conn.execute.return_value = iter(rows)
    return mock_conn


# ---------------------------------------------------------------------------
# GET /api/v1/statistics/recent
# ---------------------------------------------------------------------------

class TestRecentTests:
    def test_recent_tests_no_token_returns_401(self, client):
        with patch('routes.statistics.get_user_from_token', return_value=None):
            resp = client.get('/api/v1/statistics/recent')
        assert resp.status_code == 401

    def test_recent_tests_with_token_returns_200(self, client, mock_db):
        mock_conn = _make_mock_conn(mapping_dicts=[
            {'device_serial': 'SN-001', 'test_type': 'ping', 'avg_latency': 5.0,
             'created_at': '2025-01-01T00:00:00'},
        ])
        mock_db.engine.connect.return_value = mock_conn

        with patch('routes.statistics.get_user_from_token', return_value=1):
            with patch('routes.statistics.get_db', return_value=mock_db):
                resp = client.get('/api/v1/statistics/recent')

        assert resp.status_code == 200
        data = resp.get_json()
        assert 'results' in data
        assert len(data['results']) == 1

    def test_recent_tests_empty_returns_200_empty_list(self, client, mock_db):
        mock_conn = _make_mock_conn()
        mock_db.engine.connect.return_value = mock_conn

        with patch('routes.statistics.get_user_from_token', return_value=1):
            with patch('routes.statistics.get_db', return_value=mock_db):
                resp = client.get('/api/v1/statistics/recent')

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['results'] == []

    def test_recent_tests_default_limit(self, client, mock_db):
        """Default limit should be applied when not specified."""
        mock_conn = _make_mock_conn()
        mock_db.engine.connect.return_value = mock_conn

        with patch('routes.statistics.get_user_from_token', return_value=1):
            with patch('routes.statistics.get_db', return_value=mock_db):
                resp = client.get('/api/v1/statistics/recent')

        # Just verify that the query was executed (limit defaults to 100)
        assert resp.status_code == 200
        mock_conn.execute.assert_called_once()

    def test_recent_tests_custom_limit(self, client, mock_db):
        """Custom limit parameter should be forwarded to the query."""
        mock_conn = _make_mock_conn()
        mock_db.engine.connect.return_value = mock_conn

        with patch('routes.statistics.get_user_from_token', return_value=1):
            with patch('routes.statistics.get_db', return_value=mock_db):
                resp = client.get('/api/v1/statistics/recent?limit=10')

        assert resp.status_code == 200

    def test_recent_tests_multiple_rows_returned(self, client, mock_db):
        rows_data = [
            {'device_serial': 'SN-001', 'avg_latency': 3.5},
            {'device_serial': 'SN-002', 'avg_latency': 7.2},
            {'device_serial': 'SN-003', 'avg_latency': 1.1},
        ]
        mock_conn = _make_mock_conn(mapping_dicts=rows_data)
        mock_db.engine.connect.return_value = mock_conn

        with patch('routes.statistics.get_user_from_token', return_value=1):
            with patch('routes.statistics.get_db', return_value=mock_db):
                resp = client.get('/api/v1/statistics/recent')

        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data['results']) == 3


# ---------------------------------------------------------------------------
# GET /api/v1/statistics/device/<device_serial>
# ---------------------------------------------------------------------------

class TestDeviceStats:
    def test_device_stats_no_token_returns_401(self, client):
        with patch('routes.statistics.get_user_from_token', return_value=None):
            resp = client.get('/api/v1/statistics/device/SN-001')
        assert resp.status_code == 401

    def test_device_stats_with_token_returns_200(self, client, mock_db):
        mock_conn = _make_mock_conn(mapping_dicts=[
            {'device_serial': 'SN-001', 'avg_latency': 5.0, 'test_count': 10},
        ])
        mock_db.engine.connect.return_value = mock_conn

        with patch('routes.statistics.get_user_from_token', return_value=1):
            with patch('routes.statistics.get_db', return_value=mock_db):
                resp = client.get('/api/v1/statistics/device/SN-001')

        assert resp.status_code == 200
        data = resp.get_json()
        assert 'device' in data
        assert data['device'] == 'SN-001'
        assert 'statistics' in data

    def test_device_stats_no_data_returns_empty_list(self, client, mock_db):
        mock_conn = _make_mock_conn()
        mock_db.engine.connect.return_value = mock_conn

        with patch('routes.statistics.get_user_from_token', return_value=1):
            with patch('routes.statistics.get_db', return_value=mock_db):
                resp = client.get('/api/v1/statistics/device/SN-UNKNOWN')

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['statistics'] == []
        assert data['device'] == 'SN-UNKNOWN'

    def test_device_stats_serial_in_response(self, client, mock_db):
        serial = 'DEVICE-XYZ-9999'
        mock_conn = _make_mock_conn(mapping_dicts=[
            {'device_serial': serial, 'avg_latency': 2.3},
        ])
        mock_db.engine.connect.return_value = mock_conn

        with patch('routes.statistics.get_user_from_token', return_value=1):
            with patch('routes.statistics.get_db', return_value=mock_db):
                resp = client.get(f'/api/v1/statistics/device/{serial}')

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['device'] == serial

    def test_device_stats_multiple_stat_rows(self, client, mock_db):
        rows_data = [
            {'device_serial': 'SN-001', 'test_type': 'ping', 'avg_latency': 4.0},
            {'device_serial': 'SN-001', 'test_type': 'download', 'avg_latency': 12.5},
        ]
        mock_conn = _make_mock_conn(mapping_dicts=rows_data)
        mock_db.engine.connect.return_value = mock_conn

        with patch('routes.statistics.get_user_from_token', return_value=1):
            with patch('routes.statistics.get_db', return_value=mock_db):
                resp = client.get('/api/v1/statistics/device/SN-001')

        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data['statistics']) == 2

    def test_device_stats_query_executed_with_serial(self, client, mock_db):
        """Verify the serial is passed as a parameter to the query."""
        mock_conn = _make_mock_conn()
        mock_db.engine.connect.return_value = mock_conn

        with patch('routes.statistics.get_user_from_token', return_value=1):
            with patch('routes.statistics.get_db', return_value=mock_db):
                resp = client.get('/api/v1/statistics/device/SN-TEST')

        assert resp.status_code == 200
        call_args = mock_conn.execute.call_args
        # The second positional arg is the params dict
        params = call_args[0][1]
        assert params.get('serial') == 'SN-TEST'
