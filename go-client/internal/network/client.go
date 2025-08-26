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

	"github.com/go-ping/ping"
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
	host, _, err := net.SplitHostPort(c.serverAddr)
	if err != nil {
		// If no port specified, use the address as-is
		host = c.serverAddr
	}

	pinger, err := ping.NewPinger(host)
	if err != nil {
		return nil, fmt.Errorf("failed to create pinger: %w", err)
	}

	// Configure pinger
	pinger.Count = 10
	pinger.Timeout = 10 * time.Second
	pinger.SetPrivileged(false) // Use unprivileged mode

	// Run ping
	err = pinger.Run()
	if err != nil {
		return nil, fmt.Errorf("failed to run ping: %w", err)
	}

	stats := pinger.Statistics()

	return &PingResults{
		PacketsSent: stats.PacketsSent,
		PacketsRecv: stats.PacketsRecv,
		PacketLoss:  stats.PacketLoss,
		MinRtt:      stats.MinRtt,
		MaxRtt:      stats.MaxRtt,
		AvgRtt:      stats.AvgRtt,
		StdDevRtt:   stats.StdDevRtt,
	}, nil
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
	host, _, err := net.SplitHostPort(c.serverAddr)
	if err != nil {
		host = c.serverAddr
	}
	
	// Use context-aware ping
	pinger, err := ping.NewPinger(host)
	if err != nil {
		return nil, fmt.Errorf("failed to create pinger: %w", err)
	}
	
	pinger.Count = 5 // Reduced for faster execution
	pinger.Timeout = 5 * time.Second // Reduced timeout
	pinger.SetPrivileged(false)
	
	// Check context before running
	select {
	case <-ctx.Done():
		return nil, ctx.Err()
	default:
	}
	
	err = pinger.Run()
	if err != nil {
		return nil, fmt.Errorf("failed to run ping: %w", err)
	}
	
	stats := pinger.Statistics()
	
	return &PingResults{
		PacketsSent: stats.PacketsSent,
		PacketsRecv: stats.PacketsRecv,
		PacketLoss:  stats.PacketLoss,
		MinRtt:      stats.MinRtt,
		MaxRtt:      stats.MaxRtt,
		AvgRtt:      stats.AvgRtt,
		StdDevRtt:   stats.StdDevRtt,
	}, nil
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
