import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import TestForm from './TestForm'

describe('TestForm component', () => {
  const mockOnTestStart = vi.fn()

  beforeEach(() => {
    mockOnTestStart.mockClear()
  })

  it('renders the test form with all sections', () => {
    render(<TestForm onTestStart={mockOnTestStart} isRunning={false} />)
    expect(screen.getByText('Test Configuration')).toBeInTheDocument()
    expect(screen.getByText('Configure and run network performance tests')).toBeInTheDocument()
  })

  it('renders all four test type buttons', () => {
    render(<TestForm onTestStart={mockOnTestStart} isRunning={false} />)
    expect(screen.getByText('HTTP')).toBeInTheDocument()
    expect(screen.getByText('TCP')).toBeInTheDocument()
    expect(screen.getByText('UDP')).toBeInTheDocument()
    expect(screen.getByText('ICMP')).toBeInTheDocument()
  })

  it('shows Start Test button when not running', () => {
    render(<TestForm onTestStart={mockOnTestStart} isRunning={false} />)
    expect(screen.getByText('Start Test')).toBeInTheDocument()
  })

  it('shows Running Test... when isRunning is true', () => {
    render(<TestForm onTestStart={mockOnTestStart} isRunning={true} />)
    expect(screen.getByText('Running Test...')).toBeInTheDocument()
  })

  it('disables test type buttons when test is running', () => {
    render(<TestForm onTestStart={mockOnTestStart} isRunning={true} />)
    const httpBtn = screen.getByText('HTTP')
    expect(httpBtn).toBeDisabled()
  })

  it('shows protocol dropdown for HTTP test type', () => {
    render(<TestForm onTestStart={mockOnTestStart} isRunning={false} />)
    expect(screen.getByRole('combobox')).toBeInTheDocument()
    expect(screen.getByText('HTTP/1.1')).toBeInTheDocument()
    expect(screen.getByText('HTTP/2')).toBeInTheDocument()
    expect(screen.getByText('HTTP/3')).toBeInTheDocument()
  })

  it('shows DNS query field when UDP is selected', async () => {
    const user = userEvent.setup()
    render(<TestForm onTestStart={mockOnTestStart} isRunning={false} />)
    await user.click(screen.getByText('UDP'))
    expect(screen.getByLabelText(/DNS Query/i)).toBeInTheDocument()
  })

  it('hides port field for ICMP test type', async () => {
    const user = userEvent.setup()
    render(<TestForm onTestStart={mockOnTestStart} isRunning={false} />)
    await user.click(screen.getByText('ICMP'))
    expect(screen.queryByLabelText(/^Port$/i)).not.toBeInTheDocument()
  })

  it('shows validation error for empty target on submit', async () => {
    render(<TestForm onTestStart={mockOnTestStart} isRunning={false} />)
    // Submit the form directly — button is disabled when target is empty
    const form = document.querySelector('form')!
    fireEvent.submit(form)
    expect(screen.getByText(/Target cannot be empty/i)).toBeInTheDocument()
  })

  it('shows validation error for invalid port', async () => {
    const user = userEvent.setup()
    render(<TestForm onTestStart={mockOnTestStart} isRunning={false} />)
    const targetInput = screen.getByLabelText(/Target Host/i)
    await user.type(targetInput, 'example.com')
    const portInput = screen.getByLabelText(/^Port$/i)
    await user.clear(portInput)
    await user.type(portInput, '99999')
    // Submit the form directly to bypass disabled-button check
    const form = document.querySelector('form')!
    fireEvent.submit(form)
    expect(screen.getByText(/Port must be between/i)).toBeInTheDocument()
  })

  it('shows validation error for invalid timeout', async () => {
    const user = userEvent.setup()
    render(<TestForm onTestStart={mockOnTestStart} isRunning={false} />)
    const targetInput = screen.getByLabelText(/Target Host/i)
    await user.type(targetInput, 'example.com')
    const timeoutInput = screen.getByLabelText(/Timeout/i)
    await user.clear(timeoutInput)
    await user.type(timeoutInput, '99999')
    const form = document.querySelector('form')!
    fireEvent.submit(form)
    expect(screen.getByText(/Timeout cannot exceed/i)).toBeInTheDocument()
  })

  it('calls onTestStart with correct data when form is valid', async () => {
    const user = userEvent.setup()
    render(<TestForm onTestStart={mockOnTestStart} isRunning={false} />)
    const targetInput = screen.getByLabelText(/Target Host/i)
    await user.type(targetInput, 'example.com')
    await user.click(screen.getByText('Start Test'))
    expect(mockOnTestStart).toHaveBeenCalledOnce()
    const callArgs = mockOnTestStart.mock.calls[0][0]
    expect(callArgs.test_type).toBe('http')
    expect(callArgs.target).toBe('example.com')
  })

  it('changes test type when clicking TCP button', async () => {
    const user = userEvent.setup()
    render(<TestForm onTestStart={mockOnTestStart} isRunning={false} />)
    await user.click(screen.getByText('TCP'))
    expect(screen.getByText('Raw TCP')).toBeInTheDocument()
    expect(screen.getByText('SSH')).toBeInTheDocument()
    expect(screen.getByText('TLS')).toBeInTheDocument()
  })

  it('start button is disabled when target is empty', () => {
    render(<TestForm onTestStart={mockOnTestStart} isRunning={false} />)
    const submitBtn = screen.getByText('Start Test')
    expect(submitBtn).toBeDisabled()
  })

  it('start button becomes enabled when target has a value', async () => {
    const user = userEvent.setup()
    render(<TestForm onTestStart={mockOnTestStart} isRunning={false} />)
    const targetInput = screen.getByLabelText(/Target Host/i)
    await user.type(targetInput, 'example.com')
    expect(screen.getByText('Start Test')).not.toBeDisabled()
  })

  it('shows UDP DNS fields when UDP is selected', async () => {
    const user = userEvent.setup()
    render(<TestForm onTestStart={mockOnTestStart} isRunning={false} />)
    await user.click(screen.getByText('UDP'))
    expect(screen.getByLabelText(/Target DNS Server/i)).toBeInTheDocument()
    expect(screen.getByText('DNS uses port 53')).toBeInTheDocument()
  })

  it('validates DNS query for UDP test type', async () => {
    const user = userEvent.setup()
    render(<TestForm onTestStart={mockOnTestStart} isRunning={false} />)
    await user.click(screen.getByText('UDP'))
    const targetInput = screen.getByLabelText(/Target DNS Server/i)
    await user.type(targetInput, '8.8.8.8')
    const dnsQueryInput = screen.getByLabelText(/DNS Query/i)
    await user.clear(dnsQueryInput)
    await user.type(dnsQueryInput, 'invalid domain!')
    await user.click(screen.getByText('Start Test'))
    expect(screen.getByText(/Invalid domain name format/i)).toBeInTheDocument()
  })

  it('shows footer info about timeout and count', () => {
    render(<TestForm onTestStart={mockOnTestStart} isRunning={false} />)
    expect(screen.getByText(/Timeout:/)).toBeInTheDocument()
    expect(screen.getByText(/Count:/)).toBeInTheDocument()
  })
})
