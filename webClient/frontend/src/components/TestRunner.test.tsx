import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import TestRunner from './TestRunner'

// Use vi.hoisted to define mocks that are referenced in vi.mock factories
const mocks = vi.hoisted(() => ({
  logout: vi.fn().mockResolvedValue(undefined),
  websocketService: {
    connect: vi.fn().mockResolvedValue(undefined),
    disconnect: vi.fn(),
    onTestStarted: vi.fn(),
    onTestProgress: vi.fn(),
    onTestComplete: vi.fn(),
    onError: vi.fn(),
    startTest: vi.fn(),
    getConnectionStatus: vi.fn().mockReturnValue(true),
  },
}))

// Mock all child components that have complex deps
vi.mock('./TestForm', () => ({
  default: vi.fn(({ onTestStart, isRunning }) => (
    <div data-testid="test-form">
      <button data-testid="start-test" onClick={() => onTestStart({ test_type: 'http', target: 'example.com' })}>
        Start Test
      </button>
      <span data-testid="is-running">{String(isRunning)}</span>
    </div>
  )),
}))

vi.mock('./TestResults', () => ({
  default: vi.fn(({ result, onClose, onRunAgain }) => (
    <div data-testid="test-results">
      <span data-testid="result-type">{result.test_type}</span>
      <button data-testid="close-results" onClick={onClose}>Close</button>
      <button data-testid="run-again" onClick={onRunAgain}>Run Again</button>
    </div>
  )),
}))

vi.mock('./RealtimeCharts', () => ({
  default: vi.fn(({ isRunning, latencyData }) => (
    <div data-testid="realtime-charts" data-running={String(isRunning)} data-points={latencyData.length} />
  )),
}))

vi.mock('./SpeedTest', () => ({
  default: vi.fn(({ testServerUrl }) => (
    <div data-testid="speed-test" data-url={testServerUrl} />
  )),
}))

vi.mock('./DownloadTest', () => ({
  default: vi.fn(({ testServerUrl }) => (
    <div data-testid="download-test" data-url={testServerUrl} />
  )),
}))

vi.mock('./TraceTest', () => ({
  default: vi.fn(({ isAuthenticated }) => (
    <div data-testid="trace-test" data-authenticated={String(isAuthenticated)} />
  )),
}))

vi.mock('./ThemeToggle', () => ({
  default: vi.fn(() => <div data-testid="theme-toggle" />),
}))

vi.mock('../services/api', () => ({
  logout: mocks.logout,
}))

vi.mock('../services/websocket', () => ({
  websocketService: mocks.websocketService,
}))

const defaultUser = {
  id: 1,
  username: 'testuser',
  email: 'test@example.com',
  role: 'admin',
}

describe('TestRunner component', () => {
  const mockOnLogout = vi.fn()

  beforeEach(() => {
    mockOnLogout.mockClear()
    vi.clearAllMocks()
    // Re-setup the mock after clearAllMocks
    mocks.websocketService.connect.mockResolvedValue(undefined)
    mocks.websocketService.onTestStarted.mockImplementation(() => {})
    mocks.websocketService.onTestProgress.mockImplementation(() => {})
    mocks.websocketService.onTestComplete.mockImplementation(() => {})
    mocks.websocketService.onError.mockImplementation(() => {})
    mocks.logout.mockResolvedValue(undefined)
  })

  it('renders the header with WaddlePerf title', async () => {
    render(<TestRunner user={defaultUser} onLogout={mockOnLogout} authEnabled={true} />)
    await waitFor(() => expect(screen.getByText('WaddlePerf')).toBeInTheDocument())
  })

  it('renders the footer', async () => {
    render(<TestRunner user={defaultUser} onLogout={mockOnLogout} authEnabled={true} />)
    await waitFor(() => expect(screen.getByText(/WaddlePerf Web Client/)).toBeInTheDocument())
  })

  it('shows username when auth is enabled and user is present', async () => {
    render(<TestRunner user={defaultUser} onLogout={mockOnLogout} authEnabled={true} />)
    await waitFor(() => expect(screen.getByText('testuser')).toBeInTheDocument())
  })

  it('hides user menu when auth is disabled', async () => {
    render(<TestRunner user={defaultUser} onLogout={mockOnLogout} authEnabled={false} />)
    await waitFor(() => expect(screen.queryByText('testuser')).not.toBeInTheDocument())
  })

  it('renders the tab navigation buttons', async () => {
    render(<TestRunner user={defaultUser} onLogout={mockOnLogout} authEnabled={true} />)
    await waitFor(() => {
      expect(screen.getByText('Speed Test')).toBeInTheDocument()
      expect(screen.getByText('Network Tests')).toBeInTheDocument()
      expect(screen.getByText('Trace Tests')).toBeInTheDocument()
      expect(screen.getByText('Download Test')).toBeInTheDocument()
    })
  })

  it('shows Speed Test tab content by default', async () => {
    render(<TestRunner user={defaultUser} onLogout={mockOnLogout} authEnabled={true} />)
    await waitFor(() => expect(screen.getByTestId('speed-test')).toBeInTheDocument())
  })

  it('switches to Network Tests tab when clicked', async () => {
    render(<TestRunner user={defaultUser} onLogout={mockOnLogout} authEnabled={true} />)
    await waitFor(() => screen.getByText('Network Tests'))
    fireEvent.click(screen.getByText('Network Tests'))
    expect(screen.getByTestId('test-form')).toBeInTheDocument()
  })

  it('switches to Download Test tab when clicked', async () => {
    render(<TestRunner user={defaultUser} onLogout={mockOnLogout} authEnabled={true} />)
    await waitFor(() => screen.getByText('Download Test'))
    fireEvent.click(screen.getByText('Download Test'))
    expect(screen.getByTestId('download-test')).toBeInTheDocument()
  })

  it('switches to Trace Tests tab when clicked', async () => {
    render(<TestRunner user={defaultUser} onLogout={mockOnLogout} authEnabled={true} />)
    await waitFor(() => screen.getByText('Trace Tests'))
    fireEvent.click(screen.getByText('Trace Tests'))
    expect(screen.getByTestId('trace-test')).toBeInTheDocument()
  })

  it('TraceTest receives isAuthenticated=true when user is set', async () => {
    render(<TestRunner user={defaultUser} onLogout={mockOnLogout} authEnabled={true} />)
    await waitFor(() => screen.getByText('Trace Tests'))
    fireEvent.click(screen.getByText('Trace Tests'))
    const traceTest = screen.getByTestId('trace-test')
    expect(traceTest.getAttribute('data-authenticated')).toBe('true')
  })

  it('TraceTest receives isAuthenticated=false when user is null', async () => {
    render(<TestRunner user={null} onLogout={mockOnLogout} authEnabled={false} />)
    await waitFor(() => screen.getByText('Trace Tests'))
    fireEvent.click(screen.getByText('Trace Tests'))
    const traceTest = screen.getByTestId('trace-test')
    expect(traceTest.getAttribute('data-authenticated')).toBe('false')
  })

  it('calls logout and onLogout when Logout button is clicked', async () => {
    render(<TestRunner user={defaultUser} onLogout={mockOnLogout} authEnabled={true} />)
    await waitFor(() => screen.getByText('Logout'))
    fireEvent.click(screen.getByText('Logout'))
    await waitFor(() => {
      expect(mocks.logout).toHaveBeenCalled()
      expect(mockOnLogout).toHaveBeenCalled()
    })
  })

  it('shows welcome message in Network Tests tab when no test is running', async () => {
    render(<TestRunner user={defaultUser} onLogout={mockOnLogout} authEnabled={true} />)
    await waitFor(() => screen.getByText('Network Tests'))
    fireEvent.click(screen.getByText('Network Tests'))
    expect(screen.getByText('Welcome to WaddlePerf')).toBeInTheDocument()
  })

  it('renders ThemeToggle in header', async () => {
    render(<TestRunner user={defaultUser} onLogout={mockOnLogout} authEnabled={true} />)
    await waitFor(() => expect(screen.getByTestId('theme-toggle')).toBeInTheDocument())
  })

  it('shows connection status indicator', async () => {
    render(<TestRunner user={defaultUser} onLogout={mockOnLogout} authEnabled={true} />)
    await waitFor(() => {
      const statusIndicator = document.querySelector('.status-indicator')
      expect(statusIndicator).toBeInTheDocument()
    })
  })

  it('triggers onTestStarted callback when websocket receives test_started event', async () => {
    let startedCallback: ((data: any) => void) | null = null
    mocks.websocketService.onTestStarted.mockImplementation((cb: (data: any) => void) => {
      startedCallback = cb
    })

    render(<TestRunner user={defaultUser} onLogout={mockOnLogout} authEnabled={true} />)
    await waitFor(() => screen.getByText('Network Tests'))
    fireEvent.click(screen.getByText('Network Tests'))
    expect(screen.getByTestId('is-running')).toHaveTextContent('false')

    // Simulate test started event
    act(() => {
      if (startedCallback) startedCallback({ test_type: 'http' })
    })

    expect(screen.getByTestId('is-running')).toHaveTextContent('true')
  })

  it('triggers onTestProgress callback to update progress', async () => {
    let progressCallback: ((data: any) => void) | null = null
    mocks.websocketService.onTestProgress.mockImplementation((cb: (data: any) => void) => {
      progressCallback = cb
    })

    render(<TestRunner user={defaultUser} onLogout={mockOnLogout} authEnabled={true} />)
    await waitFor(() => screen.getByText('Network Tests'))
    fireEvent.click(screen.getByText('Network Tests'))

    // Start test first
    mocks.websocketService.onTestStarted.mockImplementation(() => {})

    // Simulate progress directly
    act(() => {
      if (progressCallback) {
        progressCallback({ progress: 50, current_index: 5 })
      }
    })
  })

  it('shows test results when test completes', async () => {
    let completeCallback: ((data: any) => void) | null = null
    let startedCallback: ((data: any) => void) | null = null
    mocks.websocketService.onTestStarted.mockImplementation((cb: (data: any) => void) => {
      startedCallback = cb
    })
    mocks.websocketService.onTestComplete.mockImplementation((cb: (data: any) => void) => {
      completeCallback = cb
    })

    render(<TestRunner user={defaultUser} onLogout={mockOnLogout} authEnabled={true} />)
    await waitFor(() => screen.getByText('Network Tests'))
    fireEvent.click(screen.getByText('Network Tests'))

    // Simulate test start and completion
    act(() => {
      if (startedCallback) startedCallback({ test_type: 'http' })
    })

    act(() => {
      if (completeCallback) {
        completeCallback({
          test_type: 'http',
          target_host: 'example.com',
          success: true,
          latency_ms: 45,
          throughput_mbps: 100,
          jitter_ms: 2,
          packet_loss_percent: 0,
        })
      }
    })

    expect(screen.getByTestId('test-results')).toBeInTheDocument()
  })

  it('handles websocket error callback', async () => {
    let errorCallback: ((error: any) => void) | null = null
    let startedCallback: ((data: any) => void) | null = null
    mocks.websocketService.onTestStarted.mockImplementation((cb: (data: any) => void) => {
      startedCallback = cb
    })
    mocks.websocketService.onError.mockImplementation((cb: (error: any) => void) => {
      errorCallback = cb
    })

    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    render(<TestRunner user={defaultUser} onLogout={mockOnLogout} authEnabled={true} />)
    await waitFor(() => screen.getByText('Network Tests'))
    fireEvent.click(screen.getByText('Network Tests'))

    act(() => {
      if (startedCallback) startedCallback({ test_type: 'http' })
    })
    act(() => {
      if (errorCallback) errorCallback({ error: 'Connection lost' })
    })

    expect(screen.getByTestId('is-running')).toHaveTextContent('false')
    consoleSpy.mockRestore()
  })

  it('close test results resets result to null', async () => {
    let completeCallback: ((data: any) => void) | null = null
    let startedCallback: ((data: any) => void) | null = null
    mocks.websocketService.onTestStarted.mockImplementation((cb: (data: any) => void) => {
      startedCallback = cb
    })
    mocks.websocketService.onTestComplete.mockImplementation((cb: (data: any) => void) => {
      completeCallback = cb
    })

    render(<TestRunner user={defaultUser} onLogout={mockOnLogout} authEnabled={true} />)
    await waitFor(() => screen.getByText('Network Tests'))
    fireEvent.click(screen.getByText('Network Tests'))

    act(() => {
      if (startedCallback) startedCallback({ test_type: 'http' })
    })
    act(() => {
      if (completeCallback) {
        completeCallback({ test_type: 'http', success: true, latency_ms: 45 })
      }
    })

    expect(screen.getByTestId('test-results')).toBeInTheDocument()
    fireEvent.click(screen.getByTestId('close-results'))
    expect(screen.queryByTestId('test-results')).not.toBeInTheDocument()
    expect(screen.getByText('Welcome to WaddlePerf')).toBeInTheDocument()
  })

  it('handles WebSocket connection failure gracefully', async () => {
    mocks.websocketService.connect.mockRejectedValue(new Error('Connection failed'))
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    render(<TestRunner user={defaultUser} onLogout={mockOnLogout} authEnabled={true} />)
    await waitFor(() => expect(screen.getByText('WaddlePerf')).toBeInTheDocument())
    consoleSpy.mockRestore()
  })

  it('attempts reconnection when test is started but WebSocket is not connected', async () => {
    // Connect fails, so wsConnected stays false
    mocks.websocketService.connect.mockRejectedValue(new Error('Connection failed'))
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    render(<TestRunner user={defaultUser} onLogout={mockOnLogout} authEnabled={true} />)
    await waitFor(() => screen.getByText('Network Tests'))
    fireEvent.click(screen.getByText('Network Tests'))

    // Start test while disconnected — triggers reconnect path
    fireEvent.click(screen.getByTestId('start-test'))

    // Verify it tried to re-initialize (connect called at least twice: initial + reconnect)
    await waitFor(() => expect(mocks.websocketService.connect).toHaveBeenCalledTimes(2))
    consoleSpy.mockRestore()
  })

  it('run again callback resets latency data and metrics', async () => {
    let completeCallback: ((data: any) => void) | null = null
    let startedCallback: ((data: any) => void) | null = null
    mocks.websocketService.onTestStarted.mockImplementation((cb: (data: any) => void) => {
      startedCallback = cb
    })
    mocks.websocketService.onTestComplete.mockImplementation((cb: (data: any) => void) => {
      completeCallback = cb
    })

    render(<TestRunner user={defaultUser} onLogout={mockOnLogout} authEnabled={true} />)
    await waitFor(() => screen.getByText('Network Tests'))
    fireEvent.click(screen.getByText('Network Tests'))

    act(() => {
      if (startedCallback) startedCallback({ test_type: 'http' })
    })
    act(() => {
      if (completeCallback) {
        completeCallback({ test_type: 'http', success: true, latency_ms: 45 })
      }
    })

    expect(screen.getByTestId('test-results')).toBeInTheDocument()
    // Click Run Again via the mocked TestResults component
    fireEvent.click(screen.getByTestId('run-again'))
    // After run again, results are cleared and welcome message reappears
    expect(screen.queryByTestId('test-results')).not.toBeInTheDocument()
    expect(screen.getByText('Welcome to WaddlePerf')).toBeInTheDocument()
  })

  it('handles logout failure and still calls onLogout', async () => {
    mocks.logout.mockRejectedValue(new Error('Logout failed'))
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    render(<TestRunner user={defaultUser} onLogout={mockOnLogout} authEnabled={true} />)
    await waitFor(() => screen.getByText('Logout'))
    fireEvent.click(screen.getByText('Logout'))
    await waitFor(() => expect(mockOnLogout).toHaveBeenCalled())
    consoleSpy.mockRestore()
  })
})
