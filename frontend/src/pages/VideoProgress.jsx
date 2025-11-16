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
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [progress, setProgress] = useState({
    current_scene: null,
    completed_scenes: 0,
    total_scenes: 0,
    generating_scenes: 0,
    failed_scenes: 0,
    scenes: []
  })
  const [audioStatus, setAudioStatus] = useState({
    status: "pending",
    audio_url: null,
    error: null
  })

  useEffect(() => {
    // Validate campaignId exists
    if (!campaignId) {
      setError("Campaign ID is missing")
      setLoading(false)
      return
    }

    let isMounted = true;
    let pollInterval = null;
    let shouldStopPolling = false;

    // Poll for status updates
    const pollStatus = async () => {
      if (shouldStopPolling || !isMounted) return
      
      try {
        const response = await api.getCampaignStatus(campaignId)
        
        if (!isMounted) return
        
        setStatus(response.status)
        setError(null) // Clear any previous errors
        
        if (response.progress) {
          // Update progress state - ensure scenes array is properly set
          setProgress({
            current_scene: response.progress.current_scene,
            completed_scenes: response.progress.completed_scenes,
            total_scenes: response.progress.total_scenes,
            generating_scenes: response.progress.generating_scenes,
            failed_scenes: response.progress.failed_scenes,
            scenes: response.progress.scenes || []
          })
        }
        
        // Update audio status
        if (response.audio) {
          setAudioStatus({
            status: response.audio.status || "pending",
            audio_url: response.audio.audio_url,
            error: response.audio.error
          })
        }
        
        // Only redirect when ALL scenes are completed
        if (response.status === "completed" && 
            response.progress.completed_scenes === response.progress.total_scenes) {
          setFinalVideoUrl(response.final_video_url)
          shouldStopPolling = true
          if (pollInterval) clearInterval(pollInterval)
          // Stop polling and navigate to video player
          setTimeout(() => {
            if (isMounted) {
              navigate(`/campaigns/${campaignId}/video`)
            }
          }, 2000)
        } else if (response.status === "failed") {
          shouldStopPolling = true
          if (pollInterval) clearInterval(pollInterval)
          setError("Video generation failed. Please try again.")
        }
        
        setLoading(false)
      } catch (error) {
        if (!isMounted) return
        
        console.error("Failed to fetch status:", error)
        const errorMessage = error instanceof Error ? error.message : "Failed to fetch campaign status"
        
        // Only set error if it's not a temporary network issue
        if (errorMessage.includes("404") || errorMessage.includes("403") || errorMessage.includes("Not found")) {
          setError(errorMessage)
          shouldStopPolling = true
          if (pollInterval) clearInterval(pollInterval)
        } else {
          // For other errors, log but don't stop polling (might be temporary)
          setError(null)
        }
        
        setLoading(false)
      }
    }

    // Initial poll immediately
    pollStatus()

    // Poll every 3 seconds for faster updates
    pollInterval = setInterval(() => {
      if (!shouldStopPolling && isMounted) {
        pollStatus()
      }
    }, 3000)

    return () => {
      isMounted = false
      shouldStopPolling = true
      if (pollInterval) {
        clearInterval(pollInterval)
      }
    }
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
      case "processing":
        return {
          stage: "Generating Videos...",
          description: `${progress.completed_scenes} of ${progress.total_scenes} videos complete`,
          icon: <Loader2 className="h-12 w-12 animate-spin text-primary" />
        }
      case "completed":
        return {
          stage: "Complete!",
          description: "All videos are ready",
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
          description: "Working on your videos",
          icon: <Loader2 className="h-12 w-12 animate-spin text-primary" />
        }
    }
  }

  const stageInfo = getStageInfo()
  const scenes = progress.scenes || []

  // Show error state
  if (error && !loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-8">
        <Card className="w-full max-w-2xl">
          <CardHeader className="text-center">
            <XCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
            <CardTitle className="text-2xl mb-2">Error</CardTitle>
            <p className="text-muted-foreground">{error}</p>
          </CardHeader>
          <CardContent className="text-center">
            <button
              onClick={() => navigate(-1)}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
            >
              Go Back
            </button>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Show loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-8">
        <Card className="w-full max-w-2xl">
          <CardHeader className="text-center">
            <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto mb-4" />
            <CardTitle className="text-2xl mb-2">Loading...</CardTitle>
            <p className="text-muted-foreground">Fetching campaign status...</p>
          </CardHeader>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-8">
      <Card className="w-full max-w-3xl">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-6">
            {stageInfo.icon}
          </div>
          <CardTitle className="text-3xl mb-2">{stageInfo.stage}</CardTitle>
          <p className="text-muted-foreground">{stageInfo.description}</p>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Summary Stats */}
            {progress.total_scenes > 0 && (
              <div className="flex justify-center gap-6 mb-6 text-sm">
                <div className="text-center">
                  <div className="text-2xl font-bold text-primary">{progress.completed_scenes}</div>
                  <div className="text-muted-foreground">Complete</div>
                </div>
                {progress.generating_scenes > 0 && (
                  <div className="text-center">
                    <div className="text-2xl font-bold text-yellow-500">{progress.generating_scenes}</div>
                    <div className="text-muted-foreground">Generating</div>
                  </div>
                )}
                {progress.failed_scenes > 0 && (
                  <div className="text-center">
                    <div className="text-2xl font-bold text-destructive">{progress.failed_scenes}</div>
                    <div className="text-muted-foreground">Failed</div>
                  </div>
                )}
                <div className="text-center">
                  <div className="text-2xl font-bold">{progress.total_scenes}</div>
                  <div className="text-muted-foreground">Total</div>
                </div>
              </div>
            )}

            {/* Audio Generation Status */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-3">Soundtrack Generation</h3>
              <AudioStatusItem audioStatus={audioStatus} />
            </div>

            {/* Individual Scene Progress */}
            {scenes.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-lg font-semibold mb-4">Video Generation Progress</h3>
                {scenes.map((scene) => (
                  <SceneProgressItem key={scene.scene_number} scene={scene} />
                ))}
              </div>
            )}
            
            {/* Display video URLs for completed scenes */}
            {scenes.length > 0 && scenes.some(s => s.video_url) && (
              <div className="mt-6 space-y-2">
                <h3 className="text-lg font-semibold mb-3">Generated Videos</h3>
                {scenes
                  .filter(s => s.video_url)
                  .map((scene) => (
                    <div key={scene.scene_number} className="p-3 rounded-lg border bg-card">
                      <div className="flex items-center justify-between">
                        <span className="font-medium">Scene {scene.scene_number}: {scene.title}</span>
                        <a
                          href={scene.video_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm text-primary hover:underline"
                        >
                          View Video
                        </a>
                      </div>
                    </div>
                  ))}
              </div>
            )}

            {/* Fallback for when scenes array is not available */}
            {scenes.length === 0 && progress.total_scenes > 0 && (
              <div className="space-y-3">
                <div className="text-center text-sm text-muted-foreground">
                  <p>
                    {progress.current_scene
                      ? `Generating Scene ${progress.current_scene}... This may take 30-60 seconds per scene.`
                      : "Preparing video generation..."}
                  </p>
                  <p className="mt-2">
                    Progress: {progress.completed_scenes} of {progress.total_scenes} scenes completed
                  </p>
                </div>
              </div>
            )}

            {/* Status message */}
            {(status === "generating" || status === "processing") && (
              <div className="mt-6 text-center text-sm text-muted-foreground">
                <p>Videos are being generated in parallel. This usually takes 2-3 minutes.</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function AudioStatusItem({ audioStatus }) {
  const getStatusIcon = () => {
    switch (audioStatus.status) {
      case "completed":
        return <CheckCircle2 className="h-5 w-5 text-green-500 flex-shrink-0" />
      case "generating":
        return <Loader2 className="h-5 w-5 animate-spin text-primary flex-shrink-0" />
      case "failed":
        return <XCircle className="h-5 w-5 text-destructive flex-shrink-0" />
      default:
        return <div className="h-5 w-5 rounded-full border-2 border-muted flex-shrink-0" />
    }
  }

  const getStatusText = () => {
    switch (audioStatus.status) {
      case "completed":
        return "Soundtrack Ready"
      case "generating":
        return "Generating Soundtrack..."
      case "failed":
        return "Soundtrack Generation Failed"
      default:
        return "Pending"
    }
  }

  return (
    <div className="flex items-center gap-3 p-3 rounded-lg border bg-card">
      {getStatusIcon()}
      <div className="flex-1">
        <div className="flex items-center justify-between">
          <p className={`font-medium ${
            audioStatus.status === "completed" 
              ? "text-foreground" 
              : "text-muted-foreground"
          }`}>
            {getStatusText()}
          </p>
          <span className={`text-xs px-2 py-1 rounded ${
            audioStatus.status === "completed" 
              ? "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300"
              : audioStatus.status === "failed"
              ? "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300"
              : audioStatus.status === "generating"
              ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300"
              : "bg-muted text-muted-foreground"
          }`}>
            {audioStatus.status}
          </span>
        </div>
        {audioStatus.error && (
          <p className="text-xs text-destructive mt-1">Error: {audioStatus.error}</p>
        )}
      </div>
    </div>
  )
}

function SceneProgressItem({ scene }) {
  const getStatusIcon = () => {
    switch (scene.status) {
      case "completed":
        return <CheckCircle2 className="h-5 w-5 text-green-500 flex-shrink-0" />
      case "generating":
      case "retrying":
        return <Loader2 className="h-5 w-5 animate-spin text-primary flex-shrink-0" />
      case "failed":
        return <XCircle className="h-5 w-5 text-destructive flex-shrink-0" />
      default:
        return <div className="h-5 w-5 rounded-full border-2 border-muted flex-shrink-0" />
    }
  }

  const getStatusText = () => {
    switch (scene.status) {
      case "completed":
        return "Complete"
      case "generating":
        return "Generating..."
      case "retrying":
        return "Retrying..."
      case "failed":
        return "Failed"
      default:
        return "Pending"
    }
  }

  return (
    <div className="flex items-center gap-3 p-3 rounded-lg border bg-card">
      {getStatusIcon()}
      <div className="flex-1">
        <div className="flex items-center justify-between">
          <p className={`font-medium ${scene.status === "completed" ? "text-foreground" : "text-muted-foreground"}`}>
            Scene {scene.scene_number}: {scene.title || `Scene ${scene.scene_number}`}
          </p>
          <span className={`text-xs px-2 py-1 rounded ${
            scene.status === "completed" 
              ? "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300"
              : scene.status === "failed"
              ? "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300"
              : scene.status === "generating" || scene.status === "retrying"
              ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300"
              : "bg-muted text-muted-foreground"
          }`}>
            {getStatusText()}
          </span>
        </div>
        {scene.error && (
          <p className="text-xs text-destructive mt-1">Error: {scene.error}</p>
        )}
        {scene.video_url && (
          <a
            href={scene.video_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-primary hover:underline mt-1 block"
          >
            View Video →
          </a>
        )}
      </div>
    </div>
  )
}

