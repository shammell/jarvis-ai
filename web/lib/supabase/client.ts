import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
const hasSupabaseConfig = Boolean(supabaseUrl && supabaseAnonKey)

export const supabase = hasSupabaseConfig
  ? createClient(supabaseUrl!, supabaseAnonKey!)
  : null

function getConfiguredSupabase() {
  if (!supabase) {
    throw new Error('Supabase is not configured. Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY.')
  }
  return supabase
}

export function isSupabaseConfigured() {
  return hasSupabaseConfig
}

export function getSupabaseConfigError() {
  if (hasSupabaseConfig) return null
  return 'Supabase config missing: NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY are required.'
}

export const supabaseClient = {
  auth: {
    getSession: (...args: Parameters<ReturnType<typeof getConfiguredSupabase>['auth']['getSession']>) => getConfiguredSupabase().auth.getSession(...args),
    signInWithPassword: (...args: Parameters<ReturnType<typeof getConfiguredSupabase>['auth']['signInWithPassword']>) => getConfiguredSupabase().auth.signInWithPassword(...args),
    signUp: (...args: Parameters<ReturnType<typeof getConfiguredSupabase>['auth']['signUp']>) => getConfiguredSupabase().auth.signUp(...args),
    signOut: (...args: Parameters<ReturnType<typeof getConfiguredSupabase>['auth']['signOut']>) => getConfiguredSupabase().auth.signOut(...args),
  },
}

export type AuthUser = {
  id: string
  email?: string
}

export async function getSession() {
  if (!supabase) return null
  const { data: { session } } = await supabaseClient.auth.getSession()
  return session
}

export async function signIn(email: string, password: string) {
  if (!supabase) {
    return { data: null, error: { message: getSupabaseConfigError() || 'Supabase not configured' } }
  }

  const { data, error } = await supabaseClient.auth.signInWithPassword({
    email,
    password,
  })
  return { data, error }
}

export async function signUp(email: string, password: string) {
  if (!supabase) {
    return { data: null, error: { message: getSupabaseConfigError() || 'Supabase not configured' } }
  }

  const { data, error } = await supabaseClient.auth.signUp({
    email,
    password,
  })
  return { data, error }
}

export async function signOut() {
  if (!supabase) {
    return { error: { message: getSupabaseConfigError() || 'Supabase not configured' } }
  }

  const { error } = await supabaseClient.auth.signOut()
  return { error }
}
