import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { SentimentBadge } from '../shared/SentimentBadge'

describe('SentimentBadge', () => {
  it('renders positive sentiment correctly', () => {
    render(<SentimentBadge sentiment="positive" score={0.75} />)
    const badge = screen.getByText(/Positive/)
    expect(badge).toBeInTheDocument()
    expect(badge).toHaveClass('sentiment-positive')
  })

  it('renders negative sentiment correctly', () => {
    render(<SentimentBadge sentiment="negative" score={-0.5} />)
    const badge = screen.getByText(/Negative/)
    expect(badge).toBeInTheDocument()
    expect(badge).toHaveClass('sentiment-negative')
  })

  it('renders neutral sentiment correctly', () => {
    render(<SentimentBadge sentiment="neutral" score={0.05} />)
    const badge = screen.getByText(/Neutral/)
    expect(badge).toBeInTheDocument()
    expect(badge).toHaveClass('sentiment-neutral')
  })

  it('renders mixed sentiment correctly', () => {
    render(<SentimentBadge sentiment="mixed" score={0.0} />)
    const badge = screen.getByText(/Mixed/)
    expect(badge).toBeInTheDocument()
    expect(badge).toHaveClass('sentiment-mixed')
  })

  it('renders N/A when sentiment is null', () => {
    render(<SentimentBadge sentiment={null} />)
    expect(screen.getByText('N/A')).toBeInTheDocument()
  })

  it('shows score in title attribute', () => {
    render(<SentimentBadge sentiment="positive" score={0.8} />)
    const badge = screen.getByText(/Positive/)
    expect(badge).toHaveAttribute('title', 'Score: 0.80')
  })

  it('renders without score', () => {
    render(<SentimentBadge sentiment="positive" />)
    expect(screen.getByText('Positive')).toBeInTheDocument()
  })

  it('formats positive score with + sign', () => {
    render(<SentimentBadge sentiment="positive" score={0.7} />)
    expect(screen.getByText('Positive (+0.70)')).toBeInTheDocument()
  })

  it('formats negative score without + sign', () => {
    render(<SentimentBadge sentiment="negative" score={-0.5} />)
    expect(screen.getByText('Negative (-0.50)')).toBeInTheDocument()
  })
})
