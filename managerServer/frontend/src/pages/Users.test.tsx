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

  it('shows error when create user fails', async () => {
    const user = userEvent.setup()
    api.createUser.mockRejectedValue({ response: { data: { error: 'Username already exists' } } })
    render(<Users />)
    await waitFor(() => screen.getByText('Create User'))
    fireEvent.click(screen.getByText('Create User'))
    await user.type(screen.getByLabelText('Username'), 'dupuser')
    await user.type(screen.getByLabelText('Email'), 'dup@test.com')
    await user.type(screen.getByLabelText('Password'), 'password123')
    fireEvent.click(screen.getByText('Create'))
    await waitFor(() => expect(screen.getByText('Username already exists')).toBeInTheDocument())
  })

  it('edits user when edit form is submitted successfully', async () => {
    const user = userEvent.setup()
    api.updateUser.mockResolvedValue({ message: 'Updated' })
    render(<Users />)
    await waitFor(() => screen.getAllByText('Edit').length > 0)
    const editButtons = screen.getAllByText('Edit')
    fireEvent.click(editButtons[0])
    expect(screen.getByText(/Edit User:/)).toBeInTheDocument()
    const emailInput = screen.getByLabelText('Email')
    await user.clear(emailInput)
    await user.type(emailInput, 'updated@test.com')
    fireEvent.click(screen.getByText('Update'))
    await waitFor(() => expect(api.updateUser).toHaveBeenCalled())
  })

  it('shows error when edit user fails', async () => {
    const user = userEvent.setup()
    api.updateUser.mockRejectedValue({ response: { data: { error: 'Update failed' } } })
    render(<Users />)
    await waitFor(() => screen.getAllByText('Edit').length > 0)
    const editButtons = screen.getAllByText('Edit')
    fireEvent.click(editButtons[0])
    fireEvent.click(screen.getByText('Update'))
    await waitFor(() => expect(screen.getByText('Update failed')).toBeInTheDocument())
  })

  it('shows error when delete user fails', async () => {
    api.deleteUser.mockRejectedValue({ response: { data: { error: 'Cannot delete admin' } } })
    ;(global.confirm as ReturnType<typeof vi.fn>).mockReturnValue(true)
    render(<Users />)
    await waitFor(() => screen.getAllByText('Delete').length > 0)
    const deleteButtons = screen.getAllByText('Delete')
    fireEvent.click(deleteButtons[0])
    await waitFor(() => expect(screen.getByText('Cannot delete admin')).toBeInTheDocument())
  })

  it('resets form when create modal is submitted and closed', async () => {
    const user = userEvent.setup()
    api.createUser.mockResolvedValue({ id: 99, username: 'newguy', email: 'new@test.com', role: 'user', ou_id: null, mfa_enabled: false, is_active: true, created_at: '', updated_at: '' })
    render(<Users />)
    await waitFor(() => screen.getByText('Create User'))
    fireEvent.click(screen.getByText('Create User'))
    await user.type(screen.getByLabelText('Username'), 'newguy')
    await user.type(screen.getByLabelText('Email'), 'new@test.com')
    await user.type(screen.getByLabelText('Password'), 'password123')
    fireEvent.click(screen.getByText('Create'))
    await waitFor(() => expect(api.createUser).toHaveBeenCalled())
    // Modal should close after successful create
    await waitFor(() => expect(screen.queryByText('Create New User')).not.toBeInTheDocument())
  })

  it('shows N/A org name for user with unknown ou_id', async () => {
    // ou_id 99 has no matching org
    const usersWithUnknownOrg = [{ ...mockUsers[1], ou_id: 99 }]
    api.listUsers.mockResolvedValue({ users: usersWithUnknownOrg, total: 1, page: 1, per_page: 50 })
    render(<Users />)
    // The org lookup falls back to displaying the ou_id number
    await waitFor(() => expect(screen.getByText('99')).toBeInTheDocument())
  })

  it('navigates to next page when Next is clicked', async () => {
    // Return 50 users so Next button is enabled
    const fiftyUsers = Array.from({ length: 50 }, (_, i) => ({
      id: i + 1,
      username: `user${i}`,
      email: `user${i}@test.com`,
      role: 'user',
      ou_id: null,
      mfa_enabled: false,
      is_active: true,
      created_at: '',
      updated_at: '',
    }))
    api.listUsers.mockResolvedValue({ users: fiftyUsers, total: 100, page: 1, per_page: 50 })
    render(<Users />)
    await waitFor(() => expect(screen.getByText('Next')).not.toBeDisabled())
    fireEvent.click(screen.getByText('Next'))
    await waitFor(() => expect(api.listUsers).toHaveBeenCalledWith(2, 50))
  })

  it('navigates to previous page when Previous is clicked after going to page 2', async () => {
    const fiftyUsers = Array.from({ length: 50 }, (_, i) => ({
      id: i + 1,
      username: `user${i}`,
      email: `user${i}@test.com`,
      role: 'user',
      ou_id: null,
      mfa_enabled: false,
      is_active: true,
      created_at: '',
      updated_at: '',
    }))
    api.listUsers.mockResolvedValue({ users: fiftyUsers, total: 100, page: 1, per_page: 50 })
    render(<Users />)
    await waitFor(() => expect(screen.getByText('Next')).not.toBeDisabled())
    fireEvent.click(screen.getByText('Next'))
    await waitFor(() => expect(api.listUsers).toHaveBeenCalledWith(2, 50))
    await waitFor(() => expect(screen.getByText('Previous')).not.toBeDisabled())
    fireEvent.click(screen.getByText('Previous'))
    await waitFor(() => expect(api.listUsers).toHaveBeenCalledWith(1, 50))
  })

  it('closes edit modal when Cancel is clicked', async () => {
    render(<Users />)
    await waitFor(() => screen.getAllByText('Edit').length > 0)
    fireEvent.click(screen.getAllByText('Edit')[0])
    expect(screen.getByText(/Edit User:/)).toBeInTheDocument()
    // Find Cancel button in the modal
    const cancelButtons = screen.getAllByText('Cancel')
    fireEvent.click(cancelButtons[0])
    expect(screen.queryByText(/Edit User:/)).not.toBeInTheDocument()
  })

  it('handles organization loading failure gracefully', async () => {
    api.listOrganizations.mockRejectedValue({ error: 'Failed to load orgs' })
    render(<Users />)
    await waitFor(() => expect(screen.getByText('User Management')).toBeInTheDocument())
    // Should still render successfully even if orgs fail to load
    expect(screen.getByText('Create User')).toBeInTheDocument()
  })

  it('changes organization when select value is updated in create form', async () => {
    const user = userEvent.setup()
    api.createUser.mockResolvedValue({ id: 3, username: 'newuser', email: 'new@test.com', role: 'user', ou_id: 1, mfa_enabled: false, is_active: true, created_at: '', updated_at: '' })
    render(<Users />)
    await waitFor(() => screen.getByText('Create User'))
    fireEvent.click(screen.getByText('Create User'))
    const ouSelect = screen.getByLabelText('Organization (Optional)')
    await user.selectOptions(ouSelect, '1')
    expect((ouSelect as HTMLSelectElement).value).toBe('1')
  })

  it('changes organization when select value is updated in edit form', async () => {
    const user = userEvent.setup()
    api.updateUser.mockResolvedValue({ message: 'Updated' })
    render(<Users />)
    await waitFor(() => screen.getAllByText('Edit').length > 0)
    const editButtons = screen.getAllByText('Edit')
    fireEvent.click(editButtons[0])
    await waitFor(() => screen.getByText(/Edit User:/))
    const ouSelect = screen.getByLabelText('Organization')
    await user.selectOptions(ouSelect, '1')
    expect((ouSelect as HTMLSelectElement).value).toBe('1')
  })

  it('toggles active status checkbox in edit form', async () => {
    const user = userEvent.setup()
    api.updateUser.mockResolvedValue({ message: 'Updated' })
    render(<Users />)
    await waitFor(() => screen.getAllByText('Edit').length > 0)
    const editButtons = screen.getAllByText('Edit')
    fireEvent.click(editButtons[0])
    await waitFor(() => screen.getByText(/Edit User:/))
    const activeCheckbox = screen.getByRole('checkbox', { name: 'Active' })
    expect((activeCheckbox as HTMLInputElement).checked).toBe(true)
    await user.click(activeCheckbox)
    expect((activeCheckbox as HTMLInputElement).checked).toBe(false)
  })

  it('closes create modal when overlay is clicked', async () => {
    render(<Users />)
    await waitFor(() => screen.getByText('Create User'))
    fireEvent.click(screen.getByText('Create User'))
    expect(screen.getByText('Create New User')).toBeInTheDocument()
    // Click the modal overlay
    const modalOverlay = document.querySelector('.modal-overlay') as HTMLElement
    fireEvent.click(modalOverlay)
    expect(screen.queryByText('Create New User')).not.toBeInTheDocument()
  })

  it('does not close create modal when modal content is clicked', async () => {
    render(<Users />)
    await waitFor(() => screen.getByText('Create User'))
    fireEvent.click(screen.getByText('Create User'))
    expect(screen.getByText('Create New User')).toBeInTheDocument()
    // Click inside the modal (not the overlay)
    const modal = document.querySelector('.modal') as HTMLElement
    fireEvent.click(modal)
    // Modal should still be open
    expect(screen.getByText('Create New User')).toBeInTheDocument()
  })

  it('closes edit modal when overlay is clicked', async () => {
    render(<Users />)
    await waitFor(() => screen.getAllByText('Edit').length > 0)
    fireEvent.click(screen.getAllByText('Edit')[0])
    expect(screen.getByText(/Edit User:/)).toBeInTheDocument()
    // Click the modal overlay
    const modalOverlays = document.querySelectorAll('.modal-overlay') as NodeListOf<HTMLElement>
    const editModalOverlay = Array.from(modalOverlays).find((overlay) => overlay.querySelector('.modal')?.textContent?.includes('Edit User:'))
    if (editModalOverlay) {
      fireEvent.click(editModalOverlay)
    }
    expect(screen.queryByText(/Edit User:/)).not.toBeInTheDocument()
  })

  it('selects a role from dropdown in create form', async () => {
    const user = userEvent.setup()
    render(<Users />)
    await waitFor(() => screen.getByText('Create User'))
    fireEvent.click(screen.getByText('Create User'))
    const roleSelect = screen.getByLabelText('Role')
    await user.selectOptions(roleSelect, 'global_admin')
    expect((roleSelect as HTMLSelectElement).value).toBe('global_admin')
  })

  it('selects a role from dropdown in edit form', async () => {
    const user = userEvent.setup()
    render(<Users />)
    await waitFor(() => screen.getAllByText('Edit').length > 0)
    fireEvent.click(screen.getAllByText('Edit')[0])
    await waitFor(() => screen.getByText(/Edit User:/))
    const editRoleSelect = screen.getByLabelText('Role')
    await user.selectOptions(editRoleSelect, 'ou_admin')
    expect((editRoleSelect as HTMLSelectElement).value).toBe('ou_admin')
  })
})
