from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
from app.db.session import get_session
from app.models.clinic import (
    Appointment, AppointmentCreate, Owner, OwnerCreate,
    Pet, PetCreate, Veterinarian, VeterinarianCreate,
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
    session.commit()
    session.refresh(record)
    return record


@router.get("/owners", response_model=list[Owner])
def list_owners(session: DBSession):
    return session.exec(select(Owner).order_by(Owner.id)).all()


@router.post("/owners", response_model=Owner, status_code=201)
def create_owner(data: OwnerCreate, session: DBSession):
    return save(session, Owner.model_validate(data))


@router.get("/pets", response_model=list[Pet])
def list_pets(session: DBSession):
    return session.exec(select(Pet).order_by(Pet.id)).all()


@router.post("/pets", response_model=Pet, status_code=201)
def create_pet(data: PetCreate, session: DBSession):
    if session.get(Owner, data.owner_id) is None:
        raise HTTPException(404, "Жануардың иесі табылмады")
    return save(session, Pet.model_validate(data))


@router.get("/veterinarians", response_model=list[Veterinarian])
def list_veterinarians(session: DBSession):
    return session.exec(select(Veterinarian).order_by(Veterinarian.id)).all()


@router.post("/veterinarians", response_model=Veterinarian, status_code=201)
def create_veterinarian(data: VeterinarianCreate, session: DBSession):
    return save(session, Veterinarian.model_validate(data))


@router.get("/appointments", response_model=list[Appointment])
def list_appointments(session: DBSession):
    return session.exec(select(Appointment).order_by(Appointment.starts_at, Appointment.id)).all()


@router.post("/appointments", response_model=Appointment, status_code=201)
def create_appointment(data: AppointmentCreate, session: DBSession):
    if session.get(Pet, data.pet_id) is None:
        raise HTTPException(404, "Жануар табылмады")
    if session.get(Veterinarian, data.veterinarian_id) is None:
        raise HTTPException(404, "Ветеринар табылмады")
    try:
        return save(session, Appointment.model_validate(data))
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "Осы уақытта ветеринар немесе жануар басқа қабылдауға жазылған") from None
