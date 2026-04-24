"""Tests for webClient/api test proxy endpoint (/api/test/<test_type>)."""
import pytest
from unittest.mock import patch, MagicMock
import requests as requests_lib


# ---------------------------------------------------------------------------
# POST /api/test/<test_type> — auth disabled (default fixture)
# ---------------------------------------------------------------------------

class TestRunTestValidation:
    def test_invalid_test_type_returns_400(self, client):
        resp = client.post('/api/test/invalid_type', json={'target': 'example.com'})
        assert resp.status_code == 400

    def test_valid_test_type_no_target_returns_400(self, client):
        resp = client.post('/api/test/http', json={})
        assert resp.status_code == 400

    def test_target_too_long_returns_400(self, client):
        long_target = 'a' * 256
        resp = client.post('/api/test/http', json={'target': long_target})
        assert resp.status_code == 400

    def test_invalid_port_returns_400(self, client):
        resp = client.post('/api/test/tcp', json={'target': 'example.com', 'port': 99999})
        assert resp.status_code == 400

    def test_invalid_port_string_returns_400(self, client):
        resp = client.post('/api/test/tcp', json={'target': 'example.com', 'port': 'bad'})
        assert resp.status_code == 400

    def test_invalid_timeout_returns_400(self, client):
        resp = client.post('/api/test/http', json={'target': 'example.com', 'timeout': 999})
        assert resp.status_code == 400

    def test_invalid_count_returns_400(self, client):
        resp = client.post('/api/test/icmp', json={'target': '8.8.8.8', 'count': 9999})
        assert resp.status_code == 400

    def test_all_valid_test_types_accepted(self, client):
        valid_types = ['http', 'tcp', 'udp', 'icmp', 'http_trace', 'tcp_trace', 'udp_trace', 'traceroute']
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'success': True}

        for test_type in valid_types:
            with patch('app.requests.post') as mock_post:
                mock_post.return_value = mock_resp
                resp = client.post(f'/api/test/{test_type}', json={'target': 'example.com'})
            # Should succeed (200) or fail with proper error, not 400 for invalid test type
            assert resp.status_code == 200 or resp.get_json().get('error') != 'Invalid test type'


class TestRunTestProxying:
    def test_successful_proxy_returns_200(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'latency_ms': 12.5, 'success': True}

        with patch('app.requests.post') as mock_post:
            mock_post.return_value = mock_resp
            resp = client.post('/api/test/http', json={'target': 'example.com'})

        assert resp.status_code == 200

    def test_testserver_error_propagates(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 503
        mock_resp.text = 'Service Unavailable'

        with patch('app.requests.post') as mock_post:
            mock_post.return_value = mock_resp
            resp = client.post('/api/test/http', json={'target': 'example.com'})

        assert resp.status_code == 503

    def test_connection_error_returns_503(self, client):
        with patch('app.requests.post') as mock_post:
            mock_post.side_effect = requests_lib.exceptions.ConnectionError('refused')
            resp = client.post('/api/test/http', json={'target': 'example.com'})

        assert resp.status_code == 503

    def test_timeout_error_returns_503(self, client):
        with patch('app.requests.post') as mock_post:
            mock_post.side_effect = requests_lib.exceptions.Timeout('timed out')
            resp = client.post('/api/test/http', json={'target': 'example.com'})

        assert resp.status_code == 503

    def test_proxy_sends_correct_url(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {}

        with patch('app.requests.post') as mock_post:
            mock_post.return_value = mock_resp
            client.post('/api/test/http', json={'target': 'example.com'})

        # Verify the request was made to the correct URL
        mock_post.assert_called()
        call_args = mock_post.call_args
        assert call_args is not None
        assert 'http://testserver.test/api/v1/test/http' == call_args[0][0]

    def test_proxy_includes_target_in_payload(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {}

        with patch('app.requests.post') as mock_post:
            mock_post.return_value = mock_resp
            client.post('/api/test/http', json={'target': 'myserver.com'})

        # Verify the request includes the target
        mock_post.assert_called()
        call_args = mock_post.call_args
        assert call_args is not None
        sent_json = call_args[1].get('json') if call_args[1] else {}
        assert sent_json.get('target') == 'myserver.com'

    def test_proxy_with_valid_port(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {}

        with patch('app.requests.post') as mock_post:
            mock_post.return_value = mock_resp
            resp = client.post('/api/test/tcp', json={'target': 'server.com', 'port': 8080})

        assert resp.status_code == 200

    def test_proxy_with_valid_count_and_timeout(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {}

        with patch('app.requests.post') as mock_post:
            mock_post.return_value = mock_resp
            resp = client.post('/api/test/icmp', json={
                'target': '8.8.8.8', 'count': 5, 'timeout': 10
            })

        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Input validation helpers directly
# ---------------------------------------------------------------------------

class TestValidateTestParams:
    def test_empty_target_fails(self):
        from app import validate_test_params
        ok, err = validate_test_params({'target': ''}, 'http')
        assert ok is False
        assert err is not None

    def test_valid_target_passes(self):
        from app import validate_test_params
        ok, err = validate_test_params({'target': 'example.com'}, 'http')
        assert ok is True
        assert err is None

    def test_port_out_of_range_fails(self):
        from app import validate_test_params
        ok, err = validate_test_params({'target': 'host', 'port': 0}, 'tcp')
        assert ok is False

    def test_port_65535_passes(self):
        from app import validate_test_params
        ok, err = validate_test_params({'target': 'host', 'port': 65535}, 'tcp')
        assert ok is True

    def test_timeout_300_passes(self):
        from app import validate_test_params
        ok, err = validate_test_params({'target': 'host', 'timeout': 300}, 'http')
        assert ok is True

    def test_timeout_zero_fails(self):
        from app import validate_test_params
        ok, err = validate_test_params({'target': 'host', 'timeout': 0}, 'http')
        assert ok is False

    def test_count_1000_passes(self):
        from app import validate_test_params
        ok, err = validate_test_params({'target': 'host', 'count': 1000}, 'icmp')
        assert ok is True

    def test_count_0_fails(self):
        from app import validate_test_params
        ok, err = validate_test_params({'target': 'host', 'count': 0}, 'icmp')
        assert ok is False

    def test_non_integer_port_fails(self):
        from app import validate_test_params
        ok, err = validate_test_params({'target': 'host', 'port': 'abc'}, 'tcp')
        assert ok is False

    def test_target_too_long_fails(self):
        from app import validate_test_params
        ok, err = validate_test_params({'target': 'x' * 256}, 'http')
        assert ok is False
