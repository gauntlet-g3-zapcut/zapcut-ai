import { useState, useEffect } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { Button } from "../components/ui/button"
import { Card } from "../components/ui/card"
import { api } from "../services/api"
import { Download, Share2, ArrowLeft } from "lucide-react"

export default function VideoPlayer() {
  const { campaignId } = useParams()
  const navigate = useNavigate()
  const [campaign, setCampaign] = useState(null)
  const [loading, setLoading] = useState(true)
  const [shareLink, setShareLink] = useState("")

  useEffect(() => {
    const fetchCampaign = async () => {
      try {
        const data = await api.getCampaign(campaignId)
        setCampaign(data)
      } catch (error) {
        console.error("Failed to fetch campaign:", error)
        // DO NOT show placeholder video - just show error
        setCampaign(null)
      } finally {
        setLoading(false)
      }
    }
    fetchCampaign()
  }, [campaignId])

  const handleDownloadMP4 = () => {
    if (campaign?.final_video_url) {
      window.open(campaign.final_video_url, "_blank")
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
      <div className="min-h-screen bg-background flex items-center justify-center p-8">
        <Card className="w-full max-w-md p-8 text-center">
          <h2 className="text-2xl font-semibold mb-4">Video Not Found</h2>
          <p className="text-muted-foreground mb-6">
            The video you're looking for doesn't exist or failed to generate.
          </p>
          <Button onClick={() => navigate("/dashboard")}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Dashboard
          </Button>
        </Card>
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
            <Card className="p-0 overflow-hidden">
              <video
                controls
                autoPlay
                className="w-full aspect-video bg-black"
                src={campaign.final_video_url}
              >
                Your browser does not support the video tag.
              </video>
            </Card>

            {/* Action Buttons */}
            <div className="mt-6 grid grid-cols-3 gap-4">
              <Button onClick={handleDownloadMP4} variant="outline">
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

        {/* Storyline Display */}
        {campaign.storyline && campaign.storyline.scenes && (
          <div className="mt-12">
            <h2 className="text-2xl font-semibold mb-6">Storyline</h2>
            <div className="grid md:grid-cols-5 gap-4">
              {campaign.storyline.scenes.map((scene) => (
                <Card key={scene.scene_number} className="p-4">
                  <p className="text-sm font-medium mb-2">Scene {scene.scene_number}</p>
                  <p className="text-xs text-muted-foreground">{scene.title}</p>
                </Card>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

