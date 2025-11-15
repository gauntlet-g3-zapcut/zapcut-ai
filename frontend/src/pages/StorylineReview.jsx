import { useState, useEffect } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { Button } from "../components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import { api } from "../services/api"
import { Play, Sparkles } from "lucide-react"

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
      
      // Navigate to video generation progress page
      navigate(`/campaigns/${response.campaign_id}/progress`)
    } catch (error) {
      console.error("Failed to start generation:", error)
      alert("Failed to start video generation. Please try again.")
    } finally {
      setGenerating(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-muted-foreground">Loading storyline...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-6xl mx-auto">
        <Button
          variant="ghost"
          onClick={() => navigate("/dashboard")}
          className="mb-6"
        >
          ← Back to Dashboard
        </Button>

        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-4">Storyline Review</h1>
          <p className="text-muted-foreground">
            Review your video ad storyline before we generate it
          </p>
        </div>

        {/* Creative Bible Summary */}
        {creativeBible && (
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>Creative Bible</CardTitle>
              <CardDescription>Visual style and direction</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium mb-1">Style</p>
                  <p className="text-muted-foreground">{creativeBible.brand_style}</p>
                </div>
                <div>
                  <p className="text-sm font-medium mb-1">Vibe</p>
                  <p className="text-muted-foreground">{creativeBible.vibe}</p>
                </div>
                <div>
                  <p className="text-sm font-medium mb-1">Colors</p>
                  <div className="flex gap-2">
                    {creativeBible.colors?.map((color, idx) => (
                      <div
                        key={idx}
                        className="w-8 h-8 rounded border"
                        style={{ backgroundColor: color }}
                        title={color}
                      />
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-sm font-medium mb-1">Energy Level</p>
                  <p className="text-muted-foreground">{creativeBible.energy_level}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Storyline Scenes */}
        {storyline && (
          <div className="space-y-6">
            <h2 className="text-2xl font-semibold">Video Scenes (30 seconds)</h2>
            
            {storyline.scenes?.map((scene) => (
              <Card key={scene.scene_number}>
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle>
                        Scene {scene.scene_number}: {scene.title}
                      </CardTitle>
                      <CardDescription>
                        {scene.start_time}s - {scene.end_time}s ({scene.duration}s)
                      </CardDescription>
                    </div>
                    <div className="text-sm text-muted-foreground">
                      Energy: {scene.energy_start} → {scene.energy_end}
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="mb-4">{scene.description}</p>
                  <div className="text-sm text-muted-foreground">
                    <strong>Visual Notes:</strong> {scene.visual_notes}
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
            className="flex-1"
          >
            Edit Brief
          </Button>
          <Button
            onClick={handleApprove}
            disabled={generating}
            className="flex-1"
            size="lg"
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
          </Button>
        </div>
      </div>
    </div>
  )
}

