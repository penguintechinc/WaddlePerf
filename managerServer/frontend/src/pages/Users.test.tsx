import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import Users from './Users'
import { api } from '../services/api'

vi.mock('../services/api', () => ({
  api: {
    listUsers: vi.fn(),
    listOrganizations: vi.fn(),
    createUser: vi.fn(),
    updateUser: vi.fn(),
    deleteUser: vi.fn(),
  },
}))

// Mock window.confirm
global.confirm = vi.fn()

const mockUsers = [
  { id: 1, username: 'admin', email: 'admin@test.com', role: 'global_admin', ou_id: null, mfa_enabled: true, is_active: true, created_at: '', updated_at: '' },
  { id: 2, username: 'viewer', email: 'viewer@test.com', role: 'user', ou_id: 1, mfa_enabled: false, is_active: false, created_at: '', updated_at: '' },
]

const mockOrgs = [
  { id: 1, name: 'Org A', created_at: '', updated_at: '' },
]

describe('Users page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    api.listUsers.mockResolvedValue({ users: mockUsers, total: 2, page: 1, per_page: 50 })
    api.listOrganizations.mockResolvedValue({ organizations: mockOrgs })
  })

  it('shows loading spinner initially', () => {
    api.listUsers.mockImplementation(() => new Promise(() => {}))
    render(<Users />)
    expect(document.querySelector('.spinner')).toBeInTheDocument()
  })

  it('renders the User Management heading', async () => {
    render(<Users />)
    await waitFor(() => expect(screen.getByText('User Management')).toBeInTheDocument())
  })

  it('shows Create User button', async () => {
    render(<Users />)
    await waitFor(() => expect(screen.getByText('Create User')).toBeInTheDocument())
  })

  it('renders user table with headers', async () => {
    render(<Users />)
    await waitFor(() => {
      expect(screen.getByText('Username')).toBeInTheDocument()
      expect(screen.getByText('Email')).toBeInTheDocument()
      expect(screen.getByText('Role')).toBeInTheDocument()
      expect(screen.getByText('MFA')).toBeInTheDocument()
      expect(screen.getByText('Status')).toBeInTheDocument()
    })
  })

  it('shows user data in table', async () => {
    render(<Users />)
    await waitFor(() => {
      expect(screen.getByText('admin')).toBeInTheDocument()
      expect(screen.getByText('viewer')).toBeInTheDocument()
      expect(screen.getByText('admin@test.com')).toBeInTheDocument()
    })
  })

  it('shows MFA Enabled/Disabled for each user', async () => {
    render(<Users />)
    await waitFor(() => {
      expect(screen.getByText('Enabled')).toBeInTheDocument()
      expect(screen.getByText('Disabled')).toBeInTheDocument()
    })
  })

  it('shows Active/Inactive status badges', async () => {
    render(<Users />)
    await waitFor(() => {
      expect(screen.getByText('Active')).toBeInTheDocument()
      expect(screen.getByText('Inactive')).toBeInTheDocument()
    })
  })

  it('opens create user modal when Create User is clicked', async () => {
    render(<Users />)
    await waitFor(() => screen.getByText('Create User'))
    fireEvent.click(screen.getByText('Create User'))
    expect(screen.getByText('Create New User')).toBeInTheDocument()
  })

  it('closes create modal when Cancel is clicked', async () => {
    render(<Users />)
    await waitFor(() => screen.getByText('Create User'))
    fireEvent.click(screen.getByText('Create User'))
    fireEvent.click(screen.getByText('Cancel'))
    expect(screen.queryByText('Create New User')).not.toBeInTheDocument()
  })

  it('creates a user when form is submitted', async () => {
    const user = userEvent.setup()
    api.createUser.mockResolvedValue({ id: 3, username: 'newuser', email: 'new@test.com', role: 'user', ou_id: null, mfa_enabled: false, is_active: true, created_at: '', updated_at: '' })
    render(<Users />)
    await waitFor(() => screen.getByText('Create User'))
    fireEvent.click(screen.getByText('Create User'))
    await user.type(screen.getByLabelText('Username'), 'newuser')
    await user.type(screen.getByLabelText('Email'), 'new@test.com')
    await user.type(screen.getByLabelText('Password'), 'password123')
    fireEvent.click(screen.getByText('Create'))
    await waitFor(() => expect(api.createUser).toHaveBeenCalled())
  })

  it('opens edit modal when Edit button is clicked', async () => {
    render(<Users />)
    await waitFor(() => screen.getAllByText('Edit').length > 0)
    const editButtons = screen.getAllByText('Edit')
    fireEvent.click(editButtons[0])
    expect(screen.getByText(/Edit User:/)).toBeInTheDocument()
  })

  it('deletes user when Delete is confirmed', async () => {
    api.deleteUser.mockResolvedValue({ message: 'Deleted' })
    ;(global.confirm as ReturnType<typeof vi.fn>).mockReturnValue(true)
    render(<Users />)
    await waitFor(() => screen.getAllByText('Delete').length > 0)
    const deleteButtons = screen.getAllByText('Delete')
    fireEvent.click(deleteButtons[0])
    await waitFor(() => expect(api.deleteUser).toHaveBeenCalled())
  })

  it('does not delete user when delete is cancelled', async () => {
    ;(global.confirm as ReturnType<typeof vi.fn>).mockReturnValue(false)
    render(<Users />)
    await waitFor(() => screen.getAllByText('Delete').length > 0)
    const deleteButtons = screen.getAllByText('Delete')
    fireEvent.click(deleteButtons[0])
    expect(api.deleteUser).not.toHaveBeenCalled()
  })

  it('shows error message when loading users fails', async () => {
    api.listUsers.mockRejectedValue({ response: { data: { error: 'Load failed' } } })
    render(<Users />)
    await waitFor(() => expect(screen.getByText('Load failed')).toBeInTheDocument())
  })

  it('shows organization name for user with ou_id', async () => {
    render(<Users />)
    await waitFor(() => expect(screen.getByText('Org A')).toBeInTheDocument())
  })

  it('shows N/A for user with no organization', async () => {
    render(<Users />)
    await waitFor(() => expect(screen.getAllByText('N/A').length).toBeGreaterThan(0))
  })

  it('shows pagination controls', async () => {
    render(<Users />)
    await waitFor(() => {
      expect(screen.getByText('Previous')).toBeInTheDocument()
      expect(screen.getByText('Next')).toBeInTheDocument()
    })
  })
})
