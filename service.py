import time
import uuid

from fastapi import FastAPI, HTTPException, Request as HTTPRequest
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from policy_detector import detect_prompt_injection
from security_domain import require_audit_context

app = FastAPI(title="ai-security-platform", version="1.1.0")


class PrincipalObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: HTTPRequest, call_next) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        correlation_id = request.headers.get("x-correlation-id") or request_id
        start = time.perf_counter()
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        response.headers["x-correlation-id"] = correlation_id
        response.headers["x-latency-ms"] = f"{(time.perf_counter() - start) * 1000:.3f}"
        return response


app.add_middleware(PrincipalObservabilityMiddleware)


class SecurityRequest(BaseModel):
    key: str = Field(min_length=1, max_length=128)
    payload: dict[str, object] = Field(default_factory=dict)


@app.get("/health/live")
def live():
    return {"status": "ok"}


@app.get("/health/ready")
def ready():
    return {"status": "ready"}


@app.post("/v1/security")
def handle(r: SecurityRequest):
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
