import { render, screen, waitFor, act } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import { AuthProvider, useAuth } from './AuthContext'
import { api } from '../services/api'

vi.mock('../services/api', () => ({
  api: {
    login: vi.fn(),
    logout: vi.fn(),
  },
}))

// Test component that reads context values
function AuthConsumer() {
  const { user, token, isAuthenticated, isLoading, login, logout } = useAuth()
  return (
    <div>
      <span data-testid="is-loading">{String(isLoading)}</span>
      <span data-testid="is-authenticated">{String(isAuthenticated)}</span>
      <span data-testid="username">{user?.username ?? 'null'}</span>
      <span data-testid="token">{token ?? 'null'}</span>
      <button data-testid="login-btn" onClick={() => login({ username: 'admin', password: 'pass' })}>
        Login
      </button>
      <button data-testid="logout-btn" onClick={logout}>
        Logout
      </button>
    </div>
  )
}

describe('AuthContext', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('starts with loading=false after initial render', async () => {
    render(
      <AuthProvider>
        <AuthConsumer />
      </AuthProvider>
    )
    await waitFor(() => expect(screen.getByTestId('is-loading')).toHaveTextContent('false'))
  })

  it('is not authenticated initially with no stored token', async () => {
    render(
      <AuthProvider>
        <AuthConsumer />
      </AuthProvider>
    )
    await waitFor(() => expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false'))
  })

  it('restores auth state from localStorage', async () => {
    const storedUser = { id: 1, username: 'storedUser', email: 'a@a.com', role: 'global_admin', ou_id: null, mfa_enabled: false, is_active: true, created_at: '', updated_at: '' }
    localStorage.setItem('auth_token', 'stored-token')
    localStorage.setItem('user', JSON.stringify(storedUser))
    render(
      <AuthProvider>
        <AuthConsumer />
      </AuthProvider>
    )
    await waitFor(() => expect(screen.getByTestId('is-authenticated')).toHaveTextContent('true'))
    expect(screen.getByTestId('username')).toHaveTextContent('storedUser')
    expect(screen.getByTestId('token')).toHaveTextContent('stored-token')
  })

  it('performs login and updates state', async () => {
    const mockUser = { id: 2, username: 'newuser', email: 'b@b.com', role: 'user', ou_id: null, mfa_enabled: false, is_active: true, created_at: '', updated_at: '' }
    api.login.mockResolvedValue({ token: 'new-token', user: mockUser, expires_in: 3600 })

    render(
      <AuthProvider>
        <AuthConsumer />
      </AuthProvider>
    )
    await waitFor(() => expect(screen.getByTestId('is-loading')).toHaveTextContent('false'))

    await act(async () => {
      screen.getByTestId('login-btn').click()
    })

    await waitFor(() => expect(screen.getByTestId('is-authenticated')).toHaveTextContent('true'))
    expect(screen.getByTestId('username')).toHaveTextContent('newuser')
    expect(screen.getByTestId('token')).toHaveTextContent('new-token')
  })

  it('stores token and user in localStorage after login', async () => {
    const mockUser = { id: 2, username: 'newuser', email: 'b@b.com', role: 'user', ou_id: null, mfa_enabled: false, is_active: true, created_at: '', updated_at: '' }
    api.login.mockResolvedValue({ token: 'new-token', user: mockUser, expires_in: 3600 })

    render(
      <AuthProvider>
        <AuthConsumer />
      </AuthProvider>
    )
    await waitFor(() => expect(screen.getByTestId('is-loading')).toHaveTextContent('false'))

    await act(async () => {
      screen.getByTestId('login-btn').click()
    })

    await waitFor(() => expect(localStorage.getItem('auth_token')).toBe('new-token'))
    const stored = JSON.parse(localStorage.getItem('user') || '{}')
    expect(stored.username).toBe('newuser')
  })

  it('performs logout and clears state', async () => {
    api.logout.mockResolvedValue(undefined)
    localStorage.setItem('auth_token', 'token')
    localStorage.setItem('user', JSON.stringify({ id: 1, username: 'u', email: 'e@e.com', role: 'user', ou_id: null, mfa_enabled: false, is_active: true, created_at: '', updated_at: '' }))

    render(
      <AuthProvider>
        <AuthConsumer />
      </AuthProvider>
    )
    await waitFor(() => expect(screen.getByTestId('is-authenticated')).toHaveTextContent('true'))

    await act(async () => {
      screen.getByTestId('logout-btn').click()
    })

    await waitFor(() => expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false'))
    expect(localStorage.getItem('auth_token')).toBeNull()
    expect(localStorage.getItem('user')).toBeNull()
  })

  it('handles logout API failure gracefully (still clears local state)', async () => {
    api.logout.mockRejectedValue(new Error('Network error'))
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    localStorage.setItem('auth_token', 'token')
    localStorage.setItem('user', JSON.stringify({ id: 1, username: 'u', email: 'e@e.com', role: 'user', ou_id: null, mfa_enabled: false, is_active: true, created_at: '', updated_at: '' }))

    render(
      <AuthProvider>
        <AuthConsumer />
      </AuthProvider>
    )
    await waitFor(() => expect(screen.getByTestId('is-authenticated')).toHaveTextContent('true'))

    await act(async () => {
      screen.getByTestId('logout-btn').click()
    })

    await waitFor(() => expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false'))
    consoleSpy.mockRestore()
  })

  it('throws an error when useAuth is called outside AuthProvider', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    expect(() => render(<AuthConsumer />)).toThrow('useAuth must be used within an AuthProvider')
    consoleSpy.mockRestore()
  })
})
