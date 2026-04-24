import { render, screen } from '@testing-library/react'
import { vi, describe, it, expect } from 'vitest'
import RealtimeCharts from './RealtimeCharts'
import type { LatencyDataPoint } from './TestRunner'

// Mock recharts to avoid complex SVG rendering in jsdom
vi.mock('recharts', () => ({
  LineChart: vi.fn(({ children }) => <div data-testid="line-chart">{children}</div>),
  Line: vi.fn(() => null),
  XAxis: vi.fn(() => null),
  YAxis: vi.fn(() => null),
  CartesianGrid: vi.fn(() => null),
  Tooltip: vi.fn(() => null),
  ResponsiveContainer: vi.fn(({ children }) => <div data-testid="responsive-container">{children}</div>),
}))

const defaultMetrics = {
  latency: 0,
  throughput: 0,
  jitter: 0,
  packetLoss: 0,
}

describe('RealtimeCharts component', () => {
  it('renders the real-time metrics section', () => {
    render(<RealtimeCharts latencyData={[]} currentMetrics={defaultMetrics} isRunning={false} />)
    expect(screen.getByText('Real-time Metrics')).toBeInTheDocument()
  })

  it('shows the four gauge cards', () => {
    render(<RealtimeCharts latencyData={[]} currentMetrics={defaultMetrics} isRunning={false} />)
    expect(screen.getByText('Latency')).toBeInTheDocument()
    expect(screen.getByText('Throughput')).toBeInTheDocument()
    expect(screen.getByText('Jitter')).toBeInTheDocument()
    expect(screen.getByText('Packet Loss')).toBeInTheDocument()
  })

  it('shows Live badge when isRunning is true', () => {
    render(<RealtimeCharts latencyData={[]} currentMetrics={defaultMetrics} isRunning={true} />)
    expect(screen.getByText('Live')).toBeInTheDocument()
  })

  it('hides Live badge when isRunning is false', () => {
    render(<RealtimeCharts latencyData={[]} currentMetrics={defaultMetrics} isRunning={false} />)
    expect(screen.queryByText('Live')).not.toBeInTheDocument()
  })

  it('displays formatted latency value', () => {
    const metrics = { ...defaultMetrics, latency: 45.678 }
    render(<RealtimeCharts latencyData={[]} currentMetrics={metrics} isRunning={false} />)
    expect(screen.getByText('45.68ms')).toBeInTheDocument()
  })

  it('displays formatted throughput value', () => {
    const metrics = { ...defaultMetrics, throughput: 100.5 }
    render(<RealtimeCharts latencyData={[]} currentMetrics={metrics} isRunning={false} />)
    expect(screen.getByText('100.50 Mbps')).toBeInTheDocument()
  })

  it('displays formatted packet loss percentage', () => {
    const metrics = { ...defaultMetrics, packetLoss: 2.5 }
    render(<RealtimeCharts latencyData={[]} currentMetrics={metrics} isRunning={false} />)
    expect(screen.getByText('2.50%')).toBeInTheDocument()
  })

  it('shows latency chart when there is data', () => {
    const latencyData: LatencyDataPoint[] = [
      { timestamp: Date.now(), latency: 20, index: 0 },
      { timestamp: Date.now(), latency: 30, index: 1 },
    ]
    render(<RealtimeCharts latencyData={latencyData} currentMetrics={defaultMetrics} isRunning={false} />)
    expect(screen.getByText('Latency Over Time')).toBeInTheDocument()
    expect(screen.getByTestId('responsive-container')).toBeInTheDocument()
  })

  it('hides latency chart section when there is no data', () => {
    render(<RealtimeCharts latencyData={[]} currentMetrics={defaultMetrics} isRunning={false} />)
    expect(screen.queryByText('Latency Over Time')).not.toBeInTheDocument()
  })

  it('shows gauge bar range labels for latency', () => {
    render(<RealtimeCharts latencyData={[]} currentMetrics={defaultMetrics} isRunning={false} />)
    // Multiple "0ms" elements may exist (latency = 0 displayed as "0.00ms" or "0ms" range labels)
    expect(screen.getAllByText('0ms').length).toBeGreaterThan(0)
    expect(screen.getByText('200ms')).toBeInTheDocument()
  })

  it('shows gauge bar range labels for throughput', () => {
    render(<RealtimeCharts latencyData={[]} currentMetrics={defaultMetrics} isRunning={false} />)
    expect(screen.getByText('1000 Mbps')).toBeInTheDocument()
  })

  it('shows gauge bar range labels for packet loss', () => {
    render(<RealtimeCharts latencyData={[]} currentMetrics={defaultMetrics} isRunning={false} />)
    expect(screen.getByText('10%')).toBeInTheDocument()
  })
})
