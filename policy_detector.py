import re
import unicodedata

# Heuristic detection only. Treat untrusted content as untrusted even when no pattern matches.
PATTERNS = (
    r"ignore\s+(?:all\s+)?previous\s+instructions",
    r"(?:reveal\s+(?:the\s+)?)?system\s+prompt",
    r"developer\s+message",
)
_INVISIBLE = dict.fromkeys(map(ord, "\u200b\u200c\u200d\u2060\ufeff"), None)


def detect_prompt_injection(text: str) -> dict:
    if not text:
        return {"detected": False, "matches": []}
    normalized = unicodedata.normalize("NFKC", text).translate(_INVISIBLE)
    matches = [pattern for pattern in PATTERNS if re.search(pattern, normalized, re.I)]
    return {"detected": bool(matches), "matches": matches}
