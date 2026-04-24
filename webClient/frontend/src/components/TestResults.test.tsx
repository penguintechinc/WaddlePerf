import { render, screen, fireEvent } from '@testing-library/react'
import { vi, describe, it, expect } from 'vitest'
import TestResults from './TestResults'
import type { TestCompleteData } from '../services/websocket'

const baseResult: TestCompleteData = {
  test_type: 'http',
  target_host: 'example.com',
  target_ip: '93.184.216.34',
  success: true,
}

describe('TestResults component', () => {
  it('renders the modal with test result data', () => {
    render(<TestResults result={baseResult} onClose={vi.fn()} />)
    expect(screen.getByText('Network Test Results')).toBeInTheDocument()
  })

  it('shows Success status badge when result is successful', () => {
    render(<TestResults result={baseResult} onClose={vi.fn()} />)
    expect(screen.getByText('Success')).toBeInTheDocument()
  })

  it('shows Failed status badge when result is unsuccessful', () => {
    render(<TestResults result={{ ...baseResult, success: false }} onClose={vi.fn()} />)
    expect(screen.getByText('Failed')).toBeInTheDocument()
  })

  it('displays the test type in uppercase', () => {
    render(<TestResults result={baseResult} onClose={vi.fn()} />)
    expect(screen.getByText('HTTP')).toBeInTheDocument()
  })

  it('displays the target host', () => {
    render(<TestResults result={baseResult} onClose={vi.fn()} />)
    expect(screen.getByText('example.com')).toBeInTheDocument()
  })

  it('displays the target IP', () => {
    render(<TestResults result={baseResult} onClose={vi.fn()} />)
    expect(screen.getByText('93.184.216.34')).toBeInTheDocument()
  })

  it('shows latency metric when provided', () => {
    const result = { ...baseResult, latency_ms: 25.5 }
    render(<TestResults result={result} onClose={vi.fn()} />)
    expect(screen.getByText('25.50')).toBeInTheDocument()
    expect(screen.getByText('Latency')).toBeInTheDocument()
  })

  it('hides latency card when latency is not provided', () => {
    render(<TestResults result={baseResult} onClose={vi.fn()} />)
    expect(screen.queryByText('Latency')).not.toBeInTheDocument()
  })

  it('shows throughput metric when provided', () => {
    const result = { ...baseResult, throughput_mbps: 100.25 }
    render(<TestResults result={result} onClose={vi.fn()} />)
    expect(screen.getByText('100.25')).toBeInTheDocument()
    expect(screen.getByText('Throughput')).toBeInTheDocument()
  })

  it('shows jitter metric when provided', () => {
    const result = { ...baseResult, jitter_ms: 3.75 }
    render(<TestResults result={result} onClose={vi.fn()} />)
    expect(screen.getByText('3.75')).toBeInTheDocument()
    expect(screen.getByText('Jitter')).toBeInTheDocument()
  })

  it('shows packet loss metric when provided', () => {
    const result = { ...baseResult, packet_loss_percent: 0.5 }
    render(<TestResults result={result} onClose={vi.fn()} />)
    expect(screen.getByText('0.5')).toBeInTheDocument()
    expect(screen.getByText('Packet Loss')).toBeInTheDocument()
  })

  it('displays error message when result has an error', () => {
    const result = { ...baseResult, success: false, error: 'Connection refused' }
    render(<TestResults result={result} onClose={vi.fn()} />)
    expect(screen.getByText('Connection refused')).toBeInTheDocument()
  })

  it('shows raw results when provided', () => {
    const result = { ...baseResult, raw_results: { key: 'value', count: 42 } }
    render(<TestResults result={result} onClose={vi.fn()} />)
    expect(screen.getByText('Detailed Results')).toBeInTheDocument()
    expect(screen.getByText(/"key": "value"/)).toBeInTheDocument()
  })

  it('hides raw results section when empty', () => {
    render(<TestResults result={baseResult} onClose={vi.fn()} />)
    expect(screen.queryByText('Detailed Results')).not.toBeInTheDocument()
  })

  it('calls onClose when Close button is clicked', () => {
    const mockClose = vi.fn()
    render(<TestResults result={baseResult} onClose={mockClose} />)
    fireEvent.click(screen.getByText('Close'))
    expect(mockClose).toHaveBeenCalledOnce()
  })

  it('calls onClose when overlay is clicked', () => {
    const mockClose = vi.fn()
    render(<TestResults result={baseResult} onClose={mockClose} />)
    const overlay = document.querySelector('.modal-overlay')!
    fireEvent.click(overlay)
    expect(mockClose).toHaveBeenCalled()
  })

  it('does not close when modal content is clicked', () => {
    const mockClose = vi.fn()
    render(<TestResults result={baseResult} onClose={mockClose} />)
    const content = document.querySelector('.modal-content')!
    fireEvent.click(content)
    expect(mockClose).not.toHaveBeenCalled()
  })

  it('shows Run Again button when onRunAgain is provided', () => {
    render(<TestResults result={baseResult} onClose={vi.fn()} onRunAgain={vi.fn()} />)
    expect(screen.getByText('Run Again')).toBeInTheDocument()
  })

  it('hides Run Again button when onRunAgain is not provided', () => {
    render(<TestResults result={baseResult} onClose={vi.fn()} />)
    expect(screen.queryByText('Run Again')).not.toBeInTheDocument()
  })

  it('calls both onClose and onRunAgain when Run Again is clicked', () => {
    const mockClose = vi.fn()
    const mockRunAgain = vi.fn()
    render(<TestResults result={baseResult} onClose={mockClose} onRunAgain={mockRunAgain} />)
    fireEvent.click(screen.getByText('Run Again'))
    expect(mockClose).toHaveBeenCalledOnce()
    expect(mockRunAgain).toHaveBeenCalledOnce()
  })

  it('shows × close button in modal header', () => {
    render(<TestResults result={baseResult} onClose={vi.fn()} />)
    const closeBtn = screen.getByText('×')
    expect(closeBtn).toBeInTheDocument()
  })

  it('calls onClose when × header button is clicked', () => {
    const mockClose = vi.fn()
    render(<TestResults result={baseResult} onClose={mockClose} />)
    fireEvent.click(screen.getByText('×'))
    expect(mockClose).toHaveBeenCalledOnce()
  })
})
