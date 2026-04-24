import { useState, FormEvent, useEffect } from 'react'
import { websocketService } from '../services/websocket'
import './TraceTest.css'
import {
  validateTarget,
  validateTimeout,
  sanitizeString,
  MAX_TARGET_LENGTH,
} from '../utils/validation'

interface TraceTestProps {
  isAuthenticated: boolean
}

interface TraceResult {
  test_type: string
  target: string
  hops?: string[]
  route_info?: any
  latency_ms?: number
  success: boolean
  error?: string
  raw_results?: any
}

function TraceTest({ isAuthenticated }: TraceTestProps) {
  const [testType, setTestType] = useState<'http' | 'tcp' | 'icmp'>('http')
  const [target, setTarget] = useState('')
  const [port, setPort] = useState('443')
  const [timeout, setTimeout] = useState('30')
  const [isRunning, setIsRunning] = useState(false)
  const [result, setResult] = useState<TraceResult | null>(null)
  const [validationError, setValidationError] = useState<string>('')
  const [showDetailedResults, setShowDetailedResults] = useState(false)

  const defaultPorts: Record<string, string> = {
    http: '443',
    tcp: '22',
    icmp: '',
  }

  useEffect(() => {
    // Set up websocket listeners
    websocketService.onTestComplete((data: any) => {
      if (isRunning) {
        console.log('[TraceTest] Test complete:', data)
        setResult(data)
        setIsRunning(false)
      }
    })

    websocketService.onError((error: any) => {
      if (isRunning) {
        console.error('[TraceTest] Test error:', error)
        setValidationError(error.error || 'Test failed')
        setIsRunning(false)
      }
    })
  }, [isRunning])

  const handleTestTypeChange = (newType: 'http' | 'tcp' | 'icmp') => {
    setTestType(newType)
    setPort(defaultPorts[newType] || '')
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setValidationError('')
    setResult(null)

    if (!isAuthenticated) {
      setValidationError('You must be logged in to run tests')
      return
    }

    // Validate target
    const targetResult = validateTarget(target)
    if (!targetResult.valid) {
      setValidationError(targetResult.error || 'Invalid target')
      return
    }

    // Validate timeout
    const timeoutResult = validateTimeout(timeout)
    if (!timeoutResult.valid) {
      setValidationError(timeoutResult.error || 'Invalid timeout')
      return
    }

    setIsRunning(true)

    try {
      const sessionId = sessionStorage.getItem('session_id')
      const testData = {
        test_type: testType === 'http' ? 'http_trace' : testType === 'tcp' ? 'tcp_trace' : 'traceroute',
        target: sanitizeString(target, MAX_TARGET_LENGTH),
        port: port && testType !== 'icmp' ? parseInt(port, 10) : undefined,
        timeout: parseInt(timeout, 10),
        session_id: sessionId || undefined,
      }

      console.log('[TraceTest] Submitting trace test:', testData)

      // Send test via WebSocket
      websocketService.startTest(testData)

      // Listen for result - we'll use a timeout since we can't easily hook into websocket events
      // The test will complete via websocket but we need a different approach
      // For now, poll or wait for response
      console.log('[TraceTest] Test started, waiting for results...')
    } catch (error) {
      console.error('[TraceTest] Error:', error)
      setValidationError('Failed to start test')
      setIsRunning(false)
    }
  }

  const formatHops = (hops: string[] | undefined) => {
    if (!hops || hops.length === 0) return 'No route information available'
    return hops.map((hop, index) => `${index + 1}. ${hop}`).join('\n')
  }

  const downloadDetailedResults = () => {
    if (!result) return

    const dataToDownload = result.raw_results || result
    const jsonString = JSON.stringify(dataToDownload, null, 2)
    /* v8 ignore next 8 */
    const blob = new Blob([jsonString], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `trace-results-${result.target || 'unknown'}-${new Date().toISOString()}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="trace-test-container">
      <div className="trace-test-header">
        <h2>Trace Tests</h2>
        <p>Trace network routes and analyze connection paths</p>
      </div>

      <div className="trace-test-content">
        <form onSubmit={handleSubmit} className="trace-form">
          {validationError && (
            <div className="error-box" style={{ marginBottom: '1rem', padding: '0.75rem', backgroundColor: 'var(--error-bg, #fee)', border: '1px solid var(--error-border, #f88)', borderRadius: '4px', color: 'var(--error-text, #c00)' }}>
              <strong>Error:</strong> {validationError}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="test-type">Trace Type</label>
            <div className="test-type-buttons">
              <button
                type="button"
                className={`test-type-btn ${testType === 'http' ? 'active' : ''}`}
                onClick={() => handleTestTypeChange('http')}
                disabled={isRunning}
              >
                HTTP Trace
              </button>
              <button
                type="button"
                className={`test-type-btn ${testType === 'tcp' ? 'active' : ''}`}
                onClick={() => handleTestTypeChange('tcp')}
                disabled={isRunning}
              >
                TCP Trace
              </button>
              <button
                type="button"
                className={`test-type-btn ${testType === 'icmp' ? 'active' : ''}`}
                onClick={() => handleTestTypeChange('icmp')}
                disabled={isRunning}
              >
                Traceroute
              </button>
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="target">Target Host</label>
            <input
              type="text"
              id="target"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              placeholder={
                testType === 'http'
                  ? 'example.com or https://example.com'
                  : testType === 'icmp'
                  ? '8.8.8.8 or example.com'
                  : 'hostname or IP address'
              }
              required
              disabled={isRunning}
            />
          </div>

          {testType !== 'icmp' && (
            <div className="form-group">
              <label htmlFor="port">Port</label>
              <input
                type="number"
                id="port"
                value={port}
                onChange={(e) => setPort(e.target.value)}
                placeholder="Auto-detect"
                min="1"
                max="65535"
                disabled={isRunning}
              />
            </div>
          )}

          <div className="form-group">
            <label htmlFor="timeout">Timeout (s)</label>
            <input
              type="number"
              id="timeout"
              value={timeout}
              onChange={(e) => setTimeout(e.target.value)}
              min="1"
              max="300"
              required
              disabled={isRunning}
            />
          </div>

          <button type="submit" className="btn-start-test" disabled={isRunning || !target.trim()}>
            {isRunning ? (
              <>
                <span className="spinner-small"></span>
                Running Trace...
              </>
            ) : (
              'Start Trace'
            )}
          </button>
        </form>

        {result && (
          <div className="trace-results">
            <div className="results-header">
              <h3>Trace Results</h3>
              <span className={`status-badge ${result.success ? 'success' : 'error'}`}>
                {result.success ? 'Success' : 'Failed'}
              </span>
            </div>

            {result.error && (
              <div className="error-box">
                <strong>Error:</strong> {result.error}
              </div>
            )}

            <div className="result-summary">
              <div className="result-card">
                <div className="result-label">Target</div>
                <div className="result-value">{result.target || 'N/A'}</div>
              </div>
              {result.latency_ms !== undefined && (
                <div className="result-card">
                  <div className="result-label">Latency</div>
                  <div className="result-value">{result.latency_ms.toFixed(2)} ms</div>
                </div>
              )}
            </div>

            {result.hops && result.hops.length > 0 && (
              <div className="hops-section">
                <h4>Network Route</h4>
                <pre className="hops-output">{formatHops(result.hops)}</pre>
              </div>
            )}

            <div className="detailed-results-section">
              <button
                className="btn-view-details"
                onClick={() => setShowDetailedResults(true)}
              >
                View Detailed Results
              </button>
            </div>

            {showDetailedResults && result && (
              <div className="modal-overlay" onClick={() => setShowDetailedResults(false)}>
                <div className="modal-content modal-large" onClick={(e) => e.stopPropagation()}>
                  <div className="modal-header">
                    <h3>Full Trace Report</h3>
                    <div className="modal-header-actions">
                      <button className="btn-download-json" onClick={downloadDetailedResults}>
                        Download JSON
                      </button>
                      <button className="modal-close" onClick={() => setShowDetailedResults(false)}>×</button>
                    </div>
                  </div>
                  <div className="modal-body modal-body-columns">
                    <div className="modal-column summary-column">
                      <h4>Summary</h4>
                      <div className="summary-item">
                        <span className="summary-label">Target:</span>
                        <span className="summary-value">{result.target || 'N/A'}</span>
                      </div>
                      {result.latency_ms !== undefined && (
                        <div className="summary-item">
                          <span className="summary-label">Latency:</span>
                          <span className="summary-value">{result.latency_ms.toFixed(2)} ms</span>
                        </div>
                      )}
                      <div className="summary-item">
                        <span className="summary-label">Status:</span>
                        <span className={`summary-value ${result.success ? 'success-text' : 'error-text'}`}>
                          {result.success ? 'Success' : 'Failed'}
                        </span>
                      </div>
                      {result.error && (
                        <div className="summary-item">
                          <span className="summary-label">Error:</span>
                          <span className="summary-value error-text">{result.error}</span>
                        </div>
                      )}
                      {result.hops && result.hops.length > 0 && (
                        <div className="summary-item">
                          <span className="summary-label">Total Hops:</span>
                          <span className="summary-value">{result.hops.length}</span>
                        </div>
                      )}
                    </div>
                    <div className="modal-column details-column">
                      <h4>Detailed Results</h4>
                      {result.raw_results && Object.keys(result.raw_results).length > 0 ? (
                        <pre className="json-output">{JSON.stringify(result.raw_results, null, 2)}</pre>
                      ) : (
                        <pre className="json-output">{JSON.stringify(result, null, 2)}</pre>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default TraceTest
