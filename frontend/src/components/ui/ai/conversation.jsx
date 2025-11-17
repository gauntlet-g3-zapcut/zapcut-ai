import { useEffect, useRef, useState } from "react"
import { Button } from "../button"
import { ChevronDown } from "lucide-react"
import { cn } from "../../../lib/utils"

export function Conversation({ children, className, ...props }) {
  const [showScrollButton, setShowScrollButton] = useState(false)
  const containerRef = useRef(null)
  const contentRef = useRef(null)

  const checkScrollPosition = () => {
    if (!containerRef.current || !contentRef.current) return
    
    const container = containerRef.current
    const content = contentRef.current
    const isAtBottom = 
      container.scrollHeight - container.scrollTop - container.clientHeight < 100
    
    setShowScrollButton(!isAtBottom)
  }

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    container.addEventListener("scroll", checkScrollPosition)
    checkScrollPosition()

    return () => {
      container.removeEventListener("scroll", checkScrollPosition)
    }
  }, [children])

  const scrollToBottom = () => {
    if (containerRef.current) {
      containerRef.current.scrollTo({
        top: containerRef.current.scrollHeight,
        behavior: "smooth",
      })
    }
  }

  return (
    <div
      ref={containerRef}
      className={cn(
        "relative flex-1 overflow-y-auto",
        className
      )}
      {...props}
    >
      <div ref={contentRef} className="h-full">
        {children}
      </div>
      {showScrollButton && (
        <ConversationScrollButton onClick={scrollToBottom} />
      )}
    </div>
  )
}

export function ConversationContent({ children, className, ...props }) {
  const messagesEndRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [children])

  return (
    <div className={cn("flex flex-col gap-4 p-4", className)} {...props}>
      {children}
      <div ref={messagesEndRef} />
    </div>
  )
}

export function ConversationScrollButton({ onClick, className, ...props }) {
  return (
    <Button
      variant="outline"
      size="icon"
      className={cn(
        "absolute bottom-4 right-4 h-8 w-8 rounded-full shadow-lg",
        className
      )}
      onClick={onClick}
      {...props}
    >
      <ChevronDown className="h-4 w-4" />
    </Button>
  )
}

