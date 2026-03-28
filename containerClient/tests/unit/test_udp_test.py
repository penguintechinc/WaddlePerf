"""Unit tests for UdpTest in containerClient/tests/udp_test.py."""
import asyncio
import sys
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tests.udp_test import UdpTest, UdpTestResult


# ---------------------------------------------------------------------------
# UdpTestResult dataclass
# ---------------------------------------------------------------------------

class TestUdpTestResult:
    def test_default_values(self):
        r = UdpTestResult()
        assert r.test_type == 'udp'
        assert r.success is False
        assert r.error is None
        assert r.latency_ms == 0.0
        assert r.jitter_ms == 0.0
        assert r.packet_loss_percent == 0.0
        assert r.packets_sent == 0
        assert r.packets_received == 0

    def test_fields_assignable(self):
        r = UdpTestResult(
            target_host='example.com',
            target_port=53,
            latency_ms=10.0,
            jitter_ms=2.0,
            packet_loss_percent=0.0,
            packets_sent=4,
            packets_received=4,
            success=True,
        )
        assert r.target_host == 'example.com'
        assert r.target_port == 53
        assert r.success is True
        assert r.packets_sent == 4


# ---------------------------------------------------------------------------
# UdpTest initialization
# ---------------------------------------------------------------------------

class TestUdpTestInit:
    def test_default_timeout(self):
        ut = UdpTest()
        assert ut.timeout == 5

    def test_custom_timeout(self):
        ut = UdpTest(timeout=10)
        assert ut.timeout == 10

    def test_default_packet_count(self):
        ut = UdpTest()
        assert ut.packet_count == 4

    def test_custom_packet_count(self):
        ut = UdpTest(packet_count=8)
        assert ut.packet_count == 8

    def test_packet_size(self):
        ut = UdpTest()
        assert ut.packet_size == 64


# ---------------------------------------------------------------------------
# _resolve_host
# ---------------------------------------------------------------------------

class TestResolveHost:
    async def test_resolve_host_returns_ip(self):
        ut = UdpTest()
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_loop_obj = MagicMock()
            mock_loop.return_value = mock_loop_obj
            mock_loop_obj.getaddrinfo = AsyncMock(return_value=[
                (10, 1, 17, '', ('192.0.2.1', 53))
            ])
            result = await ut._resolve_host('example.com')
        assert result == '192.0.2.1'

    async def test_resolve_host_handles_error(self):
        ut = UdpTest()
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_loop_obj = MagicMock()
            mock_loop.return_value = mock_loop_obj
            mock_loop_obj.getaddrinfo = AsyncMock(side_effect=Exception("DNS error"))
            result = await ut._resolve_host('invalid.example')
        assert result is None

    async def test_resolve_host_empty_result(self):
        ut = UdpTest()
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_loop_obj = MagicMock()
            mock_loop.return_value = mock_loop_obj
            mock_loop_obj.getaddrinfo = AsyncMock(return_value=[])
            result = await ut._resolve_host('example.com')
        assert result is None


# ---------------------------------------------------------------------------
# Basic run_test
# ---------------------------------------------------------------------------

class TestUdpTestRun:
    async def test_run_test_raw_udp_success(self):
        ut = UdpTest(timeout=1, packet_count=2)
        with patch.object(ut, '_test_raw_udp', new_callable=AsyncMock) as mock_raw:
            mock_result = UdpTestResult(
                target_host='example.com',
                target_port=5000,
                success=True,
                packets_sent=2,
                packets_received=2,
            )
            mock_raw.return_value = mock_result
            result = await ut.run_test('example.com:5000', protocol='raw_udp')
        assert result.success is True

    async def test_run_test_dns_lookup(self):
        ut = UdpTest(timeout=1)
        with patch.object(ut, '_test_dns', new_callable=AsyncMock) as mock_dns:
            mock_result = UdpTestResult(
                target_host='example.com',
                target_port=53,
                success=True,
            )
            mock_dns.return_value = mock_result
            result = await ut.run_test('example.com', protocol='dns')
        assert result.success is True

    async def test_run_test_raw_udp_default_port(self):
        ut = UdpTest(timeout=1)
        with patch.object(ut, '_test_raw_udp', new_callable=AsyncMock) as mock_raw:
            mock_result = UdpTestResult(success=False)
            mock_raw.return_value = mock_result
            result = await ut.run_test('192.0.2.1')
        mock_raw.assert_called_with('192.0.2.1', 2000)


# ---------------------------------------------------------------------------
# To Dict
# ---------------------------------------------------------------------------

class TestUdpTestToDict:
    def test_to_dict_returns_dict(self):
        ut = UdpTest()
        result = UdpTestResult(success=True, latency_ms=5.0)
        d = ut.to_dict(result)
        assert isinstance(d, dict)

    def test_to_dict_includes_all_fields(self):
        ut = UdpTest()
        result = UdpTestResult(
            target_host='example.com',
            target_port=53,
            success=True,
            packets_sent=4,
        )
        d = ut.to_dict(result)
        assert d['target_host'] == 'example.com'
        assert d['target_port'] == 53
        assert d['success'] is True
        assert d['packets_sent'] == 4
