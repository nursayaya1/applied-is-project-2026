from pathlib import Path

from streamlit.testing.v1 import AppTest


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

        def __init__(self, rows):
            self.rows = rows

        def json(self):
            return self.rows

    monkeypatch.setattr("requests.request", lambda method, url, **kwargs: Response(data[url.rsplit("/", 1)[-1]]))
    page = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "frontend/app.py")).run()
    assert not page.exception
    assert not page.error
    assert [m.value for m in page.metric] == ["1", "1", "1", "1"]
    assert len(page.tabs) == 4
    assert len(page.date_input) == 1
    assert len(page.time_input) == 1
    assert any("Марғау" in str(frame.value) for frame in page.dataframe)
