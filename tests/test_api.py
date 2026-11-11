import pytest


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


@pytest.mark.parametrize("path", ["owners", "pets", "veterinarians", "appointments"])
def test_missing_update_delete(client, path):
    assert client.patch(f"/api/{path}/99999", json={}).status_code == 404
    assert client.delete(f"/api/{path}/99999").status_code == 404


def test_patch_and_safe_delete_lifecycle(client):
    owner, pet, vet = register(client)
    visit = client.post("/api/appointments", json=dict(pet_id=pet["id"], veterinarian_id=vet["id"], starts_at="2026-11-10T10:00:00", reason="Exam")).json()
    for path, item, changes in [
        ("owners", owner, {"phone": "DEMO-NEW"}),
        ("pets", pet, {"age_years": 4}),
        ("veterinarians", vet, {"specialty": "Хирургия"}),
        ("appointments", visit, {"reason": "Жаңа себеп"}),
    ]:
        url = f"/api/{path}/{item['id']}"
        result = client.patch(url, json=changes)
        assert result.status_code == 200
        assert result.json() == {**item, **changes}
        assert client.get(url).json() == result.json()
    for path, item in [("owners", owner), ("pets", pet), ("veterinarians", vet)]:
        assert client.delete(f"/api/{path}/{item['id']}").status_code == 409
        assert client.get(f"/api/{path}/{item['id']}").status_code == 200
    for path, item in [("appointments", visit), ("pets", pet), ("owners", owner), ("veterinarians", vet)]:
        url = f"/api/{path}/{item['id']}"
        response = client.delete(url)
        assert response.status_code == 204 and response.content == b""
        assert client.get(url).status_code == 404
        assert client.patch(url, json={}).status_code == 404
        assert client.delete(url).status_code == 404
        assert client.get(f"/api/{path}").json() == []


@pytest.mark.parametrize("changes", [{"name": " "}, {"age_years": -1}, {"name": None}, {"id": 777}, {"unknown": 1}])
def test_patch_validation_and_unchanged_data(client, changes):
    _, pet, _ = register(client)
    url = f"/api/pets/{pet['id']}"
    assert client.patch(url, json=changes).status_code == 422
    assert client.get(url).json() == pet


def test_patch_references_conflict_and_rollback(client):
    owner, pet, vet = register(client)
    assert client.patch(f"/api/pets/{pet['id']}", json={"owner_id": 99999}).status_code == 404
    assert client.get(f"/api/pets/{pet['id']}").json() == pet
    new_owner = client.post("/api/owners", json={"name": "New", "phone": "DEMO-2"}).json()
    assert client.patch(f"/api/pets/{pet['id']}", json={"owner_id": new_owner["id"]}).json()["owner_id"] == new_owner["id"]
    base = dict(pet_id=pet["id"], veterinarian_id=vet["id"], reason="Exam")
    first = client.post("/api/appointments", json={**base, "starts_at": "2026-11-10T10:00:00"}).json()
    second = client.post("/api/appointments", json={**base, "starts_at": "2026-11-10T11:00:00"}).json()
    url = f"/api/appointments/{second['id']}"
    assert client.patch(url, json={"starts_at": first["starts_at"]}).status_code == 409
    assert client.get(url).json() == second
    assert client.patch(url, json={"veterinarian_id": 99999}).status_code == 404
    assert client.patch(url, json={"starts_at": "2026-11-10T11:00:01"}).status_code == 422
    assert client.patch(url, json={"starts_at": "2026-11-10T12:00:00"}).status_code == 200


def test_search_and_ranges(client):
    owner, pet, vet = register(client)
    client.post("/api/pets", json=dict(name="Ақтөс", species="Ит", age_years=5, owner_id=owner["id"]))
    assert client.get("/api/pets", params={"search": "МАРҒ", "min_age": 2, "max_age": 2, "species": "мысық", "owner_id": owner["id"]}).json() == [pet]
    assert client.get("/api/pets", params={"min_age": 3}).json()[0]["name"] == "Ақтөс"
    assert client.get("/api/pets", params={"search": "%' OR 1=1 --"}).json() == []
    assert client.get("/api/pets", params={"search": "%"}).json() == []
    assert client.get("/api/pets", params={"min_age": 5, "max_age": 2}).status_code == 422
    assert client.get("/api/pets", params={"min_age": -1}).status_code == 422
    assert client.get("/api/owners", params={"search": "АЙГҮЛ"}).json() == [owner]
    assert client.get("/api/veterinarians", params={"search": "ДАН", "specialty": "жалпы практика"}).json() == [vet]
    visit = client.post("/api/appointments", json=dict(pet_id=pet["id"], veterinarian_id=vet["id"], starts_at="2026-11-10T10:00:00", reason="Жоспарлы тексеру")).json()
    params = dict(pet_id=pet["id"], veterinarian_id=vet["id"], search="ТЕКСЕРУ", starts_from="2026-11-10T10:00:00", starts_until="2026-11-10T10:00:00")
    assert client.get("/api/appointments", params=params).json() == [visit]
    assert client.get("/api/appointments", params={"starts_from": "2026-11-11T10:00:00"}).json() == []
    assert client.get("/api/appointments", params={"starts_from": "2026-11-11T00:00:00", "starts_until": "2026-11-10T00:00:00"}).status_code == 422
    assert client.get("/api/appointments", params={"starts_from": "2026-11-11T00:00:00Z"}).status_code == 422


def test_openapi_contract(client):
    paths = client.get("/openapi.json").json()["paths"]
    for path in ["owners", "pets", "veterinarians", "appointments"]:
        assert {"get", "post"} <= paths[f"/api/{path}"].keys()
        assert {"get", "patch", "delete"} <= paths[f"/api/{path}/{{record_id}}"].keys()
