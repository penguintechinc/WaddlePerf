import { render, screen, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import App from './App'

const mocks = vi.hoisted(() => ({
  checkAuthStatus: vi.fn(),
}))

vi.mock('@penguintechinc/react-libs', () => ({
  AppConsoleVersion: vi.fn(() => null),
  LoginPageBuilder: vi.fn(({ onSuccess }) => (
    <div data-testid="login-page">
      <button onClick={() => onSuccess({ user: { id: 1, username: 'admin', email: 'a@a.com', role: 'admin' } })}>
        Mock Login
      </button>
    </div>
  )),
}))

vi.mock('./components/Login', () => ({
  default: vi.fn(({ onLogin }) => (
    <div data-testid="login-component">
      <button onClick={() => onLogin({ id: 1, username: 'admin', email: 'a@a.com', role: 'admin' })}>
        Login
      </button>
    </div>
  )),
}))

vi.mock('./components/TestRunner', () => ({
  default: vi.fn(({ user, onLogout, authEnabled }) => (
    <div data-testid="test-runner">
      <span data-testid="user-name">{user?.username || 'no-user'}</span>
      <span data-testid="auth-enabled">{String(authEnabled)}</span>
      <button data-testid="logout-btn" onClick={onLogout}>Logout</button>
    </div>
  )),
}))

vi.mock('./services/api', () => ({
  checkAuthStatus: mocks.checkAuthStatus,
}))

describe('App component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading state initially', () => {
    mocks.checkAuthStatus.mockImplementation(() => new Promise(() => {})) // Never resolves
    render(<App />)
    expect(screen.getByText(/Loading WaddlePerf/i)).toBeInTheDocument()
  })

  it('shows TestRunner when auth is disabled', async () => {
    mocks.checkAuthStatus.mockResolvedValue({ authenticated: false, auth_enabled: false })
    render(<App />)
    await waitFor(() => expect(screen.getByTestId('test-runner')).toBeInTheDocument())
  })

  it('shows Login when auth is enabled and user is not authenticated', async () => {
    mocks.checkAuthStatus.mockResolvedValue({ authenticated: false, auth_enabled: true })
    render(<App />)
    await waitFor(() => expect(screen.getByTestId('login-component')).toBeInTheDocument())
  })

  it('shows TestRunner when auth is enabled and user is authenticated', async () => {
    mocks.checkAuthStatus.mockResolvedValue({
      authenticated: true,
      auth_enabled: true,
      user: { id: 1, username: 'testuser', email: 'test@test.com', role: 'admin' },
    })
    render(<App />)
    await waitFor(() => expect(screen.getByTestId('test-runner')).toBeInTheDocument())
    expect(screen.getByTestId('user-name')).toHaveTextContent('testuser')
  })

  it('passes auth_enabled=false to TestRunner when auth is disabled', async () => {
    mocks.checkAuthStatus.mockResolvedValue({ authenticated: false, auth_enabled: false })
    render(<App />)
    await waitFor(() => expect(screen.getByTestId('auth-enabled')).toHaveTextContent('false'))
  })

  it('handles checkAuthStatus API failure gracefully', async () => {
    mocks.checkAuthStatus.mockRejectedValue(new Error('Network error'))
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    render(<App />)
    await waitFor(() => expect(screen.getByTestId('login-component')).toBeInTheDocument())
    consoleSpy.mockRestore()
  })

  it('shows spinner during loading', () => {
    mocks.checkAuthStatus.mockImplementation(() => new Promise(() => {}))
    render(<App />)
    expect(document.querySelector('.spinner')).toBeInTheDocument()
  })

  it('handles logout by clearing user state', async () => {
    mocks.checkAuthStatus.mockResolvedValue({
      authenticated: true,
      auth_enabled: true,
      user: { id: 1, username: 'testuser', email: 'test@test.com', role: 'admin' },
    })
    const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {})
    render(<App />)
    await waitFor(() => expect(screen.getByTestId('test-runner')).toBeInTheDocument())

    // Click logout button
    const logoutBtn = screen.getByTestId('logout-btn')
    logoutBtn.click()

    // After logout, should redirect to login
    await waitFor(() => expect(screen.getByTestId('login-component')).toBeInTheDocument())
    consoleSpy.mockRestore()
  })

  it('redirects to / when user logs in', async () => {
    mocks.checkAuthStatus.mockResolvedValue({ authenticated: false, auth_enabled: true })
    const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {})
    render(<App />)
    await waitFor(() => expect(screen.getByTestId('login-component')).toBeInTheDocument())

    // Click login button
    const loginBtn = screen.getByRole('button', { name: /login/i })
    loginBtn.click()

    // After login, should show TestRunner
    await waitFor(() => expect(screen.getByTestId('test-runner')).toBeInTheDocument())
    consoleSpy.mockRestore()
  })

  it('renders AppConsoleVersion component', async () => {
    const { AppConsoleVersion } = await import('@penguintechinc/react-libs')
    mocks.checkAuthStatus.mockResolvedValue({ authenticated: false, auth_enabled: false })
    render(<App />)
    await waitFor(() => expect(AppConsoleVersion).toHaveBeenCalled())
  })
})
