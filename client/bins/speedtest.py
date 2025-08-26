#!/usr/bin/env python3

import time
import json
import asyncio
import aiohttp
import threading
import os
import socket
from typing import Dict, List


class SpeedTest:
    """
    Async/threaded speedtest implementation for network performance testing
    Replaces LibreSpeed with py4web-integrated solution
    """

    def __init__(self, server_url: str = None, test_duration: int = 10,
                 chunk_size: int = 1048576, parallel_connections: int = 4):
        self.server_url = server_url or os.getenv('SPEEDTEST_SERVER', 'http://localhost')
        self.test_duration = test_duration
        self.chunk_size = chunk_size  # 1MB chunks
        self.parallel_connections = parallel_connections
        self.results = {}

    async def ping_test(self, count: int = 10) -> Dict:
        """Async ping test using HTTP requests"""
        ping_results = []

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            for i in range(count):
                start_time = time.perf_counter()
                try:
                    async with session.get(f"{self.server_url}/ping") as response:
                        if response.status == 200:
                            end_time = time.perf_counter()
                            latency = (end_time - start_time) * 1000  # Convert to ms
                            ping_results.append(latency)
                        else:
                            ping_results.append(None)
                except Exception:
                    ping_results.append(None)

                await asyncio.sleep(0.1)  # 100ms between pings

        successful_pings = [p for p in ping_results if p is not None]

        if successful_pings:
            return {
                'count': count,
                'successful': len(successful_pings),
                'failed': count - len(successful_pings),
                'min_ms': min(successful_pings),
                'max_ms': max(successful_pings),
                'avg_ms': sum(successful_pings) / len(successful_pings),
                'packet_loss_percent': ((count - len(successful_pings)) / count) * 100,
                'raw_results': ping_results
            }
        else:
            return {
                'count': count,
                'successful': 0,
                'failed': count,
                'min_ms': None,
                'max_ms': None,
                'avg_ms': None,
                'packet_loss_percent': 100.0,
                'raw_results': ping_results
            }

    async def download_test_single(self, session: aiohttp.ClientSession,
                                   connection_id: int) -> List[float]:
        """Single connection download test"""
        speeds = []
        start_time = time.perf_counter()

        while (time.perf_counter() - start_time) < self.test_duration:
            chunk_start = time.perf_counter()

            try:
                # Request a chunk of data from server
                async with session.get(
                    f"{self.server_url}/download",
                    params={'size': self.chunk_size, 'connection': connection_id}
                ) as response:
                    if response.status == 200:
                        data = await response.read()
                        chunk_end = time.perf_counter()

                        if len(data) > 0:
                            chunk_time = chunk_end - chunk_start
                            speed_bps = len(data) / chunk_time  # bytes per second
                            speed_mbps = (speed_bps * 8) / (1024 * 1024)  # Convert to Mbps
                            speeds.append(speed_mbps)

            except Exception as e:
                print(f"Download error on connection {connection_id}: {e}")
                await asyncio.sleep(0.1)
                continue

        return speeds

    async def download_test(self) -> Dict:
        """Multi-connection download speed test"""
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.test_duration + 5),
            connector=aiohttp.TCPConnector(limit=self.parallel_connections + 5)
        ) as session:

            # Start multiple download connections
            tasks = []
            for i in range(self.parallel_connections):
                task = asyncio.create_task(self.download_test_single(session, i))
                tasks.append(task)

            # Wait for all connections to complete
            connection_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Aggregate results
            all_speeds = []
            for result in connection_results:
                if isinstance(result, list):
                    all_speeds.extend(result)

            if all_speeds:
                return {
                    'connections': self.parallel_connections,
                    'duration_seconds': self.test_duration,
                    'samples': len(all_speeds),
                    'max_speed_mbps': max(all_speeds),
                    'min_speed_mbps': min(all_speeds),
                    'avg_speed_mbps': sum(all_speeds) / len(all_speeds),
                    'total_data_mb': sum(all_speeds) * self.test_duration / len(all_speeds) / 8,
                    'raw_speeds': all_speeds
                }
            else:
                return {
                    'error': 'No successful download measurements',
                    'connections': self.parallel_connections,
                    'duration_seconds': self.test_duration
                }

    async def upload_test_single(self, session: aiohttp.ClientSession,
                                 connection_id: int) -> List[float]:
        """Single connection upload test"""
        speeds = []
        start_time = time.perf_counter()

        # Generate test data
        test_data = b'0' * self.chunk_size

        while (time.perf_counter() - start_time) < self.test_duration:
            chunk_start = time.perf_counter()

            try:
                async with session.post(
                    f"{self.server_url}/upload",
                    data=test_data,
                    params={'connection': connection_id}
                ) as response:
                    if response.status == 200:
                        chunk_end = time.perf_counter()
                        chunk_time = chunk_end - chunk_start
                        speed_bps = len(test_data) / chunk_time
                        speed_mbps = (speed_bps * 8) / (1024 * 1024)
                        speeds.append(speed_mbps)

            except Exception as e:
                print(f"Upload error on connection {connection_id}: {e}")
                await asyncio.sleep(0.1)
                continue

        return speeds

    async def upload_test(self) -> Dict:
        """Multi-connection upload speed test"""
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.test_duration + 5),
            connector=aiohttp.TCPConnector(limit=self.parallel_connections + 5)
        ) as session:

            tasks = []
            for i in range(self.parallel_connections):
                task = asyncio.create_task(self.upload_test_single(session, i))
                tasks.append(task)

            connection_results = await asyncio.gather(*tasks, return_exceptions=True)

            all_speeds = []
            for result in connection_results:
                if isinstance(result, list):
                    all_speeds.extend(result)

            if all_speeds:
                return {
                    'connections': self.parallel_connections,
                    'duration_seconds': self.test_duration,
                    'samples': len(all_speeds),
                    'max_speed_mbps': max(all_speeds),
                    'min_speed_mbps': min(all_speeds),
                    'avg_speed_mbps': sum(all_speeds) / len(all_speeds),
                    'total_data_mb': sum(all_speeds) * self.test_duration / len(all_speeds) / 8,
                    'raw_speeds': all_speeds
                }
            else:
                return {
                    'error': 'No successful upload measurements',
                    'connections': self.parallel_connections,
                    'duration_seconds': self.test_duration
                }

    def get_server_info(self) -> Dict:
        """Get server information and geolocation"""
        try:
            # Parse server URL
            from urllib.parse import urlparse
            parsed_url = urlparse(self.server_url)
            hostname = parsed_url.hostname
            port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)

            # Resolve hostname
            ip_address = socket.gethostbyname(hostname)

            return {
                'server_url': self.server_url,
                'hostname': hostname,
                'ip_address': ip_address,
                'port': port,
                'ssl_enabled': parsed_url.scheme == 'https'
            }
        except Exception as e:
            return {
                'server_url': self.server_url,
                'error': str(e)
            }

    async def run_full_test(self) -> Dict:
        """Run complete speed test suite"""
        test_start = time.time()

        print("Starting WaddlePerf SpeedTest...")

        # Get server info
        server_info = self.get_server_info()
        print(f"Testing against: {server_info.get('hostname', 'unknown')}")

        # Run ping test
        print("Running ping test...")
        ping_results = await self.ping_test()

        # Run download test
        print("Running download test...")
        download_results = await self.download_test()

        # Run upload test
        print("Running upload test...")
        upload_results = await self.upload_test()

        test_end = time.time()

        return {
            'timestamp': int(test_start),
            'test_duration_seconds': test_end - test_start,
            'server_info': server_info,
            'ping': ping_results,
            'download': download_results,
            'upload': upload_results,
            'test_config': {
                'duration': self.test_duration,
                'chunk_size': self.chunk_size,
                'parallel_connections': self.parallel_connections
            }
        }


def threaded_speedtest(server_url: str = None, duration: int = 10,
                       connections: int = 4) -> Dict:
    """Thread-safe wrapper for speedtest"""
    async def run_test():
        speedtest = SpeedTest(server_url, duration, parallel_connections=connections)
        return await speedtest.run_full_test()

    # Run in new event loop for thread safety
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(run_test())
    finally:
        loop.close()


def main():
    """CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description='WaddlePerf SpeedTest')
    parser.add_argument('--server', '-s', default='http://localhost:8080',
                        help='Speed test server URL')
    parser.add_argument('--duration', '-d', type=int, default=10,
                        help='Test duration in seconds')
    parser.add_argument('--connections', '-c', type=int, default=4,
                        help='Number of parallel connections')
    parser.add_argument('--output', '-o', choices=['json', 'text'], default='text',
                        help='Output format')

    args = parser.parse_args()

    # Run the test
    results = threaded_speedtest(args.server, args.duration, args.connections)

    if args.output == 'json':
        print(json.dumps(results, indent=2))
    else:
        # Text output
        print("\n🐧 WaddlePerf SpeedTest Results")
        print("=" * 50)
        print(f"Server: {results['server_info'].get('hostname', 'N/A')}")
        print(f"Test Duration: {results['test_duration_seconds']:.2f}s")

        if 'ping' in results:
            ping = results['ping']
            print("\n📡 Ping Test:")
            print(f"  Successful: {ping['successful']}/{ping['count']}")
            print(f"  Average: {ping['avg_ms']:.2f}ms" if ping['avg_ms'] else "  Average: N/A")
            print(f"  Packet Loss: {ping['packet_loss_percent']:.1f}%")

        if 'download' in results and 'avg_speed_mbps' in results['download']:
            dl = results['download']
            print("\n⬇️  Download Test:")
            print(f"  Speed: {dl['avg_speed_mbps']:.2f} Mbps")
            print(f"  Data Transferred: {dl['total_data_mb']:.2f} MB")
            print(f"  Connections: {dl['connections']}")

        if 'upload' in results and 'avg_speed_mbps' in results['upload']:
            ul = results['upload']
            print("\n⬆️  Upload Test:")
            print(f"  Speed: {ul['avg_speed_mbps']:.2f} Mbps")
            print(f"  Data Transferred: {ul['total_data_mb']:.2f} MB")
            print(f"  Connections: {ul['connections']}")


if __name__ == "__main__":
    main()
