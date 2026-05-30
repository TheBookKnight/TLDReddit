import { useEffect, useState } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'
import api from '../../shared/api'
import type { SentimentDataPoint, Subreddit } from '../../shared/types'

export function TrendsPage() {
  const [subreddits, setSubreddits] = useState<Subreddit[]>([])
  const [selected, setSelected] = useState<string>('')
  const [days, setDays] = useState(30)
  const [sentimentData, setSentimentData] = useState<SentimentDataPoint[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.get<Subreddit[]>('/subreddits/').then((r) => {
      setSubreddits(r.data)
      if (r.data.length > 0) setSelected(r.data[0].name)
    })
  }, [])

  useEffect(() => {
    if (!selected) return
    setLoading(true)
    setError(null)
    api
      .get<SentimentDataPoint[]>(`/trends/${selected}/sentiment?days=${days}`)
      .then((r) => setSentimentData(r.data))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [selected, days])

  return (
    <div>
      <div className="page-header">
        <h1>Trends</h1>
        <p>Historical sentiment and theme analysis</p>
      </div>

      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        <div>
          <label style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', display: 'block', marginBottom: '0.3rem' }}>
            Subreddit
          </label>
          <select
            className="input"
            style={{ width: 'auto' }}
            value={selected}
            onChange={(e) => setSelected(e.target.value)}
          >
            {subreddits.map((sr) => (
              <option key={sr.id} value={sr.name}>
                r/{sr.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', display: 'block', marginBottom: '0.3rem' }}>
            Time Range
          </label>
          <select
            className="input"
            style={{ width: 'auto' }}
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
            <option value={365}>Last year</option>
          </select>
        </div>
      </div>

      {error && <div className="error-msg" style={{ marginBottom: '1rem' }}>{error}</div>}

      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ marginBottom: '1rem', fontSize: '0.95rem' }}>
          Sentiment Over Time — r/{selected}
        </h3>
        {loading ? (
          <div className="loading">Loading chart…</div>
        ) : sentimentData.length === 0 ? (
          <div style={{ color: 'var(--color-text-muted)', padding: '2rem', textAlign: 'center' }}>
            No data available for this time range.
          </div>
        ) : (
          <SentimentChart data={sentimentData} />
        )}
      </div>
    </div>
  )
}

function SentimentChart({ data }: { data: SentimentDataPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 11, fill: '#8b8fa8' }}
          tickLine={false}
        />
        <YAxis
          domain={[-1, 1]}
          tick={{ fontSize: 11, fill: '#8b8fa8' }}
          tickLine={false}
          tickFormatter={(v: number) => v.toFixed(1)}
        />
        <Tooltip
          contentStyle={{
            background: '#1a1d27',
            border: '1px solid #2a2d3e',
            borderRadius: '6px',
            fontSize: '0.85rem',
          }}
          formatter={(value: number) => [value.toFixed(2), 'Sentiment Score']}
        />
        <ReferenceLine y={0} stroke="rgba(255,255,255,0.15)" strokeDasharray="4 4" />
        <Line
          type="monotone"
          dataKey="community_sentiment_score"
          stroke="#7c6af7"
          strokeWidth={2}
          dot={{ r: 3, fill: '#7c6af7' }}
          activeDot={{ r: 5 }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
