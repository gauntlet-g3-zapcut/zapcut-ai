import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import { Button } from "../components/ui/button"
import { GradientButton } from "@/components/ui/gradient-button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import { Input } from "../components/ui/input"

export default function Login() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [loading, setLoading] = useState(false)
  const [isSignup, setIsSignup] = useState(false)
  const { user, loginWithEmail, signupWithEmail } = useAuth()
  const navigate = useNavigate()

  // Redirect if already logged in
  useEffect(() => {
    if (user) {
      navigate("/dashboard")
    }
  }, [user, navigate])

  const handleEmailSubmit = async (e) => {
    e.preventDefault()
    setError("")
    setSuccess("")
    setLoading(true)

    try {
      if (isSignup) {
        await signupWithEmail(email, password)
        setSuccess("Account created successfully! Please sign in.")
        setEmail("")
        setPassword("")
        setIsSignup(false)
      } else {
        await loginWithEmail(email, password)
        // Wait a moment for auth state to update
        setTimeout(() => {
          navigate("/dashboard")
        }, 100)
      }
    } catch (err) {
      console.error('Login form error:', err)
      setError(err.message || 'An error occurred. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 via-white to-pink-50 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-3xl font-bold" style={{ fontFamily: "'Playfair Display', serif" }}>
            {isSignup ? "Create your account" : "Welcome back"}
          </CardTitle>
          <CardDescription className="text-base">
            {isSignup 
              ? "Create an account to start creating amazing video ads"
              : "Sign in to start creating amazing video ads"
            }
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleEmailSubmit} className="space-y-4">
            {error && (
              <div className="bg-destructive/10 text-destructive text-sm p-3 rounded-md">
                {error}
              </div>
            )}
            {success && (
              <div className="bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-400 text-sm p-3 rounded-md">
                {success}
              </div>
            )}

            <div className="space-y-2">
              <label htmlFor="email" className="text-sm font-medium">
                Email
              </label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="password" className="text-sm font-medium">
                Password
              </label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            <GradientButton type="submit" className="w-full" disabled={loading}>
              {loading 
                ? (isSignup ? "Creating account..." : "Signing in...") 
                : (isSignup ? "Sign Up" : "Sign In")
              }
            </GradientButton>
          </form>

          <div className="mt-4 text-center text-sm">
            <span className="text-muted-foreground">
              {isSignup ? "Already have an account? " : "Don't have an account? "}
            </span>
            <button
              type="button"
              onClick={() => {
                setIsSignup(!isSignup)
                setError("")
                setSuccess("")
              }}
              className="text-primary hover:underline font-medium"
            >
              {isSignup ? "Sign In" : "Sign Up"}
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

