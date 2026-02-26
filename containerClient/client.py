#!/usr/bin/env python3
"""
WaddlePerf containerClient - Python 3.13 network performance testing client
Implements HTTP, TCP, UDP, and ICMP tests with multi-threading support
"""

import asyncio
import logging
import os
import sys
import argparse
import time
import platform
import socket
import json
from datetime import datetime
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, asdict
import aiohttp
from penguintechinc_utils.logging import get_logger

from tests import (
    HttpTest, HttpTestResult,
    TcpTest, TcpTestResult,
    UdpTest, UdpTestResult,
    IcmpTest, IcmpTestResult
)


@dataclass
class DeviceInfo:
    """Device information"""
    serial: str
    hostname: str
    os: str
    os_version: str


@dataclass
class ClientConfig:
    """Client configuration from environment variables"""
    auth_type: str = "userpass"
    auth_user: Optional[str] = None
    auth_pass: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    manager_url: str = "https://waddleperf.penguintech.io"
    test_server_url: str = "http://localhost:8081"
    run_seconds: int = 0
    enable_http_test: bool = True
    enable_tcp_test: bool = True
    enable_udp_test: bool = True
    enable_icmp_test: bool = True
    device_serial: Optional[str] = None
    device_hostname: Optional[str] = None
    http_targets: List[str] = None
    tcp_targets: List[str] = None
    udp_targets: List[str] = None
    icmp_targets: List[str] = None

    def __post_init__(self):
        if self.http_targets is None:
            self.http_targets = []
        if self.tcp_targets is None:
            self.tcp_targets = []
        if self.udp_targets is None:
            self.udp_targets = []
        if self.icmp_targets is None:
            self.icmp_targets = []


class WaddlePerfClient:
    """Main WaddlePerf containerClient"""

    def __init__(self, config: ClientConfig):
        self.config = config
        self.device_info = self._detect_device_info()
        self.logger = get_logger(__name__)
        self.session: Optional[aiohttp.ClientSession] = None
        self._token_lock = asyncio.Lock()  # Protect token updates

    def _detect_device_info(self) -> DeviceInfo:
        """Auto-detect device information"""
        serial = self.config.device_serial or self._get_device_serial()
        hostname = self.config.device_hostname or socket.gethostname()
        os_name = platform.system()
        os_version = platform.release()

        return DeviceInfo(
            serial=serial,
            hostname=hostname,
            os=os_name,
            os_version=os_version
        )

    def _get_device_serial(self) -> str:
        """Generate or detect device serial number"""
        try:
            # Try to get machine ID on Linux
            if os.path.exists('/etc/machine-id'):
                with open('/etc/machine-id', 'r') as f:
                    return f.read().strip()
            elif os.path.exists('/var/lib/dbus/machine-id'):
                with open('/var/lib/dbus/machine-id', 'r') as f:
                    return f.read().strip()
        except Exception:
            pass

        # Fallback to hostname-based ID
        import hashlib
        return hashlib.sha256(socket.gethostname().encode()).hexdigest()[:32]

    async def _create_session(self) -> aiohttp.ClientSession:
        """Create HTTP session for API communication"""
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        return aiohttp.ClientSession(timeout=timeout)

    async def _login(self) -> bool:
        """Authenticate with manager and obtain tokens"""
        if not self.session:
            self.session = await self._create_session()

        if not self.config.auth_user or not self.config.auth_pass:
            self.logger.error("Username and password required for authentication")
            return False

        login_url = f"{self.config.manager_url}/api/v1/auth/login"
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'WaddlePerf-containerClient/1.0'
        }

        try:
            async with self.session.post(
                login_url,
                json={
                    'username': self.config.auth_user,
                    'password': self.config.auth_pass
                },
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.config.access_token = data.get('access_token')
                    self.config.refresh_token = data.get('refresh_token')
                    self.logger.info("Successfully authenticated with manager")
                    return True
                else:
                    error_text = await response.text()
                    self.logger.error(f"Login failed: {response.status} - {error_text}")
                    return False
        except Exception as e:
            self.logger.error(f"Login request failed: {e}")
            return False

    async def _refresh_token(self) -> bool:
        """Refresh access token using refresh token"""
        if not self.config.refresh_token:
            self.logger.warning("No refresh token available, attempting login")
            return await self._login()

        if not self.session:
            self.session = await self._create_session()

        refresh_url = f"{self.config.manager_url}/api/v1/auth/refresh"
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'WaddlePerf-containerClient/1.0'
        }

        try:
            async with self.session.post(
                refresh_url,
                json={'refresh_token': self.config.refresh_token},
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.config.access_token = data.get('access_token')
                    self.logger.debug("Token refreshed successfully")
                    return True
                else:
                    self.logger.warning("Token refresh failed, attempting login")
                    return await self._login()
        except Exception as e:
            self.logger.error(f"Token refresh request failed: {e}")
            return await self._login()

    async def _ensure_authenticated(self) -> bool:
        """Ensure we have valid authentication tokens"""
        async with self._token_lock:
            if not self.config.access_token:
                return await self._login()
            return True

    def _get_auth_headers(self) -> Dict[str, str]:
        """Build authentication headers with Bearer token"""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'WaddlePerf-containerClient/1.0'
        }

        if self.config.access_token:
            headers['Authorization'] = f'Bearer {self.config.access_token}'

        return headers

    async def _upload_result(self, result_data: Dict) -> bool:
        """Upload test result to manager server"""
        # Ensure authentication before uploading
        if not await self._ensure_authenticated():
            self.logger.error("Failed to authenticate before uploading result")
            return False

        if not self.session:
            self.session = await self._create_session()

        # Refresh token before request
        await self._refresh_token()

        # Add device info to result
        result_data['device_serial'] = self.device_info.serial
        result_data['device_hostname'] = self.device_info.hostname
        result_data['device_os'] = self.device_info.os
        result_data['device_os_version'] = self.device_info.os_version
        result_data['timestamp'] = datetime.now().astimezone().isoformat()

        upload_url = f"{self.config.manager_url}/api/v1/tests/"
        headers = self._get_auth_headers()

        try:
            async with self.session.post(
                upload_url,
                json=result_data,
                headers=headers
            ) as response:
                if response.status in (200, 201):
                    self.logger.info(f"Successfully uploaded result: {result_data.get('test_type')}")
                    return True
                else:
                    error_text = await response.text()
                    self.logger.error(
                        f"Failed to upload result: {response.status} - {error_text}"
                    )
                    return False

        except aiohttp.ClientError as e:
            self.logger.error(f"Failed to upload result: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error uploading result: {e}")
            return False

    async def run_http_tests(self) -> List[HttpTestResult]:
        """Run HTTP tests against all targets"""
        if not self.config.enable_http_test or not self.config.http_targets:
            return []

        self.logger.info(f"Running HTTP tests against {len(self.config.http_targets)} targets")
        results = []

        http_test = HttpTest(timeout=30)

        for target in self.config.http_targets:
            try:
                result = await http_test.run_test(target)
                results.append(result)

                # Upload result
                result_dict = http_test.to_dict(result)
                await self._upload_result(result_dict)

            except Exception as e:
                self.logger.error(f"HTTP test failed for {target}: {e}")

        await http_test.close()
        return results

    async def run_tcp_tests(self) -> List[TcpTestResult]:
        """Run TCP tests against all targets"""
        if not self.config.enable_tcp_test or not self.config.tcp_targets:
            return []

        self.logger.info(f"Running TCP tests against {len(self.config.tcp_targets)} targets")
        results = []

        tcp_test = TcpTest(timeout=10)

        for target in self.config.tcp_targets:
            try:
                # Parse protocol from target if specified (e.g., ssh://host:22)
                protocol = "raw_tcp"
                if target.startswith("ssh://"):
                    protocol = "ssh"
                    target = target[6:]
                elif target.startswith("tls://"):
                    protocol = "tcp_tls"
                    target = target[6:]

                result = await tcp_test.run_test(target, protocol)
                results.append(result)

                # Upload result
                result_dict = tcp_test.to_dict(result)
                await self._upload_result(result_dict)

            except Exception as e:
                self.logger.error(f"TCP test failed for {target}: {e}")

        return results

    async def run_udp_tests(self) -> List[UdpTestResult]:
        """Run UDP tests against all targets"""
        if not self.config.enable_udp_test or not self.config.udp_targets:
            return []

        self.logger.info(f"Running UDP tests against {len(self.config.udp_targets)} targets")
        results = []

        udp_test = UdpTest(timeout=5, packet_count=4)

        for target in self.config.udp_targets:
            try:
                # Parse protocol from target if specified (e.g., dns://example.com)
                protocol = "raw_udp"
                if target.startswith("dns://"):
                    protocol = "dns"
                    target = target[6:]

                result = await udp_test.run_test(target, protocol)
                results.append(result)

                # Upload result
                result_dict = udp_test.to_dict(result)
                await self._upload_result(result_dict)

            except Exception as e:
                self.logger.error(f"UDP test failed for {target}: {e}")

        return results

    async def run_icmp_tests(self) -> List[IcmpTestResult]:
        """Run ICMP tests against all targets"""
        if not self.config.enable_icmp_test or not self.config.icmp_targets:
            return []

        self.logger.info(f"Running ICMP tests against {len(self.config.icmp_targets)} targets")
        results = []

        icmp_test = IcmpTest(timeout=5, packet_count=4)

        for target in self.config.icmp_targets:
            try:
                result = await icmp_test.run_test(target)
                results.append(result)

                # Upload result
                result_dict = icmp_test.to_dict(result)
                await self._upload_result(result_dict)

            except Exception as e:
                self.logger.error(f"ICMP test failed for {target}: {e}")

        return results

    async def run_all_tests(self) -> Dict[str, List]:
        """Run all enabled tests"""
        self.logger.info("Starting test suite")
        start_time = time.time()

        # Run tests concurrently
        results = await asyncio.gather(
            self.run_http_tests(),
            self.run_tcp_tests(),
            self.run_udp_tests(),
            self.run_icmp_tests(),
            return_exceptions=True
        )

        http_results, tcp_results, udp_results, icmp_results = results

        # Handle exceptions
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                test_types = ['HTTP', 'TCP', 'UDP', 'ICMP']
                self.logger.error(f"{test_types[i]} tests failed with exception: {result}")

        elapsed = time.time() - start_time
        self.logger.info(f"Test suite completed in {elapsed:.2f} seconds")

        return {
            'http': http_results if not isinstance(http_results, Exception) else [],
            'tcp': tcp_results if not isinstance(tcp_results, Exception) else [],
            'udp': udp_results if not isinstance(udp_results, Exception) else [],
            'icmp': icmp_results if not isinstance(icmp_results, Exception) else []
        }

    async def run_scheduler(self):
        """Run tests on a schedule"""
        if self.config.run_seconds <= 0:
            self.logger.info("Scheduler disabled (RUN_SECONDS <= 0)")
            return

        self.logger.info(f"Starting scheduler: running tests every {self.config.run_seconds} seconds")

        while True:
            try:
                await self.run_all_tests()
            except Exception as e:
                self.logger.error(f"Scheduled test run failed: {e}")

            # Wait for next run
            self.logger.info(f"Waiting {self.config.run_seconds} seconds until next run")
            await asyncio.sleep(self.config.run_seconds)

    async def close(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()


def load_config_from_env() -> ClientConfig:
    """Load configuration from environment variables"""
    config = ClientConfig()

    config.auth_user = os.getenv('AUTH_USER')
    config.auth_pass = os.getenv('AUTH_PASS')
    config.access_token = os.getenv('ACCESS_TOKEN')
    config.refresh_token = os.getenv('REFRESH_TOKEN')

    config.manager_url = os.getenv('MANAGER_URL', 'https://waddleperf.penguintech.io')
    config.test_server_url = os.getenv('TEST_SERVER_URL', 'http://localhost:8081')

    config.run_seconds = int(os.getenv('RUN_SECONDS', '0'))

    config.enable_http_test = os.getenv('ENABLE_HTTP_TEST', 'true').lower() == 'true'
    config.enable_tcp_test = os.getenv('ENABLE_TCP_TEST', 'true').lower() == 'true'
    config.enable_udp_test = os.getenv('ENABLE_UDP_TEST', 'true').lower() == 'true'
    config.enable_icmp_test = os.getenv('ENABLE_ICMP_TEST', 'true').lower() == 'true'

    config.device_serial = os.getenv('DEVICE_SERIAL')
    config.device_hostname = os.getenv('DEVICE_HOSTNAME')

    # Parse targets from environment
    http_targets_str = os.getenv('HTTP_TARGETS', 'https://www.google.com')
    config.http_targets = [t.strip() for t in http_targets_str.split(',') if t.strip()]

    tcp_targets_str = os.getenv('TCP_TARGETS', '')
    config.tcp_targets = [t.strip() for t in tcp_targets_str.split(',') if t.strip()]

    udp_targets_str = os.getenv('UDP_TARGETS', '')
    config.udp_targets = [t.strip() for t in udp_targets_str.split(',') if t.strip()]

    icmp_targets_str = os.getenv('ICMP_TARGETS', '8.8.8.8')
    config.icmp_targets = [t.strip() for t in icmp_targets_str.split(',') if t.strip()]

    return config


def setup_logging(level: str = "INFO"):
    """Setup logging configuration"""
    log_level = getattr(logging, level.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


async def main_async(args):
    """Main async execution"""
    if args.config_file:
        # Load config from JSON file
        with open(args.config_file, 'r') as f:
            config_dict = json.load(f)
        config = ClientConfig(**config_dict)
    else:
        # Load config from environment
        config = load_config_from_env()

    # Override with CLI arguments
    if args.http_target:
        config.http_targets = [args.http_target]
        config.enable_http_test = True

    if args.tcp_target:
        config.tcp_targets = [args.tcp_target]
        config.enable_tcp_test = True

    if args.udp_target:
        config.udp_targets = [args.udp_target]
        config.enable_udp_test = True

    if args.icmp_target:
        config.icmp_targets = [args.icmp_target]
        config.enable_icmp_test = True

    if args.test_type:
        # Disable all, then enable only specified
        config.enable_http_test = False
        config.enable_tcp_test = False
        config.enable_udp_test = False
        config.enable_icmp_test = False

        if args.test_type == 'http':
            config.enable_http_test = True
        elif args.test_type == 'tcp':
            config.enable_tcp_test = True
        elif args.test_type == 'udp':
            config.enable_udp_test = True
        elif args.test_type == 'icmp':
            config.enable_icmp_test = True
        elif args.test_type == 'all':
            config.enable_http_test = True
            config.enable_tcp_test = True
            config.enable_udp_test = True
            config.enable_icmp_test = True

    # Create client
    client = WaddlePerfClient(config)

    try:
        if args.schedule or config.run_seconds > 0:
            # Run in scheduler mode
            await client.run_scheduler()
        else:
            # Run once
            results = await client.run_all_tests()

            # Print summary
            print("\n" + "="*60)
            print("WaddlePerf Test Results Summary")
            print("="*60)

            for test_type, test_results in results.items():
                if test_results:
                    successful = sum(1 for r in test_results if r.success)
                    print(f"\n{test_type.upper()} Tests: {successful}/{len(test_results)} successful")

                    for result in test_results:
                        status = "✓" if result.success else "✗"
                        target = result.target_host
                        if result.success:
                            print(f"  {status} {target}: {result.latency_ms:.2f}ms")
                        else:
                            print(f"  {status} {target}: {result.error}")

            print("\n" + "="*60)

    finally:
        await client.close()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='WaddlePerf containerClient - Network Performance Testing'
    )

    parser.add_argument(
        '--test-type',
        choices=['http', 'tcp', 'udp', 'icmp', 'all'],
        help='Type of test to run (default: all enabled in config)'
    )

    parser.add_argument(
        '--http-target',
        help='HTTP/HTTPS target URL'
    )

    parser.add_argument(
        '--tcp-target',
        help='TCP target (host:port or ssh://host:port)'
    )

    parser.add_argument(
        '--udp-target',
        help='UDP target (host:port or dns://hostname)'
    )

    parser.add_argument(
        '--icmp-target',
        help='ICMP target (hostname or IP)'
    )

    parser.add_argument(
        '--config-file',
        help='JSON configuration file path'
    )

    parser.add_argument(
        '--schedule',
        action='store_true',
        help='Run in scheduler mode (use RUN_SECONDS from env)'
    )

    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)

    # Run async main
    try:
        asyncio.run(main_async(args))
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
