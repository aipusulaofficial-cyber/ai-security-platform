from locust import HttpUser,task,between
class APIUser(HttpUser):
 wait_time=between(.1,.5)
 @task
 def health(self):self.client.get("/health/live",name="health")
