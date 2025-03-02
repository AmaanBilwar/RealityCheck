import { useEffect, useState } from "react"
import ChatInput from "./chat-input"
import ChatMessage from "./chat-message"

export default function Chat() {
  const [messages, setMessages] = useState([])

  const fetchMessages = async () => {
    const response = await fetch('/api/messages')
    const data = await response.json()
    setMessages(data)
  }

  const handleSendMessage = async (message) => {
    const response = await fetch('/api/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message }),
    })
    const newMessage = await response.json()
    setMessages((prevMessages) => [...prevMessages, newMessage])
  }

  useEffect(() => {
    fetchMessages()
  }, [])

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto">
        {messages.map((msg, index) => (
          <ChatMessage key={index} message={msg} />
        ))}
      </div>
      <ChatInput onSendMessage={handleSendMessage} />
    </div>
  )
}