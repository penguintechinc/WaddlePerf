#!/usr/bin/env python3

import asyncio
import time
import string
import random
import signal
import os
import getopt
import json
import logging
import base64
import socket
import sys
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass


@dataclass
class UDPPingResult:
    """Single UDP ping result"""
    seq: int
    rtt_ms: Optional[float]
    success: bool
    error: Optional[str] = None
    timestamp: float = 0.0


class AsyncUDPPing:
    """Async/threaded UDP ping implementation with improved performance"""
    
    def __init__(self, dst_host: str = "127.0.0.1", port: int = 2000):
        self.dst_host = dst_host
        self.port = port
        self.interval_ms = 1000
        self.packet_len = 64
        self.ping_count = 4
        self.output_file = "udpping_async_results.json"
        self.ttl = 64
        self.token = None
        self.timeout_ms = 5000
        self.concurrent_pings = 1  # UDP is generally sequential
        
        # Statistics
        self.results: List[UDPPingResult] = []
        self._running = True
        
    def signal_handler(self, signum, frame):
        """Handle interrupt signal"""
        self._running = False
        logging.info("Interrupt received, finishing current tests...")
    
    def random_string(self, length: int) -> str:
        """Generate random string for payload"""
        return ''.join(random.choice(string.ascii_letters + string.digits) 
                      for _ in range(length))
    
    async def send_udp_ping_async(self, seq: int) -> UDPPingResult:
        """Send single UDP ping with async socket operations"""
        loop = asyncio.get_event_loop()
        
        # Create socket in thread pool to avoid blocking
        def create_socket():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_IP, socket.IP_TTL, self.ttl)
            sock.settimeout(self.timeout_ms / 1000.0)
            return sock
        
        with ThreadPoolExecutor(max_workers=1) as executor:
            try:
                sock = await loop.run_in_executor(executor, create_socket)
                
                # Prepare payload
                payload = self.random_string(self.packet_len).encode()
                if self.token:
                    encoded_token = base64.b64encode(self.token.encode()).decode()
                    payload = f"{encoded_token}:{payload.decode()}".encode()
                
                # Send packet
                send_time = time.perf_counter()
                await loop.run_in_executor(
                    executor, 
                    lambda: sock.sendto(payload, (self.dst_host, self.port))
                )
                
                # Wait for response with timeout
                deadline = send_time + (self.timeout_ms / 1000.0)
                
                while time.perf_counter() < deadline:
                    try:
                        timeout_remaining = deadline - time.perf_counter()
                        if timeout_remaining <= 0:
                            break
                        
                        sock.settimeout(timeout_remaining)
                        response, addr = await loop.run_in_executor(
                            executor,
                            lambda: sock.recvfrom(1024)
                        )
                        
                        if addr[0] == self.dst_host and addr[1] == self.port:
                            recv_time = time.perf_counter()
                            rtt = (recv_time - send_time) * 1000  # Convert to ms
                            
                            return UDPPingResult(
                                seq=seq,
                                rtt_ms=rtt,
                                success=True,
                                timestamp=send_time
                            )
                    
                    except socket.timeout:
                        break
                    except Exception as e:
                        return UDPPingResult(
                            seq=seq,
                            rtt_ms=None,
                            success=False,
                            error=str(e),
                            timestamp=send_time
                        )
                
                # Timeout
                return UDPPingResult(
                    seq=seq,
                    rtt_ms=None,
                    success=False,
                    error="timeout",
                    timestamp=send_time
                )
                
            except Exception as e:
                return UDPPingResult(
                    seq=seq,
                    rtt_ms=None,
                    success=False,
                    error=str(e),
                    timestamp=time.perf_counter()
                )
            finally:
                if 'sock' in locals():
                    sock.close()
    
    async def run_async_pings(self) -> List[UDPPingResult]:
        """Execute UDP pings with proper interval timing"""
        logging.info(f"UDPping {self.dst_host} via port {self.port} "
                    f"with {self.packet_len} bytes of payload")
        
        results = []
        
        for seq in range(self.ping_count):
            if not self._running:
                logging.info("Stopping due to interrupt")
                break
            
            # Send ping
            result = await self.send_udp_ping_async(seq)
            results.append(result)
            
            # Log result
            if result.success and result.rtt_ms is not None:
                logging.info(f"Reply from {self.dst_host} seq={seq} "
                           f"time={result.rtt_ms:.2f} ms")
            else:
                logging.warning(f"Request {seq} failed: {result.error or 'timeout'}")
            
            # Wait for interval (except on last ping)
            if seq < self.ping_count - 1 and self._running:
                await asyncio.sleep(self.interval_ms / 1000.0)
        
        return results
    
    def calculate_statistics(self, results: List[UDPPingResult]) -> Dict:
        """Calculate comprehensive statistics from ping results"""
        successful_results = [r for r in results if r.success and r.rtt_ms is not None]
        failed_results = [r for r in results if not r.success]
        
        stats = {
            'packets_transmitted': len(results),
            'packets_received': len(successful_results),
            'packets_lost': len(failed_results),
            'packet_loss_percent': (len(failed_results) / len(results)) * 100 if results else 0,
            'test_duration_seconds': 0,
            'rtt_stats': None
        }
        
        if results:
            start_time = min(r.timestamp for r in results)
            end_time = max(r.timestamp for r in results)
            stats['test_duration_seconds'] = end_time - start_time
        
        if successful_results:
            rtts = [r.rtt_ms for r in successful_results]
            stats['rtt_stats'] = {
                'min_ms': min(rtts),
                'max_ms': max(rtts),
                'avg_ms': sum(rtts) / len(rtts),
                'count': len(rtts),
                'all_rtts': rtts
            }
        
        return stats
    
    def write_results_to_json(self, results: List[UDPPingResult], stats: Dict):
        """Write detailed results to JSON file"""
        output_data = {
            'test_config': {
                'dst_host': self.dst_host,
                'port': self.port,
                'packet_len': self.packet_len,
                'interval_ms': self.interval_ms,
                'ping_count': self.ping_count,
                'timeout_ms': self.timeout_ms,
                'ttl': self.ttl
            },
            'statistics': stats,
            'detailed_results': [
                {
                    'seq': r.seq,
                    'rtt_ms': r.rtt_ms,
                    'success': r.success,
                    'error': r.error,
                    'timestamp': r.timestamp
                }
                for r in results
            ]
        }
        
        try:
            with open(self.output_file, 'w') as f:
                json.dump(output_data, f, indent=2)
            logging.info(f"Results saved to {self.output_file}")
        except Exception as e:
            logging.error(f"Failed to save results to {self.output_file}: {e}")
    
    def print_summary(self, stats: Dict):
        """Print human-readable summary"""
        print(f"\n--- UDP ping statistics ---")
        print(f"{stats['packets_transmitted']} packets transmitted, "
              f"{stats['packets_received']} received, "
              f"{stats['packet_loss_percent']:.1f}% packet loss")
        
        if stats['rtt_stats']:
            rtt = stats['rtt_stats']
            print(f"rtt min/avg/max = {rtt['min_ms']:.2f}/"
                  f"{rtt['avg_ms']:.2f}/{rtt['max_ms']:.2f} ms")
    
    async def run_async(self):
        """Main async execution method"""
        # Set up signal handling
        signal.signal(signal.SIGINT, self.signal_handler)
        
        try:
            # Run the ping tests
            self.results = await self.run_async_pings()
            
            # Calculate and display statistics
            stats = self.calculate_statistics(self.results)
            self.print_summary(stats)
            
            # Save results to file
            self.write_results_to_json(self.results, stats)
            
            return stats
            
        except Exception as e:
            logging.error(f"UDP ping test failed: {e}")
            raise
    
    def run(self):
        """Synchronous wrapper for async execution"""
        return asyncio.run(self.run_async())


def run_threaded_udp_ping(dst_host: str, port: int = 2000, 
                         count: int = 4, interval_ms: int = 1000,
                         packet_len: int = 64, timeout_ms: int = 5000) -> Dict:
    """Thread-safe wrapper for async UDP ping"""
    ping = AsyncUDPPing(dst_host, port)
    ping.ping_count = count
    ping.interval_ms = interval_ms
    ping.packet_len = packet_len
    ping.timeout_ms = timeout_ms
    
    return ping.run()


def main():
    """CLI interface for async UDP ping"""
    # Default values
    dst_host = "127.0.0.1"
    port = 2000
    count = 4
    interval_ms = 1000
    packet_len = 64
    output_file = "udpping_async_results.json"
    ttl = 64
    log_level = logging.INFO
    token = None
    timeout_ms = 5000
    
    try:
        opts, args = getopt.getopt(
            sys.argv[1:], 
            "a:c:i:p:f:t:l:k:T:s:h", 
            ["address=", "count=", "interval=", "port=", "file=", "ttl=", 
             "loglevel=", "token=", "timeout=", "size=", "help"]
        )
    except getopt.GetoptError as err:
        print(f"Error: {err}")
        print("Usage: udpping_async.py -a <address> [options]")
        sys.exit(2)
    
    for opt, arg in opts:
        if opt in ("-a", "--address"):
            dst_host = arg
        elif opt in ("-c", "--count"):
            count = int(arg)
        elif opt in ("-i", "--interval"):
            interval_ms = int(arg)
        elif opt in ("-p", "--port"):
            port = int(arg)
        elif opt in ("-f", "--file"):
            output_file = arg
        elif opt in ("-t", "--ttl"):
            ttl = int(arg)
        elif opt in ("-l", "--loglevel"):
            log_level = getattr(logging, arg.upper(), logging.INFO)
        elif opt in ("-k", "--token"):
            token = arg
        elif opt in ("-T", "--timeout"):
            timeout_ms = int(arg)
        elif opt in ("-s", "--size"):
            packet_len = int(arg)
        elif opt in ("-h", "--help"):
            print("Async UDP Ping Tool")
            print("Usage: udpping_async.py -a <address> [options]")
            print("Options:")
            print("  -a, --address    Destination host (required)")
            print("  -p, --port       Destination port (default: 2000)")
            print("  -c, --count      Number of pings (default: 4)")
            print("  -i, --interval   Interval between pings in ms (default: 1000)")
            print("  -s, --size       Packet size in bytes (default: 64)")
            print("  -T, --timeout    Timeout per ping in ms (default: 5000)")
            print("  -t, --ttl        TTL value (default: 64)")
            print("  -f, --file       Output file (default: udpping_async_results.json)")
            print("  -k, --token      Authentication token")
            print("  -l, --loglevel   Log level (DEBUG, INFO, WARNING, ERROR)")
            print("  -h, --help       Show this help")
            sys.exit(0)
    
    # Validate inputs
    if not dst_host:
        print("Error: Destination host is required (-a option)")
        sys.exit(2)
    
    if packet_len < 5:
        print("Error: Packet size must be >= 5 bytes")
        sys.exit(2)
    
    if interval_ms < 50:
        print("Error: Interval must be >= 50ms")
        sys.exit(2)
    
    # Set up logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Create and run UDP ping
    ping = AsyncUDPPing(dst_host, port)
    ping.ping_count = count
    ping.interval_ms = interval_ms
    ping.packet_len = packet_len
    ping.output_file = output_file
    ping.ttl = ttl
    ping.token = token
    ping.timeout_ms = timeout_ms
    
    try:
        ping.run()
    except KeyboardInterrupt:
        logging.info("Test interrupted by user")
    except Exception as e:
        logging.error(f"Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()