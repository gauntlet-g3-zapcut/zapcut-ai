import { useState, useEffect } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card"
import { api } from "../services/api"
import { Loader2, CheckCircle2, XCircle } from "lucide-react"

export default function VideoProgress() {
  const { campaignId } = useParams()
  const navigate = useNavigate()
  const [status, setStatus] = useState("pending")
  const [stage, setStage] = useState("not_started")
  const [progress, setProgress] = useState(0)
  const [finalVideoUrl, setFinalVideoUrl] = useState(null)

  useEffect(() => {
    let progressTimer = null
    let pollingInterval = null

    // Poll for status updates
    const pollStatus = async () => {
      try {
        const response = await api.getCampaignStatus(campaignId)

        // 🔥 Log status update
        console.log("📊 Status update:", {
          status: response.status,
          stage: response.stage,
          progress: response.progress,
          campaign_id: campaignId
        })

        // 🔥 Log generation progress messages
        if (response.logs && response.logs.length > 0) {
          // Only log new messages (track last seen log index)
          const lastLogIndex = window._lastLogIndex || 0
          const newLogs = response.logs.slice(lastLogIndex)

          newLogs.forEach(log => {
            console.log(`🎬 ${log.message}`)
          })

          window._lastLogIndex = response.logs.length
        }

        setStatus(response.status)
        setStage(response.stage || "not_started")
        setProgress(response.progress || 0)

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
        // DO NOT show default video - stay on error state
        setStatus("failed")
        setStage("error")
      }
    }

    // Initial poll
    console.log("🎬 Starting to poll for campaign:", campaignId)
    pollStatus()

    // Poll every 30 seconds
    console.log("⏱️  Polling every 30 seconds for updates...")
    pollingInterval = setInterval(pollStatus, 30000)

    return () => {
      clearInterval(pollingInterval)
      if (progressTimer) clearTimeout(progressTimer)
    }
  }, [campaignId, navigate])

  const getStageInfo = () => {
    if (status === "completed") {
      return {
        stage: "Your Ad is Ready!",
        description: "Redirecting to video player...",
        icon: <CheckCircle2 className="h-12 w-12 text-green-500" />
      }
    }

    if (status === "failed") {
      return {
        stage: "Generation Failed",
        description: "Something went wrong. Please try again.",
        icon: <XCircle className="h-12 w-12 text-destructive" />
      }
    }

    // Map granular stages to user-friendly text
    const stageMap = {
      not_started: "Initializing...",
      reference_images: "Generating reference images...",
      storyboard: "Creating storyboard...",
      scene_videos: "Generating video scenes...",
      voiceovers: "Generating voiceovers...",
      music: "Composing soundtrack...",
      compositing: "Composing final video...",
      complete: "Complete!"
    }

    return {
      stage: stageMap[stage] || "Processing...",
      description: `${progress}% complete`,
      icon: <Loader2 className="h-12 w-12 animate-spin text-primary" />
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
          <div className="space-y-6">
            {/* Progress Bar */}
            <div className="space-y-2">
              <div className="w-full bg-secondary rounded-full h-2.5">
                <div
                  className="bg-primary h-2.5 rounded-full transition-all duration-500"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="text-xs text-center text-muted-foreground">{progress}%</p>
            </div>

            {/* Progress stages */}
            <div className="space-y-3">
              <ProgressStage
                label="Generating reference images"
                completed={progress > 10}
                active={stage === "reference_images"}
              />
              <ProgressStage
                label="Creating storyboard"
                completed={progress > 20}
                active={stage === "storyboard"}
              />
              <ProgressStage
                label="Generating video scenes"
                completed={progress > 60}
                active={stage === "scene_videos"}
              />
              <ProgressStage
                label="Generating voiceovers"
                completed={progress > 70}
                active={stage === "voiceovers"}
              />
              <ProgressStage
                label="Composing soundtrack"
                completed={progress > 80}
                active={stage === "music"}
              />
              <ProgressStage
                label="Composing final video"
                completed={progress >= 100}
                active={stage === "compositing"}
              />
            </div>

            {status === "generating" && (
              <div className="mt-6 text-center text-sm text-muted-foreground">
                <p>This usually takes 6-8 minutes...</p>
                <p className="text-xs mt-1">Please keep this page open</p>
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

