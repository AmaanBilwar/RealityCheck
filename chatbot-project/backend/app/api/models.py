from pydantic import BaseModel

class Message(BaseModel):
    id: int
    content: str
    sender: str
    timestamp: str

class User(BaseModel):
    id: int
    username: str
    email: str

class Chat(BaseModel):
    id: int
    messages: list[Message]
    participants: list[User]