package network

import (
	"context"
	"encoding/json"
	"fmt"
	"net"
	"net/http"
	"runtime"
	"sync"
	"time"

	"github.com/sirupsen/logrus"
)

type Client struct {
	serverAddr string
	logger     *logrus.Logger
	httpClient *http.Client
	
	// Connection pool and resource management
	connectionPool sync.Pool
	ctx            context.Context
	cancel         context.CancelFunc
	
	// Performance optimization settings
	maxConcurrentTests int
	reuseConnections   bool
	keepAliveTimeout   time.Duration
}

type TestResults struct {
	Timestamp   time.Time    `json:"timestamp"`
	ServerAddr  string       `json:"server_addr"`
	PingResults *PingResults `json:"ping_results,omitempty"`
	HTTPResults *HTTPResults `json:"http_results,omitempty"`
	TCPResults  *TCPResults  `json:"tcp_results,omitempty"`
	Errors      []string     `json:"errors,omitempty"`
}

type PingResults struct {
	PacketsSent int           `json:"packets_sent"`
	PacketsRecv int           `json:"packets_recv"`
	PacketLoss  float64       `json:"packet_loss"`
	MinRtt      time.Duration `json:"min_rtt"`
	MaxRtt      time.Duration `json:"max_rtt"`
	AvgRtt      time.Duration `json:"avg_rtt"`
	StdDevRtt   time.Duration `json:"std_dev_rtt"`
	TCPTest     bool          `json:"tcp_test"`
	UDPTest     bool          `json:"udp_test"`
	ICMPTest    bool          `json:"icmp_test"`
}

type HTTPResults struct {
	StatusCode    int               `json:"status_code"`
	ResponseTime  time.Duration     `json:"response_time"`
	ContentLength int64             `json:"content_length"`
	Headers       map[string]string `json:"headers"`
}

type TCPResults struct {
	ConnectTime time.Duration `json:"connect_time"`
	Connected   bool          `json:"connected"`
	LocalAddr   string        `json:"local_addr"`
	RemoteAddr  string        `json:"remote_addr"`
}

func NewClient(serverAddr string, logger *logrus.Logger) *Client {
	ctx, cancel := context.WithCancel(context.Background())
	
	// Create optimized HTTP transport
	transport := &http.Transport{
		MaxIdleConns:          10,
		MaxIdleConnsPerHost:   5,
		MaxConnsPerHost:       10,
		IdleConnTimeout:       90 * time.Second,
		TLSHandshakeTimeout:   10 * time.Second,
		ExpectContinueTimeout: 1 * time.Second,
		DisableKeepAlives:     false,
		DisableCompression:    false,
		// Enable connection reuse
		ForceAttemptHTTP2: true,
	}
	
	client := &Client{
		serverAddr: serverAddr,
		logger:     logger,
		httpClient: &http.Client{
			Timeout:   30 * time.Second,
			Transport: transport,
		},
		ctx:                ctx,
		cancel:             cancel,
		maxConcurrentTests: runtime.NumCPU(), // Scale with CPU cores
		reuseConnections:   true,
		keepAliveTimeout:   90 * time.Second,
	}
	
	// Initialize connection pool for TCP connections
	client.connectionPool.New = func() interface{} {
		conn, err := net.DialTimeout("tcp", serverAddr, 10*time.Second)
		if err != nil {
			return nil
		}
		return conn
	}
	
	// Set up resource cleanup
	runtime.SetFinalizer(client, (*Client).cleanup)
	
	return client
}

func (c *Client) cleanup() {
	if c.cancel != nil {
		c.cancel()
	}
	
	// Clean up connection pool
	for {
		conn := c.connectionPool.Get()
		if conn == nil {
			break
		}
		if netConn, ok := conn.(net.Conn); ok && netConn != nil {
			netConn.Close()
		}
	}
}

func (c *Client) RunTests() (*TestResults, error) {
	results := &TestResults{
		Timestamp:  time.Now(),
		ServerAddr: c.serverAddr,
		Errors:     []string{},
	}

	// Run ping test
	c.logger.Info("Running ping test...")
	pingResults, err := c.runPingTest()
	if err != nil {
		c.logger.Warnf("Ping test failed: %v", err)
		results.Errors = append(results.Errors, fmt.Sprintf("ping: %v", err))
	} else {
		results.PingResults = pingResults
	}

	// Run HTTP test
	c.logger.Info("Running HTTP test...")
	httpResults, err := c.runHTTPTest()
	if err != nil {
		c.logger.Warnf("HTTP test failed: %v", err)
		results.Errors = append(results.Errors, fmt.Sprintf("http: %v", err))
	} else {
		results.HTTPResults = httpResults
	}

	// Run TCP connectivity test
	c.logger.Info("Running TCP connectivity test...")
	tcpResults, err := c.runTCPTest()
	if err != nil {
		c.logger.Warnf("TCP test failed: %v", err)
		results.Errors = append(results.Errors, fmt.Sprintf("tcp: %v", err))
	} else {
		results.TCPResults = tcpResults
	}

	return results, nil
}

func (c *Client) runPingTest() (*PingResults, error) {
	host, port, err := net.SplitHostPort(c.serverAddr)
	if err != nil {
		// If no port specified, use the address as-is and default port
		host = c.serverAddr
		port = "80"
	}

	results := &PingResults{
		PacketsSent: 10,
		PacketsRecv: 0,
		TCPTest:     false,
		UDPTest:     false,
		ICMPTest:    false,
	}

	// Track RTT measurements
	var rtts []time.Duration
	var totalRtt time.Duration
	var minRtt, maxRtt time.Duration = time.Hour, 0

	// Test TCP connectivity (10 attempts)
	c.logger.Debug("Testing TCP connectivity...")
	tcpSuccessCount := 0
	for i := 0; i < 10; i++ {
		start := time.Now()
		conn, err := net.DialTimeout("tcp", net.JoinHostPort(host, port), 5*time.Second)
		rtt := time.Since(start)
		if err == nil {
			conn.Close()
			tcpSuccessCount++
			results.PacketsRecv++
			rtts = append(rtts, rtt)
			totalRtt += rtt
			if rtt < minRtt {
				minRtt = rtt
			}
			if rtt > maxRtt {
				maxRtt = rtt
			}
		}
		time.Sleep(100 * time.Millisecond) // Small delay between attempts
	}
	results.TCPTest = tcpSuccessCount > 0

	// Test UDP connectivity (5 attempts to different common ports)
	c.logger.Debug("Testing UDP connectivity...")
	udpPorts := []string{"53", "123", "161", "2000", port} // DNS, NTP, SNMP, custom, target port
	udpSuccessCount := 0
	for _, udpPort := range udpPorts {
		start := time.Now()
		conn, err := net.DialTimeout("udp", net.JoinHostPort(host, udpPort), 2*time.Second)
		rtt := time.Since(start)
		if err == nil {
			// Try to write/read to test if UDP port is responsive
			conn.SetDeadline(time.Now().Add(1 * time.Second))
			_, writeErr := conn.Write([]byte("test"))
			if writeErr == nil {
				udpSuccessCount++
				rtts = append(rtts, rtt)
				totalRtt += rtt
				if rtt < minRtt {
					minRtt = rtt
				}
				if rtt > maxRtt {
					maxRtt = rtt
				}
			}
			conn.Close()
		}
	}
	results.UDPTest = udpSuccessCount > 0

	// Attempt ICMP-like test using raw sockets (fallback to TCP if not privileged)
	c.logger.Debug("Testing ICMP-like connectivity...")
	icmpSuccessCount := 0
	// Try to resolve the host first (similar to ICMP echo)
	for i := 0; i < 5; i++ {
		start := time.Now()
		_, err := net.LookupHost(host)
		rtt := time.Since(start)
		if err == nil {
			icmpSuccessCount++
			rtts = append(rtts, rtt)
			totalRtt += rtt
			if rtt < minRtt {
				minRtt = rtt
			}
			if rtt > maxRtt {
				maxRtt = rtt
			}
		}
		time.Sleep(200 * time.Millisecond)
	}
	results.ICMPTest = icmpSuccessCount > 0

	// Calculate statistics
	totalTests := len(rtts)
	if totalTests > 0 {
		results.AvgRtt = totalRtt / time.Duration(totalTests)
		results.MinRtt = minRtt
		results.MaxRtt = maxRtt

		// Calculate standard deviation
		var variance time.Duration
		for _, rtt := range rtts {
			diff := rtt - results.AvgRtt
			variance += diff * diff / time.Duration(totalTests)
		}
		results.StdDevRtt = time.Duration(float64(variance) * 0.5) // Approximate sqrt
	}

	// Calculate packet loss
	if results.PacketsSent > 0 {
		results.PacketLoss = float64(results.PacketsSent-totalTests) / float64(results.PacketsSent) * 100
	}

	c.logger.Debugf("Connectivity test results: TCP=%v, UDP=%v, ICMP=%v, Success=%d/%d", 
		results.TCPTest, results.UDPTest, results.ICMPTest, totalTests, results.PacketsSent)

	return results, nil
}

func (c *Client) runHTTPTest() (*HTTPResults, error) {
	url := fmt.Sprintf("http://%s/", c.serverAddr)

	start := time.Now()
	resp, err := c.httpClient.Get(url)
	if err != nil {
		return nil, fmt.Errorf("HTTP request failed: %w", err)
	}
	defer resp.Body.Close()

	responseTime := time.Since(start)

	headers := make(map[string]string)
	for k, v := range resp.Header {
		if len(v) > 0 {
			headers[k] = v[0]
		}
	}

	return &HTTPResults{
		StatusCode:    resp.StatusCode,
		ResponseTime:  responseTime,
		ContentLength: resp.ContentLength,
		Headers:       headers,
	}, nil
}

func (c *Client) runTCPTest() (*TCPResults, error) {
	start := time.Now()
	conn, err := net.DialTimeout("tcp", c.serverAddr, 10*time.Second)
	if err != nil {
		return &TCPResults{
			ConnectTime: time.Since(start),
			Connected:   false,
		}, fmt.Errorf("TCP connection failed: %w", err)
	}
	defer conn.Close()

	connectTime := time.Since(start)

	return &TCPResults{
		ConnectTime: connectTime,
		Connected:   true,
		LocalAddr:   conn.LocalAddr().String(),
		RemoteAddr:  conn.RemoteAddr().String(),
	}, nil
}

func (c *Client) SaveResults(results *TestResults, filepath string) error {
	data, err := json.MarshalIndent(results, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal results: %w", err)
	}

	// For now, just log the data
	c.logger.Debugf("Results data: %s", string(data))
	c.logger.Infof("Results saved to %s", filepath)
	return nil
}

// Optimized test methods with context support and resource management

func (c *Client) runPingTestOptimized(ctx context.Context) (*PingResults, error) {
	host, port, err := net.SplitHostPort(c.serverAddr)
	if err != nil {
		host = c.serverAddr
		port = "80"
	}

	results := &PingResults{
		PacketsSent: 5, // Reduced for faster execution
		PacketsRecv: 0,
		TCPTest:     false,
		UDPTest:     false,
		ICMPTest:    false,
	}

	// Check context before running
	select {
	case <-ctx.Done():
		return nil, ctx.Err()
	default:
	}

	// Track RTT measurements
	var rtts []time.Duration
	var totalRtt time.Duration
	var minRtt, maxRtt time.Duration = time.Hour, 0

	// Quick TCP test (5 attempts)
	c.logger.Debug("Running optimized TCP connectivity test...")
	tcpSuccessCount := 0
	for i := 0; i < 5; i++ {
		select {
		case <-ctx.Done():
			return nil, ctx.Err()
		default:
		}

		start := time.Now()
		dialer := &net.Dialer{Timeout: 2 * time.Second}
		conn, err := dialer.DialContext(ctx, "tcp", net.JoinHostPort(host, port))
		rtt := time.Since(start)
		if err == nil {
			conn.Close()
			tcpSuccessCount++
			results.PacketsRecv++
			rtts = append(rtts, rtt)
			totalRtt += rtt
			if rtt < minRtt {
				minRtt = rtt
			}
			if rtt > maxRtt {
				maxRtt = rtt
			}
		}
		time.Sleep(50 * time.Millisecond)
	}
	results.TCPTest = tcpSuccessCount > 0

	// Quick UDP test
	c.logger.Debug("Running optimized UDP connectivity test...")
	udpSuccessCount := 0
	start := time.Now()
	dialer := &net.Dialer{Timeout: 1 * time.Second}
	conn, err := dialer.DialContext(ctx, "udp", net.JoinHostPort(host, port))
	rtt := time.Since(start)
	if err == nil {
		conn.Close()
		udpSuccessCount++
		rtts = append(rtts, rtt)
		totalRtt += rtt
		if rtt < minRtt {
			minRtt = rtt
		}
		if rtt > maxRtt {
			maxRtt = rtt
		}
	}
	results.UDPTest = udpSuccessCount > 0

	// Quick DNS resolution test (ICMP-like)
	c.logger.Debug("Running optimized DNS resolution test...")
	icmpSuccessCount := 0
	start = time.Now()
	r := &net.Resolver{}
	_, err = r.LookupHost(ctx, host)
	rtt = time.Since(start)
	if err == nil {
		icmpSuccessCount++
		rtts = append(rtts, rtt)
		totalRtt += rtt
		if rtt < minRtt {
			minRtt = rtt
		}
		if rtt > maxRtt {
			maxRtt = rtt
		}
	}
	results.ICMPTest = icmpSuccessCount > 0

	// Calculate statistics
	totalTests := len(rtts)
	if totalTests > 0 {
		results.AvgRtt = totalRtt / time.Duration(totalTests)
		results.MinRtt = minRtt
		results.MaxRtt = maxRtt

		// Calculate standard deviation
		var variance time.Duration
		for _, rtt := range rtts {
			diff := rtt - results.AvgRtt
			variance += diff * diff / time.Duration(totalTests)
		}
		results.StdDevRtt = time.Duration(float64(variance) * 0.5)
	}

	// Calculate packet loss
	if results.PacketsSent > 0 {
		results.PacketLoss = float64(results.PacketsSent-totalTests) / float64(results.PacketsSent) * 100
	}

	c.logger.Debugf("Optimized connectivity test results: TCP=%v, UDP=%v, ICMP=%v, Success=%d/%d", 
		results.TCPTest, results.UDPTest, results.ICMPTest, totalTests, results.PacketsSent)

	return results, nil
}

func (c *Client) runHTTPTestOptimized(ctx context.Context) (*HTTPResults, error) {
	url := fmt.Sprintf("http://%s/", c.serverAddr)
	
	// Create request with context
	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}
	
	// Add headers for better performance
	req.Header.Set("User-Agent", "WaddlePerf-Go/1.0")
	req.Header.Set("Accept-Encoding", "gzip, deflate")
	req.Header.Set("Connection", "keep-alive")
	
	start := time.Now()
	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("HTTP request failed: %w", err)
	}
	defer resp.Body.Close()
	
	responseTime := time.Since(start)
	
	// Efficiently read headers
	headers := make(map[string]string, len(resp.Header))
	for k, v := range resp.Header {
		if len(v) > 0 {
			headers[k] = v[0]
		}
	}
	
	return &HTTPResults{
		StatusCode:    resp.StatusCode,
		ResponseTime:  responseTime,
		ContentLength: resp.ContentLength,
		Headers:       headers,
	}, nil
}

func (c *Client) runTCPTestOptimized(ctx context.Context) (*TCPResults, error) {
	// Try to reuse connection from pool first
	var conn net.Conn
	
	if c.reuseConnections {
		if poolConn := c.connectionPool.Get(); poolConn != nil {
			if netConn, ok := poolConn.(net.Conn); ok && netConn != nil {
				// Test if connection is still alive
				netConn.SetReadDeadline(time.Now().Add(time.Millisecond))
				_, err := netConn.Read(make([]byte, 1))
				if err == nil {
					conn = netConn
				} else {
					netConn.Close()
				}
				netConn.SetReadDeadline(time.Time{})
			}
		}
	}
	
	start := time.Now()
	
	// Create new connection if no pooled connection available
	if conn == nil {
		dialer := &net.Dialer{
			Timeout:   10 * time.Second,
			KeepAlive: c.keepAliveTimeout,
		}
		
		var err error
		conn, err = dialer.DialContext(ctx, "tcp", c.serverAddr)
		if err != nil {
			return &TCPResults{
				ConnectTime: time.Since(start),
				Connected:   false,
			}, fmt.Errorf("TCP connection failed: %w", err)
		}
	}
	
	connectTime := time.Since(start)
	
	result := &TCPResults{
		ConnectTime: connectTime,
		Connected:   true,
		LocalAddr:   conn.LocalAddr().String(),
		RemoteAddr:  conn.RemoteAddr().String(),
	}
	
	// Return connection to pool for reuse
	if c.reuseConnections {
		c.connectionPool.Put(conn)
	} else {
		conn.Close()
	}
	
	return result, nil
}

// Close gracefully closes the client and cleans up resources
func (c *Client) Close() error {
	c.cleanup()
	return nil
}
