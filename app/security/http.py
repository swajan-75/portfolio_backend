"""HTTP-level protections: origin check, request size limit and security headers."""

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

from app.core.config import settings

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Cross-Origin-Resource-Policy": "same-site",
}
# The API only ever returns JSON; nothing should load or frame it.
API_CSP = "default-src 'none'; frame-ancestors 'none'"
DOCS_PATHS = ("/docs", "/redoc", "/openapi.json")


def require_allowed_origin(request: Request) -> None:
    """
    CORS only stops browsers on other sites from *reading* the reply; this rejects the
    request itself. Scripts can fake the Origin header, so it is a speed bump for casual
    abuse, and the rate limit is what actually caps cost.
    """
    origin = (request.headers.get("origin") or "").rstrip("/")
    if origin not in settings.allowed_origins:
        raise HTTPException(status_code=403, detail="Forbidden")


class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        length = request.headers.get("content-length")
        if length and (not length.isdigit() or int(length) > settings.MAX_BODY_BYTES):
            return self._secure(request, JSONResponse(status_code=413, content={"detail": "Request too large"}))
        return self._secure(request, await call_next(request))

    @staticmethod
    def _secure(request: Request, response: Response) -> Response:
        response.headers.update(SECURITY_HEADERS)
        if not request.url.path.startswith(DOCS_PATHS):
            response.headers["Content-Security-Policy"] = API_CSP
        return response
