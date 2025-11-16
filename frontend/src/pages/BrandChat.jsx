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

  const handleOptionSelect = (questionId, option) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: option
    }))
  }

  const handleSubmit = async () => {
    // Check if all questions are answered
    const allAnswered = QUESTIONS.every(q => answers[q.id])
    if (!allAnswered) {
      alert("Please answer all questions before continuing.")
      return
    }

    setLoading(true)
    try {
      const response = await api.submitCampaignAnswers(brandId, answers)
      if (!response?.creative_bible_id) {
        throw new Error("Invalid response: missing creative_bible_id")
      }
      navigate(`/brands/${brandId}/storyline/${response.creative_bible_id}`)
    } catch (error) {
      console.error("Failed to submit answers:", error)
      const errorMessage = error instanceof Error ? error.message : "Unknown error occurred"
      alert(`Failed to submit answers: ${errorMessage}. Please check the console for details.`)
    } finally {
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

            <div className="pt-6">
              <Button
                onClick={handleSubmit}
                disabled={loading || Object.keys(answers).length < QUESTIONS.length}
                className="w-full"
                size="lg"
              >
                {loading ? "Processing..." : "Continue to Storyline →"}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

