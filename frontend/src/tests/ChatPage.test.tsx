import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { ChatPage } from '../features/chat/ChatPage'
import type { ChatSession } from '../shared/types'
import api from '../shared/api'

vi.mock('../shared/api', () => ({
  default: { get: vi.fn(), post: vi.fn(), patch: vi.fn() },
}))

const mockGet = vi.mocked(api.get)

const mockSessions: ChatSession[] = [
  {
    id: 1,
    title: 'What is r/stocks discussing?',
    created_at: '2024-01-15T10:00:00Z',
    messages: [],
  },
]

const mockSessionWithMessages: ChatSession = {
  id: 1,
  title: 'What is r/stocks discussing?',
  created_at: '2024-01-15T10:00:00Z',
  messages: [
    {
      id: 1,
      session_id: 1,
      role: 'user',
      content: 'What is r/stocks discussing?',
      created_at: '2024-01-15T10:00:00Z',
    },
    {
      id: 2,
      session_id: 1,
      role: 'assistant',
      content: 'r/stocks is discussing earnings and Fed rates.',
      created_at: '2024-01-15T10:00:05Z',
    },
  ],
}

function renderChat() {
  return render(
    <MemoryRouter>
      <ChatPage />
    </MemoryRouter>,
  )
}

describe('ChatPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the new chat button', () => {
    mockGet.mockResolvedValue({ data: mockSessions } as Awaited<ReturnType<typeof api.get>>)
    renderChat()
    expect(screen.getByText('+ New Chat')).toBeInTheDocument()
  })

  it('displays existing sessions', async () => {
    mockGet.mockResolvedValue({ data: mockSessions } as Awaited<ReturnType<typeof api.get>>)
    renderChat()
    await waitFor(() =>
      expect(screen.getByText('What is r/stocks discussing?')).toBeInTheDocument(),
    )
  })

  it('shows empty state prompt when no session selected', async () => {
    mockGet.mockResolvedValue({ data: [] } as Awaited<ReturnType<typeof api.get>>)
    renderChat()
    await waitFor(() =>
      expect(screen.getByText(/Select or start a new conversation/)).toBeInTheDocument(),
    )
  })

  it('displays messages when a session is selected', async () => {
    mockGet.mockImplementation((url: string) => {
      if ((url as string).includes('/sessions/1')) {
        return Promise.resolve({ data: mockSessionWithMessages }) as ReturnType<typeof api.get>
      }
      return Promise.resolve({ data: mockSessions }) as ReturnType<typeof api.get>
    })
    renderChat()
    await waitFor(() => screen.getByText('What is r/stocks discussing?'))
    fireEvent.click(screen.getByText('What is r/stocks discussing?'))
    await waitFor(() =>
      expect(
        screen.getByText('r/stocks is discussing earnings and Fed rates.'),
      ).toBeInTheDocument(),
    )
  })

  it('send button is disabled when input is empty', async () => {
    mockGet.mockImplementation((url: string) => {
      if ((url as string).includes('/sessions/1')) {
        return Promise.resolve({ data: mockSessionWithMessages }) as ReturnType<typeof api.get>
      }
      return Promise.resolve({ data: mockSessions }) as ReturnType<typeof api.get>
    })
    renderChat()
    await waitFor(() => screen.getByText('What is r/stocks discussing?'))
    fireEvent.click(screen.getByText('What is r/stocks discussing?'))
    await waitFor(() => screen.getByPlaceholderText(/Ask about Reddit trends/))
    const sendBtn = screen.getByRole('button', { name: 'Send' })
    expect(sendBtn).toBeDisabled()
  })
})
