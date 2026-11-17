"""Authorized disposable clinic workload; each user deletes only its own records."""
import os
import uuid
from locust import HttpUser, between, task


class ClinicUser(HttpUser):
    wait_time = between(0.2, 0.8)

    def on_start(self):
        self.client.headers["Authorization"] = "Bearer " + os.environ["LOAD_TEST_TOKEN"]

    @task(4)
    def browse(self):
        for path in ("owners", "pets", "veterinarians", "appointments"):
            with self.client.get(f"/api/{path}", catch_response=True) as response:
                if response.status_code != 200:
                    response.failure(f"Expected 200, got {response.status_code}")
                elif not isinstance(response.json(), list):
                    response.failure("Expected JSON list")

    @task(2)
    def search(self):
        self.client.get("/api/pets", params={"search": "Мар", "min_age": 0, "max_age": 100}, name="/api/pets?filters")

    @task(1)
    def owner_lifecycle(self):
        with self.client.post("/api/owners", json={"name": "Load-" + uuid.uuid4().hex, "phone": "test-only"},
                              catch_response=True) as response:
            if response.status_code != 201:
                response.failure(f"Expected 201, got {response.status_code}")
                return
            record_id = response.json()["id"]
        try:
            self.client.put(f"/api/owners/{record_id}", json={"name": "Load-updated", "phone": "test-only"}, name="/api/owners/[id]")
        finally:
            self.client.delete(f"/api/owners/{record_id}", name="/api/owners/[id]")
