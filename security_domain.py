from dataclasses import dataclass

@dataclass(frozen=True)
class ThreatDecision:
    blocked:bool; reason:str

def inspect_prompt(prompt:str)->ThreatDecision:
    p=prompt.lower()
    indicators=("ignore previous instructions","system prompt","developer message")
    for x in indicators:
        if x in p:return ThreatDecision(True,"prompt_injection_indicator")
    return ThreatDecision(False,"no_indicator")

def require_audit_context(actor:str,request_id:str)->None:
    if not actor or not request_id:raise ValueError("audit context required")
