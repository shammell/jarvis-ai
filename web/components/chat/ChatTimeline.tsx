import { type Message } from '@/lib/api'

type Props = {
  messages: Message[]
}

export default function ChatTimeline({ messages }: Props) {
  if (messages.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        <p>No messages yet. Start the conversation!</p>
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto py-8 px-4 space-y-6">
      {messages.map((message) => (
        <div
          key={message.id}
          className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
        >
          <div
            className={`max-w-[80%] rounded-lg px-4 py-3 ${
              message.role === 'user'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-800 border border-gray-200'
            }`}
          >
            {/* Role label */}
            <div className="text-xs font-semibold mb-1 opacity-70">
              {message.role === 'user' ? 'You' : 'JARVIS'}
            </div>

            {/* Content */}
            <div className="whitespace-pre-wrap break-words">
              {message.content}
            </div>

            {/* Metadata (for assistant messages) */}
            {message.role === 'assistant' && message.metadata && (
              <div className="mt-2 pt-2 border-t border-gray-200 text-xs text-gray-500">
                {message.metadata.latency_ms && (
                  <span>Response time: {message.metadata.latency_ms}ms</span>
                )}
                {message.metadata.source && (
                  <span className="ml-3">Source: {message.metadata.source}</span>
                )}
              </div>
            )}

            {/* Timestamp */}
            <div className="text-xs mt-1 opacity-60">
              {new Date(message.created_at).toLocaleTimeString()}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
