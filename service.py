from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from policy_detector import detect_prompt_injection
from security_domain import require_audit_context

app = FastAPI(title="ai-security-platform", version="1.1.0")


class Request(BaseModel):
    key: str = Field(min_length=1, max_length=128)
    payload: dict[str, object] = Field(default_factory=dict)


@app.get("/health/live")
def live():
    return {"status": "ok"}


@app.get("/health/ready")
def ready():
    return {"status": "ready"}


@app.post("/v1/security")
def handle(r: Request):
    prompt = r.payload.get("prompt", "")
    actor = r.payload.get("actor", "")
    if not isinstance(prompt, str) or not isinstance(actor, str):
        raise HTTPException(status_code=422, detail="prompt and actor must be strings")
    try:
        require_audit_context(actor.strip(), r.key)
        detection = detect_prompt_injection(prompt)
        return {
            "blocked": detection["detected"],
            "reason": "prompt_injection" if detection["detected"] else "allowed",
            "matches": detection["matches"],
        }
    except (ValueError, KeyError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
