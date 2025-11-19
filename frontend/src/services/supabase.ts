import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables')
}

export const SUPABASE_STORAGE_KEY = 'supabase.auth.token'
const STORAGE_VERSION_KEY = 'supabase.storage.version'
const STORAGE_VERSION = 'v2'
const EXPECTED_JWT_ALG =
  typeof import.meta.env.VITE_SUPABASE_JWT_ALG === 'string'
    ? (import.meta.env.VITE_SUPABASE_JWT_ALG as string)
    : undefined

// Debug flag - controls GoTrueClient and custom auth logging
//
// To enable debug mode:
// 1. In browser console: localStorage.setItem('DEBUG_AUTH', 'true')
// 2. Refresh the page
// 3. Auth logs will now appear in console
//
// To disable:
// localStorage.removeItem('DEBUG_AUTH') and refresh
//
// Or set VITE_DEBUG_AUTH=true in .env file
export const DEBUG_AUTH =
  (typeof window !== 'undefined' && localStorage.getItem('DEBUG_AUTH') === 'true') ||
  import.meta.env.VITE_DEBUG_AUTH === 'true'

const safeJsonParse = <T>(value: string | null): T | null => {
  if (!value) return null
  try {
    return JSON.parse(value) as T
  } catch (error) {
    if (DEBUG_AUTH) {
      console.warn('[Auth] Failed to parse JSON from storage', error)
    }
    return null
  }
}

const decodeJwtHeader = (token: string): Record<string, unknown> | null => {
  if (typeof window === 'undefined') return null

  try {
    const [encodedHeader] = token.split('.')
    if (!encodedHeader) return null
    const normalized = encodedHeader.replace(/-/g, '+').replace(/_/g, '/')
    const headerJson = window.atob(normalized)
    return JSON.parse(headerJson)
  } catch (error) {
    if (DEBUG_AUTH) {
      console.warn('[Auth] Failed to decode JWT header', error)
    }
    return null
  }
}

export interface StoredSupabaseSession {
  access_token: string
  refresh_token?: string
  expires_at?: number
  user?: Record<string, unknown>
}

export const readSupabaseSessionFromStorage = (): StoredSupabaseSession | null => {
  if (typeof window === 'undefined') {
    return null
  }

  const raw = window.localStorage.getItem(SUPABASE_STORAGE_KEY)
  const parsed = safeJsonParse<{ currentSession?: unknown; session?: unknown; access_token?: string }>(raw)

  const sessionData = (parsed?.currentSession ?? parsed?.session ?? parsed) as Record<string, unknown> | null

  if (!sessionData) {
    return null
  }

  const maybeUser = sessionData.user as Record<string, unknown> | undefined
  const access_token = sessionData.access_token as string | undefined
  const refresh_token = sessionData.refresh_token as string | undefined
  const expires_at = sessionData.expires_at as number | undefined

  if (!access_token) {
    return null
  }

  return {
    access_token,
    refresh_token,
    expires_at,
    user: maybeUser,
  }
}

export const clearSupabaseAuthStorage = () => {
  if (typeof window === 'undefined') return
  const keysToClear: string[] = []

  Object.keys(window.localStorage).forEach((storageKey) => {
    if (storageKey.startsWith('supabase') || storageKey.includes('auth')) {
      keysToClear.push(storageKey)
    }
  })

  keysToClear.forEach((key) => window.localStorage.removeItem(key))
}

// Log debug status on load
if (typeof window !== 'undefined' && DEBUG_AUTH) {
  console.log('[Auth] Debug mode enabled. Auth logs will be visible.')
}

// Storage migration - MUST run BEFORE creating client to clear stale tokens
if (typeof window !== 'undefined') {
  try {
    const storage = window.localStorage
    const currentVersion = storage.getItem(STORAGE_VERSION_KEY)
    let needsMigration = currentVersion !== STORAGE_VERSION
    const reasons: string[] = []

    if (!needsMigration) {
      const storedSession = readSupabaseSessionFromStorage()
      if (storedSession?.access_token) {
        const header = decodeJwtHeader(storedSession.access_token)
        const detectedAlg = typeof header?.alg === 'string' ? (header.alg as string) : undefined

        if (EXPECTED_JWT_ALG && detectedAlg && detectedAlg !== EXPECTED_JWT_ALG) {
          needsMigration = true
          reasons.push(`token algorithm ${detectedAlg} differs from expected ${EXPECTED_JWT_ALG}`)
        } else if (!detectedAlg && DEBUG_AUTH) {
          console.warn('[Auth] Unable to determine stored token algorithm; leaving session untouched')
        }
      }
    }

    if (needsMigration) {
      if (DEBUG_AUTH) {
        console.warn('[Auth] Clearing Supabase auth storage', { reasons, currentVersion, targetVersion: STORAGE_VERSION })
      }

      Object.keys(storage).forEach((storageKey) => {
        if (storageKey.startsWith('supabase') || storageKey.includes('auth')) {
          storage.removeItem(storageKey)
        }
      })

      storage.setItem(STORAGE_VERSION_KEY, STORAGE_VERSION)
    } else if (!currentVersion) {
      // Ensure we mark the version once even if no migration occurred
      storage.setItem(STORAGE_VERSION_KEY, STORAGE_VERSION)
    }
  } catch (error) {
    console.warn('[Auth] Storage migration skipped', error)
  }
}

// Configure Supabase client with explicit auth options
export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
    flowType: 'pkce',
    storage: typeof window !== 'undefined' ? window.localStorage : undefined,
    storageKey: SUPABASE_STORAGE_KEY,
    debug: DEBUG_AUTH, // Only log GoTrueClient messages when DEBUG_AUTH is enabled
  },
})

