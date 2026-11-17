import secrets
import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import HTTPAuthorizationCredentials
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.auth import Account, AccountPublic, LoginInput, LoginOutput, LoginSession
from app.security import (
    SESSION_SECONDS, bearer, current_account, hash_password, token_digest, verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["Кіру"])
DBSession = Annotated[Session, Depends(get_session)]
# Same expensive verification for a missing account to limit timing differences.
DUMMY_HASH = hash_password(secrets.token_urlsafe(32) + "aA1!")


@router.post("/login", response_model=LoginOutput)
def login(data: LoginInput, session: DBSession, response: Response):
    account = session.exec(select(Account).where(Account.username == data.username)).first()
    valid = verify_password(data.password.get_secret_value(), account.password_hash if account else DUMMY_HASH)
    if not valid or account is None or not account.active:
        raise HTTPException(401, "Логин немесе құпиясөз қате", headers={"WWW-Authenticate": "Bearer"})
    token = secrets.token_urlsafe(32)
    session.add(LoginSession(token_hash=token_digest(token), account_id=account.id,
                             expires_at=time.time() + SESSION_SECONDS))
    session.commit()
    response.headers["Cache-Control"] = "no-store"
    return LoginOutput(access_token=token, user=AccountPublic(username=account.username, role=account.role))


@router.get("/me", response_model=AccountPublic)
def me(account: Annotated[Account, Depends(current_account)]):
    return AccountPublic(username=account.username, role=account.role)


@router.post("/logout", status_code=204)
def logout(session: DBSession, account: Annotated[Account, Depends(current_account)],
           credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)]):
    record = session.get(LoginSession, token_digest(credentials.credentials))
    session.delete(record)
    session.commit()
    return Response(status_code=204)
