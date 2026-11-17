"""Isolated API database; no test touches the user's SQLite file."""
import pytest
import secrets
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine
from app.db.session import get_session, enable_foreign_keys
from app.main import app
from app.security import create_account


@pytest.fixture(scope="session")
def credentials():
    return {"username": "test_admin", "password": secrets.token_urlsafe(24) + "aA1!"}


@pytest.fixture
def db_engine():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    event.listen(engine, "connect", enable_foreign_keys)
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def raw_client(db_engine):

    def override():
        with Session(db_engine) as session:
            yield session

    app.dependency_overrides[get_session] = override
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        test_client.close()
        app.dependency_overrides.clear()


@pytest.fixture
def client(raw_client, db_engine, credentials):
    with Session(db_engine) as session:
        create_account(session, **credentials, role="admin")
    response = raw_client.post("/api/auth/login", json=credentials)
    assert response.status_code == 200
    raw_client.headers["Authorization"] = f"Bearer {response.json()['access_token']}"
    return raw_client
