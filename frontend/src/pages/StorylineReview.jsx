import { useState, useEffect } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { Button } from "../components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import { api } from "../services/api"
import { Play } from "lucide-react"

export default function StorylineReview() {
  const { brandId, creativeBibleId } = useParams()
  const navigate = useNavigate()
  const [storyline, setStoryline] = useState({
    scenes: [
      {
        scene_number: 1,
        title: "Opening Shot",
        start_time: 0,
        end_time: 10,
        duration: 10,
        description: "Product showcase with dynamic camera movement",
        visual_notes: "Clean background, focused lighting",
        energy_start: "Medium",
        energy_end: "High"
      },
      {
        scene_number: 2,
        title: "Feature Highlight",
        start_time: 10,
        end_time: 20,
        duration: 10,
        description: "Close-up of key product features",
        visual_notes: "Detail shots, smooth transitions",
        energy_start: "High",
        energy_end: "High"
      },
      {
        scene_number: 3,
        title: "Call to Action",
        start_time: 20,
        end_time: 30,
        duration: 10,
        description: "Brand message and product positioning",
        visual_notes: "Wide shot, brand elements visible",
        energy_start: "High",
        energy_end: "Medium"
      }
    ]
  })
  const [creativeBible, setCreativeBible] = useState({
    brand_style: "Modern & Sleek",
    vibe: "Professional",
    colors: ["#3b82f6", "#1e40af", "#60a5fa"],
    energy_level: "Medium"
  })

  useEffect(() => {
    // Try to fetch real data in background, but don't block on it
    const fetchStoryline = async () => {
      try {
        const response = await api.getStoryline(brandId, creativeBibleId)
        setStoryline(response.storyline)
        setCreativeBible(response.creative_bible)
      } catch (error) {
        console.error("Failed to fetch storyline:", error)
        // Keep using placeholder data that's already set in initial state
      }
    }
    fetchStoryline()
  }, [brandId, creativeBibleId])

  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState(null)

  const handleApprove = async () => {
    setIsGenerating(true)
    setError(null)

    try {
      // Create campaign with brand_id and creative_bible_id
      const response = await api.createCampaign({
        brand_id: brandId,
        creative_bible_id: creativeBibleId
      })

      // Navigate to progress page with real campaign ID
      navigate(`/campaigns/${response.campaign_id}/progress`)
    } catch (err) {
      console.error("Failed to create campaign:", err)
      setError(err.message || "Failed to start video generation")
      setIsGenerating(false)
    }
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

        {/* Error Display */}
        {error && (
          <Card className="mt-6 border-destructive">
            <CardContent className="pt-6">
              <p className="text-destructive">{error}</p>
            </CardContent>
          </Card>
        )}

        {/* Action Buttons */}
        <div className="mt-8 flex gap-4">
          <Button
            variant="outline"
            onClick={() => navigate(`/brands/${brandId}/chat`)}
            className="flex-1"
            disabled={isGenerating}
          >
            Edit Brief
          </Button>
          <Button
            onClick={handleApprove}
            className="flex-1"
            size="lg"
            disabled={isGenerating}
          >
            <Play className="mr-2 h-4 w-4" />
            {isGenerating ? "Starting Generation..." : "Generate Video Ad"}
          </Button>
        </div>
      </div>
    </div>
  )
}

