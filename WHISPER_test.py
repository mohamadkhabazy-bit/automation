import os

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
from pathlib import Path
from faster_whisper import WhisperModel
import ctranslate2
import time

# مسیر مدل محلی
MODEL_PATH = Path(
    r"E:\whisper_models\models--Systran--faster-whisper-small"
    r"\snapshots\536b0662742c02347bc0e980a01041f333bce120"
)

# مسیر فایل صوتی
AUDIO_PATH = Path(
    r"C:\Users\RAYANSTAR\Downloads\audio_2026-11-05_17-43-57.ogg"
)

# بررسی مسیرها
if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Model not found: {MODEL_PATH}")

if not AUDIO_PATH.exists():
    raise FileNotFoundError(f"Audio not found: {AUDIO_PATH}")

# بررسی شناسایی GPU توسط CTranslate2
gpu_count = ctranslate2.get_cuda_device_count()

print("CUDA GPU count:", gpu_count, flush=True)

if gpu_count == 0:
    raise RuntimeError(
        "CTranslate2 cannot detect a CUDA GPU. "
        "CUDA/cuDNN libraries may not be configured."
    )

# بارگذاری مدل روی کارت گرافیک
print("\nLoading Whisper model on GPU...", flush=True)

load_start = time.time()

model = WhisperModel(
    str(MODEL_PATH),
    device="cpu",
    compute_type="int8",
    local_files_only=True
)

print(
    f"Model loaded in {time.time() - load_start:.2f} seconds",
    flush=True
)

# Transcription
print("\nTranscribing audio on GPU...", flush=True)

transcribe_start = time.time()

segments, info = model.transcribe(
    str(AUDIO_PATH),
    language="fa",
    beam_size=5,
    best_of=5,
    temperature=0,
    vad_filter=False,
    condition_on_previous_text=False,
    initial_prompt=(
        "متن شامل دیکته پزشکی فارسی است. "
        "نام داروها، اصطلاحات پزشکی، مقدار داروها، "
        "دوز و دستور مصرف دارو را با دقت تشخیص بده."
    )
)

transcription = []

for segment in segments:
    text = segment.text.strip()

    if text:
        transcription.append(text)
        print(
            f"[{segment.start:.2f}s - {segment.end:.2f}s] {text}",
            flush=True
        )

full_text = " ".join(transcription)

print("\n========== RESULT ==========")
print("Detected language:", info.language)
print("Language probability:", info.language_probability)
print("Audio duration:", info.duration)
print(
    "Transcription time:",
    round(time.time() - transcribe_start, 2),
    "seconds"
)

print("\nFull transcription:")
print(full_text)