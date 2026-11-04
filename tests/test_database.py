from sqlalchemy import event, inspect
from sqlmodel import Session, create_engine, select

from app.db.seed import seed_data
from app.models import Owner, Pet, Veterinarian, Appointment


def test_seed_and_relationships(tmp_path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'clinic.db').as_posix()}")
    event.listen(engine, "connect", lambda connection, _: connection.execute("PRAGMA foreign_keys=ON"))
    assert seed_data(engine) == dict(owners=3, pets=3, veterinarians=3, appointments=4)
    assert seed_data(engine) == dict(owners=0, pets=0, veterinarians=0, appointments=0)
    with Session(engine) as session:
        owner = session.exec(select(Owner).where(Owner.name == "Айгүл")).one()
        pet = owner.pets[0]
        assert pet.owner.id == owner.id
        assert len(pet.appointments) == 2
        assert len(pet.veterinarians) == 2
        vet = session.exec(select(Veterinarian).where(Veterinarian.name == "Дана")).one()
        assert len(vet.patients) == 2
        assert vet.appointments[0].veterinarian.id == vet.id
        assert len(session.exec(select(Appointment)).all()) == 4
    assert len(inspect(engine).get_foreign_keys("appointment")) == 2
    engine.dispose()
