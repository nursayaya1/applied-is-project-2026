import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

from app.db.session import get_session
from app.main import app


@pytest.fixture
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)

    def override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override
    # No lifespan: all test tables live exclusively in memory.
    yield TestClient(app)
    app.dependency_overrides.clear()
    engine.dispose()


def register(client):
    owner = client.post("/api/owners", json={"name": "Айгүл", "phone": "+7 700 000 00 00"})
    assert owner.status_code == 201
    pet = client.post("/api/pets", json={"name": "Марғау", "species": "Мысық", "age_years": 2, "owner_id": owner.json()["id"]})
    vet = client.post("/api/veterinarians", json={"name": "Дана", "specialty": "Жалпы практика"})
    assert pet.status_code == vet.status_code == 201
    return owner.json(), pet.json(), vet.json()


def test_clinic_flow(client):
    assert client.get("/health").json() == {"status": "ok"}
    owner, pet, vet = register(client)
    payload = dict(pet_id=pet["id"], veterinarian_id=vet["id"], starts_at="2026-11-10T10:00:00", reason="Жоспарлы тексеру")
    response = client.post("/api/appointments", json=payload)
    assert response.status_code == 201
    assert client.get("/api/appointments").json() == [response.json()]
    for path, record in [("owners", owner), ("pets", pet), ("veterinarians", vet)]:
        assert client.get(f"/api/{path}").json() == [record]
        assert client.get(f"/api/{path}/{record['id']}").json() == record
    assert client.get(f"/api/appointments/{response.json()['id']}").json() == response.json()
    assert client.get("/api/products").status_code == 404


@pytest.mark.parametrize("path", ["owners", "pets", "veterinarians", "appointments"])
def test_get_missing_id(client, path):
    assert client.get(f"/api/{path}/99999").status_code == 404


def test_root_and_client_id_rejection(client):
    assert client.get("/").json()["status"] == "ok"
    assert client.post("/api/owners", json={"id": 500, "name": "Test", "phone": "DEMO"}).status_code == 422


@pytest.mark.parametrize("field,value", [("age_years", -1), ("age_years", 101), ("name", "   "), ("species", "")])
def test_invalid_pet(client, field, value):
    payload = dict(name="Марғау", species="Мысық", age_years=2, owner_id=1)
    payload[field] = value
    assert client.post("/api/pets", json=payload).status_code == 422


def test_missing_references(client):
    assert client.post("/api/pets", json=dict(name="Cat", species="Cat", age_years=0, owner_id=999)).status_code == 404
    payload = dict(pet_id=999, veterinarian_id=999, starts_at="2026-11-10T10:00:00", reason="Exam")
    assert client.post("/api/appointments", json=payload).status_code == 404
    _, pet, _ = register(client)
    payload["pet_id"] = pet["id"]
    assert client.post("/api/appointments", json=payload).status_code == 404


def test_duplicate_booking(client):
    owner, pet, vet = register(client)
    payload = dict(pet_id=pet["id"], veterinarian_id=vet["id"], starts_at="2026-11-10T10:00:00", reason="Exam")
    assert client.post("/api/appointments", json=payload).status_code == 201
    second_pet = client.post("/api/pets", json=dict(name="Ақтөс", species="Ит", age_years=3, owner_id=owner["id"])).json()
    assert client.post("/api/appointments", json={**payload, "pet_id": second_pet["id"]}).status_code == 409
    second_vet = client.post("/api/veterinarians", json=dict(name="Ерлан", specialty="Хирург" )).json()
    assert client.post("/api/appointments", json={**payload, "veterinarian_id": second_vet["id"]}).status_code == 409
    assert client.post("/api/appointments", json={**payload, "starts_at": "2026-11-10T11:00:00"}).status_code == 201
    assert len(client.get("/api/appointments").json()) == 2


@pytest.mark.parametrize("value", ["not-a-date", "2026-11-10T10:00:00+05:00", "2026-11-10T10:00:01"])
def test_invalid_appointment_time(client, value):
    payload = dict(pet_id=1, veterinarian_id=1, starts_at=value, reason="Exam")
    assert client.post("/api/appointments", json=payload).status_code == 422


def test_required_fields(client):
    assert client.post("/api/owners", json={"name": "Айгүл", "phone": " "}).status_code == 422
    assert client.post("/api/veterinarians", json={"name": "Дана", "specialty": ""}).status_code == 422
    payload = dict(pet_id=1, veterinarian_id=1, starts_at="2026-11-10T10:00:00", reason=" ")
    assert client.post("/api/appointments", json=payload).status_code == 422
