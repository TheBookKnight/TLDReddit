import { useEffect, useRef, useState } from 'react'
import api from '../../shared/api'
import type { ChatMessage, ChatSession } from '../../shared/types'

export function ChatPage() {
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [activeSession, setActiveSession] = useState<ChatSession | null>(null)
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    api.get<ChatSession[]>('/chat/sessions').then((r) => {
      setSessions(r.data)
    })
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [activeSession?.messages])

  async function handleNewSession() {
    const r = await api.post<ChatSession>('/chat/sessions', {})
    setSessions((prev) => [r.data, ...prev])
    setActiveSession(r.data)
  }

  async function handleSelectSession(session: ChatSession) {
    const r = await api.get<ChatSession>(`/chat/sessions/${session.id}`)
    setActiveSession(r.data)
  }

  async function handleSend() {
    if (!input.trim() || !activeSession || sending) return
    const content = input.trim()
    setInput('')
    setSending(true)

    // Optimistically add user message
    const tempUserMsg: ChatMessage = {
      id: -1,
      session_id: activeSession.id,
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    }
    setActiveSession((prev) =>
      prev ? { ...prev, messages: [...prev.messages, tempUserMsg] } : prev,
    )

    try {
      await api.post<ChatMessage>(
        `/chat/sessions/${activeSession.id}/messages`,
        { content },
      )
      // Reload session to get both user and assistant messages
      const sessionResp = await api.get<ChatSession>(`/chat/sessions/${activeSession.id}`)
      setActiveSession(sessionResp.data)
      // Update session title in list
      setSessions((prev) =>
        prev.map((s) =>
          s.id === activeSession.id ? { ...s, title: sessionResp.data.title } : s,
        ),
      )
    } catch {
      setActiveSession((prev) =>
        prev
          ? {
              ...prev,
              messages: [
                ...prev.messages,
                {
                  id: -2,
                  session_id: prev.id,
                  role: 'assistant',
                  content: 'Sorry, there was an error getting a response.',
                  created_at: new Date().toISOString(),
                },
              ],
            }
          : prev,
      )
    } finally {
      setSending(false)
    }
  }

  return (
    <div style={{ display: 'flex', gap: '1rem', height: 'calc(100vh - 4rem)' }}>
      {/* Sessions sidebar */}
      <div
        className="card"
        style={{ width: '200px', flexShrink: 0, overflowY: 'auto', padding: '0.75rem' }}
      >
        <button className="btn btn-primary" style={{ width: '100%', marginBottom: '0.75rem' }} onClick={handleNewSession}>
          + New Chat
        </button>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
          {sessions.map((s) => (
            <button
              key={s.id}
              onClick={() => handleSelectSession(s)}
              style={{
                background: activeSession?.id === s.id ? 'rgba(124,106,247,0.2)' : 'transparent',
                border: 'none',
                borderRadius: '6px',
                padding: '0.5rem',
                color: activeSession?.id === s.id ? 'var(--color-accent)' : 'var(--color-text-muted)',
                cursor: 'pointer',
                fontSize: '0.8rem',
                textAlign: 'left',
                width: '100%',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {s.title || 'New Conversation'}
            </button>
          ))}
        </div>
      </div>

      {/* Chat area */}
      <div className="card" style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '1rem' }}>
        {!activeSession ? (
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-text-muted)' }}>
            <div style={{ textAlign: 'center' }}>
              <p>Select or start a new conversation.</p>
              <p style={{ fontSize: '0.85rem', marginTop: '0.5rem' }}>
                Ask about subreddit trends, sentiment, recurring themes…
              </p>
            </div>
          </div>
        ) : (
          <>
            <div style={{ flex: 1, overflowY: 'auto', marginBottom: '1rem' }}>
              {activeSession.messages.map((msg, i) => (
                <MessageBubble key={msg.id !== -1 ? msg.id : `tmp-${i}`} message={msg} />
              ))}
              {sending && (
                <div style={{ color: 'var(--color-text-muted)', fontSize: '0.85rem', padding: '0.5rem' }}>
                  Thinking…
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <input
                className="input"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
                placeholder="Ask about Reddit trends…"
                disabled={sending}
              />
              <button className="btn btn-primary" onClick={handleSend} disabled={sending || !input.trim()}>
                Send
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user'
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        marginBottom: '0.75rem',
      }}
    >
      <div
        style={{
          maxWidth: '75%',
          padding: '0.6rem 0.9rem',
          borderRadius: isUser ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
          background: isUser ? 'var(--color-accent)' : 'var(--color-border)',
          color: 'var(--color-text)',
          fontSize: '0.875rem',
          lineHeight: '1.5',
          whiteSpace: 'pre-wrap',
        }}
      >
        {message.content}
      </div>
    </div>
  )
}
