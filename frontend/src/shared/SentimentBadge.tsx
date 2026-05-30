interface Props {
  sentiment: string | null
  score?: number | null
}

export function SentimentBadge({ sentiment, score }: Props) {
  const cls = `sentiment-bg sentiment-${sentiment ?? 'neutral'}`
  const label = sentiment ? sentiment.charAt(0).toUpperCase() + sentiment.slice(1) : 'N/A'
  return (
    <span className={cls} title={score != null ? `Score: ${score.toFixed(2)}` : undefined}>
      {label}
      {score != null && ` (${score > 0 ? '+' : ''}${score.toFixed(2)})`}
    </span>
  )
}
