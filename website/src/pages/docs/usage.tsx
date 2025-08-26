import Link from 'next/link'
import { GetStaticProps } from 'next'

export default function UsagePage() {
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
            🚀 Usage Guide
          </h1>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-8">
          <div className="prose prose-lg max-w-none">
            <h2>Getting Started with WaddlePerf</h2>
            <p>WaddlePerf provides comprehensive network performance testing with multiple testing modes and detailed analytics.</p>
            
            <h3>🎯 Basic Testing</h3>
            <p>Run a single performance test:</p>
            <pre><code>waddleperf run --server your-server:8080</code></pre>
            
            <h3>📊 System Tray Mode</h3>
            <p>Continuous monitoring with system tray integration:</p>
            <pre><code>waddleperf tray --server your-server:8080 --autostart --interval 3600</code></pre>
            
            <h3>🔧 Configuration Options</h3>
            <ul>
              <li><strong>--server</strong>: WaddlePerf server address</li>
              <li><strong>--verbose</strong>: Enable detailed logging</li>
              <li><strong>--config</strong>: Specify configuration file</li>
              <li><strong>--interval</strong>: Test interval in seconds</li>
              <li><strong>--log-file</strong>: Log file location</li>
            </ul>
            
            <h3>📈 Test Types</h3>
            <ul>
              <li><strong>Speed Test</strong>: Upload/download bandwidth testing</li>
              <li><strong>Latency Test</strong>: Round-trip time measurements</li>
              <li><strong>HTTP Trace</strong>: Detailed HTTP performance analysis</li>
              <li><strong>DNS Resolution</strong>: DNS lookup time testing</li>
              <li><strong>UDP Ping</strong>: UDP connectivity and response time</li>
            </ul>
            
            <h3>🏗️ AutoPerf Mode</h3>
            <p>Automated tiered testing based on performance thresholds:</p>
            <ul>
              <li><strong>Tier 1</strong>: Basic continuous monitoring (every X minutes)</li>
              <li><strong>Tier 2</strong>: Enhanced testing when Tier 1 thresholds exceeded</li>
              <li><strong>Tier 3</strong>: Comprehensive diagnostics when Tier 2 thresholds exceeded</li>
            </ul>
            
            <h3>📋 System Information</h3>
            <p>View detailed system and network information:</p>
            <pre><code>waddleperf info</code></pre>
            
            <h3>⚙️ Configuration File</h3>
            <p>Create <code>~/.waddleperf.yaml</code> with your settings:</p>
            <pre><code>server: "your-server:8080"
verbose: true
interval: 3600
autostart: true
log-file: "/var/log/waddleperf.log"</code></pre>
            
            <div className="bg-green-50 border-l-4 border-green-400 p-4 my-6">
              <div className="flex">
                <div className="ml-3">
                  <p className="text-sm text-green-700">
                    <strong>💡 Pro Tip:</strong> Use system tray mode for continuous monitoring while maintaining normal system usage.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}