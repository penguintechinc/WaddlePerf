# WaddlePerf Installation Guide

## Prerequisites

### System Requirements
- **Operating Systems**: Linux (Ubuntu 20.04+, Debian 11+, RHEL 8+), Windows 10/11, macOS 10.15+
- **Memory**: Minimum 512MB RAM (1GB+ recommended)
- **Disk Space**: 100MB for client, 500MB for server
- **Network**: Outbound connectivity to target servers

### Software Dependencies

#### Python Components (Client & Server)
- Python 3.9 or higher
- pip package manager

#### Go Client Build Dependencies
For building the Go client from source:
- Go 1.21 or higher
- Git

##### Linux (Ubuntu/Debian)
```bash
# For system tray support
sudo apt-get update
sudo apt-get install -y libayatana-appindicator3-dev libgtk-3-dev

# For Python components
sudo apt-get install -y python3-pip python3-venv
```

##### macOS
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install Homebrew if not present
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install go python@3.11
```

##### Windows
- Install Python from [python.org](https://python.org)
- Install Go from [go.dev](https://go.dev)
- Install Git from [git-scm.com](https://git-scm.com)

## Installation Methods

### 1. Docker Installation (Recommended)

#### Using Docker Compose (Full Stack)
```bash
# Clone the repository
git clone https://github.com/penguintechinc/WaddlePerf.git
cd WaddlePerf

# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

#### Individual Container Deployment

##### Client Container
```bash
docker run -d \
  --name waddleperf-client \
  -p 8080:8080 \
  -e TARGET_SERVER=your-server-address \
  ghcr.io/penguincloud/waddleperf-client:latest
```

##### Server Container
```bash
docker run -d \
  --name waddleperf-server \
  -p 80:80 -p 443:443 -p 5201:5201 -p 2000:2000/udp \
  ghcr.io/penguincloud/waddleperf-server:latest
```

### 2. Go Client Installation

#### Pre-built Binaries
Download from [GitHub Releases](https://github.com/penguintechinc/WaddlePerf/releases):

##### Linux
```bash
# AMD64
wget https://github.com/penguintechinc/WaddlePerf/releases/latest/download/waddleperf-linux-amd64.tar.gz
tar xzf waddleperf-linux-amd64.tar.gz
sudo mv waddleperf /usr/local/bin/
sudo chmod +x /usr/local/bin/waddleperf

# ARM64
wget https://github.com/penguintechinc/WaddlePerf/releases/latest/download/waddleperf-linux-arm64.tar.gz
tar xzf waddleperf-linux-arm64.tar.gz
sudo mv waddleperf /usr/local/bin/
sudo chmod +x /usr/local/bin/waddleperf
```

##### macOS (Universal Binary)
```bash
wget https://github.com/penguintechinc/WaddlePerf/releases/latest/download/waddleperf-macos-universal.tar.gz
tar xzf waddleperf-macos-universal.tar.gz
sudo mv waddleperf /usr/local/bin/
sudo chmod +x /usr/local/bin/waddleperf
```

##### Windows
Download and extract the appropriate ZIP file:
- `waddleperf-windows-amd64.zip` for 64-bit systems
- `waddleperf-windows-arm64.zip` for ARM systems

#### Building from Source
```bash
# Clone repository
git clone https://github.com/penguintechinc/WaddlePerf.git
cd WaddlePerf/go-client

# Install dependencies
go mod download

# Build with system tray support
go build -o waddleperf ./cmd/waddleperf

# Build without system tray (no GTK dependencies)
go build -tags nosystray -o waddleperf ./cmd/waddleperf

# Install to system
sudo mv waddleperf /usr/local/bin/
```

### 3. Thin Client Installation

#### Linux/macOS
```bash
curl -sSL https://raw.githubusercontent.com/penguintechinc/WaddlePerf/main/client/thin-installers/debian-thininstall.sh | bash
```

#### Windows (PowerShell as Administrator)
```powershell
Invoke-WebRequest -Uri https://raw.githubusercontent.com/penguintechinc/WaddlePerf/main/client/thin-installers/windows-thininstall.ps -OutFile install.ps1
./install.ps1
```

## Configuration

### Environment Variables

#### Client Configuration
```bash
export WADDLEPERF_SERVER=server.example.com:8080
export WADDLEPERF_LOG_LEVEL=info
export WADDLEPERF_INTERVAL=3600
export WADDLEPERF_AUTOSTART=true
```

#### Server Configuration
```bash
export LISTEN_PORT=80
export SSL_PORT=443
export IPERF_PORT=5201
export UDP_PORT=2000
export ENABLE_GEOIP=true
```

### Configuration Files

#### Go Client Configuration (~/.waddleperf.yaml)
```yaml
server: server.example.com:8080
interval: 3600
autostart: true
log-file: /var/log/waddleperf.log
verbose: false
```

#### Client Docker Configuration (/client/vars/base.yml)
```yaml
TARGET_SERVER: server.example.com
TEST_INTERVAL: 3600
S3_BUCKET: waddleperf-results
S3_ENDPOINT: s3.amazonaws.com
```

## Verification

### Test Installation
```bash
# Go Client
waddleperf info
waddleperf run -s server.example.com

# Docker
docker exec waddleperf-client python3 /app/bins/getSysInfo.py

# Check logs
docker logs waddleperf-client
docker logs waddleperf-server
```

### Health Checks
- Client Web UI: http://localhost:8080
- Server Status: http://server-ip/health
- iperf3 Test: `iperf3 -c server-ip -p 5201`

## Troubleshooting

### Common Issues

#### Permission Denied
```bash
# Fix permissions
sudo chown -R $(whoami):$(whoami) /opt/waddleperf
chmod +x /usr/local/bin/waddleperf
```

#### Port Already in Use
```bash
# Check what's using the port
sudo lsof -i :8080
sudo netstat -tulpn | grep 8080

# Kill the process or change port
docker run -p 8081:8080 ...
```

#### System Tray Not Working (Linux)
```bash
# Install required libraries
sudo apt-get install libayatana-appindicator3-dev libgtk-3-dev

# Or build without system tray
go build -tags nosystray -o waddleperf ./cmd/waddleperf
```

#### Python Module Errors
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

## Next Steps
- Read the [Usage Guide](USAGE.md) for operational details
- Configure [AutoPerf Mode](AUTOPERF.md) for continuous monitoring
- Set up [S3 Integration](S3_INTEGRATION.md) for results storage
- Review [Security Best Practices](SECURITY.md)