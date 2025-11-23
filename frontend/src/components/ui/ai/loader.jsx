import { Sparkles } from "lucide-react"
import { cn } from "../../../lib/utils"

export function Loader({ className, ...props }) {
  return (
    <div className={cn("flex items-center gap-3", className)} {...props}>
      <div className="w-8 h-8 rounded-full bg-purple-50 text-purple-600 border border-purple-100 flex items-center justify-center shrink-0">
        <Sparkles className="w-4 h-4" />
      </div>
      <div className="bg-white/90 backdrop-blur-sm border border-purple-100 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
        <div className="flex space-x-1.5">
          <div 
            className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" 
            style={{ animationDelay: "0ms" }} 
          />
          <div 
            className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" 
            style={{ animationDelay: "150ms" }} 
          />
          <div 
            className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" 
            style={{ animationDelay: "300ms" }} 
          />
        </div>
      </div>
    </div>
  )
}

