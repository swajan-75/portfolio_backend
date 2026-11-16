from functools import cached_property

from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_ORIGINS = "https://swajan.vercel.app,https://swajan.dev,https://www.swajan.dev"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-3.1-flash-lite"
    GEMINI_TIMEOUT_MS: int = 20_000

    # Comma-separated. Add http://localhost:3000 in a local .env for development.
    ALLOWED_ORIGINS: str = DEFAULT_ORIGINS

    # Per client IP, in slowapi/limits syntax; separate several limits with ";".
    RATE_LIMIT: str = "8/minute;60/day"
    # "memory://" counts per server instance. Point this at Redis (for example
    # Upstash "rediss://...") to share the limits across every Vercel instance.
    RATE_LIMIT_STORAGE_URI: str = "memory://"

    MAX_MESSAGE_CHARS: int = 500
    MAX_BODY_BYTES: int = 4_096
    MAX_REPLY_CHARS: int = 1_200

    # Swagger UI and the OpenAPI schema stay off in production.
    ENABLE_DOCS: bool = False

    @cached_property
    def allowed_origins(self) -> frozenset[str]:
        return frozenset(o.strip().rstrip("/") for o in self.ALLOWED_ORIGINS.split(",") if o.strip())


settings = Settings()
