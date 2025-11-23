import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import { Button } from "../components/ui/button"
import { GradientButton } from "@/components/ui/gradient-button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import { api } from "../services/api"
import HomeSidebar from "../components/layout/HomeSidebar"
import { Play, Clock, CheckCircle2, XCircle, Loader2, Trash2 } from "lucide-react"

export default function CampaignsList() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [campaigns, setCampaigns] = useState([])
  const [loading, setLoading] = useState(true)
  const [deleting, setDeleting] = useState(null)

  const fetchCampaigns = async () => {
    try {
      const data = await api.getAllCampaigns()
      setCampaigns(data)
    } catch (error) {
      console.error("Failed to fetch campaigns:", error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCampaigns()
  }, [])

  const handleDelete = async (campaignId, e) => {
    e.stopPropagation()
    
    if (!confirm("Are you sure you want to delete this campaign? This action cannot be undone.")) {
      return
    }

    setDeleting(campaignId)
    try {
      await api.deleteCampaign(campaignId)
      // Refresh the campaigns list
      await fetchCampaigns()
    } catch (error) {
      console.error("Failed to delete campaign:", error)
      alert("Failed to delete campaign. Please try again.")
    } finally {
      setDeleting(null)
    }
  }

  const handleLogout = async () => {
    await logout()
    navigate("/")
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case "completed":
        return <CheckCircle2 className="h-5 w-5 text-green-500" />
      case "failed":
        return <XCircle className="h-5 w-5 text-red-500" />
      case "processing":
        return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />
      default:
        return <Clock className="h-5 w-5 text-gray-500" />
    }
  }

  const getStatusLabel = (status) => {
    switch (status) {
      case "completed":
        return "Completed"
      case "failed":
        return "Failed"
      case "processing":
        return "Generating"
      case "pending":
        return "Pending"
      default:
        return status
    }
  }

  const handleCampaignClick = (campaign) => {
    if (campaign.status === "completed" && campaign.final_video_url) {
      navigate(`/campaigns/${campaign.id}/video`)
    } else if (campaign.status === "processing" || campaign.status === "pending") {
      navigate(`/campaigns/${campaign.id}/progress`)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-pink-50">
      <div className="flex">
        <HomeSidebar active="campaigns" userEmail={user?.email} onLogout={handleLogout} />

        {/* Main Content */}
        <main className="flex-1 p-8 ml-64">
          <div className="mb-8">
            <h1 className="text-3xl font-bold mb-2" style={{ fontFamily: "'Playfair Display', serif" }}>
              Campaigns
            </h1>
            <p className="text-base text-muted-foreground">
              View all your video ad campaigns across all brands
            </p>
          </div>

          {loading ? (
            <div className="text-center py-12 text-muted-foreground">
              Loading campaigns...
            </div>
          ) : campaigns.length === 0 ? (
            <Card className="p-12 text-center">
              <CardHeader>
                <CardTitle className="text-2xl mb-2" style={{ fontFamily: "'Playfair Display', serif" }}>
                  No campaigns yet
                </CardTitle>
                <CardDescription className="text-base">
                  Create your first campaign to start generating video ads
                </CardDescription>
              </CardHeader>
              <CardContent>
                <GradientButton onClick={() => navigate("/dashboard")}>
                  Go to Brands
                </GradientButton>
              </CardContent>
            </Card>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {campaigns.map((campaign) => (
                <Card
                  key={campaign.id}
                  className="group relative hover:shadow-lg transition-all cursor-pointer"
                  onClick={() => handleCampaignClick(campaign)}
                >
                  <CardHeader>
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-2">
                        {getStatusIcon(campaign.status)}
                        <span className="text-sm font-medium">
                          {getStatusLabel(campaign.status)}
                        </span>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 w-8 p-0 text-muted-foreground hover:text-destructive"
                        onClick={(e) => handleDelete(campaign.id, e)}
                        disabled={deleting === campaign.id}
                      >
                        {deleting === campaign.id ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Trash2 className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                    <CardTitle className="text-lg" style={{ fontFamily: "'Playfair Display', serif" }}>
                      {campaign.brand_title}
                    </CardTitle>
                    <CardDescription className="text-base">
                      {campaign.video_urls_count} scenes generated
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="text-xs text-muted-foreground">
                        Created: {new Date(campaign.created_at).toLocaleDateString()}
                      </div>
                      <div className="flex gap-2 mt-4">
                        {campaign.status === "completed" && campaign.final_video_url && (
                          <GradientButton
                            className="flex-1 !px-8 !py-2.5 !text-base !min-w-0"
                            onClick={(e) => {
                              e.stopPropagation()
                              navigate(`/campaigns/${campaign.id}/video`)
                            }}
                          >
                            <Play className="mr-2 h-4 w-4" />
                            View Video
                          </GradientButton>
                        )}
                        {(campaign.status === "processing" || campaign.status === "pending") && (
                          <Button
                            className="flex-1"
                            size="sm"
                            variant="outline"
                            onClick={(e) => {
                              e.stopPropagation()
                              navigate(`/campaigns/${campaign.id}/progress`)
                            }}
                          >
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            View Progress
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </main>
      </div>
    </div>
  )
}

