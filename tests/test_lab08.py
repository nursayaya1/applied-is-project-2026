"""Lab 8: real authorization, transactional integrity and complete PUT semantics."""
import secrets
import time
import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.models import Owner, Pet
from app.models.auth import Account, LoginSession
from app.security import create_account, hash_password, verify_password, token_digest


def test_unauthorized_resource(raw_client):
    response = raw_client.get("/api/owners")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_wrong_login_same_message(client, credentials):
    missing = client.post("/api/auth/login", json={**credentials, "username": "missing"})
    wrong = client.post("/api/auth/login", json={**credentials, "password": "incorrect"})
    assert missing.status_code == wrong.status_code == 401
    assert missing.json() == wrong.json()


@pytest.mark.parametrize("password", ["", "short", "a" * 20, "123456789012"])
def test_reject_weak_password(password):
    with pytest.raises(ValueError):
        hash_password(password)


def test_empty_login_password(client, credentials):
    response = client.post("/api/auth/login", json={**credentials, "password": ""})
    assert response.status_code == 422


def test_password_hashes_salted():
    password = secrets.token_urlsafe(20) + "aA1!"
    first, second = hash_password(password), hash_password(password)
    assert first != second and password not in first
    assert verify_password(password, first)
    assert not verify_password(password + "x", first)


def test_viewer_cannot_write(raw_client, db_engine):
    password = secrets.token_urlsafe(20) + "aA1!"
    with Session(db_engine) as session:
        create_account(session, "test_viewer", password, "viewer")
    response = raw_client.post("/api/auth/login", json={"username": "test_viewer", "password": password})
    raw_client.headers["Authorization"] = f"Bearer {response.json()['access_token']}"
    assert raw_client.get("/api/owners").status_code == 200
    for method, path in [("POST", "/api/owners"), ("PUT", "/api/owners/1"),
                         ("PATCH", "/api/owners/1"), ("DELETE", "/api/owners/1")]:
        assert raw_client.request(method, path, json={"name": "No", "phone": "No"}).status_code == 403
    assert raw_client.get("/api/owners").json() == []


def test_logout_revokes_token(client):
    assert client.get("/api/auth/me").json()["role"] == "admin"
    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/owners").status_code == 401


def test_expired_token(client, db_engine):
    token = client.headers["Authorization"].split()[1]
    with Session(db_engine) as session:
        record = session.get(LoginSession, token_digest(token))
        record.expires_at = time.time() - 1
        session.add(record)
        session.commit()
    assert client.get("/api/owners").status_code == 401


def test_disabled_account(client, db_engine):
    with Session(db_engine) as session:
        record = session.exec(select(Account)).one()
        record.active = False
        session.add(record)
        session.commit()
    assert client.get("/api/owners").status_code == 401


def test_secret_not_echoed_or_logged(client, credentials, caplog):
    response = client.post("/api/auth/login", json={**credentials, "password": {"secret": credentials["password"]}})
    assert response.status_code == 422
    assert credentials["password"] not in response.text
    assert credentials["password"] not in caplog.text
    assert "password_hash" not in client.get("/api/auth/me").text


def test_malformed_json(client):
    response = client.post("/api/owners", content='{invalid', headers={"Content-Type": "application/json"})
    assert response.status_code == 400
    assert "{invalid" not in response.text


def test_put_full_replace_and_persist(client, db_engine):
    owner = client.post("/api/owners", json={"name": "Before", "phone": "000"}).json()
    path = f"/api/owners/{owner['id']}"
    response = client.put(path, json={"name": "After", "phone": "111"})
    assert response.status_code == 200
    with Session(db_engine) as session:
        assert session.get(Owner, owner["id"]).name == "After"
    assert client.put(path, json={"name": "Incomplete"}).status_code == 422
    assert client.get(path).json() == response.json()
    assert client.delete(path).status_code == 204
    with Session(db_engine) as session:
        assert session.get(Owner, owner["id"]) is None


def test_put_unknown_id(client):
    assert client.put("/api/owners/999999", json={"name": "Name", "phone": "1"}).status_code == 404


def test_database_transaction_atomic_rollback(db_engine):
    with Session(db_engine) as session:
        session.add(Owner(name="Must rollback", phone="1"))
        session.flush()
        # SQLModel table constructors don't validate input; DB NOT NULL must protect it.
        session.add(Pet(name=None, species="Cat", age_years=1, owner_id=1))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        assert session.exec(select(Owner)).all() == []
        assert session.exec(select(Pet)).all() == []
        session.add(Owner(name="After rollback", phone="2"))
        session.commit()
        assert len(session.exec(select(Owner)).all()) == 1


def test_sql_injection_is_literal(client):
    client.post("/api/owners", json={"name": "Safe", "phone": "123"})
    response = client.get("/api/owners", params={"search": "' OR 1=1; DROP TABLE owner; --"})
    assert response.status_code == 200 and response.json() == []
    assert len(client.get("/api/owners").json()) == 1
