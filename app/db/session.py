from pathlib import Path
import os

from sqlalchemy import event
from sqlalchemy.pool import NullPool
from sqlmodel import Session, SQLModel, create_engine

from app.models import Appointment, Owner, Pet, Veterinarian  # Registers all tables.
from app.models.auth import Account, LoginSession  # Registers authentication tables.

DB_PATH = Path(os.getenv("DATABASE_PATH", str(Path(__file__).resolve().parents[2] / "vet_clinic.db"))).resolve()
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
engine = create_engine(
    f"sqlite:///{DB_PATH.as_posix()}", connect_args={"check_same_thread": False, "timeout": 10},
    # Short-lived SQLite connections avoid QueuePool starvation between sync
    # auth dependencies and handlers under concurrent requests (lab 8 evidence).
    poolclass=NullPool,
    echo=os.getenv("SQL_ECHO", "0") == "1",
    hide_parameters=True,
)


@event.listens_for(engine, "connect")
def enable_foreign_keys(connection, _):
    connection.execute("PRAGMA foreign_keys=ON")
    connection.create_function("casefold", 1, lambda value: value.casefold() if value else "", deterministic=True)


def init_db(db_engine=engine):
    # Set once at initialization, not on every connection. WAL lets readers
    # continue while a writer commits; SQLite still permits only one writer.
    if db_engine.dialect.name == "sqlite":
        with db_engine.connect() as connection:
            connection.exec_driver_sql("PRAGMA journal_mode=WAL")
    SQLModel.metadata.create_all(db_engine)


def create_db_and_tables():
    init_db()


def get_session():
    with Session(engine) as session:
        yield session
