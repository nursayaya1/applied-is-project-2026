from typing import Annotated
from datetime import datetime
import json
from pydantic import ValidationError
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from sqlmodel import Session, select
from app.db.session import get_session
from app.models.clinic import (
    Appointment, AppointmentCreate, Owner, OwnerCreate,
    Pet, PetCreate, Veterinarian, VeterinarianCreate,
    OwnerUpdate, PetUpdate, VeterinarianUpdate, AppointmentUpdate,
)

router = APIRouter(prefix="/api")
DBSession = Annotated[Session, Depends(get_session)]


def require_record(session, model, record_id):
    record = session.get(model, record_id)
    if record is None:
        raise HTTPException(404, "Жазба табылмады")
    return record


@router.get("/owners/{record_id}", response_model=Owner)
def get_owner(record_id: int, session: DBSession):
    return require_record(session, Owner, record_id)


@router.get("/pets/{record_id}", response_model=Pet)
def get_pet(record_id: int, session: DBSession):
    return require_record(session, Pet, record_id)


@router.get("/veterinarians/{record_id}", response_model=Veterinarian)
def get_veterinarian(record_id: int, session: DBSession):
    return require_record(session, Veterinarian, record_id)


@router.get("/appointments/{record_id}", response_model=Appointment)
def get_appointment(record_id: int, session: DBSession):
    return require_record(session, Appointment, record_id)


def save(session, record):
    session.add(record)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "Байланыс немесе қабылдау уақытының қайшылығы") from None
    session.refresh(record)
    return record


@router.get("/owners", response_model=list[Owner])
def list_owners(session: DBSession, search: str | None = None):
    query = select(Owner)
    if search is not None:
        query = query.where(func.instr(func.casefold(Owner.name), search.strip().casefold()) > 0)
    return session.exec(query.order_by(Owner.id)).all()


@router.post("/owners", response_model=Owner, status_code=201)
def create_owner(data: OwnerCreate, session: DBSession):
    return save(session, Owner.model_validate(data))


@router.get("/pets", response_model=list[Pet])
def list_pets(
    session: DBSession, search: str | None = None, species: str | None = None,
    owner_id: int | None = Query(default=None, gt=0),
    min_age: int | None = Query(default=None, ge=0, le=100),
    max_age: int | None = Query(default=None, ge=0, le=100),
):
    if min_age is not None and max_age is not None and min_age > max_age:
        raise HTTPException(422, "min_age max_age мәнінен үлкен болмауы тиіс")
    query = select(Pet)
    if search is not None:
        query = query.where(func.instr(func.casefold(Pet.name), search.strip().casefold()) > 0)
    if species is not None:
        query = query.where(func.casefold(Pet.species) == species.strip().casefold())
    if owner_id is not None:
        query = query.where(Pet.owner_id == owner_id)
    if min_age is not None:
        query = query.where(Pet.age_years >= min_age)
    if max_age is not None:
        query = query.where(Pet.age_years <= max_age)
    return session.exec(query.order_by(Pet.id)).all()


@router.post("/pets", response_model=Pet, status_code=201)
def create_pet(data: PetCreate, session: DBSession):
    if session.get(Owner, data.owner_id) is None:
        raise HTTPException(404, "Жануардың иесі табылмады")
    return save(session, Pet.model_validate(data))


@router.get("/veterinarians", response_model=list[Veterinarian])
def list_veterinarians(session: DBSession, search: str | None = None, specialty: str | None = None):
    query = select(Veterinarian)
    if search is not None:
        query = query.where(func.instr(func.casefold(Veterinarian.name), search.strip().casefold()) > 0)
    if specialty is not None:
        query = query.where(func.casefold(Veterinarian.specialty) == specialty.strip().casefold())
    return session.exec(query.order_by(Veterinarian.id)).all()


@router.post("/veterinarians", response_model=Veterinarian, status_code=201)
def create_veterinarian(data: VeterinarianCreate, session: DBSession):
    return save(session, Veterinarian.model_validate(data))


@router.get("/appointments", response_model=list[Appointment])
def list_appointments(
    session: DBSession, search: str | None = None,
    pet_id: int | None = Query(default=None, gt=0),
    veterinarian_id: int | None = Query(default=None, gt=0),
    starts_from: datetime | None = None, starts_until: datetime | None = None,
):
    for value in (starts_from, starts_until):
        if value is not None and value.tzinfo is not None:
            raise HTTPException(422, "Клиниканың жергілікті уақытын белдеу жұрнағынсыз беріңіз")
    if starts_from is not None and starts_until is not None and starts_from > starts_until:
        raise HTTPException(422, "Уақыт аралығы қате")
    query = select(Appointment)
    if search is not None:
        query = query.where(func.instr(func.casefold(Appointment.reason), search.strip().casefold()) > 0)
    if pet_id is not None:
        query = query.where(Appointment.pet_id == pet_id)
    if veterinarian_id is not None:
        query = query.where(Appointment.veterinarian_id == veterinarian_id)
    if starts_from is not None:
        query = query.where(Appointment.starts_at >= starts_from)
    if starts_until is not None:
        query = query.where(Appointment.starts_at <= starts_until)
    return session.exec(query.order_by(Appointment.starts_at, Appointment.id)).all()


@router.post("/appointments", response_model=Appointment, status_code=201)
def create_appointment(data: AppointmentCreate, session: DBSession):
    if session.get(Pet, data.pet_id) is None:
        raise HTTPException(404, "Жануар табылмады")
    if session.get(Veterinarian, data.veterinarian_id) is None:
        raise HTTPException(404, "Ветеринар табылмады")
    return save(session, Appointment.model_validate(data))


REFERENCES = {
    Pet: {"owner_id": Owner},
    Appointment: {"pet_id": Pet, "veterinarian_id": Veterinarian},
}
DEPENDENTS = {
    Owner: (Pet, Pet.owner_id),
    Pet: (Appointment, Appointment.pet_id),
    Veterinarian: (Appointment, Appointment.veterinarian_id),
}


def update_record(session, model, create_schema, record_id, changes):
    record = require_record(session, model, record_id)
    values = changes.model_dump(exclude_unset=True)
    merged = {**record.model_dump(exclude={"id"}), **values}
    try:
        validated = create_schema.model_validate(merged)
    except ValidationError as error:
        raise HTTPException(422, json.loads(error.json())) from None
    for field, target in REFERENCES.get(model, {}).items():
        require_record(session, target, getattr(validated, field))
    record.sqlmodel_update(values)
    return save(session, record)


def delete_record(session, model, record_id):
    record = require_record(session, model, record_id)
    if model in DEPENDENTS:
        child, foreign_key = DEPENDENTS[model]
        if session.exec(select(child).where(foreign_key == record_id)).first() is not None:
            raise HTTPException(409, "Алдымен осы жазбаға байланысты жазбаларды жойыңыз")
    session.delete(record)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "Жазба басқа мәліметтермен байланысты") from None
    return Response(status_code=204)


@router.patch("/owners/{record_id}", response_model=Owner)
def update_owner(record_id: int, data: OwnerUpdate, session: DBSession):
    return update_record(session, Owner, OwnerCreate, record_id, data)


@router.delete("/owners/{record_id}", status_code=204)
def delete_owner(record_id: int, session: DBSession):
    return delete_record(session, Owner, record_id)


@router.patch("/pets/{record_id}", response_model=Pet)
def update_pet(record_id: int, data: PetUpdate, session: DBSession):
    return update_record(session, Pet, PetCreate, record_id, data)


@router.delete("/pets/{record_id}", status_code=204)
def delete_pet(record_id: int, session: DBSession):
    return delete_record(session, Pet, record_id)


@router.patch("/veterinarians/{record_id}", response_model=Veterinarian)
def update_veterinarian(record_id: int, data: VeterinarianUpdate, session: DBSession):
    return update_record(session, Veterinarian, VeterinarianCreate, record_id, data)


@router.delete("/veterinarians/{record_id}", status_code=204)
def delete_veterinarian(record_id: int, session: DBSession):
    return delete_record(session, Veterinarian, record_id)


@router.patch("/appointments/{record_id}", response_model=Appointment)
def update_appointment(record_id: int, data: AppointmentUpdate, session: DBSession):
    return update_record(session, Appointment, AppointmentCreate, record_id, data)


@router.delete("/appointments/{record_id}", status_code=204)
def delete_appointment(record_id: int, session: DBSession):
    return delete_record(session, Appointment, record_id)
