from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded

from app.core.config import settings

RATE_LIMITED_REPLY = "You're sending messages too quickly. Please wait a minute and try again."
DEFAULT_RETRY_AFTER_SECONDS = 60


def client_ip(request: Request) -> str:
    """Vercel's edge sets x-real-ip / x-forwarded-for itself, so clients cannot spoof them there."""
    for header in ("x-real-ip", "x-vercel-forwarded-for", "x-forwarded-for"):
        value = request.headers.get(header)
        if value:
            return value.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


limiter = Limiter(key_func=client_ip, storage_uri=settings.RATE_LIMIT_STORAGE_URI, headers_enabled=False)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    # Same {"text": ...} shape as a normal reply, so the chat window can show it.
    try:
        retry_after = int(exc.limit.limit.get_expiry())
    except (AttributeError, TypeError, ValueError):
        retry_after = DEFAULT_RETRY_AFTER_SECONDS
    return JSONResponse(
        status_code=429,
        content={"text": RATE_LIMITED_REPLY},
        headers={"Retry-After": str(retry_after)},
    )
