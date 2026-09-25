"""Dependency-free resilience primitives for service boundaries."""
from __future__ import annotations
import random,threading,time
from concurrent.futures import ThreadPoolExecutor,TimeoutError as FutureTimeout
from dataclasses import dataclass
from typing import Callable,Generic,TypeVar
T=TypeVar("T")
class CircuitOpenError(RuntimeError): pass
class OperationTimeoutError(TimeoutError): pass
@dataclass(frozen=True)
class RetryPolicy:
    attempts:int=3; base_delay:float=0.05; max_delay:float=1.0; jitter:float=0.1
    def delay(self,attempt:int)->float:
        raw=min(self.max_delay,self.base_delay*(2**max(0,attempt-1)));return max(0.0,raw+random.uniform(0.0,self.jitter))
class CircuitBreaker:
    def __init__(self,failure_threshold:int=3,reset_timeout:float=5.0):
        if failure_threshold<1 or reset_timeout<=0:raise ValueError("invalid circuit policy")
        self.failure_threshold=failure_threshold;self.reset_timeout=reset_timeout;self._failures=0;self._opened_at=0.0;self._lock=threading.Lock()
    @property
    def open(self)->bool:
        with self._lock:return self._opened_at>0 and time.monotonic()-self._opened_at<self.reset_timeout
    def allow(self)->bool:
        with self._lock:
            if self._opened_at==0:return True
            if time.monotonic()-self._opened_at>=self.reset_timeout:self._opened_at=0.0;self._failures=0;return True
            return False
    def record_success(self)->None:
        with self._lock:self._failures=0;self._opened_at=0.0
    def record_failure(self)->None:
        with self._lock:
            self._failures+=1
            if self._failures>=self.failure_threshold:self._opened_at=time.monotonic()
class BoundedExecutor(Generic[T]):
    def __init__(self,limit:int):
        if limit<1:raise ValueError("limit must be positive")
        self._sem=threading.BoundedSemaphore(limit)
    def run(self,fn:Callable[[],T])->T:
        if not self._sem.acquire(blocking=False):raise RuntimeError("concurrency limit exceeded")
        try:return fn()
        finally:self._sem.release()
class TokenBucket:
    def __init__(self,rate:float,capacity:int):
        if rate<=0 or capacity<1:raise ValueError("invalid rate limit")
        self.rate=rate;self.capacity=float(capacity);self.tokens=float(capacity);self.updated=time.monotonic();self._lock=threading.Lock()
    def allow(self,cost:float=1.0)->bool:
        if cost<=0:raise ValueError("cost must be positive")
        with self._lock:
            now=time.monotonic();self.tokens=min(self.capacity,self.tokens+(now-self.updated)*self.rate);self.updated=now
            if self.tokens<cost:return False
            self.tokens-=cost;return True
class IdempotencyKeyStore(Generic[T]):
    def __init__(self):self._results={};self._locks={};self._guard=threading.Lock()
    def execute_once(self,key:str,fn:Callable[[],T])->T:
        if not key:raise ValueError("idempotency key required")
        with self._guard:lock=self._locks.setdefault(key,threading.Lock())
        with lock:
            if key in self._results:return self._results[key]
            result=fn();self._results[key]=result;return result
def call_with_timeout(fn:Callable[[],T],timeout_seconds:float)->T:
    if timeout_seconds<=0:raise ValueError("timeout must be positive")
    executor=ThreadPoolExecutor(max_workers=1);future=executor.submit(fn)
    try:return future.result(timeout=timeout_seconds)
    except FutureTimeout as exc:future.cancel();raise OperationTimeoutError("operation timed out") from exc
    finally:executor.shutdown(wait=False,cancel_futures=True)
def with_fallback(primary:Callable[[],T],fallback:Callable[[],T],recoverable:Callable[[Exception],bool]=lambda e:True)->T:
    try:return primary()
    except Exception as exc:
        if not recoverable(exc):raise
        return fallback()
def call_with_retry(fn:Callable[[],T],*,policy:RetryPolicy,retryable:Callable[[Exception],bool],breaker:CircuitBreaker|None=None)->T:
    if policy.attempts<1:raise ValueError("attempts must be positive")
    if breaker is not None and not breaker.allow():raise CircuitOpenError("circuit is open")
    for attempt in range(1,policy.attempts+1):
        try:
            result=fn()
            if breaker is not None:breaker.record_success()
            return result
        except Exception as exc:
            if breaker is not None:breaker.record_failure()
            if attempt>=policy.attempts or not retryable(exc):raise
            time.sleep(policy.delay(attempt))
    raise AssertionError("unreachable")