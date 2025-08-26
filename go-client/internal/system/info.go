package system

import (
	"net"
	"os"
	"runtime"
)

type SystemInfo struct {
	Hostname    string   `json:"hostname"`
	OS          string   `json:"os"`
	Arch        string   `json:"arch"`
	CPUCount    int      `json:"cpu_count"`
	GoVersion   string   `json:"go_version"`
	IPAddresses []string `json:"ip_addresses"`
}

func GetSystemInfo() *SystemInfo {
	hostname, _ := os.Hostname()

	return &SystemInfo{
		Hostname:    hostname,
		OS:          runtime.GOOS,
		Arch:        runtime.GOARCH,
		CPUCount:    runtime.NumCPU(),
		GoVersion:   runtime.Version(),
		IPAddresses: getIPAddresses(),
	}
}

func getIPAddresses() []string {
	var ips []string

	interfaces, err := net.Interfaces()
	if err != nil {
		return ips
	}

	for _, iface := range interfaces {
		// Skip down interfaces
		if iface.Flags&net.FlagUp == 0 {
			continue
		}

		// Skip loopback
		if iface.Flags&net.FlagLoopback != 0 {
			continue
		}

		addrs, err := iface.Addrs()
		if err != nil {
			continue
		}

		for _, addr := range addrs {
			var ip net.IP
			switch v := addr.(type) {
			case *net.IPNet:
				ip = v.IP
			case *net.IPAddr:
				ip = v.IP
			}

			if ip == nil || ip.IsLoopback() {
				continue
			}

			// Only include IPv4 for simplicity
			if ip.To4() != nil {
				ips = append(ips, ip.String())
			}
		}
	}

	return ips
}
