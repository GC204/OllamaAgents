import type { ChatMessage } from '../api/client'
import { MarkdownRenderer } from './MarkdownRenderer'

export function MessageList({
  messages,
  streamingContent,
  isStreaming,
}: {
  messages: ChatMessage[]
  streamingContent: string
  isStreaming: boolean
}) {
  return (
    <div style={{ flex: 1, overflow: 'auto', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {messages.map((m, i) => (
        <div
          key={i}
          style={{
            alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
            maxWidth: '85%',
            padding: '0.75rem 1rem',
            borderRadius: '12px',
            background: m.role === 'user' ? 'var(--user-bg)' : 'var(--assistant-bg)',
            border: '1px solid var(--border)',
          }}
        >
          <span style={{ fontSize: '0.75rem', color: 'var(--muted)', marginBottom: '0.25rem', display: 'block' }}>
            {m.role === 'user' ? 'You' : 'Assistant'}
          </span>
          {m.role === 'assistant' ? (
            <MarkdownRenderer content={m.content} />
          ) : (
            <span style={{ whiteSpace: 'pre-wrap' }}>{m.content}</span>
          )}
        </div>
      ))}
      {isStreaming && (
        <div
          style={{
            alignSelf: 'flex-start',
            maxWidth: '85%',
            padding: '0.75rem 1rem',
            borderRadius: '12px',
            background: 'var(--assistant-bg)',
            border: '1px solid var(--border)',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.25rem',
          }}
        >
          <span style={{ fontSize: '0.75rem', color: 'var(--muted)', marginBottom: '0.1rem' }}>Assistant</span>
          {streamingContent ? (
            <>
              <MarkdownRenderer content={streamingContent} />
              <span style={{ opacity: 0.7 }}>▌</span>
            </>
          ) : (
            <span style={{ fontSize: '0.9rem', color: 'var(--muted)' }}>Thinking…</span>
          )}
        </div>
      )}
    </div>
  )
}
