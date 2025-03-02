import React from 'react';

interface ChatMessageProps {
  message: string;
  sender: 'user' | 'bot';
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message, sender }) => {
  return (
    <div className={`chat-message ${sender}`}>
      <span className="message-sender">{sender === 'user' ? 'You' : 'Bot'}:</span>
      <span className="message-content">{message}</span>
    </div>
  );
};

export default ChatMessage;