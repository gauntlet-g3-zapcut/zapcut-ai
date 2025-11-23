import { User, Sparkles } from "lucide-react"
import { cn } from "../../../lib/utils"

export function Message({ children, from = "assistant", className, ...props }) {
  return (
    <div
      className={cn(
        "flex items-start gap-3",
        from === "user" && "flex-row-reverse",
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}

export function MessageAvatar({ from = "assistant", className, ...props }) {
  return (
    <div
      className={cn(
        "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
        from === "user"
          ? "bg-purple-100 text-purple-700 border border-purple-200"
          : "bg-purple-50 text-purple-600 border border-purple-100",
        className
      )}
      {...props}
    >
      {from === "user" ? (
        <User className="h-4 w-4" />
      ) : (
        <Sparkles className="h-4 w-4" />
      )}
    </div>
  )
}

export function MessageContent({ children, from = "assistant", className, ...props }) {
  return (
    <div
      className={cn(
        "max-w-[75%] rounded-2xl px-4 py-3 shadow-sm",
        from === "user"
          ? "bg-black text-white rounded-tr-sm"
          : "bg-gray-100 rounded-tl-sm",
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}

