"""First line of defence: clean the visitor's message and catch obvious prompt-injection attempts.

This is a cheap filter, not the only protection. Anything subtle that gets past it
still meets the hardened system prompt and the output guard.
"""

import re
import unicodedata
from dataclasses import dataclass

# Zero-width and bidi-control characters used to hide words from filters.
_INVISIBLE = re.compile(r"[​-‏‪-‮⁠-⁤⁦-⁩﻿­]")
# Control characters other than newline and tab.
_CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")
_BLANK_LINES = re.compile(r"\n{3,}")
_SPACES = re.compile(r"[ \t]{2,}")

# Kept narrow on purpose: words like "programming" or "context" appear in real questions.
_INSTRUCTION_WORDS = r"(instructions?|rules?|prompts?|guidelines?|constraints?)"

_INJECTION_PATTERNS = [
    # "ignore / forget / override all previous instructions"
    rf"\b(ignore|disregard|forget|override|bypass|skip|drop|delete|reset)\b.{{0,40}}\b(previous|prior|above|earlier|preceding|initial|original|your|system|all|these|those|any)\b.{{0,20}}\b{_INSTRUCTION_WORDS}",
    # "reveal / print / repeat your system prompt"
    rf"\b(reveal|show|print|display|output|repeat|recite|leak|dump|expose|share|give|tell|send|write|spell|translate|summari[sz]e|paraphrase|encode)\b.{{0,40}}\b(system|initial|hidden|secret|original|internal|full|exact|developer|your)\b.{{0,15}}\b{_INSTRUCTION_WORDS}",
    rf"\bwhat\s+(are|were|is)\s+your\s+(\w+\s+)?{_INSTRUCTION_WORDS}",
    # "repeat the text above", "print everything before this"
    r"\b(repeat|print|output|copy|recite|echo|write\s+out)\b.{0,30}\b(text|words|everything|content|lines?|messages?)\b.{0,15}\b(above|before|preceding|prior)\b",
    r"\bstart(ing)?\s+with\s+['\"]?you\s+are\b",
    r"\b(system|developer)\s*(prompt|message|instructions?)\b",
    r"\bconfidential reference code\b",
    # Persona / mode switching
    r"\byou\s+are\s+(now|no\s+longer)\b",
    r"\bfrom\s+now\s+on\b.{0,30}\b(you|act|respond|answer|reply|behave)\b",
    r"\b(act|behave|respond)\s+as\s+(if\s+you\s+(are|were)|an?\s+(unrestricted|unfiltered|different|new)|my\b)",
    r"\bpretend\s+(to\s+be|you\s*('re|are)|that\s+you)\b",
    r"\b(role\s*-?\s*play|roleplay)\b",
    r"\b(developer|god|admin|debug|jailbreak|unrestricted|sudo)\s*mode\b",
    r"\bjail\s*-?\s*break",
    r"\bDAN\b",
    r"\bdo\s+anything\s+now\b",
    r"\b(no|without)\s+(restrictions|rules|filters|guidelines|censorship)\b",
    r"\bnew\s+(system\s+)?(instructions?|rules|persona)\s*:",
    # Fake chat-template / role markers
    r"<\s*/?\s*(system|assistant|user|instructions?|visitor_message|im_start|im_end)\b",
    r"<\|.{0,20}\|>",
    r"\[\s*/?\s*(system|inst|instructions?)\s*\]",
    r"(^|\n)\s*#{1,6}\s*(system|instructions?|rules)\b",
    r"(^|\n)\s*(system|assistant)\s*:",
]
_INJECTION = re.compile("|".join(f"(?:{p})" for p in _INJECTION_PATTERNS), re.IGNORECASE | re.DOTALL)
# "DAN" is only a jailbreak marker in capitals; "Dan" is a name.
_CASE_SENSITIVE = re.compile(r"\bDAN\b")

# Long encoded blobs (base64/hex) are a common way to smuggle instructions.
_ENCODED_BLOB = re.compile(r"[A-Za-z0-9+/=_-]{60,}")


@dataclass(frozen=True)
class InputVerdict:
    text: str
    is_blocked: bool
    reason: str | None = None


def normalize(message: str) -> str:
    """NFKC folds look-alike characters (fullwidth letters, ligatures) back to plain text."""
    text = unicodedata.normalize("NFKC", message)
    text = _INVISIBLE.sub("", text)
    text = _CONTROL.sub("", text)
    text = _SPACES.sub(" ", text)
    text = _BLANK_LINES.sub("\n\n", text)
    return text.strip()


def _is_injection(text: str) -> bool:
    for match in _INJECTION.finditer(text):
        if match.group(0).strip().upper() != "DAN" or _CASE_SENSITIVE.search(match.group(0)):
            return True
    return False


def inspect_message(message: str) -> InputVerdict:
    text = normalize(message)
    if not text:
        return InputVerdict(text, True, "empty")
    if _is_injection(text):
        return InputVerdict(text, True, "injection")
    if _ENCODED_BLOB.search(text):
        return InputVerdict(text, True, "encoded")
    return InputVerdict(text, False)
