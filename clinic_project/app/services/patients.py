import re
from datetime import date
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import Patient


class PatientError(Exception):
    pass


def is_valid_national_code(code: str) -> bool:
    """Validate Iranian national code (10 digits + checksum)."""
    if not re.fullmatch(r"\d{10}", code):
        return False
    if len(set(code)) == 1:
        return False
    digits = [int(c) for c in code]
    s = sum(digits[i] * (10 - i) for i in range(9))
    r = s % 11
    check = r if r < 2 else 11 - r
    return check == digits[9]


def get_patient_by_national_code(db, national_code: str) -> Optional[Patient]:
    return db.scalar(select(Patient).where(Patient.national_code == national_code))


def create_patient(db, national_code: str, first_name: str, last_name: str,
                   phone_number: Optional[str] = None,
                   birth_date: Optional[date] = None) -> Patient:
    national_code = national_code.strip()
    if not is_valid_national_code(national_code):
        raise PatientError("Invalid national code.")
    if get_patient_by_national_code(db, national_code):
        raise PatientError("A patient with this national code already exists.")
    if not first_name.strip() or not last_name.strip():
        raise PatientError("First name and last name are required.")

    patient = Patient(
        national_code=national_code,
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        phone_number=phone_number,
        birth_date=birth_date,
    )
    db.add(patient)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise PatientError("Could not save patient (duplicate or invalid data).")
    except Exception:
        db.rollback()
        raise PatientError("Could not save patient.")
    db.refresh(patient)
    return patient


def _clean_required(value: Optional[str], field_name: str) -> str:
    if value is None or not value.strip():
        raise PatientError(f"{field_name} cannot be empty.")
    return value.strip()


def update_patient(db, patient_id: int, **fields) -> Patient:
    allowed = {"first_name", "last_name", "phone_number", "birth_date"}
    patient = db.get(Patient, patient_id)
    if not patient:
        raise PatientError("Patient not found.")

    cleaned = {}
    for key, value in fields.items():
        if key not in allowed:
            raise PatientError(f"Field '{key}' cannot be updated.")
        if key in {"first_name", "last_name"}:
            value = _clean_required(value, key)
        cleaned[key] = value

    for key, value in cleaned.items():
        setattr(patient, key, value)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise PatientError("Could not update patient.")
    db.refresh(patient)
    return patient


def list_patients(db, limit: int = 50, offset: int = 0):
    return db.scalars(
        select(Patient).order_by(Patient.patient_id).limit(limit).offset(offset)
    ).all()