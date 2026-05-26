import { useEffect, useRef } from 'react'

interface MessageProps {
  role: 'user' | 'assistant' | 'system'
  content: string
}

export function ChatMessage({ role, content }: MessageProps) {
  const roleColor = {
    user: 'bg-blue-600',
    assistant: 'bg-slate-700',
    system: 'bg-amber-600/80',
  }

  const roleLabel = {
    user: 'You',
    assistant: 'Agent',
    system: 'System',
  }

  return (
    <div className="mb-4 flex gap-3">
      <div className={`flex-shrink-0 w-8 h-8 rounded-full ${roleColor[role]} flex items-center justify-center text-xs font-bold text-white`}>
        {roleLabel[role].charAt(0)}
      </div>
      <div className="flex-1">
        <div className="text-xs text-slate-400 font-medium mb-1">{roleLabel[role]}</div>
        <div className="bg-slate-700 rounded p-3 text-slate-100 text-sm whitespace-pre-wrap break-words">
          {content}
        </div>
      </div>
    </div>
  )
}

interface ChatAreaProps {
  messages: MessageProps[]
  loading?: boolean
}

export function ChatArea({ messages, loading = false }: ChatAreaProps) {
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-900">
      {messages.length === 0 ? (
        <div className="h-full flex items-center justify-center text-center">
          <div>
            <p className="text-2xl font-bold text-slate-400 mb-2">No messages yet</p>
            <p className="text-slate-500 text-sm">Start a conversation to get started</p>
          </div>
        </div>
      ) : (
        <>
          {messages.map((msg, idx) => (
            <ChatMessage key={idx} {...msg} />
          ))}
          {loading && (
            <div className="mb-4 flex gap-3">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center">
                <div className="animate-spin">⚙️</div>
              </div>
              <div className="bg-slate-700 rounded p-3 text-slate-400">Thinking...</div>
            </div>
          )}
          <div ref={endRef} />
        </>
      )}
    </div>
  )
}
