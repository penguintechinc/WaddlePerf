"""Unit tests for HttpTest in containerClient/tests/http_test.py."""
import asyncio
import sys
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aioresponses import aioresponses

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tests.http_test import HttpTest, HttpTestResult


# ---------------------------------------------------------------------------
# HttpTestResult dataclass
# ---------------------------------------------------------------------------

class TestHttpTestResult:
    def test_default_values(self):
        r = HttpTestResult()
        assert r.test_type == 'http'
        assert r.success is False
        assert r.error is None
        assert r.latency_ms == 0.0

    def test_fields_assignable(self):
        r = HttpTestResult(
            target_host='example.com',
            http_code=200,
            latency_ms=25.0,
            success=True,
        )
        assert r.target_host == 'example.com'
        assert r.http_code == 200
        assert r.success is True

    def test_raw_results_is_dict(self):
        r = HttpTestResult()
        assert isinstance(r.raw_results, dict)


# ---------------------------------------------------------------------------
# HttpTest initialisation
# ---------------------------------------------------------------------------

class TestHttpTestInit:
    def test_default_timeout(self):
        ht = HttpTest()
        assert ht.timeout == 30

    def test_custom_timeout(self):
        ht = HttpTest(timeout=60)
        assert ht.timeout == 60

    def test_session_initially_none(self):
        ht = HttpTest()
        assert ht.session is None


# ---------------------------------------------------------------------------
# run_test — success cases
# ---------------------------------------------------------------------------

class TestHttpTestRunSuccess:
    async def test_run_test_sets_success_true_on_200(self):
        ht = HttpTest(timeout=5)
        with aioresponses() as m:
            m.get('http://example.com/', status=200, body=b'Hello')
            result = await ht.run_test('http://example.com/')
        assert result.success is True
        await ht.close()

    async def test_run_test_sets_http_code(self):
        ht = HttpTest(timeout=5)
        with aioresponses() as m:
            m.get('http://example.com/', status=200, body=b'OK')
            result = await ht.run_test('http://example.com/')
        assert result.http_code == 200
        await ht.close()

    async def test_run_test_sets_content_length(self):
        ht = HttpTest(timeout=5)
        body = b'Hello World'
        with aioresponses() as m:
            m.get('http://example.com/', status=200, body=body)
            result = await ht.run_test('http://example.com/')
        assert result.content_length == len(body)
        await ht.close()

    async def test_run_test_records_latency(self):
        ht = HttpTest(timeout=5)
        with aioresponses() as m:
            m.get('http://example.com/', status=200, body=b'')
            result = await ht.run_test('http://example.com/')
        assert result.latency_ms >= 0
        await ht.close()

    async def test_301_redirect_treated_as_success(self):
        ht = HttpTest(timeout=5)
        with aioresponses() as m:
            m.get('http://example.com/', status=301, body=b'Moved')
            result = await ht.run_test('http://example.com/')
        # 200 <= 301 < 400, so success=True
        assert result.success is True
        await ht.close()

    async def test_404_not_success(self):
        ht = HttpTest(timeout=5)
        with aioresponses() as m:
            m.get('http://example.com/', status=404, body=b'Not Found')
            result = await ht.run_test('http://example.com/')
        assert result.success is False
        await ht.close()

    async def test_result_has_no_error_on_success(self):
        ht = HttpTest(timeout=5)
        with aioresponses() as m:
            m.get('http://example.com/', status=200, body=b'')
            result = await ht.run_test('http://example.com/')
        assert result.error is None
        await ht.close()


# ---------------------------------------------------------------------------
# run_test — error cases
# ---------------------------------------------------------------------------

class TestHttpTestRunErrors:
    async def test_timeout_sets_error(self):
        import aiohttp
        ht = HttpTest(timeout=1)
        with aioresponses() as m:
            m.get('http://example.com/', exception=asyncio.TimeoutError())
            result = await ht.run_test('http://example.com/')
        assert result.error == 'timeout'
        assert result.success is False
        await ht.close()

    async def test_timeout_sets_latency_to_timeout_ms(self):
        ht = HttpTest(timeout=5)
        with aioresponses() as m:
            m.get('http://example.com/', exception=asyncio.TimeoutError())
            result = await ht.run_test('http://example.com/')
        assert result.latency_ms == 5000
        await ht.close()

    async def test_client_error_sets_error_field(self):
        import aiohttp
        ht = HttpTest(timeout=5)
        with aioresponses() as m:
            m.get('http://unreachable.local/',
                  exception=aiohttp.ClientError('connection refused'))
            result = await ht.run_test('http://unreachable.local/')
        assert result.error is not None
        assert 'client_error' in result.error
        assert result.success is False
        await ht.close()

    async def test_unexpected_exception_sets_error(self):
        ht = HttpTest(timeout=5)
        with aioresponses() as m:
            m.get('http://example.com/', exception=ValueError('bad'))
            result = await ht.run_test('http://example.com/')
        assert result.error is not None
        assert 'unexpected_error' in result.error
        await ht.close()

    async def test_target_host_set_even_on_error(self):
        import aiohttp
        ht = HttpTest(timeout=5)
        with aioresponses() as m:
            m.get('http://example.com/',
                  exception=aiohttp.ClientError('conn refused'))
            result = await ht.run_test('http://example.com/')
        assert result.target_host == 'http://example.com/'
        await ht.close()


# ---------------------------------------------------------------------------
# to_dict
# ---------------------------------------------------------------------------

class TestHttpTestToDict:
    def test_to_dict_returns_dict(self):
        ht = HttpTest()
        result = HttpTestResult(target_host='example.com', success=True)
        d = ht.to_dict(result)
        assert isinstance(d, dict)

    def test_to_dict_includes_all_fields(self):
        ht = HttpTest()
        result = HttpTestResult()
        d = ht.to_dict(result)
        for field in ('test_type', 'success', 'latency_ms', 'target_host', 'error'):
            assert field in d


# ---------------------------------------------------------------------------
# close
# ---------------------------------------------------------------------------

class TestHttpTestClose:
    async def test_close_clears_session(self):
        ht = HttpTest(timeout=5)
        with aioresponses() as m:
            m.get('http://example.com/', status=200, body=b'')
            await ht.run_test('http://example.com/')
        await ht.close()
        assert ht.session is None

    async def test_close_with_no_session_does_not_raise(self):
        ht = HttpTest()
        await ht.close()  # Should not raise


# ---------------------------------------------------------------------------
# Additional coverage: session reuse, throughput, protocol detection
# ---------------------------------------------------------------------------

class TestHttpTestSessionReuse:
    async def test_session_created_on_first_run(self):
        ht = HttpTest(timeout=5)
        assert ht.session is None
        with aioresponses() as m:
            m.get('http://example.com/', status=200, body=b'')
            await ht.run_test('http://example.com/')
        assert ht.session is not None
        await ht.close()

    async def test_run_test_https_target(self):
        ht = HttpTest(timeout=5)
        with aioresponses() as m:
            m.get('https://secure.example.com/', status=200, body=b'Secure')
            result = await ht.run_test('https://secure.example.com/')
        # Check it ran without exception and returned a result
        assert isinstance(result, HttpTestResult)
        await ht.close()

    async def test_server_error_500_not_success(self):
        ht = HttpTest(timeout=5)
        with aioresponses() as m:
            m.get('http://example.com/', status=500, body=b'Internal Server Error')
            result = await ht.run_test('http://example.com/')
        assert result.success is False
        assert result.http_code == 500
        await ht.close()

    async def test_throughput_calculated_correctly(self):
        ht = HttpTest(timeout=5)
        # 1000 bytes body
        body = b'x' * 1000
        with aioresponses() as m:
            m.get('http://example.com/', status=200, body=body)
            result = await ht.run_test('http://example.com/')
        # throughput = (bytes * 8) / (latency_ms * 1000)
        if result.latency_ms > 0:
            expected = (1000 * 8) / (result.latency_ms * 1000)
            assert abs(result.throughput_mbps - expected) < 0.001
        await ht.close()

    async def test_empty_body_no_throughput_error(self):
        ht = HttpTest(timeout=5)
        with aioresponses() as m:
            m.get('http://example.com/', status=200, body=b'')
            result = await ht.run_test('http://example.com/')
        assert result.throughput_mbps >= 0.0
        await ht.close()

    async def test_run_test_returns_correct_type(self):
        ht = HttpTest(timeout=5)
        with aioresponses() as m:
            m.get('http://example.com/', status=200, body=b'')
            result = await ht.run_test('http://example.com/')
        assert isinstance(result, HttpTestResult)
        await ht.close()

    async def test_create_session_returns_session(self):
        ht = HttpTest(timeout=5)
        session = await ht._create_session()
        assert session is not None
        await session.close()

    async def test_result_raw_results_dict_on_success(self):
        ht = HttpTest(timeout=5)
        with aioresponses() as m:
            m.get('http://example.com/', status=200, body=b'ok')
            result = await ht.run_test('http://example.com/')
        assert isinstance(result.raw_results, dict)
        await ht.close()
