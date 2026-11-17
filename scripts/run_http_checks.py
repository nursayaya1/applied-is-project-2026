"""Requests -> real Uvicorn -> SQLite; save responses, never tokens/passwords."""
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import requests
from scripts.test_server import test_server


def main():
    records = []
    with test_server(port=18009) as (url, token, _):
        session = requests.Session()
        session.headers["Authorization"] = "Bearer " + token

        def check(name, method, path, expected, **kwargs):
            response = session.request(method, url + path, timeout=10, **kwargs)
            body = response.json() if response.content else None
            records.append({"name": name, "method": method, "path": path, "expected": expected,
                            "actual": response.status_code, "body": body})
            assert response.status_code == expected, name
            return body

        check("Read seed data", "GET", "/api/owners", 200)
        owner = check("Create", "POST", "/api/owners", 201, json={"name": "HTTP test", "phone": "test-only"})
        path = f"/api/owners/{owner['id']}"
        check("Read created", "GET", path, 200)
        check("Full replacement", "PUT", path, 200, json={"name": "HTTP updated", "phone": "new"})
        assert check("Read updated", "GET", path, 200)["name"] == "HTTP updated"
        check("Delete", "DELETE", path, 204)
        check("Read deleted", "GET", path, 404)
        check("Empty input", "POST", "/api/owners", 422, json={})
        check("Malformed JSON", "POST", "/api/owners", 400, data="{bad", headers={"Content-Type": "application/json"})
        check("Unknown identifier", "GET", "/api/pets/999999", 404)
        check("Without authorization", "GET", "/api/owners", 401, headers={"Authorization": ""})
        check("Wrong login", "POST", "/api/auth/login", 401, json={"username": "missing", "password": "incorrect"})
        check("Literal SQL injection search", "GET", "/api/owners", 200, params={"search": "' OR 1=1 --"})
        # Regression for the file-backed SQLite QueuePool exhaustion found at 100 users.
        def read_in_parallel(_):
            return requests.get(url + "/api/owners", headers={"Authorization": "Bearer " + token}, timeout=10).status_code
        with ThreadPoolExecutor(max_workers=50) as workers:
            statuses = list(workers.map(read_in_parallel, range(100)))
        assert statuses == [200] * 100
        records.append({"name": "Concurrent reads", "method": "GET", "path": "/api/owners",
                        "expected": 200, "actual": 200, "body": {"requests": 100, "workers": 50, "failures": 0}})
        session.close()
    output = Path("docs/reports/lab08")
    output.mkdir(parents=True, exist_ok=True)
    (output / "http-results.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"PASS: {len(records)} HTTP integration checks")


if __name__ == "__main__":
    main()
