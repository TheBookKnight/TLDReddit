import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { SettingsPage } from '../features/settings/SettingsPage'
import type { Subreddit } from '../shared/types'
import api from '../shared/api'

vi.mock('../shared/api', () => ({
  default: { get: vi.fn(), post: vi.fn(), patch: vi.fn() },
}))

const mockGet = vi.mocked(api.get)

const mockSubreddits: Subreddit[] = [
  {
    id: 1,
    name: 'Python',
    display_name: null,
    description: null,
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 2,
    name: 'stocks',
    display_name: 'r/stocks',
    description: null,
    is_active: false,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
]

function renderSettings() {
  return render(
    <MemoryRouter>
      <SettingsPage />
    </MemoryRouter>,
  )
}

describe('SettingsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders heading and add form', () => {
    mockGet.mockResolvedValue({ data: [] } as Awaited<ReturnType<typeof api.get>>)
    renderSettings()
    expect(screen.getByText('Settings')).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/subreddit name/)).toBeInTheDocument()
  })

  it('displays subreddits in table', async () => {
    mockGet.mockResolvedValue({ data: mockSubreddits } as Awaited<ReturnType<typeof api.get>>)
    renderSettings()
    await waitFor(() => {
      expect(screen.getByText('r/Python')).toBeInTheDocument()
      expect(screen.getByText('r/stocks')).toBeInTheDocument()
    })
  })

  it('shows active/inactive status', async () => {
    mockGet.mockResolvedValue({ data: mockSubreddits } as Awaited<ReturnType<typeof api.get>>)
    renderSettings()
    await waitFor(() => {
      expect(screen.getByText('Active')).toBeInTheDocument()
      expect(screen.getByText('Inactive')).toBeInTheDocument()
    })
  })

  it('shows empty state when no subreddits', async () => {
    mockGet.mockResolvedValue({ data: [] } as Awaited<ReturnType<typeof api.get>>)
    renderSettings()
    await waitFor(() =>
      expect(screen.getByText(/No subreddits configured/)).toBeInTheDocument(),
    )
  })

  it('add button is disabled when input is empty', () => {
    mockGet.mockResolvedValue({ data: [] } as Awaited<ReturnType<typeof api.get>>)
    renderSettings()
    const addBtn = screen.getByRole('button', { name: 'Add' })
    expect(addBtn).toBeDisabled()
  })

  it('enables add button when input has value', () => {
    mockGet.mockResolvedValue({ data: [] } as Awaited<ReturnType<typeof api.get>>)
    renderSettings()
    const input = screen.getByPlaceholderText(/subreddit name/)
    fireEvent.change(input, { target: { value: 'MachineLearning' } })
    const addBtn = screen.getByRole('button', { name: 'Add' })
    expect(addBtn).not.toBeDisabled()
  })
})
