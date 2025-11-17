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

  const progressPercentage = (progress / 5) * 100

  const handleSubmit = (message) => {
    if (message && message.trim() && !isLoading) {
      onSendMessage(message.trim())
      setInputValue("")
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Enhanced Progress indicator */}
      <div className="mb-4 p-4 bg-white/80 backdrop-blur-sm rounded-lg border border-purple-100 shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-purple-600" />
            <span className="text-sm font-semibold">Progress</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-foreground">{progress}/5</span>
            <span className="text-xs text-muted-foreground">aspects collected</span>
          </div>
        </div>
        <div className="relative w-full bg-gray-100 rounded-full h-2.5 overflow-hidden">
          <div
            className="absolute top-0 left-0 h-full bg-gradient-to-r from-purple-400 via-pink-400 to-purple-400 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
        {progress > 0 && (
          <div className="mt-2 flex gap-1">
            {[...Array(5)].map((_, i) => (
              <div
                key={i}
                className={cn(
                  "h-1 flex-1 rounded-full transition-all duration-300",
                  i < progress ? "bg-purple-400" : "bg-gray-200"
                )}
              />
            ))}
          </div>
        )}
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
                        ? "text-purple-700/70" 
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
          <div className="flex items-center gap-2 p-4 bg-green-50 border border-green-200 rounded-lg mb-2">
            <CheckCircle2 className="w-5 h-5 text-green-600" />
            <p className="text-sm font-medium text-green-800">All aspects collected! Ready to generate your campaign.</p>
          </div>
          <GradientButton
            onClick={onComplete}
            className="w-full"
          >
            Continue to Storyline
            <Sparkles className="w-4 h-4 ml-2" />
          </GradientButton>
        </div>
      ) : (
        <PromptInput onSubmit={handleSubmit}>
          <PromptInputTextarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Type your message..."
            disabled={isLoading}
          />
          <div className="flex justify-end">
            <PromptInputSubmit disabled={!inputValue.trim() || isLoading} />
          </div>
        </PromptInput>
      )}
    </div>
  )
}
