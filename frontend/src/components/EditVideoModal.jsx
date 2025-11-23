import { useState, useEffect } from "react"
import { Button } from "./ui/button"
import { Textarea } from "./ui/textarea"
import { X, Loader2 } from "lucide-react"

export function EditVideoModal({ scene, isOpen, onClose, onRegenerate }) {
  const [prompt, setPrompt] = useState("")
  const [isRegenerating, setIsRegenerating] = useState(false)

  useEffect(() => {
    if (scene?.sora_prompt) {
      setPrompt(scene.sora_prompt)
    }
  }, [scene])

  if (!isOpen || !scene) return null

  const handleRegenerate = async () => {
    if (!prompt.trim()) {
      alert("Please enter a prompt")
      return
    }

    setIsRegenerating(true)
    try {
      await onRegenerate(scene.scene_number, prompt)
      onClose()
    } catch (error) {
      console.error("Failed to regenerate video:", error)
      alert("Failed to regenerate video. Please try again.")
    } finally {
      setIsRegenerating(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-2xl font-semibold" style={{ fontFamily: "'Playfair Display', serif" }}>
            Edit Scene {scene.scene_number}
          </h2>
          <button
            onClick={onClose}
            disabled={isRegenerating}
            className="text-gray-400 hover:text-gray-600 transition-colors disabled:opacity-50"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Scene Title
            </label>
            <p className="text-gray-900 font-medium">{scene.title || `Scene ${scene.scene_number}`}</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Video Generation Prompt
            </label>
            <Textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              disabled={isRegenerating}
              placeholder="Enter the prompt for video generation..."
              className="min-h-[200px] resize-none"
            />
            <p className="text-xs text-gray-500 mt-2">
              Edit the prompt to change how the video is generated. Be specific and descriptive.
            </p>
          </div>

          {/* Preview current video */}
          {scene.video_url && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Current Video
              </label>
              <div className="relative aspect-video bg-black rounded overflow-hidden">
                <video
                  src={scene.video_url}
                  controls
                  className="w-full h-full"
                >
                  Your browser does not support the video tag.
                </video>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200 bg-gray-50">
          <Button
            variant="outline"
            onClick={onClose}
            disabled={isRegenerating}
          >
            Cancel
          </Button>
          <Button
            onClick={handleRegenerate}
            disabled={isRegenerating || !prompt.trim()}
            className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white"
          >
            {isRegenerating ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Regenerating...
              </>
            ) : (
              "Regenerate Video"
            )}
          </Button>
        </div>
      </div>
    </div>
  )
}

