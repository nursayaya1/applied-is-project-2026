"""CI-only disposable deployment verification. Password supplied via environment."""
import os
import requests


def main():
    url = "http://127.0.0.1:8000"
    assert requests.get(url + "/health", timeout=10).status_code == 200
    assert requests.get(url + "/docs", timeout=10).status_code == 200
    assert requests.get("http://127.0.0.1:8501/_stcore/health", timeout=10).status_code == 200
    assert requests.get(url + "/api/owners", timeout=10).status_code == 401
    login = requests.post(url + "/api/auth/login", json={"username": "ci_admin", "password": os.environ["QUALITY_PASSWORD"]}, timeout=10)
    assert login.status_code == 200
    headers = {"Authorization": "Bearer " + login.json()["access_token"]}
    created = requests.post(url + "/api/owners", headers=headers, json={"name": "CI disposable", "phone": "test"}, timeout=10)
    assert created.status_code == 201
    path = url + f"/api/owners/{created.json()['id']}"
    assert requests.delete(path, headers=headers, timeout=10).status_code == 204
    assert requests.get(path, headers=headers, timeout=10).status_code == 404
    print("PASS: Docker backend/frontend health, protected API and create/delete")


if __name__ == "__main__":
    main()
