from fastapi.testclient import TestClient
from hypothesis import given
from hypothesis import strategies as st

from service import app

c = TestClient(app)


def test_contract():
    assert c.get("/health/live").status_code == 200


@given(st.text(min_size=1, max_size=32).filter(lambda value: value.strip()))
def test_property(v):
    response = c.post(
        "/v1/security",
        json={"key": v, "payload": {"prompt": v, "actor": "a"}},
    )
    assert response.status_code == 200


@given(st.text(min_size=1, max_size=32))
def test_blank_key_rejected(v):
    if not v.strip():
        response = c.post(
            "/v1/security",
            json={"key": v, "payload": {"prompt": v, "actor": "a"}},
        )
        assert response.status_code == 422
