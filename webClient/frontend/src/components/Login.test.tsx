import { render, screen } from '@testing-library/react'
import { vi, describe, it, expect } from 'vitest'
import Login from './Login'

// Use vi.hoisted so we can reference LoginPageBuilderMock in vi.mock factory
const { LoginPageBuilderMock } = vi.hoisted(() => {
  const LoginPageBuilderMock = vi.fn(({ branding, onSuccess, onError }: any) => (
    <div data-testid="login-page-builder">
      <div data-testid="app-name">{branding?.appName}</div>
      <div data-testid="tagline">{branding?.tagline}</div>
      <button
        data-testid="trigger-success"
        onClick={() => onSuccess({ user: { id: 1, username: 'testuser', email: 'test@test.com', role: 'admin' }, session_id: 'sess123' })}
      >
        Trigger Success
      </button>
      <button
        data-testid="trigger-error"
        onClick={() => onError('Login failed')}
      >
        Trigger Error
      </button>
    </div>
  ))
  return { LoginPageBuilderMock }
})

vi.mock('@penguintechinc/react-libs', () => ({
  LoginPageBuilder: LoginPageBuilderMock,
  AppConsoleVersion: vi.fn(() => null),
}))

describe('Login component', () => {
  it('renders the LoginPageBuilder component', () => {
    const mockOnLogin = vi.fn()
    render(<Login onLogin={mockOnLogin} />)
    expect(screen.getByTestId('login-page-builder')).toBeInTheDocument()
  })

  it('passes WaddlePerf as the app name to LoginPageBuilder', () => {
    const mockOnLogin = vi.fn()
    render(<Login onLogin={mockOnLogin} />)
    expect(screen.getByTestId('app-name')).toHaveTextContent('WaddlePerf')
  })

  it('passes the correct tagline to LoginPageBuilder', () => {
    const mockOnLogin = vi.fn()
    render(<Login onLogin={mockOnLogin} />)
    expect(screen.getByTestId('tagline')).toHaveTextContent('Network Performance Testing')
  })

  it('calls onLogin with user data on successful login', () => {
    const mockOnLogin = vi.fn()
    render(<Login onLogin={mockOnLogin} />)
    screen.getByTestId('trigger-success').click()
    expect(mockOnLogin).toHaveBeenCalledWith({
      id: 1,
      username: 'testuser',
      email: 'test@test.com',
      role: 'admin',
    })
  })

  it('stores session_id in sessionStorage on success', () => {
    const mockOnLogin = vi.fn()
    render(<Login onLogin={mockOnLogin} />)
    screen.getByTestId('trigger-success').click()
    expect(sessionStorage.getItem('session_id')).toBe('sess123')
  })

  it('does not call onLogin if response has no user', () => {
    // Override the mock implementation once to return a version that fires onSuccess with no user
    LoginPageBuilderMock.mockImplementationOnce(({ onSuccess }: { onSuccess: Function }) => (
      <button data-testid="no-user-success" onClick={() => onSuccess({})}>
        No User
      </button>
    ))
    const mockOnLogin = vi.fn()
    render(<Login onLogin={mockOnLogin} />)
    screen.getByTestId('no-user-success').click()
    expect(mockOnLogin).not.toHaveBeenCalled()
  })

  it('handles login error without crashing', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    const mockOnLogin = vi.fn()
    render(<Login onLogin={mockOnLogin} />)
    screen.getByTestId('trigger-error').click()
    expect(consoleSpy).toHaveBeenCalledWith('Login failed:', 'Login failed')
    consoleSpy.mockRestore()
  })
})
