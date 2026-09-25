from locust import HttpUser, task, between


class APIUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task
    def domain(self):
        self.client.post(
            "/v1/security",
            json={
                "key": "load",
                "payload": {
                    "prompt": "load",
                    "actor": "load",
                    "scope": "inference",
                    "token": "Bearer inference",
                    "model": "m",
                    "input_tokens": 100,
                    "output_tokens": 50,
                    "compute_seconds": 1,
                    "input_per_1k": 1,
                    "output_per_1k": 1,
                    "compute_per_s": 1,
                    "target": 0.99,
                    "total": 100,
                    "successes": 99,
                    "version": "1",
                    "expires_at": 9999999999,
                    "now": 0,
                    "steps": ["a"],
                    "value": 1,
                },
            },
            name="/v1/security",
        )
