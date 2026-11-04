"""Short, deterministic answers to direct assistant-creator questions."""

from __future__ import annotations

import re
import unicodedata
from typing import Any


_BENGALI_SCRIPT = re.compile(r"[\u0980-\u09ff]")
_ENGLISH_IDENTITY_PATTERNS = (
    re.compile(r"^who (?:created|made|built) (?:you|cendrix(?: ai)?|bikash ai)$"),
    re.compile(r"^who is (?:your )?(?:creator|developer|owner)$"),
    re.compile(
        r"^who is (?:the )?(?:creator|developer|owner) of "
        r"(?:you|cendrix(?: ai)?|bikash ai)$"
    ),
)
_BANGLISH_IDENTITY_PATTERNS = (
    re.compile(r"^tomake ke (?:baniyeche|banayse|banayche|toiri koreche)$"),
    re.compile(r"^tomar (?:creator|developer|owner) ke$"),
    re.compile(r"^(?:cendrix|bikash) ai ke (?:baniyeche|banayse|banayche)$"),
)
_BENGALI_IDENTITY_PATTERNS = (
    re.compile(r"^তোমাকে কে (?:তৈরি করেছে|বানিয়েছে|বানিয়েছে|বানিয়েছেন|বানিয়েছেন)$"),
    re.compile(r"^তোমার (?:নির্মাতা|স্রষ্টা) কে$"),
    re.compile(r"^বিকাশ এআই কে (?:বানিয়েছে|বানিয়েছে|বানিয়েছেন|বানিয়েছেন|তৈরি করেছে)$"),
)


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    normalized = "".join(
        " " if unicodedata.category(character)[0] in {"P", "S"} else character
        for character in normalized
    )
    return " ".join(normalized.split())


def _language(question: str) -> str:
    if _BENGALI_SCRIPT.search(question):
        return "bn"
    if re.match(r"\s*who\b", question.casefold()):
        return "en"
    return "bx"


def is_creator_identity_question(question: str) -> bool:
    """Match only direct questions asking who created, made, or developed the assistant."""
    normalized = _normalize(question)
    if not normalized:
        return False
    if _BENGALI_SCRIPT.search(normalized):
        patterns = _BENGALI_IDENTITY_PATTERNS
    elif normalized.startswith("who "):
        patterns = _ENGLISH_IDENTITY_PATTERNS
    else:
        patterns = _BANGLISH_IDENTITY_PATTERNS
    return any(pattern.fullmatch(normalized) for pattern in patterns)


def answer_creator_identity(question: str, identity: dict[str, Any]) -> str | None:
    """Return one concise localized answer for a recognized creator question."""
    if not is_creator_identity_question(question):
        return None

    language = _language(question)
    assistant_name = identity["assistant_name"]
    permanent = identity["permanent"]
    creator_name = permanent["creator_name"]
    creator_role = permanent["creator_role"][language]

    if language == "bn":
        return f"আমি {assistant_name}। আমাকে তৈরি করেছেন {creator_name}, {creator_role}।"
    if language == "bx":
        return f"Ami {assistant_name}. Amake baniyechen {creator_name}, {creator_role}."
    return f"I am {assistant_name}. I was created by {creator_name}, {creator_role}."
