import Link from 'next/link'
import CodeBlock from '../../components/CodeBlock'

export default function InstallationPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Navigation Breadcrumb */}
        <nav className="flex mb-8" aria-label="Breadcrumb">
          <ol className="inline-flex items-center space-x-1 md:space-x-3">
            <li className="inline-flex items-center">
              <Link href="/" className="text-gray-700 hover:text-blue-600">
                Home
              </Link>
            </li>
            <li>
              <div className="flex items-center">
                <svg className="w-3 h-3 mx-2 text-gray-400" fill="currentColor" viewBox="0 0 12 12">
                  <path d="M5.293 3.293a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 01-1.414-1.414L6.586 8H3a1 1 0 110-2h3.586L5.293 4.707a1 1 0 010-1.414z"/>
                </svg>
                <Link href="/docs" className="text-gray-700 hover:text-blue-600">
                  Documentation
                </Link>
              </div>
            </li>
            <li>
              <div className="flex items-center">
                <svg className="w-3 h-3 mx-2 text-gray-400" fill="currentColor" viewBox="0 0 12 12">
                  <path d="M5.293 3.293a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 01-1.414-1.414L6.586 8H3a1 1 0 110-2h3.586L5.293 4.707a1 1 0 010-1.414z"/>
                </svg>
                <span className="text-gray-500">Installation</span>
              </div>
            </li>
          </ol>
        </nav>

        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Installation Guide
          </h1>
          <p className="text-xl text-gray-600">
            Get WaddlePerf up and running in minutes with multiple installation options
          </p>
        </div>

        {/* Quick Navigation */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Navigation</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <a href="#prerequisites" className="text-blue-600 hover:text-blue-800">Prerequisites</a>
            <a href="#docker" className="text-blue-600 hover:text-blue-800">Docker Install</a>
            <a href="#binary" className="text-blue-600 hover:text-blue-800">Binary Install</a>
            <a href="#source" className="text-blue-600 hover:text-blue-800">Build from Source</a>
            <a href="#configuration" className="text-blue-600 hover:text-blue-800">Configuration</a>
            <a href="#verification" className="text-blue-600 hover:text-blue-800">Verification</a>
            <a href="#troubleshooting" className="text-blue-600 hover:text-blue-800">Troubleshooting</a>
            <a href="#next-steps" className="text-blue-600 hover:text-blue-800">Next Steps</a>
          </div>
        </div>

        {/* Main Content */}
        <div className="space-y-12">
          {/* Prerequisites Section */}
          <section id="prerequisites" className="bg-white rounded-lg shadow-lg p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Prerequisites</h2>
            
            <h3 className="text-xl font-semibold text-gray-800 mb-4">System Requirements</h3>
            <div className="overflow-x-auto mb-6">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Component</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Requirements</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap font-medium">Operating System</td>
                    <td className="px-6 py-4 text-gray-600">Linux (Ubuntu 20.04+, Debian 11+, RHEL 8+), Windows 10/11, macOS 10.15+</td>
                  </tr>
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap font-medium">Memory</td>
                    <td className="px-6 py-4 text-gray-600">Minimum 512MB RAM (1GB+ recommended)</td>
                  </tr>
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap font-medium">Disk Space</td>
                    <td className="px-6 py-4 text-gray-600">100MB for client, 500MB for server</td>
                  </tr>
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap font-medium">Network</td>
                    <td className="px-6 py-4 text-gray-600">Outbound connectivity to target servers</td>
                  </tr>
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap font-medium">Software</td>
                    <td className="px-6 py-4 text-gray-600">Python 3.9+ or Go 1.21+ (for building from source)</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <h3 className="text-xl font-semibold text-gray-800 mb-4">Network Ports</h3>
            <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-yellow-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-yellow-700">
                    <strong>Important:</strong> Ensure the following ports are accessible:
                  </p>
                  <ul className="list-disc list-inside text-sm text-yellow-700 mt-2">
                    <li>HTTP: 80</li>
                    <li>HTTPS: 443</li>
                    <li>Web UI: 8080</li>
                    <li>iperf3: 5201</li>
                    <li>UDP Ping: 2000/udp</li>
                  </ul>
                </div>
              </div>
            </div>
          </section>

          {/* Docker Installation */}
          <section id="docker" className="bg-white rounded-lg shadow-lg p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Docker Installation (Recommended)</h2>
            <p className="text-gray-600 mb-6">The fastest way to get started with WaddlePerf is using Docker containers.</p>
            
            <h3 className="text-xl font-semibold text-gray-800 mb-4">Full Stack with Docker Compose</h3>
            <CodeBlock
              title="Terminal"
              code={`# Clone the repository
git clone https://github.com/penguintechinc/WaddlePerf.git
cd WaddlePerf

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f`}
            />

            <h3 className="text-xl font-semibold text-gray-800 mb-4 mt-8">Individual Container Deployment</h3>
            
            <h4 className="text-lg font-medium text-gray-700 mb-3">Deploy Client Container</h4>
            <CodeBlock
              title="Terminal"
              code={`docker run -d \\
  --name waddleperf-client \\
  -p 8080:8080 \\
  -e TARGET_SERVER=your-server-address \\
  ghcr.io/penguincloud/waddleperf-client:latest`}
            />

            <h4 className="text-lg font-medium text-gray-700 mb-3">Deploy Server Container</h4>
            <CodeBlock
              title="Terminal"
              code={`docker run -d \\
  --name waddleperf-server \\
  -p 80:80 -p 443:443 -p 5201:5201 -p 2000:2000/udp \\
  ghcr.io/penguincloud/waddleperf-server:latest`}
            />

            <div className="bg-green-50 border-l-4 border-green-400 p-4 mt-6">
              <div className="flex">
                <div className="ml-3">
                  <p className="text-sm text-green-700">
                    <strong>Pro Tip:</strong> Docker installation handles all dependencies automatically and provides consistent environments across platforms.
                  </p>
                </div>
              </div>
            </div>
          </section>

          {/* Binary Installation */}
          <section id="binary" className="bg-white rounded-lg shadow-lg p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Binary Installation</h2>
            <p className="text-gray-600 mb-6">
              Download pre-built binaries for your platform from{' '}
              <a href="https://github.com/penguintechinc/WaddlePerf/releases" target="_blank" rel="noopener" className="text-blue-600 hover:text-blue-800">
                GitHub Releases
              </a>
            </p>
            
            <h3 className="text-xl font-semibold text-gray-800 mb-4">Linux Installation</h3>
            
            <h4 className="text-lg font-medium text-gray-700 mb-3">AMD64 Architecture</h4>
            <CodeBlock
              title="Terminal"
              code={`wget https://github.com/penguintechinc/WaddlePerf/releases/latest/download/waddleperf-linux-amd64.tar.gz
tar xzf waddleperf-linux-amd64.tar.gz
sudo mv waddleperf /usr/local/bin/
sudo chmod +x /usr/local/bin/waddleperf`}
            />
            
            <h4 className="text-lg font-medium text-gray-700 mb-3">ARM64 Architecture</h4>
            <CodeBlock
              title="Terminal"
              code={`wget https://github.com/penguintechinc/WaddlePerf/releases/latest/download/waddleperf-linux-arm64.tar.gz
tar xzf waddleperf-linux-arm64.tar.gz
sudo mv waddleperf /usr/local/bin/
sudo chmod +x /usr/local/bin/waddleperf`}
            />
            
            <h3 className="text-xl font-semibold text-gray-800 mb-4 mt-8">macOS Installation (Universal Binary)</h3>
            <CodeBlock
              title="Terminal"
              code={`wget https://github.com/penguintechinc/WaddlePerf/releases/latest/download/waddleperf-macos-universal.tar.gz
tar xzf waddleperf-macos-universal.tar.gz
sudo mv waddleperf /usr/local/bin/
sudo chmod +x /usr/local/bin/waddleperf`}
            />
            
            <h3 className="text-xl font-semibold text-gray-800 mb-4 mt-8">Windows Installation</h3>
            <p className="text-gray-600 mb-4">Download and extract the appropriate ZIP file:</p>
            <ul className="list-disc list-inside text-gray-600 mb-4">
              <li><code className="bg-gray-100 px-2 py-1 rounded">waddleperf-windows-amd64.zip</code> for 64-bit systems</li>
              <li><code className="bg-gray-100 px-2 py-1 rounded">waddleperf-windows-arm64.zip</code> for ARM systems</li>
            </ul>
            <p className="text-gray-600">Add the extracted directory to your PATH environment variable.</p>
          </section>

          {/* Build from Source */}
          <section id="source" className="bg-white rounded-lg shadow-lg p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Building from Source</h2>
            <p className="text-gray-600 mb-6">Build WaddlePerf from source for custom configurations or development.</p>
            
            <h3 className="text-xl font-semibold text-gray-800 mb-4">Prerequisites for Building</h3>
            
            <h4 className="text-lg font-medium text-gray-700 mb-3">Linux (Ubuntu/Debian)</h4>
            <CodeBlock
              title="Terminal"
              code={`# Install build dependencies
sudo apt-get update
sudo apt-get install -y build-essential git golang-go

# For system tray support
sudo apt-get install -y libayatana-appindicator3-dev libgtk-3-dev`}
            />
            
            <h4 className="text-lg font-medium text-gray-700 mb-3">macOS</h4>
            <CodeBlock
              title="Terminal"
              code={`# Install Xcode Command Line Tools
xcode-select --install

# Install Homebrew if not present
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Go
brew install go`}
            />
            
            <h3 className="text-xl font-semibold text-gray-800 mb-4 mt-8">Build Process</h3>
            <CodeBlock
              title="Terminal"
              code={`# Clone repository
git clone https://github.com/penguintechinc/WaddlePerf.git
cd WaddlePerf/go-client

# Install dependencies
go mod download

# Build with system tray support
go build -o waddleperf ./cmd/waddleperf

# Build without system tray (no GTK dependencies)
go build -tags nosystray -o waddleperf ./cmd/waddleperf

# Install to system
sudo mv waddleperf /usr/local/bin/`}
            />
          </section>

          {/* Thin Client Installation */}
          <section id="thin-client" className="bg-white rounded-lg shadow-lg p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Thin Client Installation</h2>
            <p className="text-gray-600 mb-6">Quick installation scripts for minimal setup.</p>
            
            <h3 className="text-xl font-semibold text-gray-800 mb-4">Linux/macOS</h3>
            <CodeBlock
              title="Terminal"
              code={`curl -sSL https://raw.githubusercontent.com/penguintechinc/WaddlePerf/main/client/thin-installers/debian-thininstall.sh | bash`}
            />
            
            <h3 className="text-xl font-semibold text-gray-800 mb-4 mt-8">Windows (PowerShell as Administrator)</h3>
            <CodeBlock
              title="PowerShell"
              code={`Invoke-WebRequest -Uri https://raw.githubusercontent.com/penguintechinc/WaddlePerf/main/client/thin-installers/windows-thininstall.ps -OutFile install.ps1
./install.ps1`}
            />
          </section>

          {/* Configuration */}
          <section id="configuration" className="bg-white rounded-lg shadow-lg p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Configuration</h2>
            
            <h3 className="text-xl font-semibold text-gray-800 mb-4">Environment Variables</h3>
            
            <h4 className="text-lg font-medium text-gray-700 mb-3">Client Configuration</h4>
            <CodeBlock
              title="Terminal"
              code={`export WADDLEPERF_SERVER=server.example.com:8080
export WADDLEPERF_LOG_LEVEL=info
export WADDLEPERF_INTERVAL=3600
export WADDLEPERF_AUTOSTART=true`}
            />
            
            <h4 className="text-lg font-medium text-gray-700 mb-3">Server Configuration</h4>
            <CodeBlock
              title="Terminal"
              code={`export LISTEN_PORT=80
export SSL_PORT=443
export IPERF_PORT=5201
export UDP_PORT=2000
export ENABLE_GEOIP=true`}
            />
            
            <h3 className="text-xl font-semibold text-gray-800 mb-4 mt-8">Configuration Files</h3>
            
            <h4 className="text-lg font-medium text-gray-700 mb-3">Go Client Configuration (~/.waddleperf.yaml)</h4>
            <CodeBlock
              title="~/.waddleperf.yaml"
              language="yaml"
              code={`server: server.example.com:8080
interval: 3600
autostart: true
log-file: /var/log/waddleperf.log
verbose: false`}
            />
            
            <h4 className="text-lg font-medium text-gray-700 mb-3">Docker Configuration (/client/vars/base.yml)</h4>
            <CodeBlock
              title="/client/vars/base.yml"
              language="yaml"
              code={`TARGET_SERVER: server.example.com
TEST_INTERVAL: 3600
S3_BUCKET: waddleperf-results
S3_ENDPOINT: s3.amazonaws.com`}
            />
          </section>

          {/* Verification */}
          <section id="verification" className="bg-white rounded-lg shadow-lg p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Verification</h2>
            <p className="text-gray-600 mb-6">Verify your installation is working correctly.</p>
            
            <h3 className="text-xl font-semibold text-gray-800 mb-4">Test Commands</h3>
            <CodeBlock
              title="Terminal"
              code={`# Go Client
waddleperf info
waddleperf run -s server.example.com

# Docker
docker exec waddleperf-client python3 /app/bins/getSysInfo.py

# Check logs
docker logs waddleperf-client
docker logs waddleperf-server`}
            />
            
            <h3 className="text-xl font-semibold text-gray-800 mb-4 mt-8">Health Checks</h3>
            <ul className="list-disc list-inside text-gray-600">
              <li><strong>Client Web UI:</strong> <a href="http://localhost:8080" target="_blank" className="text-blue-600 hover:text-blue-800">http://localhost:8080</a></li>
              <li><strong>Server Status:</strong> <code className="bg-gray-100 px-2 py-1 rounded">http://server-ip/health</code></li>
              <li><strong>iperf3 Test:</strong> <code className="bg-gray-100 px-2 py-1 rounded">iperf3 -c server-ip -p 5201</code></li>
            </ul>
          </section>

          {/* Troubleshooting */}
          <section id="troubleshooting" className="bg-white rounded-lg shadow-lg p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Troubleshooting</h2>
            
            <h3 className="text-xl font-semibold text-gray-800 mb-4">Common Issues</h3>
            
            <div className="space-y-4">
              <details className="border rounded-lg p-4">
                <summary className="font-semibold cursor-pointer">Permission Denied Errors</summary>
                <div className="mt-4">
                  <CodeBlock
                    title="Terminal"
                    code={`# Fix permissions
sudo chown -R $(whoami):$(whoami) /opt/waddleperf
chmod +x /usr/local/bin/waddleperf`}
                  />
                </div>
              </details>
              
              <details className="border rounded-lg p-4">
                <summary className="font-semibold cursor-pointer">Port Already in Use</summary>
                <div className="mt-4">
                  <CodeBlock
                    title="Terminal"
                    code={`# Check what's using the port
sudo lsof -i :8080
sudo netstat -tulpn | grep 8080

# Kill the process or change port
docker run -p 8081:8080 ...`}
                  />
                </div>
              </details>
              
              <details className="border rounded-lg p-4">
                <summary className="font-semibold cursor-pointer">System Tray Not Working (Linux)</summary>
                <div className="mt-4">
                  <CodeBlock
                    title="Terminal"
                    code={`# Install required libraries
sudo apt-get install libayatana-appindicator3-dev libgtk-3-dev

# Or build without system tray
go build -tags nosystray -o waddleperf ./cmd/waddleperf`}
                  />
                </div>
              </details>
              
              <details className="border rounded-lg p-4">
                <summary className="font-semibold cursor-pointer">Python Module Errors</summary>
                <div className="mt-4">
                  <CodeBlock
                    title="Terminal"
                    code={`# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt`}
                  />
                </div>
              </details>
            </div>
          </section>

          {/* Next Steps */}
          <section id="next-steps" className="bg-white rounded-lg shadow-lg p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Next Steps</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Link href="/docs/usage" className="block p-6 bg-gray-50 border border-gray-200 rounded-lg hover:bg-gray-100 transition-colors">
                <h3 className="mb-2 text-xl font-bold tracking-tight text-gray-900">Usage Guide</h3>
                <p className="font-normal text-gray-700">Learn how to use WaddlePerf for network testing</p>
              </Link>
              <Link href="/docs/autoperf" className="block p-6 bg-gray-50 border border-gray-200 rounded-lg hover:bg-gray-100 transition-colors">
                <h3 className="mb-2 text-xl font-bold tracking-tight text-gray-900">AutoPerf Mode</h3>
                <p className="font-normal text-gray-700">Set up continuous monitoring with alerts</p>
              </Link>
              <Link href="/docs/architecture" className="block p-6 bg-gray-50 border border-gray-200 rounded-lg hover:bg-gray-100 transition-colors">
                <h3 className="mb-2 text-xl font-bold tracking-tight text-gray-900">Architecture</h3>
                <p className="font-normal text-gray-700">Understand WaddlePerf's system design</p>
              </Link>
              <a href="https://github.com/penguintechinc/WaddlePerf" target="_blank" className="block p-6 bg-gray-50 border border-gray-200 rounded-lg hover:bg-gray-100 transition-colors">
                <h3 className="mb-2 text-xl font-bold tracking-tight text-gray-900">GitHub Repository</h3>
                <p className="font-normal text-gray-700">View source code and contribute</p>
              </a>
            </div>
          </section>
        </div>

        {/* Navigation Footer */}
        <div className="mt-8 flex justify-between">
          <Link
            href="/docs"
            className="inline-flex items-center text-blue-600 hover:text-blue-800 font-medium"
          >
            ← Back to Documentation
          </Link>
          <Link
            href="/docs/usage"
            className="inline-flex items-center text-blue-600 hover:text-blue-800 font-medium"
          >
            Next: Usage Guide →
          </Link>
        </div>
      </div>
    </div>
  )
}