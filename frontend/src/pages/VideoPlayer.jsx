import { useState, useEffect, useRef, useMemo } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { Button } from "../components/ui/button"
import { GradientButton } from "@/components/ui/gradient-button"
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/card"
import { api } from "../services/api"
import { Download, Share2, ArrowLeft, Play, Volume2, VolumeX, Edit } from "lucide-react"
import { prepareEditorProject } from "@/lib/editor-bridge"
import { EditVideoModal } from "../components/EditVideoModal"

export default function VideoPlayer() {
  const { campaignId } = useParams()
  const navigate = useNavigate()
  const [campaign, setCampaign] = useState(null)
  const [statusData, setStatusData] = useState(null)
  const [selectedScene, setSelectedScene] = useState(null)
  const [loading, setLoading] = useState(true)
  const [shareLink, setShareLink] = useState("")
  const [isPlayingAll, setIsPlayingAll] = useState(false)
  const [currentSceneIndex, setCurrentSceneIndex] = useState(0)
  const [audioMuted, setAudioMuted] = useState(false)
  const [isSyncingEditor, setIsSyncingEditor] = useState(false)
  const [editingScene, setEditingScene] = useState(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const videoRef = useRef(null)
  const audioRef = useRef(null)
  const scenesRef = useRef([])

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
          const completedScenes = statusResponse.progress.scenes.filter(
            s => s.status === "completed" && s.video_url
          )
          scenesRef.current = completedScenes
          if (completedScenes.length > 0) {
            setSelectedScene(completedScenes[0])
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

  const completedScenes = useMemo(() => {
    if (!statusData?.progress?.scenes) {
      return []
    }
    return statusData.progress.scenes
      .filter((scene) => scene.status === "completed" && scene.video_url)
      .sort((a, b) => {
        const aOrder = a.scene_number ?? a.order ?? a.index ?? 0
        const bOrder = b.scene_number ?? b.order ?? b.index ?? 0
        return aOrder - bOrder
      })
  }, [statusData?.progress?.scenes])

  useEffect(() => {
    scenesRef.current = completedScenes
  }, [completedScenes])

  useEffect(() => {
    if (completedScenes.length === 0) {
      return
    }

    if (
      !selectedScene ||
      !completedScenes.some(
        (scene) =>
          scene.scene_number === selectedScene.scene_number && scene.video_url === selectedScene.video_url
      )
    ) {
      setSelectedScene(completedScenes[0])
    }
  }, [completedScenes, selectedScene])

  const soundtrackAsset = useMemo(() => {
    if (!statusData?.audio?.audio_url || statusData.audio.status !== "completed") {
      return null
    }

    return {
      url: statusData.audio.audio_url,
      name: statusData.audio.file_name || statusData.audio.title || "Soundtrack"
    }
  }, [statusData?.audio])

  const finalCompositeAsset = useMemo(() => {
    if (!campaign?.final_video_url) {
      return null
    }

    const labelBase =
      campaign.title || campaign.name || campaign.brand_title || `Campaign ${campaignId}`

    return {
      url: campaign.final_video_url,
      name: `${labelBase} - Final Cut`
    }
  }, [campaign, campaignId])

  const editorProjectName = useMemo(() => {
    return (
      campaign?.title ||
      campaign?.name ||
      campaign?.brand_title ||
      (campaign ? `Campaign ${campaign.id}` : `Campaign ${campaignId}`)
    )
  }, [campaign, campaignId])

  const handleAddToEditor = async () => {
    if (completedScenes.length === 0 || isSyncingEditor) {
      return
    }

    setIsSyncingEditor(true)

    try {
      await prepareEditorProject({
        projectName: editorProjectName,
        videos: completedScenes.map((scene, index) => ({
          url: scene.video_url,
          name: scene.title?.trim() || `Scene ${scene.scene_number ?? index + 1}`,
          order: scene.scene_number ?? index + 1,
          sceneNumber: scene.scene_number
        })),
        audio: soundtrackAsset || undefined,
        includeFinalComposite: finalCompositeAsset || undefined
      })

      navigate("/editor")
    } catch (error) {
      console.error("Failed to sync project to editor:", error)
      alert("We couldn't load this campaign into the editor. Please try again.")
    } finally {
      setIsSyncingEditor(false)
    }
  }

  const handlePlayAll = () => {
    const completedScenes = scenesRef.current
    if (completedScenes.length === 0) return

    setIsPlayingAll(true)
    setCurrentSceneIndex(0)
    setSelectedScene(completedScenes[0])
    
    // Start audio if available
    if (statusData?.audio?.audio_url && audioRef.current) {
      audioRef.current.play().catch(err => {
        console.error("Failed to play audio:", err)
      })
    }

    // Start first video
    setTimeout(() => {
      if (videoRef.current) {
        videoRef.current.play().catch(err => {
          console.error("Failed to play video:", err)
        })
      }
    }, 100)
  }

  const handleVideoEnd = () => {
    if (!isPlayingAll) return

    const completedScenes = scenesRef.current
    const nextIndex = currentSceneIndex + 1

    if (nextIndex < completedScenes.length) {
      setCurrentSceneIndex(nextIndex)
      setSelectedScene(completedScenes[nextIndex])
      
      // Play next video
      setTimeout(() => {
        if (videoRef.current) {
          videoRef.current.currentTime = 0
          videoRef.current.play().catch(err => {
            console.error("Failed to play video:", err)
          })
        }
      }, 100)
    } else {
      // All scenes played
      setIsPlayingAll(false)
      if (audioRef.current) {
        audioRef.current.pause()
        audioRef.current.currentTime = 0
      }
    }
  }

  const toggleAudioMute = () => {
    if (audioRef.current) {
      audioRef.current.muted = !audioMuted
      setAudioMuted(!audioMuted)
    }
  }

  const handleEditScene = (scene) => {
    setEditingScene(scene)
    setIsModalOpen(true)
  }

  const handleRegenerateVideo = async (sceneNumber, prompt) => {
    try {
      await api.regenerateScene(campaignId, sceneNumber, prompt)
      
      // Update the scene status to regenerating
      if (statusData?.progress?.scenes) {
        const updatedScenes = statusData.progress.scenes.map(s => 
          s.scene_number === sceneNumber 
            ? { ...s, status: "generating", sora_prompt: prompt }
            : s
        )
        setStatusData({
          ...statusData,
          progress: {
            ...statusData.progress,
            scenes: updatedScenes
          }
        })
      }

      // Start polling for updated status
      const pollInterval = setInterval(async () => {
        try {
          const statusResponse = await api.getCampaignStatus(campaignId)
          setStatusData(statusResponse)
          
          // Check if the scene has completed or failed
          const scene = statusResponse?.progress?.scenes?.find(s => s.scene_number === sceneNumber)
          if (scene && (scene.status === "completed" || scene.status === "failed")) {
            clearInterval(pollInterval)
            
            // Update completed scenes ref if completed
            if (scene.status === "completed" && scene.video_url) {
              const completedScenes = statusResponse.progress.scenes.filter(
                s => s.status === "completed" && s.video_url
              )
              scenesRef.current = completedScenes
            }
          }
        } catch (error) {
          console.error("Failed to poll campaign status:", error)
          clearInterval(pollInterval)
        }
      }, 3000) // Poll every 3 seconds

      // Stop polling after 5 minutes
      setTimeout(() => clearInterval(pollInterval), 300000)
      
    } catch (error) {
      console.error("Failed to regenerate video:", error)
      throw error
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-pink-50 flex items-center justify-center">
        <div className="text-muted-foreground">Loading video...</div>
      </div>
    )
  }

  if (!campaign) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-pink-50 flex items-center justify-center">
        <div className="text-destructive">Campaign not found</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-pink-50 p-8">
      <div className="max-w-6xl mx-auto">
        <Button
          variant="ghost"
          onClick={() => navigate("/dashboard")}
          className="mb-6 hover:bg-white/50 transition-colors"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Dashboard
        </Button>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Video Player */}
          <div className="lg:col-span-2">
            {selectedScene?.video_url ? (
              <Card className="p-0 overflow-hidden shadow-lg bg-white/80 backdrop-blur-sm border-purple-100">
                <div className="relative">
                  <video
                    ref={videoRef}
                    controls
                    className="w-full aspect-video bg-black"
                    src={selectedScene.video_url}
                    key={selectedScene.scene_number}
                    onEnded={handleVideoEnd}
                    muted={false}
                  >
                    Your browser does not support the video tag.
                  </video>
                  {/* Background audio track */}
                  {statusData?.audio?.audio_url && (
                    <audio
                      ref={audioRef}
                      src={statusData.audio.audio_url}
                      loop={false}
                      muted={audioMuted}
                    />
                  )}
                </div>
              </Card>
            ) : (
              <Card className="p-12 text-center shadow-lg bg-white/80 backdrop-blur-sm border-purple-100">
                <p className="text-muted-foreground">No video selected</p>
              </Card>
            )}

            {/* Action Buttons */}
            {selectedScene?.video_url && (
              <div className="mt-6 space-y-4">
                <GradientButton
                  onClick={handleAddToEditor}
                  className="w-full"
                  disabled={completedScenes.length === 0 || isSyncingEditor}
                >
                  {isSyncingEditor ? "Adding to Editor..." : "Add to Editor"}
                </GradientButton>
                {/* Play All Button */}
                {scenesRef.current.length > 1 && (
                  <GradientButton 
                    onClick={handlePlayAll} 
                    className="w-full"
                    disabled={isPlayingAll}
                  >
                    <Play className="mr-2 h-4 w-4" />
                    {isPlayingAll ? "Playing All Scenes..." : "Play All Scenes with Soundtrack"}
                  </GradientButton>
                )}
                
                {/* Audio Controls */}
                {statusData?.audio?.audio_url && (
                  <Card className="p-4 flex items-center gap-3 shadow-sm bg-white/80 backdrop-blur-sm border-purple-100">
                    <Button 
                      onClick={toggleAudioMute} 
                      variant="outline"
                      size="sm"
                      className="border-purple-200 hover:bg-purple-50"
                    >
                      {audioMuted ? (
                        <VolumeX className="h-4 w-4" />
                      ) : (
                        <Volume2 className="h-4 w-4" />
                      )}
                    </Button>
                    <span className="text-sm font-medium text-foreground">
                      {audioMuted ? "Soundtrack Muted" : "Soundtrack Playing"}
                    </span>
                  </Card>
                )}

                <div className="grid grid-cols-3 gap-4">
                  <Button 
                    onClick={() => handleDownloadMP4(selectedScene.video_url)} 
                    variant="outline"
                    className="border-purple-200 hover:bg-purple-50 hover:border-purple-300"
                  >
                    <Download className="mr-2 h-4 w-4" />
                    Download MP4
                  </Button>
                  <Button 
                    onClick={handleDownloadWebM} 
                    variant="outline"
                    className="border-purple-200 hover:bg-purple-50 hover:border-purple-300"
                  >
                    <Download className="mr-2 h-4 w-4" />
                    Download WebM
                  </Button>
                  <Button 
                    onClick={handleShare} 
                    variant="outline"
                    className="border-purple-200 hover:bg-purple-50 hover:border-purple-300"
                  >
                    <Share2 className="mr-2 h-4 w-4" />
                    Share Link
                  </Button>
                </div>
              </div>
            )}
          </div>

          {/* Sidebar Info */}
          <div className="space-y-6">
            <Card className="shadow-lg bg-white/80 backdrop-blur-sm border-purple-100">
              <CardHeader>
                <CardTitle className="text-xl" style={{ fontFamily: "'Playfair Display', serif" }}>
                  Video Details
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div>
                  <p className="text-muted-foreground">Status</p>
                  <p className="font-medium capitalize">{campaign.status}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Duration</p>
                  <p className="font-medium">30 seconds</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Quality</p>
                  <p className="font-medium">4K (3840×2160)</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Soundtrack</p>
                  <p className={`font-medium ${
                    statusData?.audio?.status === "completed" 
                      ? "text-green-600" 
                      : statusData?.audio?.status === "failed"
                      ? "text-red-600"
                      : statusData?.audio?.status === "generating"
                      ? "text-yellow-600"
                      : ""
                  }`}>
                    {statusData?.audio?.status === "completed" ? "Ready" :
                     statusData?.audio?.status === "generating" ? "Generating..." :
                     statusData?.audio?.status === "failed" ? "Failed" :
                     "Pending"}
                  </p>
                </div>
                <div>
                  <p className="text-muted-foreground">Created</p>
                  <p className="font-medium">
                    {new Date(campaign.created_at).toLocaleDateString()}
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card className="shadow-lg bg-white/80 backdrop-blur-sm border-purple-100">
              <CardHeader>
                <CardTitle className="text-xl" style={{ fontFamily: "'Playfair Display', serif" }}>
                  What's Next?
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <GradientButton
                  className="w-full"
                  onClick={() => navigate(`/brands/${campaign.brand_id}/chat`)}
                >
                  Create Another Ad
                </GradientButton>
                <Button
                  variant="outline"
                  className="w-full border-purple-200 hover:bg-purple-50 hover:border-purple-300"
                  onClick={() => navigate("/dashboard")}
                >
                  View All Brands
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* All Scene Videos */}
        {statusData?.progress?.scenes && statusData.progress.scenes.length > 0 && (
          <div className="mt-12">
            <h2 className="text-2xl font-semibold mb-6" style={{ fontFamily: "'Playfair Display', serif" }}>
              All Scene Videos
            </h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {statusData.progress.scenes.map((scene) => (
                <Card 
                  key={scene.scene_number} 
                  className={`p-4 cursor-pointer transition-all hover:shadow-lg shadow-sm bg-white/80 backdrop-blur-sm border-purple-100 group ${
                    selectedScene?.scene_number === scene.scene_number 
                      ? "ring-2 ring-purple-400 border-purple-400" 
                      : "hover:border-purple-200"
                  }`}
                  onClick={() => scene.video_url && setSelectedScene(scene)}
                >
                  {scene.video_url && scene.status !== "generating" ? (
                    <div className="relative aspect-video bg-black rounded mb-3 overflow-hidden">
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
                      <div className="absolute inset-0 flex items-center justify-center bg-black/30 group-hover:bg-black/20 transition-colors">
                        <Play className="h-10 w-10 text-white drop-shadow-lg" />
                      </div>
                    </div>
                  ) : (
                    <div className="aspect-video bg-gradient-to-br from-purple-100 to-pink-100 rounded mb-3 flex items-center justify-center">
                      <div className="flex flex-col items-center gap-2">
                        {scene.status === "generating" && (
                          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
                        )}
                        <p className="text-xs text-muted-foreground font-medium">
                          {scene.status === "generating" ? "Generating..." : 
                           scene.status === "retrying" ? "Retrying..." :
                           scene.status === "failed" ? "Failed" : "Pending"}
                        </p>
                      </div>
                    </div>
                  )}
                  <p className="text-sm font-semibold mb-1">Scene {scene.scene_number}</p>
                  <p className="text-xs text-muted-foreground line-clamp-2 mb-3">
                    {scene.title || `Scene ${scene.scene_number}`}
                  </p>
                  {scene.status === "generating" || scene.status === "retrying" ? (
                    <div className="text-center py-2">
                      <p className="text-xs text-purple-600 font-medium">
                        {scene.status === "retrying" ? "Retrying generation..." : "Generating video..."}
                      </p>
                    </div>
                  ) : scene.video_url ? (
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        className="flex-1 border-purple-200 hover:bg-purple-50 hover:border-purple-300"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDownloadMP4(scene.video_url)
                        }}
                      >
                        <Download className="mr-2 h-3 w-3" />
                        Download
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="flex-1 border-purple-200 hover:bg-purple-50 hover:border-purple-300"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleEditScene(scene)
                        }}
                      >
                        <Edit className="mr-2 h-3 w-3" />
                        Edit
                      </Button>
                    </div>
                  ) : scene.status === "failed" ? (
                    <Button
                      size="sm"
                      variant="outline"
                      className="w-full border-red-200 hover:bg-red-50 hover:border-red-300 text-red-600"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleEditScene(scene)
                      }}
                    >
                      <Edit className="mr-2 h-3 w-3" />
                      Retry
                    </Button>
                  ) : null}
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Edit Video Modal */}
        <EditVideoModal
          scene={editingScene}
          isOpen={isModalOpen}
          onClose={() => {
            setIsModalOpen(false)
            setEditingScene(null)
          }}
          onRegenerate={handleRegenerateVideo}
        />
      </div>
    </div>
  )
}

