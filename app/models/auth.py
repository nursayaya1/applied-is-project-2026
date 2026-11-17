"""Accounts and revocable, expiring sessions; no plaintext credentials in the DB."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field as SchemaField, SecretStr
from sqlmodel import Field, SQLModel


class Account(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    password_hash: str
    role: str = Field(default="viewer")
    active: bool = True


class LoginSession(SQLModel, table=True):
    token_hash: str = Field(primary_key=True)
    account_id: int = Field(foreign_key="account.id", index=True)
    expires_at: float


class LoginInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = SchemaField(min_length=1, max_length=64)
    password: SecretStr = SchemaField(min_length=1, max_length=256)


class AccountPublic(BaseModel):
    username: str
    role: Literal["admin", "viewer"]


class LoginOutput(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AccountPublic
