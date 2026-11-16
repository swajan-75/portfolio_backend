from fastapi import APIRouter, Depends, Request

from app.core.config import settings
from app.schemas.chat import ChatRequest, ChatResponse
from app.security.http import require_allowed_origin
from app.security.rate_limit import limiter
from app.services.gemini_service import GeminiService, get_gemini_service

router = APIRouter()


@router.post("/", response_model=ChatResponse, dependencies=[Depends(require_allowed_origin)])
@limiter.limit(settings.RATE_LIMIT)
async def chat_endpoint(
    request: Request,  # required by the rate limiter
    payload: ChatRequest,
    service: GeminiService = Depends(get_gemini_service),
) -> ChatResponse:
    return ChatResponse(text=await service.get_chat_response(payload.message))
