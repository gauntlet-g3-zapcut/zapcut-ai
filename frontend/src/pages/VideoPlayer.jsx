import { useState, useEffect } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { Button } from "../components/ui/button"
import { Card } from "../components/ui/card"
import { api } from "../services/api"
import { Download, Share2, ArrowLeft, Play } from "lucide-react"

export default function VideoPlayer() {
  const { campaignId } = useParams()
  const navigate = useNavigate()
  const [campaign, setCampaign] = useState(null)
  const [statusData, setStatusData] = useState(null)
  const [selectedScene, setSelectedScene] = useState(null)
  const [loading, setLoading] = useState(true)
  const [shareLink, setShareLink] = useState("")

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [campaignData, statusResponse] = await Promise.all([
          api.getCampaign(campaignId),
          api.getCampaignStatus(campaignId)
        ])
        setCampaign(campaignData)
        setStatusData(statusResponse)
        
        // Set first completed scene as selected by default
        if (statusResponse?.progress?.scenes) {
          const firstCompleted = statusResponse.progress.scenes.find(
            s => s.status === "completed" && s.video_url
          )
          if (firstCompleted) {
            setSelectedScene(firstCompleted)
          }
        }
      } catch (error) {
        console.error("Failed to fetch campaign:", error)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [campaignId])

  const handleDownloadMP4 = (videoUrl) => {
    const url = videoUrl || selectedScene?.video_url || campaign?.final_video_url
    if (url) {
      window.open(url, "_blank")
    }
  }

  const handleDownloadWebM = () => {
    // Convert to WebM (if backend supports it)
    // For now, just download MP4
    handleDownloadMP4()
  }

  const handleShare = async () => {
    const link = `${window.location.origin}/campaigns/${campaignId}/video`
    setShareLink(link)
    
    // Copy to clipboard
    try {
      await navigator.clipboard.writeText(link)
      alert("Link copied to clipboard!")
    } catch (error) {
      console.error("Failed to copy link:", error)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-muted-foreground">Loading video...</div>
      </div>
    )
  }

  if (!campaign) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-destructive">Campaign not found</div>
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
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Dashboard
        </Button>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Video Player */}
          <div className="lg:col-span-2">
            {selectedScene?.video_url ? (
              <Card className="p-0 overflow-hidden">
                <video
                  controls
                  autoPlay
                  className="w-full aspect-video bg-black"
                  src={selectedScene.video_url}
                  key={selectedScene.scene_number}
                >
                  Your browser does not support the video tag.
                </video>
              </Card>
            ) : (
              <Card className="p-12 text-center">
                <p className="text-muted-foreground">No video selected</p>
              </Card>
            )}

            {/* Action Buttons */}
            {selectedScene?.video_url && (
              <div className="mt-6 grid grid-cols-3 gap-4">
                <Button onClick={() => handleDownloadMP4(selectedScene.video_url)} variant="outline">
                  <Download className="mr-2 h-4 w-4" />
                  Download MP4
                </Button>
                <Button onClick={handleDownloadWebM} variant="outline">
                  <Download className="mr-2 h-4 w-4" />
                  Download WebM
                </Button>
                <Button onClick={handleShare} variant="outline">
                  <Share2 className="mr-2 h-4 w-4" />
                  Share Link
                </Button>
              </div>
            )}
          </div>

          {/* Sidebar Info */}
          <div className="space-y-6">
            <Card className="p-6">
              <h3 className="font-semibold mb-4">Video Details</h3>
              <div className="space-y-3 text-sm">
                <div>
                  <p className="text-muted-foreground">Status</p>
                  <p className="font-medium">{campaign.status}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Duration</p>
                  <p className="font-medium">30 seconds</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Quality</p>
                  <p className="font-medium">4K (3840x2160)</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Created</p>
                  <p className="font-medium">
                    {new Date(campaign.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            </Card>

            <Card className="p-6">
              <h3 className="font-semibold mb-4">What's Next?</h3>
              <div className="space-y-3 text-sm">
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => navigate(`/brands/${campaign.brand_id}/chat`)}
                >
                  Create Another Ad
                </Button>
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => navigate("/dashboard")}
                >
                  View All Brands
                </Button>
              </div>
            </Card>
          </div>
        </div>

        {/* All Scene Videos */}
        {statusData?.progress?.scenes && statusData.progress.scenes.length > 0 && (
          <div className="mt-12">
            <h2 className="text-2xl font-semibold mb-6">All Scene Videos</h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {statusData.progress.scenes.map((scene) => (
                <Card 
                  key={scene.scene_number} 
                  className={`p-4 cursor-pointer transition-all hover:shadow-lg ${
                    selectedScene?.scene_number === scene.scene_number 
                      ? "ring-2 ring-primary" 
                      : ""
                  }`}
                  onClick={() => scene.video_url && setSelectedScene(scene)}
                >
                  {scene.video_url ? (
                    <div className="relative aspect-video bg-black rounded mb-2 overflow-hidden">
                      <video
                        src={scene.video_url}
                        className="w-full h-full object-cover"
                        muted
                        onMouseEnter={(e) => e.target.play()}
                        onMouseLeave={(e) => {
                          e.target.pause()
                          e.target.currentTime = 0
                        }}
                      />
                      <div className="absolute inset-0 flex items-center justify-center bg-black/30">
                        <Play className="h-8 w-8 text-white" />
                      </div>
                    </div>
                  ) : (
                    <div className="aspect-video bg-muted rounded mb-2 flex items-center justify-center">
                      <p className="text-xs text-muted-foreground">
                        {scene.status === "generating" ? "Generating..." : 
                         scene.status === "failed" ? "Failed" : "Pending"}
                      </p>
                    </div>
                  )}
                  <p className="text-sm font-medium mb-1">Scene {scene.scene_number}</p>
                  <p className="text-xs text-muted-foreground line-clamp-2">
                    {scene.title || `Scene ${scene.scene_number}`}
                  </p>
                  {scene.video_url && (
                    <Button
                      size="sm"
                      variant="ghost"
                      className="mt-2 w-full"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDownloadMP4(scene.video_url)
                      }}
                    >
                      <Download className="mr-2 h-3 w-3" />
                      Download
                    </Button>
                  )}
                </Card>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

