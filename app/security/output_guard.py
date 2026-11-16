"""Last line of defence: check the model's reply before it reaches the visitor.

Even if a message slips past the input filter and talks the model into misbehaving,
a reply that leaks the prompt or carries an unknown link is replaced with a refusal.
"""

import re
from functools import lru_cache

from app.core.prompt import REFUSAL, SystemPrompt

# Any run of this many consecutive words copied from the rules counts as a leak.
LEAK_SHINGLE_WORDS = 8

_WORD = re.compile(r"[a-z0-9']+")
_URL = re.compile(r"\b(?:https?://|www\.)[^\s<>\"')\]]+", re.IGNORECASE)
_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
_LEAK_MARKERS = re.compile(
    r"visitor_message|security rules|strict rules|confidential reference code|system (prompt|instruction)",
    re.IGNORECASE,
)
_MARKDOWN = re.compile(r"\*\*|__|`|^\s{0,3}#{1,6}\s+", re.MULTILINE)


def _words(text: str) -> list[str]:
    return _WORD.findall(text.lower())


@lru_cache(maxsize=4)
def _shingles(protected_text: str) -> frozenset[tuple[str, ...]]:
    words = _words(protected_text)
    return frozenset(tuple(words[i : i + LEAK_SHINGLE_WORDS]) for i in range(len(words) - LEAK_SHINGLE_WORDS + 1))


def _leaks_prompt(reply: str, prompt: SystemPrompt) -> bool:
    if prompt.canary in reply or _LEAK_MARKERS.search(reply):
        return True
    words = _words(reply)
    protected = _shingles(prompt.protected_text)
    return any(tuple(words[i : i + LEAK_SHINGLE_WORDS]) in protected for i in range(len(words) - LEAK_SHINGLE_WORDS + 1))


def _host(url: str) -> str:
    without_scheme = re.sub(r"^https?://", "", url, flags=re.IGNORECASE)
    host = re.split(r"[/?#:]", without_scheme, maxsplit=1)[0].lower()
    return host.removeprefix("www.")


def _has_foreign_contact(reply: str, prompt: SystemPrompt) -> bool:
    if any(_host(url) not in prompt.allowed_hosts for url in _URL.findall(reply)):
        return True
    return any(email.lower() not in prompt.allowed_emails for email in _EMAIL.findall(reply))


def check_reply(reply: str | None, prompt: SystemPrompt, max_chars: int) -> tuple[str, str | None]:
    """Returns the text to send and, when the reply was replaced, why."""
    if not reply or not reply.strip():
        return REFUSAL, "empty"
    if _leaks_prompt(reply, prompt):
        return REFUSAL, "prompt_leak"
    if _has_foreign_contact(reply, prompt):
        return REFUSAL, "foreign_link"
    text = _MARKDOWN.sub("", reply).strip()
    if len(text) > max_chars:
        text = text[:max_chars].rsplit(" ", 1)[0].rstrip(",;:") + "..."
    return text, None
