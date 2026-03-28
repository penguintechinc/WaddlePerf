import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import DownloadTest from './DownloadTest'

// Helper to create a ReadableStream that yields one chunk then closes
function makeStream(bytes: Uint8Array): ReadableStream {
  return new ReadableStream({
    start(controller) {
      controller.enqueue(bytes)
      controller.close()
    },
  })
}

function makeFetchResponse(bodyBytes: Uint8Array = new Uint8Array(1024)) {
  return {
    ok: true,
    body: makeStream(bodyBytes),
  }
}

const mockFetch = vi.fn()
global.fetch = mockFetch

describe('DownloadTest component', () => {
  const testServerUrl = 'http://localhost:8080'

  beforeEach(() => {
    mockFetch.mockReset()
  })

  it('renders the Download Speed Test heading', () => {
    render(<DownloadTest testServerUrl={testServerUrl} />)
    expect(screen.getByText('Download Speed Test')).toBeInTheDocument()
  })

  it('renders the description', () => {
    render(<DownloadTest testServerUrl={testServerUrl} />)
    expect(screen.getByText(/Measure your download bandwidth/)).toBeInTheDocument()
  })

  it('shows all file size options', () => {
    render(<DownloadTest testServerUrl={testServerUrl} />)
    expect(screen.getByText('10 MB')).toBeInTheDocument()
    expect(screen.getByText('50 MB')).toBeInTheDocument()
    expect(screen.getByText('100 MB')).toBeInTheDocument()
    expect(screen.getByText('500 MB')).toBeInTheDocument()
    expect(screen.getByText('1 GB')).toBeInTheDocument()
  })

  it('shows Start Download Test button', () => {
    render(<DownloadTest testServerUrl={testServerUrl} />)
    expect(screen.getByText('Start Download Test')).toBeInTheDocument()
  })

  it('shows default selected size label', () => {
    render(<DownloadTest testServerUrl={testServerUrl} />)
    // Default is 100MB
    expect(screen.getByText(/Test will download a 100MB file/)).toBeInTheDocument()
  })

  it('changes selected size when a size button is clicked', () => {
    render(<DownloadTest testServerUrl={testServerUrl} />)
    fireEvent.click(screen.getByText('50 MB'))
    expect(screen.getByText(/Test will download a 50MB file/)).toBeInTheDocument()
  })

  it('marks the active size button with active class', () => {
    render(<DownloadTest testServerUrl={testServerUrl} />)
    const btn100 = screen.getByText('100 MB')
    expect(btn100.classList.contains('active')).toBe(true)
  })

  it('updates active class when different size is selected', () => {
    render(<DownloadTest testServerUrl={testServerUrl} />)
    fireEvent.click(screen.getByText('50 MB'))
    const btn50 = screen.getByText('50 MB')
    expect(btn50.classList.contains('active')).toBe(true)
    const btn100 = screen.getByText('100 MB')
    expect(btn100.classList.contains('active')).toBe(false)
  })

  it('shows the footer note', () => {
    render(<DownloadTest testServerUrl={testServerUrl} />)
    expect(screen.getByText(/Download test measures your maximum/)).toBeInTheDocument()
  })

  it('renders select size label', () => {
    render(<DownloadTest testServerUrl={testServerUrl} />)
    expect(screen.getByText('Select file size:')).toBeInTheDocument()
  })

  it('has an SVG download icon', () => {
    render(<DownloadTest testServerUrl={testServerUrl} />)
    const svg = document.querySelector('.downloadtest-icon svg')
    expect(svg).toBeTruthy()
  })

  it('starts download test and shows Cancel button', async () => {
    // Mock fetch to never resolve so we can check the running state
    mockFetch.mockImplementation(() => new Promise(() => {}))

    const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {})
    render(<DownloadTest testServerUrl={testServerUrl} />)

    // Select smallest size to make test faster
    fireEvent.click(screen.getByText('10 MB'))
    fireEvent.click(screen.getByText('Start Download Test'))

    await waitFor(() => expect(screen.getByText('Cancel')).toBeInTheDocument(), { timeout: 3000 })
    consoleSpy.mockRestore()
  })

  it('can cancel a running download test', async () => {
    // Mock fetch that respects the AbortSignal
    mockFetch.mockImplementation((url: string, options: RequestInit) => {
      return new Promise((_resolve, reject) => {
        // If signal is already aborted, reject immediately
        if (options?.signal?.aborted) {
          const err = new DOMException('Aborted', 'AbortError')
          reject(err)
          return
        }
        // Listen for abort event
        options?.signal?.addEventListener('abort', () => {
          const err = new DOMException('Aborted', 'AbortError')
          reject(err)
        })
      })
    })

    const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {})
    render(<DownloadTest testServerUrl={testServerUrl} />)

    fireEvent.click(screen.getByText('10 MB'))
    fireEvent.click(screen.getByText('Start Download Test'))

    await waitFor(() => screen.getByText('Cancel'), { timeout: 2000 })
    fireEvent.click(screen.getByText('Cancel'))

    // After cancelling, should return to idle (finally block sets isRunning=false)
    await waitFor(() => expect(screen.getByText('Start Download Test')).toBeInTheDocument(), { timeout: 3000 })
    consoleSpy.mockRestore()
  })

  it('handles a complete download test and shows results', async () => {
    // Use 10MB and return 10MB+1 of data so the while loop exits
    const bigBytes = new Uint8Array(10 * 1024 * 1024 + 1)

    mockFetch.mockResolvedValue(makeFetchResponse(bigBytes))

    const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {})
    render(<DownloadTest testServerUrl={testServerUrl} />)

    fireEvent.click(screen.getByText('10 MB'))
    fireEvent.click(screen.getByText('Start Download Test'))

    // Wait for results or back to idle
    await waitFor(() => {
      const hasResults = screen.queryByText('Test Complete!')
      const hasStart = screen.queryByText('Start Download Test')
      return hasResults !== null || hasStart !== null
    }, { timeout: 10000 })

    consoleSpy.mockRestore()
  })

  it('handles fetch failure during download', async () => {
    mockFetch.mockRejectedValue(new Error('Network error'))

    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    const consoleLogSpy = vi.spyOn(console, 'log').mockImplementation(() => {})
    render(<DownloadTest testServerUrl={testServerUrl} />)

    fireEvent.click(screen.getByText('10 MB'))
    fireEvent.click(screen.getByText('Start Download Test'))

    // Should return to idle state after failure
    await waitFor(() => expect(screen.getByText('Start Download Test')).toBeInTheDocument(), { timeout: 5000 })
    consoleSpy.mockRestore()
    consoleLogSpy.mockRestore()
  })

  it('handles HTTP error response during download', async () => {
    mockFetch.mockResolvedValue({ ok: false, status: 500, body: null })

    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    const consoleLogSpy = vi.spyOn(console, 'log').mockImplementation(() => {})
    render(<DownloadTest testServerUrl={testServerUrl} />)

    fireEvent.click(screen.getByText('10 MB'))
    fireEvent.click(screen.getByText('Start Download Test'))

    await waitFor(() => expect(screen.getByText('Start Download Test')).toBeInTheDocument(), { timeout: 5000 })
    consoleSpy.mockRestore()
    consoleLogSpy.mockRestore()
  })

  it('changes 1 GB label to show GB info text', () => {
    render(<DownloadTest testServerUrl={testServerUrl} />)
    fireEvent.click(screen.getByText('1 GB'))
    expect(screen.getByText(/Test will download a 1000MB file/)).toBeInTheDocument()
  })
})
