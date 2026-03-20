'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { getSession, signOut } from '@/lib/supabase/client'
import { listChats, createChat, getMessages, sendMessage, type Chat, type Message } from '@/lib/api'
import ChatSidebar from '@/components/chat/ChatSidebar'
import ChatTimeline from '@/components/chat/ChatTimeline'
import ChatComposer from '@/components/chat/ChatComposer'

export default function ChatPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [chats, setChats] = useState<Chat[]>([])
  const [activeChat, setActiveChat] = useState<Chat | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [sending, setSending] = useState(false)

  useEffect(() => {
    checkAuthAndLoadChats()
  }, [])

  useEffect(() => {
    if (activeChat) {
      loadMessages(activeChat.id)
    }
  }, [activeChat])

  async function checkAuthAndLoadChats() {
    const session = await getSession()
    if (!session) {
      router.push('/login')
      return
    }

    await loadChats()
    setLoading(false)
  }

  async function loadChats() {
    try {
      const { chats: chatList } = await listChats()
      setChats(chatList)

      // Auto-select first chat or create new one
      if (chatList.length > 0) {
        setActiveChat(chatList[0])
      } else {
        await handleNewChat()
      }
    } catch (error) {
      console.error('Failed to load chats:', error)
    }
  }

  async function loadMessages(chatId: string) {
    try {
      const { messages: messageList } = await getMessages(chatId)
      setMessages(messageList)
    } catch (error) {
      console.error('Failed to load messages:', error)
    }
  }

  async function handleNewChat() {
    try {
      const newChat = await createChat('New Chat')
      setChats([newChat, ...chats])
      setActiveChat(newChat)
      setMessages([])
    } catch (error) {
      console.error('Failed to create chat:', error)
    }
  }

  async function handleSendMessage(content: string) {
    if (!activeChat || sending) return

    setSending(true)

    try {
      const response = await sendMessage(activeChat.id, content)

      // Add both messages to timeline
      setMessages([...messages, response.user_message, response.assistant_message])

      // Update chat title if it's the first message
      if (messages.length === 0) {
        const updatedChats = chats.map(c =>
          c.id === activeChat.id
            ? { ...c, title: content.slice(0, 50) }
            : c
        )
        setChats(updatedChats)
      }
    } catch (error) {
      console.error('Failed to send message:', error)
    } finally {
      setSending(false)
    }
  }

  async function handleSignOut() {
    await signOut()
    router.push('/login')
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-2">Loading JARVIS...</h1>
          <p className="text-gray-600">Please wait</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <ChatSidebar
        chats={chats}
        activeChat={activeChat}
        onSelectChat={setActiveChat}
        onNewChat={handleNewChat}
        onSignOut={handleSignOut}
      />

      {/* Main chat area */}
      <div className="flex-1 flex flex-col">
        {activeChat ? (
          <>
            {/* Header */}
            <div className="bg-white border-b px-6 py-4">
              <h2 className="text-lg font-semibold text-gray-800">
                {activeChat.title || 'New Chat'}
              </h2>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto">
              <ChatTimeline messages={messages} />
            </div>

            {/* Composer */}
            <div className="bg-white border-t p-4">
              <ChatComposer
                onSend={handleSendMessage}
                disabled={sending}
                placeholder="Message JARVIS..."
              />
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <h2 className="text-2xl font-bold mb-2">Welcome to JARVIS</h2>
              <p className="text-gray-600 mb-4">Start a new conversation</p>
              <button
                onClick={handleNewChat}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                New Chat
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
