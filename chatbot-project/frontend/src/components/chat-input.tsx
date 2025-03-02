"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent } from "@/components/ui/card"
import { MessageSquare, Send } from "lucide-react"
import { sendMessage } from "@/lib/api"

export default function ChatInput() {
  const [message, setMessage] = useState("")

  const handleSendMessage = async () => {
    if (!message.trim()) return

    try {
      const response = await sendMessage(message)
      console.log("Response from server:", response)
    } catch (error) {
      console.error("Error sending message:", error)
    } finally {
      setMessage("")
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <Card className="border-t-0 rounded-t-none shadow-lg">
      <CardContent className="p-4">
        <div className="flex items-end gap-3">
          <div className="relative flex-1">
            <Textarea
              placeholder="Ask a question about this article..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              className="min-h-[60px] pr-12 resize-none border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-md transition-all duration-200"
            />
            <MessageSquare className="absolute right-4 top-4 h-5 w-5 text-gray-500" />
          </div>
          <Button
            onClick={handleSendMessage}
            disabled={!message.trim()}
            size="icon"
            className="h-12 w-12 bg-blue-500 hover:bg-blue-600 disabled:opacity-50 transition-colors duration-200 flex items-center justify-center rounded-full"
          >
            <Send className="h-5 w-5 text-white" />
            <span className="sr-only">Send message</span>
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}