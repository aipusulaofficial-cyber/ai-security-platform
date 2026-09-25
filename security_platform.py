"""AI security policy engine with threat classification and audit records."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SecurityEvent:
    request_id: str
    rule: str
    severity: str


@dataclass
class AuditLog:
    events: list[SecurityEvent] = field(default_factory=list)


class SecurityPolicy:
    def __init__(self, patterns=None):
        self.patterns = patterns or ["prompt injection", "credential", "secret"]

    def evaluate(self, request_id, text, audit):
        hits = [p for p in self.patterns if p in text.lower()]
        for p in hits:
            audit.events.append(SecurityEvent(request_id, p, "high"))
        return not hits
