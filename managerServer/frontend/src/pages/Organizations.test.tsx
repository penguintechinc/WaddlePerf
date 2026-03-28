import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import Organizations from './Organizations'
import { api } from '../services/api'

vi.mock('../services/api', () => ({
  api: {
    listOrganizations: vi.fn(),
    createOrganization: vi.fn(),
  },
}))

const mockOrgs = [
  { id: 1, name: 'Org Alpha', description: 'First org', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
  { id: 2, name: 'Org Beta', description: '', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
]

describe('Organizations page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading spinner initially', () => {
    api.listOrganizations.mockImplementation(() => new Promise(() => {}))
    render(<Organizations />)
    expect(document.querySelector('.spinner')).toBeInTheDocument()
  })

  it('renders the Organization Units heading', async () => {
    api.listOrganizations.mockResolvedValue({ organizations: [] })
    render(<Organizations />)
    await waitFor(() => expect(screen.getByText('Organization Units')).toBeInTheDocument())
  })

  it('shows Create Organization button', async () => {
    api.listOrganizations.mockResolvedValue({ organizations: [] })
    render(<Organizations />)
    await waitFor(() => expect(screen.getByText('Create Organization')).toBeInTheDocument())
  })

  it('renders organization cards after loading', async () => {
    api.listOrganizations.mockResolvedValue({ organizations: mockOrgs })
    render(<Organizations />)
    await waitFor(() => {
      expect(screen.getByText('Org Alpha')).toBeInTheDocument()
      expect(screen.getByText('Org Beta')).toBeInTheDocument()
    })
  })

  it('shows organization description', async () => {
    api.listOrganizations.mockResolvedValue({ organizations: mockOrgs })
    render(<Organizations />)
    await waitFor(() => expect(screen.getByText('First org')).toBeInTheDocument())
  })

  it('shows "No description" for orgs with empty description', async () => {
    api.listOrganizations.mockResolvedValue({ organizations: mockOrgs })
    render(<Organizations />)
    await waitFor(() => expect(screen.getByText('No description')).toBeInTheDocument())
  })

  it('shows "No organizations found" when list is empty', async () => {
    api.listOrganizations.mockResolvedValue({ organizations: [] })
    render(<Organizations />)
    await waitFor(() => expect(screen.getByText(/No organizations found/)).toBeInTheDocument())
  })

  it('opens create modal when Create Organization is clicked', async () => {
    api.listOrganizations.mockResolvedValue({ organizations: [] })
    render(<Organizations />)
    await waitFor(() => screen.getByText('Create Organization'))
    fireEvent.click(screen.getByText('Create Organization'))
    expect(screen.getByText('Create New Organization')).toBeInTheDocument()
  })

  it('closes modal when Cancel is clicked', async () => {
    api.listOrganizations.mockResolvedValue({ organizations: [] })
    render(<Organizations />)
    await waitFor(() => screen.getByText('Create Organization'))
    fireEvent.click(screen.getByText('Create Organization'))
    expect(screen.getByText('Create New Organization')).toBeInTheDocument()
    fireEvent.click(screen.getByText('Cancel'))
    expect(screen.queryByText('Create New Organization')).not.toBeInTheDocument()
  })

  it('creates organization and refreshes list on form submit', async () => {
    const user = userEvent.setup()
    api.listOrganizations.mockResolvedValue({ organizations: [] })
    api.createOrganization.mockResolvedValue({ id: 3, name: 'New Org', description: 'desc', created_at: '', updated_at: '' })
    render(<Organizations />)
    await waitFor(() => screen.getByText('Create Organization'))
    fireEvent.click(screen.getByText('Create Organization'))
    await user.type(screen.getByLabelText('Name'), 'New Org')
    await user.type(screen.getByLabelText('Description'), 'A description')
    fireEvent.click(screen.getByText('Create'))
    await waitFor(() => expect(api.createOrganization).toHaveBeenCalledWith({ name: 'New Org', description: 'A description' }))
  })

  it('shows error message when create fails', async () => {
    const user = userEvent.setup()
    api.listOrganizations.mockResolvedValue({ organizations: [] })
    api.createOrganization.mockRejectedValue({ response: { data: { error: 'Create failed' } } })
    render(<Organizations />)
    await waitFor(() => screen.getByText('Create Organization'))
    fireEvent.click(screen.getByText('Create Organization'))
    await user.type(screen.getByLabelText('Name'), 'Fail Org')
    fireEvent.click(screen.getByText('Create'))
    await waitFor(() => expect(screen.getByText('Create failed')).toBeInTheDocument())
  })

  it('shows error when API fails to load', async () => {    api.listOrganizations.mockRejectedValue({ response: { data: { error: 'Server error' } } })
    render(<Organizations />)
    await waitFor(() => expect(screen.getByText('Server error')).toBeInTheDocument())
  })

  it('closes modal when clicking the overlay background', async () => {    api.listOrganizations.mockResolvedValue({ organizations: [] })
    render(<Organizations />)
    await waitFor(() => screen.getByText('Create Organization'))
    fireEvent.click(screen.getByText('Create Organization'))
    const overlay = document.querySelector('.modal-overlay')!
    fireEvent.click(overlay)
    expect(screen.queryByText('Create New Organization')).not.toBeInTheDocument()
  })
})
