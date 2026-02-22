from fastapi import APIRouter, Depends
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.gemini_service import GeminiService

router = APIRouter()

@router.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, service: GeminiService = Depends()):
    ai_text = await service.get_chat_response(request.message)
    return ChatResponse(text=ai_text)
