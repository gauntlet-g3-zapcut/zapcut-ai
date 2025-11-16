import { createContext, useContext, useEffect, useState } from "react"
import { supabase } from "../services/supabase"

const AuthContext = createContext()

export function AuthProvider({ children }) {
  // Skip authentication - provide mock user immediately
  const [user, setUser] = useState({
    id: "mock-user-123",
    email: "dev@example.com"
  })
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    // Skip Supabase auth completely
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
      console.log('Login successful:', data?.user?.email)
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
      console.log('Signup successful:', data?.user?.email)
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
    const { error } = await supabase.auth.signOut()
    if (error) throw error
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

