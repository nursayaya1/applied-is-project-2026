"""Requests -> real Uvicorn -> SQLite; save responses, never tokens/passwords."""
import json
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
        session.close()
    output = Path("docs/reports/lab08")
    output.mkdir(parents=True, exist_ok=True)
    (output / "http-results.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"PASS: {len(records)} HTTP integration checks")


if __name__ == "__main__":
    main()
