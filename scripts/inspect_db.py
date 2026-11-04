"""Read-only structural inspection for lab 2: python -m scripts.inspect_db."""
from sqlalchemy import inspect, func
from sqlmodel import Session, select

from app.db.session import engine
from app.models import Appointment, Owner, Pet, Veterinarian


def main():
    inspector = inspect(engine)
    with Session(engine) as session:
        for model in (Owner, Pet, Veterinarian, Appointment):
            table = model.__tablename__
            if not inspector.has_table(table):
                raise SystemExit("Missing table. Run python seed.py first.")
            count = session.exec(select(func.count()).select_from(model)).one()
            print(f"{table}: rows={count}, PK={inspector.get_pk_constraint(table)['constrained_columns']}")
            for key in inspector.get_foreign_keys(table):
                print(f"  FK {key['constrained_columns']} -> {key['referred_table']}.{key['referred_columns']}")
        print("SQLite foreign_key_check:", session.connection().exec_driver_sql("PRAGMA foreign_key_check").all())


if __name__ == "__main__":
    main()
