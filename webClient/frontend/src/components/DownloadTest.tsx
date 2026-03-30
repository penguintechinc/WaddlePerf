import { useState, useRef } from 'react'
import './DownloadTest.css'

interface DownloadTestProps {
  testServerUrl: string
}

interface DownloadResult {
  fileSize: number
  duration: number
  averageSpeed: number
  peakSpeed: number
  timestamp: number
}

function DownloadTest({ testServerUrl }: DownloadTestProps) {
  const [isRunning, setIsRunning] = useState(false)
  const [progress, setProgress] = useState(0)
  const [currentSpeed, setCurrentSpeed] = useState(0)
  const [peakSpeed, setPeakSpeed] = useState(0)
  const [bytesDownloaded, setBytesDownloaded] = useState(0)
  const [result, setResult] = useState<DownloadResult | null>(null)
  const [selectedSize, setSelectedSize] = useState(100) // Default 100MB
  const abortControllerRef = useRef<AbortController | null>(null)

  const fileSizeOptions = [
    { label: '10 MB', value: 10 },
    { label: '50 MB', value: 50 },
    { label: '100 MB', value: 100 },
    { label: '500 MB', value: 500 },
    { label: '1 GB', value: 1000 },
  ]

  const runDownloadTest = async () => {
    console.log(`[DownloadTest] Starting download test for ${selectedSize}MB...`)
    setIsRunning(true)
    setResult(null)
    setProgress(0)
    setCurrentSpeed(0)
    setPeakSpeed(0)
    setBytesDownloaded(0)

    abortControllerRef.current = new AbortController()
    const startTime = Date.now()
    let totalBytes = 0
    let maxSpeed = 0
    const chunkSizeMB = 10 // Download in 10MB chunks
    const targetBytes = selectedSize * 1024 * 1024
    let lastUpdateTime = startTime

    try {
      while (totalBytes < targetBytes) {
        if (abortControllerRef.current?.signal.aborted) {
          throw new Error('Download cancelled')
        }

        const remainingBytes = targetBytes - totalBytes
        const downloadSize = Math.min(chunkSizeMB, Math.ceil(remainingBytes / (1024 * 1024)))

        const response = await fetch(
          `${testServerUrl}/speedtest/download?size=${downloadSize}&t=${Date.now()}`,
          {
            method: 'GET',
            cache: 'no-cache',
            signal: abortControllerRef.current?.signal,
          }
        )

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }

        const reader = response.body?.getReader()
        /* v8 ignore next 3 */
        if (!reader) {
          throw new Error('No response body')
        }

        let chunkBytes = 0
        /* v8 ignore next 27 */
        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          chunkBytes += value.length
          totalBytes += value.length
          setBytesDownloaded(totalBytes)

          // Calculate current speed every 100ms
          const now = Date.now()
          if (now - lastUpdateTime >= 100) {
            const elapsed = (now - startTime) / 1000
            if (elapsed > 0) {
              const speedMbps = (totalBytes * 8) / (elapsed * 1_000_000)
              setCurrentSpeed(speedMbps)

              if (speedMbps > maxSpeed) {
                maxSpeed = speedMbps
                setPeakSpeed(speedMbps)
              }
            }
            lastUpdateTime = now
          }

          // Update progress
          const progressPercent = (totalBytes / targetBytes) * 100
          setProgress(Math.min(progressPercent, 100))
        }

        console.log(`[DownloadTest] Downloaded ${chunkBytes} bytes (${totalBytes} total)`)
      }

      const duration = (Date.now() - startTime) / 1000
      const avgSpeedMbps = (totalBytes * 8) / (duration * 1_000_000)

      // Apply 4% overhead compensation
      const compensatedAvgSpeed = avgSpeedMbps * 1.04
      const compensatedPeakSpeed = maxSpeed * 1.04

      const finalResult: DownloadResult = {
        fileSize: selectedSize,
        duration,
        averageSpeed: compensatedAvgSpeed,
        peakSpeed: compensatedPeakSpeed,
        timestamp: Date.now(),
      }

      setResult(finalResult)
      console.log('[DownloadTest] Test complete:', finalResult)
    } catch (error) {
      /* v8 ignore next 5 */
      if (error instanceof Error && error.name === 'AbortError') {
        console.log('[DownloadTest] Test cancelled by user')
      } else {
        console.error('[DownloadTest] Test failed:', error)
      }
    } finally {
      setIsRunning(false)
      setProgress(0)
      setCurrentSpeed(0)
      abortControllerRef.current = null
    }
  }

  const cancelTest = () => {
    console.log('[DownloadTest] Cancelling test...')
    abortControllerRef.current?.abort()
  }

  const formatSpeed = (mbps: number) => {
    if (mbps === 0) return '0'
    if (mbps < 1) return mbps.toFixed(2)
    if (mbps < 10) return mbps.toFixed(1)
    return mbps.toFixed(0)
  }

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const mb = bytes / (1024 * 1024)
    if (mb < 1) return `${(bytes / 1024).toFixed(1)} KB`
    if (mb < 1000) return `${mb.toFixed(1)} MB`
    return `${(mb / 1024).toFixed(2)} GB`
  }

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = Math.floor(seconds % 60)
    return `${minutes}m ${remainingSeconds}s`
  }

  return (
    <div className="downloadtest-container">
      <div className="downloadtest-header">
        <h2>Download Speed Test</h2>
        <p>Measure your download bandwidth by downloading a test file</p>
      </div>

      <div className="downloadtest-content">
        {!isRunning && !result && (
          <div className="downloadtest-idle">
            <div className="downloadtest-icon">
              <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10"
                />
              </svg>
            </div>

            <div className="size-selector">
              <label>Select file size:</label>
              <div className="size-options">
                {fileSizeOptions.map((option) => (
                  <button
                    key={option.value}
                    className={`size-option ${selectedSize === option.value ? 'active' : ''}`}
                    onClick={() => setSelectedSize(option.value)}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>

            <button onClick={runDownloadTest} className="btn-start-download">
              Start Download Test
            </button>

            <div className="download-info">
              <p>Test will download a {selectedSize}MB file to measure your connection speed</p>
            </div>
          </div>
        )}

        {isRunning && (
          <div className="downloadtest-running">
            <div className="download-icon-animated">
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10"
                  className="download-arrow"
                />
              </svg>
            </div>

            <div className="speed-display">
              <div className="speed-value">{formatSpeed(currentSpeed)}</div>
              <div className="speed-unit">Mbps</div>
              <div className="speed-label">Current Speed</div>
            </div>

            <div className="download-stats">
              <div className="stat-item">
                <span className="stat-label">Downloaded:</span>
                <span className="stat-value">{formatBytes(bytesDownloaded)}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Peak Speed:</span>
                <span className="stat-value">{formatSpeed(peakSpeed)} Mbps</span>
              </div>
            </div>

            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${progress}%` }}></div>
              <span className="progress-text">{progress.toFixed(0)}%</span>
            </div>

            <button onClick={cancelTest} className="btn-cancel-download">
              Cancel
            </button>
          </div>
        )}
      </div>

      <div className="downloadtest-footer">
        <p className="downloadtest-note">
          Download test measures your maximum download bandwidth from our server.
        </p>
      </div>

      {/* Results Modal */}
      {result && !isRunning && (
        <div className="modal-overlay" onClick={() => setResult(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Download Test Results</h2>
              <button className="modal-close" onClick={() => setResult(null)}>
                ×
              </button>
            </div>

            <div className="result-grid">
              <div className="result-card">
                <div className="result-icon average">⚡</div>
                <div className="result-value">{formatSpeed(result.averageSpeed)}</div>
                <div className="result-unit">Mbps</div>
                <div className="result-label">Average Speed</div>
              </div>

              <div className="result-card">
                <div className="result-icon peak">🚀</div>
                <div className="result-value">{formatSpeed(result.peakSpeed)}</div>
                <div className="result-unit">Mbps</div>
                <div className="result-label">Peak Speed</div>
              </div>

              <div className="result-card">
                <div className="result-icon size">📦</div>
                <div className="result-value">{result.fileSize}</div>
                <div className="result-unit">MB</div>
                <div className="result-label">File Size</div>
              </div>

              <div className="result-card">
                <div className="result-icon duration">⏱️</div>
                <div className="result-value">{formatDuration(result.duration)}</div>
                <div className="result-unit"></div>
                <div className="result-label">Duration</div>
              </div>
            </div>

            <div className="result-timestamp">
              Test completed at {new Date(result.timestamp).toLocaleTimeString()}
            </div>

            <div className="modal-actions">
              <button onClick={() => setResult(null)} className="btn-close-modal">
                Close
              </button>
              <button
                onClick={() => {
                  setResult(null)
                  runDownloadTest()
                }}
                className="btn-restart-download"
              >
                Run Again
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default DownloadTest
