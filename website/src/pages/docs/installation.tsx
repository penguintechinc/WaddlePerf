import Link from 'next/link'
import { GetStaticProps } from 'next'
import { useState } from 'react'

interface InstallationPageProps {
  content: string
}

export default function InstallationPage({ content }: InstallationPageProps) {
  const [activeTab, setActiveTab] = useState('docker')
  
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
        <div className="bg-white rounded-lg shadow-lg p-8">
          <div 
            className="prose prose-lg max-w-none"
            dangerouslySetInnerHTML={{ __html: content }}
          />
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

export const getStaticProps: GetStaticProps = async () => {
  const content = `
    <h2 id="prerequisites">Prerequisites</h2>
    
    <h3>System Requirements</h3>
    <table class="min-w-full divide-y divide-gray-200">
      <thead>
        <tr>
          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Component</th>
          <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Requirements</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-gray-200">
        <tr>
          <td class="px-6 py-4 whitespace-nowrap">Operating System</td>
          <td class="px-6 py-4">Linux (Ubuntu 20.04+, Debian 11+, RHEL 8+), Windows 10/11, macOS 10.15+</td>
        </tr>
        <tr>
          <td class="px-6 py-4 whitespace-nowrap">Memory</td>
          <td class="px-6 py-4">Minimum 512MB RAM (1GB+ recommended)</td>
        </tr>
        <tr>
          <td class="px-6 py-4 whitespace-nowrap">Disk Space</td>
          <td class="px-6 py-4">100MB for client, 500MB for server</td>
        </tr>
        <tr>
          <td class="px-6 py-4 whitespace-nowrap">Network</td>
          <td class="px-6 py-4">Outbound connectivity to target servers</td>
        </tr>
        <tr>
          <td class="px-6 py-4 whitespace-nowrap">Software</td>
          <td class="px-6 py-4">Python 3.9+ or Go 1.21+ (for building from source)</td>
        </tr>
      </tbody>
    </table>

    <h3>Network Ports</h3>
    <div class="bg-yellow-50 border-l-4 border-yellow-400 p-4 my-6">
      <div class="flex">
        <div class="flex-shrink-0">
          <svg class="h-5 w-5 text-yellow-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
          </svg>
        </div>
        <div class="ml-3">
          <p class="text-sm text-yellow-700">
            <strong>Important:</strong> Ensure the following ports are accessible:
          </p>
          <ul class="list-disc list-inside text-sm text-yellow-700 mt-2">
            <li>HTTP: 80</li>
            <li>HTTPS: 443</li>
            <li>Web UI: 8080</li>
            <li>iperf3: 5201</li>
            <li>UDP Ping: 2000/udp</li>
          </ul>
        </div>
      </div>
    </div>

    <h2 id="docker">Docker Installation (Recommended)</h2>
    <p>The fastest way to get started with WaddlePerf is using Docker containers.</p>
    
    <h3>Full Stack with Docker Compose</h3>
    <pre><code># Clone the repository
git clone https://github.com/penguintechinc/WaddlePerf.git
cd WaddlePerf

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f</code></pre>

    <h3>Individual Container Deployment</h3>
    <h4>Deploy Client Container</h4>
    <pre><code>docker run -d \\
  --name waddleperf-client \\
  -p 8080:8080 \\
  -e TARGET_SERVER=your-server-address \\
  ghcr.io/penguincloud/waddleperf-client:latest</code></pre>

    <h4>Deploy Server Container</h4>
    <pre><code>docker run -d \\
  --name waddleperf-server \\
  -p 80:80 -p 443:443 -p 5201:5201 -p 2000:2000/udp \\
  ghcr.io/penguincloud/waddleperf-server:latest</code></pre>

    <div class="bg-green-50 border-l-4 border-green-400 p-4 my-6">
      <div class="flex">
        <div class="ml-3">
          <p class="text-sm text-green-700">
            <strong>Pro Tip:</strong> Docker installation handles all dependencies automatically and provides consistent environments across platforms.
          </p>
        </div>
      </div>
    </div>

    <h2 id="binary">Binary Installation</h2>
    <p>Download pre-built binaries for your platform from <a href="https://github.com/penguintechinc/WaddlePerf/releases" target="_blank" rel="noopener" class="text-blue-600 hover:text-blue-800">GitHub Releases</a>.</p>
    
    <h3>Linux Installation</h3>
    <h4>AMD64 Architecture</h4>
    <pre><code>wget https://github.com/penguintechinc/WaddlePerf/releases/latest/download/waddleperf-linux-amd64.tar.gz
tar xzf waddleperf-linux-amd64.tar.gz
sudo mv waddleperf /usr/local/bin/
sudo chmod +x /usr/local/bin/waddleperf</code></pre>
    
    <h4>ARM64 Architecture</h4>
    <pre><code>wget https://github.com/penguintechinc/WaddlePerf/releases/latest/download/waddleperf-linux-arm64.tar.gz
tar xzf waddleperf-linux-arm64.tar.gz
sudo mv waddleperf /usr/local/bin/
sudo chmod +x /usr/local/bin/waddleperf</code></pre>
    
    <h3>macOS Installation (Universal Binary)</h3>
    <pre><code>wget https://github.com/penguintechinc/WaddlePerf/releases/latest/download/waddleperf-macos-universal.tar.gz
tar xzf waddleperf-macos-universal.tar.gz
sudo mv waddleperf /usr/local/bin/
sudo chmod +x /usr/local/bin/waddleperf</code></pre>
    
    <h3>Windows Installation</h3>
    <p>Download and extract the appropriate ZIP file:</p>
    <ul>
      <li><code>waddleperf-windows-amd64.zip</code> for 64-bit systems</li>
      <li><code>waddleperf-windows-arm64.zip</code> for ARM systems</li>
    </ul>
    <p>Add the extracted directory to your PATH environment variable.</p>

    <h2 id="source">Building from Source</h2>
    <p>Build WaddlePerf from source for custom configurations or development.</p>
    
    <h3>Prerequisites for Building</h3>
    <h4>Linux (Ubuntu/Debian)</h4>
    <pre><code># Install build dependencies
sudo apt-get update
sudo apt-get install -y build-essential git golang-go

# For system tray support
sudo apt-get install -y libayatana-appindicator3-dev libgtk-3-dev</code></pre>
    
    <h4>macOS</h4>
    <pre><code># Install Xcode Command Line Tools
xcode-select --install

# Install Homebrew if not present
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Go
brew install go</code></pre>
    
    <h3>Build Process</h3>
    <pre><code># Clone repository
git clone https://github.com/penguintechinc/WaddlePerf.git
cd WaddlePerf/go-client

# Install dependencies
go mod download

# Build with system tray support
go build -o waddleperf ./cmd/waddleperf

# Build without system tray (no GTK dependencies)
go build -tags nosystray -o waddleperf ./cmd/waddleperf

# Install to system
sudo mv waddleperf /usr/local/bin/</code></pre>

    <h2 id="thin-client">Thin Client Installation</h2>
    <p>Quick installation scripts for minimal setup.</p>
    
    <h3>Linux/macOS</h3>
    <pre><code>curl -sSL https://raw.githubusercontent.com/penguintechinc/WaddlePerf/main/client/thin-installers/debian-thininstall.sh | bash</code></pre>
    
    <h3>Windows (PowerShell as Administrator)</h3>
    <pre><code>Invoke-WebRequest -Uri https://raw.githubusercontent.com/penguintechinc/WaddlePerf/main/client/thin-installers/windows-thininstall.ps -OutFile install.ps1
./install.ps1</code></pre>

    <h2 id="configuration">Configuration</h2>
    
    <h3>Environment Variables</h3>
    <h4>Client Configuration</h4>
    <pre><code>export WADDLEPERF_SERVER=server.example.com:8080
export WADDLEPERF_LOG_LEVEL=info
export WADDLEPERF_INTERVAL=3600
export WADDLEPERF_AUTOSTART=true</code></pre>
    
    <h4>Server Configuration</h4>
    <pre><code>export LISTEN_PORT=80
export SSL_PORT=443
export IPERF_PORT=5201
export UDP_PORT=2000
export ENABLE_GEOIP=true</code></pre>
    
    <h3>Configuration Files</h3>
    <h4>Go Client Configuration (~/.waddleperf.yaml)</h4>
    <pre><code>server: server.example.com:8080
interval: 3600
autostart: true
log-file: /var/log/waddleperf.log
verbose: false</code></pre>
    
    <h4>Docker Configuration (/client/vars/base.yml)</h4>
    <pre><code>TARGET_SERVER: server.example.com
TEST_INTERVAL: 3600
S3_BUCKET: waddleperf-results
S3_ENDPOINT: s3.amazonaws.com</code></pre>

    <h2 id="verification">Verification</h2>
    <p>Verify your installation is working correctly.</p>
    
    <h3>Test Commands</h3>
    <pre><code># Go Client
waddleperf info
waddleperf run -s server.example.com

# Docker
docker exec waddleperf-client python3 /app/bins/getSysInfo.py

# Check logs
docker logs waddleperf-client
docker logs waddleperf-server</code></pre>
    
    <h3>Health Checks</h3>
    <ul>
      <li><strong>Client Web UI:</strong> <a href="http://localhost:8080" target="_blank">http://localhost:8080</a></li>
      <li><strong>Server Status:</strong> <code>http://server-ip/health</code></li>
      <li><strong>iperf3 Test:</strong> <code>iperf3 -c server-ip -p 5201</code></li>
    </ul>

    <h2 id="troubleshooting">Troubleshooting</h2>
    
    <h3>Common Issues</h3>
    
    <div class="space-y-4">
      <details class="border rounded-lg p-4">
        <summary class="font-semibold cursor-pointer">Permission Denied Errors</summary>
        <pre class="mt-4"><code># Fix permissions
sudo chown -R $(whoami):$(whoami) /opt/waddleperf
chmod +x /usr/local/bin/waddleperf</code></pre>
      </details>
      
      <details class="border rounded-lg p-4">
        <summary class="font-semibold cursor-pointer">Port Already in Use</summary>
        <pre class="mt-4"><code># Check what's using the port
sudo lsof -i :8080
sudo netstat -tulpn | grep 8080

# Kill the process or change port
docker run -p 8081:8080 ...</code></pre>
      </details>
      
      <details class="border rounded-lg p-4">
        <summary class="font-semibold cursor-pointer">System Tray Not Working (Linux)</summary>
        <pre class="mt-4"><code># Install required libraries
sudo apt-get install libayatana-appindicator3-dev libgtk-3-dev

# Or build without system tray
go build -tags nosystray -o waddleperf ./cmd/waddleperf</code></pre>
      </details>
      
      <details class="border rounded-lg p-4">
        <summary class="font-semibold cursor-pointer">Python Module Errors</summary>
        <pre class="mt-4"><code># Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt</code></pre>
      </details>
    </div>

    <h2 id="next-steps">Next Steps</h2>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
      <a href="/docs/usage" class="block p-6 bg-white border border-gray-200 rounded-lg shadow hover:bg-gray-50">
        <h3 class="mb-2 text-xl font-bold tracking-tight text-gray-900">Usage Guide</h3>
        <p class="font-normal text-gray-700">Learn how to use WaddlePerf for network testing</p>
      </a>
      <a href="/docs/autoperf" class="block p-6 bg-white border border-gray-200 rounded-lg shadow hover:bg-gray-50">
        <h3 class="mb-2 text-xl font-bold tracking-tight text-gray-900">AutoPerf Mode</h3>
        <p class="font-normal text-gray-700">Set up continuous monitoring with alerts</p>
      </a>
      <a href="/docs/architecture" class="block p-6 bg-white border border-gray-200 rounded-lg shadow hover:bg-gray-50">
        <h3 class="mb-2 text-xl font-bold tracking-tight text-gray-900">Architecture</h3>
        <p class="font-normal text-gray-700">Understand WaddlePerf's system design</p>
      </a>
      <a href="https://github.com/penguintechinc/WaddlePerf" target="_blank" class="block p-6 bg-white border border-gray-200 rounded-lg shadow hover:bg-gray-50">
        <h3 class="mb-2 text-xl font-bold tracking-tight text-gray-900">GitHub Repository</h3>
        <p class="font-normal text-gray-700">View source code and contribute</p>
      </a>
    </div>
  `

  return {
    props: {
      content
    }
  }
}