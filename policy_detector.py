import re

# Pattern catalog\nPATTERNS = (
    r"ignore\s+(?:all\s+)?previous\s+instructions",
    r"reveal\s+(?:the\s+)?system\s+prompt",
    r"developer\s+message",
)


def detect_prompt_injection(text: str) -> dict:
    if not text:
        return {"detected": False, "matches": []}
    matches = [p for p in PATTERNS if re.search(p, text, re.I)]
    return {"detected": bool(matches), "matches": matches}
