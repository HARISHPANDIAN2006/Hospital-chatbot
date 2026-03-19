from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, TypedDict

from transcription import TranscriptSegment

try:
    from pyannote.audio import Pipeline  # type: ignore
except Exception:  # pragma: no cover
    Pipeline = None  # type: ignore


class SpeakerTurn(TypedDict):
    start: float
    end: float
    speaker: str
    text: str


DOCTOR_HINTS = (
    "what are the problems",
    "any other symptoms",
    "do you have",
    "please lie on that bed",
    "does it hurt",
    "i am prescribing",
    "i am writing down some tests",
    "take it",
    "after dinner",
    "nothing to worry",
    "come back immediately",
    "doctor",
)

PATIENT_HINTS = (
    "i have",
    "i am ",
    "it hurts",
    "thank you doctor",
    "is it something serious",
    "i took",
    "i had",
    "okay doctor",
    "please doctor",
)


def _overlap(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    return max(0.0, min(a_end, b_end) - max(a_start, b_start))


def _normalize_speakers(turns: List[SpeakerTurn]) -> Dict[str, str]:
    counts = Counter(turn["speaker"] for turn in turns if turn["speaker"] != "UNKNOWN")
    most_common = [speaker for speaker, _ in counts.most_common()]
    speaker_map: Dict[str, str] = {}
    if most_common:
        speaker_map[most_common[0]] = "Doctor"
    if len(most_common) > 1:
        speaker_map[most_common[1]] = "Patient"
    return speaker_map


def _heuristic_label(text: str) -> str:
    t = text.lower()
    doctor_score = sum(1 for k in DOCTOR_HINTS if k in t)
    patient_score = sum(1 for k in PATIENT_HINTS if k in t)
    if doctor_score > patient_score:
        return "Doctor"
    if patient_score > doctor_score:
        return "Patient"
    return "Patient" if "?" not in t else "Doctor"


def _fallback_turns(transcript_segments: List[TranscriptSegment]) -> List[SpeakerTurn]:
    return [
        {
            "start": segment["start"],
            "end": segment["end"],
            "speaker": _heuristic_label(segment["text"]),
            "text": segment["text"],
        }
        for segment in transcript_segments
    ]


def diarize_transcript(
    audio_path: Path,
    transcript_segments: List[TranscriptSegment],
    hf_auth_token: Optional[str] = None,
) -> List[SpeakerTurn]:
    if not transcript_segments:
        return []

    if Pipeline is None or not hf_auth_token:
        return _fallback_turns(transcript_segments)

    try:
        # Support both older and newer pyannote signatures.
        if hf_auth_token:
            try:
                pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1", token=hf_auth_token
                )
            except TypeError:
                pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1", use_auth_token=hf_auth_token
                )
        else:
            pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1")
        diarization = pipeline(str(audio_path))
    except Exception:
        # Never block the consultation pipeline if diarization fails.
        return _fallback_turns(transcript_segments)

    raw_turns: List[SpeakerTurn] = []
    diarization_tracks = list(diarization.itertracks(yield_label=True))

    for segment in transcript_segments:
        seg_start = segment["start"]
        seg_end = segment["end"]

        best_speaker = "UNKNOWN"
        best_score = 0.0
        for turn, _, speaker in diarization_tracks:
            score = _overlap(seg_start, seg_end, float(turn.start), float(turn.end))
            if score > best_score:
                best_score = score
                best_speaker = str(speaker)

        raw_turns.append(
            {
                "start": seg_start,
                "end": seg_end,
                "speaker": best_speaker,
                "text": segment["text"],
            }
        )

    speaker_map = _normalize_speakers(raw_turns)
    normalized: List[SpeakerTurn] = []
    for turn in raw_turns:
        normalized.append(
            {
                "start": turn["start"],
                "end": turn["end"],
                "speaker": speaker_map.get(
                    turn["speaker"], _heuristic_label(turn["text"])
                ),
                "text": turn["text"],
            }
        )
    return normalized


def conversation_text(turns: List[SpeakerTurn]) -> str:
    lines = [f"{turn['speaker']}: {turn['text']}" for turn in turns]
    return "\n".join(lines)
