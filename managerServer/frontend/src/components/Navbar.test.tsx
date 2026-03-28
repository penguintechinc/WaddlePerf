import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import Navbar from './Navbar'
import * as AuthContextModule from '../contexts/AuthContext'
import * as ThemeContextModule from '../contexts/ThemeContext'

const mockNavigate = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

vi.mock('../contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}))

vi.mock('../contexts/ThemeContext', () => ({
  useTheme: vi.fn(),
}))

const mockUseAuth = vi.mocked(AuthContextModule.useAuth)
const mockUseTheme = vi.mocked(ThemeContextModule.useTheme)

const mockAdminUser = {
  id: 1,
  username: 'adminuser',
  email: 'admin@test.com',
  role: 'global_admin',
  ou_id: null,
  mfa_enabled: false,
  is_active: true,
  created_at: '',
  updated_at: '',
}

const mockRegularUser = {
  ...mockAdminUser,
  username: 'regularuser',
  role: 'user',
}

const mockSetTheme = vi.fn()

function renderNavbar() {
  return render(
    <MemoryRouter>
      <Navbar />
    </MemoryRouter>
  )
}

describe('Navbar component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseAuth.mockReturnValue({ user: mockAdminUser, logout: vi.fn() } as any)
    mockUseTheme.mockReturnValue({ theme: 'auto', setTheme: mockSetTheme } as any)
  })

  it('renders the navbar brand link', () => {
    renderNavbar()
    expect(screen.getByText('WaddlePerf Manager')).toBeInTheDocument()
  })

  it('renders Dashboard link', () => {
    renderNavbar()
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
  })

  it('renders Devices link', () => {
    renderNavbar()
    expect(screen.getByText('Devices')).toBeInTheDocument()
  })

  it('renders Statistics link', () => {
    renderNavbar()
    expect(screen.getByText('Statistics')).toBeInTheDocument()
  })

  it('renders Profile link', () => {
    renderNavbar()
    expect(screen.getByText('Profile')).toBeInTheDocument()
  })

  it('shows Users link for admin users', () => {
    renderNavbar()
    expect(screen.getByText('Users')).toBeInTheDocument()
  })

  it('shows Organizations link for admin users', () => {
    renderNavbar()
    expect(screen.getByText('Organizations')).toBeInTheDocument()
  })

  it('hides Users link for non-admin users', () => {
    mockUseAuth.mockReturnValue({ user: mockRegularUser, logout: vi.fn() } as any)
    renderNavbar()
    expect(screen.queryByText('Users')).not.toBeInTheDocument()
  })

  it('hides Organizations link for non-admin users', () => {
    mockUseAuth.mockReturnValue({ user: mockRegularUser, logout: vi.fn() } as any)
    renderNavbar()
    expect(screen.queryByText('Organizations')).not.toBeInTheDocument()
  })

  it('shows ou_admin as an admin user (Users visible)', () => {
    mockUseAuth.mockReturnValue({ user: { ...mockAdminUser, role: 'ou_admin' }, logout: vi.fn() } as any)
    renderNavbar()
    expect(screen.getByText('Users')).toBeInTheDocument()
  })

  it('displays the current username', () => {
    renderNavbar()
    expect(screen.getByText('adminuser')).toBeInTheDocument()
  })

  it('shows Logout button', () => {
    renderNavbar()
    expect(screen.getByText('Logout')).toBeInTheDocument()
  })

  it('calls logout and navigates to /login when Logout is clicked', async () => {
    const mockLogout = vi.fn().mockResolvedValue(undefined)
    mockUseAuth.mockReturnValue({ user: mockAdminUser, logout: mockLogout } as any)
    mockNavigate.mockClear()
    renderNavbar()
    const logoutBtn = screen.getByText('Logout')
    fireEvent.click(logoutBtn)
    await Promise.resolve()
    await Promise.resolve()
    expect(mockLogout).toHaveBeenCalledOnce()
    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/login'))
  })

  it('shows theme toggle button', () => {
    renderNavbar()
    const themeBtn = screen.getByTitle(/Theme: auto/i)
    expect(themeBtn).toBeInTheDocument()
  })

  it('cycles theme when theme toggle is clicked', () => {
    renderNavbar()
    const themeBtn = screen.getByTitle(/Theme: auto/i)
    fireEvent.click(themeBtn)
    expect(mockSetTheme).toHaveBeenCalledWith('light')
  })

  it('shows correct icon for auto theme (🔄)', () => {
    renderNavbar()
    const themeBtn = screen.getByTitle(/Theme: auto/i)
    expect(themeBtn.textContent).toContain('🔄')
  })

  it('shows correct icon for light theme (☀️)', () => {
    mockUseTheme.mockReturnValue({ theme: 'light', setTheme: mockSetTheme } as any)
    renderNavbar()
    const themeBtn = screen.getByTitle(/Theme: light/i)
    expect(themeBtn.textContent).toContain('☀️')
  })

  it('shows correct icon for dark theme (🌙)', () => {
    mockUseTheme.mockReturnValue({ theme: 'dark', setTheme: mockSetTheme } as any)
    renderNavbar()
    const themeBtn = screen.getByTitle(/Theme: dark/i)
    expect(themeBtn.textContent).toContain('🌙')
  })
})
