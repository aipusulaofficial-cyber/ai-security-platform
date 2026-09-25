from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from opentelemetry import trace
from security_domain import *

try:
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

    p = TracerProvider(resource=Resource.create({"service.name": "ai-security-platform"}))
    p.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(p)
except Exception:
    pass
app = FastAPI(title="ai-security-platform", version="1.0.0")
tracer = trace.get_tracer("ai-security-platform")


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
