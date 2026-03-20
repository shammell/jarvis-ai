import { useState, KeyboardEvent } from 'react'

type Props = {
  onSend: (content: string) => void
  disabled?: boolean
  placeholder?: string
}

export default function ChatComposer({ onSend, disabled, placeholder }: Props) {
  const [input, setInput] = useState('')

  function handleSend() {
    if (input.trim() && !disabled) {
      onSend(input.trim())
      setInput('')
    }
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="max-w-3xl mx-auto w-full">
      <div className="flex items-end gap-2">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder || 'Type a message...'}
          disabled={disabled}
          rows={1}
          className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none disabled:opacity-50 disabled:cursor-not-allowed"
          style={{ minHeight: '48px', maxHeight: '200px' }}
        />
        <button
          onClick={handleSend}
          disabled={disabled || !input.trim()}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
        >
          {disabled ? 'Sending...' : 'Send'}
        </button>
      </div>
      <p className="text-xs text-gray-500 mt-2">
        Press Enter to send, Shift+Enter for new line
      </p>
    </div>
  )
}
