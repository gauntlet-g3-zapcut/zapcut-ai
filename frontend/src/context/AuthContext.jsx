import { createContext, useContext, useEffect, useRef, useState } from "react"
import {
  supabase,
  readSupabaseSessionFromStorage,
  clearSupabaseAuthStorage,
  DEBUG_AUTH,
} from "../services/supabase"

const AuthContext = createContext()

const TOKEN_REFRESH_BUFFER_MS = 60 * 1000 // refresh 60s before expiry
const MIN_REFRESH_INTERVAL_MS = 15 * 1000 // clamp refresh timer to avoid extremely short intervals
const hasWindow = typeof window !== "undefined"
const persistedSnapshot = hasWindow ? readSupabaseSessionFromStorage() : null
const initialUser = persistedSnapshot?.user ?? null

export function AuthProvider({ children }) {
  const [user, setUser] = useState(initialUser)
  const [loading, setLoading] = useState(true)
  const sessionRef = useRef(null)
  const refreshTimerRef = useRef(null)

  function clearRefreshTimer() {
    if (refreshTimerRef.current) {
      clearTimeout(refreshTimerRef.current)
      refreshTimerRef.current = null
    }
  }

  function shouldRefreshSoon(session) {
    if (!session?.expires_at) return false
    const expiresAtMs = session.expires_at * 1000
    return expiresAtMs - Date.now() <= TOKEN_REFRESH_BUFFER_MS
  }

  function scheduleSessionRefresh(session) {
    if (!hasWindow || !session?.expires_at) return

    const expiresAtMs = session.expires_at * 1000
    const now = Date.now()
    const refreshIn = Math.max(expiresAtMs - now - TOKEN_REFRESH_BUFFER_MS, MIN_REFRESH_INTERVAL_MS)

    if (DEBUG_AUTH) {
      console.log("[Auth] Scheduling session refresh", {
        expiresAt: session.expires_at,
        inMs: refreshIn,
      })
    }

    clearRefreshTimer()

    refreshTimerRef.current = window.setTimeout(async () => {
      try {
        const { data, error } = await supabase.auth.refreshSession()
        if (error) {
          throw error
        }

        if (data?.session) {
          handleSessionUpdate(data.session, { reason: "auto-refresh" })
        } else {
          handleSessionUpdate(null, { reason: "auto-refresh-empty" })
        }
      } catch (err) {
        console.error("[Auth] Automatic session refresh failed:", err)
        handleSessionUpdate(null, { reason: "auto-refresh-error" })
      }
    }, refreshIn)
  }

  function handleSessionUpdate(session, { reason } = {}) {
    if (DEBUG_AUTH) {
      console.log("[Auth] Session update", {
        reason,
        hasSession: !!session,
        expiresAt: session?.expires_at,
      })
    }

    clearRefreshTimer()
    sessionRef.current = session ?? null

    if (session?.user) {
      setUser(session.user)
      scheduleSessionRefresh(session)
    } else {
      setUser(null)
    }
  }

  useEffect(() => {
    let mounted = true

    const initializeSession = async () => {
      try {
        const {
          data: { session },
          error,
        } = await supabase.auth.getSession()

        let activeSession = session ?? null

        if (error) {
          console.error("[Auth] Error getting session:", error)
        }

        // Attempt to restore from localStorage when Supabase client returns null on boot
        if (!activeSession) {
          const stored = readSupabaseSessionFromStorage()
          if (stored?.refresh_token) {
            try {
              const { data: setData, error: setError } = await supabase.auth.setSession({
                access_token: stored.access_token,
                refresh_token: stored.refresh_token,
              })
              if (setError) {
                console.error("[Auth] Failed to set session from storage:", setError)
              } else if (setData?.session) {
                activeSession = setData.session
              }
            } catch (setErr) {
              console.error("[Auth] Exception restoring session from storage:", setErr)
            }
          }
        }

        // Ensure the recovered session is fresh enough before using it
        if (activeSession && shouldRefreshSoon(activeSession)) {
          try {
            const { data: refreshed, error: refreshError } = await supabase.auth.refreshSession()
            if (refreshError) {
              console.error("[Auth] Error refreshing near-expiry session:", refreshError)
            } else if (refreshed?.session) {
              activeSession = refreshed.session
            }
          } catch (refreshErr) {
            console.error("[Auth] Exception during session refresh:", refreshErr)
          }
        }

        if (mounted) {
          handleSessionUpdate(activeSession, { reason: "bootstrap" })
        }
      } catch (err) {
        console.error("[Auth] Exception initializing session:", err)
        if (mounted) {
          handleSessionUpdate(null, { reason: "bootstrap-error" })
        }
      }
      if (mounted) {
        setLoading(false)
      }
    }

    initializeSession()

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, session) => {
      if (mounted) {
        if (event === "SIGNED_OUT") {
          clearSupabaseAuthStorage()
        }

        handleSessionUpdate(session ?? null, { reason: event })
        setLoading(false)
      }
    })

    return () => {
      mounted = false
      clearRefreshTimer()
      subscription.unsubscribe()
    }
  }, [])

  const loginWithEmail = async (email, password) => {
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      })
      if (error) {
        console.error('Login error:', error)
        throw new Error(error.message || 'Failed to sign in')
      }
      return data
    } catch (err) {
      console.error('Login exception:', err)
      throw err
    }
  }

  const signupWithEmail = async (email, password) => {
    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
      })
      if (error) {
        console.error('Signup error:', error)
        throw new Error(error.message || 'Failed to create account')
      }
      return data
    } catch (err) {
      console.error('Signup exception:', err)
      throw err
    }
  }

  const loginWithGoogle = async () => {
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: `${window.location.origin}/dashboard`,
      },
    })
    if (error) throw error
    // OAuth redirects automatically, so we don't need to return data here
    return data
  }

  const logout = async () => {
    clearRefreshTimer()
    const { error } = await supabase.auth.signOut()
    if (error) {
      throw error
    }
    clearSupabaseAuthStorage()
    handleSessionUpdate(null, { reason: "manual-logout" })
  }

  const refreshSession = async () => {
    const { data, error } = await supabase.auth.refreshSession()
    if (error) {
      throw error
    }
    handleSessionUpdate(data?.session ?? null, { reason: "manual-refresh" })
    return data?.session ?? null
  }

  const getAccessToken = async () => {
    const {
      data: { session },
      error,
    } = await supabase.auth.getSession()

    if (error) {
      throw error
    }

    let activeSession = session ?? sessionRef.current

    if (!activeSession) {
      throw new Error("User not authenticated")
    }

    if (shouldRefreshSoon(activeSession)) {
      const { data: refreshed, error: refreshError } = await supabase.auth.refreshSession()
      if (refreshError) {
        await supabase.auth.signOut()
        clearSupabaseAuthStorage()
        handleSessionUpdate(null, { reason: "refresh-failed" })
        throw refreshError
      }

      if (!refreshed?.session) {
        await supabase.auth.signOut()
        clearSupabaseAuthStorage()
        handleSessionUpdate(null, { reason: "refresh-empty" })
        throw new Error("Session refresh failed")
      }

      activeSession = refreshed.session
      handleSessionUpdate(activeSession, { reason: "token-refresh" })
    }

    return activeSession.access_token
  }

  const value = {
    user,
    loginWithEmail,
    signupWithEmail,
    loginWithGoogle,
    logout,
    loading,
    refreshSession,
    getAccessToken,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider")
  }
  return context
}

