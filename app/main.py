import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.api.v1.chat import router as chat_router
from app.core.config import settings
from app.security.http import SecurityMiddleware
from app.security.rate_limit import limiter, rate_limit_exceeded_handler

logging.basicConfig(level=logging.INFO)

docs = {} if settings.ENABLE_DOCS else {"docs_url": None, "redoc_url": None, "openapi_url": None}
app = FastAPI(title="Swajan Portfolio AI Backend", **docs)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Don't echo the submitted input back; give the chat window something it can show.
    return JSONResponse(
        status_code=422,
        content={"text": f"Please send a message between 1 and {settings.MAX_MESSAGE_CHARS} characters."},
    )


# Starlette runs the last-added middleware first: CORS answers preflights before anything else.
app.add_middleware(SecurityMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(settings.allowed_origins),
    allow_credentials=False,
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
    max_age=600,
)

app.include_router(chat_router, prefix="/api/v1/chat", tags=["AI"])


@app.get("/")
def read_root() -> dict[str, str]:
    return {"status": "Portfolio AI Backend is running"}
