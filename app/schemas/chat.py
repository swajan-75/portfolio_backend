from pydantic import BaseModel, ConfigDict, Field

from app.core.config import settings


class ChatRequest(BaseModel):
    # Unknown fields (a smuggled "system" or "history" key) are rejected outright.
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    message: str = Field(min_length=1, max_length=settings.MAX_MESSAGE_CHARS)


class ChatResponse(BaseModel):
    text: str
