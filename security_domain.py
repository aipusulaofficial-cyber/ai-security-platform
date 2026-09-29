from dataclasses import dataclass

from policy_detector import detect_prompt_injection


@dataclass(frozen=True)
class ThreatDecision:
    blocked: bool
    reason: str


def inspect_prompt(prompt: str) -> ThreatDecision:
    # Use the same normalization/detection rule set as the public detector.
    decision = detect_prompt_injection(prompt)
    if decision["detected"]:
        return ThreatDecision(True, "prompt_injection_indicator")
    return ThreatDecision(False, "no_indicator")


def require_audit_context(actor: str, request_id: str) -> None:
    if not actor or not request_id:
        raise ValueError("audit context required")
