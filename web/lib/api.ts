import axios from 'axios'
import { getSession } from './supabase/client'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_URL,
})

// Add auth token to requests
api.interceptors.request.use(async (config) => {
  const session = await getSession()
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`
  }
  return config
})

export type Chat = {
  id: string
  user_id: string
  title: string | null
  created_at: string
  updated_at: string
  archived: boolean
}

export type Message = {
  id: string
  chat_id: string
  user_id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  metadata?: Record<string, any>
  created_at: string
}

export type SendMessageResponse = {
  user_message: Message
  assistant_message: Message
}

// Chat API
export async function createChat(title?: string): Promise<Chat> {
  const { data } = await api.post('/api/v1/chats', { title })
  return data
}

export async function listChats(limit = 50, offset = 0): Promise<{ chats: Chat[], total: number }> {
  const { data } = await api.get('/api/v1/chats', { params: { limit, offset } })
  return data
}

export async function getMessages(chatId: string, limit = 50, offset = 0): Promise<{ messages: Message[], total: number, has_more: boolean }> {
  const { data } = await api.get(`/api/v1/chats/${chatId}/messages`, { params: { limit, offset } })
  return data
}

export async function sendMessage(chatId: string, content: string): Promise<SendMessageResponse> {
  const { data } = await api.post(`/api/v1/chats/${chatId}/messages`, { content })
  return data
}

export async function deleteChat(chatId: string): Promise<void> {
  await api.delete(`/api/v1/chats/${chatId}`)
}

// Stream message (SSE)
export function streamMessage(chatId: string, content: string, onChunk: (chunk: string) => void, onEnd: (metadata?: any) => void, onError: (error: string) => void) {
  return new Promise<void>(async (resolve, reject) => {
    try {
      const session = await getSession()
      const token = session?.access_token

      const response = await fetch(`${API_URL}/api/v1/chats/${chatId}/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ content }),
      })

      if (!response.ok) {
        throw new Error('Stream request failed')
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('No reader available')
      }

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6))

            if (data.type === 'chunk') {
              onChunk(data.content)
            } else if (data.type === 'end') {
              onEnd(data.metadata)
            } else if (data.type === 'error') {
              onError(data.content)
            }
          }
        }
      }

      resolve()
    } catch (error: any) {
      onError(error.message)
      reject(error)
    }
  })
}

export default api
