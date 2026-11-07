import os

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Type

import requests
from sqlalchemy.orm import Session

from app.models import AudioFile, AudioProcessingStatus
from app.services.audio import get_audio_full_path


class TranscriptionError(Exception):
    pass


# ---------- Provider interface ----------
class TranscriptionProvider(ABC):
    @abstractmethod
    def transcribe(self, path: Path) -> str:
        """Audio file path -> plain text."""


# ---------- OpenAI provider ----------
class OpenAIProvider(TranscriptionProvider):
    URL = "https://api.openai.com/v1/audio/transcriptions"

    def transcribe(self, path: Path) -> str:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise TranscriptionError("OPENAI_API_KEY is not set in .env")
        try:
            with path.open("rb") as f:
                response = requests.post(
                    self.URL,
                    headers={"Authorization": f"Bearer {api_key}"},
                    files={"file": (path.name, f)},
                    data={
                        "model": os.getenv("OPENAI_TRANSCRIBE_MODEL", "whisper-1"),
                        "language": "fa",
                        "response_format": "json",
                        "temperature": "0",
                    },
                    timeout=180,
                )
        except requests.RequestException as exc:
            raise TranscriptionError(f"Network error: {type(exc).__name__}")
        if response.status_code != 200:
            raise TranscriptionError(f"OpenAI returned HTTP {response.status_code}")
        return response.json().get("text", "").strip()


# Generic domain hint: tells the model these are Persian medical dictations.
# Keep it short and free of specific drug names to avoid biasing the output.
MEDICAL_PROMPT = (
    "این یک ویس پزشکی به زبان فارسی است. پزشک تشخیص، داروها، "
    "دوز، تعداد دفعات و مدت مصرف و توصیه‌ها را بیان می‌کند."
)


class LocalWhisperProvider(TranscriptionProvider):
    _model = None  # loaded once, reused

    def _get_model(self):
        if LocalWhisperProvider._model is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError:
                raise TranscriptionError("faster-whisper is not installed.")
            LocalWhisperProvider._model = WhisperModel(
                os.getenv("LOCAL_WHISPER_MODEL", "small"),
                device=os.getenv("LOCAL_WHISPER_DEVICE", "cpu"),
                compute_type=os.getenv("LOCAL_WHISPER_COMPUTE_TYPE", "int8"),
                download_root=os.getenv("LOCAL_WHISPER_CACHE_DIR") or None,
            )
        return LocalWhisperProvider._model

    def transcribe(self, path: Path) -> str:
        try:
            model = self._get_model()
            segments, _info = model.transcribe(
                str(path),
                language="fa",
                beam_size=5,
                vad_filter=True,
                temperature=0.0,
                initial_prompt=MEDICAL_PROMPT,
            )
            return " ".join(seg.text.strip() for seg in segments).strip()
        except TranscriptionError:
            raise
        except Exception as exc:
            raise TranscriptionError(f"Local transcription failed: {type(exc).__name__}")

# ---------- Registry: new provider = one class + one line ----------
PROVIDERS: Dict[str, Type[TranscriptionProvider]] = {
    "openai": OpenAIProvider,
    "local": LocalWhisperProvider,
}


def transcribe(path: Path) -> str:
    """Provider-agnostic entry point used by the rest of the app."""
    name = os.getenv("TRANSCRIPTION_PROVIDER", "local").lower()
    provider_cls = PROVIDERS.get(name)
    if provider_cls is None:
        raise TranscriptionError(f"Unknown provider: {name}")
    return provider_cls().transcribe(path)


# ---------- DB workflow (independent of the provider) ----------
def transcribe_audio(db: Session, audio_id: int) -> AudioFile:
    audio = db.get(AudioFile, audio_id)
    if not audio:
        raise TranscriptionError("Audio file not found.")
    if audio.processing_status == AudioProcessingStatus.transcribing:
        raise TranscriptionError("Audio is already being transcribed.")

    path = get_audio_full_path(audio)
    if not path.exists():
        raise TranscriptionError("Audio file is missing on disk.")

    audio.processing_status = AudioProcessingStatus.transcribing
    db.commit()

    try:
        text = transcribe(path)
        if not text:
            raise TranscriptionError("Transcription result is empty.")
    except Exception as exc:
        db.rollback()
        audio = db.get(AudioFile, audio_id)
        audio.processing_status = AudioProcessingStatus.failed
        db.commit()
        if isinstance(exc, TranscriptionError):
            raise
        raise TranscriptionError(f"Unexpected error: {type(exc).__name__}")

    audio.transcription = text
    audio.processing_status = AudioProcessingStatus.transcribed
    db.commit()
    db.refresh(audio)
    return audio