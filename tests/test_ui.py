from pathlib import Path

from streamlit.testing.v1 import AppTest
import requests
import pytest

UI_PATH = str(Path(__file__).resolve().parents[1] / "frontend/app.py")


def signed_page(token="unit-test-token"):
    page = AppTest.from_file(UI_PATH, default_timeout=30)
    page.session_state["access_token"] = token
    page.session_state["user"] = {"username": "test_admin", "role": "admin"}
    return page


@pytest.fixture
def connected_ui(client, monkeypatch):
    calls = []

    def request(method, url, **kwargs):
        path = "/api/" + url.split("/api/", 1)[1]
        response = client.request(method, path, params=kwargs.get("params"), json=kwargs.get("json"), headers=kwargs.get("headers"))
        calls.append((method, path, kwargs))
        result = requests.Response()
        result.status_code = response.status_code
        result._content = response.content
        return result

    monkeypatch.setattr("requests.request", request)
    return signed_page(client.headers["Authorization"].split()[1]), calls


def element(elements, label):
    return next(item for item in elements if item.label == label)


def test_ui_create_search_and_delete(connected_ui, client):
    page, calls = connected_ui
    page.run()
    element(page.text_input, "Иесінің аты-жөні").input("Жаңа иесі")
    element(page.text_input, "Телефон нөмірі").input("+7 700 000 00 01")
    element(page.button, "Иесін қосу").click().run()
    assert not page.exception and page.success
    assert len(client.get("/api/owners").json()) == 1
    page.text_input(key="owner_search").input("ЖАҢА").run()
    assert any(method == "GET" and path == "/api/owners" and kw.get("params") == {"search": "ЖАҢА"} for method, path, kw in calls)
    assert any("Жаңа иесі" in str(frame.value) for frame in page.dataframe)
    assert page.button(key="delete_owners").disabled
    page.checkbox(key="confirm_owners_1").check().run()
    page.button(key="delete_owners").click().run()
    assert not page.exception and page.success
    assert client.get("/api/owners").json() == []


def test_ui_blocks_related_owner_delete(connected_ui, client):
    owner = client.post("/api/owners", json={"name": "Иесі", "phone": "test"}).json()
    client.post("/api/pets", json={"name": "Марғау", "species": "Мысық", "age_years": 2, "owner_id": owner["id"]})
    page, _ = connected_ui
    page.run()
    page.checkbox(key=f"confirm_owners_{owner['id']}").check().run()
    page.button(key="delete_owners").click().run()
    assert page.error and not page.exception
    assert client.get(f"/api/owners/{owner['id']}").status_code == 200


def test_ui_disconnected_backend(monkeypatch):
    def unavailable(*args, **kwargs):
        raise requests.ConnectionError("offline")
    monkeypatch.setattr("requests.request", unavailable)
    page = signed_page().run()
    assert len(page.error) == 1 and not page.exception


def test_ui_non_json_backend_error(monkeypatch):
    response = requests.Response()
    response.status_code = 502
    response._content = b"<html>Bad gateway</html>"
    monkeypatch.setattr("requests.request", lambda *args, **kwargs: response)
    page = signed_page().run()
    assert len(page.error) == 1 and not page.exception


def test_populated_clinic_ui(monkeypatch):
    data = {
        "owners": [{"id": 1, "name": "Айгүл", "phone": "demo"}],
        "pets": [{"id": 1, "name": "Марғау", "species": "Мысық", "age_years": 2, "owner_id": 1}],
        "veterinarians": [{"id": 1, "name": "Дана", "specialty": "Жалпы практика"}],
        "appointments": [{"id": 1, "pet_id": 1, "veterinarian_id": 1,
                          "starts_at": "2026-11-10T10:00:00", "reason": "Тексеру"}],
    }

    class Response:
        ok = True
        status_code = 200

        def __init__(self, rows):
            self.rows = rows

        def json(self):
            return self.rows

    monkeypatch.setattr("requests.request", lambda method, url, **kwargs: Response(data[url.rsplit("/", 1)[-1]]))
    page = signed_page().run(timeout=30)
    assert not page.exception
    assert not page.error
    assert [m.value for m in page.metric] == ["1", "1", "1", "1"]
    assert len(page.tabs) == 4
    assert len(page.date_input) == 1
    assert len(page.time_input) == 1
    assert any("Марғау" in str(frame.value) for frame in page.dataframe)


def test_ui_login_and_logout(connected_ui, credentials):
    page, calls = connected_ui
    del page.session_state["access_token"]
    del page.session_state["user"]
    page.run()
    assert not page.tabs
    page.text_input(key="login_username").input(credentials["username"])
    page.text_input(key="login_password").input(credentials["password"])
    element(page.button, "Кіру").click().run()
    assert len(page.tabs) == 4 and not page.exception
    page.button(key="logout").click().run()
    assert not page.tabs and not page.exception
    assert page.text_input(key="login_password").value == ""


def test_ui_viewer_cannot_edit(connected_ui):
    page, _ = connected_ui
    page.session_state["user"] = {"username": "viewer", "role": "viewer"}
    page.run()
    assert element(page.button, "Иесін қосу").disabled
    assert not any(button.key == "delete_owners" for button in page.button)


def test_ui_invalid_login(connected_ui):
    page, _ = connected_ui
    del page.session_state["access_token"]
    del page.session_state["user"]
    page.run()
    page.text_input(key="login_username").input("missing")
    page.text_input(key="login_password").input("incorrect")
    element(page.button, "Кіру").click().run()
    assert page.error and not page.exception and not page.tabs

