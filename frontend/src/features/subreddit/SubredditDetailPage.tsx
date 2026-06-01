import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import api from '../../shared/api'
import { SentimentBadge } from '../../shared/SentimentBadge'
import type { Post, SubredditAnalysis } from '../../shared/types'

interface SubredditDetail {
  subreddit: { id: number; name: string; display_name: string | null; description: string | null; is_active: boolean }
  latest_analysis: SubredditAnalysis | null
  posts: Post[]
}

export function SubredditDetailPage() {
  const { name } = useParams<{ name: string }>()
  const [data, setData] = useState<SubredditDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!name) return
    setLoading(true)
    api
      .get<SubredditDetail>(`/dashboard/subreddit/${name}`)
      .then((r) => setData(r.data))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [name])

  if (loading) return <div className="loading">Loading…</div>
  if (error) return <div className="error-msg">{error}</div>
  if (!data) return null

  const { subreddit, latest_analysis, posts } = data

  return (
    <div>
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <h1>r/{subreddit.name}</h1>
          {latest_analysis && (
            <SentimentBadge
              sentiment={latest_analysis.community_sentiment}
              score={latest_analysis.community_sentiment_score}
            />
          )}
        </div>
        {subreddit.description && (
          <p>{subreddit.description}</p>
        )}
      </div>

      {latest_analysis && (
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ marginBottom: '0.75rem' }}>Latest Analysis — {latest_analysis.analysis_date}</h3>
          <p style={{ marginBottom: '1rem', color: 'var(--color-text-muted)', fontSize: '0.9rem' }}>
            {latest_analysis.summary}
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div>
              <h4 style={{ fontSize: '0.85rem', marginBottom: '0.4rem', color: 'var(--color-text-muted)' }}>
                Major Themes
              </h4>
              <div>
                {latest_analysis.major_themes.map((t) => (
                  <span key={t} className="tag">{t}</span>
                ))}
              </div>
            </div>
            <div>
              <h4 style={{ fontSize: '0.85rem', marginBottom: '0.4rem', color: 'var(--color-text-muted)' }}>
                Emerging Topics
              </h4>
              <div>
                {latest_analysis.emerging_topics.map((t) => (
                  <span key={t} className="tag" style={{ background: 'rgba(16, 185, 129, 0.1)', color: '#34d399' }}>
                    {t}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      <h2 style={{ fontSize: '1rem', marginBottom: '1rem' }}>Top Posts</h2>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {posts.map((post) => (
          <PostSummaryCard key={post.id} post={post} />
        ))}
      </div>

      <div style={{ marginTop: '1.5rem' }}>
        <Link to={`/trends`} style={{ color: 'var(--color-accent)', fontSize: '0.9rem' }}>
          View trends for r/{subreddit.name} →
        </Link>
      </div>
    </div>
  )
}

function PostSummaryCard({ post }: { post: Post }) {
  const sentimentScore = post.analysis?.sentiment_score ?? null
  const cardBg =
    sentimentScore == null
      ? undefined
      : sentimentScore > 0.2
        ? 'rgba(59, 130, 246, 0.05)'
        : sentimentScore < -0.2
          ? 'rgba(239, 68, 68, 0.05)'
          : 'rgba(107, 114, 128, 0.05)'

  return (
    <Link to={`/post/${post.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
      <div className="card" style={{ background: cardBg, cursor: 'pointer' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
          <h4 style={{ fontSize: '0.9rem', flex: 1, marginRight: '1rem' }}>{post.title}</h4>
          {post.analysis && (
            <SentimentBadge
              sentiment={post.analysis.overall_sentiment}
              score={post.analysis.sentiment_score}
            />
          )}
        </div>
        {post.analysis?.post_summary && (
          <p style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)', marginTop: '0.4rem' }}>
            {post.analysis.post_summary}
          </p>
        )}
        <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: '0.4rem' }}>
          ↑ {post.score} · {post.num_comments} comments
        </div>
      </div>
    </Link>
  )
}
