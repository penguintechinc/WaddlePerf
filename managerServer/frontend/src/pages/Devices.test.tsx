import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import Devices from './Devices'
import axios from 'axios'
import * as AuthContextModule from '../contexts/AuthContext'

vi.mock('../contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}))

const mockUseAuth = vi.mocked(AuthContextModule.useAuth)

vi.mock('axios')

global.confirm = vi.fn()
global.alert = vi.fn()

const mockDevices = [
  {
    id: 1,
    device_serial: 'SN-001',
    device_hostname: 'laptop-01',
    device_os: 'Linux',
    device_os_version: '22.04',
    client_type: 'container',
    client_version: '1.0.0',
    enrolled_at: new Date().toISOString(),
    last_seen: new Date().toISOString(),
    is_active: true,
    ou_id: 1,
    ou_name: 'Engineering',
    minutes_since_last_seen: 2,
    status: 'online' as const,
  },
  {
    id: 2,
    device_serial: 'SN-002',
    device_hostname: 'server-02',
    device_os: 'Windows',
    device_os_version: '11',
    client_type: 'thin',
    client_version: null,
    enrolled_at: new Date().toISOString(),
    last_seen: null,
    is_active: false,
    ou_id: 1,
    ou_name: 'DevOps',
    minutes_since_last_seen: null,
    status: 'never' as const,
  },
]

const mockStats = {
  total: 2,
  online: 1,
  recent: 0,
  offline: 0,
  stale: 0,
  active: 1,
  inactive: 1,
}

const mockAdminUser = {
  id: 1,
  username: 'admin',
  email: 'admin@test.com',
  role: 'global_admin',
  ou_id: null,
  mfa_enabled: false,
  is_active: true,
  created_at: '',
  updated_at: '',
}

describe('Devices page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseAuth.mockReturnValue({ user: mockAdminUser } as any)
    ;(axios.get as ReturnType<typeof vi.fn>).mockImplementation((url: string) => {
      if (url.includes('/stats')) return Promise.resolve({ data: mockStats })
      return Promise.resolve({ data: { devices: mockDevices, pages: 1 } })
    })
  })

  it('shows loading state initially', () => {
    ;(axios.get as ReturnType<typeof vi.fn>).mockImplementation(() => new Promise(() => {}))
    render(<Devices />)
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('renders Devices heading', async () => {
    render(<Devices />)
    await waitFor(() => expect(screen.getByText('Devices')).toBeInTheDocument())
  })

  it('shows statistics cards after loading', async () => {
    render(<Devices />)
    await waitFor(() => {
      expect(screen.getByText('Total Devices')).toBeInTheDocument()
      expect(screen.getByText('Online Now')).toBeInTheDocument()
      expect(screen.getByText('Recently Seen')).toBeInTheDocument()
      expect(screen.getByText('Offline/Stale')).toBeInTheDocument()
    })
  })

  it('shows correct total devices count', async () => {
    render(<Devices />)
    await waitFor(() => {
      expect(screen.getByText('2')).toBeInTheDocument()
    })
  })

  it('shows device hostnames in table', async () => {
    render(<Devices />)
    await waitFor(() => {
      expect(screen.getByText('laptop-01')).toBeInTheDocument()
      expect(screen.getByText('server-02')).toBeInTheDocument()
    })
  })

  it('shows device serials', async () => {
    render(<Devices />)
    await waitFor(() => {
      expect(screen.getByText('SN-001')).toBeInTheDocument()
      expect(screen.getByText('SN-002')).toBeInTheDocument()
    })
  })

  it('shows organization names', async () => {
    render(<Devices />)
    await waitFor(() => {
      expect(screen.getByText('Engineering')).toBeInTheDocument()
      expect(screen.getByText('DevOps')).toBeInTheDocument()
    })
  })

  it('shows Online status badge for active device', async () => {
    render(<Devices />)
    await waitFor(() => expect(screen.getByText('Online')).toBeInTheDocument())
  })

  it('shows Never status badge for device never seen', async () => {
    render(<Devices />)
    await waitFor(() => expect(screen.getAllByText('Never').length).toBeGreaterThan(0))
  })

  it('shows Inactive badge for inactive devices', async () => {
    render(<Devices />)
    await waitFor(() => expect(screen.getByText('Inactive')).toBeInTheDocument())
  })

  it('shows search input', async () => {
    render(<Devices />)
    await waitFor(() => expect(screen.getByPlaceholderText(/Search by serial or hostname/)).toBeInTheDocument())
  })

  it('shows status filter dropdown', async () => {
    render(<Devices />)
    await waitFor(() => {
      const select = screen.getByRole('combobox')
      expect(select).toBeInTheDocument()
    })
  })

  it('shows Deactivate button for active devices when user is admin', async () => {
    render(<Devices />)
    await waitFor(() => expect(screen.getByText('Deactivate')).toBeInTheDocument())
  })

  it('shows Reactivate button for inactive devices when user is admin', async () => {
    render(<Devices />)
    await waitFor(() => expect(screen.getByText('Reactivate')).toBeInTheDocument())
  })

  it('hides action buttons for non-admin users', async () => {
    mockUseAuth.mockReturnValue({ user: { ...mockAdminUser, role: 'user' } } as any)
    render(<Devices />)
    await waitFor(() => {
      expect(screen.queryByText('Deactivate')).not.toBeInTheDocument()
      expect(screen.queryByText('Reactivate')).not.toBeInTheDocument()
    })
  })

  it('calls deactivate API when Deactivate is confirmed', async () => {
    ;(global.confirm as ReturnType<typeof vi.fn>).mockReturnValue(true)
    ;(axios.post as ReturnType<typeof vi.fn>).mockResolvedValue({})
    render(<Devices />)
    await waitFor(() => screen.getByText('Deactivate'))
    fireEvent.click(screen.getByText('Deactivate'))
    await waitFor(() => expect(axios.post).toHaveBeenCalled())
  })

  it('does not call deactivate when cancelled', async () => {
    ;(global.confirm as ReturnType<typeof vi.fn>).mockReturnValue(false)
    render(<Devices />)
    await waitFor(() => screen.getByText('Deactivate'))
    fireEvent.click(screen.getByText('Deactivate'))
    expect(axios.post).not.toHaveBeenCalled()
  })

  it('shows error message when API fails', async () => {
    ;(axios.get as ReturnType<typeof vi.fn>).mockRejectedValue({ response: { data: { error: 'Fetch failed' } } })
    render(<Devices />)
    await waitFor(() => expect(screen.getByText('Fetch failed')).toBeInTheDocument())
  })

  it('shows "No devices found" when list is empty', async () => {
    ;(axios.get as ReturnType<typeof vi.fn>).mockImplementation((url: string) => {
      if (url.includes('/stats')) return Promise.resolve({ data: mockStats })
      return Promise.resolve({ data: { devices: [], pages: 1 } })
    })
    render(<Devices />)
    await waitFor(() => expect(screen.getByText('No devices found')).toBeInTheDocument())
  })

  it('formats "Just now" for very recent last_seen', async () => {
    const recentDevices = [{ ...mockDevices[0], minutes_since_last_seen: 0.5 }]
    ;(axios.get as ReturnType<typeof vi.fn>).mockImplementation((url: string) => {
      if (url.includes('/stats')) return Promise.resolve({ data: mockStats })
      return Promise.resolve({ data: { devices: recentDevices, pages: 1 } })
    })
    render(<Devices />)
    await waitFor(() => expect(screen.getByText('Just now')).toBeInTheDocument())
  })

  it('shows Never for device with null last_seen', async () => {
    render(<Devices />)
    await waitFor(() => expect(screen.getAllByText('Never').length).toBeGreaterThan(0))
  })

  it('formats minutes-ago for device seen recently', async () => {
    const recentDevices = [{ ...mockDevices[0], minutes_since_last_seen: 30 }]
    ;(axios.get as ReturnType<typeof vi.fn>).mockImplementation((url: string) => {
      if (url.includes('/stats')) return Promise.resolve({ data: mockStats })
      return Promise.resolve({ data: { devices: recentDevices, pages: 1 } })
    })
    render(<Devices />)
    await waitFor(() => expect(screen.getByText('30m ago')).toBeInTheDocument())
  })

  it('formats hours-ago for device seen hours ago', async () => {
    const recentDevices = [{ ...mockDevices[0], minutes_since_last_seen: 120 }]
    ;(axios.get as ReturnType<typeof vi.fn>).mockImplementation((url: string) => {
      if (url.includes('/stats')) return Promise.resolve({ data: mockStats })
      return Promise.resolve({ data: { devices: recentDevices, pages: 1 } })
    })
    render(<Devices />)
    await waitFor(() => expect(screen.getByText('2h ago')).toBeInTheDocument())
  })

  it('formats days-ago for device seen days ago', async () => {
    const recentDevices = [{ ...mockDevices[0], minutes_since_last_seen: 2880 }]
    ;(axios.get as ReturnType<typeof vi.fn>).mockImplementation((url: string) => {
      if (url.includes('/stats')) return Promise.resolve({ data: mockStats })
      return Promise.resolve({ data: { devices: recentDevices, pages: 1 } })
    })
    render(<Devices />)
    await waitFor(() => expect(screen.getByText('2d ago')).toBeInTheDocument())
  })

  it('shows Unknown when last_seen is set but minutesSince is null', async () => {
    const recentDevices = [{ ...mockDevices[0], last_seen: new Date().toISOString(), minutes_since_last_seen: null }]
    ;(axios.get as ReturnType<typeof vi.fn>).mockImplementation((url: string) => {
      if (url.includes('/stats')) return Promise.resolve({ data: mockStats })
      return Promise.resolve({ data: { devices: recentDevices, pages: 1 } })
    })
    render(<Devices />)
    await waitFor(() => expect(screen.getByText('Unknown')).toBeInTheDocument())
  })

  it('calls reactivate API when Reactivate button is clicked', async () => {
    ;(axios.post as ReturnType<typeof vi.fn>).mockResolvedValue({})
    render(<Devices />)
    await waitFor(() => screen.getByText('Reactivate'))
    fireEvent.click(screen.getByText('Reactivate'))
    await waitFor(() => expect(axios.post).toHaveBeenCalledWith(
      expect.stringContaining('/reactivate'),
      {},
      expect.objectContaining({ withCredentials: true })
    ))
  })

  it('shows alert when reactivate API fails', async () => {
    ;(axios.post as ReturnType<typeof vi.fn>).mockRejectedValue({ response: { data: { error: 'Reactivate failed' } } })
    const alertSpy = vi.spyOn(global, 'alert').mockImplementation(() => {})
    render(<Devices />)
    await waitFor(() => screen.getByText('Reactivate'))
    fireEvent.click(screen.getByText('Reactivate'))
    await waitFor(() => expect(alertSpy).toHaveBeenCalledWith('Reactivate failed'))
    alertSpy.mockRestore()
  })

  it('shows alert when deactivate API fails', async () => {
    ;(global.confirm as ReturnType<typeof vi.fn>).mockReturnValue(true)
    ;(axios.post as ReturnType<typeof vi.fn>).mockRejectedValue({ response: { data: { error: 'Deactivate failed' } } })
    const alertSpy = vi.spyOn(global, 'alert').mockImplementation(() => {})
    render(<Devices />)
    await waitFor(() => screen.getByText('Deactivate'))
    fireEvent.click(screen.getByText('Deactivate'))
    await waitFor(() => expect(alertSpy).toHaveBeenCalledWith('Deactivate failed'))
    alertSpy.mockRestore()
  })

  it('shows pagination when totalPages > 1', async () => {
    ;(axios.get as ReturnType<typeof vi.fn>).mockImplementation((url: string) => {
      if (url.includes('/stats')) return Promise.resolve({ data: mockStats })
      return Promise.resolve({ data: { devices: mockDevices, pages: 3 } })
    })
    render(<Devices />)
    await waitFor(() => {
      expect(screen.getByText('Previous')).toBeInTheDocument()
      expect(screen.getByText('Next')).toBeInTheDocument()
      expect(screen.getByText('Page 1 of 3')).toBeInTheDocument()
    })
  })

  it('changes page when Next is clicked', async () => {
    ;(axios.get as ReturnType<typeof vi.fn>).mockImplementation((url: string) => {
      if (url.includes('/stats')) return Promise.resolve({ data: mockStats })
      return Promise.resolve({ data: { devices: mockDevices, pages: 3 } })
    })
    render(<Devices />)
    await waitFor(() => screen.getByText('Next'))
    fireEvent.click(screen.getByText('Next'))
    await waitFor(() => expect(screen.getByText('Page 2 of 3')).toBeInTheDocument())
  })

  it('resets page to 1 when status filter is changed', async () => {
    ;(axios.get as ReturnType<typeof vi.fn>).mockImplementation((url: string) => {
      if (url.includes('/stats')) return Promise.resolve({ data: mockStats })
      return Promise.resolve({ data: { devices: mockDevices, pages: 3 } })
    })
    render(<Devices />)
    await waitFor(() => screen.getByText('Next'))
    fireEvent.click(screen.getByText('Next'))
    await waitFor(() => expect(screen.getByText('Page 2 of 3')).toBeInTheDocument())
    const select = screen.getByRole('combobox')
    fireEvent.change(select, { target: { value: 'online' } })
    await waitFor(() => expect(screen.getByText('Page 1 of 3')).toBeInTheDocument())
  })

  it('updates search term and resets page to 1', async () => {
    ;(axios.get as ReturnType<typeof vi.fn>).mockImplementation((url: string) => {
      if (url.includes('/stats')) return Promise.resolve({ data: mockStats })
      return Promise.resolve({ data: { devices: mockDevices, pages: 3 } })
    })
    render(<Devices />)
    await waitFor(() => screen.getByText('Next'))
    fireEvent.click(screen.getByText('Next'))
    await waitFor(() => expect(screen.getByText('Page 2 of 3')).toBeInTheDocument())
    const searchInput = screen.getByPlaceholderText(/Search by serial or hostname/)
    fireEvent.change(searchInput, { target: { value: 'laptop' } })
    await waitFor(() => expect(screen.getByText('Page 1 of 3')).toBeInTheDocument())
  })

  it('shows getStatusText Unknown for unrecognized status', async () => {
    const weirdDevices = [{ ...mockDevices[0], status: 'weird' as any }]
    ;(axios.get as ReturnType<typeof vi.fn>).mockImplementation((url: string) => {
      if (url.includes('/stats')) return Promise.resolve({ data: mockStats })
      return Promise.resolve({ data: { devices: weirdDevices, pages: 1 } })
    })
    render(<Devices />)
    await waitFor(() => expect(screen.getByText('Unknown')).toBeInTheDocument())
  })

  it('shows client version when provided', async () => {
    render(<Devices />)
    await waitFor(() => expect(screen.getByText('v1.0.0')).toBeInTheDocument())
  })
})
