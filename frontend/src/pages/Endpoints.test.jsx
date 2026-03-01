import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Endpoints from './Endpoints'

const mockApiFetch = vi.fn()

vi.mock('../api', () => ({
  apiFetch: (...args) => mockApiFetch(...args),
}))

function jsonResponse(payload, ok = true, status = 200) {
  return {
    ok,
    status,
    json: async () => payload,
  }
}

describe('Endpoints (WireGuard Dashboard)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    window.confirm = vi.fn(() => true)
  })

  it('loads and renders allowed apps and endpoint list', async () => {
    mockApiFetch.mockResolvedValueOnce(
      jsonResponse({
        wiresock_allowed_apps: 'chrome.exe,telegram.exe',
        endpoints: [
          { ID: 1, name: 'Germany', address: 'de.example.com:51820', is_active: true },
        ],
      })
    )

    render(<Endpoints />)

    expect(await screen.findByText('WireGuard Dashboard')).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByDisplayValue('chrome.exe,telegram.exe')).toBeInTheDocument()
    })

    expect(screen.getByText('Germany')).toBeInTheDocument()
    expect(screen.getByText('de.example.com:51820')).toBeInTheDocument()
    expect(mockApiFetch).toHaveBeenCalledWith('/admin/wireguard')
  })

  it('saves allowed apps via admin wireguard endpoint', async () => {
    mockApiFetch
      .mockResolvedValueOnce(
        jsonResponse({
          wiresock_allowed_apps: 'chrome.exe,telegram.exe',
          endpoints: [],
        })
      )
      .mockResolvedValueOnce(
        jsonResponse({
          message: 'WireGuard settings updated',
          wiresock_allowed_apps: 'chrome.exe,discord.exe',
        })
      )

    render(<Endpoints />)

    const textarea = await screen.findByLabelText('Allowed apps list (pass-through format)')
    await userEvent.clear(textarea)
    await userEvent.type(textarea, 'chrome.exe,discord.exe')

    const saveBtn = screen.getByRole('button', { name: /save allowed apps/i })
    await userEvent.click(saveBtn)

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith('/admin/wireguard', {
        method: 'PATCH',
        body: JSON.stringify({ wiresock_allowed_apps: 'chrome.exe,discord.exe' }),
      })
    })

    expect(await screen.findByText('WireSock allowed apps updated successfully')).toBeInTheDocument()
  })

  it('shows connection error when save fails', async () => {
    mockApiFetch
      .mockResolvedValueOnce(
        jsonResponse({
          wiresock_allowed_apps: 'chrome.exe',
          endpoints: [],
        })
      )
      .mockRejectedValueOnce(new Error('network error'))

    render(<Endpoints />)

    const textarea = await screen.findByLabelText('Allowed apps list (pass-through format)')
    await userEvent.clear(textarea)
    await userEvent.type(textarea, 'new-app.exe')

    const saveBtn = screen.getByRole('button', { name: /save allowed apps/i })
    await userEvent.click(saveBtn)

    expect(await screen.findByText('Connection error')).toBeInTheDocument()
  })

  it('creates a new endpoint', async () => {
    mockApiFetch
      .mockResolvedValueOnce(
        jsonResponse({
          wiresock_allowed_apps: '',
          endpoints: [],
        })
      )
      .mockResolvedValueOnce(
        jsonResponse({
          ID: 1,
          name: 'Germany',
          address: 'de.example.com:51820',
          is_active: true,
        })
      )
      .mockResolvedValueOnce(
        jsonResponse({
          wiresock_allowed_apps: '',
          endpoints: [
            { ID: 1, name: 'Germany', address: 'de.example.com:51820', is_active: true },
          ],
        })
      )

    render(<Endpoints />)

    const addBtn = await screen.findByRole('button', { name: /add endpoint/i })
    await userEvent.click(addBtn)

    const nameInput = await screen.findByLabelText(/name/i)
    const addressInput = screen.getByLabelText(/address/i)

    await userEvent.type(nameInput, 'Germany')
    await userEvent.type(addressInput, 'de.example.com:51820')

    const saveBtn = screen.getByRole('button', { name: /save endpoint/i })
    await userEvent.click(saveBtn)

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith('/endpoints', {
        method: 'POST',
        body: JSON.stringify({
          name: 'Germany',
          address: 'de.example.com:51820',
          is_active: true,
        }),
      })
    })

    expect(await screen.findByText('Endpoint created successfully')).toBeInTheDocument()
  })

  it('edits an existing endpoint', async () => {
    mockApiFetch
      .mockResolvedValueOnce(
        jsonResponse({
          wiresock_allowed_apps: '',
          endpoints: [
            { ID: 1, name: 'Germany', address: 'de.example.com:51820', is_active: true },
          ],
        })
      )
      .mockResolvedValueOnce(
        jsonResponse({
          ID: 1,
          name: 'Germany Updated',
          address: 'de-new.example.com:51820',
          is_active: true,
        })
      )
      .mockResolvedValueOnce(
        jsonResponse({
          wiresock_allowed_apps: '',
          endpoints: [
            { ID: 1, name: 'Germany Updated', address: 'de-new.example.com:51820', is_active: true },
          ],
        })
      )

    render(<Endpoints />)

    const editBtn = await screen.findByRole('button', { name: /edit endpoint/i })
    await userEvent.click(editBtn)

    const nameInput = await screen.findByDisplayValue('Germany')
    await userEvent.clear(nameInput)
    await userEvent.type(nameInput, 'Germany Updated')

    const saveBtn = screen.getByRole('button', { name: /save changes/i })
    await userEvent.click(saveBtn)

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith('/endpoints/1', {
        method: 'PATCH',
        body: JSON.stringify({
          name: 'Germany Updated',
          address: 'de.example.com:51820',
          is_active: true,
        }),
      })
    })

    expect(await screen.findByText('Endpoint updated successfully')).toBeInTheDocument()
  })

  it('deletes an endpoint', async () => {
    mockApiFetch
      .mockResolvedValueOnce(
        jsonResponse({
          wiresock_allowed_apps: '',
          endpoints: [
            { ID: 1, name: 'Germany', address: 'de.example.com:51820', is_active: true },
          ],
        })
      )
      .mockResolvedValueOnce(
        jsonResponse({
          message: 'Endpoint deleted',
        })
      )
      .mockResolvedValueOnce(
        jsonResponse({
          wiresock_allowed_apps: '',
          endpoints: [],
        })
      )

    render(<Endpoints />)

    const deleteBtn = await screen.findByRole('button', { name: /delete endpoint/i })
    await userEvent.click(deleteBtn)

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith('/endpoints/1', {
        method: 'DELETE',
      })
    })

    expect(await screen.findByText('Endpoint deleted')).toBeInTheDocument()
  })

  it('cancels endpoint creation', async () => {
    mockApiFetch.mockResolvedValueOnce(
      jsonResponse({
        wiresock_allowed_apps: '',
        endpoints: [],
      })
    )

    render(<Endpoints />)

    const addBtn = await screen.findByRole('button', { name: /add endpoint/i })
    await userEvent.click(addBtn)

    const cancelBtn = screen.getByRole('button', { name: /cancel/i })
    await userEvent.click(cancelBtn)

    expect(screen.queryByLabelText(/name/i)).not.toBeInTheDocument()
  })

  it('shows inactive endpoint badge', async () => {
    mockApiFetch.mockResolvedValueOnce(
      jsonResponse({
        wiresock_allowed_apps: '',
        endpoints: [
          { ID: 1, name: 'Germany', address: 'de.example.com:51820', is_active: false },
        ],
      })
    )

    render(<Endpoints />)

    expect(await screen.findByText('Germany')).toBeInTheDocument()
    // The badge text might be "Inactive" or we need to check for the badge element
    const inactiveBadge = await screen.findByText(/inactive/i)
    expect(inactiveBadge).toBeInTheDocument()
  })
})
