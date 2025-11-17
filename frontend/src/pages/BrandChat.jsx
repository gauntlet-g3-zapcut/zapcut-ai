import { useState, useEffect } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { Button } from "../components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card"
import ChatInterface from "../components/ChatInterface"
import { api } from "../services/api"

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
        
        setCreativeBibleId(sessionResponse.creative_bible_id)
        
        // Load existing messages if any
        const messagesResponse = await api.getChatMessages(brandId, sessionResponse.creative_bible_id)
        if (messagesResponse?.messages) {
          setMessages(messagesResponse.messages)
          
          // Check session status for progress
          const sessionStatus = await api.getChatSession(brandId, sessionResponse.creative_bible_id)
          setProgress(sessionStatus.progress || 0)
          setIsComplete(sessionStatus.is_complete || false)
          
          // If no messages, send initial greeting (agent will send it)
          if (messagesResponse.messages.length === 0) {
            // Send empty message to trigger agent greeting
            await handleSendMessage("")
          }
        } else {
          // Send empty message to trigger agent greeting
          await handleSendMessage("")
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
      <div className="min-h-screen bg-background p-8 flex items-center justify-center">
        <div className="text-muted-foreground">Initializing chat...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-4xl mx-auto">
        <Button
          variant="ghost"
          onClick={() => navigate("/dashboard")}
          className="mb-6"
        >
          ← Back to Dashboard
        </Button>

        <Card>
          <CardHeader>
            <CardTitle className="text-3xl">Create New Campaign</CardTitle>
            <CardDescription>
              Chat with our AI consultant to describe your ideal video ad
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[600px]">
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
