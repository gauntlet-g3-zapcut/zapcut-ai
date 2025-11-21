import { useState, useEffect, useRef } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { Button } from "../components/ui/button"
import { GradientButton } from "../components/ui/gradient-button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import { api } from "../services/api"
import { Play, Sparkles, Loader2, Palette, Zap, Heart, Pencil, RotateCcw } from "lucide-react"

interface Scene {
  scene_number: number
  title: string
  description: string
  visual_notes: string
  start_time: number
  end_time: number
  duration: number
  energy_start: number
  energy_end: number
}

interface Storyline {
  scenes: Scene[]
}

interface CreativeBible {
  brand_style?: string
  vibe?: string
  colors?: string[]
  energy_level?: string
  campaign_preferences?: Record<string, unknown>
}

interface StorylineResponse {
  storyline: Storyline
  creative_bible: CreativeBible
}

interface EditableDescriptionProps {
  value: string
  sceneNumber: number
  onSave: (sceneNumber: number, newDescription: string) => void
}

// Inline editable description component
function EditableDescription({ value, sceneNumber, onSave }: EditableDescriptionProps) {
  const [isEditing, setIsEditing] = useState<boolean>(false)
  const [editValue, setEditValue] = useState<string>(value)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (isEditing && textareaRef.current) {
      textareaRef.current.focus()
      // Auto-resize textarea to fit content
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px'
    }
  }, [isEditing])

  useEffect(() => {
    setEditValue(value)
  }, [value])

  const handleBlur = () => {
    setIsEditing(false)
    if (editValue !== value) {
      onSave(sceneNumber, editValue)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Escape') {
      setEditValue(value)
      setIsEditing(false)
    }
    // Allow Shift+Enter for new lines, but blur on Enter alone
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleBlur()
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setEditValue(e.target.value)
    // Auto-resize textarea
    e.target.style.height = 'auto'
    e.target.style.height = e.target.scrollHeight + 'px'
  }

  if (isEditing) {
    return (
      <textarea
        ref={textareaRef}
        value={editValue}
        onChange={handleChange}
        onBlur={handleBlur}
        onKeyDown={handleKeyDown}
        className="w-full p-2 border border-purple-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none overflow-hidden leading-relaxed bg-white text-gray-900"
        style={{ minHeight: '60px' }}
      />
    )
  }

  return (
    <p
      onClick={() => setIsEditing(true)}
      className="text-foreground leading-relaxed cursor-text hover:bg-purple-50 p-2 rounded-md transition-colors"
      title="Click to edit"
    >
      {value}
    </p>
  )
}

export default function StorylineReview() {
  const { brandId, creativeBibleId, campaignId } = useParams<{ brandId?: string; creativeBibleId?: string; campaignId?: string }>()
  const navigate = useNavigate()
  const [storyline, setStoryline] = useState<Storyline | null>(null)
  const [creativeBible, setCreativeBible] = useState<CreativeBible | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [generating, setGenerating] = useState<boolean>(false)
  const [editingScene, setEditingScene] = useState<number | null>(null)
  const [saving, setSaving] = useState<boolean>(false)
  const [reverting, setReverting] = useState<boolean>(false)

  // Determine if using new flow (campaignId) or old flow (brandId + creativeBibleId)
  const isNewFlow = !!campaignId
  const [effectiveBrandId, setEffectiveBrandId] = useState<string | undefined>(brandId)
  const [effectiveCreativeBibleId, setEffectiveCreativeBibleId] = useState<string | undefined>(creativeBibleId)

  useEffect(() => {
    const fetchStoryline = async () => {
      // New flow: Get campaign first, then get storyline from campaign
      if (isNewFlow && campaignId) {
        try {
          const campaign = await api.getCampaign<any>(campaignId)

          // Store brandId and creativeBibleId for editing functionality
          setEffectiveBrandId(campaign.brand_id)
          setEffectiveCreativeBibleId(campaign.creative_bible_id)

          // Check if storyline exists in campaign
          // If not, generate it using the getStoryline API
          if (!campaign.storyline || !campaign.storyline.scenes || campaign.storyline.scenes.length === 0) {
            console.log("Storyline not found in campaign, generating...")

            // Generate storyline using the creative bible
            if (campaign.brand_id && campaign.creative_bible_id) {
              const storylineResponse = await api.getStoryline<StorylineResponse>(
                campaign.brand_id,
                campaign.creative_bible_id
              )
              setStoryline(storylineResponse.storyline)
              setCreativeBible(storylineResponse.creative_bible)
            } else {
              throw new Error("Missing brand_id or creative_bible_id in campaign")
            }
          } else {
            // Storyline exists, use it directly
            setStoryline(campaign.storyline || null)
            setCreativeBible(campaign.creative_bible || null)
          }
        } catch (error) {
          console.error("Failed to fetch campaign:", error)
          alert("Failed to load campaign. Please try again.")
        } finally {
          setLoading(false)
        }
        return
      }

      // Old flow: Use brandId + creativeBibleId
      if (!effectiveBrandId || !effectiveCreativeBibleId) return

      try {
        const response = await api.getStoryline<StorylineResponse>(effectiveBrandId, effectiveCreativeBibleId)
        setStoryline(response.storyline)
        setCreativeBible(response.creative_bible)
      } catch (error) {
        console.error("Failed to fetch storyline:", error)
        alert("Failed to load storyline. Please try again.")
      } finally {
        setLoading(false)
      }
    }
    fetchStoryline()
  }, [effectiveBrandId, effectiveCreativeBibleId, campaignId, isNewFlow])

  const handleApprove = async () => {
    setGenerating(true)
    try {
      // New flow: Approve existing draft campaign
      if (isNewFlow && campaignId) {
        const response = await api.approveCampaign<{ campaign_id: string }>(campaignId)
        if (!response?.campaign_id) {
          throw new Error("No campaign_id in response")
        }
        navigate(`/campaigns/${campaignId}/progress`)
        return
      }

      // Old flow: Create new campaign
      if (!effectiveBrandId || !effectiveCreativeBibleId) {
        throw new Error("Missing brand or creative bible ID")
      }

      const response = await api.createCampaign<{ campaign_id: string }>({
        brand_id: effectiveBrandId,
        creative_bible_id: effectiveCreativeBibleId,
        status: "pending" // Create and approve immediately in old flow
      })

      if (!response?.campaign_id) {
        throw new Error("No campaign_id in response")
      }

      navigate(`/campaigns/${response.campaign_id}/progress`)
    } catch (error) {
      console.error("Failed to start generation:", error)
      setGenerating(false)
      const errorMessage = error instanceof Error ? error.message : "Please try again."
      alert(`Failed to start video generation: ${errorMessage}`)
    }
  }

  const handleEditDescription = async (sceneNumber: number, newDescription: string) => {
    if (!effectiveBrandId || !effectiveCreativeBibleId) {
      console.error("Missing brandId or creativeBibleId for editing")
      alert("Cannot edit scene. Please refresh the page and try again.")
      return
    }

    // Optimistic update - update UI immediately
    setStoryline(prevStoryline => {
      if (!prevStoryline) return null
      return {
        ...prevStoryline,
        scenes: prevStoryline.scenes.map(scene =>
          scene.scene_number === sceneNumber
            ? { ...scene, description: newDescription }
            : scene
        )
      }
    })

    // Save to backend
    try {
      setSaving(true)
      const response = await api.updateStoryline<{ storyline: Storyline }>(effectiveBrandId, effectiveCreativeBibleId, sceneNumber, newDescription)

      // Update with server response (in case backend modified anything)
      if (response?.storyline) {
        setStoryline(response.storyline)
      }
    } catch (error) {
      console.error("Failed to save description:", error)
      const errorMessage = error instanceof Error ? error.message : "Please try again."
      alert(`Failed to save changes: ${errorMessage}`)

      // Revert optimistic update on error - refetch from server
      try {
        const response = await api.getStoryline<StorylineResponse>(effectiveBrandId, effectiveCreativeBibleId)
        setStoryline(response.storyline)
      } catch (refetchError) {
        console.error("Failed to refetch storyline:", refetchError)
      }
    } finally {
      setSaving(false)
    }
  }

  const handleRevertToOriginal = async () => {
    if (!effectiveBrandId || !effectiveCreativeBibleId) {
      console.error("Missing brandId or creativeBibleId for reverting")
      alert("Cannot revert storyline. Please refresh the page and try again.")
      return
    }

    if (!confirm("Are you sure you want to revert to the original AI-generated storyline? All your edits will be lost.")) {
      return
    }

    try {
      setReverting(true)
      const response = await api.revertStoryline<{ storyline: Storyline }>(effectiveBrandId, effectiveCreativeBibleId)

      if (response?.storyline) {
        setStoryline(response.storyline)
        alert("Storyline reverted to original!")
      }
    } catch (error) {
      console.error("Failed to revert storyline:", error)
      const errorMessage = error instanceof Error ? error.message : "Please try again."
      alert(`Failed to revert: ${errorMessage}`)
    } finally {
      setReverting(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-pink-50 flex items-center justify-center" style={{ fontFamily: 'Inter, sans-serif' }}>
        <div className="flex flex-col items-center gap-6">
          {/* Animated Sparkles Icon with pulsing effect */}
          <div className="relative">
            <div className="absolute inset-0 rounded-full bg-purple-200/50 animate-ping"></div>
            <div className="relative w-20 h-20 rounded-full bg-gradient-to-br from-purple-100 to-pink-100 border-2 border-purple-200 flex items-center justify-center shadow-lg">
              <Sparkles className="h-10 w-10 text-purple-600 animate-spin" style={{ animationDuration: '2s' }} />
            </div>
          </div>

          {/* Main text with fade animation */}
          <div className="text-center space-y-2">
            <h2 className="text-2xl font-semibold text-foreground animate-pulse" style={{ fontFamily: 'Inter, sans-serif' }}>
              Generating Storyline
            </h2>
            <div className="flex items-center justify-center gap-1">
              <span className="w-1.5 h-1.5 bg-purple-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
              <span className="w-1.5 h-1.5 bg-purple-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
              <span className="w-1.5 h-1.5 bg-purple-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-pink-50 p-4 sm:p-6 lg:p-8">
      <div className="max-w-6xl mx-auto">
        <Button
          variant="ghost"
          onClick={() => navigate("/dashboard")}
          className="mb-6 hover:bg-white/50 transition-colors"
        >
          ← Back to Dashboard
        </Button>

        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2" style={{ fontFamily: "'Playfair Display', serif" }}>
            Storyline Review
          </h1>
          <p className="text-base text-muted-foreground">
            Review your video ad storyline before we generate it
          </p>
        </div>

        {/* Creative Bible Summary */}
        {creativeBible && (
          <Card className="mb-8 shadow-lg bg-white/80 backdrop-blur-sm border-purple-100">
            <CardHeader className="pb-4 border-b border-purple-100">
              <CardTitle className="text-2xl font-bold" style={{ fontFamily: "'Playfair Display', serif" }}>
                Creative Bible
              </CardTitle>
              <CardDescription className="text-base mt-2">
                Visual style and direction for your ad
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="grid md:grid-cols-2 gap-6">
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center flex-shrink-0">
                    <Palette className="w-5 h-5 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold mb-1 text-foreground">Style</p>
                    <p className="text-muted-foreground">{creativeBible.brand_style || "Not specified"}</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-lg bg-pink-100 flex items-center justify-center flex-shrink-0">
                    <Heart className="w-5 h-5 text-pink-600" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold mb-1 text-foreground">Vibe</p>
                    <p className="text-muted-foreground">{creativeBible.vibe || "Not specified"}</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center flex-shrink-0">
                    <Palette className="w-5 h-5 text-purple-600" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-semibold mb-2 text-foreground">Colors</p>
                    <div className="flex gap-2 flex-wrap">
                      {creativeBible.colors && creativeBible.colors.length > 0 ? (
                        creativeBible.colors.map((color, idx) => (
                          <div
                            key={`color-${idx}-${color}`}
                            className="w-10 h-10 rounded-lg border-2 border-gray-200 shadow-sm hover:scale-110 transition-transform"
                            style={{ backgroundColor: color }}
                            title={color}
                          />
                        ))
                      ) : (
                        <span className="text-muted-foreground text-sm">Not specified</span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-lg bg-yellow-100 flex items-center justify-center flex-shrink-0">
                    <Zap className="w-5 h-5 text-yellow-600" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold mb-1 text-foreground">Energy Level</p>
                    <p className="text-muted-foreground">{creativeBible.energy_level || "Not specified"}</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Storyline Scenes */}
        {storyline && (
          <div className="space-y-6 mb-8">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-semibold" style={{ fontFamily: "'Playfair Display', serif" }}>
                Video Scenes
              </h2>
              <div className="flex items-center gap-3">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleRevertToOriginal}
                  disabled={reverting}
                  className="border-purple-200 hover:bg-purple-50 hover:border-purple-300"
                >
                  {reverting ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Reverting...
                    </>
                  ) : (
                    <>
                      <RotateCcw className="w-4 h-4 mr-2" />
                      Revert to Original
                    </>
                  )}
                </Button>
                <span className="text-sm text-muted-foreground bg-white/60 px-3 py-1 rounded-full">
                  30 seconds
                </span>
              </div>
            </div>

            {storyline.scenes?.map((scene, idx) => (
              <Card
                key={`scene-${scene.scene_number || idx}-${scene.title || idx}`}
                className="shadow-lg bg-white/80 backdrop-blur-sm border-purple-100 hover:shadow-xl transition-shadow group"
              >
                <CardHeader className="pb-4 border-b border-purple-100">
                  <div className="flex justify-between items-start gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <div className="w-8 h-8 rounded-full bg-gray-100 border-2 border-gray-300 flex items-center justify-center text-gray-700 font-semibold text-sm">
                          {scene.scene_number || idx + 1}
                        </div>
                        <CardTitle className="text-xl">
                          {scene.title || `Scene ${scene.scene_number || idx + 1}`}
                        </CardTitle>
                      </div>
                      <CardDescription className="text-sm mt-1">
                        {scene.start_time}s - {scene.end_time}s ({scene.duration}s)
                      </CardDescription>
                    </div>
                    <div className="flex items-center gap-2 px-3 py-1.5 bg-purple-50 rounded-lg border border-purple-100">
                      <Zap className="w-4 h-4 text-purple-600" />
                      <span className="text-sm font-medium text-purple-700">
                        {scene.energy_start} → {scene.energy_end}
                      </span>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-6">
                  <div className="space-y-4">
                    <div>
                      <EditableDescription
                        value={scene.description}
                        sceneNumber={scene.scene_number || idx + 1}
                        onSave={handleEditDescription}
                      />
                    </div>
                    <div className="pt-4 border-t border-purple-50">
                      <p className="text-sm font-semibold mb-2 text-foreground flex items-center gap-2">
                        <Sparkles className="w-4 h-4 text-purple-600" />
                        Visual Notes
                      </p>
                      <p className="text-sm text-muted-foreground leading-relaxed">
                        {scene.visual_notes}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Action Buttons */}
        <div className="mt-8 flex gap-4">
          <Button
            variant="outline"
            onClick={() => {
              if (effectiveBrandId && effectiveCreativeBibleId) {
                // Pass campaignId so we reuse the same draft campaign
                const params = new URLSearchParams({
                  creativeBibleId: effectiveCreativeBibleId,
                  ...(campaignId && { campaignId })
                })
                navigate(`/brands/${effectiveBrandId}/chat?${params.toString()}`)
              } else {
                alert("Unable to edit preferences. Please refresh the page and try again.")
              }
            }}
            disabled={!effectiveBrandId || !effectiveCreativeBibleId}
            className="flex-1 h-11 border-purple-200 hover:bg-purple-50 hover:border-purple-300 text-base font-medium"
          >
            <Pencil className="mr-2 h-4 w-4" />
            Update preferences
          </Button>
          <GradientButton
            onClick={handleApprove}
            disabled={generating}
            className="flex-1 h-11"
          >
            {generating ? (
              <>
                <Sparkles className="mr-2 h-4 w-4 animate-spin" />
                Starting Generation...
              </>
            ) : (
              <>
                <Play className="mr-2 h-4 w-4" />
                Generate Video Ad
              </>
            )}
          </GradientButton>
        </div>
      </div>
    </div>
  )
}
