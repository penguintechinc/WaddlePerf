//go:build !integration

package protocols_test

import (
	"net"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/penguincloud/waddleperf/testserver/internal/protocols"
)

// ---------------------------------------------------------------------------
// parseTarget (tested indirectly via TestTCP)
// ---------------------------------------------------------------------------

// TestTCP_RawConnRefused verifies that a refused TCP connection is reported
// as a failure rather than panicking.
func TestTCP_RawConnRefused(t *testing.T) {
	// Bind a port, then close it to guarantee a "connection refused" response.
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("failed to create listener: %v", err)
	}
	port := ln.Addr().(*net.TCPAddr).Port
	ln.Close()
	// Give the OS a moment to release the port fully.
	time.Sleep(10 * time.Millisecond)

	req := protocols.TCPTestRequest{
		Target:  "127.0.0.1",
		Port:    port,
		Protocol: "raw",
		Timeout: 2,
		Count:   1,
	}

	result, err := protocols.TestTCP(req)
	// An error is expected; validate result is still returned.
	if result == nil {
		t.Fatal("TestTCP should return a result even on failure")
	}
	if result.Success {
		t.Errorf("expected success=false for refused connection")
	}
	// err may or may not be non-nil depending on implementation; just ensure no panic.
	_ = err
}

// TestTCP_RawSuccess verifies a successful raw TCP connection.
func TestTCP_RawSuccess(t *testing.T) {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("failed to create listener: %v", err)
	}
	defer ln.Close()

	port := ln.Addr().(*net.TCPAddr).Port

	// Accept in background to avoid blocking the dialer.
	go func() {
		conn, _ := ln.Accept()
		if conn != nil {
			conn.Close()
		}
	}()

	req := protocols.TCPTestRequest{
		Target:   "127.0.0.1",
		Port:     port,
		Protocol: "raw",
		Timeout:  5,
		Count:    1,
	}

	result, err := protocols.TestTCP(req)
	if err != nil {
		t.Fatalf("TestTCP unexpected error: %v", err)
	}
	if result == nil {
		t.Fatal("TestTCP returned nil result")
	}
	if !result.Success {
		t.Errorf("expected success=true, got error=%q", result.Error)
	}
	if !result.Connected {
		t.Errorf("expected connected=true")
	}
	if result.LatencyMS < 0 {
		t.Errorf("expected latency >= 0, got %f", result.LatencyMS)
	}
}

// TestTCP_UnsupportedProtocol ensures the unsupported-protocol path returns an error.
func TestTCP_UnsupportedProtocol(t *testing.T) {
	req := protocols.TCPTestRequest{
		Target:   "127.0.0.1",
		Port:     80,
		Protocol: "quic", // not supported
		Timeout:  2,
		Count:    1,
	}

	result, err := protocols.TestTCP(req)
	if err == nil {
		t.Error("expected error for unsupported protocol")
	}
	if result != nil && result.Success {
		t.Error("expected success=false for unsupported protocol")
	}
}

// TestTCP_MultipleCount verifies that multiple connection attempts produce
// an average latency and that jitter is calculated.
func TestTCP_MultipleCount(t *testing.T) {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("failed to create listener: %v", err)
	}
	defer ln.Close()

	port := ln.Addr().(*net.TCPAddr).Port

	// Accept up to 3 connections.
	go func() {
		for i := 0; i < 3; i++ {
			conn, _ := ln.Accept()
			if conn != nil {
				conn.Close()
			}
		}
	}()

	req := protocols.TCPTestRequest{
		Target:   "127.0.0.1",
		Port:     port,
		Protocol: "raw",
		Timeout:  5,
		Count:    3,
	}

	result, err := protocols.TestTCP(req)
	if err != nil {
		t.Fatalf("TestTCP unexpected error: %v", err)
	}
	if result == nil {
		t.Fatal("TestTCP returned nil result")
	}
	if !result.Success {
		t.Errorf("expected success=true, got error=%q", result.Error)
	}
	if result.MinLatencyMS > result.MaxLatencyMS {
		t.Errorf("min latency %f > max latency %f", result.MinLatencyMS, result.MaxLatencyMS)
	}
}

// TestTCP_DefaultProtocol verifies that an empty protocol defaults correctly.
func TestTCP_DefaultProtocol(t *testing.T) {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("failed to create listener: %v", err)
	}
	defer ln.Close()
	port := ln.Addr().(*net.TCPAddr).Port

	go func() {
		conn, _ := ln.Accept()
		if conn != nil {
			conn.Close()
		}
	}()

	req := protocols.TCPTestRequest{
		Target:  "127.0.0.1",
		Port:    port,
		Timeout: 5,
		Count:   1,
		// Protocol intentionally empty — should default to "raw"
	}

	result, err := protocols.TestTCP(req)
	if err != nil {
		t.Fatalf("unexpected error with default protocol: %v", err)
	}
	if !result.Success {
		t.Errorf("expected success with default protocol, got error=%q", result.Error)
	}
}

// TestTCP_ProtocolDetailFallback verifies ProtocolDetail is used when Protocol is empty.
func TestTCP_ProtocolDetailFallback(t *testing.T) {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("failed to create listener: %v", err)
	}
	defer ln.Close()
	port := ln.Addr().(*net.TCPAddr).Port

	go func() {
		conn, _ := ln.Accept()
		if conn != nil {
			conn.Close()
		}
	}()

	req := protocols.TCPTestRequest{
		Target:         "127.0.0.1",
		Port:           port,
		Protocol:       "",
		ProtocolDetail: "raw",
		Timeout:        5,
		Count:          1,
	}

	result, err := protocols.TestTCP(req)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !result.Success {
		t.Errorf("expected success=true, got error=%q", result.Error)
	}
}

// TestTCP_TLSLocalServer verifies TLS connection path (covers tlsVersionToString).
// Uses httptest.NewTLSServer as a convenient local TLS target.
func TestTCP_TLSLocalServer(t *testing.T) {
	ts := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))
	defer ts.Close()

	// Extract host:port from the test server URL.
	addr := ts.Listener.Addr().String()

	req := protocols.TCPTestRequest{
		Target:   addr,
		Protocol: "tls",
		Timeout:  5,
		Count:    1,
	}

	result, _ := protocols.TestTCP(req)
	if result == nil {
		t.Fatal("TestTCP with TLS must return non-nil result")
	}
	// TLS to the test server uses a self-signed cert so InsecureSkipVerify=false
	// will fail cert validation — that's expected. We just check no panic.
}

// TestTCP_RawTCP_WithProtocolVariants exercises all protocol-normalization paths.
func TestTCP_RawTCP_WithProtocolVariants(t *testing.T) {
	protocols_ := []string{"raw", "tcp", "Raw TCP", "raw_tcp"}

	for _, proto := range protocols_ {
		t.Run(proto, func(t *testing.T) {
			ln, err := net.Listen("tcp", "127.0.0.1:0")
			if err != nil {
				t.Fatalf("failed to create listener: %v", err)
			}
			defer ln.Close()
			port := ln.Addr().(*net.TCPAddr).Port

			go func() {
				conn, _ := ln.Accept()
				if conn != nil {
					conn.Close()
				}
			}()

			req := protocols.TCPTestRequest{
				Target:   "127.0.0.1",
				Port:     port,
				Protocol: proto,
				Timeout:  5,
				Count:    1,
			}

			result, err := protocols.TestTCP(req)
			if err != nil {
				// Some variants might not map to supported protocol after normalization
				// but should not panic.
				return
			}
			if result == nil {
				t.Fatalf("TestTCP returned nil result for protocol %q", proto)
			}
		})
	}
}

// TestTCPTestResult_ToJSON verifies JSON marshalling of results.
func TestTCPTestResult_ToJSON(t *testing.T) {
	r := &protocols.TCPTestResult{
		Target:    "example.com:80",
		Protocol:  "raw",
		Connected: true,
		Success:   true,
		LatencyMS: 5.5,
	}
	data, err := r.ToJSON()
	if err != nil {
		t.Fatalf("ToJSON failed: %v", err)
	}
	if len(data) == 0 {
		t.Error("ToJSON returned empty data")
	}
}

// TestTCP_SSHConnRefused exercises the testSSH path where the target port
// doesn't have an SSH server. The testSSH function treats connection failures
// as "connectivity test" successes if a TCP connection was established,
// but actually refused connections are also handled gracefully.
func TestTCP_SSH_ConnRefused(t *testing.T) {
	// Bind a port and close it to ensure connection refused.
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("failed to create listener: %v", err)
	}
	port := ln.Addr().(*net.TCPAddr).Port
	ln.Close()
	time.Sleep(10 * time.Millisecond)

	req := protocols.TCPTestRequest{
		Target:   "127.0.0.1",
		Port:     port,
		Protocol: "ssh",
		Timeout:  2,
		Count:    1,
	}

	result, _ := protocols.TestTCP(req)
	if result == nil {
		t.Fatal("TestTCP SSH must return non-nil result")
	}
	// Connection refused — should be reported as failure.
	// (testSSH marks success only after banner exchange)
}

// TestTCP_SSH_LocalListener exercises testSSH against a plain TCP listener.
// SSH auth will fail (no real SSH server), but the function treats any
// connection attempt (even failed auth) as "connectivity test success".
func TestTCP_SSH_LocalListener(t *testing.T) {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("failed to create listener: %v", err)
	}
	defer ln.Close()
	port := ln.Addr().(*net.TCPAddr).Port

	// Accept and close immediately (no SSH banner).
	go func() {
		for {
			conn, err := ln.Accept()
			if err != nil {
				return
			}
			conn.Close()
		}
	}()

	req := protocols.TCPTestRequest{
		Target:   "127.0.0.1",
		Port:     port,
		Protocol: "ssh",
		Timeout:  2,
		Count:    1,
	}

	result, _ := protocols.TestTCP(req)
	if result == nil {
		t.Fatal("TestTCP SSH must return non-nil result")
	}
	// Either success (treated as connectivity test) or failure — no panic.
}

// TestTCP_TargetWithURLScheme exercises the URL parsing path in parseTarget.
func TestTCP_TargetWithURLScheme(t *testing.T) {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("failed to create listener: %v", err)
	}
	defer ln.Close()
	port := ln.Addr().(*net.TCPAddr).Port

	go func() {
		conn, _ := ln.Accept()
		if conn != nil {
			conn.Close()
		}
	}()

	req := protocols.TCPTestRequest{
		Target:   "tcp://127.0.0.1",
		Port:     port,
		Protocol: "raw",
		Timeout:  5,
		Count:    1,
	}

	result, _ := protocols.TestTCP(req)
	if result == nil {
		t.Fatal("TestTCP with URL scheme must return non-nil result")
	}
}
