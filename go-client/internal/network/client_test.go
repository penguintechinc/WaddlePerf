package network

import (
	"testing"
	"time"

	"github.com/sirupsen/logrus"
)

func TestNewClient(t *testing.T) {
	logger := logrus.New()
	logger.SetLevel(logrus.FatalLevel) // Suppress log output during tests
	
	client := NewClient("localhost:8080", logger)
	
	if client == nil {
		t.Fatal("NewClient returned nil")
	}
	
	if client.serverAddr != "localhost:8080" {
		t.Errorf("Expected server address 'localhost:8080', got '%s'", client.serverAddr)
	}
	
	if client.logger != logger {
		t.Error("Logger not set correctly")
	}
	
	if client.httpClient == nil {
		t.Error("HTTP client not initialized")
	}
	
	// Test cleanup (should not panic)
	defer func() {
		if r := recover(); r != nil {
			t.Errorf("cleanup() caused panic: %v", r)
		}
	}()
	client.Close()
}

func TestPingResults(t *testing.T) {
	results := &PingResults{
		PacketsSent: 10,
		PacketsRecv: 8,
		PacketLoss:  20.0,
		MinRtt:      50 * time.Millisecond,
		MaxRtt:      200 * time.Millisecond,
		AvgRtt:      100 * time.Millisecond,
		TCPTest:     true,
		UDPTest:     false,
		ICMPTest:    true,
	}
	
	if results.PacketsSent != 10 {
		t.Errorf("Expected 10 packets sent, got %d", results.PacketsSent)
	}
	
	if results.PacketLoss != 20.0 {
		t.Errorf("Expected 20.0%% packet loss, got %.1f%%", results.PacketLoss)
	}
	
	if !results.TCPTest {
		t.Error("Expected TCP test to be true")
	}
	
	if results.UDPTest {
		t.Error("Expected UDP test to be false")
	}
}

func TestTCPResults(t *testing.T) {
	results := &TCPResults{
		ConnectTime: 100 * time.Millisecond,
		Connected:   true,
		LocalAddr:   "127.0.0.1:12345",
		RemoteAddr:  "example.com:80",
	}
	
	if results.ConnectTime != 100*time.Millisecond {
		t.Errorf("Expected connect time 100ms, got %v", results.ConnectTime)
	}
	
	if !results.Connected {
		t.Error("Expected connection to be true")
	}
}

func TestHTTPResults(t *testing.T) {
	results := &HTTPResults{
		StatusCode:    200,
		ResponseTime:  250 * time.Millisecond,
		ContentLength: 1024,
		Headers:       map[string]string{"Content-Type": "text/html"},
	}
	
	if results.StatusCode != 200 {
		t.Errorf("Expected status code 200, got %d", results.StatusCode)
	}
	
	if results.ResponseTime != 250*time.Millisecond {
		t.Errorf("Expected response time 250ms, got %v", results.ResponseTime)
	}
	
	if results.ContentLength != 1024 {
		t.Errorf("Expected content length 1024, got %d", results.ContentLength)
	}
	
	if results.Headers["Content-Type"] != "text/html" {
		t.Errorf("Expected Content-Type 'text/html', got '%s'", results.Headers["Content-Type"])
	}
}