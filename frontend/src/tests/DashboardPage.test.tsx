import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { DashboardPage } from '../features/dashboard/DashboardPage'
import type { DashboardOverview } from '../shared/types'
import api from '../shared/api'

vi.mock('../shared/api', () => ({
  default: { get: vi.fn(), post: vi.fn(), patch: vi.fn() },
}))

const mockGet = vi.mocked(api.get)

const mockOverview: DashboardOverview = {
  total: 2,
  subreddits: [
    {
      id: 1,
      name: 'stocks',
      display_name: 'r/stocks',
      latest_analysis_date: '2024-01-15',
      community_sentiment: 'positive',
      community_sentiment_score: 0.65,
      major_themes: ['Earnings', 'Fed rates'],
      summary: 'The stock community is bullish.',
    },
    {
      id: 2,
      name: 'Python',
      display_name: null,
      latest_analysis_date: null,
      community_sentiment: null,
      community_sentiment_score: null,
      major_themes: [],
      summary: null,
    },
  ],
}

function renderDashboard() {
  return render(
    <MemoryRouter>
      <DashboardPage />
    </MemoryRouter>,
  )
}

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading state initially', () => {
    mockGet.mockReturnValue(new Promise(() => {}) as ReturnType<typeof api.get>)
    renderDashboard()
    expect(screen.getByText(/Loading dashboard/)).toBeInTheDocument()
  })

  it('renders subreddit cards after loading', async () => {
    mockGet.mockResolvedValue({ data: mockOverview } as Awaited<ReturnType<typeof api.get>>)
    renderDashboard()
    await waitFor(() => expect(screen.getByText('r/stocks')).toBeInTheDocument())
    expect(screen.getByText('r/Python')).toBeInTheDocument()
  })

  it('shows empty state when no subreddits', async () => {
    const empty: DashboardOverview = { total: 0, subreddits: [] }
    mockGet.mockResolvedValue({ data: empty } as Awaited<ReturnType<typeof api.get>>)
    renderDashboard()
    await waitFor(() =>
      expect(screen.getByText(/No subreddits configured/)).toBeInTheDocument(),
    )
  })

  it('shows error state on API failure', async () => {
    mockGet.mockRejectedValue(new Error('Network Error'))
    renderDashboard()
    await waitFor(() => expect(screen.getByText('Network Error')).toBeInTheDocument())
  })

  it('shows sentiment badge for subreddits with analysis', async () => {
    mockGet.mockResolvedValue({ data: mockOverview } as Awaited<ReturnType<typeof api.get>>)
    renderDashboard()
    await waitFor(() => expect(screen.getByText(/Positive/)).toBeInTheDocument())
  })

  it('shows major themes as tags', async () => {
    mockGet.mockResolvedValue({ data: mockOverview } as Awaited<ReturnType<typeof api.get>>)
    renderDashboard()
    await waitFor(() => {
      expect(screen.getByText('Earnings')).toBeInTheDocument()
      expect(screen.getByText('Fed rates')).toBeInTheDocument()
    })
  })
})
