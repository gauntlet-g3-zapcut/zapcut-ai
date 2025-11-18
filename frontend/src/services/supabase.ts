import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables')
}

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

// Log debug status on load
if (typeof window !== 'undefined' && DEBUG_AUTH) {
  console.log('[Auth] Debug mode enabled. Auth logs will be visible.')
}

// Storage migration - MUST run BEFORE creating client to clear stale tokens
if (typeof window !== 'undefined') {
  const STORAGE_VERSION = 'v2' // bump this when changing storage logic
  const key = 'supabase.storage.version'

  try {
    const current = localStorage.getItem(key)
    let needsMigration = current !== STORAGE_VERSION
    
    // Also check for HS256 tokens even if version matches (defensive)
    if (!needsMigration) {
      const sessionKey = 'supabase.auth.token'
      const stored = localStorage.getItem(sessionKey)
      if (stored) {
        try {
          const sessionData = JSON.parse(stored)
          const accessToken = sessionData?.access_token
          if (accessToken) {
            // Check token algorithm
            try {
              const header = JSON.parse(atob(accessToken.split('.')[0].replace(/-/g, '+').replace(/_/g, '/')))
              if (header.alg && header.alg !== 'RS256') {
                console.warn('Found HS256 token in storage, forcing migration')
                needsMigration = true
              }
            } catch {
              // If we can't parse, clear it anyway
              needsMigration = true
            }
          }
        } catch {
          // Corrupted session data
          needsMigration = true
        }
      }
    }
    
    if (needsMigration) {
      // remove only supabase/auth related keys BEFORE client loads them
      Object.keys(localStorage).forEach(k => {
        if (k.startsWith('supabase') || k.includes('auth')) {
          localStorage.removeItem(k)
        }
      })
      localStorage.setItem(key, STORAGE_VERSION)
      // Storage migration completed
    }
  } catch (e) {
    // ignore storage errors (private mode etc.)
    console.warn('Storage migration skipped', e)
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
    storageKey: 'supabase.auth.token',
    debug: DEBUG_AUTH  // Only log GoTrueClient messages when DEBUG_AUTH is enabled
  }
})

