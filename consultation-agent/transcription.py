from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List, TypedDict

import whisper


class TranscriptSegment(TypedDict):
    start: float
    end: float
    text: str


class TranscriptResult(TypedDict):
    full_text: str
    segments: List[TranscriptSegment]


@lru_cache(maxsize=4)
def _load_model(model_name: str):
    return whisper.load_model(model_name)


def transcribe_audio(audio_path: Path, model_name: str = "base") -> TranscriptResult:
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    model = _load_model(model_name)
    result = model.transcribe(str(audio_path), fp16=False)

    segments: List[TranscriptSegment] = []
    for segment in result.get("segments", []):
        text = str(segment.get("text", "")).strip()
        if not text:
            continue
        segments.append(
            {
                "start": float(segment.get("start", 0.0)),
                "end": float(segment.get("end", 0.0)),
                "text": text,
            }
        )

    return {"full_text": str(result.get("text", "")).strip(), "segments": segments}
