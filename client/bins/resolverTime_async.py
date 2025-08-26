#!/usr/bin/env python3

import asyncio
import time
import statistics
import logging
import json
import sys
import getopt
from typing import List, Dict, Optional
import dns.resolver
import dns.asyncresolver
import dns.rdatatype
from dataclasses import dataclass


@dataclass
class DNSQueryResult:
    """Single DNS query result"""
    query_time_ms: float
    success: bool
    response_data: Optional[List[str]] = None
    error: Optional[str] = None
    server: Optional[str] = None
    timestamp: float = 0.0


class AsyncResolverTime:
    """Async DNS resolver timing tool with performance improvements"""

    def __init__(self):
        self.domain = "google.com"
        self.record_type = "A"
        self.count = 3
        self.timeout = 5.0
        self.concurrent_queries = 5
        self.dns_servers = None  # Use system default
        self.output_file = None
        self.results: List[DNSQueryResult] = []

    def get_record_type_enum(self, record_type_str: str):
        """Convert string record type to dns.rdatatype enum"""
        record_types = {
            'A': dns.rdatatype.A,
            'AAAA': dns.rdatatype.AAAA,
            'CNAME': dns.rdatatype.CNAME,
            'MX': dns.rdatatype.MX,
            'NS': dns.rdatatype.NS,
            'TXT': dns.rdatatype.TXT,
            'SOA': dns.rdatatype.SOA,
            'PTR': dns.rdatatype.PTR,
            'SRV': dns.rdatatype.SRV
        }
        return record_types.get(record_type_str.upper(), dns.rdatatype.A)

    async def query_dns_async(self, query_id: int) -> DNSQueryResult:
        """Perform single async DNS query"""
        start_time = time.perf_counter()
        timestamp = start_time

        try:
            # Create async resolver
            resolver = dns.asyncresolver.Resolver()
            resolver.timeout = self.timeout
            resolver.lifetime = self.timeout

            # Set custom DNS servers if specified
            if self.dns_servers:
                resolver.nameservers = self.dns_servers

            # Perform the query
            record_type_enum = self.get_record_type_enum(self.record_type)

            try:
                response = await resolver.resolve(self.domain, record_type_enum)
                end_time = time.perf_counter()
                query_time = (end_time - start_time) * 1000  # Convert to ms

                # Extract response data
                response_data = []
                for rdata in response:
                    response_data.append(str(rdata))

                return DNSQueryResult(
                    query_time_ms=query_time,
                    success=True,
                    response_data=response_data,
                    server=str(response.nameserver) if hasattr(response, 'nameserver') else None,
                    timestamp=timestamp
                )

            except dns.resolver.NXDOMAIN:
                end_time = time.perf_counter()
                query_time = (end_time - start_time) * 1000
                return DNSQueryResult(
                    query_time_ms=query_time,
                    success=False,
                    error="NXDOMAIN - Domain does not exist",
                    timestamp=timestamp
                )

            except dns.resolver.NoAnswer:
                end_time = time.perf_counter()
                query_time = (end_time - start_time) * 1000
                return DNSQueryResult(
                    query_time_ms=query_time,
                    success=False,
                    error=f"No {self.record_type} record found",
                    timestamp=timestamp
                )

            except dns.resolver.Timeout:
                return DNSQueryResult(
                    query_time_ms=self.timeout * 1000,
                    success=False,
                    error="DNS query timeout",
                    timestamp=timestamp
                )

        except Exception as e:
            end_time = time.perf_counter()
            query_time = (end_time - start_time) * 1000
            return DNSQueryResult(
                query_time_ms=query_time,
                success=False,
                error=str(e),
                timestamp=timestamp
            )

    async def run_concurrent_queries(self) -> List[DNSQueryResult]:
        """Run DNS queries with controlled concurrency"""
        semaphore = asyncio.Semaphore(self.concurrent_queries)

        async def semaphore_wrapper(query_id):
            async with semaphore:
                return await self.query_dns_async(query_id)

        logging.info(f"Running {self.count} DNS queries for {self.domain} "
                     f"({self.record_type} record)")

        # Create tasks
        tasks = [
            asyncio.create_task(semaphore_wrapper(i))
            for i in range(self.count)
        ]

        # Execute with progress tracking
        results = []
        for i, task in enumerate(asyncio.as_completed(tasks), 1):
            result = await task
            results.append(result)

            # Log individual result
            if result.success:
                logging.debug(f"Query {i}: {result.query_time_ms:.2f}ms - "
                              f"{len(result.response_data or [])} records")
            else:
                logging.debug(f"Query {i}: Failed - {result.error}")

        return results

    def calculate_statistics(self, results: List[DNSQueryResult]) -> Dict:
        """Calculate comprehensive statistics"""
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]

        stats = {
            'domain': self.domain,
            'record_type': self.record_type,
            'total_queries': len(results),
            'successful_queries': len(successful_results),
            'failed_queries': len(failed_results),
            'success_rate_percent': (
                (len(successful_results) / len(results)) * 100
                if results else 0),
            'query_times': None,
            'errors': {}
        }

        # Timing statistics
        if successful_results:
            times = [r.query_time_ms for r in successful_results]
            stats['query_times'] = {
                'min_ms': min(times),
                'max_ms': max(times),
                'mean_ms': statistics.mean(times),
                'median_ms': statistics.median(times),
                'std_dev_ms': statistics.stdev(times) if len(times) > 1 else 0,
                'all_times': times
            }

            # Add percentiles for larger samples
            if len(times) >= 10:
                sorted_times = sorted(times)
                stats['query_times']['percentiles'] = {
                    'p90': sorted_times[int(len(sorted_times) * 0.9)],
                    'p95': sorted_times[int(len(sorted_times) * 0.95)],
                    'p99': sorted_times[int(len(sorted_times) * 0.99)]
                }

        # Error analysis
        if failed_results:
            error_counts = {}
            for result in failed_results:
                error = result.error or "Unknown error"
                error_counts[error] = error_counts.get(error, 0) + 1
            stats['errors'] = error_counts

        # Response data analysis
        if successful_results and successful_results[0].response_data:
            unique_responses = set()
            for result in successful_results:
                if result.response_data:
                    for response in result.response_data:
                        unique_responses.add(response)
            stats['unique_responses'] = list(unique_responses)

        return stats

    def save_results_to_file(self, results: List[DNSQueryResult], stats: Dict):
        """Save detailed results to JSON file"""
        if not self.output_file:
            return

        output_data = {
            'test_config': {
                'domain': self.domain,
                'record_type': self.record_type,
                'count': self.count,
                'timeout': self.timeout,
                'concurrent_queries': self.concurrent_queries,
                'dns_servers': self.dns_servers
            },
            'statistics': stats,
            'detailed_results': [
                {
                    'query_time_ms': r.query_time_ms,
                    'success': r.success,
                    'response_data': r.response_data,
                    'error': r.error,
                    'server': r.server,
                    'timestamp': r.timestamp
                }
                for r in results
            ]
        }

        try:
            with open(self.output_file, 'w') as f:
                json.dump(output_data, f, indent=2, default=str)
            logging.info(f"Results saved to {self.output_file}")
        except Exception as e:
            logging.error(f"Failed to save results: {e}")

    def print_summary(self, stats: Dict):
        """Print human-readable summary"""
        print(f"\n🔍 DNS Resolution Results for {stats['domain']} ({stats['record_type']} record)")
        print(f"{'='*60}")
        print(f"Total Queries: {stats['total_queries']}")
        print(f"Successful: {stats['successful_queries']}")
        print(f"Failed: {stats['failed_queries']}")
        print(f"Success Rate: {stats['success_rate_percent']:.1f}%")

        if stats['query_times']:
            qt = stats['query_times']
            print("\n⏱️  Response Times:")
            print(f"  Min: {qt['min_ms']:.2f}ms")
            print(f"  Max: {qt['max_ms']:.2f}ms")
            print(f"  Mean: {qt['mean_ms']:.2f}ms")
            print(f"  Median: {qt['median_ms']:.2f}ms")
            print(f"  Std Dev: {qt['std_dev_ms']:.2f}ms")

            if 'percentiles' in qt:
                p = qt['percentiles']
                print(f"  90th percentile: {p['p90']:.2f}ms")
                print(f"  95th percentile: {p['p95']:.2f}ms")
                print(f"  99th percentile: {p['p99']:.2f}ms")

        if stats.get('unique_responses'):
            print("\n📋 Resolved Addresses:")
            for response in stats['unique_responses'][:10]:  # Show first 10
                print(f"  {response}")
            if len(stats['unique_responses']) > 10:
                print(f"  ... and {len(stats['unique_responses']) - 10} more")

        if stats.get('errors'):
            print("\n❌ Errors:")
            for error, count in stats['errors'].items():
                print(f"  {error}: {count}")

    async def run_async(self):
        """Main async execution method"""
        try:
            # Run the DNS queries
            self.results = await self.run_concurrent_queries()

            # Calculate statistics
            stats = self.calculate_statistics(self.results)

            # Display results
            self.print_summary(stats)

            # Save to file if requested
            self.save_results_to_file(self.results, stats)

            return stats

        except Exception as e:
            logging.error(f"DNS resolution test failed: {e}")
            raise

    def run(self):
        """Synchronous wrapper for async execution"""
        return asyncio.run(self.run_async())


def run_threaded_dns_test(domain: str, record_type: str = "A", count: int = 3,
                          concurrent: int = 5, timeout: float = 5.0) -> Dict:
    """Thread-safe wrapper for async DNS resolution testing"""
    resolver = AsyncResolverTime()
    resolver.domain = domain
    resolver.record_type = record_type
    resolver.count = count
    resolver.concurrent_queries = concurrent
    resolver.timeout = timeout

    return resolver.run()


def main():
    """CLI interface"""
    # Default values
    domain = "google.com"
    record_type = "A"
    count = 3
    concurrent = 5
    timeout = 5.0
    dns_servers = None
    output_file = None
    log_level = logging.INFO

    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            "d:r:c:t:s:o:l:C:h",
            ["domain=", "record-type=", "count=", "timeout=", "servers=",
             "output=", "loglevel=", "concurrent=", "help"]
        )
    except getopt.GetoptError as err:
        print(f"Error: {err}")
        print("Usage: resolverTime_async.py -d <domain> [options]")
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-d", "--domain"):
            domain = arg
        elif opt in ("-r", "--record-type"):
            record_type = arg.upper()
        elif opt in ("-c", "--count"):
            count = int(arg)
        elif opt in ("-t", "--timeout"):
            timeout = float(arg)
        elif opt in ("-s", "--servers"):
            dns_servers = arg.split(",")
        elif opt in ("-o", "--output"):
            output_file = arg
        elif opt in ("-l", "--loglevel"):
            log_level = getattr(logging, arg.upper(), logging.INFO)
        elif opt in ("-C", "--concurrent"):
            concurrent = int(arg)
        elif opt in ("-h", "--help"):
            print("Async DNS Resolver Timing Tool")
            print("Usage: resolverTime_async.py -d <domain> [options]")
            print("Options:")
            print("  -d, --domain      Domain to resolve (required)")
            print("  -r, --record-type Record type (A, AAAA, CNAME, MX, etc. - default: A)")
            print("  -c, --count       Number of queries (default: 3)")
            print("  -C, --concurrent  Concurrent queries (default: 5)")
            print("  -t, --timeout     Query timeout in seconds (default: 5.0)")
            print("  -s, --servers     DNS servers (comma-separated)")
            print("  -o, --output      Output file for JSON results")
            print("  -l, --loglevel    Log level (DEBUG, INFO, WARNING, ERROR)")
            print("  -h, --help        Show this help")
            sys.exit(0)

    # Validate inputs
    if not domain:
        print("Error: Domain is required (-d option)")
        sys.exit(2)

    valid_types = ['A', 'AAAA', 'CNAME', 'MX', 'NS', 'TXT', 'SOA', 'PTR', 'SRV']
    if record_type not in valid_types:
        print(f"Error: Invalid record type. Valid types: {', '.join(valid_types)}")
        sys.exit(2)

    # Set up logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

    # Create and run resolver
    resolver = AsyncResolverTime()
    resolver.domain = domain
    resolver.record_type = record_type
    resolver.count = count
    resolver.concurrent_queries = concurrent
    resolver.timeout = timeout
    resolver.dns_servers = dns_servers
    resolver.output_file = output_file

    try:
        resolver.run()
    except KeyboardInterrupt:
        logging.info("Test interrupted by user")
    except Exception as e:
        logging.error(f"Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
