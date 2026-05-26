import { useState, useRef, useEffect } from 'react'
import type { ChatMessage } from '../api/client'
import { sendChatStream } from '../api/client'
import { MessageList } from './MessageList'
import { FileUpload } from './FileUpload'

export function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [streamingContent, setStreamingContent] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const streamAccumulatorRef = useRef('')

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingContent])

  async function send() {
    const text = input.trim()
    if (!text || isStreaming) return
    setInput('')
    setError(null)
    const userMessage: ChatMessage = { role: 'user', content: text }
    setMessages((prev) => [...prev, userMessage])
    setStreamingContent('')
    streamAccumulatorRef.current = ''
    setIsStreaming(true)

    await sendChatStream(
      text,
      messages,
      (token) => {
        streamAccumulatorRef.current += token
        setStreamingContent(streamAccumulatorRef.current)
      },
      () => {
        const final = streamAccumulatorRef.current
        if (final) {
          setMessages((prev) => [...prev, { role: 'assistant', content: final }])
        }
        setStreamingContent('')
        streamAccumulatorRef.current = ''
        setIsStreaming(false)
      },
      (err) => {
        setError(err)
        setIsStreaming(false)
        setStreamingContent('')
      }
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', maxWidth: '900px', margin: '0 auto', width: '100%' }}>
      <div style={{ padding: '0.75rem', borderBottom: '1px solid var(--border)' }}>
        <FileUpload onUploaded={() => {}} />
      </div>
      <MessageList messages={messages} streamingContent={streamingContent} isStreaming={isStreaming} />
      {error && (
        <div style={{ padding: '0.5rem 1rem', background: 'rgba(239,68,68,0.15)', color: '#f87171', fontSize: '0.9rem' }}>
          {error}
        </div>
      )}
      <div style={{ padding: '1rem', borderTop: '1px solid var(--border)' }}>
        <form
          onSubmit={(e) => { e.preventDefault(); send() }}
          style={{ display: 'flex', gap: '0.5rem' }}
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about market trends, sectors, or analyze uploaded files..."
            disabled={isStreaming}
            style={{
              flex: 1,
              padding: '0.75rem 1rem',
              borderRadius: '8px',
              border: '1px solid var(--border)',
              background: 'var(--surface)',
              color: 'var(--text)',
              fontSize: '1rem',
            }}
          />
          <button
            type="submit"
            disabled={isStreaming || !input.trim()}
            style={{
              padding: '0.75rem 1.25rem',
              background: isStreaming ? 'var(--border)' : 'var(--accent)',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: isStreaming ? 'not-allowed' : 'pointer',
              fontWeight: 600,
            }}
          >
            {isStreaming ? '…' : 'Send'}
          </button>
        </form>
      </div>
      <div ref={bottomRef} />
    </div>
  )
}
