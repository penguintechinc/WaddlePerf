import Link from 'next/link'

export default function ArchitecturePage() {
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
            🏗️ Architecture
          </h1>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-8">
          <div className="prose prose-lg max-w-none">
            <h2>System Architecture Overview</h2>
            <p>WaddlePerf follows a distributed client-server architecture optimized for scalable network performance testing.</p>
            
            <h3>🏢 Core Components</h3>
            
            <div className="grid gap-6 my-8">
              <div className="border rounded-lg p-6 border-blue-200 bg-blue-50">
                <h4 className="text-blue-800 font-semibold text-lg mb-3">🖥️ WaddlePerf Server</h4>
                <ul>
                  <li><strong>py4web Framework:</strong> Modern Python web application</li>
                  <li><strong>Docker Containerized:</strong> Easy deployment and scaling</li>
                  <li><strong>Multi-protocol Support:</strong> HTTP, UDP, TCP, WebSocket</li>
                  <li><strong>Database Integration:</strong> Performance data storage and analytics</li>
                </ul>
              </div>
              
              <div className="border rounded-lg p-6 border-green-200 bg-green-50">
                <h4 className="text-green-800 font-semibold text-lg mb-3">📱 Go Desktop Client</h4>
                <ul>
                  <li><strong>Cross-platform:</strong> Windows, macOS, Linux</li>
                  <li><strong>System Tray Integration:</strong> Background monitoring</li>
                  <li><strong>Resource Optimized:</strong> Minimal CPU and memory usage</li>
                  <li><strong>Connection Pooling:</strong> Efficient network utilization</li>
                </ul>
              </div>
              
              <div className="border rounded-lg p-6 border-purple-200 bg-purple-50">
                <h4 className="text-purple-800 font-semibold text-lg mb-3">🐍 Python Client Tools</h4>
                <ul>
                  <li><strong>Async/Threading:</strong> High-performance concurrent testing</li>
                  <li><strong>Modular Design:</strong> Independent testing tools</li>
                  <li><strong>JSON Output:</strong> Machine-readable results</li>
                  <li><strong>CLI Interface:</strong> Scriptable and automatable</li>
                </ul>
              </div>
            </div>
            
            <h3>🔧 Testing Tools</h3>
            <ul>
              <li><strong>speedtest.py:</strong> Bandwidth measurement (upload/download)</li>
              <li><strong>httptrace_async.py:</strong> HTTP performance analysis</li>
              <li><strong>udpping_async.py:</strong> UDP connectivity testing</li>
              <li><strong>resolverTime_async.py:</strong> DNS resolution timing</li>
            </ul>
            
            <h3>📊 Data Flow</h3>
            <ol>
              <li><strong>Test Execution:</strong> Client initiates performance tests</li>
              <li><strong>Data Collection:</strong> Metrics gathered during test execution</li>
              <li><strong>Result Transmission:</strong> JSON results sent to server</li>
              <li><strong>Storage & Analytics:</strong> Server processes and stores data</li>
              <li><strong>Visualization:</strong> Web interface displays results and trends</li>
            </ol>
            
            <h3>🚀 Performance Optimizations</h3>
            <ul>
              <li><strong>Async I/O:</strong> Non-blocking network operations</li>
              <li><strong>Connection Reuse:</strong> HTTP keep-alive and pooling</li>
              <li><strong>Concurrent Testing:</strong> Parallel test execution</li>
              <li><strong>Resource Management:</strong> Automatic cleanup and garbage collection</li>
            </ul>
            
            <h3>🔒 Security Features</h3>
            <ul>
              <li><strong>TLS Encryption:</strong> Secure data transmission</li>
              <li><strong>Token Authentication:</strong> API access control</li>
              <li><strong>Input Validation:</strong> Protection against injection attacks</li>
              <li><strong>Rate Limiting:</strong> DDoS prevention</li>
            </ul>
            
            <h3>📈 Scalability</h3>
            <ul>
              <li><strong>Horizontal Scaling:</strong> Multiple server instances</li>
              <li><strong>Load Balancing:</strong> Distribute client connections</li>
              <li><strong>Database Sharding:</strong> Handle large datasets</li>
              <li><strong>CDN Integration:</strong> Global performance testing</li>
            </ul>
            
            <div className="bg-orange-50 border-l-4 border-orange-400 p-4 my-6">
              <div className="flex">
                <div className="ml-3">
                  <p className="text-sm text-orange-700">
                    <strong>🏗️ Design Principle:</strong> WaddlePerf prioritizes accuracy, efficiency, and ease of deployment while maintaining comprehensive testing capabilities.
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