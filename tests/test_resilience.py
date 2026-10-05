import time

import pytest

from resilience import (
    BoundedExecutor,
    CircuitBreaker,
    CircuitOpenError,
    IdempotencyKeyStore,
    OperationTimeoutError,
    RetryPolicy,
    TokenBucket,
    call_with_retry,
    call_with_timeout,
    with_fallback,
)


def test_retry_is_bounded():
    n = []

    def fn():
        n.append(1)
        if len(n) < 3:
            raise TimeoutError
        return "ok"

    assert (
        call_with_retry(
            fn,
            policy=RetryPolicy(3, 0),
            retryable=lambda e: isinstance(e, TimeoutError),
        )
        == "ok"
    )
    assert len(n) == 3


def test_non_retryable_fails_once():
    n = []

    def fn():
        n.append(1)
        raise ValueError

    with pytest.raises(ValueError):
        call_with_retry(fn, policy=RetryPolicy(3, 0), retryable=lambda e: False)
    assert len(n) == 1


def test_timeout_is_bounded():
    with pytest.raises(OperationTimeoutError):
        call_with_timeout(lambda: time.sleep(0.05), 0.001)


def test_idempotency_executes_once():
    s = IdempotencyKeyStore()
    n = []
    assert s.execute_once("k", lambda: n.append(1) or "ok") == "ok"
    assert s.execute_once("k", lambda: n.append(2) or "new") == "ok"
    assert n == [1]


def test_graceful_degradation_uses_fallback():
    assert with_fallback(lambda: 1 / 0, lambda: "degraded") == "degraded"


def test_concurrency_limit():
    ex = BoundedExecutor(1)
    ex._sem.acquire()
    try:
        with pytest.raises(RuntimeError):
            ex.run(lambda: "x")
    finally:
        ex._sem.release()


def test_rate_limit():
    b = TokenBucket(1, 1)
    assert b.allow()
    assert not b.allow()


def test_circuit_open():
    b = CircuitBreaker(3, 60)
    for _ in range(3):
        b.record_failure()
    with pytest.raises(CircuitOpenError):
        call_with_retry(lambda: "x", policy=RetryPolicy(1), retryable=lambda e: True, breaker=b)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf"), True, False])
def test_token_bucket_rejects_non_finite_and_bool_cost_without_poisoning_state(bad):
    bucket = TokenBucket(10.0, 2)
    before = bucket.tokens
    with pytest.raises(ValueError):
        bucket.allow(bad)
    assert bucket.tokens == before
    assert bucket.allow(1.0)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf"), True, False, 0, -1])
def test_token_bucket_rejects_invalid_rate(bad):
    with pytest.raises(ValueError):
        TokenBucket(bad, 1)


@pytest.mark.parametrize("bad", [True, False, 0, -1, 1.5])
def test_positive_integer_boundaries_are_strict(bad):
    with pytest.raises(ValueError):
        BoundedExecutor(bad)
    with pytest.raises(ValueError):
        CircuitBreaker(bad, 1.0)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf"), True, False, 0, -1])
def test_timeout_rejects_invalid_values(bad):
    with pytest.raises(ValueError):
        call_with_timeout(lambda: "never-started", bad)


@pytest.mark.parametrize("field,bad", [
    ("base_delay", float("nan")),
    ("base_delay", float("inf")),
    ("max_delay", float("nan")),
    ("max_delay", float("inf")),
    ("jitter", float("nan")),
    ("jitter", float("inf")),
    ("jitter", True),
])
def test_retry_policy_rejects_non_finite_or_bool_timing(field, bad):
    kwargs = {field: bad}
    with pytest.raises(ValueError):
        RetryPolicy(**kwargs)


def test_retry_policy_rejects_invalid_attempts_and_delay_ordering():
    for bad in (True, False, 0, -1, 1.5):
        with pytest.raises(ValueError):
            RetryPolicy(attempts=bad)
    with pytest.raises(ValueError):
        RetryPolicy(base_delay=2.0, max_delay=1.0)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf"), True, False, 0, -1])
def test_circuit_breaker_rejects_invalid_reset_timeout(bad):
    with pytest.raises(ValueError):
        CircuitBreaker(1, bad)
