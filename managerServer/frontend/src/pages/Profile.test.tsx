import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import Profile from './Profile'
import * as AuthContextModule from '../contexts/AuthContext'
import { api } from '../services/api'

vi.mock('../contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}))

const mockUseAuth = vi.mocked(AuthContextModule.useAuth)

vi.mock('../services/api', () => ({
  api: {
    getUser: vi.fn(),
    setupMfa: vi.fn(),
    verifyMfa: vi.fn(),
    changeUserPassword: vi.fn(),
  },
}))

vi.mock('qrcode.react', () => ({
  QRCodeSVG: vi.fn(({ value }) => <div data-testid="qr-code" data-value={value} />),
}))

const mockAuthUser = {
  id: 1,
  username: 'testuser',
  email: 'test@test.com',
  role: 'user',
  ou_id: null,
  mfa_enabled: false,
  is_active: true,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  api_key: 'test-api-key-123',
}

describe('Profile page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseAuth.mockReturnValue({ user: mockAuthUser } as any)
    api.getUser.mockResolvedValue(mockAuthUser)
  })

  it('shows loading spinner initially', () => {
    api.getUser.mockImplementation(() => new Promise(() => {}))
    render(<Profile />)
    expect(document.querySelector('.spinner')).toBeInTheDocument()
  })

  it('renders User Profile heading after loading', async () => {
    render(<Profile />)
    await waitFor(() => expect(screen.getByText('User Profile')).toBeInTheDocument())
  })

  it('shows Account Information section', async () => {
    render(<Profile />)
    await waitFor(() => expect(screen.getByText('Account Information')).toBeInTheDocument())
  })

  it('shows username in profile info', async () => {
    render(<Profile />)
    await waitFor(() => expect(screen.getByText('testuser')).toBeInTheDocument())
  })

  it('shows email in profile info', async () => {
    render(<Profile />)
    await waitFor(() => expect(screen.getByText('test@test.com')).toBeInTheDocument())
  })

  it('shows API key section with key value', async () => {
    render(<Profile />)
    await waitFor(() => {
      expect(screen.getByText('API Key')).toBeInTheDocument()
      expect(screen.getByText('test-api-key-123')).toBeInTheDocument()
    })
  })

  it('shows API key not available when no api_key', async () => {
    api.getUser.mockResolvedValue({ ...mockAuthUser, api_key: undefined })
    render(<Profile />)
    await waitFor(() => expect(screen.getByText(/API key not available/)).toBeInTheDocument())
  })

  it('shows Security Settings section', async () => {
    render(<Profile />)
    await waitFor(() => expect(screen.getByText('Security Settings')).toBeInTheDocument())
  })

  it('shows Enable MFA button when MFA is disabled', async () => {
    render(<Profile />)
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Enable MFA/i })).toBeInTheDocument()
    })
  })

  it('hides Enable MFA button when MFA is already enabled', async () => {
    api.getUser.mockResolvedValue({ ...mockAuthUser, mfa_enabled: true })
    render(<Profile />)
    await waitFor(() => expect(screen.queryByText('Enable MFA')).not.toBeInTheDocument())
  })

  it('shows Change Password button', async () => {
    render(<Profile />)
    await waitFor(() => expect(screen.getByText('Change Password')).toBeInTheDocument())
  })

  it('shows password form when Change Password is clicked', async () => {
    render(<Profile />)
    await waitFor(() => screen.getByText('Change Password'))
    fireEvent.click(screen.getByText('Change Password'))
    expect(screen.getByLabelText('New Password')).toBeInTheDocument()
    expect(screen.getByLabelText('Confirm Password')).toBeInTheDocument()
  })

  it('shows password mismatch error', async () => {
    const user = userEvent.setup()
    render(<Profile />)
    await waitFor(() => screen.getByText('Change Password'))
    fireEvent.click(screen.getByText('Change Password'))
    await user.type(screen.getByLabelText('New Password'), 'password123')
    await user.type(screen.getByLabelText('Confirm Password'), 'different456')
    fireEvent.click(screen.getByText('Update Password'))
    await waitFor(() => expect(screen.getByText('Passwords do not match')).toBeInTheDocument())
  })

  it('shows error for password shorter than 8 chars', async () => {
    const user = userEvent.setup()
    render(<Profile />)
    await waitFor(() => screen.getByText('Change Password'))
    fireEvent.click(screen.getByText('Change Password'))
    await user.type(screen.getByLabelText('New Password'), 'short')
    await user.type(screen.getByLabelText('Confirm Password'), 'short')
    fireEvent.click(screen.getByText('Update Password'))
    await waitFor(() => expect(screen.getByText('Password must be at least 8 characters')).toBeInTheDocument())
  })

  it('successfully changes password', async () => {
    const user = userEvent.setup()
    api.changeUserPassword.mockResolvedValue({ success: true, message: 'Password changed' })
    render(<Profile />)
    await waitFor(() => screen.getByText('Change Password'))
    fireEvent.click(screen.getByText('Change Password'))
    await user.type(screen.getByLabelText('New Password'), 'newpassword123')
    await user.type(screen.getByLabelText('Confirm Password'), 'newpassword123')
    fireEvent.click(screen.getByText('Update Password'))
    await waitFor(() => expect(screen.getByText('Password changed successfully!')).toBeInTheDocument())
  })

  it('shows MFA setup UI when Enable MFA is clicked', async () => {
    api.setupMfa.mockResolvedValue({ secret: 'MYSECRET', qr_uri: 'otpauth://...' })
    render(<Profile />)
    await waitFor(() => screen.getByText('Enable MFA'))
    fireEvent.click(screen.getByText('Enable MFA'))
    await waitFor(() => {
      expect(screen.getByText('Setup Multi-Factor Authentication')).toBeInTheDocument()
      expect(screen.getByTestId('qr-code')).toBeInTheDocument()
    })
  })

  it('shows the MFA secret after setup', async () => {
    api.setupMfa.mockResolvedValue({ secret: 'MYSECRET', qr_uri: 'otpauth://...' })
    render(<Profile />)
    await waitFor(() => screen.getByText('Enable MFA'))
    fireEvent.click(screen.getByText('Enable MFA'))
    await waitFor(() => expect(screen.getByText('MYSECRET')).toBeInTheDocument())
  })

  it('verifies MFA code and shows success', async () => {
    const user = userEvent.setup()
    api.setupMfa.mockResolvedValue({ secret: 'MYSECRET', qr_uri: 'otpauth://...' })
    api.verifyMfa.mockResolvedValue({ message: 'MFA enabled' })
    // Don't set mfa_enabled: true initially - it hides the button. After verification, it should be true.
    api.getUser.mockResolvedValueOnce(mockAuthUser) // Initial load shows button
    api.getUser.mockResolvedValueOnce({ ...mockAuthUser, mfa_enabled: true }) // After verification, MFA is enabled
    render(<Profile />)
    await waitFor(() => screen.getByRole('button', { name: /Enable MFA/i }))
    fireEvent.click(screen.getByRole('button', { name: /Enable MFA/i }))
    await waitFor(() => screen.getByLabelText(/Enter verification code/i))
    await user.type(screen.getByLabelText(/Enter verification code/i), '123456')
    fireEvent.click(screen.getByText('Verify and Enable'))
    await waitFor(() => expect(screen.getByText('MFA enabled successfully!')).toBeInTheDocument())
  })

  it('shows error message when API fails to load profile', async () => {
    api.getUser.mockRejectedValue({ response: { data: { error: 'Load failed' } } })
    render(<Profile />)
    await waitFor(() => {
      const errorContainer = document.querySelector('.error-message')
      expect(errorContainer).toBeInTheDocument()
    })
  })

  it('copies API key to clipboard when Copy is clicked', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined)
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText },
      configurable: true,
    })
    render(<Profile />)
    await waitFor(() => screen.getByText('test-api-key-123'))
    const copyButtons = screen.getAllByText('Copy')
    fireEvent.click(copyButtons[0])
    await waitFor(() => expect(writeText).toHaveBeenCalledWith('test-api-key-123'))
  })
})
