from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import PatientCreate, PatientOut, PatientUpdate
from app.services import patients as service

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.post("", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
def create_patient(data: PatientCreate, db: Session = Depends(get_db)):
    try:
        return service.create_patient(db, **data.model_dump())
    except service.PatientError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[PatientOut])
def list_patients(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return service.list_patients(db, limit=limit, offset=offset)


@router.get("/{national_code}", response_model=PatientOut)
def get_patient(national_code: str, db: Session = Depends(get_db)):
    patient = service.get_patient_by_national_code(db, national_code.strip())
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")
    return patient


@router.put("/{patient_id}", response_model=PatientOut)
def update_patient(patient_id: int, data: PatientUpdate, db: Session = Depends(get_db)):
    fields = data.model_dump(exclude_unset=True)
    try:
        return service.update_patient(db, patient_id, **fields)
    except service.PatientError as e:
        code = 404 if "not found" in str(e).lower() else 400
        raise HTTPException(status_code=code, detail=str(e))