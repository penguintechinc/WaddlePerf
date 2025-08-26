//go:build !nosystray
// +build !nosystray

package ui

import (
	"fmt"
	"os"
	"time"

	"github.com/penguintechinc/WaddlePerf/go-client/internal/network"
	"github.com/getlantern/systray"
	"github.com/sirupsen/logrus"
	"github.com/spf13/viper"
)

type TrayApp struct {
	serverAddr   string
	logger       *logrus.Logger
	client       *network.Client
	ticker       *time.Ticker
	stopMonitor  chan bool
	isMonitoring bool
}

func NewTrayApp(serverAddr string, logger *logrus.Logger) *TrayApp {
	return &TrayApp{
		serverAddr:  serverAddr,
		logger:      logger,
		client:      network.NewClient(serverAddr, logger),
		stopMonitor: make(chan bool),
	}
}

func (app *TrayApp) Run() error {
	systray.Run(app.onReady, app.onExit)
	return nil
}

func (app *TrayApp) onReady() {
	systray.SetTitle("WaddlePerf")
	systray.SetTooltip("WaddlePerf Network Monitor")

	// Menu items
	mRunTest := systray.AddMenuItem("Run Test Now", "Execute network performance test")
	systray.AddSeparator()

	mToggleMonitor := systray.AddMenuItem("Start Continuous Monitoring", "Toggle continuous monitoring")
	mViewResults := systray.AddMenuItem("View Results", "Open results in browser")
	systray.AddSeparator()

	mSettings := systray.AddMenuItem("Settings", "Configure WaddlePerf")
	systray.AddSeparator()

	mQuit := systray.AddMenuItem("Quit", "Exit WaddlePerf")

	// Auto-start monitoring if configured
	if viper.GetBool("autostart") {
		go app.startMonitoring()
		mToggleMonitor.SetTitle("Stop Continuous Monitoring")
		app.isMonitoring = true
	}

	// Handle menu clicks
	go func() {
		for {
			select {
			case <-mRunTest.ClickedCh:
				app.logger.Info("Manual test triggered")
				go app.runSingleTest()

			case <-mToggleMonitor.ClickedCh:
				if app.isMonitoring {
					app.stopMonitoring()
					mToggleMonitor.SetTitle("Start Continuous Monitoring")
					app.isMonitoring = false
				} else {
					go app.startMonitoring()
					mToggleMonitor.SetTitle("Stop Continuous Monitoring")
					app.isMonitoring = true
				}

			case <-mViewResults.ClickedCh:
				app.openResultsInBrowser()

			case <-mSettings.ClickedCh:
				app.logger.Info("Settings clicked - not yet implemented")

			case <-mQuit.ClickedCh:
				systray.Quit()
			}
		}
	}()
}

func (app *TrayApp) onExit() {
	if app.isMonitoring {
		app.stopMonitoring()
	}
	app.logger.Info("WaddlePerf tray application exiting")
}

func (app *TrayApp) startMonitoring() {
	interval := viper.GetInt("interval")
	if interval <= 0 {
		interval = 3600 // Default to 1 hour
	}

	app.logger.Infof("Starting continuous monitoring with %d second interval", interval)
	app.ticker = time.NewTicker(time.Duration(interval) * time.Second)

	// Run initial test
	app.runSingleTest()

	// Run periodic tests
	go func() {
		for {
			select {
			case <-app.ticker.C:
				app.runSingleTest()
			case <-app.stopMonitor:
				return
			}
		}
	}()
}

func (app *TrayApp) stopMonitoring() {
	app.logger.Info("Stopping continuous monitoring")
	if app.ticker != nil {
		app.ticker.Stop()
	}
	app.stopMonitor <- true
}

func (app *TrayApp) runSingleTest() {
	app.logger.Info("Running network performance test")

	results, err := app.client.RunTests()
	if err != nil {
		app.logger.Errorf("Test failed: %v", err)
		systray.SetTooltip(fmt.Sprintf("WaddlePerf - Last test failed: %v", err))
		return
	}

	// Update tray tooltip with results summary
	var status string
	if results.PingResults != nil {
		status = fmt.Sprintf("Ping: %.2fms", float64(results.PingResults.AvgRtt)/float64(time.Millisecond))
	}
	systray.SetTooltip(fmt.Sprintf("WaddlePerf - %s", status))

	// Save results to log file
	logFile := viper.GetString("log-file")
	if logFile != "" {
		app.saveResultsToFile(results, logFile)
	}

	app.logger.Info("Test completed successfully")
}

func (app *TrayApp) saveResultsToFile(results *network.TestResults, filepath string) {
	file, err := os.OpenFile(filepath, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0666)
	if err != nil {
		app.logger.Errorf("Failed to open log file: %v", err)
		return
	}
	defer file.Close()

	// Write results as JSON line
	timestamp := results.Timestamp.Format(time.RFC3339)
	logLine := fmt.Sprintf("[%s] Server: %s", timestamp, results.ServerAddr)

	if results.PingResults != nil {
		logLine += fmt.Sprintf(" | Ping: %.2fms (loss: %.1f%%)",
			float64(results.PingResults.AvgRtt)/float64(time.Millisecond),
			results.PingResults.PacketLoss)
	}

	if results.HTTPResults != nil {
		logLine += fmt.Sprintf(" | HTTP: %dms (status: %d)",
			results.HTTPResults.ResponseTime/time.Millisecond,
			results.HTTPResults.StatusCode)
	}

	if results.TCPResults != nil {
		logLine += fmt.Sprintf(" | TCP: %s (time: %dms)",
			map[bool]string{true: "connected", false: "failed"}[results.TCPResults.Connected],
			results.TCPResults.ConnectTime/time.Millisecond)
	}

	if len(results.Errors) > 0 {
		logLine += fmt.Sprintf(" | Errors: %v", results.Errors)
	}

	file.WriteString(logLine + "\n")
}

func (app *TrayApp) openResultsInBrowser() {
	// This would create a temporary HTML file and open it
	app.logger.Info("Opening results in browser - not yet fully implemented")
	// Implementation would generate HTML from recent results and open in default browser
}
