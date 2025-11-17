import { useRef, useEffect } from "react"
import { Button } from "../button"
import { Textarea } from "../textarea"
import { Send } from "lucide-react"
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
      className={cn("flex flex-col gap-2 border-t bg-white/80 backdrop-blur-sm p-4", className)}
      {...props}
    >
      {children}
    </form>
  )
}

export function PromptInputTextarea({ 
  value = "", 
  onChange, 
  placeholder = "Type your message...",
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
        "min-h-[44px] max-h-[200px] resize-none pr-12",
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
      variant="outline"
      disabled={disabled}
      size="lg"
      className={cn("h-12 px-6 shadow-sm hover:shadow-md transition-all border-purple-200 hover:border-purple-300", className)}
      {...props}
    >
      <Send className="w-4 h-4 mr-2" />
      Send
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

