import pytest
from resilience import BoundedExecutor,CircuitBreaker,CircuitOpenError,RetryPolicy,TokenBucket,call_with_retry
def test_retry_is_bounded():
 n=[]
 def fn():
  n.append(1)
  if len(n)<3:raise TimeoutError
  return "ok"
 assert call_with_retry(fn,policy=RetryPolicy(3,0),retryable=lambda e:isinstance(e,TimeoutError))=="ok";assert len(n)==3
def test_non_retryable_fails_once():
 n=[]
 def fn():n.append(1);raise ValueError
 with pytest.raises(ValueError):call_with_retry(fn,policy=RetryPolicy(3,0),retryable=lambda e:False)
 assert len(n)==1
def test_concurrency_limit():
 ex=BoundedExecutor(1);ex._sem.acquire()
 try:
  with pytest.raises(RuntimeError):ex.run(lambda:"x")
 finally:ex._sem.release()
def test_rate_limit():b=TokenBucket(1,1);assert b.allow();assert not b.allow()
def test_circuit_open():
 b=CircuitBreaker(3,60)
 for _ in range(3):b.record_failure()
 with pytest.raises(CircuitOpenError):call_with_retry(lambda:"x",policy=RetryPolicy(1),retryable=lambda e:True,breaker=b)