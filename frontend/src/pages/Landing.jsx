import { useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import { GradientButton } from "@/components/ui/gradient-button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"

export default function Landing() {
  const { user } = useAuth()
  const navigate = useNavigate()

  // Redirect if already logged in
  useEffect(() => {
    if (user) {
      navigate("/dashboard")
    }
  }, [user, navigate])

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-pink-50 flex items-center">
      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-10">
          <h1 className="text-6xl font-bold mb-4 text-black" style={{ fontFamily: "'Playfair Display', serif" }}>
            Create a winning ad in <span className="italic">minutes</span>
          </h1>
          <p className="text-base text-muted-foreground mb-8 max-w-2xl mx-auto">
            Create stunning 4K video ads with AI. Generate professional product videos
            with music in minutes, not hours.
          </p>
          <GradientButton
            onClick={() => navigate("/login")}
          >
            Get Started
          </GradientButton>
        </div>

        <div className="grid md:grid-cols-3 gap-8 mt-20">
          <Card>
            <CardHeader className="space-y-0 pb-0">
              <CardTitle className="text-center mb-4" style={{ fontFamily: "'Playfair Display', serif" }}>AI-Powered</CardTitle>
              <CardDescription className="mt-0 mb-0">
                Let our Creative Director AI guide you through the process
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-0 px-6 pb-6">
              <p className="text-sm text-muted-foreground mt-4">
                Chat with our AI to define your ad style, and watch it create
                a complete video production.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="space-y-0 pb-0">
              <CardTitle className="text-center mb-4" style={{ fontFamily: "'Playfair Display', serif" }}>4K Quality</CardTitle>
              <CardDescription className="mt-0 mb-0">
                Professional-grade video output
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-0 px-6 pb-6">
              <p className="text-sm text-muted-foreground mt-4">
                Generate 4K video ads with matching soundtracks, ready for
                any platform.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="space-y-0 pb-0">
              <CardTitle className="text-center mb-4" style={{ fontFamily: "'Playfair Display', serif" }}>Fast & Easy</CardTitle>
              <CardDescription className="mt-0 mb-0">
                From concept to video in under 5 minutes
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-0 px-6 pb-6">
              <p className="text-sm text-muted-foreground mt-4">
                No video editing skills required. Just describe your vision
                and we'll bring it to life.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

