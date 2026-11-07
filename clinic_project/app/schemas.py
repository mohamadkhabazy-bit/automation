from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models import AppointmentStatus


# ---------- Patients ----------
class PatientCreate(BaseModel):
    national_code: str = Field(min_length=10, max_length=10)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone_number: Optional[str] = Field(default=None, max_length=20)
    birth_date: Optional[date] = None


class PatientUpdate(BaseModel):
    first_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    phone_number: Optional[str] = Field(default=None, max_length=20)
    birth_date: Optional[date] = None


class PatientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    patient_id: int
    national_code: str
    first_name: str
    last_name: str
    phone_number: Optional[str]
    birth_date: Optional[date]
    created_at: datetime


# ---------- Appointments ----------
class AppointmentCreate(BaseModel):
    patient_id: int
    created_by: int  # TEMPORARY: will come from the login token later
    appointment_date: Optional[datetime] = None


class AppointmentStatusUpdate(BaseModel):
    status: AppointmentStatus


class AppointmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    appointment_id: int
    patient_id: int
    created_by: int
    appointment_date: datetime
    status: AppointmentStatus
    created_at: datetime