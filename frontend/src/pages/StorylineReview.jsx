import { useState, useEffect } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { Button } from "../components/ui/button"
import { GradientButton } from "../components/ui/gradient-button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import { api } from "../services/api"
import { Play, Sparkles, Loader2, Palette, Zap, Heart, Edit2, Pencil } from "lucide-react"

export default function StorylineReview() {
  const { brandId, creativeBibleId } = useParams()
  const navigate = useNavigate()
  const [storyline, setStoryline] = useState(null)
  const [creativeBible, setCreativeBible] = useState(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)

  useEffect(() => {
    const fetchStoryline = async () => {
      try {
        const response = await api.getStoryline(brandId, creativeBibleId)
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
  }, [brandId, creativeBibleId])

  const handleApprove = async () => {
    setGenerating(true)
    try {
      const response = await api.createCampaign({
        brand_id: brandId,
        creative_bible_id: creativeBibleId
      })
      
      if (!response?.campaign_id) {
        throw new Error("No campaign_id in response")
      }
      
      // Navigate to video generation progress page immediately
      navigate(`/campaigns/${response.campaign_id}/progress`)
      
      // Don't set generating to false - let navigation happen
      // The component will unmount anyway
    } catch (error) {
      console.error("Failed to start generation:", error)
      setGenerating(false) // Only reset if there's an error
      alert(`Failed to start video generation: ${error.message || "Please try again."}`)
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
              <span className="text-sm text-muted-foreground bg-white/60 px-3 py-1 rounded-full">
                30 seconds
              </span>
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
                    <div className="flex items-center gap-3">
                      <div className="flex items-center gap-2 px-3 py-1.5 bg-purple-50 rounded-lg border border-purple-100">
                        <Zap className="w-4 h-4 text-purple-600" />
                        <span className="text-sm font-medium text-purple-700">
                          {scene.energy_start} → {scene.energy_end}
                        </span>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => navigate(`/brands/${brandId}/chat?editScene=${scene.scene_number || idx + 1}`)}
                        className="opacity-0 group-hover:opacity-100 transition-opacity border-purple-200 hover:bg-purple-50 hover:border-purple-300"
                        title="Edit this scene"
                      >
                        <Edit2 className="w-4 h-4 mr-1.5" />
                        Edit
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-6">
                  <div className="space-y-4">
                    <div>
                      <p className="text-foreground leading-relaxed">{scene.description}</p>
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
            onClick={() => navigate(`/brands/${brandId}/chat`)}
            className="flex-1 h-11 border-purple-200 hover:bg-purple-50 hover:border-purple-300 text-base font-medium"
          >
            <Pencil className="mr-2 h-4 w-4" />
            Edit Brief
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

