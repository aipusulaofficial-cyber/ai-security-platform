import time

from fastapi import FastAPI, HTTPException
from fastapi import Request as FastAPIRequest
from opentelemetry import trace
from pydantic import BaseModel
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
    key: str
    payload: dict = {}


@app.get("/health/live")
def live():
    return {"status": "ok"}


@app.get("/health/ready")
def ready():
    return {"status": "ready"}


@app.post("/v1/security")
def handle(r: Request):
    with tracer.start_as_current_span("ai-security-platform.domain"):
        try:
            d = inspect_prompt(r.payload.get("prompt", ""))
            require_audit_context(r.payload.get("actor", ""), r.key)
            return {"blocked": d.blocked, "reason": d.reason}
        except (ValueError, KeyError, RuntimeError) as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
