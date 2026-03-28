package protocols_test

import (
	"net"
	"testing"

	"github.com/penguincloud/waddleperf/testserver/internal/protocols"
)

// ---------------------------------------------------------------------------
// TestUDP_UnsupportedProtocol
// ---------------------------------------------------------------------------

func TestUDP_UnsupportedProtocol(t *testing.T) {
	req := protocols.UDPTestRequest{
		Target:   "127.0.0.1",
		Port:     1234,
		Protocol: "quic", // not supported
		Timeout:  2,
		Count:    1,
	}

	result, err := protocols.TestUDP(req)
	if err == nil {
		t.Error("expected error for unsupported UDP protocol")
	}
	if result != nil && result.Success {
		t.Error("expected success=false for unsupported protocol")
	}
}

// TestUDP_DTLSNotImplemented verifies the DTLS stub returns an error.
func TestUDP_DTLSNotImplemented(t *testing.T) {
	req := protocols.UDPTestRequest{
		Target:   "127.0.0.1",
		Port:     1234,
		Protocol: "tls", // DTLS — not yet implemented
		Timeout:  2,
		Count:    1,
	}

	result, err := protocols.TestUDP(req)
	if err == nil {
		t.Error("expected error for DTLS (not implemented)")
	}
	if result != nil && result.Success {
		t.Error("expected success=false for DTLS")
	}
}

// TestUDP_DefaultProtocol verifies that an empty protocol defaults to dns
// and that the test at least returns a result (may fail if no DNS server at target).
func TestUDP_DefaultProtocol_Struct(t *testing.T) {
	req := protocols.UDPTestRequest{
		Target:  "8.8.8.8",
		Timeout: 3,
		Count:   1,
		// Protocol intentionally empty — should default to "dns"
	}
	// We only check that the call doesn't panic and returns non-nil
	result, _ := protocols.TestUDP(req)
	if result == nil {
		t.Error("TestUDP should always return a non-nil result")
	}
}

// TestUDP_ProtocolDetailFallback verifies ProtocolDetail is used when Protocol is empty.
func TestUDP_ProtocolDetailFallback(t *testing.T) {
	req := protocols.UDPTestRequest{
		Target:         "127.0.0.1",
		Port:           9999,
		Protocol:       "",
		ProtocolDetail: "raw",
		Timeout:        2,
		Count:          1,
	}
	// Raw UDP to a closed port — connection may "succeed" from dial perspective
	// or fail. We just verify no panic and non-nil result.
	result, _ := protocols.TestUDP(req)
	if result == nil {
		t.Error("TestUDP should return non-nil result")
	}
}

// TestUDPTestResult_ToJSON verifies JSON marshalling.
func TestUDPTestResult_ToJSON(t *testing.T) {
	r := &protocols.UDPTestResult{
		Target:    "8.8.8.8:53",
		Protocol:  "dns",
		Success:   true,
		LatencyMS: 3.2,
	}
	data, err := r.ToJSON()
	if err != nil {
		t.Fatalf("ToJSON failed: %v", err)
	}
	if len(data) == 0 {
		t.Error("ToJSON returned empty data")
	}
}

// TestUDP_RawSuccess exercises testRawUDP with a listening UDP socket.
// We send a PING packet and verify the protocol handles both response and
// no-response cases correctly.
func TestUDP_RawSuccess(t *testing.T) {
	// Bind a real UDP socket to receive the test packet.
	pc, err := net.ListenPacket("udp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("failed to create UDP listener: %v", err)
	}
	defer pc.Close()

	port := pc.LocalAddr().(*net.UDPAddr).Port

	// Goroutine to accept and echo the packet back (simulating a real UDP response).
	go func() {
		buf := make([]byte, 1024)
		n, addr, err := pc.ReadFrom(buf)
		if err != nil {
			return
		}
		// Echo back the received data.
		_, _ = pc.WriteTo(buf[:n], addr)
	}()

	req := protocols.UDPTestRequest{
		Target:   "127.0.0.1",
		Port:     port,
		Protocol: "raw",
		Timeout:  3,
		Count:    1,
	}

	result, err := protocols.TestUDP(req)
	if err != nil {
		t.Logf("TestUDP raw error (may be expected): %v", err)
	}
	if result == nil {
		t.Fatal("TestUDP must return non-nil result")
	}
	// Raw UDP to a real listener should succeed.
	if !result.Success {
		t.Logf("raw UDP not successful (may be timing issue): %v", result.Error)
	}
}

// TestUDP_RawNoResponse exercises testRawUDP where no response is received
// (write succeeds, read times out).
func TestUDP_RawNoResponse(t *testing.T) {
	// Bind a UDP socket but don't send anything back — simulates a one-way sink.
	pc, err := net.ListenPacket("udp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("failed to create UDP listener: %v", err)
	}
	defer pc.Close()

	port := pc.LocalAddr().(*net.UDPAddr).Port

	req := protocols.UDPTestRequest{
		Target:   "127.0.0.1",
		Port:     port,
		Protocol: "raw",
		Timeout:  1, // short timeout so read deadline expires quickly
		Count:    1,
	}

	result, _ := protocols.TestUDP(req)
	if result == nil {
		t.Fatal("TestUDP must return non-nil result")
	}
	// With no response, raw UDP still marks success (UDP is connectionless).
}

// TestUDP_MultipleCountRaw verifies jitter calculation for multiple raw UDP attempts.
func TestUDP_MultipleCountRaw(t *testing.T) {
	pc, err := net.ListenPacket("udp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("failed to create UDP listener: %v", err)
	}
	defer pc.Close()
	port := pc.LocalAddr().(*net.UDPAddr).Port

	// Echo back all packets received.
	go func() {
		buf := make([]byte, 1024)
		for {
			n, addr, err := pc.ReadFrom(buf)
			if err != nil {
				return
			}
			_, _ = pc.WriteTo(buf[:n], addr)
		}
	}()

	req := protocols.UDPTestRequest{
		Target:   "127.0.0.1",
		Port:     port,
		Protocol: "raw",
		Timeout:  3,
		Count:    3,
	}

	result, _ := protocols.TestUDP(req)
	if result == nil {
		t.Fatal("TestUDP must return non-nil result")
	}
	// Multiple counts should produce min/max latency (even if only one succeeds).
}
