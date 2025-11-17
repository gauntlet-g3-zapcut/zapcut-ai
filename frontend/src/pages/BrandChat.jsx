import { useState, useEffect } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { Button } from "../components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import ChatInterface from "../components/ChatInterface"
import { api } from "../services/api"
import { Sparkles } from "lucide-react"

export default function BrandChat() {
  const { brandId } = useParams()
  const navigate = useNavigate()
  const [messages, setMessages] = useState([])
  const [creativeBibleId, setCreativeBibleId] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [isComplete, setIsComplete] = useState(false)
  const [isInitializing, setIsInitializing] = useState(true)

  // Initialize chat session
  useEffect(() => {
    const initializeChat = async () => {
      try {
        setIsInitializing(true)
        // Create chat session
        const sessionResponse = await api.createChatSession(brandId)
        if (!sessionResponse?.creative_bible_id) {
          throw new Error("Failed to create chat session")
        }
        
        const creativeBibleId = sessionResponse.creative_bible_id
        setCreativeBibleId(creativeBibleId)
        
        // Load existing messages if any
        const messagesResponse = await api.getChatMessages(brandId, creativeBibleId)
        if (messagesResponse?.messages && messagesResponse.messages.length > 0) {
          setMessages(messagesResponse.messages)
          
          // Check session status for progress
          const sessionStatus = await api.getChatSession(brandId, creativeBibleId)
          setProgress(sessionStatus.progress || 0)
          setIsComplete(sessionStatus.is_complete || false)
        } else {
          // No messages exist, trigger agent greeting by sending empty message
          setIsLoading(true)
          try {
            const response = await api.sendChatMessage(brandId, creativeBibleId, "")
            
            if (response?.message) {
              // Add agent response
              setMessages([{
                role: "assistant",
                content: response.message,
                created_at: new Date().toISOString()
              }])
            }

            // Update progress
            if (response?.metadata) {
              setProgress(response.metadata.progress || 0)
              setIsComplete(response.metadata.is_complete || false)
            }
          } catch (error) {
            console.error("Failed to get initial message:", error)
            alert(`Failed to start conversation: ${error.message}`)
          } finally {
            setIsLoading(false)
          }
        }
      } catch (error) {
        console.error("Failed to initialize chat:", error)
        alert(`Failed to start chat: ${error.message}`)
      } finally {
        setIsInitializing(false)
      }
    }

    if (brandId) {
      initializeChat()
    }
  }, [brandId])

  const handleSendMessage = async (message) => {
    if (!creativeBibleId) return

    try {
      setIsLoading(true)
      
      // Add user message to UI immediately
      if (message) {
        setMessages(prev => [...prev, {
          role: "user",
          content: message,
          created_at: new Date().toISOString()
        }])
      }

      // Send message to backend
      const response = await api.sendChatMessage(brandId, creativeBibleId, message)
      
      if (response?.message) {
        // Add agent response
        setMessages(prev => [...prev, {
          role: "assistant",
          content: response.message,
          created_at: new Date().toISOString()
        }])
      }

      // Update progress
      if (response?.metadata) {
        setProgress(response.metadata.progress || 0)
        setIsComplete(response.metadata.is_complete || false)
      }

      // If complete, we can show the completion button
      if (response?.metadata?.is_complete) {
        setIsComplete(true)
      }
    } catch (error) {
      console.error("Failed to send message:", error)
      alert(`Failed to send message: ${error.message}`)
    } finally {
      setIsLoading(false)
    }
  }

  const handleComplete = async () => {
    if (!creativeBibleId) return

    try {
      setIsLoading(true)
      await api.completeChat(brandId, creativeBibleId)
      // Navigate to storyline review
      navigate(`/brands/${brandId}/storyline/${creativeBibleId}`)
    } catch (error) {
      console.error("Failed to complete chat:", error)
      alert(`Failed to complete chat: ${error.message}`)
    } finally {
      setIsLoading(false)
    }
  }

  if (isInitializing) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-pink-50 p-8 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-white/80 backdrop-blur-sm border border-purple-100 flex items-center justify-center animate-pulse shadow-sm">
            <Sparkles className="w-6 h-6 text-purple-600 animate-spin" />
          </div>
          <div className="text-muted-foreground font-medium">Initializing chat...</div>
          <p className="text-muted-foreground/70 text-sm">Setting up your AI consultant</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-pink-50 p-4 sm:p-6 lg:p-8">
      <div className="max-w-5xl mx-auto">
        <Button
          variant="ghost"
          onClick={() => navigate("/dashboard")}
          className="mb-6 hover:bg-white/50 transition-colors"
        >
          ← Back to Dashboard
        </Button>

        <Card className="shadow-lg">
          <CardHeader className="pb-4 border-b">
            <CardTitle className="text-3xl font-bold" style={{ fontFamily: "'Playfair Display', serif" }}>
              Create New Campaign
            </CardTitle>
            <CardDescription className="text-base mt-2">
              Chat with our AI consultant to describe your ideal video ad
            </CardDescription>
          </CardHeader>
          <CardContent className="p-6">
            <div className="h-[650px] sm:h-[700px]">
              <ChatInterface
                messages={messages}
                onSendMessage={handleSendMessage}
                isLoading={isLoading}
                progress={progress}
                isComplete={isComplete}
                onComplete={handleComplete}
              />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
