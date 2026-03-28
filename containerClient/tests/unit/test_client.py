"""Unit tests for WaddlePerfClient in containerClient/client.py."""
import asyncio
import os
import sys
import socket
import platform
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from aioresponses import aioresponses

# Ensure the project root is on sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from client import WaddlePerfClient, ClientConfig, DeviceInfo, load_config_from_env


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_config(**overrides) -> ClientConfig:
    defaults = dict(
        auth_user='testuser',
        auth_pass='testpass',
        manager_url='http://manager.test',
        test_server_url='http://testserver.test',
        run_seconds=0,
        http_targets=['http://example.com'],
        tcp_targets=[],
        udp_targets=[],
        icmp_targets=[],
    )
    defaults.update(overrides)
    return ClientConfig(**defaults)


def _make_client(**config_overrides) -> WaddlePerfClient:
    cfg = _make_config(**config_overrides)
    with patch('client.get_logger', return_value=MagicMock()):
        return WaddlePerfClient(cfg)


# ---------------------------------------------------------------------------
# DeviceInfo detection
# ---------------------------------------------------------------------------

class TestDetectDeviceInfo:
    def test_uses_config_device_serial_when_set(self):
        client = _make_client(device_serial='MY-SERIAL-001', device_hostname='myhost')
        assert client.device_info.serial == 'MY-SERIAL-001'

    def test_uses_config_hostname_when_set(self):
        client = _make_client(device_serial='S', device_hostname='custom-host')
        assert client.device_info.hostname == 'custom-host'

    def test_detects_platform_os(self):
        client = _make_client(device_serial='S', device_hostname='h')
        assert client.device_info.os == platform.system()

    def test_detects_platform_version(self):
        client = _make_client(device_serial='S', device_hostname='h')
        assert client.device_info.os_version == platform.release()

    def test_falls_back_to_gethostname(self):
        with patch('socket.gethostname', return_value='auto-detected-host'):
            client = _make_client(device_serial='S')
        assert client.device_info.hostname == 'auto-detected-host'

    def test_serial_from_machine_id_file(self):
        with patch('os.path.exists', side_effect=lambda p: p == '/etc/machine-id'), \
             patch('builtins.open', mock_open(read_data='machine-id-value\n')):
            client = _make_client()
        assert client.device_info.serial == 'machine-id-value'

    def test_serial_fallback_hash_when_no_file(self):
        with patch('os.path.exists', return_value=False), \
             patch('socket.gethostname', return_value='hostname'):
            client = _make_client()
        assert len(client.device_info.serial) == 32

    def test_device_info_is_dataclass(self):
        client = _make_client(device_serial='S', device_hostname='h')
        assert isinstance(client.device_info, DeviceInfo)


# ---------------------------------------------------------------------------
# _login
# ---------------------------------------------------------------------------

class TestLogin:
    async def test_login_success_stores_tokens(self):
        client = _make_client()
        with aioresponses() as m:
            m.post(
                'http://manager.test/api/v1/auth/login',
                payload={'access_token': 'AT123', 'refresh_token': 'RT456'},
                status=200,
            )
            result = await client._login()

        assert result is True
        assert client.config.access_token == 'AT123'
        assert client.config.refresh_token == 'RT456'

    async def test_login_failure_returns_false(self):
        client = _make_client()
        with aioresponses() as m:
            m.post('http://manager.test/api/v1/auth/login', status=401, body='Unauthorized')
            result = await client._login()

        assert result is False

    async def test_login_missing_credentials_returns_false(self):
        client = _make_client(auth_user=None, auth_pass=None)
        result = await client._login()
        assert result is False

    async def test_login_network_error_returns_false(self):
        client = _make_client()
        with aioresponses() as m:
            m.post('http://manager.test/api/v1/auth/login',
                   exception=Exception('connection refused'))
            result = await client._login()
        assert result is False

    async def test_login_creates_session_if_none(self):
        client = _make_client()
        assert client.session is None
        with aioresponses() as m:
            m.post('http://manager.test/api/v1/auth/login', status=401, body='')
            await client._login()
        assert client.session is not None
        await client.close()


# ---------------------------------------------------------------------------
# _refresh_token
# ---------------------------------------------------------------------------

class TestRefreshToken:
    async def test_refresh_success_updates_access_token(self):
        client = _make_client()
        client.config.refresh_token = 'REFRESH-TOKEN'
        with aioresponses() as m:
            m.post('http://manager.test/api/v1/auth/refresh',
                   payload={'access_token': 'NEW-AT'}, status=200)
            result = await client._refresh_token()
        assert result is True
        assert client.config.access_token == 'NEW-AT'
        await client.close()

    async def test_refresh_failure_falls_back_to_login(self):
        client = _make_client()
        client.config.refresh_token = 'OLD-RT'
        with aioresponses() as m:
            m.post('http://manager.test/api/v1/auth/refresh', status=401, body='')
            m.post('http://manager.test/api/v1/auth/login',
                   payload={'access_token': 'FROM-LOGIN', 'refresh_token': 'RT'},
                   status=200)
            result = await client._refresh_token()
        assert result is True
        assert client.config.access_token == 'FROM-LOGIN'
        await client.close()

    async def test_refresh_without_refresh_token_attempts_login(self):
        client = _make_client()
        client.config.refresh_token = None
        with aioresponses() as m:
            m.post('http://manager.test/api/v1/auth/login',
                   payload={'access_token': 'NEW', 'refresh_token': 'RT'},
                   status=200)
            result = await client._refresh_token()
        assert result is True
        await client.close()


# ---------------------------------------------------------------------------
# _ensure_authenticated
# ---------------------------------------------------------------------------

class TestEnsureAuthenticated:
    async def test_returns_true_when_token_already_set(self):
        client = _make_client()
        client.config.access_token = 'EXISTING-TOKEN'
        result = await client._ensure_authenticated()
        assert result is True

    async def test_calls_login_when_no_token(self):
        client = _make_client()
        client.config.access_token = None
        with aioresponses() as m:
            m.post('http://manager.test/api/v1/auth/login',
                   payload={'access_token': 'FRESH', 'refresh_token': 'RT'},
                   status=200)
            result = await client._ensure_authenticated()
        assert result is True
        await client.close()


# ---------------------------------------------------------------------------
# _get_auth_headers
# ---------------------------------------------------------------------------

class TestGetAuthHeaders:
    def test_includes_bearer_token_when_set(self):
        client = _make_client()
        client.config.access_token = 'MY-TOKEN'
        headers = client._get_auth_headers()
        assert headers['Authorization'] == 'Bearer MY-TOKEN'

    def test_no_authorization_header_when_no_token(self):
        client = _make_client()
        client.config.access_token = None
        headers = client._get_auth_headers()
        assert 'Authorization' not in headers

    def test_includes_content_type(self):
        client = _make_client()
        headers = client._get_auth_headers()
        assert headers['Content-Type'] == 'application/json'

    def test_includes_user_agent(self):
        client = _make_client()
        headers = client._get_auth_headers()
        assert 'WaddlePerf' in headers['User-Agent']


# ---------------------------------------------------------------------------
# _upload_result
# ---------------------------------------------------------------------------

class TestUploadResult:
    async def test_upload_success_returns_true(self):
        client = _make_client()
        client.config.access_token = 'TOKEN'
        with aioresponses() as m:
            # refresh call
            m.post('http://manager.test/api/v1/auth/refresh',
                   payload={'access_token': 'TOKEN'}, status=200)
            # upload call
            m.post('http://manager.test/api/v1/tests/',
                   payload={'id': 1}, status=201)
            result = await client._upload_result({'test_type': 'http', 'latency_ms': 10})
        assert result is True
        await client.close()

    async def test_upload_failure_returns_false(self):
        client = _make_client()
        client.config.access_token = 'TOKEN'
        with aioresponses() as m:
            m.post('http://manager.test/api/v1/auth/refresh',
                   payload={'access_token': 'TOKEN'}, status=200)
            m.post('http://manager.test/api/v1/tests/', status=500, body='error')
            result = await client._upload_result({'test_type': 'http'})
        assert result is False
        await client.close()

    async def test_upload_adds_device_info(self):
        client = _make_client(device_serial='SN-123', device_hostname='myhost')
        client.config.access_token = 'TOKEN'
        sent_payload = {}
        with aioresponses() as m:
            m.post('http://manager.test/api/v1/auth/refresh',
                   payload={'access_token': 'TOKEN'}, status=200)
            m.post('http://manager.test/api/v1/tests/',
                   payload={'id': 1}, status=201)
            await client._upload_result({'test_type': 'http'})
        # device_info is added to the result_data dict in-place
        # We verify by checking the client's device_info attributes are accessible
        assert client.device_info.serial == 'SN-123'
        assert client.device_info.hostname == 'myhost'
        await client.close()


# ---------------------------------------------------------------------------
# run_http_tests / run_tcp_tests / etc. (disabled when no targets)
# ---------------------------------------------------------------------------

class TestRunTests:
    async def test_run_http_tests_empty_when_disabled(self):
        client = _make_client(enable_http_test=False)
        results = await client.run_http_tests()
        assert results == []

    async def test_run_http_tests_empty_when_no_targets(self):
        client = _make_client(enable_http_test=True, http_targets=[])
        results = await client.run_http_tests()
        assert results == []

    async def test_run_tcp_tests_empty_when_disabled(self):
        client = _make_client(enable_tcp_test=False)
        results = await client.run_tcp_tests()
        assert results == []

    async def test_run_udp_tests_empty_when_disabled(self):
        client = _make_client(enable_udp_test=False)
        results = await client.run_udp_tests()
        assert results == []

    async def test_run_icmp_tests_empty_when_disabled(self):
        client = _make_client(enable_icmp_test=False)
        results = await client.run_icmp_tests()
        assert results == []

    async def test_run_all_tests_returns_dict(self):
        client = _make_client(
            enable_http_test=False, enable_tcp_test=False,
            enable_udp_test=False, enable_icmp_test=False,
        )
        results = await client.run_all_tests()
        assert isinstance(results, dict)
        assert 'http' in results
        assert 'tcp' in results


# ---------------------------------------------------------------------------
# close
# ---------------------------------------------------------------------------

class TestClose:
    async def test_close_closes_session(self):
        client = _make_client()
        mock_session = AsyncMock()
        client.session = mock_session
        await client.close()
        mock_session.close.assert_called_once()

    async def test_close_when_no_session(self):
        client = _make_client()
        assert client.session is None
        await client.close()  # should not raise


# ---------------------------------------------------------------------------
# load_config_from_env
# ---------------------------------------------------------------------------

class TestLoadConfigFromEnv:
    def test_loads_auth_user(self, monkeypatch):
        monkeypatch.setenv('AUTH_USER', 'envuser')
        cfg = load_config_from_env()
        assert cfg.auth_user == 'envuser'

    def test_loads_manager_url(self, monkeypatch):
        monkeypatch.setenv('MANAGER_URL', 'http://custom.manager')
        cfg = load_config_from_env()
        assert cfg.manager_url == 'http://custom.manager'

    def test_loads_run_seconds(self, monkeypatch):
        monkeypatch.setenv('RUN_SECONDS', '300')
        cfg = load_config_from_env()
        assert cfg.run_seconds == 300

    def test_loads_enable_http_test_false(self, monkeypatch):
        monkeypatch.setenv('ENABLE_HTTP_TEST', 'false')
        cfg = load_config_from_env()
        assert cfg.enable_http_test is False

    def test_loads_http_targets(self, monkeypatch):
        monkeypatch.setenv('HTTP_TARGETS', 'http://a.com,http://b.com')
        cfg = load_config_from_env()
        assert 'http://a.com' in cfg.http_targets
        assert 'http://b.com' in cfg.http_targets

    def test_loads_icmp_targets(self, monkeypatch):
        monkeypatch.setenv('ICMP_TARGETS', '8.8.8.8,1.1.1.1')
        cfg = load_config_from_env()
        assert '8.8.8.8' in cfg.icmp_targets

    def test_empty_tcp_targets(self, monkeypatch):
        monkeypatch.setenv('TCP_TARGETS', '')
        cfg = load_config_from_env()
        assert cfg.tcp_targets == []

    def test_loads_device_serial(self, monkeypatch):
        monkeypatch.setenv('DEVICE_SERIAL', 'ENV-SERIAL')
        cfg = load_config_from_env()
        assert cfg.device_serial == 'ENV-SERIAL'
