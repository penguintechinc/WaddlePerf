"""Unit tests for TcpTest in containerClient/tests/tcp_test.py."""
import asyncio
import ssl
import sys
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tests.tcp_test import TcpTest, TcpTestResult


# ---------------------------------------------------------------------------
# TcpTestResult dataclass
# ---------------------------------------------------------------------------

class TestTcpTestResult:
    def test_default_values(self):
        r = TcpTestResult()
        assert r.test_type == 'tcp'
        assert r.success is False
        assert r.error is None
        assert r.latency_ms == 0.0

    def test_fields_assignable(self):
        r = TcpTestResult(target_host='host', target_port=443, success=True)
        assert r.target_host == 'host'
        assert r.target_port == 443
        assert r.success is True

    def test_raw_results_default_dict(self):
        assert isinstance(TcpTestResult().raw_results, dict)


# ---------------------------------------------------------------------------
# TcpTest init
# ---------------------------------------------------------------------------

class TestTcpTestInit:
    def test_default_timeout(self):
        t = TcpTest()
        assert t.timeout == 10

    def test_custom_timeout(self):
        t = TcpTest(timeout=30)
        assert t.timeout == 30


# ---------------------------------------------------------------------------
# _resolve_host
# ---------------------------------------------------------------------------

class TestResolveHost:
    async def test_resolve_returns_ip(self):
        t = TcpTest()
        with patch('asyncio.get_event_loop') as mock_loop_factory:
            mock_loop = AsyncMock()
            mock_loop_factory.return_value = mock_loop
            mock_loop.getaddrinfo.return_value = [
                (None, None, None, None, ('1.2.3.4', 0))
            ]
            ip = await t._resolve_host('example.com')
        assert ip == '1.2.3.4'

    async def test_resolve_returns_none_on_failure(self):
        t = TcpTest()
        with patch('asyncio.get_event_loop') as mock_loop_factory:
            mock_loop = AsyncMock()
            mock_loop_factory.return_value = mock_loop
            mock_loop.getaddrinfo.side_effect = Exception('DNS failure')
            ip = await t._resolve_host('invalid.host.xyz')
        assert ip is None


# ---------------------------------------------------------------------------
# _test_raw_tcp
# ---------------------------------------------------------------------------

class TestRawTCP:
    async def test_success_sets_success_true(self):
        t = TcpTest(timeout=5)
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_writer.wait_closed = AsyncMock()

        with patch('asyncio.wait_for', return_value=(mock_reader, mock_writer)), \
             patch.object(t, '_resolve_host', return_value='1.2.3.4'):
            result = await t._test_raw_tcp('example.com', 80)

        assert result.success is True
        assert result.target_host == 'example.com'
        assert result.target_port == 80

    async def test_success_records_latency(self):
        t = TcpTest(timeout=5)
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_writer.wait_closed = AsyncMock()

        with patch('asyncio.wait_for', return_value=(mock_reader, mock_writer)), \
             patch.object(t, '_resolve_host', return_value='1.2.3.4'):
            result = await t._test_raw_tcp('example.com', 80)

        assert result.latency_ms >= 0

    async def test_connection_refused_sets_error(self):
        t = TcpTest(timeout=5)
        with patch('asyncio.wait_for', side_effect=ConnectionRefusedError()), \
             patch.object(t, '_resolve_host', return_value='1.2.3.4'):
            result = await t._test_raw_tcp('example.com', 9999)

        assert result.error == 'connection_refused'
        assert result.success is False

    async def test_timeout_sets_error(self):
        t = TcpTest(timeout=1)
        with patch('asyncio.wait_for', side_effect=asyncio.TimeoutError()), \
             patch.object(t, '_resolve_host', return_value='1.2.3.4'):
            result = await t._test_raw_tcp('example.com', 80)

        assert result.error == 'timeout'
        assert result.latency_ms == 1000

    async def test_unexpected_error_sets_error_field(self):
        t = TcpTest(timeout=5)
        with patch('asyncio.wait_for', side_effect=OSError('network unreachable')), \
             patch.object(t, '_resolve_host', return_value='1.2.3.4'):
            result = await t._test_raw_tcp('host.local', 80)

        assert result.error is not None
        assert result.success is False


# ---------------------------------------------------------------------------
# _test_tcp_tls
# ---------------------------------------------------------------------------

class TestTcpTLS:
    async def test_tls_success(self):
        t = TcpTest(timeout=5)
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_writer.wait_closed = AsyncMock()
        mock_writer.get_extra_info = MagicMock(return_value=None)

        with patch('asyncio.wait_for', return_value=(mock_reader, mock_writer)), \
             patch.object(t, '_resolve_host', return_value='1.2.3.4'):
            result = await t._test_tcp_tls('example.com', 443)

        assert result.success is True
        assert result.protocol_detail == 'tcp_tls'

    async def test_tls_ssl_error_captured(self):
        t = TcpTest(timeout=5)
        with patch('asyncio.wait_for', side_effect=ssl.SSLError('cert verify failed')), \
             patch.object(t, '_resolve_host', return_value='1.2.3.4'):
            result = await t._test_tcp_tls('example.com', 443)

        assert 'ssl_error' in result.error
        assert result.success is False

    async def test_tls_timeout_sets_error(self):
        t = TcpTest(timeout=2)
        with patch('asyncio.wait_for', side_effect=asyncio.TimeoutError()), \
             patch.object(t, '_resolve_host', return_value='1.2.3.4'):
            result = await t._test_tcp_tls('example.com', 443)

        assert result.error == 'timeout'

    async def test_tls_connection_refused(self):
        t = TcpTest(timeout=5)
        with patch('asyncio.wait_for', side_effect=ConnectionRefusedError()), \
             patch.object(t, '_resolve_host', return_value='1.2.3.4'):
            result = await t._test_tcp_tls('example.com', 443)

        assert result.error == 'connection_refused'


# ---------------------------------------------------------------------------
# _test_ssh
# ---------------------------------------------------------------------------

class TestSSH:
    async def test_ssh_success_reads_banner(self):
        t = TcpTest(timeout=5)
        mock_reader = AsyncMock()
        mock_reader.readline = AsyncMock(return_value=b'SSH-2.0-OpenSSH_8.9\r\n')
        mock_writer = AsyncMock()
        mock_writer.wait_closed = AsyncMock()

        with patch('asyncio.wait_for', side_effect=[
            (mock_reader, mock_writer),  # open_connection
            b'SSH-2.0-OpenSSH_8.9\r\n',  # readline
        ]), patch.object(t, '_resolve_host', return_value='1.2.3.4'):
            result = await t._test_ssh('ssh.example.com', 22)

        assert result.protocol_detail == 'ssh'

    async def test_ssh_timeout(self):
        t = TcpTest(timeout=2)
        with patch('asyncio.wait_for', side_effect=asyncio.TimeoutError()), \
             patch.object(t, '_resolve_host', return_value='1.2.3.4'):
            result = await t._test_ssh('ssh.example.com', 22)
        assert result.error == 'timeout'

    async def test_ssh_connection_refused(self):
        t = TcpTest(timeout=5)
        with patch('asyncio.wait_for', side_effect=ConnectionRefusedError()), \
             patch.object(t, '_resolve_host', return_value='1.2.3.4'):
            result = await t._test_ssh('ssh.example.com', 22)
        assert result.error == 'connection_refused'


# ---------------------------------------------------------------------------
# run_test — routing logic
# ---------------------------------------------------------------------------

class TestRunTestRouting:
    async def test_run_test_parses_host_port(self):
        t = TcpTest(timeout=5)
        with patch.object(t, '_test_raw_tcp', new_callable=AsyncMock) as mock_raw:
            mock_raw.return_value = TcpTestResult(success=True)
            await t.run_test('myhost:8080')
        mock_raw.assert_called_once_with('myhost', 8080)

    async def test_run_test_ssh_protocol(self):
        t = TcpTest(timeout=5)
        with patch.object(t, '_test_ssh', new_callable=AsyncMock) as mock_ssh:
            mock_ssh.return_value = TcpTestResult(success=True)
            await t.run_test('myhost:22', protocol='ssh')
        mock_ssh.assert_called_once_with('myhost', 22)

    async def test_run_test_tls_protocol(self):
        t = TcpTest(timeout=5)
        with patch.object(t, '_test_tcp_tls', new_callable=AsyncMock) as mock_tls:
            mock_tls.return_value = TcpTestResult(success=True)
            await t.run_test('myhost:443', protocol='tcp_tls')
        mock_tls.assert_called_once_with('myhost', 443)

    async def test_run_test_default_port_raw_tcp(self):
        t = TcpTest(timeout=5)
        with patch.object(t, '_test_raw_tcp', new_callable=AsyncMock) as mock_raw:
            mock_raw.return_value = TcpTestResult()
            await t.run_test('myhost')
        mock_raw.assert_called_once_with('myhost', 80)

    async def test_run_test_default_port_ssh(self):
        t = TcpTest(timeout=5)
        with patch.object(t, '_test_ssh', new_callable=AsyncMock) as mock_ssh:
            mock_ssh.return_value = TcpTestResult()
            await t.run_test('myhost', protocol='ssh')
        mock_ssh.assert_called_once_with('myhost', 22)


# ---------------------------------------------------------------------------
# to_dict
# ---------------------------------------------------------------------------

class TestTcpToDict:
    def test_to_dict_returns_dict(self):
        t = TcpTest()
        d = t.to_dict(TcpTestResult())
        assert isinstance(d, dict)

    def test_to_dict_includes_required_fields(self):
        t = TcpTest()
        d = t.to_dict(TcpTestResult(target_host='host', target_port=80))
        assert 'test_type' in d
        assert 'success' in d
        assert 'latency_ms' in d

    def test_to_dict_preserves_all_values(self):
        t = TcpTest()
        r = TcpTestResult(
            target_host='myhost', target_port=443,
            latency_ms=5.5, success=True, protocol_detail='tcp_tls'
        )
        d = t.to_dict(r)
        assert d['target_host'] == 'myhost'
        assert d['target_port'] == 443
        assert d['success'] is True
        assert d['protocol_detail'] == 'tcp_tls'

    def test_to_dict_includes_raw_results(self):
        t = TcpTest()
        d = t.to_dict(TcpTestResult())
        assert 'raw_results' in d


# ---------------------------------------------------------------------------
# Additional coverage: connection_time_ms, raw_results content
# ---------------------------------------------------------------------------

class TestTcpRawResults:
    async def test_raw_tcp_success_includes_connect_time(self):
        t = TcpTest(timeout=5)
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_writer.wait_closed = AsyncMock()

        with patch('asyncio.wait_for', return_value=(mock_reader, mock_writer)), \
             patch.object(t, '_resolve_host', return_value='1.2.3.4'):
            result = await t._test_raw_tcp('host', 80)

        assert result.raw_results.get('connection_established') is True
        assert 'connect_time_ms' in result.raw_results

    async def test_tls_raw_results_has_tls_version(self):
        t = TcpTest(timeout=5)
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_writer.wait_closed = AsyncMock()
        mock_ssl_obj = MagicMock()
        mock_ssl_obj.version.return_value = 'TLSv1.3'
        mock_ssl_obj.cipher.return_value = ('AES256', 'TLSv1.3', 256)
        mock_writer.get_extra_info = MagicMock(return_value=mock_ssl_obj)

        with patch('asyncio.wait_for', return_value=(mock_reader, mock_writer)), \
             patch.object(t, '_resolve_host', return_value='1.2.3.4'):
            result = await t._test_tcp_tls('host', 443)

        assert result.raw_results.get('connection_established') is True

    async def test_run_test_default_port_tls(self):
        t = TcpTest(timeout=5)
        with patch.object(t, '_test_tcp_tls', new_callable=AsyncMock) as mock_tls:
            mock_tls.return_value = TcpTestResult()
            await t.run_test('host', protocol='tcp_tls')
        mock_tls.assert_called_once_with('host', 443)

    async def test_resolve_host_called_in_raw_tcp(self):
        t = TcpTest(timeout=5)
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_writer.wait_closed = AsyncMock()

        with patch('asyncio.wait_for', return_value=(mock_reader, mock_writer)), \
             patch.object(t, '_resolve_host', new_callable=AsyncMock,
                          return_value='1.2.3.4') as mock_resolve:
            await t._test_raw_tcp('example.com', 80)
        mock_resolve.assert_called_once_with('example.com')

    async def test_connection_time_equals_latency_on_raw_tcp(self):
        t = TcpTest(timeout=5)
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_writer.wait_closed = AsyncMock()

        with patch('asyncio.wait_for', return_value=(mock_reader, mock_writer)), \
             patch.object(t, '_resolve_host', return_value='1.2.3.4'):
            result = await t._test_raw_tcp('host', 80)

        assert result.connection_time_ms == result.latency_ms

    async def test_ssh_success_has_banner_in_raw_results(self):
        t = TcpTest(timeout=5)
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_writer.wait_closed = AsyncMock()
        banner = b'SSH-2.0-OpenSSH_8.9\r\n'

        async def fake_wait_for(coro_or_fut, timeout):
            # First call: open_connection returns (reader, writer)
            # Second call: reader.readline returns banner
            if hasattr(coro_or_fut, '__await__') or asyncio.iscoroutine(coro_or_fut):
                try:
                    return await coro_or_fut
                except Exception:
                    return (mock_reader, mock_writer)
            return (mock_reader, mock_writer)

        mock_reader.readline = AsyncMock(return_value=banner)

        with patch('asyncio.wait_for', side_effect=[
            (mock_reader, mock_writer),
            banner,
        ]), patch.object(t, '_resolve_host', return_value='1.2.3.4'):
            result = await t._test_ssh('ssh.host.com', 22)

        assert result.success is True
        assert 'ssh_banner' in result.raw_results
