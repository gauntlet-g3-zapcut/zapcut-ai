import { useState, useEffect } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { Button } from "../components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card"
import { api } from "../services/api"
import { Loader2, CheckCircle2, XCircle, Sparkles, Music, Video, ArrowLeft } from "lucide-react"

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
          icon: (
            <div className="relative">
              <div className="absolute inset-0 rounded-full bg-purple-200/50 animate-ping"></div>
              <div className="relative w-16 h-16 rounded-full bg-gradient-to-br from-purple-100 to-pink-100 border-2 border-purple-200 flex items-center justify-center shadow-lg">
                <Sparkles className="h-8 w-8 text-purple-600 animate-spin" style={{ animationDuration: '2s' }} />
              </div>
            </div>
          )
        }
      case "generating":
      case "processing":
        return {
          stage: "Generating Videos...",
          description: `${progress.completed_scenes} of ${progress.total_scenes} videos complete`,
          icon: (
            <div className="relative">
              <div className="absolute inset-0 rounded-full bg-purple-200/50 animate-ping"></div>
              <div className="relative w-16 h-16 rounded-full bg-gradient-to-br from-purple-100 to-pink-100 border-2 border-purple-200 flex items-center justify-center shadow-lg">
                <Video className="h-8 w-8 text-purple-600 animate-pulse" />
              </div>
            </div>
          )
        }
      case "completed":
        return {
          stage: "Complete!",
          description: "All videos are ready",
          icon: (
            <div className="w-16 h-16 rounded-full bg-green-100 border-2 border-green-200 flex items-center justify-center shadow-lg">
              <CheckCircle2 className="h-8 w-8 text-green-600" />
            </div>
          )
        }
      case "failed":
        return {
          stage: "Generation Failed",
          description: "Something went wrong. Please try again.",
          icon: (
            <div className="w-16 h-16 rounded-full bg-red-100 border-2 border-red-200 flex items-center justify-center shadow-lg">
              <XCircle className="h-8 w-8 text-red-600" />
            </div>
          )
        }
      default:
        return {
          stage: "Processing...",
          description: "Working on your videos",
          icon: (
            <div className="relative">
              <div className="absolute inset-0 rounded-full bg-purple-200/50 animate-ping"></div>
              <div className="relative w-16 h-16 rounded-full bg-gradient-to-br from-purple-100 to-pink-100 border-2 border-purple-200 flex items-center justify-center shadow-lg">
                <Loader2 className="h-8 w-8 text-purple-600 animate-spin" />
              </div>
            </div>
          )
        }
    }
  }

  const stageInfo = getStageInfo()
  const scenes = progress.scenes || []

  // Show error state
  if (error && !loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-pink-50 p-4 sm:p-6 lg:p-8">
        <div className="max-w-4xl mx-auto">
          <Button
            variant="ghost"
            onClick={() => navigate(-1)}
            className="mb-6 hover:bg-white/50 transition-colors"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Go Back
          </Button>
          <Card className="shadow-lg bg-white/80 backdrop-blur-sm border-red-100">
            <CardHeader className="text-center pb-4 border-b border-red-100">
              <div className="w-16 h-16 rounded-full bg-red-100 border-2 border-red-200 flex items-center justify-center shadow-lg mx-auto mb-4">
                <XCircle className="h-8 w-8 text-red-600" />
              </div>
              <CardTitle className="text-3xl mb-2" style={{ fontFamily: "'Playfair Display', serif" }}>
                Error
              </CardTitle>
              <CardDescription className="text-base">{error}</CardDescription>
            </CardHeader>
            <CardContent className="text-center pt-6">
              <Button
                onClick={() => navigate(-1)}
                className="border-purple-200 hover:bg-purple-50 hover:border-purple-300"
              >
                Go Back
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  // Show loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-pink-50 flex items-center justify-center p-4 sm:p-6 lg:p-8" style={{ fontFamily: 'Inter, sans-serif' }}>
        <div className="flex flex-col items-center gap-6">
          {/* Animated Sparkles Icon with pulsing effect */}
          <div className="relative">
            <div className="absolute inset-0 rounded-full bg-purple-200/50 animate-ping"></div>
            <div className="relative w-20 h-20 rounded-full bg-gradient-to-br from-purple-100 to-pink-100 border-2 border-purple-200 flex items-center justify-center shadow-lg">
              <Sparkles className="w-10 h-10 text-purple-600 animate-spin" style={{ animationDuration: '2s' }} />
            </div>
          </div>
          
          {/* Main text with fade animation */}
          <div className="text-center space-y-2">
            <h2 className="text-2xl font-semibold text-foreground animate-pulse" style={{ fontFamily: 'Inter, sans-serif' }}>
              Loading...
            </h2>
            <div className="flex items-center justify-center gap-1 text-sm text-muted-foreground">
              <span>Fetching campaign status</span>
              <span className="flex gap-1">
                <span className="w-1.5 h-1.5 bg-purple-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                <span className="w-1.5 h-1.5 bg-purple-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                <span className="w-1.5 h-1.5 bg-purple-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
              </span>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-pink-50 p-4 sm:p-6 lg:p-8">
      <div className="max-w-4xl mx-auto">
        <Button
          variant="ghost"
          onClick={() => navigate("/dashboard")}
          className="mb-6 hover:bg-white/50 transition-colors"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Dashboard
        </Button>

        <Card className="shadow-lg bg-white/80 backdrop-blur-sm border-purple-100 mb-6">
          <CardHeader className="text-center pb-4 border-b border-purple-100">
            <div className="flex justify-center mb-6">
              {stageInfo.icon}
            </div>
            <CardTitle className="text-3xl mb-2" style={{ fontFamily: "'Playfair Display', serif" }}>
              {stageInfo.stage}
            </CardTitle>
            <CardDescription className="text-base">{stageInfo.description}</CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            {/* Summary Stats */}
            {progress.total_scenes > 0 && (
              <div className="flex justify-center gap-8 mb-8">
                <div className="text-center">
                  <div className="text-3xl font-bold text-purple-600">{progress.completed_scenes}</div>
                  <div className="text-sm text-muted-foreground font-medium">Complete</div>
                </div>
                {progress.generating_scenes > 0 && (
                  <div className="text-center">
                    <div className="text-3xl font-bold text-yellow-600">{progress.generating_scenes}</div>
                    <div className="text-sm text-muted-foreground font-medium">Generating</div>
                  </div>
                )}
                {progress.failed_scenes > 0 && (
                  <div className="text-center">
                    <div className="text-3xl font-bold text-red-600">{progress.failed_scenes}</div>
                    <div className="text-sm text-muted-foreground font-medium">Failed</div>
                  </div>
                )}
                <div className="text-center">
                  <div className="text-3xl font-bold text-gray-700">{progress.total_scenes}</div>
                  <div className="text-sm text-muted-foreground font-medium">Total</div>
                </div>
              </div>
            )}

            {/* Audio Generation Status */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ fontFamily: "'Playfair Display', serif" }}>
                <Music className="w-5 h-5 text-purple-600" />
                Soundtrack Generation
              </h3>
              <AudioStatusItem audioStatus={audioStatus} />
            </div>

            {/* Individual Scene Progress */}
            {scenes.length > 0 && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ fontFamily: "'Playfair Display', serif" }}>
                  <Video className="w-5 h-5 text-purple-600" />
                  Video Generation Progress
                </h3>
                {scenes.map((scene) => (
                  <SceneProgressItem key={scene.scene_number} scene={scene} />
                ))}
              </div>
            )}
            
            {/* Display video URLs for completed scenes */}
            {scenes.length > 0 && scenes.some(s => s.video_url) && (
              <div className="mt-6 space-y-3">
                <h3 className="text-lg font-semibold mb-3" style={{ fontFamily: "'Playfair Display', serif" }}>
                  Generated Videos
                </h3>
                {scenes
                  .filter(s => s.video_url)
                  .map((scene) => (
                    <div key={scene.scene_number} className="p-4 rounded-lg border border-purple-100 bg-white/60 hover:bg-white/80 transition-colors">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-foreground">Scene {scene.scene_number}: {scene.title}</span>
                        <a
                          href={scene.video_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm text-purple-600 hover:text-purple-700 hover:underline font-medium"
                        >
                          View Video →
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
              <div className="mt-6 text-center">
                <div className="inline-flex items-center gap-2 px-4 py-2 bg-purple-50 border border-purple-100 rounded-lg">
                  <Sparkles className="w-4 h-4 text-purple-600 animate-pulse" />
                  <p className="text-sm text-purple-700 font-medium">
                    Videos are being generated in parallel. This usually takes 2-3 minutes.
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
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
    <div className="flex items-center gap-3 p-4 rounded-lg border border-purple-100 bg-white/60 hover:bg-white/80 transition-colors">
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
          <span className={`text-xs px-3 py-1 rounded-full font-medium ${
            audioStatus.status === "completed" 
              ? "bg-green-100 text-green-700"
              : audioStatus.status === "failed"
              ? "bg-red-100 text-red-700"
              : audioStatus.status === "generating"
              ? "bg-yellow-100 text-yellow-700"
              : "bg-gray-100 text-gray-600"
          }`}>
            {audioStatus.status}
          </span>
        </div>
        {audioStatus.error && (
          <p className="text-xs text-red-600 mt-2">Error: {audioStatus.error}</p>
        )}
      </div>
    </div>
  )
}

function SceneProgressItem({ scene }) {
  const getStatusIcon = () => {
    switch (scene.status) {
      case "completed":
        return <CheckCircle2 className="h-5 w-5 text-green-600 flex-shrink-0" />
      case "generating":
      case "retrying":
        return <Loader2 className="h-5 w-5 animate-spin text-purple-600 flex-shrink-0" />
      case "failed":
        return <XCircle className="h-5 w-5 text-red-600 flex-shrink-0" />
      default:
        return <div className="h-5 w-5 rounded-full border-2 border-gray-300 flex-shrink-0" />
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
    <div className="flex items-center gap-3 p-4 rounded-lg border border-purple-100 bg-white/60 hover:bg-white/80 transition-colors">
      {getStatusIcon()}
      <div className="flex-1">
        <div className="flex items-center justify-between">
          <p className={`font-medium ${scene.status === "completed" ? "text-foreground" : "text-muted-foreground"}`}>
            Scene {scene.scene_number}: {scene.title || `Scene ${scene.scene_number}`}
          </p>
          <span className={`text-xs px-3 py-1 rounded-full font-medium ${
            scene.status === "completed" 
              ? "bg-green-100 text-green-700"
              : scene.status === "failed"
              ? "bg-red-100 text-red-700"
              : scene.status === "generating" || scene.status === "retrying"
              ? "bg-yellow-100 text-yellow-700"
              : "bg-gray-100 text-gray-600"
          }`}>
            {getStatusText()}
          </span>
        </div>
        {scene.error && (
          <p className="text-xs text-red-600 mt-2">Error: {scene.error}</p>
        )}
        {scene.video_url && (
          <a
            href={scene.video_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-purple-600 hover:text-purple-700 hover:underline mt-2 block font-medium"
          >
            View Video →
          </a>
        )}
      </div>
    </div>
  )
}

