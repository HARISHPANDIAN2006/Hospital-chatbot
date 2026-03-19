# Consultation AI Agent

This module processes recorded doctor-patient consultation audio and automatically:

1. Transcribes speech to text (Whisper)
2. Performs speaker diarization (pyannote)
3. Extracts prescription and advice (Gemini)
4. Retrieves patient/doctor details using `appointment_id` from MongoDB
5. Generates a prescription PDF (reportlab)
6. Sends the PDF to the patient by email (SMTP)

## Folder structure

```
consultation-agent/
├── audio_samples/
├── agent_main.py
├── transcription.py
├── diarization.py
├── prescription_extractor.py
├── pdf_generator.py
├── email_sender.py
├── mcp_client.py
├── requirements.txt
└── .env.example
```

## Setup

1. Create a virtual environment and install dependencies:

```bash
pip install -r consultation-agent/requirements.txt
```

2. Copy `.env.example` to `.env` and update values.

3. Place demo audio files in:

`consultation-agent/audio_samples/`

Example:
- `consultation_1.wav`
- `consultation_2.wav`

4. Configure mappings:
- `APPOINTMENT_AUDIO_MAP_JSON` maps appointment id to audio filename.
- `APPOINTMENT_DB_ID_MAP_JSON` maps appointment id to MongoDB appointment `_id` when needed.

Note: mappings are now optional if you provide values in API request:
- `audio_filename` to directly select the consultation audio file
- `db_appointment_id` when `appointment_id` is a human code (for example `A102`)

## Run

```bash
python consultation-agent/agent_main.py
```

Service starts on `http://localhost:8001`.

## API

### Health

`GET /health`

### Process consultation

`POST /consultation/process`

Request body:

```json
{
  "appointment_id": "A102",
  "send_email": true,
  "audio_filename": "consultation_1.mp3",
  "db_appointment_id": "69523f5aa9e439af2d10ef6c"
}
```

If `audio_filename` is omitted, the agent tries:
1. `APPOINTMENT_AUDIO_MAP_JSON`
2. `audio_samples/consultation_<appointment_id>.(wav|mp3|m4a|flac)`
3. `audio_samples/<appointment_id>.(wav|mp3|m4a|flac)`

Successful response includes transcript, extracted medications/advice, output PDF path, and email status.
