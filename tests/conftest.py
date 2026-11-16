import os

# Settings are read at import time; tests never talk to the real Gemini API.
os.environ["GEMINI_API_KEY"] = "test-key"
os.environ["ALLOWED_ORIGINS"] = "https://swajan.dev,https://www.swajan.dev"
os.environ["RATE_LIMIT"] = "3/minute"
os.environ["RATE_LIMIT_STORAGE_URI"] = "memory://"
os.environ["ENABLE_DOCS"] = "false"

from types import SimpleNamespace  # noqa: E402

import pytest  # noqa: E402

from app.core.prompt import load_system_prompt  # noqa: E402
from app.services.gemini_service import GeminiService  # noqa: E402

SITE_HOSTS = frozenset({"swajan.dev"})


class FakeModels:
    def __init__(self, reply: str | None = "He builds NestJS and Next.js apps.", error: Exception | None = None):
        self.reply = reply
        self.error = error
        self.calls: list[dict] = []

    async def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return SimpleNamespace(text=self.reply)


def make_service(**kwargs) -> tuple[GeminiService, FakeModels]:
    models = FakeModels(**kwargs)
    client = SimpleNamespace(aio=SimpleNamespace(models=models))
    return GeminiService(client, load_system_prompt(SITE_HOSTS)), models


@pytest.fixture
def prompt():
    return load_system_prompt(SITE_HOSTS)
