import { BrowserRouter, Route, Routes, NavLink } from 'react-router-dom'
import { DashboardPage } from './features/dashboard/DashboardPage'
import { SubredditDetailPage } from './features/subreddit/SubredditDetailPage'
import { TrendsPage } from './features/trends/TrendsPage'
import { ChatPage } from './features/chat/ChatPage'
import { SettingsPage } from './features/settings/SettingsPage'
import './App.css'

export default function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <nav className="sidebar">
          <div className="sidebar-brand">
            <h2>TLDReddit</h2>
            <span className="brand-tagline">Reddit Trend Intelligence</span>
          </div>
          <ul className="nav-links">
            <li>
              <NavLink to="/" end className={({ isActive }) => (isActive ? 'active' : '')}>
                📊 Dashboard
              </NavLink>
            </li>
            <li>
              <NavLink to="/trends" className={({ isActive }) => (isActive ? 'active' : '')}>
                📈 Trends
              </NavLink>
            </li>
            <li>
              <NavLink to="/chat" className={({ isActive }) => (isActive ? 'active' : '')}>
                💬 Chat
              </NavLink>
            </li>
            <li>
              <NavLink to="/settings" className={({ isActive }) => (isActive ? 'active' : '')}>
                ⚙️ Settings
              </NavLink>
            </li>
          </ul>
        </nav>
        <main className="main-content">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/subreddit/:name" element={<SubredditDetailPage />} />
            <Route path="/trends" element={<TrendsPage />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
