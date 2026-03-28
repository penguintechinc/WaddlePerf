import { render, screen, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import Dashboard from './Dashboard'
import { api } from '../services/api'

vi.mock('../services/api', () => ({
  api: {
    getRecentTests: vi.fn(),
  },
}))

vi.mock('recharts', () => ({
  LineChart: vi.fn(({ children }) => <div data-testid="line-chart">{children}</div>),
  Line: vi.fn(() => null),
  XAxis: vi.fn(() => null),
  YAxis: vi.fn(() => null),
  CartesianGrid: vi.fn(() => null),
  Tooltip: vi.fn(() => null),
  Legend: vi.fn(() => null),
  ResponsiveContainer: vi.fn(({ children }) => <div data-testid="responsive-container">{children}</div>),
}))

const mockTests = [
  { id: 1, device_serial: 'DEV-001', test_type: 'http', result_data: {}, created_at: new Date().toISOString(), latency: 25, success: true },
  { id: 2, device_serial: 'DEV-002', test_type: 'tcp', result_data: {}, created_at: new Date().toISOString(), latency: 50, success: true },
  { id: 3, device_serial: 'DEV-001', test_type: 'icmp', result_data: {}, created_at: new Date().toISOString(), latency: 10, success: false },
]

describe('Dashboard page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading state initially', () => {    api.getRecentTests.mockImplementation(() => new Promise(() => {}))
    render(<Dashboard />)
    expect(screen.getByText(/Loading dashboard/i)).toBeInTheDocument()
    expect(document.querySelector('.spinner')).toBeInTheDocument()
  })

  it('renders the Dashboard heading after loading', async () => {    api.getRecentTests.mockResolvedValue({ results: [] })
    render(<Dashboard />)
    await waitFor(() => expect(screen.getByText('Dashboard')).toBeInTheDocument())
  })

  it('shows stat cards after data loads', async () => {    api.getRecentTests.mockResolvedValue({ results: mockTests })
    render(<Dashboard />)
    await waitFor(() => {
      expect(screen.getByText('Total Tests')).toBeInTheDocument()
      expect(screen.getByText('Success Rate')).toBeInTheDocument()
      expect(screen.getByText('Avg Latency')).toBeInTheDocument()
      expect(screen.getByText('Active Devices')).toBeInTheDocument()
    })
  })

  it('calculates correct total test count', async () => {    api.getRecentTests.mockResolvedValue({ results: mockTests })
    render(<Dashboard />)
    await waitFor(() => {
      const statValues = screen.getAllByText('3')
      expect(statValues.length).toBeGreaterThan(0)
    })
  })

  it('shows error message when API call fails', async () => {    api.getRecentTests.mockRejectedValue({
      response: { data: { error: 'Server error' } },
    })
    render(<Dashboard />)
    await waitFor(() => expect(screen.getByText('Server error')).toBeInTheDocument())
  })

  it('shows fallback error when no response data', async () => {    api.getRecentTests.mockRejectedValue(new Error('Network error'))
    render(<Dashboard />)
    await waitFor(() => expect(screen.getByText('Failed to load dashboard data')).toBeInTheDocument())
  })

  it('shows recent tests table headers', async () => {    api.getRecentTests.mockResolvedValue({ results: mockTests })
    render(<Dashboard />)
    await waitFor(() => {
      expect(screen.getByText('Device')).toBeInTheDocument()
      expect(screen.getByText('Test Type')).toBeInTheDocument()
      expect(screen.getByText('Latency')).toBeInTheDocument()
      expect(screen.getByText('Status')).toBeInTheDocument()
      expect(screen.getByText('Timestamp')).toBeInTheDocument()
    })
  })

  it('shows device serials in table', async () => {    api.getRecentTests.mockResolvedValue({ results: mockTests })
    render(<Dashboard />)
    await waitFor(() => {
      expect(screen.getAllByText('DEV-001').length).toBeGreaterThan(0)
      expect(screen.getAllByText('DEV-002').length).toBeGreaterThan(0)
    })
  })

  it('shows success and failure badges', async () => {    api.getRecentTests.mockResolvedValue({ results: mockTests })
    render(<Dashboard />)
    await waitFor(() => {
      expect(screen.getAllByText('Success').length).toBeGreaterThan(0)
      expect(screen.getAllByText('Failed').length).toBeGreaterThan(0)
    })
  })

  it('shows no data message when no latency data', async () => {    api.getRecentTests.mockResolvedValue({ results: [] })
    render(<Dashboard />)
    await waitFor(() => expect(screen.getByText('No latency data available')).toBeInTheDocument())
  })

  it('shows chart section with recharts when latency data exists', async () => {    api.getRecentTests.mockResolvedValue({ results: mockTests })
    render(<Dashboard />)
    await waitFor(() => expect(screen.getByTestId('responsive-container')).toBeInTheDocument())
  })

  it('shows Recent Test Latency heading', async () => {    api.getRecentTests.mockResolvedValue({ results: mockTests })
    render(<Dashboard />)
    await waitFor(() => expect(screen.getByText('Recent Test Latency')).toBeInTheDocument())
  })
})
