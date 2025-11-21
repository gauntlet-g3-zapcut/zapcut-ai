import { useState, useEffect } from "react"
import { useNavigate, useParams, useSearchParams } from "react-router-dom"
import { Button } from "../components/ui/button"
import { GradientButton } from "../components/ui/gradient-button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import { Textarea } from "../components/ui/textarea"
import { api } from "../services/api"
import type { Question, QuestionId, CampaignAnswers, SubmitCampaignAnswersResponse } from "../types/campaign"
import { Loader2 } from "lucide-react"
import { ImageUploader, ImageGallery } from "../components/images"
import type { ImageMetadata } from "../types/image"

const QUESTIONS: readonly Question[] = [
  {
    id: "style",
    question: "How do you want this ad to look and feel?",
    options: ["Modern & Sleek", "Energetic & Fun", "Luxurious & Sophisticated", "Minimal & Clean", "Bold & Dramatic"] as const
  },
  {
    id: "audience",
    question: "Who is your target audience?",
    options: ["Young Adults (18-25)", "Professionals (25-40)", "Families", "Seniors (50+)", "Everyone"] as const
  },
  {
    id: "emotion",
    question: "What's the key message or emotion you want viewers to feel?",
    options: ["Excitement", "Trust & Reliability", "Joy & Happiness", "Luxury & Prestige", "Innovation"] as const
  },
  {
    id: "pacing",
    question: "What should be the pacing and energy?",
    options: ["Fast-paced & Exciting", "Slow & Elegant", "Dynamic Build-up", "Steady & Calm"] as const
  },
  {
    id: "colors",
    question: "What colors or visual style do you prefer?",
    options: ["Bold & Vibrant", "Dark & Moody", "Light & Airy", "Natural & Earthy", "Match Product Colors"] as const
  }
] as const

const MAX_IDEAS_LENGTH = 2000

export default function CampaignPreferences() {
  const { brandId } = useParams<{ brandId: string }>()
  const [searchParams] = useSearchParams()
  const creativeBibleId = searchParams.get("creativeBibleId")
  const existingCampaignId = searchParams.get("campaignId")  // For edit mode - reuse existing campaign
  const navigate = useNavigate()
  const [answers, setAnswers] = useState<CampaignAnswers>({})
  const [ideas, setIdeas] = useState<string>("")
  const [selectedImages, setSelectedImages] = useState<File[]>([])
  const [existingImages, setExistingImages] = useState<ImageMetadata[]>([])
  const [loading, setLoading] = useState<boolean>(false)
  const [initialLoading, setInitialLoading] = useState<boolean>(false)

  // Load existing campaign data (preferences and images) if editing
  useEffect(() => {
    const loadExistingData = async () => {
      // In edit mode, we have a campaignId - use that to load data quickly
      if (!existingCampaignId) return

      setInitialLoading(true)
      try {
        console.log("[CampaignPreferences] Loading campaign data for:", existingCampaignId)

        // Load campaign and images in parallel for speed
        const [campaignResponse, imagesResponse] = await Promise.all([
          api.getCampaign<{ campaign_preferences?: Record<string, string> }>(existingCampaignId),
          api.getCampaignImages<ImageMetadata[]>(existingCampaignId)
        ])

        console.log("[CampaignPreferences] Campaign response:", campaignResponse)
        console.log("[CampaignPreferences] Images response:", imagesResponse)

        // Load preferences from campaign
        const prefs = campaignResponse.campaign_preferences
        if (prefs) {
          console.log("[CampaignPreferences] Found preferences:", prefs)
          const loadedAnswers: CampaignAnswers = {}
          if (prefs.style) loadedAnswers.style = prefs.style
          if (prefs.audience) loadedAnswers.audience = prefs.audience
          if (prefs.emotion) loadedAnswers.emotion = prefs.emotion
          if (prefs.pacing) loadedAnswers.pacing = prefs.pacing
          if (prefs.colors) loadedAnswers.colors = prefs.colors

          setAnswers(loadedAnswers)
          setIdeas(prefs.ideas || "")
        } else {
          console.warn("[CampaignPreferences] No campaign_preferences found")
        }

        // Set existing images
        setExistingImages(imagesResponse || [])
      } catch (error) {
        console.error("Failed to load campaign data:", error)
        alert("Failed to load existing preferences. Starting fresh.")
      } finally {
        setInitialLoading(false)
      }
    }

    loadExistingData()
  }, [existingCampaignId])

  const handleOptionSelect = (questionId: QuestionId, option: string): void => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: option
    }))
  }

  const handleIdeasChange = (e: React.ChangeEvent<HTMLTextAreaElement>): void => {
    const value = e.target.value
    // Enforce max length
    if (value.length <= MAX_IDEAS_LENGTH) {
      setIdeas(value)
    }
  }

  const handleSubmit = async (): Promise<void> => {
    // Check if all questions are answered
    const allAnswered = QUESTIONS.every(q => answers[q.id])
    if (!allAnswered) {
      alert("Please answer all questions before continuing.")
      return
    }

    if (!brandId) {
      alert("Brand ID is missing. Please go back to the dashboard.")
      return
    }

    setLoading(true)
    try {
      // Include ideas in the submission
      const submissionData: CampaignAnswers = {
        ...answers,
        ideas: ideas.trim() || ""
      }

      let responseCreativeBibleId: string
      let campaignId: string

      if (isEditMode && creativeBibleId) {
        // Update existing creative bible
        const response = await api.updateCampaignAnswers<SubmitCampaignAnswersResponse>(brandId, creativeBibleId, submissionData)
        if (!response?.creative_bible_id) {
          throw new Error("Invalid response: missing creative_bible_id")
        }
        responseCreativeBibleId = response.creative_bible_id

        // Reuse existing campaign if we have one
        if (existingCampaignId) {
          console.log("[CampaignPreferences] Reusing existing draft campaign:", existingCampaignId)
          campaignId = existingCampaignId
        } else {
          // No existing campaign (shouldn't happen in normal flow, but handle it)
          console.log("[CampaignPreferences] Creating new draft campaign for updated creative bible...")
          const campaignResponse = await api.createCampaign<{ campaign_id: string }>({
            brand_id: brandId,
            creative_bible_id: responseCreativeBibleId,
            status: "draft"
          })
          if (!campaignResponse?.campaign_id) {
            throw new Error("Invalid response: missing campaign_id")
          }
          campaignId = campaignResponse.campaign_id
        }
      } else {
        // Create new creative bible
        const response = await api.submitCampaignAnswers<SubmitCampaignAnswersResponse>(brandId, submissionData)
        if (!response?.creative_bible_id) {
          throw new Error("Invalid response: missing creative_bible_id")
        }
        responseCreativeBibleId = response.creative_bible_id

        // Create new draft campaign
        console.log("[CampaignPreferences] Creating draft campaign...")
        const campaignResponse = await api.createCampaign<{ campaign_id: string }>({
          brand_id: brandId,
          creative_bible_id: responseCreativeBibleId,
          status: "draft"
        })

        if (!campaignResponse?.campaign_id) {
          throw new Error("Invalid response: missing campaign_id")
        }
        campaignId = campaignResponse.campaign_id
        console.log("[CampaignPreferences] Draft campaign created:", campaignId)
      }

      // Upload new images if any were selected
      if (selectedImages.length > 0) {
        console.log("[CampaignPreferences] Uploading images to campaign...")
        try {
          await api.uploadCampaignImages(campaignId, selectedImages)
          console.log("[CampaignPreferences] Images uploaded successfully")
        } catch (uploadError) {
          console.error("[CampaignPreferences] Failed to upload images:", uploadError)
          // Don't fail the whole operation, just warn
          alert("Campaign saved but some images failed to upload. You can add them later.")
        }
      }

      // Navigate to storyline review with campaign_id
      navigate(`/campaigns/${campaignId}/storyline`)
    } catch (error) {
      console.error("Failed to submit answers:", error)
      const errorMessage = error instanceof Error ? error.message : "Unknown error occurred"
      alert(`Failed to ${isEditMode ? "update" : "submit"} answers: ${errorMessage}. Please check the console for details.`)
    } finally {
      setLoading(false)
    }
  }

  const isFormValid = Object.keys(answers).length >= QUESTIONS.length
  const isEditMode = !!creativeBibleId

  // Show loading spinner while fetching existing preferences
  if (initialLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-pink-50 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-purple-600" />
          <p className="text-muted-foreground">Loading preferences...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-pink-50 p-4 sm:p-6 lg:p-8">
      <div className="max-w-4xl mx-auto">
        <Button
          variant="ghost"
          onClick={() => navigate(isEditMode ? `/brands/${brandId}/storyline/${creativeBibleId}` : "/dashboard")}
          className="mb-6 hover:bg-white/50 transition-colors"
        >
          ← Back {isEditMode ? "to Storyline" : "to Dashboard"}
        </Button>

        <Card className="shadow-lg bg-white/80 backdrop-blur-sm">
          <CardHeader className="pb-4 border-b border-purple-100">
            <CardTitle className="text-3xl font-bold" style={{ fontFamily: "'Playfair Display', serif" }}>
              {isEditMode ? "Update Campaign Preferences" : "Create New Campaign"}
            </CardTitle>
            <CardDescription className="text-base mt-2">
              {isEditMode ? "Update your preferences and regenerate the storyline" : "Select your preferences for your video ad campaign"}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-8 pt-6">
            {QUESTIONS.map((question, qIndex) => (
              <div key={question.id} className="space-y-3">
                <h3 className="text-lg font-semibold text-foreground">
                  {qIndex + 1}. {question.question}
                </h3>
                <div className="flex flex-wrap gap-2">
                  {question.options.map((option) => (
                    <Button
                      key={option}
                      onClick={() => handleOptionSelect(question.id, option)}
                      variant={answers[question.id] === option ? "default" : "outline"}
                      className={`h-auto py-2 px-4 transition-all text-sm ${
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
              <div className="relative">
                <Textarea
                  value={ideas}
                  onChange={handleIdeasChange}
                  placeholder="Share any specific scenes, messages, or creative ideas you have in mind..."
                  className="min-h-[120px] resize-y border-purple-200 focus:border-purple-400 focus:ring-purple-400"
                  maxLength={MAX_IDEAS_LENGTH}
                />
                <div className="absolute bottom-2 right-2 text-xs text-muted-foreground">
                  {ideas.length}/{MAX_IDEAS_LENGTH}
                </div>
              </div>
              <p className="text-sm text-muted-foreground">
                Feel free to describe any specific moments, visuals, or messages you'd like to see in your ad.
              </p>
            </div>

            {/* Optional Image Upload */}
            <div className="space-y-3 pt-4 border-t border-purple-100">
              <h3 className="text-lg font-semibold text-foreground">
                7. Reference Images (Optional)
              </h3>
              <p className="text-sm text-muted-foreground">
                Upload reference images, mood boards, or visual inspiration for your campaign (up to 20 images)
              </p>

              {/* Show existing images in edit mode */}
              {existingImages.length > 0 && (
                <div className="mb-4">
                  <p className="text-sm font-medium text-foreground mb-2">
                    Current Images ({existingImages.length})
                  </p>
                  <div className="grid grid-cols-4 gap-2">
                    {existingImages.map((image) => (
                      <div key={image.id} className="relative aspect-square rounded-md overflow-hidden border border-gray-200">
                        <img
                          src={image.url}
                          alt={image.alt_text || "Campaign image"}
                          className="w-full h-full object-cover"
                        />
                      </div>
                    ))}
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    You can manage these images from the storyline review page
                  </p>
                </div>
              )}

              {/* Image uploader - always show */}
              <ImageUploader
                entityType="campaign"
                currentImageCount={existingImages.length}
                onFilesSelected={setSelectedImages}
                maxImages={20}
                disabled={loading}
              />
              {selectedImages.length > 0 && (
                <p className="text-sm text-green-600 font-medium">
                  {selectedImages.length} new image{selectedImages.length !== 1 ? 's' : ''} to upload
                </p>
              )}
            </div>

            <div className="pt-6">
              <GradientButton
                onClick={handleSubmit}
                disabled={loading || !isFormValid}
                className="w-full h-12 text-base"
              >
                {loading ? "Processing..." : isEditMode ? "Update & Regenerate Storyline →" : "Continue to Storyline →"}
              </GradientButton>
              {isEditMode && (
                <p className="text-sm text-muted-foreground text-center mt-3">
                  Your storyline will be regenerated with the updated preferences
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
