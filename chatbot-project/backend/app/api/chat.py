from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class Message(BaseModel):
    content: str

@router.post("/chat")
async def send_message(message: Message):
    if not message.content.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    # Here you would typically process the message and generate a response
    response = {"response": f"You said: {message.content}"}
    
    return response