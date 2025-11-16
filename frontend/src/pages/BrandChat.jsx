import { useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { Button } from "../components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import { api } from "../services/api"

const QUESTIONS = [
  {
    id: "style",
    question: "How do you want this ad to look and feel?",
    options: ["Modern & Sleek", "Energetic & Fun", "Luxurious & Sophisticated", "Minimal & Clean", "Bold & Dramatic"]
  },
  {
    id: "audience",
    question: "Who is your target audience?",
    options: ["Young Adults (18-25)", "Professionals (25-40)", "Families", "Seniors (50+)", "Everyone"]
  },
  {
    id: "emotion",
    question: "What's the key message or emotion you want viewers to feel?",
    options: ["Excitement", "Trust & Reliability", "Joy & Happiness", "Luxury & Prestige", "Innovation"]
  },
  {
    id: "pacing",
    question: "What should be the pacing and energy?",
    options: ["Fast-paced & Exciting", "Slow & Elegant", "Dynamic Build-up", "Steady & Calm"]
  },
  {
    id: "colors",
    question: "What colors or visual style do you prefer?",
    options: ["Bold & Vibrant", "Dark & Moody", "Light & Airy", "Natural & Earthy", "Match Product Colors"]
  }
]

export default function BrandChat() {
  const { brandId } = useParams()
  const navigate = useNavigate()
  const [answers, setAnswers] = useState({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleOptionSelect = (questionId, option) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: option
    }))
    // Clear error when user makes a selection
    if (error) setError(null)
  }

  // Check if all questions are answered
  const allQuestionsAnswered = QUESTIONS.every(q => answers[q.id])
  const answeredCount = QUESTIONS.filter(q => answers[q.id]).length

  const handleSubmit = async () => {
    console.log("\n" + "=".repeat(80))
    console.log("🚀 BRAND CHAT - Continue to Storyline button clicked")
    console.log("=".repeat(80))

    // Double-check validation before submitting
    if (!allQuestionsAnswered) {
      console.log("❌ Validation failed: Not all questions answered")
      console.log(`   Answered: ${answeredCount}/${QUESTIONS.length}`)
      setError(`Please answer all ${QUESTIONS.length} questions (${answeredCount}/${QUESTIONS.length} answered)`)
      return
    }

    console.log("✅ Validation passed")
    console.log(`   Brand ID: ${brandId}`)
    console.log(`   Answers:`, answers)

    setLoading(true)
    setError(null)

    try {
      console.log("\n📤 Step 1: Calling createCreativeBible API...")

      // Call backend to generate creative bible from answers
      const response = await api.createCreativeBible(brandId, answers)

      console.log("✅ Step 1 Success: Creative bible created")
      console.log(`   Creative Bible ID: ${response.creative_bible_id}`)

      console.log("\n📤 Step 2: Navigating to storyline review page...")
      const targetUrl = `/brands/${brandId}/storyline/${response.creative_bible_id}`
      console.log(`   Target URL: ${targetUrl}`)

      // Navigate to storyline review with the creative_bible_id
      navigate(targetUrl)

      console.log("✅ Step 2 Success: Navigation initiated")
      console.log("=".repeat(80) + "\n")
    } catch (error) {
      console.error("\n" + "=".repeat(80))
      console.error("❌ ERROR in handleSubmit")
      console.error("=".repeat(80))
      console.error("   Error type:", error.constructor.name)
      console.error("   Error message:", error.message)
      console.error("   Full error:", error)
      if (error.stack) {
        console.error("   Stack trace:", error.stack)
      }
      console.error("=".repeat(80) + "\n")

      // Show error to user instead of silent fallback
      const errorMessage = error.message || "Failed to save your preferences. Please try again."
      setError(errorMessage)
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-4xl mx-auto">
        <Button
          variant="ghost"
          onClick={() => navigate("/dashboard")}
          className="mb-6"
        >
          ← Back to Dashboard
        </Button>

        <Card>
          <CardHeader>
            <CardTitle className="text-3xl">Create New Campaign</CardTitle>
            <CardDescription>
              Select your preferences for your video ad campaign
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-8">
            {QUESTIONS.map((question, qIndex) => (
              <div key={question.id} className="space-y-3">
                <h3 className="text-lg font-medium">
                  {qIndex + 1}. {question.question}
                </h3>
                <div className="grid grid-cols-1 gap-2">
                  {question.options.map((option) => (
                    <Button
                      key={option}
                      onClick={() => handleOptionSelect(question.id, option)}
                      variant={answers[question.id] === option ? "default" : "outline"}
                      className="w-full justify-start text-left h-auto py-3"
                    >
                      {option}
                    </Button>
                  ))}
                </div>
              </div>
            ))}

            <div className="pt-6 space-y-4">
              {error && (
                <div className="bg-destructive/15 text-destructive px-4 py-3 rounded-md text-sm">
                  {error}
                </div>
              )}

              {!allQuestionsAnswered && !error && (
                <div className="bg-muted px-4 py-3 rounded-md text-sm text-muted-foreground">
                  Please answer all questions to continue ({answeredCount}/{QUESTIONS.length} answered)
                </div>
              )}

              <Button
                onClick={handleSubmit}
                className="w-full"
                size="lg"
                disabled={loading || !allQuestionsAnswered}
              >
                {loading ? "Creating your creative bible..." :
                 !allQuestionsAnswered ? `Answer all questions (${answeredCount}/${QUESTIONS.length})` :
                 "Continue to Storyline →"}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

