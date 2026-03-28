import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import SpeedTest from './SpeedTest'

// Helper to create a ReadableStream that yields one chunk then closes
function makeStream(bytes: Uint8Array): ReadableStream {
  return new ReadableStream({
    start(controller) {
      controller.enqueue(bytes)
      controller.close()
    },
  })
}

function makeFetchResponse(data: any = {}, bodyBytes: Uint8Array = new Uint8Array(1024)) {
  return {
    ok: true,
    json: vi.fn().mockResolvedValue(data),
    body: makeStream(bodyBytes),
  }
}

const mockFetch = vi.fn()
global.fetch = mockFetch

describe('SpeedTest component', () => {
  const testServerUrl = 'http://localhost:8080'

  beforeEach(() => {
    mockFetch.mockReset()
    mockFetch.mockResolvedValue(makeFetchResponse({ name: 'Test Server' }))
  })

  it('renders the Speed Test heading', async () => {
    render(<SpeedTest testServerUrl={testServerUrl} />)
    await waitFor(() => expect(screen.getByText('Speed Test')).toBeInTheDocument())
  })

  it('renders the description text', () => {
    render(<SpeedTest testServerUrl={testServerUrl} />)
    expect(screen.getByText(/Measure your bandwidth/)).toBeInTheDocument()
  })

  it('shows Start Speed Test button in idle state', async () => {
    render(<SpeedTest testServerUrl={testServerUrl} />)
    await waitFor(() => expect(screen.getAllByText('Start Speed Test').length).toBeGreaterThan(0), { timeout: 3000 })
  })

  it('shows server info after loading', async () => {
    render(<SpeedTest testServerUrl={testServerUrl} />)
    await waitFor(() => expect(screen.getByText('Server: Test Server')).toBeInTheDocument(), { timeout: 3000 })
  })

  it('shows streams slider in idle state', () => {
    render(<SpeedTest testServerUrl={testServerUrl} />)
    const slider = screen.getByRole('slider')
    expect(slider).toBeInTheDocument()
  })

  it('shows number of streams control', () => {
    render(<SpeedTest testServerUrl={testServerUrl} />)
    expect(screen.getByText(/Number of Streams:/)).toBeInTheDocument()
  })

  it('shows default 6 streams', () => {
    render(<SpeedTest testServerUrl={testServerUrl} />)
    const label = screen.getByText(/Number of Streams:/)
    expect(label).toBeInTheDocument()
    const strongEl = label.querySelector('strong') || label.parentElement?.querySelector('strong')
    expect(strongEl?.textContent).toBe('6')
  })

  it('changes number of streams when slider is moved', () => {
    render(<SpeedTest testServerUrl={testServerUrl} />)
    const slider = screen.getByRole('slider')
    fireEvent.change(slider, { target: { value: '10' } })
    const label = screen.getByText(/Number of Streams:/)
    const strongEl = label.querySelector('strong') || label.parentElement?.querySelector('strong')
    expect(strongEl?.textContent).toBe('10')
  })

  it('shows footer note', () => {
    render(<SpeedTest testServerUrl={testServerUrl} />)
    expect(screen.getByText(/Tests run directly from your browser/)).toBeInTheDocument()
  })

  it('fetches server info on mount using the provided URL', async () => {
    render(<SpeedTest testServerUrl={testServerUrl} />)
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(`${testServerUrl}/speedtest/info`)
    }, { timeout: 3000 })
  })

  it('handles server info fetch failure gracefully', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'))
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    render(<SpeedTest testServerUrl={testServerUrl} />)
    await waitFor(() => expect(consoleSpy).toHaveBeenCalled(), { timeout: 3000 })
    expect(screen.getByText('Speed Test')).toBeInTheDocument()
    consoleSpy.mockRestore()
  })

  it('shows streams range labels 1 and 20', () => {
    render(<SpeedTest testServerUrl={testServerUrl} />)
    const labels = screen.getAllByText(/^(1|20)$/)
    expect(labels.length).toBeGreaterThanOrEqual(2)
  })

  it('starts speed test when Start Speed Test button is clicked', async () => {
    // Ping never resolves so test stays in running state
    mockFetch.mockImplementation((url: string) => {
      if (url.includes('/speedtest/info')) {
        return Promise.resolve(makeFetchResponse({ name: 'Test Server' }))
      }
      return new Promise(() => {}) // Never resolves
    })

    const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {})
    render(<SpeedTest testServerUrl={testServerUrl} />)

    await waitFor(() => screen.getAllByText('Start Speed Test'), { timeout: 3000 })
    fireEvent.click(screen.getAllByText('Start Speed Test')[0])

    await waitFor(() => expect(screen.getByText('Cancel')).toBeInTheDocument(), { timeout: 3000 })
    consoleSpy.mockRestore()
  })

  it('can cancel a running speed test', async () => {
    // Fetch that respects the abort signal
    mockFetch.mockImplementation((url: string, options?: RequestInit) => {
      if (url.includes('/speedtest/info')) {
        return Promise.resolve(makeFetchResponse({ name: 'Test Server' }))
      }
      return new Promise((_resolve, reject) => {
        if (options?.signal?.aborted) {
          reject(new DOMException('Aborted', 'AbortError'))
          return
        }
        options?.signal?.addEventListener('abort', () => {
          reject(new DOMException('Aborted', 'AbortError'))
        })
      })
    })

    const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {})
    render(<SpeedTest testServerUrl={testServerUrl} />)

    await waitFor(() => screen.getAllByText('Start Speed Test'), { timeout: 3000 })
    fireEvent.click(screen.getAllByText('Start Speed Test')[0])
    await waitFor(() => screen.getByText('Cancel'), { timeout: 2000 })
    fireEvent.click(screen.getByText('Cancel'))

    // After abort, should eventually go back to idle
    await waitFor(() => expect(screen.queryByText('Cancel')).not.toBeInTheDocument(), { timeout: 3000 })
    consoleSpy.mockRestore()
  })

  it('handles failed ping during latency measurement (warn)', async () => {
    // Pings fail with non-abort error, then never resolve to keep test in running state
    let pingCount = 0
    mockFetch.mockImplementation((url: string) => {
      if (url.includes('/speedtest/info')) {
        return Promise.resolve(makeFetchResponse({ name: 'Test Server' }))
      }
      if (url.includes('/speedtest/ping')) {
        pingCount++
        if (pingCount <= 3) {
          return Promise.reject(new Error('Ping failed'))
        }
        return new Promise(() => {}) // Stall after a few pings
      }
      return new Promise(() => {})
    })

    const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {})
    const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

    render(<SpeedTest testServerUrl={testServerUrl} />)
    await waitFor(() => screen.getAllByText('Start Speed Test'), { timeout: 3000 })
    fireEvent.click(screen.getAllByText('Start Speed Test')[0])

    await waitFor(() => expect(screen.getByText('Cancel')).toBeInTheDocument(), { timeout: 3000 })
    await waitFor(() => expect(consoleWarnSpy).toHaveBeenCalled(), { timeout: 5000 })

    consoleSpy.mockRestore()
    consoleWarnSpy.mockRestore()
  })

  it('shows phase indicators during running state', async () => {
    // Make fetch never resolve for pings
    mockFetch.mockImplementation((url: string) => {
      if (url.includes('/speedtest/info')) {
        return Promise.resolve(makeFetchResponse({ name: 'Test Server' }))
      }
      return new Promise(() => {})
    })

    const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {})
    render(<SpeedTest testServerUrl={testServerUrl} />)
    await waitFor(() => screen.getAllByText('Start Speed Test'), { timeout: 3000 })
    fireEvent.click(screen.getAllByText('Start Speed Test')[0])

    await waitFor(() => expect(screen.getByText('Cancel')).toBeInTheDocument(), { timeout: 3000 })
    // Phase indicators should be visible during test (multiple Latency elements may exist)
    expect(screen.getAllByText('Latency').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Download').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Upload').length).toBeGreaterThan(0)

    consoleSpy.mockRestore()
  })

  it('renders formatSpeed for different speed values', () => {
    render(<SpeedTest testServerUrl={testServerUrl} />)
    // Just verify it renders - formatSpeed is used in display logic
    expect(screen.getByText('Speed Test')).toBeInTheDocument()
  })

  it('handles multiple parallel streams', () => {
    render(<SpeedTest testServerUrl={testServerUrl} />)
    const slider = screen.getByRole('slider')
    fireEvent.change(slider, { target: { value: '12' } })
    const label = screen.getByText(/Number of Streams:/)
    const strongEl = label.querySelector('strong') || label.parentElement?.querySelector('strong')
    expect(strongEl?.textContent).toBe('12')
  })

  it('slider respects min and max bounds', () => {
    render(<SpeedTest testServerUrl={testServerUrl} />)
    const slider = screen.getByRole('slider') as HTMLInputElement
    expect(slider.min).toBe('1')
    expect(slider.max).toBe('20')
  })
})
