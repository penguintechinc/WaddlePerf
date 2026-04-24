import { useState, useRef, useEffect } from 'react'
import './SpeedTest.css'

interface SpeedTestProps {
  testServerUrl: string
}

interface LatencyResult {
  ping: number
  jitter: number
  samples: number[]
}

interface SpeedTestResult {
  download: number
  upload: number
  latency: LatencyResult
  timestamp: number
}

function SpeedTest({ testServerUrl }: SpeedTestProps) {
  const [isRunning, setIsRunning] = useState(false)
  const [currentPhase, setCurrentPhase] = useState<'idle' | 'latency' | 'download' | 'upload'>('idle')
  const [progress, setProgress] = useState(0)
  const [currentSpeed, setCurrentSpeed] = useState(0)
  const [latency, setLatency] = useState(0)
  const [result, setResult] = useState<SpeedTestResult | null>(null)
  const [serverInfo, setServerInfo] = useState<any>(null)
  const [numStreams, setNumStreams] = useState(6)
  const abortControllerRef = useRef<AbortController | null>(null)

  useEffect(() => {
    fetchServerInfo()
  }, [testServerUrl])

  const fetchServerInfo = async () => {
    try {
      const response = await fetch(`${testServerUrl}/speedtest/info`)
      const data = await response.json()
      setServerInfo(data)
      console.log('[SpeedTest] Server info:', data)
    } catch (error) {
      console.error('[SpeedTest] Failed to fetch server info:', error)
    }
  }

  const measureLatency = async (): Promise<LatencyResult> => {
    console.log('[SpeedTest] Measuring latency...')
    setCurrentPhase('latency')
    setProgress(0)

    const samples: number[] = []
    const numSamples = 20

    for (let i = 0; i < numSamples; i++) {
      if (abortControllerRef.current?.signal.aborted) {
        throw new Error('Test cancelled')
      }

      const start = performance.now()
      try {
        await fetch(`${testServerUrl}/speedtest/ping?t=${Date.now()}`, {
          method: 'GET',
          cache: 'no-cache',
          signal: abortControllerRef.current?.signal,
        })
        const latency = performance.now() - start
        samples.push(latency)
        setLatency(latency)
        setProgress(((i + 1) / numSamples) * 100)
      } catch (error) {
        if (error instanceof Error && error.name === 'AbortError') {
          throw error
        }
        console.warn('[SpeedTest] Latency ping failed:', error)
      }

      // Small delay between pings
      await new Promise((resolve) => setTimeout(resolve, 100))
    }

    // Calculate average and jitter
    const avgLatency = samples.reduce((a, b) => a + b, 0) / samples.length
    const jitterValue =
      samples.reduce((sum, sample) => sum + Math.abs(sample - avgLatency), 0) / samples.length

    return {
      ping: avgLatency,
      jitter: jitterValue,
      samples,
    }
  }

  const measureDownload = async (): Promise<number> => {
    console.log('[SpeedTest] Measuring download speed...')
    setCurrentPhase('download')
    setProgress(0)
    setCurrentSpeed(0)

    const chunkSizeMB = 10
    const testDuration = 10000 // 10 seconds

    const startTime = Date.now()
    let totalBytes = 0
    const speedSamples: number[] = []

    // Create multiple parallel streams
    const streams = Array.from({ length: numStreams }, async (_, streamIndex) => {
      let streamBytes = 0

      while (Date.now() - startTime < testDuration) {
        if (abortControllerRef.current?.signal.aborted) {
          throw new Error('Test cancelled')
        }

        try {
          const response = await fetch(
            `${testServerUrl}/speedtest/download?size=${chunkSizeMB}&t=${Date.now()}`,
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

          /* v8 ignore next 13 */
          while (true) {
            const { done, value } = await reader.read()
            if (done) break

            streamBytes += value.length
            totalBytes += value.length

            // Calculate current speed
            const elapsed = (Date.now() - startTime) / 1000
            if (elapsed > 0) {
              const speedMbps = (totalBytes * 8) / (elapsed * 1_000_000)
              setCurrentSpeed(speedMbps)
              speedSamples.push(speedMbps)
            }
          }
        } catch (error) {
          /* v8 ignore next 3 */
          if (error instanceof Error && error.name === 'AbortError') {
            throw error
          }
          console.warn(`[SpeedTest] Download stream ${streamIndex} error:`, error)
          break
        }
      }

      return streamBytes
    })

    try {
      await Promise.all(streams)
    } catch (error) {
      /* v8 ignore next 3 */
      if (error instanceof Error && error.name === 'AbortError') {
        throw error
      }
    }

    const elapsed = (Date.now() - startTime) / 1000
    const avgSpeedMbps = (totalBytes * 8) / (elapsed * 1_000_000)

    // Apply 4% overhead compensation like OpenSpeedTest
    const compensatedSpeed = avgSpeedMbps * 1.04

    console.log(
      `[SpeedTest] Download complete: ${compensatedSpeed.toFixed(2)} Mbps (${totalBytes} bytes in ${elapsed.toFixed(2)}s)`
    )

    setProgress(100)

    return compensatedSpeed
  }

  const measureUpload = async (): Promise<number> => {
    console.log('[SpeedTest] Measuring upload speed...')
    setCurrentPhase('upload')
    setProgress(0)
    setCurrentSpeed(0)

    const chunkSizeMB = 10
    const testDuration = 10000 // 10 seconds

    // Generate random data to upload
    // Note: crypto.getRandomValues() has a 65KB limit, so we fill in chunks
    const chunkSize = chunkSizeMB * 1024 * 1024
    const uploadData = new Uint8Array(chunkSize)
    const maxChunkSize = 65536 // 64KB max for getRandomValues

    for (let i = 0; i < chunkSize; i += maxChunkSize) {
      const chunkEnd = Math.min(i + maxChunkSize, chunkSize)
      crypto.getRandomValues(uploadData.subarray(i, chunkEnd))
    }

    const startTime = Date.now()
    let totalBytes = 0

    // Create multiple parallel streams
    const streams = Array.from({ length: numStreams }, async (_, streamIndex) => {
      let streamBytes = 0

      while (Date.now() - startTime < testDuration) {
        if (abortControllerRef.current?.signal.aborted) {
          throw new Error('Test cancelled')
        }

        try {
          const response = await fetch(`${testServerUrl}/speedtest/upload?t=${Date.now()}`, {
            method: 'POST',
            body: uploadData,
            headers: {
              'Content-Type': 'application/octet-stream',
            },
            cache: 'no-cache',
            signal: abortControllerRef.current?.signal,
          })

          if (!response.ok) {
            throw new Error(`HTTP ${response.status}`)
          }

          streamBytes += chunkSize
          totalBytes += chunkSize

          // Calculate current speed
          const elapsed = (Date.now() - startTime) / 1000
          if (elapsed > 0) {
            const speedMbps = (totalBytes * 8) / (elapsed * 1_000_000)
            setCurrentSpeed(speedMbps)
          }
        } catch (error) {
          /* v8 ignore next 3 */
          if (error instanceof Error && error.name === 'AbortError') {
            throw error
          }
          console.warn(`[SpeedTest] Upload stream ${streamIndex} error:`, error)
          break
        }
      }

      return streamBytes
    })

    try {
      await Promise.all(streams)
    } catch (error) {
      /* v8 ignore next 3 */
      if (error instanceof Error && error.name === 'AbortError') {
        throw error
      }
    }

    const elapsed = (Date.now() - startTime) / 1000
    const avgSpeedMbps = (totalBytes * 8) / (elapsed * 1_000_000)

    // Apply 4% overhead compensation like OpenSpeedTest
    const compensatedSpeed = avgSpeedMbps * 1.04

    console.log(
      `[SpeedTest] Upload complete: ${compensatedSpeed.toFixed(2)} Mbps (${totalBytes} bytes in ${elapsed.toFixed(2)}s)`
    )

    setProgress(100)

    return compensatedSpeed
  }

  const runSpeedTest = async () => {
    console.log('[SpeedTest] Starting speed test...')
    setIsRunning(true)
    setResult(null)
    setLatency(0)

    abortControllerRef.current = new AbortController()

    try {
      // Phase 1: Measure latency
      const latencyResult = await measureLatency()

      // Phase 2: Measure download speed
      const download = await measureDownload()

      // Phase 3: Measure upload speed
      const upload = await measureUpload()

      // Store final result
      const finalResult: SpeedTestResult = {
        download,
        upload,
        latency: latencyResult,
        timestamp: Date.now(),
      }

      setResult(finalResult)
      console.log('[SpeedTest] Test complete:', finalResult)
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        console.log('[SpeedTest] Test cancelled by user')
      } else {
        console.error('[SpeedTest] Test failed:', error)
      }
    } finally {
      setIsRunning(false)
      setCurrentPhase('idle')
      setProgress(0)
      setCurrentSpeed(0)
      abortControllerRef.current = null
    }
  }

  const cancelTest = () => {
    console.log('[SpeedTest] Cancelling test...')
    abortControllerRef.current?.abort()
  }

  const formatSpeed = (mbps: number) => {
    if (mbps === 0) return '0'
    if (mbps < 1) return mbps.toFixed(2)
    if (mbps < 10) return mbps.toFixed(1)
    return mbps.toFixed(0)
  }

  return (
    <div className="speedtest-container">
      <div className="speedtest-header">
        <h2>Speed Test</h2>
        <p>Measure your bandwidth directly from your browser</p>
      </div>

      <div className="speedtest-content">
        {!isRunning && !result && (
          <div className="speedtest-idle">
            <div className="speedtest-icon">
              <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
            </div>

            <div className="streams-control">
              <label htmlFor="streams-slider">
                Number of Streams: <strong>{numStreams}</strong>
              </label>
              <input
                id="streams-slider"
                type="range"
                min="1"
                max="20"
                value={numStreams}
                onChange={(e) => setNumStreams(parseInt(e.target.value, 10))}
                className="streams-slider"
              />
              <div className="streams-range-labels">
                <span>1</span>
                <span>20</span>
              </div>
            </div>

            <button onClick={runSpeedTest} className="btn-start-speedtest">
              Start Speed Test
            </button>
            {serverInfo && (
              <div className="server-info">
                <p>Server: {serverInfo.name}</p>
              </div>
            )}
          </div>
        )}

        {isRunning && (
          <div className="speedtest-running">
            <div className="phase-indicator">
              <div className={`phase-item ${currentPhase === 'latency' ? 'active' : currentPhase !== 'idle' ? 'completed' : ''}`}>
                <div className="phase-dot"></div>
                <span>Latency</span>
              </div>
              <div className={`phase-item ${currentPhase === 'download' ? 'active' : (currentPhase === 'upload' || result) ? 'completed' : ''}`}>
                <div className="phase-dot"></div>
                <span>Download</span>
              </div>
              <div className={`phase-item ${currentPhase === 'upload' ? 'active' : result ? 'completed' : ''}`}>
                <div className="phase-dot"></div>
                <span>Upload</span>
              </div>
            </div>

            <div className="speed-display">
              {currentPhase === 'latency' && (
                <>
                  <div className="speed-value">{latency.toFixed(0)}</div>
                  <div className="speed-unit">ms</div>
                  <div className="speed-label">Latency</div>
                </>
              )}
              {(currentPhase === 'download' || currentPhase === 'upload') && (
                <>
                  <div className="speed-value">{formatSpeed(currentSpeed)}</div>
                  <div className="speed-unit">Mbps</div>
                  <div className="speed-label">
                    {currentPhase === 'download' ? 'Download' : 'Upload'} Speed
                  </div>
                </>
              )}
            </div>

            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${progress}%` }}></div>
            </div>

            <button onClick={cancelTest} className="btn-cancel-speedtest">
              Cancel
            </button>
          </div>
        )}

        {!isRunning && !result && (
          <div className="speedtest-idle">
            <button onClick={runSpeedTest} className="btn-restart-speedtest">
              Run Another Test
            </button>
          </div>
        )}
      </div>

      <div className="speedtest-footer">
        <p className="speedtest-note">
          Tests run directly from your browser to measure your actual bandwidth to our server.
        </p>
      </div>

      {/* Results Modal */}
      {result && !isRunning && (
        <div className="modal-overlay" onClick={() => setResult(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Speed Test Results</h2>
              <button className="modal-close" onClick={() => setResult(null)}>
                ×
              </button>
            </div>

            <div className="result-grid">
              <div className="result-card">
                <div className="result-icon download">↓</div>
                <div className="result-value">{formatSpeed(result.download)}</div>
                <div className="result-unit">Mbps</div>
                <div className="result-label">Download</div>
              </div>

              <div className="result-card">
                <div className="result-icon upload">↑</div>
                <div className="result-value">{formatSpeed(result.upload)}</div>
                <div className="result-unit">Mbps</div>
                <div className="result-label">Upload</div>
              </div>

              <div className="result-card">
                <div className="result-icon latency">⚡</div>
                <div className="result-value">{result.latency.ping.toFixed(0)}</div>
                <div className="result-unit">ms</div>
                <div className="result-label">Latency</div>
              </div>

              <div className="result-card">
                <div className="result-icon jitter">~</div>
                <div className="result-value">{result.latency.jitter.toFixed(1)}</div>
                <div className="result-unit">ms</div>
                <div className="result-label">Jitter</div>
              </div>
            </div>

            <div className="result-timestamp">
              Test completed at {new Date(result.timestamp).toLocaleTimeString()}
            </div>

            <div className="modal-actions">
              <button onClick={() => setResult(null)} className="btn-close-modal">
                Close
              </button>
              <button onClick={() => { setResult(null); runSpeedTest(); }} className="btn-restart-speedtest">
                Run Again
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default SpeedTest
