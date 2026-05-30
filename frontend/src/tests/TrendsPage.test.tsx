import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { TrendsPage } from '../features/trends/TrendsPage'
import type { Subreddit, SentimentDataPoint } from '../shared/types'
import api from '../shared/api'

vi.mock('../shared/api', () => ({
  default: { get: vi.fn(), post: vi.fn(), patch: vi.fn() },
}))

const mockGet = vi.mocked(api.get)

const mockSubreddits: Subreddit[] = [
  {
    id: 1,
    name: 'stocks',
    display_name: 'r/stocks',
    description: null,
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
]

const mockSentimentData: SentimentDataPoint[] = [
  { date: '2024-01-01', community_sentiment: 'negative', community_sentiment_score: -0.3 },
  { date: '2024-01-08', community_sentiment: 'neutral', community_sentiment_score: 0.1 },
  { date: '2024-01-15', community_sentiment: 'positive', community_sentiment_score: 0.7 },
]

function renderTrends() {
  return render(
    <MemoryRouter>
      <TrendsPage />
    </MemoryRouter>,
  )
}

describe('TrendsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the page heading', () => {
    mockGet.mockResolvedValue({ data: [] } as Awaited<ReturnType<typeof api.get>>)
    renderTrends()
    expect(screen.getByText('Trends')).toBeInTheDocument()
  })

  it('renders subreddit selector after loading', async () => {
    mockGet.mockImplementation((url: string) => {
      if ((url as string).includes('/subreddits/')) {
        return Promise.resolve({ data: mockSubreddits }) as ReturnType<typeof api.get>
      }
      return Promise.resolve({ data: mockSentimentData }) as ReturnType<typeof api.get>
    })
    renderTrends()
    await waitFor(() =>
      expect(screen.getByDisplayValue('r/stocks')).toBeInTheDocument(),
    )
  })

  it('shows empty state when no data', async () => {
    mockGet.mockImplementation((url: string) => {
      if ((url as string).includes('/subreddits/')) {
        return Promise.resolve({ data: mockSubreddits }) as ReturnType<typeof api.get>
      }
      return Promise.resolve({ data: [] }) as ReturnType<typeof api.get>
    })
    renderTrends()
    await waitFor(() =>
      expect(screen.getByText(/No data available/)).toBeInTheDocument(),
    )
  })

  it('shows time range selector', () => {
    mockGet.mockResolvedValue({ data: [] } as Awaited<ReturnType<typeof api.get>>)
    renderTrends()
    expect(screen.getByText('Last 30 days')).toBeInTheDocument()
  })
})
