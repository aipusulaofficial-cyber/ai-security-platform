from fastapi.testclient import TestClient
from service import app
def test_request_and_correlation_ids_are_exposed():
    c=TestClient(app)
    r=c.get("/health/live",headers={"x-request-id":"req-test","x-correlation-id":"corr-test"})
    assert r.status_code==200
    assert r.headers["x-request-id"]=="req-test"
    assert r.headers["x-correlation-id"]=="corr-test"
    assert float(r.headers["x-latency-ms"])>=0
