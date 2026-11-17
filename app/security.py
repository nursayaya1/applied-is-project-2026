"""Local clinic authentication. Use HTTPS when deployed outside localhost."""
import hashlib
import hmac
import re
import secrets
import time
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.auth import Account, LoginSession

ITERATIONS = 600_000
SESSION_SECONDS = 8 * 60 * 60
bearer = HTTPBearer(auto_error=False)


def validate_password(password: str):
    if not 12 <= len(password) <= 256 or not all((
        re.search(r"[a-z]", password), re.search(r"[A-Z]", password),
        re.search(r"[0-9]", password), re.search(r"[^a-zA-Z0-9\s]", password),
    )):
        raise ValueError("Құпиясөз: 12–256 таңба, үлкен/кіші латын әрпі, сан және арнайы таңба қажет")


def hash_password(password: str) -> str:
    validate_password(password)
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), ITERATIONS).hex()
    return f"pbkdf2_sha256${ITERATIONS}${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    algorithm, iterations, salt, expected = stored.split("$")
    if algorithm != "pbkdf2_sha256":
        return False
    actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(iterations)).hex()
    return hmac.compare_digest(actual, expected)


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_account(session: Session, username: str, password: str, role: str):
    if not re.fullmatch(r"[a-zA-Z0-9_.-]{3,64}", username):
        raise ValueError("Логин: 3–64 латын әрпі, сан, нүкте, сызықша не астын сызу")
    if role not in {"admin", "viewer"}:
        raise ValueError("Unknown role")
    if session.exec(select(Account).where(Account.username == username)).first():
        raise ValueError("Бұл логин тіркелген")
    account = Account(username=username, password_hash=hash_password(password), role=role)
    session.add(account)
    session.commit()
    session.refresh(account)
    return account


def unauthorized():
    return HTTPException(401, "Кіру қажет немесе сессия жарамсыз", headers={"WWW-Authenticate": "Bearer"})


def current_account(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    session: Annotated[Session, Depends(get_session)],
) -> Account:
    if credentials is None:
        raise unauthorized()
    login = session.get(LoginSession, token_digest(credentials.credentials))
    if login is None or login.expires_at <= time.time():
        raise unauthorized()
    account = session.get(Account, login.account_id)
    if account is None or not account.active:
        raise unauthorized()
    return account


def require_access(request: Request, account: Annotated[Account, Depends(current_account)]):
    if request.method not in {"GET", "HEAD", "OPTIONS"} and account.role != "admin":
        raise HTTPException(403, "Бұл әрекетке әкімші рөлі қажет")
    return account
