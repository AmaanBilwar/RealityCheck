"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent } from "@/components/ui/card"
import { MessageSquare, Send } from "lucide-react"

export default function ChatInput() {
  const [message, setMessage] = useState("")

  const handleSendMessage = () => {
    if (!message.trim()) return

    // In a real implementation, this would send the message to your Chat Agent
    console.log("Sending message:", message)

    // Clear the input after sending
    setMessage("")
  }

  return (
    <Card className="border-t-0 rounded-t-none">
      <CardContent className="p-4">
        <div className="flex items-end gap-2">
          <div className="relative flex-1">
            <Textarea
              placeholder="Ask a question about this article..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              className="min-h-[60px] pr-10 resize-none"
            />
            <MessageSquare className="absolute right-3 top-3 h-4 w-4 text-muted-foreground" />
          </div>
          <Button onClick={handleSendMessage} disabled={!message.trim()} size="icon" className="h-10 w-10">
            <Send className="h-4 w-4" />
            <span className="sr-only">Send message</span>
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

