import Link from 'next/link'

export default function AutoPerfPage() {
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
            🤖 AutoPerf Mode
          </h1>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-8">
          <div className="prose prose-lg max-w-none">
            <h2>Automated Network Performance Monitoring</h2>
            <p>AutoPerf provides intelligent, tiered performance testing that scales monitoring intensity based on network conditions.</p>
            
            <h3>📊 How AutoPerf Works</h3>
            <p>AutoPerf uses a three-tier approach to optimize monitoring resources while ensuring comprehensive coverage:</p>
            
            <div className="grid gap-6 my-8">
              <div className="border rounded-lg p-6 border-green-200 bg-green-50">
                <h4 className="text-green-800 font-semibold text-lg mb-3">🟢 Tier 1 - Baseline Monitoring</h4>
                <ul>
                  <li>Runs basic connectivity tests every X minutes (configurable)</li>
                  <li>Lightweight tests: ping, basic HTTP, DNS lookup</li>
                  <li>Minimal system resource usage</li>
                  <li>Establishes performance baseline</li>
                </ul>
              </div>
              
              <div className="border rounded-lg p-6 border-yellow-200 bg-yellow-50">
                <h4 className="text-yellow-800 font-semibold text-lg mb-3">🟡 Tier 2 - Enhanced Testing</h4>
                <ul>
                  <li>Triggered when Tier 1 thresholds are exceeded</li>
                  <li>More comprehensive tests: bandwidth, detailed latency</li>
                  <li>Increased testing frequency</li>
                  <li>Identifies performance degradation patterns</li>
                </ul>
              </div>
              
              <div className="border rounded-lg p-6 border-red-200 bg-red-50">
                <h4 className="text-red-800 font-semibold text-lg mb-3">🔴 Tier 3 - Comprehensive Diagnostics</h4>
                <ul>
                  <li>Triggered when Tier 2 thresholds are exceeded</li>
                  <li>Full diagnostic suite: traceroute, advanced HTTP traces</li>
                  <li>Maximum testing detail and frequency</li>
                  <li>Problem identification and root cause analysis</li>
                </ul>
              </div>
            </div>
            
            <h3>⚙️ Configuration</h3>
            <p>Each tool must be configured with tier assignment and thresholds:</p>
            <pre><code># Example AutoPerf configuration
autoperf:
  tier1:
    interval: 300  # 5 minutes
    tools:
      - ping
      - dns
    thresholds:
      latency_ms: 100
      packet_loss: 5
      
  tier2:
    tools:
      - speedtest
      - http_trace
    thresholds:
      bandwidth_mbps: 10
      response_time_ms: 1000
      
  tier3:
    tools:
      - traceroute
      - comprehensive_http
    thresholds:
      critical_latency_ms: 500</code></pre>
            
            <h3>📈 Benefits</h3>
            <ul>
              <li><strong>Resource Efficiency</strong>: Only runs intensive tests when needed</li>
              <li><strong>Early Detection</strong>: Catches performance issues before they become critical</li>
              <li><strong>Scalable Monitoring</strong>: Adapts testing intensity to network conditions</li>
              <li><strong>Comprehensive Coverage</strong>: Full diagnostic capability when required</li>
            </ul>
            
            <h3>🎯 Use Cases</h3>
            <ul>
              <li><strong>Enterprise Networks</strong>: Monitor critical connections with minimal overhead</li>
              <li><strong>Remote Workers</strong>: Ensure stable connectivity for productivity</li>
              <li><strong>Service Providers</strong>: Proactive network quality assurance</li>
              <li><strong>DevOps Teams</strong>: Continuous infrastructure monitoring</li>
            </ul>
            
            <div className="bg-blue-50 border-l-4 border-blue-400 p-4 my-6">
              <div className="flex">
                <div className="ml-3">
                  <p className="text-sm text-blue-700">
                    <strong>💡 Note:</strong> AutoPerf requires tools to be properly configured with tier assignments and enabled status for optimal operation.
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