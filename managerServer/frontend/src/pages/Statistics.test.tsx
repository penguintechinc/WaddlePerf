import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import Statistics from './Statistics'
import { api } from '../services/api'

vi.mock('../services/api', () => ({
  api: {
    getRecentTests: vi.fn(),
  },
}))

vi.mock('recharts', () => ({
  LineChart: vi.fn(({ children }) => <div data-testid="line-chart">{children}</div>),
  BarChart: vi.fn(({ children }) => <div data-testid="bar-chart">{children}</div>),
  Line: vi.fn(() => null),
  Bar: vi.fn(() => null),
  XAxis: vi.fn(() => null),
  YAxis: vi.fn(() => null),
  CartesianGrid: vi.fn(() => null),
  Tooltip: vi.fn(() => null),
  Legend: vi.fn(() => null),
  ResponsiveContainer: vi.fn(({ children }) => <div data-testid="responsive-container">{children}</div>),
}))

const mockTests = [
  { id: 1, device_serial: 'DEV-001', test_type: 'http', result_data: {}, created_at: new Date().toISOString(), latency: 20, bandwidth: 100, success: true },
  { id: 2, device_serial: 'DEV-002', test_type: 'tcp', result_data: {}, created_at: new Date().toISOString(), latency: 50, bandwidth: null, success: true },
  { id: 3, device_serial: 'DEV-001', test_type: 'http', result_data: {}, created_at: new Date().toISOString(), latency: null, bandwidth: null, success: false },
]

describe('Statistics page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading spinner initially', () => {    api.getRecentTests.mockImplementation(() => new Promise(() => {}))
    render(<Statistics />)
    expect(document.querySelector('.spinner')).toBeInTheDocument()
  })

  it('renders the Test Statistics heading', async () => {    api.getRecentTests.mockResolvedValue({ results: [] })
    render(<Statistics />)
    await waitFor(() => expect(screen.getByText('Test Statistics')).toBeInTheDocument())
  })

  it('shows filter controls', async () => {    api.getRecentTests.mockResolvedValue({ results: [] })
    render(<Statistics />)
    await waitFor(() => {
      expect(screen.getByLabelText(/Device Filter/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Test Type/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Results Limit/i)).toBeInTheDocument()
    })
  })

  it('shows Refresh button', async () => {    api.getRecentTests.mockResolvedValue({ results: [] })
    render(<Statistics />)
    await waitFor(() => expect(screen.getByText('Refresh')).toBeInTheDocument())
  })

  it('shows summary cards after loading', async () => {    api.getRecentTests.mockResolvedValue({ results: mockTests })
    render(<Statistics />)
    await waitFor(() => {
      expect(screen.getByText('Total Tests')).toBeInTheDocument()
      expect(screen.getByText('Success Rate')).toBeInTheDocument()
      expect(screen.getByText('Avg Latency')).toBeInTheDocument()
      expect(screen.getByText('Unique Devices')).toBeInTheDocument()
    })
  })

  it('shows correct total tests count', async () => {    api.getRecentTests.mockResolvedValue({ results: mockTests })
    render(<Statistics />)
    await waitFor(() => {
      const totalTestsCard = screen.getByText('Total Tests')
      // The count should appear in the same card or right after the label
      expect(totalTestsCard.closest('.stats-card') || totalTestsCard.parentElement).toHaveTextContent('3')
    })
  })

  it('filters tests by device serial', async () => {    api.getRecentTests.mockResolvedValue({ results: mockTests })
    render(<Statistics />)
    await waitFor(() => screen.getByLabelText(/Device Filter/i))
    const deviceFilter = screen.getByLabelText(/Device Filter/i)
    fireEvent.change(deviceFilter, { target: { value: 'DEV-001' } })
    // DEV-001 appears twice, DEV-002 once. After filtering to DEV-001, should show 2.
    await waitFor(() => {
      const totalTestsCard = screen.getByText('Total Tests')
      expect(totalTestsCard.closest('.stats-card') || totalTestsCard.parentElement).toHaveTextContent('2')
    })
  })

  it('filters tests by test type', async () => {    api.getRecentTests.mockResolvedValue({ results: mockTests })
    render(<Statistics />)
    await waitFor(() => screen.getByLabelText(/Test Type/i))
    const typeFilter = screen.getByLabelText(/Test Type/i)
    fireEvent.change(typeFilter, { target: { value: 'tcp' } })
    await waitFor(() => {
      // DEV-002 with tcp appears
      expect(screen.getByText('DEV-002')).toBeInTheDocument()
    })
  })

  it('calls refresh when Refresh button is clicked', async () => {    api.getRecentTests.mockResolvedValue({ results: mockTests })
    render(<Statistics />)
    await waitFor(() => screen.getByText('Refresh'))
    fireEvent.click(screen.getByText('Refresh'))
    await waitFor(() => expect(api.getRecentTests).toHaveBeenCalledTimes(2))
  })

  it('shows error message when API fails', async () => {    api.getRecentTests.mockRejectedValue({ response: { data: { error: 'Load failed' } } })
    render(<Statistics />)
    await waitFor(() => expect(screen.getByText('Load failed')).toBeInTheDocument())
  })

  it('shows "No latency data available" when no tests have latency', async () => {    api.getRecentTests.mockResolvedValue({ results: [{ ...mockTests[2], latency: null }] })
    render(<Statistics />)
    await waitFor(() => expect(screen.getByText('No latency data available')).toBeInTheDocument())
  })

  it('renders responsive containers for charts when data exists', async () => {    api.getRecentTests.mockResolvedValue({ results: mockTests })
    render(<Statistics />)
    await waitFor(() => expect(screen.getAllByTestId('responsive-container').length).toBeGreaterThan(0))
  })

  it('shows table with test data', async () => {    api.getRecentTests.mockResolvedValue({ results: mockTests })
    render(<Statistics />)
    await waitFor(() => {
      // Check for the device serial - may appear multiple times in charts and table
      expect(screen.getAllByText('DEV-001').length).toBeGreaterThan(0)
      // Check for bandwidth formatting: 100Mbps (no space)
      expect(screen.getByText(/100Mbps|100 Mbps/)).toBeInTheDocument()
    })
  })
})
