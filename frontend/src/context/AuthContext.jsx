import { createContext, useContext, useEffect, useState } from "react"
import {
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut,
  onAuthStateChanged,
} from "firebase/auth"
import { auth, googleProvider } from "../services/firebase"

const AuthContext = createContext()

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      setUser(user)
      setLoading(false)
    })

    return () => unsubscribe()
  }, [])

  const loginWithEmail = async (email, password) => {
    return await signInWithEmailAndPassword(auth, email, password)
  }

  const loginWithGoogle = async () => {
    return await signInWithPopup(auth, googleProvider)
  }

  const logout = async () => {
    return await signOut(auth)
  }

  const value = {
    user,
    loginWithEmail,
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

