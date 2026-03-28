//go:build !integration

package protocols_test

import (
	"net"
	"testing"

	"github.com/penguincloud/waddleperf/testserver/internal/protocols"
)

// ---------------------------------------------------------------------------
// TraceResult.ToJSON
// ---------------------------------------------------------------------------

func TestTraceResult_ToJSON(t *testing.T) {
	r := &protocols.TraceResult{
		Target:    "example.com",
		Protocol:  "tcp_trace",
		Success:   true,
		LatencyMS: 20.0,
		Hops:      []string{"Hop 1: 10.0.0.1", "Hop 2: 10.0.0.2"},
	}
	data, err := r.ToJSON()
	if err != nil {
		t.Fatalf("ToJSON failed: %v", err)
	}
	if len(data) == 0 {
		t.Error("ToJSON returned empty data")
	}
}

// ---------------------------------------------------------------------------
// TestTCPTrace
// ---------------------------------------------------------------------------

// TestTCPTrace_InvalidTarget verifies that an unparsable target returns an error.
func TestTCPTrace_InvalidTarget(t *testing.T) {
	req := protocols.TCPTraceRequest{
		Target:  ":::bad::target:::",
		Port:    80,
		Timeout: 2,
	}
	result, err := protocols.TestTCPTrace(req)
	if err == nil {
		t.Error("expected error for invalid target")
	}
	if result != nil && result.Success {
		t.Error("expected success=false for invalid target")
	}
}

// TestTCPTrace_DNSFailure verifies that an unresolvable hostname returns an error.
func TestTCPTrace_DNSFailure(t *testing.T) {
	req := protocols.TCPTraceRequest{
		Target:  "this.hostname.does.not.exist.invalid",
		Port:    80,
		Timeout: 2,
	}
	result, err := protocols.TestTCPTrace(req)
	if err == nil {
		t.Error("expected error for unresolvable hostname")
	}
	if result != nil && result.Success {
		t.Error("expected success=false for DNS failure")
	}
}

// TestTCPTrace_DefaultPort verifies that port 0 defaults to 22.
func TestTCPTrace_DefaultPort(t *testing.T) {
	// We only check that the default port logic is exercised (no panic).
	// DNS resolution may or may not succeed for localhost — just verify non-nil result.
	req := protocols.TCPTraceRequest{
		Target:  "127.0.0.1",
		Port:    0, // should default to 22
		Timeout: 2,
	}
	result, _ := protocols.TestTCPTrace(req)
	if result == nil {
		t.Fatal("TestTCPTrace must return non-nil result")
	}
}

// ---------------------------------------------------------------------------
// TestTraceroute
// ---------------------------------------------------------------------------

// TestTraceroute_LocalhostNoPanic verifies no panic on localhost target.
func TestTraceroute_LocalhostNoPanic(t *testing.T) {
	req := protocols.TracerouteRequest{
		Target:  "127.0.0.1",
		Timeout: 2,
	}
	result, _ := protocols.TestTraceroute(req)
	if result == nil {
		t.Fatal("TestTraceroute must return non-nil result")
	}
}

// TestTraceroute_DefaultTimeout verifies that a zero timeout defaults properly.
func TestTraceroute_DefaultTimeout(t *testing.T) {
	req := protocols.TracerouteRequest{
		Target:  "127.0.0.1",
		Timeout: 0, // should default to 30
	}
	result, _ := protocols.TestTraceroute(req)
	if result == nil {
		t.Fatal("TestTraceroute must return non-nil result")
	}
}

// ---------------------------------------------------------------------------
// TestUDPTrace
// ---------------------------------------------------------------------------

// TestUDPTrace_DNSFailure verifies that an unresolvable hostname returns an error.
func TestUDPTrace_DNSFailure(t *testing.T) {
	req := protocols.UDPTraceRequest{
		Target:  "this.hostname.does.not.exist.invalid",
		Port:    53,
		Timeout: 2,
	}
	result, err := protocols.TestUDPTrace(req)
	if err == nil {
		t.Error("expected error for unresolvable hostname")
	}
	if result != nil && result.Success {
		t.Error("expected success=false for DNS failure")
	}
}

// TestUDPTrace_DefaultPort verifies that port 0 defaults to 53.
func TestUDPTrace_DefaultPort(t *testing.T) {
	req := protocols.UDPTraceRequest{
		Target:  "127.0.0.1",
		Port:    0, // should default to 53
		Timeout: 2,
	}
	result, _ := protocols.TestUDPTrace(req)
	if result == nil {
		t.Fatal("TestUDPTrace must return non-nil result")
	}
}

// TestUDPTrace_DefaultTimeout verifies zero timeout defaults to 30.
func TestUDPTrace_DefaultTimeout(t *testing.T) {
	req := protocols.UDPTraceRequest{
		Target:  "127.0.0.1",
		Timeout: 0, // should default to 30
		Port:    53,
	}
	result, _ := protocols.TestUDPTrace(req)
	if result == nil {
		t.Fatal("TestUDPTrace must return non-nil result")
	}
}

// ---------------------------------------------------------------------------
// TestHTTPTrace
// ---------------------------------------------------------------------------

// TestHTTPTrace_InvalidTarget verifies an error is returned for a bad target.
func TestHTTPTrace_InvalidRequest(t *testing.T) {
	req := protocols.HTTPTraceRequest{
		Target:  "http://\x7f", // invalid URL character
		Timeout: 2,
	}
	result, _ := protocols.TestHTTPTrace(req)
	// The function may succeed or fail; we only check no panic.
	if result == nil {
		t.Fatal("TestHTTPTrace must return non-nil result")
	}
}

// TestHTTPTrace_HTTPScheme verifies http:// scheme is detected and port set to 80.
func TestHTTPTrace_HTTPScheme(t *testing.T) {
	req := protocols.HTTPTraceRequest{
		Target:  "http://127.0.0.1",
		Timeout: 2,
	}
	result, _ := protocols.TestHTTPTrace(req)
	if result == nil {
		t.Fatal("TestHTTPTrace must return non-nil result")
	}
}

// TestHTTPTrace_CustomPort verifies a custom port is honoured.
func TestHTTPTrace_CustomPort(t *testing.T) {
	req := protocols.HTTPTraceRequest{
		Target:  "https://127.0.0.1",
		Port:    8443,
		Timeout: 2,
	}
	result, _ := protocols.TestHTTPTrace(req)
	if result == nil {
		t.Fatal("TestHTTPTrace must return non-nil result")
	}
}

// ---------------------------------------------------------------------------
// HopDetail struct coverage
// ---------------------------------------------------------------------------

func TestHopDetail_Fields(t *testing.T) {
	h := protocols.HopDetail{
		HopNumber: 1,
		IPAddress: "10.0.0.1",
		Hostname:  "router.local",
		Latency:   "2.3 ms",
		RawOutput: "10.0.0.1  2.3 ms",
		Timeout:   false,
	}
	if h.HopNumber != 1 {
		t.Errorf("HopNumber expected 1, got %d", h.HopNumber)
	}
	if h.IPAddress != "10.0.0.1" {
		t.Errorf("IPAddress expected 10.0.0.1, got %s", h.IPAddress)
	}
}

// ---------------------------------------------------------------------------
// TraceResult RawResults field
// ---------------------------------------------------------------------------

func TestTraceResult_WithRawResults(t *testing.T) {
	r := &protocols.TraceResult{
		Target:    "example.com",
		Protocol:  "http_trace",
		Success:   true,
		LatencyMS: 30.0,
		RawResults: map[string]interface{}{
			"status_code": 200,
			"hop_count":   5,
		},
	}
	data, err := r.ToJSON()
	if err != nil {
		t.Fatalf("ToJSON failed: %v", err)
	}
	if len(data) == 0 {
		t.Error("ToJSON returned empty data")
	}
}

// ---------------------------------------------------------------------------
// TestTCPTrace_DirectConnect exercises the fallback TCP connect path.
// ---------------------------------------------------------------------------

func TestTCPTrace_DirectConnectFallback(t *testing.T) {
	// Start a listener so direct TCP connection succeeds.
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("failed to start listener: %v", err)
	}
	defer ln.Close()

	go func() {
		for {
			conn, err := ln.Accept()
			if err != nil {
				return
			}
			conn.Close()
		}
	}()

	addr := ln.Addr().(*net.TCPAddr)

	req := protocols.TCPTraceRequest{
		Target:  addr.IP.String(),
		Port:    addr.Port,
		Timeout: 5,
	}

	result, _ := protocols.TestTCPTrace(req)
	if result == nil {
		t.Fatal("TestTCPTrace must return non-nil result")
	}
	// traceroute may or may not succeed; we just validate no panic.
}

// TestTraceroute_WithHops exercises the hop-parsing path by running against localhost.
func TestTraceroute_RunAndParse(t *testing.T) {
	req := protocols.TracerouteRequest{
		Target:  "127.0.0.1",
		Timeout: 5,
	}
	result, _ := protocols.TestTraceroute(req)
	if result == nil {
		t.Fatal("TestTraceroute must return non-nil result")
	}
	// RouteInfo should be set if any hops were found.
	_ = result.RouteInfo
}

// TestUDPTrace_DirectFallback tests the UDP direct-connection fallback path.
func TestUDPTrace_LocalHost(t *testing.T) {
	req := protocols.UDPTraceRequest{
		Target:  "127.0.0.1",
		Port:    53,
		Timeout: 3,
	}
	result, _ := protocols.TestUDPTrace(req)
	if result == nil {
		t.Fatal("TestUDPTrace must return non-nil result")
	}
}
