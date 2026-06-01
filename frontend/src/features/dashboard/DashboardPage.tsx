import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../../shared/api'
import { SentimentBadge } from '../../shared/SentimentBadge'
import type { DashboardOverview, SubredditOverview } from '../../shared/types'

export function DashboardPage() {
  const [data, setData] = useState<DashboardOverview | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .get<DashboardOverview>('/dashboard/overview')
      .then((r) => setData(r.data))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="loading">Loading dashboard…</div>
  if (error) return <div className="error-msg">{error}</div>

  return (
    <div>
      <div className="page-header">
        <h1>Dashboard</h1>
        <p>Overview of all monitored subreddits</p>
      </div>
      {data && data.total === 0 ? (
        <div className="card">
          <p style={{ color: 'var(--color-text-muted)' }}>
            No subreddits configured yet. Go to{' '}
            <Link to="/settings" style={{ color: 'var(--color-accent)' }}>
              Settings
            </Link>{' '}
            to add some.
          </p>
        </div>
      ) : (
        <div className="grid-2">
          {data?.subreddits.map((sr) => (
            <SubredditCard key={sr.id} subreddit={sr} />
          ))}
        </div>
      )}
    </div>
  )
}

function SubredditCard({ subreddit }: { subreddit: SubredditOverview }) {
  return (
    <Link
      to={`/subreddit/${subreddit.name}`}
      style={{ textDecoration: 'none', color: 'inherit' }}
    >
      <div className="card" style={{ cursor: 'pointer' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
          <h3 style={{ fontSize: '1rem', marginBottom: '0.5rem' }}>r/{subreddit.name}</h3>
          <SentimentBadge
            sentiment={subreddit.community_sentiment}
            score={subreddit.community_sentiment_score}
          />
        </div>
        {subreddit.summary && (
          <p
            style={{
              fontSize: '0.85rem',
              color: 'var(--color-text-muted)',
              marginBottom: '0.75rem',
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
            }}
          >
            {subreddit.summary}
          </p>
        )}
        {subreddit.major_themes.length > 0 && (
          <div>
            {subreddit.major_themes.slice(0, 3).map((t) => (
              <span key={t} className="tag">
                {t}
              </span>
            ))}
          </div>
        )}
        {subreddit.latest_analysis_date && (
          <p
            style={{
              fontSize: '0.75rem',
              color: 'var(--color-text-muted)',
              marginTop: '0.75rem',
            }}
          >
            Last analyzed: {subreddit.latest_analysis_date}
          </p>
        )}
      </div>
    </Link>
  )
}
