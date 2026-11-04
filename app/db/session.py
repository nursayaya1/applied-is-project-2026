from pathlib import Path
import os

from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine

from app.models import Appointment, Owner, Pet, Veterinarian  # Registers all tables.

DB_PATH = Path(__file__).resolve().parents[2] / "vet_clinic.db"
engine = create_engine(
    f"sqlite:///{DB_PATH.as_posix()}", connect_args={"check_same_thread": False},
    echo=os.getenv("SQL_ECHO", "0") == "1",
)


@event.listens_for(engine, "connect")
def enable_foreign_keys(connection, _):
    connection.execute("PRAGMA foreign_keys=ON")
    connection.create_function("casefold", 1, lambda value: value.casefold() if value else "", deterministic=True)


def init_db(db_engine=engine):
    SQLModel.metadata.create_all(db_engine)


def create_db_and_tables():
    init_db()


def get_session():
    with Session(engine) as session:
        yield session
