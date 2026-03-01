import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Settings from './Settings'

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

describe('Settings', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('loads and renders settings including required channel', async () => {
    mockApiFetch
      .mockResolvedValueOnce(
        jsonResponse([
          { ID: 1, name: 'Server 1', server_type: 'v2ray', api_url: 'http://server1.com', credentials: '{"username":"user1","password":"pass1"}' },
        ])
      )
      .mockResolvedValueOnce(
        jsonResponse({
          admin_card_number: '1234-5678-9012-3456',
          bot_name: 'TestBot',
          required_channel: '@mychannel',
        })
      )

    render(<Settings />)

    expect(await screen.findByText('Settings')).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByDisplayValue('1234-5678-9012-3456')).toBeInTheDocument()
    })

    expect(screen.getByDisplayValue('@mychannel')).toBeInTheDocument()
    expect(mockApiFetch).toHaveBeenCalledWith('/admin/servers')
    expect(mockApiFetch).toHaveBeenCalledWith('/admin/settings')
  })

  it('saves required channel when updated', async () => {
    mockApiFetch
      .mockResolvedValueOnce(jsonResponse([]))
      .mockResolvedValueOnce(
        jsonResponse({
          admin_card_number: '',
          bot_name: '',
          required_channel: '',
        })
      )
      .mockResolvedValueOnce(
        jsonResponse({
          message: 'Settings updated',
          admin_card_number: '',
          required_channel: '@newchannel',
        })
      )

    render(<Settings />)

    const channelInput = await screen.findByPlaceholderText('@mychannel or channel ID')
    await userEvent.clear(channelInput)
    await userEvent.type(channelInput, '@newchannel')

    const saveBtn = screen.getAllByText('Save').find(btn => 
      btn.closest('.glass-card')?.querySelector('input[placeholder*="channel"]')
    )
    await userEvent.click(saveBtn)

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith('/admin/settings', {
        method: 'PATCH',
        body: JSON.stringify({ required_channel: '@newchannel' }),
      })
    })

    expect(await screen.findByText('Required channel updated')).toBeInTheDocument()
  })

  it('disables channel requirement when cleared', async () => {
    mockApiFetch
      .mockResolvedValueOnce(jsonResponse([]))
      .mockResolvedValueOnce(
        jsonResponse({
          admin_card_number: '',
          bot_name: '',
          required_channel: '@mychannel',
        })
      )
      .mockResolvedValueOnce(
        jsonResponse({
          message: 'Settings updated',
          admin_card_number: '',
          required_channel: '',
        })
      )

    render(<Settings />)

    const channelInput = await screen.findByDisplayValue('@mychannel')
    await userEvent.clear(channelInput)

    const saveBtn = screen.getAllByText('Save').find(btn => 
      btn.closest('.glass-card')?.querySelector('input[placeholder*="channel"]')
    )
    await userEvent.click(saveBtn)

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith('/admin/settings', {
        method: 'PATCH',
        body: JSON.stringify({ required_channel: null }),
      })
    })

    expect(await screen.findByText('Channel requirement disabled')).toBeInTheDocument()
  })

  it('shows note when channel is set', async () => {
    mockApiFetch
      .mockResolvedValueOnce(jsonResponse([]))
      .mockResolvedValueOnce(
        jsonResponse({
          admin_card_number: '',
          bot_name: '',
          required_channel: '@mychannel',
        })
      )

    render(<Settings />)

    await waitFor(() => {
      expect(screen.getByText(/Make sure your bot is added as an administrator/)).toBeInTheDocument()
    })
  })

  it('does not show note when channel is empty', async () => {
    mockApiFetch
      .mockResolvedValueOnce(jsonResponse([]))
      .mockResolvedValueOnce(
        jsonResponse({
          admin_card_number: '',
          bot_name: '',
          required_channel: '',
        })
      )

    render(<Settings />)

    await waitFor(() => {
      expect(screen.queryByText(/Make sure your bot is added as an administrator/)).not.toBeInTheDocument()
    })
  })

  it('shows error toast when save fails', async () => {
    mockApiFetch
      .mockResolvedValueOnce(jsonResponse([]))
      .mockResolvedValueOnce(
        jsonResponse({
          admin_card_number: '',
          bot_name: '',
          required_channel: '',
        })
      )
      .mockRejectedValueOnce(new Error('network error'))

    render(<Settings />)

    const channelInput = await screen.findByPlaceholderText('@mychannel or channel ID')
    await userEvent.type(channelInput, '@newchannel')

    const saveBtn = screen.getAllByText('Save').find(btn => 
      btn.closest('.glass-card')?.querySelector('input[placeholder*="channel"]')
    )
    await userEvent.click(saveBtn)

    expect(await screen.findByText('Connection error')).toBeInTheDocument()
  })

  it('saves card number independently', async () => {
    mockApiFetch
      .mockResolvedValueOnce(jsonResponse([]))
      .mockResolvedValueOnce(
        jsonResponse({
          admin_card_number: '1234-5678',
          bot_name: '',
          required_channel: '',
        })
      )
      .mockResolvedValueOnce(
        jsonResponse({
          message: 'Settings updated',
          admin_card_number: '9999-8888',
          required_channel: '',
        })
      )

    render(<Settings />)

    const cardInput = await screen.findByPlaceholderText('1234-5678-9012-3456')
    await userEvent.clear(cardInput)
    await userEvent.type(cardInput, '9999-8888')

    const saveBtns = screen.getAllByText('Save')
    // First Save button is for card number
    await userEvent.click(saveBtns[0])

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith('/admin/settings', {
        method: 'PATCH',
        body: JSON.stringify({ admin_card_number: '9999-8888' }),
      })
    })

    expect(await screen.findByText('Card number updated')).toBeInTheDocument()
  })
})


