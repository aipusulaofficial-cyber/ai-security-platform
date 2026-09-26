import time

from fastapi import FastAPI, HTTPException
from fastapi import Request as FastAPIRequest
from opentelemetry import trace
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware

from security_domain import inspect_prompt, require_audit_context

try:
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

    p = TracerProvider(resource=Resource.create({"service.name": "ai-security-platform"}))
    p.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(p)
except (ImportError, RuntimeError):
    pass

app = FastAPI(title="ai-security-platform", version="1.0.0")
tracer = trace.get_tracer("ai-security-platform")


class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: FastAPIRequest, call_next):
        request_id = request.headers.get("x-request-id", "generated-request")
        correlation_id = request.headers.get("x-correlation-id", request_id)
        started = time.perf_counter()
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        response.headers["x-correlation-id"] = correlation_id
        response.headers["x-latency-ms"] = f"{(time.perf_counter() - started) * 1000:.3f}"
        return response


app.add_middleware(ObservabilityMiddleware)


class Request(BaseModel):
    key: str = Field(min_length=1, max_length=128)
    payload: dict[str, object] = Field(default_factory=dict)


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready")
def ready() -> dict[str, str]:
    return {"status": "ready"}


@app.post("/v1/security")
def handle(r: Request) -> dict[str, bool | str]:
    key = r.key.strip()
    if not key:
        raise HTTPException(status_code=422, detail="key must not be blank")

    prompt = r.payload.get("prompt", "")
    actor = r.payload.get("actor", "")
    if not isinstance(prompt, str) or not isinstance(actor, str):
        raise HTTPException(status_code=422, detail="prompt and actor must be strings")

    with tracer.start_as_current_span("ai-security-platform.domain"):
        try:
            d = inspect_prompt(prompt)
            require_audit_context(actor.strip(), key)
            return {"blocked": d.blocked, "reason": d.reason}
        except (ValueError, KeyError, RuntimeError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
