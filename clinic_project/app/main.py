from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers import appointments, patients

app = FastAPI(title="Clinic Automation API", version="0.2.0")

app.include_router(patients.router)
app.include_router(appointments.router)


@app.get("/health/db", tags=["Health"])
def health_db(db: Session = Depends(get_db)):
    return {"database": db.execute(text("SELECT DATABASE()")).scalar()}