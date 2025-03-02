from fastapi import HTTPException
from pydantic import BaseModel
from typing import List

class Message(BaseModel):
    user: str
    content: str

class ChatService:
    def __init__(self):
        self.messages: List[Message] = []

    def send_message(self, user: str, content: str) -> Message:
        if not content.strip():
            raise HTTPException(status_code=400, detail="Message content cannot be empty")
        
        message = Message(user=user, content=content)
        self.messages.append(message)
        return message

    def get_messages(self) -> List[Message]:
        return self.messages

chat_service = ChatService()