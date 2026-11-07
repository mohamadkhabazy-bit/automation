from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AppointmentStatus
from app.schemas import AppointmentCreate, AppointmentOut, AppointmentStatusUpdate
from app.services import appointments as service

router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.post("", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
def create_appointment(data: AppointmentCreate, db: Session = Depends(get_db)):
    try:
        return service.create_appointment(
            db,
            patient_id=data.patient_id,
            created_by=data.created_by,
            appointment_date=data.appointment_date,
        )
    except service.AppointmentError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[AppointmentOut])
def list_appointments(
    status_filter: Optional[AppointmentStatus] = Query(None, alias="status"),
    patient_id: Optional[int] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return service.list_appointments(
        db, status=status_filter, patient_id=patient_id, limit=limit, offset=offset
    )


@router.get("/{appointment_id}", response_model=AppointmentOut)
def get_appointment(appointment_id: int, db: Session = Depends(get_db)):
    appointment = service.get_appointment(db, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found.")
    return appointment


@router.patch("/{appointment_id}/status", response_model=AppointmentOut)
def change_status(appointment_id: int, data: AppointmentStatusUpdate,
                  db: Session = Depends(get_db)):
    try:
        return service.change_appointment_status(db, appointment_id, data.status)
    except service.AppointmentError as e:
        code = 404 if "not found" in str(e).lower() else 400
        raise HTTPException(status_code=code, detail=str(e))