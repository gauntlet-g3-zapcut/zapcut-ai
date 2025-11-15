import { useState, useEffect } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card"
import { api } from "../services/api"
import { Loader2, CheckCircle2, XCircle } from "lucide-react"

export default function VideoProgress() {
  const { campaignId } = useParams()
  const navigate = useNavigate()
  const [status, setStatus] = useState("pending")
  const [finalVideoUrl, setFinalVideoUrl] = useState(null)

  useEffect(() => {
    // Poll for status updates
    const pollStatus = async () => {
      try {
        const response = await api.getCampaignStatus(campaignId)
        setStatus(response.status)
        
        if (response.status === "completed") {
          setFinalVideoUrl(response.final_video_url)
          // Stop polling and navigate to video player
          setTimeout(() => {
            navigate(`/campaigns/${campaignId}/video`)
          }, 2000)
        } else if (response.status === "failed") {
          // Stop polling on failure
          return
        }
      } catch (error) {
        console.error("Failed to fetch status:", error)
      }
    }

    // Initial poll
    pollStatus()

    // Poll every 5 seconds
    const interval = setInterval(pollStatus, 5000)

    return () => clearInterval(interval)
  }, [campaignId, navigate])

  const getStageInfo = () => {
    switch (status) {
      case "pending":
        return {
          stage: "Initializing...",
          description: "Setting up your video generation",
          icon: <Loader2 className="h-12 w-12 animate-spin text-primary" />
        }
      case "generating":
        return {
          stage: "Generating Video...",
          description: "Creating your 4K video ad with AI",
          icon: <Loader2 className="h-12 w-12 animate-spin text-primary" />
        }
      case "completed":
        return {
          stage: "Complete!",
          description: "Your video is ready",
          icon: <CheckCircle2 className="h-12 w-12 text-green-500" />
        }
      case "failed":
        return {
          stage: "Generation Failed",
          description: "Something went wrong. Please try again.",
          icon: <XCircle className="h-12 w-12 text-destructive" />
        }
      default:
        return {
          stage: "Processing...",
          description: "Working on your video",
          icon: <Loader2 className="h-12 w-12 animate-spin text-primary" />
        }
    }
  }

  const stageInfo = getStageInfo()

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-8">
      <Card className="w-full max-w-2xl">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-6">
            {stageInfo.icon}
          </div>
          <CardTitle className="text-3xl mb-2">{stageInfo.stage}</CardTitle>
          <p className="text-muted-foreground">{stageInfo.description}</p>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Progress stages */}
            <div className="space-y-3">
              <ProgressStage
                label="Generating reference images"
                completed={status !== "pending"}
              />
              <ProgressStage
                label="Creating storyboard"
                completed={status !== "pending"}
              />
              <ProgressStage
                label="Generating video scenes (1/5 - 5/5)"
                completed={status === "completed"}
                active={status === "generating"}
              />
              <ProgressStage
                label="Generating soundtrack"
                completed={status === "completed"}
                active={status === "generating"}
              />
              <ProgressStage
                label="Composing final video"
                completed={status === "completed"}
              />
            </div>

            {status === "generating" && (
              <div className="mt-6 text-center text-sm text-muted-foreground">
                <p>This usually takes 3-5 minutes...</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function ProgressStage({ label, completed, active }) {
  return (
    <div className="flex items-center gap-3">
      {completed ? (
        <CheckCircle2 className="h-5 w-5 text-green-500 flex-shrink-0" />
      ) : active ? (
        <Loader2 className="h-5 w-5 animate-spin text-primary flex-shrink-0" />
      ) : (
        <div className="h-5 w-5 rounded-full border-2 border-muted flex-shrink-0" />
      )}
      <p className={`text-sm ${completed ? "text-foreground" : "text-muted-foreground"}`}>
        {label}
      </p>
    </div>
  )
}

