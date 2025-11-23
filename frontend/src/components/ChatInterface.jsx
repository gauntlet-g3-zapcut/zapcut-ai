import { useState, useEffect } from "react"
import { 
  Conversation, 
  ConversationContent,
} from "./ui/ai/conversation"
import { 
  Message, 
  MessageAvatar, 
  MessageContent 
} from "./ui/ai/message"
import {
  PromptInput,
  PromptInputTextarea,
  PromptInputSubmit,
  PromptInputMic,
} from "./ui/ai/prompt-input"
import { Loader } from "./ui/ai/loader"
import { Button } from "./ui/button"
import { GradientButton } from "./ui/gradient-button"
import { CheckCircle2, Sparkles } from "lucide-react"
import { cn } from "../lib/utils"

export default function ChatInterface({
  messages = [],
  onSendMessage,
  isLoading = false,
  progress = 0,
  isComplete = false,
  onComplete
}) {
  const [inputValue, setInputValue] = useState("")
  const [isGenerating, setIsGenerating] = useState(false)

  const progressPercentage = (progress / 5) * 100

  const handleSubmit = (message) => {
    if (message && message.trim() && !isLoading) {
      onSendMessage(message.trim())
      setInputValue("")
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Progress indicator */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-muted-foreground">Progress</span>
          <span className="text-xs text-muted-foreground">{progress}/5</span>
        </div>
        <div className="relative w-full bg-gray-100 rounded-full h-1.5 overflow-hidden">
          <div
            className="absolute top-0 left-0 h-full bg-green-500 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-hidden mb-4 rounded-lg shadow-sm bg-white/80 backdrop-blur-sm">
        <Conversation>
          <ConversationContent>
            {messages.length === 0 && !isLoading && (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <div className="w-16 h-16 rounded-full bg-purple-50 border border-purple-100 flex items-center justify-center mb-4 animate-pulse">
                  <Sparkles className="w-8 h-8 text-purple-600" />
                </div>
                <p className="text-muted-foreground text-sm font-medium">Starting conversation...</p>
                <p className="text-muted-foreground/70 text-xs mt-1">The AI consultant will greet you shortly</p>
              </div>
            )}
            
            {messages.map((message, index) => (
              <Message 
                key={index} 
                from={message.role}
                className="animate-in fade-in slide-in-from-bottom-2 duration-300"
                style={{ animationDelay: `${index * 50}ms` }}
              >
                <MessageAvatar from={message.role} />
                <MessageContent from={message.role}>
                  <p className="text-sm whitespace-pre-wrap leading-relaxed">{message.content}</p>
                  {message.created_at && (
                    <p className={cn(
                      "text-xs mt-2",
                      message.role === "user" 
                        ? "text-white/70" 
                        : "text-muted-foreground"
                    )}>
                      {new Date(message.created_at).toLocaleTimeString([], { 
                        hour: '2-digit', 
                        minute: '2-digit' 
                      })}
                    </p>
                  )}
                </MessageContent>
              </Message>
            ))}
            
            {isLoading && <Loader />}
          </ConversationContent>
        </Conversation>
      </div>

      {/* Input area */}
      {isComplete ? (
        <div className="space-y-2 animate-in fade-in slide-in-from-bottom-4 duration-300">
          {!isGenerating ? (
            <div className="flex justify-center">
              <GradientButton
                onClick={async () => {
                  setIsGenerating(true)
                  try {
                    await onComplete()
                  } catch (error) {
                    setIsGenerating(false)
                  }
                }}
                className="px-6 py-3 text-sm"
              >
                Generate Storyline
                <Sparkles className="w-4 h-4 ml-2" />
              </GradientButton>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-8 space-y-4">
              <div className="w-16 h-16 rounded-full bg-purple-50 border border-purple-100 flex items-center justify-center animate-pulse shadow-sm">
                <Sparkles className="w-8 h-8 text-purple-600 animate-spin" />
              </div>
              <div className="text-center">
                <p className="text-lg font-semibold text-foreground">
                  Generating Storyline
                  <span className="inline-flex gap-1 ml-2">
                    <span className="w-1.5 h-1.5 bg-purple-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                    <span className="w-1.5 h-1.5 bg-purple-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                    <span className="w-1.5 h-1.5 bg-purple-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                  </span>
                </p>
              </div>
            </div>
          )}
        </div>
      ) : (
        <PromptInput onSubmit={handleSubmit}>
          <div className="relative">
            <PromptInputTextarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Ask anything"
              disabled={isLoading}
            />
            <PromptInputMic />
            <PromptInputSubmit disabled={!inputValue.trim() || isLoading} />
          </div>
        </PromptInput>
      )}
    </div>
  )
}
