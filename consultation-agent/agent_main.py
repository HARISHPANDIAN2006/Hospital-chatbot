from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Optional

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from diarization import conversation_text, diarize_transcript
from email_sender import send_prescription_email
from mcp_client import MCPClient
from pdf_generator import generate_prescription_pdf
from prescription_extractor import ConsultationExtraction, extract_consultation_insights
from transcription import transcribe_audio

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "audio_samples"
OUTPUT_DIR = BASE_DIR / "generated_prescriptions"

DEFAULT_APPOINTMENT_AUDIO_MAP = {
    "A102": "consultation_1.wav",
    "A103": "consultation_2.wav",
}


def _load_json_map(env_name: str) -> Dict[str, str]:
    raw = os.getenv(env_name, "").strip()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{env_name} is not valid JSON.") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{env_name} must be a JSON object.")
    return {str(k): str(v) for k, v in data.items()}


def _load_appointment_audio_map() -> Dict[str, str]:
    custom = _load_json_map("APPOINTMENT_AUDIO_MAP_JSON")
    mapping = dict(DEFAULT_APPOINTMENT_AUDIO_MAP)
    mapping.update(custom)
    return mapping


def _load_appointment_db_id_map() -> Dict[str, str]:
    return _load_json_map("APPOINTMENT_DB_ID_MAP_JSON")


def _resolve_audio_path(
    appointment_id: str,
    explicit_audio_filename: Optional[str],
    audio_map: Dict[str, str],
) -> Optional[Path]:
    if explicit_audio_filename:
        path = AUDIO_DIR / explicit_audio_filename
        return path if path.exists() else None

    mapped = audio_map.get(appointment_id)
    if mapped:
        path = AUDIO_DIR / mapped
        if path.exists():
            return path

    # Auto fallback so manual map is not required for common naming conventions.
    candidates = []
    for ext in ("wav", "mp3", "m4a", "flac"):
        candidates.append(AUDIO_DIR / f"consultation_{appointment_id}.{ext}")
        candidates.append(AUDIO_DIR / f"{appointment_id}.{ext}")

    for path in candidates:
        if path.exists():
            return path

    return None


class ProcessConsultationRequest(BaseModel):
    appointment_id: str = Field(..., min_length=1)
    send_email: bool = True
    audio_filename: Optional[str] = None
    db_appointment_id: Optional[str] = None


class ProcessConsultationResponse(BaseModel):
    success: bool
    appointment_id: str
    patient_name: str
    patient_email: str
    doctor_name: str
    transcript_text: str
    conversation: str
    extraction: ConsultationExtraction
    pdf_path: str
    email_sent: bool


app = FastAPI(title="Consultation AI Agent", version="1.0.0")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "consultation-agent"}


@app.post("/consultation/process", response_model=ProcessConsultationResponse)
async def process_consultation(payload: ProcessConsultationRequest):
    appointment_id = payload.appointment_id.strip()
    audio_map = _load_appointment_audio_map()
    db_id_map = _load_appointment_db_id_map()

    audio_path = _resolve_audio_path(
        appointment_id=appointment_id,
        explicit_audio_filename=payload.audio_filename,
        audio_map=audio_map,
    )
    if not audio_path:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Audio file not found for appointment_id {appointment_id}. "
                "Provide audio_filename in request or configure APPOINTMENT_AUDIO_MAP_JSON."
            ),
        )

    mongodb_uri = os.getenv("MONGODB_URI", "")
    db_name = os.getenv("DB_NAME", "hospital_db")
    mcp_base_url = os.getenv("MCP_BASE_URL", "http://localhost:3333")
    google_api_key = os.getenv("GOOGLE_API_KEY", "")
    whisper_model = os.getenv("WHISPER_MODEL", "base")
    hf_auth_token = os.getenv("PYANNOTE_AUTH_TOKEN", "").strip() or None

    smtp_host = os.getenv("SMTP_HOST", "")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    sender_email = os.getenv("EMAIL_FROM", smtp_username)
    use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

    if not mongodb_uri:
        raise HTTPException(status_code=500, detail="MONGODB_URI is not configured.")

    print(f"Processing consultation for appointment {appointment_id}...")
    print("Transcribing audio...")
    transcript = await run_in_threadpool(transcribe_audio, audio_path, whisper_model)

    print("Separating speakers...")
    turns = await run_in_threadpool(
        diarize_transcript, audio_path, transcript["segments"], hf_auth_token
    )
    conversation = conversation_text(turns)

    print(conversation or transcript["full_text"])
    print("Extracting prescription...")
    extraction = await run_in_threadpool(
        extract_consultation_insights,
        conversation or transcript["full_text"],
        google_api_key,
    )

    print("Retrieving patient details from MCP server...")
    mcp_client = MCPClient(
        mongodb_uri=mongodb_uri, db_name=db_name, mcp_base_url=mcp_base_url
    )
    try:
        appointment_ctx = await mcp_client.get_appointment_context(
            appointment_id=appointment_id,
            db_appointment_id=payload.db_appointment_id or db_id_map.get(appointment_id),
        )
    finally:
        await mcp_client.close()

    print("Generating prescription PDF...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = OUTPUT_DIR / f"prescription_{appointment_id}.pdf"
    await run_in_threadpool(generate_prescription_pdf, pdf_path, appointment_ctx, extraction)

    email_sent = False
    if payload.send_email:
        if not smtp_host:
            raise HTTPException(status_code=500, detail="SMTP_HOST is not configured for email delivery.")
        if not appointment_ctx.patient_email:
            raise HTTPException(
                status_code=400,
                detail=f"Patient email is missing for patient_id {appointment_ctx.patient_id}. "
                "Use send_email=false or update patient email in database.",
            )
        print("Sending email to patient...")
        await run_in_threadpool(
            send_prescription_email,
            smtp_host,
            smtp_port,
            smtp_username,
            smtp_password,
            sender_email,
            appointment_ctx.patient_email,
            appointment_ctx.patient_name,
            appointment_ctx.doctor_name,
            appointment_id,
            pdf_path,
            use_tls,
        )
        email_sent = True

    return ProcessConsultationResponse(
        success=True,
        appointment_id=appointment_id,
        patient_name=appointment_ctx.patient_name,
        patient_email=appointment_ctx.patient_email,
        doctor_name=appointment_ctx.doctor_name,
        transcript_text=transcript["full_text"],
        conversation=conversation,
        extraction=extraction,
        pdf_path=str(pdf_path),
        email_sent=email_sent,
    )


if __name__ == "__main__":
    uvicorn.run("agent_main:app", host="0.0.0.0", port=8001, reload=False)
