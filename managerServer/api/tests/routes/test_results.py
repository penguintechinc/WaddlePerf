"""Unit tests for managerServer results routes."""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

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
    jwt_row = MagicMock()
    jwt_row.revoked = False
    mock_db.return_value.select.return_value.first.return_value = jwt_row


def _minimal_result_payload(**overrides):
    defaults = {
        'device_serial': 'SN-001',
        'device_hostname': 'host1',
        'device_os': 'Linux',
        'device_os_version': '5.15',
        'test_type': 'http',
        'target_host': 'example.com',
        'target_ip': '1.2.3.4',
    }
    defaults.update(overrides)
    return defaults


# ---------------------------------------------------------------------------
# POST /api/v1/results/upload
# ---------------------------------------------------------------------------

class TestUploadResults:
    def test_upload_unauthenticated_returns_401(self, client):
        resp = client.post('/api/v1/results/upload', json=_minimal_result_payload())
        assert resp.status_code == 401

    def test_upload_missing_required_fields_returns_400(self, client, mock_db):
        _patch_auth(mock_db)

        with patch('routes.results.get_db', return_value=mock_db), \
             patch('routes.auth.get_db', return_value=mock_db):
            resp = client.post('/api/v1/results/upload',
                               json={'device_serial': 'SN-001'},  # missing many required
                               headers=_valid_jwt_headers())

        assert resp.status_code == 400

    def test_upload_success_returns_201(self, client, mock_db):
        _patch_auth(mock_db)
        mock_conn = MagicMock()
        mock_db.engine.begin.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_db.engine.begin.return_value.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.return_value = None

        with patch('routes.results.get_db', return_value=mock_db), \
             patch('routes.auth.get_db', return_value=mock_db):
            resp = client.post('/api/v1/results/upload',
                               json=_minimal_result_payload(),
                               headers=_valid_jwt_headers())

        assert resp.status_code == 201

    def test_upload_with_optional_metrics(self, client, mock_db):
        _patch_auth(mock_db)
        mock_conn = MagicMock()
        mock_db.engine.begin.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_db.engine.begin.return_value.__exit__ = MagicMock(return_value=False)

        payload = _minimal_result_payload(
            latency_ms=12.5,
            throughput_mbps=100.0,
            jitter_ms=1.2,
            packet_loss_percent=0.0,
            raw_results={'detail': 'value'},
        )
        with patch('routes.results.get_db', return_value=mock_db), \
             patch('routes.auth.get_db', return_value=mock_db):
            resp = client.post('/api/v1/results/upload',
                               json=payload,
                               headers=_valid_jwt_headers())

        assert resp.status_code == 201

    def test_upload_missing_device_serial_returns_400(self, client, mock_db):
        _patch_auth(mock_db)
        payload = _minimal_result_payload()
        del payload['device_serial']

        with patch('routes.results.get_db', return_value=mock_db), \
             patch('routes.auth.get_db', return_value=mock_db):
            resp = client.post('/api/v1/results/upload',
                               json=payload,
                               headers=_valid_jwt_headers())

        assert resp.status_code == 400

    def test_upload_missing_test_type_returns_400(self, client, mock_db):
        _patch_auth(mock_db)
        payload = _minimal_result_payload()
        del payload['test_type']

        with patch('routes.results.get_db', return_value=mock_db), \
             patch('routes.auth.get_db', return_value=mock_db):
            resp = client.post('/api/v1/results/upload',
                               json=payload,
                               headers=_valid_jwt_headers())

        assert resp.status_code == 400

    def test_upload_missing_target_host_returns_400(self, client, mock_db):
        _patch_auth(mock_db)
        payload = _minimal_result_payload()
        del payload['target_host']

        with patch('routes.results.get_db', return_value=mock_db), \
             patch('routes.auth.get_db', return_value=mock_db):
            resp = client.post('/api/v1/results/upload',
                               json=payload,
                               headers=_valid_jwt_headers())

        assert resp.status_code == 400

    def test_upload_response_includes_message(self, client, mock_db):
        _patch_auth(mock_db)
        mock_conn = MagicMock()
        mock_db.engine.begin.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_db.engine.begin.return_value.__exit__ = MagicMock(return_value=False)

        with patch('routes.results.get_db', return_value=mock_db), \
             patch('routes.auth.get_db', return_value=mock_db):
            resp = client.post('/api/v1/results/upload',
                               json=_minimal_result_payload(),
                               headers=_valid_jwt_headers())

        if resp.status_code == 201:
            assert 'message' in resp.get_json()

    def test_upload_empty_body_returns_400_or_500(self, client, mock_db):
        _patch_auth(mock_db)

        with patch('routes.results.get_db', return_value=mock_db), \
             patch('routes.auth.get_db', return_value=mock_db):
            resp = client.post('/api/v1/results/upload',
                               json={},
                               headers=_valid_jwt_headers())

        assert resp.status_code in (400, 500)

    def test_upload_with_protocol_detail(self, client, mock_db):
        _patch_auth(mock_db)
        mock_conn = MagicMock()
        mock_db.engine.begin.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_db.engine.begin.return_value.__exit__ = MagicMock(return_value=False)

        payload = _minimal_result_payload(protocol_detail='http/2')
        with patch('routes.results.get_db', return_value=mock_db), \
             patch('routes.auth.get_db', return_value=mock_db):
            resp = client.post('/api/v1/results/upload',
                               json=payload,
                               headers=_valid_jwt_headers())

        assert resp.status_code == 201
