'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { getSession, getSupabaseConfigError } from '@/lib/supabase/client'

export default function Home() {
  const router = useRouter()

  useEffect(() => {
    checkAuth()
  }, [])

  async function checkAuth() {
    const configError = getSupabaseConfigError()
    if (configError) {
      router.push('/login')
      return
    }

    const session = await getSession()
    if (session) {
      router.push('/chat')
    } else {
      router.push('/login')
    }
  }

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">JARVIS</h1>
        <p className="text-gray-600">Loading...</p>
      </div>
    </div>
  )
}
