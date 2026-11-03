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


def test_inventory_flow(client):
    assert client.get("/health").json() == {"status": "ok"}
    c = client.post("/api/categories", json={"name": "Кеңсе тауарлары"})
    s = client.post("/api/suppliers", json={"name": "Almaty Supply", "phone": "+7 700 000 00 00"})
    assert c.status_code == s.status_code == 201
    payload = dict(name="Дәптер", price_tiyn=35000, quantity=20,
                   category_id=c.json()["id"], supplier_id=s.json()["id"])
    response = client.post("/api/products", json=payload)
    assert response.status_code == 201
    assert client.get("/api/products").json() == [response.json()]


@pytest.mark.parametrize("field,value", [("quantity", -1), ("price_tiyn", -1), ("name", "")])
def test_invalid_product(client, field, value):
    payload = dict(name="Pen", price_tiyn=100, quantity=1, category_id=1, supplier_id=1)
    payload[field] = value
    assert client.post("/api/products", json=payload).status_code == 422


def test_missing_references(client):
    payload = dict(name="Pen", price_tiyn=100, quantity=1, category_id=999, supplier_id=999)
    assert client.post("/api/products", json=payload).status_code == 404
    category = client.post("/api/categories", json={"name": "Office"}).json()
    payload["category_id"] = category["id"]
    assert client.post("/api/products", json=payload).status_code == 404
