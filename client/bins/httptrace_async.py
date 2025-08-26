#!/usr/bin/env python3
import asyncio
import aiohttp
import time
import json
import sys
import getopt
import statistics
import logging
import os
import ssl
from typing import Dict, List, Optional
from urllib.parse import urlparse


class AsyncHttpTrace:
    def __init__(self, url: str, tries: int = 1, output_file: Optional[str] = None,
                 concurrent_requests: int = 5, timeout: int = 30):
        self.url = url
        self.tries = tries
        self.output_file = output_file
        self.concurrent_requests = min(concurrent_requests, tries)
        self.timeout = timeout
        self.results = {}
        self.session = None

    async def create_session(self):
        """Create aiohttp session with optimized settings"""
        connector = aiohttp.TCPConnector(
            limit=self.concurrent_requests + 5,
            limit_per_host=self.concurrent_requests,
            enable_cleanup_closed=True,
            use_dns_cache=True,
            ssl=ssl.create_default_context()
        )

        timeout_config = aiohttp.ClientTimeout(
            total=self.timeout,
            connect=10,
            sock_read=10
        )

        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout_config,
            trust_env=True
        )

    async def close_session(self):
        """Clean up session"""
        if self.session:
            await self.session.close()

    async def measure_http_trace_single(self, request_id: int) -> Optional[Dict]:
        """Single HTTP trace measurement with detailed timing"""
        if not self.session:
            await self.create_session()

        trace_config = aiohttp.TraceConfig()
        timing_data = {}

        # Set up trace callbacks to collect timing information
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

        # Attach callbacks
        trace_config.on_request_start.append(on_request_start)
        trace_config.on_dns_resolvehost_start.append(on_dns_resolvehost_start)
        trace_config.on_dns_resolvehost_end.append(on_dns_resolvehost_end)
        trace_config.on_connection_create_start.append(on_connection_create_start)
        trace_config.on_connection_create_end.append(on_connection_create_end)
        trace_config.on_request_end.append(on_request_end)

        try:
            overall_start = time.perf_counter()

            async with self.session.get(
                self.url,
                trace=trace_config,
                allow_redirects=True
            ) as response:

                # Read response to ensure complete transfer
                content = await response.read()
                overall_end = time.perf_counter()

                # Calculate timing metrics
                result = {
                    'request_id': request_id,
                    'url_effective': str(response.url),
                    'http_code': response.status,
                    'content_length': len(content),
                    'time_total': overall_end - overall_start,
                }

                # Add detailed timing if available
                if 'dns_start' in timing_data and 'dns_end' in timing_data:
                    result['time_namelookup'] = timing_data['dns_end'] - timing_data['dns_start']

                if 'connect_start' in timing_data and 'connect_end' in timing_data:
                    result['time_connect'] = (timing_data['connect_end'] -
                                          timing_data['connect_start'])

                if 'request_start' in timing_data and 'request_end' in timing_data:
                    result['time_transfer'] = (timing_data['request_end'] -
                                           timing_data['request_start'])

                # Response headers info
                result['headers'] = dict(response.headers)
                result['redirect_count'] = len(response.history)

                return result

        except asyncio.TimeoutError:
            return {
                'request_id': request_id,
                'error': 'timeout',
                'time_total': self.timeout
            }
        except Exception as e:
            return {
                'request_id': request_id,
                'error': str(e),
                'time_total': 0
            }

    async def run_concurrent_tests(self) -> List[Dict]:
        """Run HTTP traces with controlled concurrency"""
        semaphore = asyncio.Semaphore(self.concurrent_requests)

        async def semaphore_wrapper(request_id):
            async with semaphore:
                return await self.measure_http_trace_single(request_id)

        # Create tasks for all requests
        tasks = [
            asyncio.create_task(semaphore_wrapper(i))
            for i in range(self.tries)
        ]

        # Execute with progress tracking
        results = []
        for i, task in enumerate(asyncio.as_completed(tasks), 1):
            result = await task
            results.append(result)
            if i % max(1, self.tries // 10) == 0:  # Progress updates
                logging.info(f"Completed {i}/{self.tries} requests")

        return results

    async def run_async(self):
        """Main async execution method"""
        await self.create_session()

        try:
            # Run the tests
            test_results = await self.run_concurrent_tests()

            # Filter successful results for statistics
            successful_results = [
                r for r in test_results
                if 'error' not in r and 'time_total' in r and r['time_total'] > 0
            ]

            error_results = [r for r in test_results if 'error' in r]

            # Build results
            self.results = {
                'test_config': {
                    'url': self.url,
                    'total_requests': self.tries,
                    'concurrent_requests': self.concurrent_requests,
                    'timeout': self.timeout
                },
                'details': test_results
            }

            # Calculate statistics if we have successful results
            if successful_results:
                times = [r['time_total'] for r in successful_results]
                self.results['summary'] = {
                    'successful_requests': len(successful_results),
                    'failed_requests': len(error_results),
                    'success_rate': len(successful_results) / self.tries * 100,
                    'min_time': min(times),
                    'max_time': max(times),
                    'mean_time': statistics.mean(times),
                    'median_time': statistics.median(times),
                    'std_dev': statistics.stdev(times) if len(times) > 1 else 0,
                    'all_times': times
                }

                # Add percentiles
                sorted_times = sorted(times)
                if len(sorted_times) > 0:
                    self.results['summary']['percentiles'] = {
                        'p50': sorted_times[int(len(sorted_times) * 0.5)],
                        'p90': sorted_times[int(len(sorted_times) * 0.9)],
                        'p95': sorted_times[int(len(sorted_times) * 0.95)],
                        'p99': sorted_times[int(len(sorted_times) * 0.99)]
                    }
            else:
                self.results['summary'] = {
                    'successful_requests': 0,
                    'failed_requests': len(error_results),
                    'success_rate': 0,
                    'error': 'No successful requests completed'
                }

            # Output results
            summary_json = json.dumps(self.results, indent=2, default=str)
            logging.info(
                f"HTTP Trace Results Summary:\n{json.dumps(self.results.get('summary', {}), indent=2)}")

            if self.output_file:
                with open(self.output_file, 'w') as f:
                    f.write(summary_json)
                logging.info(f"Results saved to {self.output_file}")

        finally:
            await self.close_session()

    def run(self):
        """Synchronous wrapper for async execution"""
        return asyncio.run(self.run_async())


def run_threaded_test(url: str, tries: int = 1, output_file: Optional[str] = None,
                      concurrent_requests: int = 5, timeout: int = 30) -> Dict:
    """Thread-safe wrapper for async HTTP trace"""
    trace = AsyncHttpTrace(url, tries, output_file, concurrent_requests, timeout)
    trace.run()
    return trace.results


def main(argv):
    url = ''
    tries = 1
    output_file = None
    concurrent_requests = 5
    timeout = 30

    try:
        opts, args = getopt.getopt(
            argv,
            "hu:t:o:c:T:",
            ["url=", "tries=", "output=", "concurrent=", "timeout="]
        )
    except getopt.GetoptError:
        logging.error(
            "Usage: python httptrace_async.py -u <URL> -t <TRIES> "
            "-o <OUTPUT_FILE> -c <CONCURRENT> -T <TIMEOUT>")
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print("Usage: python httptrace_async.py -u <URL> -t <TRIES> "
                  "-o <OUTPUT_FILE> -c <CONCURRENT> -T <TIMEOUT>")
            print("  -u, --url       URL to test (required)")
            print("  -t, --tries     Number of requests (default: 1)")
            print("  -o, --output    Output file for results")
            print("  -c, --concurrent Maximum concurrent requests "
                  "(default: 5)")
            print("  -T, --timeout   Request timeout in seconds "
                  "(default: 30)")
            sys.exit()
        elif opt in ("-u", "--url"):
            url = arg
        elif opt in ("-t", "--tries"):
            tries = int(arg)
        elif opt in ("-o", "--output"):
            output_file = arg
        elif opt in ("-c", "--concurrent"):
            concurrent_requests = int(arg)
        elif opt in ("-T", "--timeout"):
            timeout = int(arg)

    if not url:
        logging.error("URL is required. Usage: python httptrace_async.py "
                      "-u <URL> [OPTIONS]")
        sys.exit(2)

    # Validate URL
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        logging.error("Invalid URL format. URL must include scheme "
                      "(http:// or https://)")
        sys.exit(2)

    logging.info(
        f"Starting HTTP trace test: {url} ({tries} requests, "
        f"{concurrent_requests} concurrent)")

    http_trace = AsyncHttpTrace(url, tries, output_file, concurrent_requests, timeout)
    http_trace.run()

    # Print summary to stdout
    if http_trace.results and 'summary' in http_trace.results:
        summary = http_trace.results['summary']
        print(f"\n🚀 HTTP Trace Test Results:")
        print(f"URL: {url}")
        print(f"Successful: {summary.get('successful_requests', 0)}/{tries}")
        if 'mean_time' in summary:
            print(f"Average Response Time: "
              f"{summary['mean_time']*1000:.2f}ms")
            print(f"Min/Max: {summary['min_time']*1000:.2f}ms / "
                  f"{summary['max_time']*1000:.2f}ms")


if __name__ == "__main__":
    log_file = "httptrace_async.log"  # Use current directory for compatibility
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    main(sys.argv[1:])
