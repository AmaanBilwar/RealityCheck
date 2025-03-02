"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent } from "@/components/ui/card"
import { MessageSquare, Send, Loader2, Bot } from "lucide-react"
import { useToast } from "@/components/ui/use-toast"

type Message = {
  role: "user" | "assistant" | "system"
  content: string
}

interface ChatInputProps {
  articleId?: string
  onMessageReceived?: (message: Message) => void
  disabled?: boolean
  placeholder?: string
  className?: string
}

export default function ChatInput({
  articleId,
  onMessageReceived,
  disabled = false,
  placeholder = "Ask a question about this article...",
  className = ""
}: ChatInputProps) {
  const [message, setMessage] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const { toast } = useToast()

  // Initialize conversation ID from localStorage if available
  useEffect(() => {
    const storedId = localStorage.getItem(`chat_conversation_${articleId || 'general'}`)
    if (storedId) {
      setConversationId(storedId)
    }
  }, [articleId])

  const handleSendMessage = async () => {
    if (!message.trim() || isLoading || disabled) return
    
    // Create user message object
    const userMessage: Message = {
      role: "user",
      content: message
    }
    
    // Pass the user message to parent component for display
    if (onMessageReceived) {
      onMessageReceived(userMessage)
    }
    
    // Clear input and set loading state
    const sentMessage = message
    setMessage("")
    setIsLoading(true)
    
    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: sentMessage,
          conversation_id: conversationId,
          article_id: articleId
        }),
      })
      
      if (!response.ok) {
        throw new Error(`Server responded with ${response.status}`)
      }
      
      const data = await response.json()
      
      // Save conversation ID
      if (data.conversation_id) {
        setConversationId(data.conversation_id)
        localStorage.setItem(`chat_conversation_${articleId || 'general'}`, data.conversation_id)
      }
      
      // Create assistant message object
      const assistantMessage: Message = {
        role: "assistant",
        content: data.response
      }
      
      // Pass the assistant message to parent component for display
      if (onMessageReceived) {
        onMessageReceived(assistantMessage)
      }
      
    } catch (error) {
      console.error("Error sending message:", error)
      toast({
        title: "Error",
        description: "Failed to send message. Please try again.",
        variant: "destructive",
      })
      
      // Create error message object
      if (onMessageReceived) {
        onMessageReceived({
          role: "system",
          content: "Sorry, there was an error processing your request."
        })
      }
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <Card className={`border-t-0 rounded-t-none shadow-lg ${className}`}>
      <CardContent className="p-4">
        <div className="flex items-end gap-3">
          <div className="relative flex-1">
            <Textarea
              placeholder={placeholder}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading || disabled}
              className="min-h-[60px] pr-12 resize-none border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-md transition-all duration-200"
            />
            <MessageSquare className="absolute right-4 top-4 h-5 w-5 text-gray-500" />
          </div>
          <Button
            onClick={handleSendMessage}
            disabled={!message.trim() || isLoading || disabled}
            size="icon"
            className="h-12 w-12 bg-blue-500 hover:bg-blue-600 disabled:opacity-50 transition-colors duration-200 flex items-center justify-center rounded-full"
          >
            {isLoading ? (
              <Loader2 className="h-5 w-5 text-white animate-spin" />
            ) : (
              <Send className="h-5 w-5 text-white" />
            )}
            <span className="sr-only">Send message</span>
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}