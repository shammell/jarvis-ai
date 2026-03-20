import { type Chat } from '@/lib/api'

type Props = {
  chats: Chat[]
  activeChat: Chat | null
  onSelectChat: (chat: Chat) => void
  onNewChat: () => void
  onSignOut: () => void
}

export default function ChatSidebar({ chats, activeChat, onSelectChat, onNewChat, onSignOut }: Props) {
  return (
    <div className="w-64 bg-gray-900 text-white flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <h1 className="text-xl font-bold">JARVIS</h1>
      </div>

      {/* New chat button */}
      <div className="p-4">
        <button
          onClick={onNewChat}
          className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 rounded-md font-medium transition-colors"
        >
          + New Chat
        </button>
      </div>

      {/* Chat list */}
      <div className="flex-1 overflow-y-auto">
        {chats.map((chat) => (
          <button
            key={chat.id}
            onClick={() => onSelectChat(chat)}
            className={`w-full text-left px-4 py-3 hover:bg-gray-800 transition-colors ${
              activeChat?.id === chat.id ? 'bg-gray-800' : ''
            }`}
          >
            <div className="truncate text-sm">
              {chat.title || 'New Chat'}
            </div>
            <div className="text-xs text-gray-400 mt-1">
              {new Date(chat.updated_at).toLocaleDateString()}
            </div>
          </button>
        ))}
      </div>

      {/* Sign out */}
      <div className="p-4 border-t border-gray-700">
        <button
          onClick={onSignOut}
          className="w-full py-2 px-4 text-sm text-gray-300 hover:text-white hover:bg-gray-800 rounded-md transition-colors"
        >
          Sign Out
        </button>
      </div>
    </div>
  )
}
