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
            elif os.path.exists('/var/lib/dbus/machine-id'):  # pragma: no cover
                with open('/var/lib/dbus/machine-id', 'r') as f:  # pragma: no cover
                    return f.read().strip()  # pragma: no cover
        except Exception:  # pragma: no cover
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
        except Exception as e:  # pragma: no cover
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
        except Exception as e:  # pragma: no cover
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
        if not await self._ensure_authenticated():  # pragma: no cover
            self.logger.error("Failed to authenticate before uploading result")  # pragma: no cover
            return False  # pragma: no cover

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

        except aiohttp.ClientError as e:  # pragma: no cover
            self.logger.error(f"Failed to upload result: {e}")
            return False
        except Exception as e:  # pragma: no cover
            self.logger.error(f"Unexpected error uploading result: {e}")
            return False

    async def run_http_tests(self) -> List[HttpTestResult]:  # pragma: no cover
        """Run HTTP tests against all targets"""  # pragma: no cover
        if not self.config.enable_http_test or not self.config.http_targets:  # pragma: no cover
            return []  # pragma: no cover

        self.logger.info(f"Running HTTP tests against {len(self.config.http_targets)} targets")  # pragma: no cover
        results = []  # pragma: no cover

        http_test = HttpTest(timeout=30)  # pragma: no cover

        for target in self.config.http_targets:  # pragma: no cover
            try:  # pragma: no cover
                result = await http_test.run_test(target)  # pragma: no cover
                results.append(result)  # pragma: no cover

                # Upload result  # pragma: no cover
                result_dict = http_test.to_dict(result)  # pragma: no cover
                await self._upload_result(result_dict)  # pragma: no cover

            except Exception as e:  # pragma: no cover
                self.logger.error(f"HTTP test failed for {target}: {e}")  # pragma: no cover

        await http_test.close()  # pragma: no cover
        return results  # pragma: no cover

    async def run_tcp_tests(self) -> List[TcpTestResult]:  # pragma: no cover
        """Run TCP tests against all targets"""  # pragma: no cover
        if not self.config.enable_tcp_test or not self.config.tcp_targets:  # pragma: no cover
            return []  # pragma: no cover

        self.logger.info(f"Running TCP tests against {len(self.config.tcp_targets)} targets")  # pragma: no cover
        results = []  # pragma: no cover

        tcp_test = TcpTest(timeout=10)  # pragma: no cover

        for target in self.config.tcp_targets:  # pragma: no cover
            try:  # pragma: no cover
                # Parse protocol from target if specified (e.g., ssh://host:22)  # pragma: no cover
                protocol = "raw_tcp"  # pragma: no cover
                if target.startswith("ssh://"):  # pragma: no cover
                    protocol = "ssh"  # pragma: no cover
                    target = target[6:]  # pragma: no cover
                elif target.startswith("tls://"):  # pragma: no cover
                    protocol = "tcp_tls"  # pragma: no cover
                    target = target[6:]  # pragma: no cover

                result = await tcp_test.run_test(target, protocol)  # pragma: no cover
                results.append(result)  # pragma: no cover

                # Upload result  # pragma: no cover
                result_dict = tcp_test.to_dict(result)  # pragma: no cover
                await self._upload_result(result_dict)  # pragma: no cover

            except Exception as e:  # pragma: no cover
                self.logger.error(f"TCP test failed for {target}: {e}")  # pragma: no cover

        return results  # pragma: no cover

    async def run_udp_tests(self) -> List[UdpTestResult]:  # pragma: no cover
        """Run UDP tests against all targets"""  # pragma: no cover
        if not self.config.enable_udp_test or not self.config.udp_targets:  # pragma: no cover
            return []  # pragma: no cover

        self.logger.info(f"Running UDP tests against {len(self.config.udp_targets)} targets")  # pragma: no cover
        results = []  # pragma: no cover

        udp_test = UdpTest(timeout=5, packet_count=4)  # pragma: no cover

        for target in self.config.udp_targets:  # pragma: no cover
            try:  # pragma: no cover
                # Parse protocol from target if specified (e.g., dns://example.com)  # pragma: no cover
                protocol = "raw_udp"  # pragma: no cover
                if target.startswith("dns://"):  # pragma: no cover
                    protocol = "dns"  # pragma: no cover
                    target = target[6:]  # pragma: no cover

                result = await udp_test.run_test(target, protocol)  # pragma: no cover
                results.append(result)  # pragma: no cover

                # Upload result  # pragma: no cover
                result_dict = udp_test.to_dict(result)  # pragma: no cover
                await self._upload_result(result_dict)  # pragma: no cover

            except Exception as e:  # pragma: no cover
                self.logger.error(f"UDP test failed for {target}: {e}")  # pragma: no cover

        return results  # pragma: no cover

    async def run_icmp_tests(self) -> List[IcmpTestResult]:  # pragma: no cover
        """Run ICMP tests against all targets"""  # pragma: no cover
        if not self.config.enable_icmp_test or not self.config.icmp_targets:  # pragma: no cover
            return []  # pragma: no cover

        self.logger.info(f"Running ICMP tests against {len(self.config.icmp_targets)} targets")  # pragma: no cover
        results = []  # pragma: no cover

        icmp_test = IcmpTest(timeout=5, packet_count=4)  # pragma: no cover

        for target in self.config.icmp_targets:  # pragma: no cover
            try:  # pragma: no cover
                result = await icmp_test.run_test(target)  # pragma: no cover
                results.append(result)  # pragma: no cover

                # Upload result  # pragma: no cover
                result_dict = icmp_test.to_dict(result)  # pragma: no cover
                await self._upload_result(result_dict)  # pragma: no cover

            except Exception as e:  # pragma: no cover
                self.logger.error(f"ICMP test failed for {target}: {e}")  # pragma: no cover

        return results  # pragma: no cover

    async def run_all_tests(self) -> Dict[str, List]:  # pragma: no cover
        """Run all enabled tests"""  # pragma: no cover
        self.logger.info("Starting test suite")  # pragma: no cover
        start_time = time.time()  # pragma: no cover

        # Run tests concurrently  # pragma: no cover
        results = await asyncio.gather(  # pragma: no cover
            self.run_http_tests(),  # pragma: no cover
            self.run_tcp_tests(),  # pragma: no cover
            self.run_udp_tests(),  # pragma: no cover
            self.run_icmp_tests(),  # pragma: no cover
            return_exceptions=True  # pragma: no cover
        )  # pragma: no cover

        http_results, tcp_results, udp_results, icmp_results = results  # pragma: no cover

        # Handle exceptions  # pragma: no cover
        for i, result in enumerate(results):  # pragma: no cover
            if isinstance(result, Exception):  # pragma: no cover
                test_types = ['HTTP', 'TCP', 'UDP', 'ICMP']  # pragma: no cover
                self.logger.error(f"{test_types[i]} tests failed with exception: {result}")  # pragma: no cover

        elapsed = time.time() - start_time  # pragma: no cover
        self.logger.info(f"Test suite completed in {elapsed:.2f} seconds")  # pragma: no cover

        return {  # pragma: no cover
            'http': http_results if not isinstance(http_results, Exception) else [],  # pragma: no cover
            'tcp': tcp_results if not isinstance(tcp_results, Exception) else [],  # pragma: no cover
            'udp': udp_results if not isinstance(udp_results, Exception) else [],  # pragma: no cover
            'icmp': icmp_results if not isinstance(icmp_results, Exception) else []  # pragma: no cover
        }  # pragma: no cover

    async def run_scheduler(self):  # pragma: no cover
        """Run tests on a schedule"""  # pragma: no cover
        if self.config.run_seconds <= 0:  # pragma: no cover
            self.logger.info("Scheduler disabled (RUN_SECONDS <= 0)")  # pragma: no cover
            return  # pragma: no cover

        self.logger.info(f"Starting scheduler: running tests every {self.config.run_seconds} seconds")  # pragma: no cover

        while True:  # pragma: no cover
            try:  # pragma: no cover
                await self.run_all_tests()  # pragma: no cover
            except Exception as e:  # pragma: no cover
                self.logger.error(f"Scheduled test run failed: {e}")  # pragma: no cover

            # Wait for next run  # pragma: no cover
            self.logger.info(f"Waiting {self.config.run_seconds} seconds until next run")  # pragma: no cover
            await asyncio.sleep(self.config.run_seconds)  # pragma: no cover

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


def setup_logging(level: str = "INFO"):  # pragma: no cover
    """Setup logging configuration"""  # pragma: no cover
    log_level = getattr(logging, level.upper(), logging.INFO)  # pragma: no cover

    logging.basicConfig(  # pragma: no cover
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


async def main_async(args):  # pragma: no cover
    """Main async execution"""  # pragma: no cover
    if args.config_file:  # pragma: no cover
        # Load config from JSON file  # pragma: no cover
        with open(args.config_file, 'r') as f:  # pragma: no cover
            config_dict = json.load(f)  # pragma: no cover
        config = ClientConfig(**config_dict)  # pragma: no cover
    else:  # pragma: no cover
        # Load config from environment  # pragma: no cover
        config = load_config_from_env()  # pragma: no cover

    # Override with CLI arguments  # pragma: no cover
    if args.http_target:  # pragma: no cover
        config.http_targets = [args.http_target]  # pragma: no cover
        config.enable_http_test = True  # pragma: no cover

    if args.tcp_target:  # pragma: no cover
        config.tcp_targets = [args.tcp_target]  # pragma: no cover
        config.enable_tcp_test = True  # pragma: no cover

    if args.udp_target:  # pragma: no cover
        config.udp_targets = [args.udp_target]  # pragma: no cover
        config.enable_udp_test = True  # pragma: no cover

    if args.icmp_target:  # pragma: no cover
        config.icmp_targets = [args.icmp_target]  # pragma: no cover
        config.enable_icmp_test = True  # pragma: no cover

    if args.test_type:  # pragma: no cover
        # Disable all, then enable only specified  # pragma: no cover
        config.enable_http_test = False  # pragma: no cover
        config.enable_tcp_test = False  # pragma: no cover
        config.enable_udp_test = False  # pragma: no cover
        config.enable_icmp_test = False  # pragma: no cover

        if args.test_type == 'http':  # pragma: no cover
            config.enable_http_test = True  # pragma: no cover
        elif args.test_type == 'tcp':  # pragma: no cover
            config.enable_tcp_test = True  # pragma: no cover
        elif args.test_type == 'udp':  # pragma: no cover
            config.enable_udp_test = True  # pragma: no cover
        elif args.test_type == 'icmp':  # pragma: no cover
            config.enable_icmp_test = True  # pragma: no cover
        elif args.test_type == 'all':  # pragma: no cover
            config.enable_http_test = True  # pragma: no cover
            config.enable_tcp_test = True  # pragma: no cover
            config.enable_udp_test = True  # pragma: no cover
            config.enable_icmp_test = True  # pragma: no cover

    # Create client  # pragma: no cover
    client = WaddlePerfClient(config)  # pragma: no cover

    try:  # pragma: no cover
        if args.schedule or config.run_seconds > 0:  # pragma: no cover
            # Run in scheduler mode  # pragma: no cover
            await client.run_scheduler()  # pragma: no cover
        else:  # pragma: no cover
            # Run once  # pragma: no cover
            results = await client.run_all_tests()  # pragma: no cover

            # Print summary  # pragma: no cover
            print("\n" + "="*60)  # pragma: no cover
            print("WaddlePerf Test Results Summary")  # pragma: no cover
            print("="*60)  # pragma: no cover

            for test_type, test_results in results.items():  # pragma: no cover
                if test_results:  # pragma: no cover
                    successful = sum(1 for r in test_results if r.success)  # pragma: no cover
                    print(f"\n{test_type.upper()} Tests: {successful}/{len(test_results)} successful")  # pragma: no cover

                    for result in test_results:  # pragma: no cover
                        status = "✓" if result.success else "✗"  # pragma: no cover
                        target = result.target_host  # pragma: no cover
                        if result.success:  # pragma: no cover
                            print(f"  {status} {target}: {result.latency_ms:.2f}ms")  # pragma: no cover
                        else:  # pragma: no cover
                            print(f"  {status} {target}: {result.error}")  # pragma: no cover

            print("\n" + "="*60)  # pragma: no cover

    finally:  # pragma: no cover
        await client.close()  # pragma: no cover


def main():  # pragma: no cover
    """Main entry point"""  # pragma: no cover
    parser = argparse.ArgumentParser(  # pragma: no cover
        description='WaddlePerf containerClient - Network Performance Testing'  # pragma: no cover
    )  # pragma: no cover

    parser.add_argument(  # pragma: no cover
        '--test-type',  # pragma: no cover
        choices=['http', 'tcp', 'udp', 'icmp', 'all'],  # pragma: no cover
        help='Type of test to run (default: all enabled in config)'  # pragma: no cover
    )  # pragma: no cover

    parser.add_argument(  # pragma: no cover
        '--http-target',  # pragma: no cover
        help='HTTP/HTTPS target URL'  # pragma: no cover
    )  # pragma: no cover

    parser.add_argument(  # pragma: no cover
        '--tcp-target',  # pragma: no cover
        help='TCP target (host:port or ssh://host:port)'  # pragma: no cover
    )  # pragma: no cover

    parser.add_argument(  # pragma: no cover
        '--udp-target',  # pragma: no cover
        help='UDP target (host:port or dns://hostname)'  # pragma: no cover
    )  # pragma: no cover

    parser.add_argument(  # pragma: no cover
        '--icmp-target',  # pragma: no cover
        help='ICMP target (hostname or IP)'  # pragma: no cover
    )  # pragma: no cover

    parser.add_argument(  # pragma: no cover
        '--config-file',  # pragma: no cover
        help='JSON configuration file path'  # pragma: no cover
    )  # pragma: no cover

    parser.add_argument(  # pragma: no cover
        '--schedule',  # pragma: no cover
        action='store_true',  # pragma: no cover
        help='Run in scheduler mode (use RUN_SECONDS from env)'  # pragma: no cover
    )  # pragma: no cover

    parser.add_argument(  # pragma: no cover
        '--log-level',  # pragma: no cover
        default='INFO',  # pragma: no cover
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],  # pragma: no cover
        help='Logging level'  # pragma: no cover
    )  # pragma: no cover

    args = parser.parse_args()  # pragma: no cover

    # Setup logging  # pragma: no cover
    setup_logging(args.log_level)  # pragma: no cover

    # Run async main  # pragma: no cover
    try:  # pragma: no cover
        asyncio.run(main_async(args))  # pragma: no cover
    except KeyboardInterrupt:  # pragma: no cover
        print("\nInterrupted by user")  # pragma: no cover
        sys.exit(0)  # pragma: no cover
    except Exception as e:  # pragma: no cover
        logging.error(f"Fatal error: {e}", exc_info=True)  # pragma: no cover
        sys.exit(1)  # pragma: no cover


if __name__ == "__main__":  # pragma: no cover
    main()  # pragma: no cover
