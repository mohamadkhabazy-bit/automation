import uuid
from pathlib import Path

from sqlalchemy import select

from app.database import BASE_DIR
from app.models import (
    Appointment, AppointmentStatus, AudioFile, AudioProcessingStatus,
)

STORAGE_DIR = BASE_DIR / "storage"
AUDIO_DIR = STORAGE_DIR / "audio"
DOCUMENTS_DIR = STORAGE_DIR / "documents"

AUDIO_DIR.mkdir(parents=True, exist_ok=True)
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".ogg", ".webm"}
MAX_AUDIO_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB


class AudioError(Exception):
    pass


def save_audio_file(db, appointment_id: int, original_filename: str,
                    file_bytes: bytes) -> AudioFile:
    appointment = db.get(Appointment, appointment_id)
    if not appointment:
        raise AudioError("Appointment not found.")
    if appointment.status != AppointmentStatus.in_progress:
        raise AudioError("Audio can only be added to an in-progress appointment.")

    extension = Path(original_filename).suffix.lower()
    if extension not in ALLOWED_AUDIO_EXTENSIONS:
        raise AudioError(f"Unsupported audio format: '{extension}'.")
    if not file_bytes:
        raise AudioError("Audio file is empty.")
    if len(file_bytes) > MAX_AUDIO_SIZE_BYTES:
        raise AudioError("Audio file is too large (max 50 MB).")

    stored_name = f"{uuid.uuid4().hex}{extension}"
    full_path = AUDIO_DIR / stored_name
    relative_path = f"audio/{stored_name}"

    full_path.write_bytes(file_bytes)

    audio = AudioFile(
        appointment_id=appointment_id,
        file_path=relative_path,
        processing_status=AudioProcessingStatus.uploaded,
    )
    db.add(audio)
    try:
        db.commit()
    except Exception:
        db.rollback()
        full_path.unlink(missing_ok=True)
        raise AudioError("Could not save audio record.")
    db.refresh(audio)
    return audio


def get_audio_full_path(audio: AudioFile) -> Path:
    full_path = (STORAGE_DIR / audio.file_path).resolve()
    if STORAGE_DIR.resolve() not in full_path.parents:
        raise AudioError("Invalid audio path.")
    return full_path


def list_audio_files(db, appointment_id: int):
    return db.scalars(
        select(AudioFile)
        .where(AudioFile.appointment_id == appointment_id)
        .order_by(AudioFile.created_at)
    ).all()