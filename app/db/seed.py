"""Repeatable, additive demo data. Never deletes or overwrites existing records."""
from datetime import datetime

from sqlmodel import Session, select

from app.db.session import engine, init_db
from app.models import Appointment, Owner, Pet, Veterinarian


def seed_data(db_engine=engine):
    init_db(db_engine)
    created = {"owners": 0, "pets": 0, "veterinarians": 0, "appointments": 0}
    with Session(db_engine) as session:
        def obtain(model, values, key, *conditions):
            record = session.exec(select(model).where(*conditions)).first()
            if record is None:
                record = model.model_validate(values)
                session.add(record)
                session.flush()
                created[key] += 1
            return record

        owners, pets, vets = [], [], []
        for i, (name, pet_name, species, age) in enumerate([
            ("Айгүл (демо)", "Марғау (демо)", "Мысық", 2),
            ("Ерлан (демо)", "Ақтөс (демо)", "Ит", 5),
            ("Аружан (демо)", "Қарлығаш (демо)", "Құс", 1),
        ]):
            phone = f"DEMO-00{i + 1}"
            owner = obtain(Owner, dict(name=name, phone=phone), "owners", Owner.name == name, Owner.phone == phone)
            owners.append(owner)
            pets.append(obtain(Pet, dict(name=pet_name, species=species, age_years=age, owner_id=owner.id),
                               "pets", Pet.name == pet_name, Pet.owner_id == owner.id))
        for name, specialty in [("Дана (демо)", "Жалпы практика"), ("Арман (демо)", "Хирургия"), ("Әсел (демо)", "Құстар")]:
            vets.append(obtain(Veterinarian, dict(name=name, specialty=specialty), "veterinarians",
                               Veterinarian.name == name, Veterinarian.specialty == specialty))
        # Four visits demonstrate one pet seeing multiple vets and one vet seeing multiple pets.
        for pet_index, vet_index, day, hour in [(0, 0, 10, 10), (0, 1, 11, 11), (1, 0, 12, 10), (2, 2, 12, 12)]:
            starts_at = datetime(2026, 11, day, hour)
            pet, vet = pets[pet_index], vets[vet_index]
            conflict = session.exec(select(Appointment).where(
                Appointment.starts_at == starts_at,
                (Appointment.pet_id == pet.id) | (Appointment.veterinarian_id == vet.id),
            )).first()
            if conflict is None:
                session.add(Appointment(pet_id=pet.id, veterinarian_id=vet.id, starts_at=starts_at, reason="Жоспарлы тексеру (демо)"))
                session.flush()
                created["appointments"] += 1
        session.commit()
    return created
