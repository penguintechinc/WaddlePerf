package main

import (
	"fmt"
	"os"
	"runtime"

	"github.com/penguintechinc/WaddlePerf/go-client/internal/network"
	"github.com/penguintechinc/WaddlePerf/go-client/internal/system"
	"github.com/penguintechinc/WaddlePerf/go-client/internal/ui"
	"github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var (
	Version   = "dev"
	BuildTime = "unknown"
	GitCommit = "unknown"
)

var rootCmd = &cobra.Command{
	Use:   "waddleperf",
	Short: "WaddlePerf - Network Performance Testing Client",
	Long: `WaddlePerf is a comprehensive network performance testing and monitoring client.
It provides continuous monitoring, manual testing, and detailed network diagnostics.`,
	Version: fmt.Sprintf("%s (built: %s, commit: %s)", Version, BuildTime, GitCommit),
}

var runCmd = &cobra.Command{
	Use:   "run",
	Short: "Run a single network performance test",
	Long:  "Execute a one-time network performance test against a specified server",
	RunE: func(cmd *cobra.Command, args []string) error {
		server := viper.GetString("server")
		if server == "" {
			return fmt.Errorf("server address is required")
		}

		logger := logrus.New()
		logger.SetLevel(logrus.InfoLevel)
		if viper.GetBool("verbose") {
			logger.SetLevel(logrus.DebugLevel)
		}

		client := network.NewClient(server, logger)
		results, err := client.RunTests()
		if err != nil {
			return fmt.Errorf("failed to run tests: %w", err)
		}

		fmt.Printf("Test Results:\n%v\n", results)
		return nil
	},
}

var trayCmd = &cobra.Command{
	Use:   "tray",
	Short: "Run WaddlePerf in system tray mode",
	Long:  "Start WaddlePerf as a system tray application with continuous monitoring",
	RunE: func(cmd *cobra.Command, args []string) error {
		server := viper.GetString("server")
		if server == "" {
			return fmt.Errorf("server address is required")
		}

		logger := logrus.New()
		logger.SetLevel(logrus.InfoLevel)
		if viper.GetBool("verbose") {
			logger.SetLevel(logrus.DebugLevel)
		}

		logFile := viper.GetString("log-file")
		if logFile != "" {
			file, err := os.OpenFile(logFile, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0666)
			if err == nil {
				logger.SetOutput(file)
			} else {
				logger.Warnf("Failed to open log file %s: %v", logFile, err)
			}
		}

		trayApp := ui.NewTrayApp(server, logger)
		return trayApp.Run()
	},
}

var infoCmd = &cobra.Command{
	Use:   "info",
	Short: "Display system information",
	Long:  "Show detailed system and network information",
	RunE: func(cmd *cobra.Command, args []string) error {
		info := system.GetSystemInfo()
		fmt.Printf("System Information:\n")
		fmt.Printf("  OS: %s\n", runtime.GOOS)
		fmt.Printf("  Architecture: %s\n", runtime.GOARCH)
		fmt.Printf("  CPU Cores: %d\n", runtime.NumCPU())
		fmt.Printf("  Go Version: %s\n", runtime.Version())
		fmt.Printf("  Hostname: %s\n", info.Hostname)
		fmt.Printf("  IP Addresses: %v\n", info.IPAddresses)
		return nil
	},
}

func init() {
	cobra.OnInitialize(initConfig)

	rootCmd.PersistentFlags().StringP("server", "s", "", "WaddlePerf server address")
	rootCmd.PersistentFlags().StringP("config", "c", "", "config file (default is $HOME/.waddleperf.yaml)")
	rootCmd.PersistentFlags().BoolP("verbose", "v", false, "verbose output")

	trayCmd.Flags().StringP("log-file", "l", "", "log file path for continuous monitoring")
	trayCmd.Flags().IntP("interval", "i", 3600, "test interval in seconds (default: 3600)")
	trayCmd.Flags().BoolP("autostart", "a", false, "start monitoring automatically")

	viper.BindPFlag("server", rootCmd.PersistentFlags().Lookup("server"))
	viper.BindPFlag("verbose", rootCmd.PersistentFlags().Lookup("verbose"))
	viper.BindPFlag("log-file", trayCmd.Flags().Lookup("log-file"))
	viper.BindPFlag("interval", trayCmd.Flags().Lookup("interval"))
	viper.BindPFlag("autostart", trayCmd.Flags().Lookup("autostart"))

	rootCmd.AddCommand(runCmd)
	rootCmd.AddCommand(trayCmd)
	rootCmd.AddCommand(infoCmd)
}

func initConfig() {
	cfgFile := viper.GetString("config")
	if cfgFile != "" {
		viper.SetConfigFile(cfgFile)
	} else {
		home, err := os.UserHomeDir()
		if err == nil {
			viper.AddConfigPath(home)
			viper.SetConfigType("yaml")
			viper.SetConfigName(".waddleperf")
		}
	}

	viper.AutomaticEnv()
	viper.SetEnvPrefix("WADDLEPERF")

	if err := viper.ReadInConfig(); err == nil {
		fmt.Println("Using config file:", viper.ConfigFileUsed())
	}
}

func main() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
