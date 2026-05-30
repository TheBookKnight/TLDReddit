export interface Subreddit {
  id: number
  name: string
  display_name: string | null
  description: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface PostAnalysis {
  post_summary: string
  overall_sentiment: 'positive' | 'negative' | 'neutral' | 'mixed'
  sentiment_score: number
  key_community_takeaways: string[]
  bullish_arguments: string[]
  bearish_arguments: string[]
  confidence: number
  top_comments?: string[]
  analyzed_at?: string
}

export interface Post {
  id: number
  reddit_id: string
  title: string
  body?: string
  score: number
  num_comments: number
  url?: string
  permalink?: string
  author?: string
  reddit_created_at?: string
  analysis?: PostAnalysis
}

export interface SubredditAnalysis {
  id?: number
  subreddit?: string
  analysis_date: string
  major_themes: string[]
  emerging_topics: string[]
  community_sentiment: 'positive' | 'negative' | 'neutral' | 'mixed'
  community_sentiment_score: number
  notable_shifts: string[]
  summary: string
  created_at?: string
}

export interface SubredditOverview {
  id: number
  name: string
  display_name: string | null
  latest_analysis_date: string | null
  community_sentiment: string | null
  community_sentiment_score: number | null
  major_themes: string[]
  summary: string | null
}

export interface DashboardOverview {
  subreddits: SubredditOverview[]
  total: number
}

export interface SentimentDataPoint {
  date: string
  community_sentiment: string
  community_sentiment_score: number
}

export interface ThemesDataPoint {
  date: string
  major_themes: string[]
  emerging_topics: string[]
}

export interface ChatSession {
  id: number
  title: string | null
  created_at: string
  messages: ChatMessage[]
}

export interface ChatMessage {
  id: number
  session_id: number
  role: 'user' | 'assistant'
  content: string
  created_at: string
}
