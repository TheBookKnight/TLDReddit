import { useEffect, useState } from 'react'
import api from '../../shared/api'
import type { Subreddit } from '../../shared/types'

export function SettingsPage() {
  const [subreddits, setSubreddits] = useState<Subreddit[]>([])
  const [newName, setNewName] = useState('')
  const [adding, setAdding] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)
  const [triggering, setTriggering] = useState<string | null>(null)

  useEffect(() => {
    loadSubreddits()
  }, [])

  function loadSubreddits() {
    api.get<Subreddit[]>('/subreddits/?include_inactive=true').then((r) => {
      setSubreddits(r.data)
    })
  }

  async function handleAdd() {
    if (!newName.trim()) return
    setAdding(true)
    setError(null)
    try {
      await api.post('/subreddits/', { name: newName.trim() })
      setNewName('')
      setSuccessMsg(`r/${newName.trim()} added successfully!`)
      loadSubreddits()
      setTimeout(() => setSuccessMsg(null), 3000)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Failed to add subreddit'
      setError(msg)
    } finally {
      setAdding(false)
    }
  }

  async function handleToggle(name: string, isActive: boolean) {
    await api.patch(`/subreddits/${name}`, { is_active: !isActive })
    loadSubreddits()
  }

  async function handleRunIngestion(name: string) {
    setTriggering(name)
    try {
      await api.post(`/ingestion/run/${name}`)
      setSuccessMsg(`Ingestion started for r/${name}`)
      setTimeout(() => setSuccessMsg(null), 3000)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Failed to trigger ingestion'
      setError(msg)
    } finally {
      setTriggering(null)
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Settings</h1>
        <p>Manage monitored subreddits and trigger manual ingestion</p>
      </div>

      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ marginBottom: '1rem', fontSize: '0.95rem' }}>Add Subreddit</h3>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <input
            className="input"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAdd()}
            placeholder="subreddit name (e.g. Python)"
          />
          <button className="btn btn-primary" onClick={handleAdd} disabled={adding || !newName.trim()}>
            {adding ? 'Adding…' : 'Add'}
          </button>
        </div>
        {error && <div className="error-msg" style={{ marginTop: '0.5rem' }}>{error}</div>}
        {successMsg && (
          <div
            style={{
              marginTop: '0.5rem',
              padding: '0.5rem 0.75rem',
              background: 'rgba(16,185,129,0.1)',
              borderRadius: '6px',
              color: '#34d399',
              fontSize: '0.85rem',
            }}
          >
            {successMsg}
          </div>
        )}
      </div>

      <div className="card">
        <h3 style={{ marginBottom: '1rem', fontSize: '0.95rem' }}>Monitored Subreddits</h3>
        {subreddits.length === 0 ? (
          <p style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem' }}>
            No subreddits configured yet.
          </p>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                <th style={{ textAlign: 'left', padding: '0.5rem', color: 'var(--color-text-muted)' }}>Subreddit</th>
                <th style={{ textAlign: 'left', padding: '0.5rem', color: 'var(--color-text-muted)' }}>Status</th>
                <th style={{ textAlign: 'right', padding: '0.5rem', color: 'var(--color-text-muted)' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {subreddits.map((sr) => (
                <tr key={sr.id} style={{ borderBottom: '1px solid var(--color-border)' }}>
                  <td style={{ padding: '0.75rem 0.5rem' }}>r/{sr.name}</td>
                  <td style={{ padding: '0.75rem 0.5rem' }}>
                    <span
                      style={{
                        fontSize: '0.75rem',
                        padding: '0.2rem 0.5rem',
                        borderRadius: '100px',
                        background: sr.is_active ? 'rgba(16,185,129,0.1)' : 'rgba(107,114,128,0.1)',
                        color: sr.is_active ? '#34d399' : '#9ca3af',
                      }}
                    >
                      {sr.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td style={{ padding: '0.75rem 0.5rem', textAlign: 'right' }}>
                    <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                      <button
                        className="btn btn-secondary"
                        style={{ fontSize: '0.8rem', padding: '0.35rem 0.7rem' }}
                        onClick={() => handleRunIngestion(sr.name)}
                        disabled={triggering === sr.name}
                      >
                        {triggering === sr.name ? 'Starting…' : '▶ Run'}
                      </button>
                      <button
                        className="btn btn-secondary"
                        style={{ fontSize: '0.8rem', padding: '0.35rem 0.7rem' }}
                        onClick={() => handleToggle(sr.name, sr.is_active)}
                      >
                        {sr.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
