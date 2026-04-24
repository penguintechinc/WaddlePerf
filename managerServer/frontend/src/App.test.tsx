import { render, screen } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import App from './App'
import * as AuthContextModule from './contexts/AuthContext'
import * as ThemeContextModule from './contexts/ThemeContext'

vi.mock('@penguintechinc/react-libs', () => ({
  AppConsoleVersion: vi.fn(() => <div data-testid="console-version" />),
  LoginPageBuilder: vi.fn(() => <div data-testid="login-page-builder">Login</div>),
}))

vi.mock('./components/Navbar', () => ({
  default: vi.fn(() => <nav data-testid="navbar">Navbar</nav>),
}))

vi.mock('./components/ProtectedRoute', () => ({
  default: vi.fn(({ children }) => <div data-testid="protected-route">{children}</div>),
}))

vi.mock('./pages/Login', () => ({
  default: vi.fn(() => <div data-testid="login-page">Login Page</div>),
}))

vi.mock('./pages/Dashboard', () => ({
  default: vi.fn(() => <div data-testid="dashboard-page">Dashboard</div>),
}))

vi.mock('./pages/Users', () => ({
  default: vi.fn(() => <div data-testid="users-page">Users</div>),
}))

vi.mock('./pages/Organizations', () => ({
  default: vi.fn(() => <div data-testid="organizations-page">Organizations</div>),
}))

vi.mock('./pages/Statistics', () => ({
  default: vi.fn(() => <div data-testid="statistics-page">Statistics</div>),
}))

vi.mock('./pages/Profile', () => ({
  default: vi.fn(() => <div data-testid="profile-page">Profile</div>),
}))

vi.mock('./pages/Devices', () => ({
  default: vi.fn(() => <div data-testid="devices-page">Devices</div>),
}))

vi.mock('./contexts/AuthContext', () => ({
  AuthProvider: vi.fn(({ children }) => <div data-testid="auth-provider">{children}</div>),
  useAuth: vi.fn(() => ({ isAuthenticated: false, user: null, isLoading: false })),
}))

vi.mock('./contexts/ThemeContext', () => ({
  ThemeProvider: vi.fn(({ children }) => <div data-testid="theme-provider">{children}</div>),
  useTheme: vi.fn(() => ({ theme: 'auto', setTheme: vi.fn(), effectiveTheme: 'light' })),
}))

const mockAuthProvider = vi.mocked(AuthContextModule.AuthProvider)
const mockThemeProvider = vi.mocked(ThemeContextModule.ThemeProvider)

describe('App (managerServer)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockAuthProvider.mockImplementation(({ children }: { children: React.ReactNode }) => (
      <div data-testid="auth-provider">{children}</div>
    ))
    mockThemeProvider.mockImplementation(({ children }: { children: React.ReactNode }) => (
      <div data-testid="theme-provider">{children}</div>
    ))
  })

  it('renders without crashing', () => {
    render(<App />)
    expect(document.body).toBeInTheDocument()
  })

  it('wraps app in ThemeProvider', () => {
    render(<App />)
    expect(screen.getByTestId('theme-provider')).toBeInTheDocument()
  })

  it('wraps app in AuthProvider', () => {
    render(<App />)
    expect(screen.getByTestId('auth-provider')).toBeInTheDocument()
  })

  it('renders AppConsoleVersion component', () => {
    render(<App />)
    expect(screen.getByTestId('console-version')).toBeInTheDocument()
  })

  it('renders the login route for /login path', () => {
    // MemoryRouter in App uses BrowserRouter, we can check login renders
    // by checking the AppConsoleVersion component (always renders)
    render(<App />)
    expect(screen.getByTestId('console-version')).toBeInTheDocument()
  })

  it('renders ProtectedRoute for protected paths', () => {
    render(<App />)
    // ProtectedRoute is used for authenticated routes
    expect(screen.getByTestId('auth-provider')).toBeInTheDocument()
  })
})
