import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import Login from './Login'

const mockNavigate = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

vi.mock('../contexts/AuthContext', () => ({
  useAuth: vi.fn().mockReturnValue({
    login: vi.fn(),
  }),
}))

vi.mock('@penguintechinc/react-libs', () => ({
  LoginPageBuilder: vi.fn(({ branding, onSuccess, onError, mfa, showForgotPassword }) => (
    <div data-testid="login-page-builder">
      <div data-testid="app-name">{branding?.appName}</div>
      <div data-testid="tagline">{branding?.tagline}</div>
      <div data-testid="mfa-enabled">{String(mfa?.enabled)}</div>
      <div data-testid="forgot-password">{String(showForgotPassword)}</div>
      <button
        data-testid="success-btn"
        onClick={() => onSuccess({ token: 'test-token', user: { id: 1, username: 'admin' } })}
      >
        Success
      </button>
      <button data-testid="error-btn" onClick={() => onError('Bad credentials')}>
        Error
      </button>
    </div>
  )),
}))

describe('Login page (managerServer)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  function renderLogin() {
    return render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>
    )
  }

  it('renders the LoginPageBuilder component', () => {
    renderLogin()
    expect(screen.getByTestId('login-page-builder')).toBeInTheDocument()
  })

  it('passes WaddlePerf Manager as app name', () => {
    renderLogin()
    expect(screen.getByTestId('app-name')).toHaveTextContent('WaddlePerf Manager')
  })

  it('passes correct tagline', () => {
    renderLogin()
    expect(screen.getByTestId('tagline')).toHaveTextContent('Network Performance Management')
  })

  it('enables MFA in props', () => {
    renderLogin()
    expect(screen.getByTestId('mfa-enabled')).toHaveTextContent('true')
  })

  it('shows forgot password link', () => {
    renderLogin()
    expect(screen.getByTestId('forgot-password')).toHaveTextContent('true')
  })

  it('stores auth_token in localStorage on success', () => {
    renderLogin()
    fireEvent.click(screen.getByTestId('success-btn'))
    expect(localStorage.getItem('auth_token')).toBe('test-token')
  })

  it('stores user in localStorage on success', () => {
    renderLogin()
    fireEvent.click(screen.getByTestId('success-btn'))
    const storedUser = JSON.parse(localStorage.getItem('user') || '{}')
    expect(storedUser.username).toBe('admin')
  })

  it('navigates to /dashboard on successful login', () => {
    renderLogin()
    fireEvent.click(screen.getByTestId('success-btn'))
    expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
  })

  it('logs error on login failure', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    renderLogin()
    fireEvent.click(screen.getByTestId('error-btn'))
    expect(consoleSpy).toHaveBeenCalledWith('Login failed:', 'Bad credentials')
    consoleSpy.mockRestore()
  })
})
