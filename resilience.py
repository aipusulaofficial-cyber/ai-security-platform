"""Dependency-free resilience primitives for service boundaries."""

from __future__ import annotations

import math
import random
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from dataclasses import dataclass


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _finite_number(value: object, name: str, *, positive: bool = False, non_negative: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    if positive and number <= 0:
        raise ValueError(f"{name} must be positive")
    if non_negative and number < 0:
        raise ValueError(f"{name} must be non-negative")
    return number


class CircuitOpenError(RuntimeError):
    pass


class OperationTimeoutError(TimeoutError):
    pass


@dataclass(frozen=True)
class RetryPolicy:
    attempts: int = 3
    base_delay: float = 0.05
    max_delay: float = 1.0
    jitter: float = 0.1

    def __post_init__(self) -> None:
        _positive_int(self.attempts, "attempts")
        base_delay = _finite_number(self.base_delay, "base_delay", non_negative=True)
        max_delay = _finite_number(self.max_delay, "max_delay", non_negative=True)
        _finite_number(self.jitter, "jitter", non_negative=True)
        if max_delay < base_delay:
            raise ValueError("max_delay must be greater than or equal to base_delay")

    def delay(self, attempt: int) -> float:
        _positive_int(attempt, "attempt")
        raw = min(self.max_delay, self.base_delay * (2 ** (attempt - 1)))
        return raw + random.uniform(0.0, self.jitter)


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, reset_timeout: float = 5.0):
        _positive_int(failure_threshold, "failure_threshold")
        _finite_number(reset_timeout, "reset_timeout", positive=True)
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self._failures = 0
        self._opened_at = 0.0
        self._lock = threading.Lock()

    @property
    def open(self) -> bool:
        with self._lock:
            return self._opened_at > 0 and time.monotonic() - self._opened_at < self.reset_timeout

    def allow(self) -> bool:
        with self._lock:
            if self._opened_at == 0:
                return True
            if time.monotonic() - self._opened_at >= self.reset_timeout:
                self._opened_at = 0.0
                self._failures = 0
                return True
            return False

    def record_success(self) -> None:
        with self._lock:
            self._failures = 0
            self._opened_at = 0.0

    def record_failure(self) -> None:
        with self._lock:
            self._failures += 1
            if self._failures >= self.failure_threshold:
                self._opened_at = time.monotonic()


class BoundedExecutor[T]:
    def __init__(self, limit: int):
        _positive_int(limit, "limit")
        self._sem = threading.BoundedSemaphore(limit)

    def run(self, fn: Callable[[], T]) -> T:
        if not self._sem.acquire(blocking=False):
            raise RuntimeError("concurrency limit exceeded")
        try:
            return fn()
        finally:
            self._sem.release()


class TokenBucket:
    def __init__(self, rate: float, capacity: int):
        _finite_number(rate, "rate", positive=True)
        _positive_int(capacity, "capacity")
        self.rate = rate
        self.capacity = float(capacity)
        self.tokens = float(capacity)
        self.updated = time.monotonic()
        self._lock = threading.Lock()

    def allow(self, cost: float = 1.0) -> bool:
        _finite_number(cost, "cost", positive=True)
        with self._lock:
            now = time.monotonic()
            self.tokens = min(self.capacity, self.tokens + (now - self.updated) * self.rate)
            self.updated = now
            if self.tokens < cost:
                return False
            self.tokens -= cost
            return True


class IdempotencyKeyStore[T]:
    def __init__(self):
        self._results = {}
        self._locks = {}
        self._guard = threading.Lock()

    def execute_once(self, key: str, fn: Callable[[], T]) -> T:
        if not key:
            raise ValueError("idempotency key required")
        with self._guard:
            lock = self._locks.setdefault(key, threading.Lock())
        with lock:
            if key in self._results:
                return self._results[key]
            result = fn()
            self._results[key] = result
            return result


def call_with_timeout[T](fn: Callable[[], T], timeout_seconds: float) -> T:
    _finite_number(timeout_seconds, "timeout_seconds", positive=True)
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(fn)
    try:
        return future.result(timeout=timeout_seconds)
    except FutureTimeout as exc:
        future.cancel()
        raise OperationTimeoutError("operation timed out") from exc
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def with_fallback[T](
    primary: Callable[[], T],
    fallback: Callable[[], T],
    recoverable: Callable[[Exception], bool] = lambda e: True,
) -> T:
    try:
        return primary()
    except Exception as exc:
        if not recoverable(exc):
            raise
        return fallback()


def call_with_retry[T](
    fn: Callable[[], T],
    *,
    policy: RetryPolicy,
    retryable: Callable[[Exception], bool],
    breaker: CircuitBreaker | None = None,
) -> T:
    if breaker is not None and not breaker.allow():
        raise CircuitOpenError("circuit is open")
    for attempt in range(1, policy.attempts + 1):
        try:
            result = fn()
            if breaker is not None:
                breaker.record_success()
            return result
        except Exception as exc:
            if breaker is not None:
                breaker.record_failure()
            if attempt >= policy.attempts or not retryable(exc):
                raise
            time.sleep(policy.delay(attempt))
    raise AssertionError("unreachable")
