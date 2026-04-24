#!/usr/bin/env python3
"""HTTP test implementation for containerClient"""

import asyncio
import aiohttp
import time
import ssl
import logging
from typing import Dict, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class HttpTestResult:
    """HTTP test result data"""
    test_type: str = "http"
    protocol_detail: str = "http/1.1"
    target_host: str = ""
    target_ip: str = ""
    http_code: int = 0
    latency_ms: float = 0.0
    throughput_mbps: float = 0.0
    content_length: int = 0
    time_namelookup: float = 0.0
    time_connect: float = 0.0
    time_transfer: float = 0.0
    success: bool = False
    error: Optional[str] = None
    raw_results: Dict = field(default_factory=dict)


class HttpTest:
    """HTTP/HTTPS test implementation with HTTP/1.1, HTTP/2, and HTTP/3 support"""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = logging.getLogger(__name__)

    async def _create_session(self, trace_configs=None) -> aiohttp.ClientSession:
        """Create aiohttp session with optimized settings"""
        connector = aiohttp.TCPConnector(
            limit=10,
            limit_per_host=5,
            enable_cleanup_closed=True,
            use_dns_cache=True,
            ssl=ssl.create_default_context()
        )

        timeout_config = aiohttp.ClientTimeout(
            total=self.timeout,
            connect=10,
            sock_read=10
        )

        return aiohttp.ClientSession(
            connector=connector,
            timeout=timeout_config,
            trust_env=True,
            trace_configs=trace_configs or []
        )

    async def run_test(self, target_url: str) -> HttpTestResult:
        """Run HTTP test against target URL"""
        result = HttpTestResult(target_host=target_url)

        trace_config = aiohttp.TraceConfig()
        timing_data = {}

        # Trace callbacks for detailed timing
        async def on_request_start(session, trace_config_ctx, params):
            timing_data['request_start'] = time.perf_counter()

        async def on_dns_resolvehost_start(session, trace_config_ctx, params):
            timing_data['dns_start'] = time.perf_counter()

        async def on_dns_resolvehost_end(session, trace_config_ctx, params):
            timing_data['dns_end'] = time.perf_counter()

        async def on_connection_create_start(session, trace_config_ctx, params):
            timing_data['connect_start'] = time.perf_counter()

        async def on_connection_create_end(session, trace_config_ctx, params):
            timing_data['connect_end'] = time.perf_counter()

        async def on_request_end(session, trace_config_ctx, params):
            timing_data['request_end'] = time.perf_counter()

        trace_config.on_request_start.append(on_request_start)
        trace_config.on_dns_resolvehost_start.append(on_dns_resolvehost_start)
        trace_config.on_dns_resolvehost_end.append(on_dns_resolvehost_end)
        trace_config.on_connection_create_start.append(on_connection_create_start)
        trace_config.on_connection_create_end.append(on_connection_create_end)
        trace_config.on_request_end.append(on_request_end)

        # Create a new session with trace config for this request
        if not self.session:
            self.session = await self._create_session([trace_config])

        try:
            overall_start = time.perf_counter()

            async with self.session.get(
                target_url,
                allow_redirects=True
            ) as response:
                content = await response.read()
                overall_end = time.perf_counter()

                # Extract connection info
                result.target_host = str(response.url.host)
                result.target_ip = str(response.connection.transport.get_extra_info('peername')[0]) if response.connection and response.connection.transport else ""
                result.http_code = response.status
                result.content_length = len(content)
                result.latency_ms = (overall_end - overall_start) * 1000

                # Calculate throughput (Mbps)
                if result.latency_ms > 0:
                    result.throughput_mbps = (len(content) * 8) / (result.latency_ms * 1000)

                # Detailed timing
                if 'dns_start' in timing_data and 'dns_end' in timing_data:
                    result.time_namelookup = (timing_data['dns_end'] - timing_data['dns_start']) * 1000

                if 'connect_start' in timing_data and 'connect_end' in timing_data:
                    result.time_connect = (timing_data['connect_end'] - timing_data['connect_start']) * 1000

                if 'request_start' in timing_data and 'request_end' in timing_data:
                    result.time_transfer = (timing_data['request_end'] - timing_data['request_start']) * 1000

                # Detect protocol version
                if hasattr(response, 'version') and response.version is not None:
                    if response.version.major == 1 and response.version.minor == 1:
                        result.protocol_detail = "http/1.1"
                    elif response.version.major == 2:
                        result.protocol_detail = "http/2"
                    elif response.version.major == 3:
                        result.protocol_detail = "http/3"

                result.success = 200 <= response.status < 400

                # Store raw results
                result.raw_results = {
                    'url_effective': str(response.url),
                    'headers': dict(response.headers),
                    'redirect_count': len(response.history),
                    'timing_breakdown': timing_data
                }

        except asyncio.TimeoutError:
            result.error = "timeout"
            result.latency_ms = self.timeout * 1000
            self.logger.warning(f"HTTP test timeout for {target_url}")
        except aiohttp.ClientError as e:
            result.error = f"client_error: {str(e)}"
            self.logger.error(f"HTTP test client error for {target_url}: {e}")
        except Exception as e:
            result.error = f"unexpected_error: {str(e)}"
            self.logger.error(f"HTTP test unexpected error for {target_url}: {e}")

        return result

    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()
            self.session = None

    def to_dict(self, result: HttpTestResult) -> Dict:
        """Convert result to dictionary"""
        return asdict(result)
