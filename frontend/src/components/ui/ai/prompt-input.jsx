import { useRef, useEffect } from "react"
import { Button } from "../button"
import { Textarea } from "../textarea"
import { Mic, Send } from "lucide-react"
import { cn } from "../../../lib/utils"

export function PromptInput({ children, onSubmit, className, ...props }) {
  const handleSubmit = (e) => {
    e.preventDefault()
    const formData = new FormData(e.target)
    const message = formData.get("message")
    if (message && typeof message === "string" && message.trim()) {
      onSubmit?.(message.trim())
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className={cn("bg-white/80 backdrop-blur-sm p-4", className)}
      {...props}
    >
      {children}
    </form>
  )
}

export function PromptInputTextarea({ 
  value = "", 
  onChange, 
  placeholder = "Ask anything",
  disabled = false,
  className,
  ...props 
}) {
  const textareaRef = useRef(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }, [value])

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      const form = e.target.closest("form")
      if (form) {
        form.requestSubmit()
      }
    }
  }

  return (
    <Textarea
      ref={textareaRef}
      name="message"
      value={value}
      onChange={onChange}
      onKeyDown={handleKeyDown}
      placeholder={placeholder}
      disabled={disabled}
      rows={1}
      className={cn(
        "min-h-[44px] max-h-[200px] resize-none rounded-[9999px] px-4 py-3 pr-28 border border-gray-200 bg-white shadow-sm focus-visible:outline-none focus-visible:ring-0 focus-visible:border-gray-300 placeholder:text-gray-400 text-sm",
        className
      )}
      {...props}
    />
  )
}

export function PromptInputToolbar({ children, className, ...props }) {
  return (
    <div className={cn("flex items-center justify-between", className)} {...props}>
      {children}
    </div>
  )
}

export function PromptInputSubmit({ disabled = false, className, ...props }) {
  return (
    <Button
      type="submit"
      variant="ghost"
      disabled={disabled}
      size="icon"
      className={cn("absolute right-2 top-1/2 -translate-y-1/2 h-10 w-10 rounded-full bg-gray-100 hover:bg-gray-200 border border-gray-200", className)}
      {...props}
    >
      <Send className="w-4 h-4" />
    </Button>
  )
}

export function PromptInputMic({ onClick, className, ...props }) {
  return (
    <Button
      type="button"
      variant="ghost"
      size="icon"
      onClick={onClick}
      className={cn("absolute right-14 top-1/2 -translate-y-1/2 h-10 w-10 text-gray-600 hover:text-gray-900 hover:bg-transparent", className)}
      {...props}
    >
      <Mic className="w-5 h-5" />
    </Button>
  )
}

export function PromptInputButton({ children, className, ...props }) {
  return (
    <Button
      variant="ghost"
      size="icon"
      className={cn("h-10 w-10", className)}
      {...props}
    >
      {children}
    </Button>
  )
}

