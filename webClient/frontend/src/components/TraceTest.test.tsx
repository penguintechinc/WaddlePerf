import { render, screen, fireEvent, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import TraceTest from './TraceTest'

// Use vi.hoisted so these variables are available when vi.mock factory runs
const { mockStartTest, mockOnTestComplete, mockOnError } = vi.hoisted(() => {
  return {
    mockStartTest: vi.fn(),
    mockOnTestComplete: vi.fn(),
    mockOnError: vi.fn(),
  }
})

vi.mock('../services/websocket', () => ({
  websocketService: {
    onTestComplete: mockOnTestComplete,
    onError: mockOnError,
    startTest: mockStartTest,
    getConnectionStatus: vi.fn().mockReturnValue(true),
  },
}))

describe('TraceTest component', () => {
  beforeEach(() => {
    mockStartTest.mockClear()
    mockOnTestComplete.mockClear()
    mockOnError.mockClear()
    mockOnTestComplete.mockImplementation(() => {})
    mockOnError.mockImplementation(() => {})
  })

  it('renders the Trace Tests heading', () => {
    render(<TraceTest isAuthenticated={true} />)
    expect(screen.getByText('Trace Tests')).toBeInTheDocument()
  })

  it('renders the description', () => {
    render(<TraceTest isAuthenticated={true} />)
    expect(screen.getByText(/Trace network routes/)).toBeInTheDocument()
  })

  it('shows trace type buttons', () => {
    render(<TraceTest isAuthenticated={true} />)
    expect(screen.getByText('HTTP Trace')).toBeInTheDocument()
    expect(screen.getByText('TCP Trace')).toBeInTheDocument()
    expect(screen.getByText('Traceroute')).toBeInTheDocument()
  })

  it('shows Target Host input', () => {
    render(<TraceTest isAuthenticated={true} />)
    expect(screen.getByLabelText(/Target Host/i)).toBeInTheDocument()
  })

  it('shows Timeout input', () => {
    render(<TraceTest isAuthenticated={true} />)
    expect(screen.getByLabelText(/Timeout/i)).toBeInTheDocument()
  })

  it('shows Start Trace button', () => {
    render(<TraceTest isAuthenticated={true} />)
    expect(screen.getByText('Start Trace')).toBeInTheDocument()
  })

  it('Start Trace button is disabled when target is empty', () => {
    render(<TraceTest isAuthenticated={true} />)
    expect(screen.getByText('Start Trace')).toBeDisabled()
  })

  it('shows validation error if user is not authenticated and submits', async () => {
    const user = userEvent.setup()
    render(<TraceTest isAuthenticated={false} />)
    const targetInput = screen.getByLabelText(/Target Host/i)
    await user.type(targetInput, 'example.com')
    await user.click(screen.getByText('Start Trace'))
    expect(screen.getByText(/You must be logged in/i)).toBeInTheDocument()
  })

  it('shows validation error for invalid target', async () => {
    const user = userEvent.setup()
    render(<TraceTest isAuthenticated={true} />)
    const targetInput = screen.getByLabelText(/Target Host/i)
    await user.type(targetInput, 'invalid target!')
    await user.click(screen.getByText('Start Trace'))
    expect(screen.getByText(/Invalid hostname format/i)).toBeInTheDocument()
  })

  it('changes trace type to TCP when TCP Trace button is clicked', async () => {
    const user = userEvent.setup()
    render(<TraceTest isAuthenticated={true} />)
    await user.click(screen.getByText('TCP Trace'))
    const portInput = screen.getByLabelText(/^Port$/i)
    expect(portInput).toHaveValue(22)
  })

  it('hides port field for ICMP (Traceroute) type', async () => {
    const user = userEvent.setup()
    render(<TraceTest isAuthenticated={true} />)
    await user.click(screen.getByText('Traceroute'))
    expect(screen.queryByLabelText(/^Port$/i)).not.toBeInTheDocument()
  })

  it('shows placeholder text for HTTP trace target', () => {
    render(<TraceTest isAuthenticated={true} />)
    const targetInput = screen.getByLabelText(/Target Host/i)
    expect(targetInput).toHaveAttribute('placeholder', 'example.com or https://example.com')
  })

  it('calls websocketService.startTest on valid form submission', async () => {
    const user = userEvent.setup()
    render(<TraceTest isAuthenticated={true} />)
    const targetInput = screen.getByLabelText(/Target Host/i)
    await user.type(targetInput, 'example.com')
    await user.click(screen.getByText('Start Trace'))
    expect(mockStartTest).toHaveBeenCalled()
  })

  it('submits with http_trace test_type when HTTP Trace is selected', async () => {
    const user = userEvent.setup()
    render(<TraceTest isAuthenticated={true} />)
    const targetInput = screen.getByLabelText(/Target Host/i)
    await user.type(targetInput, 'example.com')
    await user.click(screen.getByText('Start Trace'))
    expect(mockStartTest).toHaveBeenCalledWith(
      expect.objectContaining({ test_type: 'http_trace' })
    )
  })

  it('changes placeholder based on trace type (ICMP)', async () => {
    const user = userEvent.setup()
    render(<TraceTest isAuthenticated={true} />)
    await user.click(screen.getByText('Traceroute'))
    const targetInput = screen.getByLabelText(/Target Host/i)
    expect(targetInput).toHaveAttribute('placeholder', '8.8.8.8 or example.com')
  })

  it('submits with tcp_trace test_type when TCP Trace is selected', async () => {
    const user = userEvent.setup()
    render(<TraceTest isAuthenticated={true} />)
    await user.click(screen.getByText('TCP Trace'))
    const targetInput = screen.getByLabelText(/Target Host/i)
    await user.type(targetInput, 'example.com')
    await user.click(screen.getByText('Start Trace'))
    expect(mockStartTest).toHaveBeenCalledWith(
      expect.objectContaining({ test_type: 'tcp_trace' })
    )
  })

  it('submits with traceroute test_type when Traceroute is selected', async () => {
    const user = userEvent.setup()
    render(<TraceTest isAuthenticated={true} />)
    await user.click(screen.getByText('Traceroute'))
    const targetInput = screen.getByLabelText(/Target Host/i)
    await user.type(targetInput, 'example.com')
    await user.click(screen.getByText('Start Trace'))
    expect(mockStartTest).toHaveBeenCalledWith(
      expect.objectContaining({ test_type: 'traceroute' })
    )
  })

  it('shows trace results when test completes successfully', async () => {
    const user = userEvent.setup()
    let capturedCallback: ((data: any) => void) | null = null

    mockOnTestComplete.mockImplementation((cb: (data: any) => void) => {
      capturedCallback = cb
    })

    render(<TraceTest isAuthenticated={true} />)
    const targetInput = screen.getByLabelText(/Target Host/i)
    await user.type(targetInput, 'example.com')
    await user.click(screen.getByText('Start Trace'))

    // Simulate websocket completing the test
    act(() => {
      if (capturedCallback) {
        capturedCallback({
          test_type: 'http_trace',
          target: 'example.com',
          success: true,
          latency_ms: 45.5,
          hops: ['192.168.1.1', '10.0.0.1', '8.8.8.8'],
        })
      }
    })

    expect(screen.getByText('Trace Results')).toBeInTheDocument()
    expect(screen.getByText('Success')).toBeInTheDocument()
  })

  it('shows hop information when hops are provided', async () => {
    const user = userEvent.setup()
    let capturedCallback: ((data: any) => void) | null = null

    mockOnTestComplete.mockImplementation((cb: (data: any) => void) => {
      capturedCallback = cb
    })

    render(<TraceTest isAuthenticated={true} />)
    const targetInput = screen.getByLabelText(/Target Host/i)
    await user.type(targetInput, 'example.com')
    await user.click(screen.getByText('Start Trace'))

    act(() => {
      if (capturedCallback) {
        capturedCallback({
          test_type: 'http_trace',
          target: 'example.com',
          success: true,
          hops: ['192.168.1.1', '10.0.0.1'],
        })
      }
    })

    expect(screen.getByText('Network Route')).toBeInTheDocument()
    expect(screen.getByText(/1\. 192\.168\.1\.1/)).toBeInTheDocument()
  })

  it('shows error when test fails via websocket', async () => {
    const user = userEvent.setup()
    let capturedCallback: ((data: any) => void) | null = null

    mockOnTestComplete.mockImplementation((cb: (data: any) => void) => {
      capturedCallback = cb
    })

    render(<TraceTest isAuthenticated={true} />)
    const targetInput = screen.getByLabelText(/Target Host/i)
    await user.type(targetInput, 'example.com')
    await user.click(screen.getByText('Start Trace'))

    act(() => {
      if (capturedCallback) {
        capturedCallback({
          test_type: 'http_trace',
          target: 'example.com',
          success: false,
          error: 'Host unreachable',
        })
      }
    })

    expect(screen.getByText('Failed')).toBeInTheDocument()
    expect(screen.getByText('Host unreachable')).toBeInTheDocument()
  })

  it('shows View Detailed Results button after test completes', async () => {
    const user = userEvent.setup()
    let capturedCallback: ((data: any) => void) | null = null

    mockOnTestComplete.mockImplementation((cb: (data: any) => void) => {
      capturedCallback = cb
    })

    render(<TraceTest isAuthenticated={true} />)
    const targetInput = screen.getByLabelText(/Target Host/i)
    await user.type(targetInput, 'example.com')
    await user.click(screen.getByText('Start Trace'))

    act(() => {
      if (capturedCallback) {
        capturedCallback({ test_type: 'http_trace', target: 'example.com', success: true })
      }
    })

    expect(screen.getByText('View Detailed Results')).toBeInTheDocument()
  })

  it('opens detailed results modal when View Detailed Results is clicked', async () => {
    const user = userEvent.setup()
    let capturedCallback: ((data: any) => void) | null = null

    mockOnTestComplete.mockImplementation((cb: (data: any) => void) => {
      capturedCallback = cb
    })

    render(<TraceTest isAuthenticated={true} />)
    const targetInput = screen.getByLabelText(/Target Host/i)
    await user.type(targetInput, 'example.com')
    await user.click(screen.getByText('Start Trace'))

    act(() => {
      if (capturedCallback) {
        capturedCallback({ test_type: 'http_trace', target: 'example.com', success: true })
      }
    })

    await user.click(screen.getByText('View Detailed Results'))
    expect(screen.getByText('Full Trace Report')).toBeInTheDocument()
  })

  it('closes detailed results modal when close button is clicked', async () => {
    const user = userEvent.setup()
    let capturedCallback: ((data: any) => void) | null = null

    mockOnTestComplete.mockImplementation((cb: (data: any) => void) => {
      capturedCallback = cb
    })

    render(<TraceTest isAuthenticated={true} />)
    const targetInput = screen.getByLabelText(/Target Host/i)
    await user.type(targetInput, 'example.com')
    await user.click(screen.getByText('Start Trace'))

    act(() => {
      if (capturedCallback) {
        capturedCallback({ test_type: 'http_trace', target: 'example.com', success: true })
      }
    })

    await user.click(screen.getByText('View Detailed Results'))
    expect(screen.getByText('Full Trace Report')).toBeInTheDocument()

    // Click the × close button
    await user.click(screen.getByText('×'))
    expect(screen.queryByText('Full Trace Report')).not.toBeInTheDocument()
  })

  it('shows latency when provided in results', async () => {
    const user = userEvent.setup()
    let capturedCallback: ((data: any) => void) | null = null

    mockOnTestComplete.mockImplementation((cb: (data: any) => void) => {
      capturedCallback = cb
    })

    render(<TraceTest isAuthenticated={true} />)
    const targetInput = screen.getByLabelText(/Target Host/i)
    await user.type(targetInput, 'example.com')
    await user.click(screen.getByText('Start Trace'))

    act(() => {
      if (capturedCallback) {
        capturedCallback({
          test_type: 'http_trace',
          target: 'example.com',
          success: true,
          latency_ms: 45.567,
        })
      }
    })

    expect(screen.getByText('45.57 ms')).toBeInTheDocument()
  })
})
