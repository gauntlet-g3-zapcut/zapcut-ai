import { Loader2 } from "lucide-react"
import { useLoading } from "../context/LoadingContext"

export default function GlobalLoadingIndicator() {
  const { isLoading, loadingMessage } = useLoading()

  if (!isLoading) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-lg p-8 shadow-xl flex flex-col items-center gap-4 max-w-sm mx-4">
        <Loader2 className="h-12 w-12 animate-spin text-purple-600" />
        <p className="text-lg font-medium text-center">{loadingMessage}</p>
      </div>
    </div>
  )
}

