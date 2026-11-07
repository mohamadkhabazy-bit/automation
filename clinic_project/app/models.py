import enum
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import (
    JSON, BigInteger, Boolean, CHAR, Date, DateTime, Enum as SAEnum,
    ForeignKey, String, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# ---------- Enums (values must match MySQL exactly) ----------
class UserRole(str, enum.Enum):
    secretary = "secretary"
    doctor = "doctor"
    admin = "admin"


class AppointmentStatus(str, enum.Enum):
    created = "created"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class AudioProcessingStatus(str, enum.Enum):
    uploaded = "uploaded"
    transcribing = "transcribing"
    transcribed = "transcribed"
    failed = "failed"


class RecordStatus(str, enum.Enum):
    draft = "draft"
    pending_review = "pending_review"
    approved = "approved"


class DocumentType(str, enum.Enum):
    medical_report = "medical_report"
    prescription = "prescription"
    other = "other"


class PrintStatus(str, enum.Enum):
    generated = "generated"
    printed = "printed"
    failed = "failed"


def pg_enum(enum_cls):
    # store the enum *values* (not names) as MySQL expects
    return SAEnum(enum_cls, values_callable=lambda e: [m.value for m in e], native_enum=True)


# ---------- Models ----------
class Patient(Base):
    __tablename__ = "patients"

    patient_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    national_code: Mapped[str] = mapped_column(CHAR(10), unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20))
    birth_date: Mapped[Optional[date]] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    appointments: Mapped[List["Appointment"]] = relationship(back_populates="patient")


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(pg_enum(UserRole), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="1", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    appointments_created: Mapped[List["Appointment"]] = relationship(back_populates="creator")
    approved_records: Mapped[List["MedicalRecord"]] = relationship(back_populates="approver")


class Appointment(Base):
    __tablename__ = "appointments"

    appointment_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("patients.patient_id"), nullable=False)
    created_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    appointment_date: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    status: Mapped[AppointmentStatus] = mapped_column(
        pg_enum(AppointmentStatus), server_default="created", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    patient: Mapped["Patient"] = relationship(back_populates="appointments")
    creator: Mapped["User"] = relationship(back_populates="appointments_created")
    audio_files: Mapped[List["AudioFile"]] = relationship(back_populates="appointment")
    medical_record: Mapped[Optional["MedicalRecord"]] = relationship(
        back_populates="appointment", uselist=False
    )


class AudioFile(Base):
    __tablename__ = "audio_files"

    audio_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    appointment_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("appointments.appointment_id"), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    transcription: Mapped[Optional[str]] = mapped_column(Text().with_variant(Text(4294967295), "mysql"))
    processing_status: Mapped[AudioProcessingStatus] = mapped_column(
        pg_enum(AudioProcessingStatus), server_default="uploaded", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    appointment: Mapped["Appointment"] = relationship(back_populates="audio_files")


class MedicalRecord(Base):
    __tablename__ = "medical_records"

    record_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    appointment_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("appointments.appointment_id"), unique=True, nullable=False
    )
    approved_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.user_id"))
    diagnosis: Mapped[Optional[str]] = mapped_column(Text)
    instructions: Mapped[Optional[str]] = mapped_column(Text)
    extraction_json: Mapped[Optional[dict]] = mapped_column(JSON)
    status: Mapped[RecordStatus] = mapped_column(pg_enum(RecordStatus), server_default="draft", nullable=False)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    appointment: Mapped["Appointment"] = relationship(back_populates="medical_record")
    approver: Mapped[Optional["User"]] = relationship(back_populates="approved_records")
    medications: Mapped[List["Medication"]] = relationship(back_populates="record")
    documents: Mapped[List["Document"]] = relationship(back_populates="record")


class Medication(Base):
    __tablename__ = "medications"

    medication_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    record_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("medical_records.record_id"), nullable=False)
    drug_name: Mapped[str] = mapped_column(String(200), nullable=False)
    dosage: Mapped[Optional[str]] = mapped_column(String(100))
    frequency: Mapped[Optional[str]] = mapped_column(String(100))
    duration: Mapped[Optional[str]] = mapped_column(String(100))
    instructions: Mapped[Optional[str]] = mapped_column(Text)

    record: Mapped["MedicalRecord"] = relationship(back_populates="medications")


class Document(Base):
    __tablename__ = "documents"

    document_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    record_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("medical_records.record_id"), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    document_type: Mapped[DocumentType] = mapped_column(
        pg_enum(DocumentType), server_default="medical_report", nullable=False
    )
    print_status: Mapped[PrintStatus] = mapped_column(
        pg_enum(PrintStatus), server_default="generated", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    record: Mapped["MedicalRecord"] = relationship(back_populates="documents")