from fastapi import APIRouter

router = APIRouter()

from . import chat  # Import chat routes

# Include the chat router
router.include_router(chat.router, prefix="/chat", tags=["chat"])