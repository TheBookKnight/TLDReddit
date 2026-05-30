# TLDReddit — Reddit Trend Intelligence Platform

A local-first platform that monitors subreddits, summarises trending discussions with LLMs, stores historical results in SQLite, and provides a dashboard and chat interface for exploring community sentiment over time.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Browser                                  │
│  React + TypeScript + Vite                                       │
│  ┌──────────┐ ┌──────────┐ ┌────────┐ ┌──────┐ ┌──────────┐   │
│  │Dashboard │ │Subreddit │ │ Trends │ │ Chat │ │ Settings │   │
│  └──────────┘ └──────────┘ └────────┘ └──────┘ └──────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP /api/v1/*
┌────────────────────────▼────────────────────────────────────────┐
│                      FastAPI Backend                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  features/                                               │   │
│  │  ├── configuration/   subreddit CRUD                     │   │
│  │  ├── reddit_client/   HTTP + retry + rate limit          │   │
│  │  ├── post_analysis/   LLM abstraction (OpenAI)           │   │
│  │  ├── subreddit_ingestion/ pipeline + APScheduler         │   │
│  │  ├── trend_analysis/  sentiment & theme queries          │   │
│  │  ├── dashboard/       overview & detail views            │   │
│  │  └── chatbot/         RAG-style chat over analyses       │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │ SQLAlchemy async
┌────────────────────────▼────────────────────────────────────────┐
│                     SQLite Database                              │
│  subreddits │ posts │ post_analyses │ subreddit_analyses        │
│  analysis_runs │ chat_sessions │ chat_messages                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Features

| Feature | Description |
|---|---|
| **Ingestion** | Daily scheduled job (APScheduler) fetches top-10 hot posts + top-20 comments per subreddit via Reddit JSON API |
| **LLM Analysis** | Per-post summaries with sentiment score, key takeaways, bullish/bearish arguments |
| **Meta Analysis** | Subreddit-level analysis: major themes, emerging topics, notable shifts |
| **Dashboard** | Overview cards with sentiment indicators; subreddit & post detail views |
| **Trends** | Recharts line chart of sentiment over time; multi-subreddit comparison |
| **Chat** | RAG-style chat — questions answered from stored analyses via keyword retrieval + LLM |
| **Settings** | Add/remove subreddits, activate/deactivate, trigger manual ingestion |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite, React Router 6, Recharts, Axios |
| Backend | Python 3.12, FastAPI, SQLAlchemy (async), APScheduler, Tenacity |
| Database | SQLite with aiosqlite async driver |
| LLM | OpenAI API (abstracted — swap for local models) |
| Package Manager | uv (backend), npm (frontend) |
| Testing | pytest + pytest-cov (backend), Vitest + React Testing Library (frontend) |
| Linting | ruff + mypy (backend), ESLint + TypeScript (frontend) |
| Containers | Docker, Docker Compose |
| CI | GitHub Actions |

---

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- [uv](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- An OpenAI API key

### 1. Clone & configure

```bash
git clone https://github.com/TheBookKnight/TLDReddit.git
cd TLDReddit
cp .env.example .env
# Edit .env — set OPENAI_API_KEY at minimum
```

### 2. Install dependencies

```bash
make install
```

### 3. Start development servers

```bash
make dev
```

- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- API docs: http://localhost:8000/api/docs

---

## Docker

```bash
# Build and start all services
make docker-up

# View logs
make docker-logs

# Stop
make docker-down
```

Frontend is served at http://localhost:3000, backend at http://localhost:8000.

---

## Testing

```bash
# All tests
make test

# Backend only (with coverage)
make test-backend

# Frontend only
make test-frontend

# Coverage reports (HTML)
make test-coverage
```

### Backend coverage target: 70%
### Frontend: 30 tests across Dashboard, Settings, Chat, Trends, SentimentBadge

---

## Linting & Type Checking

```bash
# Lint everything
make lint

# Auto-fix backend formatting
make format
```

---

## CI Workflow

GitHub Actions runs on every push and pull request to `main`:

```
CI
├── backend
│   ├── uv sync --extra dev
│   ├── ruff check
│   ├── mypy
│   └── pytest --cov (fails if < 70% coverage)
└── frontend
    ├── npm ci
    ├── eslint
    ├── tsc --noEmit
    └── vitest run
```

---

## Project Structure

```
TLDReddit/
├── backend/
│   ├── src/
│   │   ├── features/
│   │   │   ├── chatbot/           routes, retrieval, schemas
│   │   │   ├── configuration/     subreddit CRUD
│   │   │   ├── dashboard/         overview & detail routes
│   │   │   ├── post_analysis/     LLM provider + schemas
│   │   │   ├── reddit_client/     async HTTP client
│   │   │   ├── subreddit_ingestion/ pipeline + scheduler
│   │   │   └── trend_analysis/    sentiment & theme routes
│   │   ├── database/              models + session factory
│   │   ├── shared/                settings (Pydantic)
│   │   └── main.py                FastAPI app factory
│   ├── tests/                     pytest tests (57 tests)
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── features/
│   │   │   ├── chat/              ChatPage
│   │   │   ├── dashboard/         DashboardPage
│   │   │   ├── settings/          SettingsPage
│   │   │   ├── subreddit/         SubredditDetailPage
│   │   │   └── trends/            TrendsPage
│   │   ├── shared/                api client, types, SentimentBadge
│   │   └── tests/                 Vitest tests (30 tests)
│   └── package.json
├── .github/workflows/ci.yml
├── docker-compose.yml
├── Makefile
└── .env.example
```

---

## Environment Variables

See [`.env.example`](.env.example) for the full list. Key variables:

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | — | **Required.** OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model for analysis |
| `REDDIT_USER_AGENT` | `TLDReddit/1.0` | Reddit API user agent |
| `DATABASE_URL` | `sqlite+aiosqlite:///./tldreddit.db` | Database URL |
| `INGESTION_HOUR` | `6` | UTC hour for daily job |
| `INGESTION_TOP_POSTS` | `10` | Posts per subreddit per run |
| `INGESTION_TOP_COMMENTS` | `20` | Comments per post |

---

## Future Enhancements

- **Multiple LLM providers** — Ollama / local models via the existing `LLMProvider` abstraction
- **Vector database** — replace keyword retrieval with semantic search (pgvector, Chroma)
- **Additional sources** — Hacker News, X/Twitter, newsletters
- **Email digests** — scheduled HTML summaries
- **Push notifications** — alerts on sentiment spikes or emerging topics
- **User accounts** — per-user subreddit lists and chat history
- **Export** — CSV / PDF trend reports
