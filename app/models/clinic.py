"""Veterinary clinic database tables and validated request schemas."""
from datetime import datetime
from pydantic import ConfigDict, field_validator, model_validator
from sqlalchemy import DateTime, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel


class InputModel(SQLModel):
    model_config = ConfigDict(extra="forbid")
    @field_validator("*", mode="before")
    @classmethod
    def trim_strings(cls, value):
        return value.strip() if isinstance(value, str) else value


class OwnerCreate(InputModel):
    name: str = Field(min_length=1, max_length=100)
    phone: str = Field(min_length=1, max_length=30)


class Owner(OwnerCreate, table=True):
    id: int | None = Field(default=None, primary_key=True)
    pets: list["Pet"] = Relationship(back_populates="owner", passive_deletes="all")


class PetCreate(InputModel):
    name: str = Field(min_length=1, max_length=100)
    species: str = Field(min_length=1, max_length=60)
    age_years: int = Field(ge=0, le=100)
    owner_id: int = Field(foreign_key="owner.id", gt=0)


class Pet(PetCreate, table=True):
    id: int | None = Field(default=None, primary_key=True)
    owner: Owner = Relationship(back_populates="pets")
    appointments: list["Appointment"] = Relationship(back_populates="pet", passive_deletes="all")
    veterinarians: list["Veterinarian"] = Relationship(
        back_populates="patients",
        sa_relationship_kwargs={"secondary": "appointment", "viewonly": True},
    )


class VeterinarianCreate(InputModel):
    name: str = Field(min_length=1, max_length=100)
    specialty: str = Field(min_length=1, max_length=100)


class Veterinarian(VeterinarianCreate, table=True):
    id: int | None = Field(default=None, primary_key=True)
    appointments: list["Appointment"] = Relationship(back_populates="veterinarian", passive_deletes="all")
    patients: list[Pet] = Relationship(
        back_populates="veterinarians",
        sa_relationship_kwargs={"secondary": "appointment", "viewonly": True},
    )


class AppointmentCreate(InputModel):
    pet_id: int = Field(foreign_key="pet.id", gt=0)
    veterinarian_id: int = Field(foreign_key="veterinarian.id", gt=0)
    starts_at: datetime = Field(sa_type=DateTime)
    reason: str = Field(min_length=1, max_length=500)

    @field_validator("starts_at")
    @classmethod
    def local_time(cls, value):
        if value.tzinfo is not None:
            raise ValueError("Use clinic local time without timezone offset")
        if value.second or value.microsecond:
            raise ValueError("Use minute precision")
        return value


class Appointment(AppointmentCreate, table=True):
    __table_args__ = (
        UniqueConstraint("veterinarian_id", "starts_at"),
        UniqueConstraint("pet_id", "starts_at"),
    )
    id: int | None = Field(default=None, primary_key=True)
    pet: Pet = Relationship(back_populates="appointments")
    veterinarian: Veterinarian = Relationship(back_populates="appointments")


class UpdateInputModel(InputModel):
    @model_validator(mode="before")
    @classmethod
    def reject_explicit_null(cls, value):
        if isinstance(value, dict) and any(item is None for item in value.values()):
            raise ValueError("Fields may be omitted but cannot be null")
        return value


class OwnerUpdate(UpdateInputModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    phone: str | None = Field(default=None, min_length=1, max_length=30)


class PetUpdate(UpdateInputModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    species: str | None = Field(default=None, min_length=1, max_length=60)
    age_years: int | None = Field(default=None, ge=0, le=100)
    owner_id: int | None = Field(default=None, gt=0)


class VeterinarianUpdate(UpdateInputModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    specialty: str | None = Field(default=None, min_length=1, max_length=100)


class AppointmentUpdate(UpdateInputModel):
    pet_id: int | None = Field(default=None, gt=0)
    veterinarian_id: int | None = Field(default=None, gt=0)
    starts_at: datetime | None = None
    reason: str | None = Field(default=None, min_length=1, max_length=500)
