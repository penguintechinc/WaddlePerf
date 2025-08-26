import Link from 'next/link'
import { GetStaticProps } from 'next'

interface InstallationPageProps {
  content: string
}

export default function InstallationPage({ content }: InstallationPageProps) {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-8">
          <Link
            href="/docs"
            className="inline-flex items-center text-blue-600 hover:text-blue-800 font-medium mb-4"
          >
            ← Back to Documentation
          </Link>
          <h1 className="text-4xl font-bold text-gray-900">
            🛠️ Installation Guide
          </h1>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-8">
          <div 
            className="prose prose-lg max-w-none"
            dangerouslySetInnerHTML={{ __html: content }}
          />
        </div>
      </div>
    </div>
  )
}

export const getStaticProps: GetStaticProps = async () => {
  const content = `
    <h2>Quick Start</h2>
    <p>Get WaddlePerf up and running in minutes with our streamlined installation process.</p>
    
    <h3>🐧 Linux Installation</h3>
    <p>Download and install the latest release:</p>
    <pre><code>git clone https://github.com/penguintechinc/WaddlePerf.git
cd WaddlePerf
docker-compose up -d</code></pre>
    
    <h3>📦 Binary Releases</h3>
    <p>Download from <a href="https://github.com/penguintechinc/WaddlePerf/releases" target="_blank" rel="noopener">GitHub Releases</a>:</p>
    
    <h4>Linux AMD64:</h4>
    <pre><code>wget https://github.com/penguintechinc/WaddlePerf/releases/latest/download/waddleperf-linux-amd64.tar.gz
tar -xzf waddleperf-linux-amd64.tar.gz
./waddleperf --help</code></pre>
    
    <h4>Linux ARM64:</h4>
    <pre><code>wget https://github.com/penguintechinc/WaddlePerf/releases/latest/download/waddleperf-linux-arm64.tar.gz
tar -xzf waddleperf-linux-arm64.tar.gz
./waddleperf --help</code></pre>
    
    <h4>macOS Universal:</h4>
    <pre><code>wget https://github.com/penguintechinc/WaddlePerf/releases/latest/download/waddleperf-macos-universal.tar.gz
tar -xzf waddleperf-macos-universal.tar.gz
./waddleperf --help</code></pre>
    
    <h3>🐳 Docker Installation</h3>
    <p>The easiest way to get started with WaddlePerf is using Docker:</p>
    <pre><code>git clone https://github.com/penguintechinc/WaddlePerf.git
cd WaddlePerf
docker-compose up -d</code></pre>
    
    <h3>📋 Requirements</h3>
    <ul>
      <li><strong>Server:</strong> Docker & Docker Compose, Python 3.8+</li>
      <li><strong>Client:</strong> Python 3.8+ or compiled binaries</li>
      <li><strong>Network:</strong> Open ports for testing (default: 8080, 2000-2010)</li>
    </ul>
    
    <h3>🎯 Quick Client Installation</h3>
    <p>For Debian/Ubuntu systems, use our quick installer:</p>
    <pre><code>curl -sSL https://raw.githubusercontent.com/penguintechinc/WaddlePerf/main/client/thin-installers/debian-thininstall.sh | bash</code></pre>
    
    <h3>⚙️ Configuration</h3>
    <p>After installation, configure your WaddlePerf client:</p>
    <pre><code># Edit configuration file
vim ~/.waddleperf.yaml

# Test connection
waddleperf run --server your-server:8080</code></pre>
    
    <h3>🚀 System Tray Mode</h3>
    <p>For continuous monitoring, run WaddlePerf in system tray mode:</p>
    <pre><code>waddleperf tray --server your-server:8080 --autostart</code></pre>
    
    <div class="bg-blue-50 border-l-4 border-blue-400 p-4 my-6">
      <div class="flex">
        <div class="ml-3">
          <p class="text-sm text-blue-700">
            <strong>💡 Tip:</strong> For production deployments, consider using the Docker setup for easier management and scaling.
          </p>
        </div>
      </div>
    </div>
  `

  return {
    props: {
      content
    }
  }
}