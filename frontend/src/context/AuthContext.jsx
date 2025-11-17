import { createContext, useContext, useEffect, useState } from "react"
import { supabase } from "../services/supabase"

const AuthContext = createContext()

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let mounted = true

    // Get initial session with error handling
    const initializeSession = async () => {
      try {
        const { data: { session }, error } = await supabase.auth.getSession()
        
        if (error) {
          console.error('Error getting session:', error)
          // Try to refresh the session
          try {
            const { data: refreshData, error: refreshError } = await supabase.auth.refreshSession()
            if (!refreshError && refreshData.session && mounted) {
              const refreshedUser = refreshData.session.user
              setUser(refreshedUser)
              console.log('Current user (refreshed):', refreshedUser ? { id: refreshedUser.id, email: refreshedUser.email } : null)
              setLoading(false)
              return
            }
          } catch (refreshErr) {
            console.error('Error refreshing session:', refreshErr)
          }
        }
        
        if (mounted) {
          const currentUser = session?.user ?? null
          setUser(currentUser)
          console.log('Current user:', currentUser ? { id: currentUser.id, email: currentUser.email } : null)
          setLoading(false)
        }
      } catch (err) {
        console.error('Exception getting session:', err)
        if (mounted) {
          setUser(null)
          setLoading(false)
        }
      }
    }

    initializeSession()

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, session) => {
      if (mounted) {
        const currentUser = session?.user ?? null
        setUser(currentUser)
        console.log('Auth state changed:', event, currentUser ? { id: currentUser.id, email: currentUser.email } : null)
        setLoading(false)
      }
    })

    return () => {
      mounted = false
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
      console.log('✅ Login successful!', { user: data.user ? { id: data.user.id, email: data.user.email } : null })
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
    console.log('✅ Google login initiated successfully')
    // OAuth redirects automatically, so we don't need to return data here
    return data
  }

  const logout = async () => {
    try {
      const { error } = await supabase.auth.signOut()
      if (error) {
        console.error('Logout error:', error)
        throw error
      }
      // Explicitly clear user state immediately
      setUser(null)
      setLoading(false)
    } catch (err) {
      console.error('Logout exception:', err)
      // Even if signOut fails, clear local state
      setUser(null)
      setLoading(false)
      throw err
    }
  }

  const value = {
    user,
    loginWithEmail,
    signupWithEmail,
    loginWithGoogle,
    logout,
    loading,
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

