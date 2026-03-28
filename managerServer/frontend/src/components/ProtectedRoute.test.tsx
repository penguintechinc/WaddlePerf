import { render, screen } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import ProtectedRoute from './ProtectedRoute'
import * as AuthContextModule from '../contexts/AuthContext'

vi.mock('../contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}))

const mockUseAuth = vi.mocked(AuthContextModule.useAuth)

function renderWithRouter(
  element: React.ReactNode,
  initialPath = '/'
) {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route path="/" element={element} />
        <Route path="/login" element={<div data-testid="login-page">Login Page</div>} />
      </Routes>
    </MemoryRouter>
  )
}

describe('ProtectedRoute component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading spinner while isLoading is true', () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: false, user: null, isLoading: true } as any)
    renderWithRouter(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    )
    expect(screen.getByText('Loading...')).toBeInTheDocument()
    expect(document.querySelector('.spinner')).toBeInTheDocument()
  })

  it('redirects to /login when not authenticated', () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: false, user: null, isLoading: false } as any)
    renderWithRouter(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    )
    expect(screen.getByTestId('login-page')).toBeInTheDocument()
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })

  it('renders children when authenticated', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      user: { id: 1, username: 'admin', email: 'a@a.com', role: 'global_admin', ou_id: null, mfa_enabled: false, is_active: true, created_at: '', updated_at: '' },
      isLoading: false,
    } as any)
    renderWithRouter(
      <ProtectedRoute>
        <div data-testid="protected-content">Protected Content</div>
      </ProtectedRoute>
    )
    expect(screen.getByTestId('protected-content')).toBeInTheDocument()
  })

  it('shows Unauthorized when requiredRole does not match user role', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      user: { id: 2, username: 'viewer', email: 'v@v.com', role: 'user', ou_id: null, mfa_enabled: false, is_active: true, created_at: '', updated_at: '' },
      isLoading: false,
    } as any)
    renderWithRouter(
      <ProtectedRoute requiredRole="ou_admin">
        <div>Admin Content</div>
      </ProtectedRoute>
    )
    expect(screen.getByText('Unauthorized')).toBeInTheDocument()
    expect(screen.queryByText('Admin Content')).not.toBeInTheDocument()
  })

  it('allows global_admin through regardless of requiredRole', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      user: { id: 1, username: 'admin', email: 'a@a.com', role: 'global_admin', ou_id: null, mfa_enabled: false, is_active: true, created_at: '', updated_at: '' },
      isLoading: false,
    } as any)
    renderWithRouter(
      <ProtectedRoute requiredRole="ou_admin">
        <div data-testid="admin-content">Admin Content</div>
      </ProtectedRoute>
    )
    expect(screen.getByTestId('admin-content')).toBeInTheDocument()
  })

  it('renders children when no requiredRole is specified and user is authenticated', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      user: { id: 3, username: 'user', email: 'u@u.com', role: 'user', ou_id: null, mfa_enabled: false, is_active: true, created_at: '', updated_at: '' },
      isLoading: false,
    } as any)
    renderWithRouter(
      <ProtectedRoute>
        <div data-testid="any-user-content">Content for any user</div>
      </ProtectedRoute>
    )
    expect(screen.getByTestId('any-user-content')).toBeInTheDocument()
  })

  it('shows Unauthorized message with description', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      user: { id: 2, username: 'viewer', email: 'v@v.com', role: 'user', ou_id: null, mfa_enabled: false, is_active: true, created_at: '', updated_at: '' },
      isLoading: false,
    } as any)
    renderWithRouter(
      <ProtectedRoute requiredRole="global_admin">
        <div>Super Admin Content</div>
      </ProtectedRoute>
    )
    expect(screen.getByText('You do not have permission to access this page.')).toBeInTheDocument()
  })
})
