import { useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { Button } from "../components/ui/button"
import { GradientButton } from "../components/ui/gradient-button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import { Textarea } from "../components/ui/textarea"
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
  const [ideas, setIdeas] = useState("")
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
      // Include ideas in the submission
      const submissionData = {
        ...answers,
        ideas: ideas.trim() || ""
      }

      const response = await api.submitCampaignAnswers(brandId, submissionData)
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
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-pink-50 p-4 sm:p-6 lg:p-8">
      <div className="max-w-4xl mx-auto">
        <Button
          variant="ghost"
          onClick={() => navigate("/dashboard")}
          className="mb-6 hover:bg-white/50 transition-colors"
        >
          ← Back to Dashboard
        </Button>

        <Card className="shadow-lg bg-white/80 backdrop-blur-sm">
          <CardHeader className="pb-4 border-b border-purple-100">
            <CardTitle className="text-3xl font-bold" style={{ fontFamily: "'Playfair Display', serif" }}>
              Create New Campaign
            </CardTitle>
            <CardDescription className="text-base mt-2">
              Select your preferences for your video ad campaign
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-8 pt-6">
            {QUESTIONS.map((question, qIndex) => (
              <div key={question.id} className="space-y-3">
                <h3 className="text-lg font-semibold text-foreground">
                  {qIndex + 1}. {question.question}
                </h3>
                <div className="grid grid-cols-1 gap-2">
                  {question.options.map((option) => (
                    <Button
                      key={option}
                      onClick={() => handleOptionSelect(question.id, option)}
                      variant={answers[question.id] === option ? "default" : "outline"}
                      className={`w-full justify-start text-left h-auto py-3 transition-all ${
                        answers[question.id] === option
                          ? "bg-purple-600 text-white hover:bg-purple-700 border-purple-600"
                          : "hover:bg-purple-50 hover:border-purple-300"
                      }`}
                    >
                      {option}
                    </Button>
                  ))}
                </div>
              </div>
            ))}

            {/* Additional Ideas Field */}
            <div className="space-y-3 pt-4">
              <h3 className="text-lg font-semibold text-foreground">
                6. Any specific ideas or concepts you want to include? (Optional)
              </h3>
              <Textarea
                value={ideas}
                onChange={(e) => setIdeas(e.target.value)}
                placeholder="Share any specific scenes, messages, or creative ideas you have in mind..."
                className="min-h-[120px] resize-y border-purple-200 focus:border-purple-400 focus:ring-purple-400"
              />
              <p className="text-sm text-muted-foreground">
                Feel free to describe any specific moments, visuals, or messages you'd like to see in your ad.
              </p>
            </div>

            <div className="pt-6">
              <GradientButton
                onClick={handleSubmit}
                disabled={loading || Object.keys(answers).length < QUESTIONS.length}
                className="w-full h-12 text-base"
              >
                {loading ? "Processing..." : "Continue to Storyline →"}
              </GradientButton>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
