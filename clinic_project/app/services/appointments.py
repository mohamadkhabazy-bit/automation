from datetime import datetime
from typing import List, Optional

from sqlalchemy import select

from app.models import Appointment, AppointmentStatus, Patient, User, UserRole


class AppointmentError(Exception):
    pass


ALLOWED_TRANSITIONS = {
    AppointmentStatus.created: {AppointmentStatus.in_progress, AppointmentStatus.cancelled},
    AppointmentStatus.in_progress: {AppointmentStatus.completed, AppointmentStatus.cancelled},
    AppointmentStatus.completed: set(),
    AppointmentStatus.cancelled: set(),
}


def create_appointment(db, patient_id: int, created_by: int,
                       appointment_date: Optional[datetime] = None) -> Appointment:
    patient = db.get(Patient, patient_id)
    if not patient:
        raise AppointmentError("Patient not found.")

    user = db.get(User, created_by)
    if not user or not user.is_active:
        raise AppointmentError("Creator user not found or inactive.")
    if user.role not in (UserRole.secretary, UserRole.admin):
        raise AppointmentError("Only secretary or admin can create appointments.")

    appointment = Appointment(
        patient_id=patient_id,
        created_by=created_by,
        appointment_date=appointment_date or datetime.now(),
        status=AppointmentStatus.created,
    )
    db.add(appointment)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise AppointmentError("Could not create appointment.")
    db.refresh(appointment)
    return appointment


def get_appointment(db, appointment_id: int) -> Optional[Appointment]:
    return db.get(Appointment, appointment_id)


def list_appointments(db, status: Optional[AppointmentStatus] = None,
                      patient_id: Optional[int] = None,
                      limit: int = 50, offset: int = 0) -> List[Appointment]:
    stmt = select(Appointment)
    if status is not None:
        stmt = stmt.where(Appointment.status == status)
    if patient_id is not None:
        stmt = stmt.where(Appointment.patient_id == patient_id)
    stmt = stmt.order_by(Appointment.appointment_date.desc()).limit(limit).offset(offset)
    return db.scalars(stmt).all()


def change_appointment_status(db, appointment_id: int,
                              new_status: AppointmentStatus) -> Appointment:
    appointment = db.get(Appointment, appointment_id)
    if not appointment:
        raise AppointmentError("Appointment not found.")

    if new_status not in ALLOWED_TRANSITIONS[appointment.status]:
        raise AppointmentError(
            f"Cannot change status from '{appointment.status.value}' to '{new_status.value}'."
        )

    appointment.status = new_status
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise AppointmentError("Could not update appointment status.")
    db.refresh(appointment)
    return appointment