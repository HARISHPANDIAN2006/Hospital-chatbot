from __future__ import annotations

import json
import re
from typing import List

from pydantic import BaseModel, Field
from langchain_ollama import OllamaLLM


class Medication(BaseModel):
    medicine_name: str = Field(default="")
    dosage: str = Field(default="")
    frequency: str = Field(default="")
    duration: str = Field(default="")
    instructions: str = Field(default="")


class ConsultationExtraction(BaseModel):
    patient_symptoms: List[str] = Field(default_factory=list)
    doctor_prescription_summary: str = Field(default="")
    medications: List[Medication] = Field(default_factory=list)
    additional_advice: List[str] = Field(default_factory=list)


def _extract_json_block(text: str) -> str:
    """Extract JSON from response text"""
    fenced = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        return fenced.group(1)
    bare = re.search(r"(\{.*\})", text, re.DOTALL)
    if bare:
        return bare.group(1)
    raise ValueError("Ollama response did not contain JSON.")


def _rule_based_fallback(transcript: str) -> ConsultationExtraction:
    """Fallback extraction using regex rules when Ollama is unavailable"""
    t = transcript.lower()
    symptoms = []
    for key in [
        "fever",
        "cough",
        "headache",
        "stomach ache",
        "vomiting",
        "nausea",
        "pain",
        "dizziness",
    ]:
        if key in t:
            symptoms.append(key)

    meds: List[Medication] = []
    med_patterns = [
        r"(paracetamol)\s*([0-9]+mg)?",
        r"(ibuprofen)\s*([0-9]+mg)?",
        r"(amoxicillin)\s*([0-9]+mg)?",
        r"(omeprazole)\s*([0-9]+mg)?",
        r"(anticid|antacid)\s*([0-9]+mg)?",
    ]
    for pattern in med_patterns:
        m = re.search(pattern, t)
        if m:
            meds.append(
                Medication(
                    medicine_name=(m.group(1) or "").title(),
                    dosage=(m.group(2) or "").upper(),
                    frequency="",
                    duration="",
                    instructions="",
                )
            )

    summary = "Prescription extracted using fallback rules because Ollama extraction was unavailable."
    advice = []
    if "test" in t or "report" in t:
        advice.append("Complete advised tests and follow up with reports.")
    if "after dinner" in t:
        advice.append("Take medication after dinner.")

    return ConsultationExtraction(
        patient_symptoms=sorted(set(symptoms)),
        doctor_prescription_summary=summary,
        medications=meds,
        additional_advice=advice,
    )


def extract_consultation_insights(
    transcript: str, 
    ollama_model: str = "qwen2.5:3b"
) -> ConsultationExtraction:
    """
    Extract prescription data from consultation transcript using Ollama.
    
    Args:
        transcript: Doctor-patient conversation text
        ollama_model: Ollama model to use (default: qwen2.5:3b)
    
    Returns:
        ConsultationExtraction with structured prescription data
    """
    try:
        llm = OllamaLLM(model=ollama_model)
    except Exception as e:
        print(f"Failed to initialize Ollama: {e}")
        return _rule_based_fallback(transcript)

    prompt = f"""You are a clinical documentation assistant.
Extract only information that is explicitly present in the transcript.
Return STRICT JSON with this schema:
{{
  "patient_symptoms": ["symptom1", "symptom2"],
  "doctor_prescription_summary": "brief summary of diagnosis and prescription",
  "medications": [
    {{
      "medicine_name": "medication name",
      "dosage": "dosage (e.g., 500mg)",
      "frequency": "frequency (e.g., twice daily, after meals)",
      "duration": "duration (e.g., 7 days, 2 weeks)",
      "instructions": "special instructions (e.g., take after food)"
    }}
  ],
  "additional_advice": ["advice1", "advice2"]
}}

If a field is unknown, keep it empty string or empty array.
Return ONLY the JSON object, no other text.

Transcript:
{transcript}
"""

    try:
        response = llm.invoke(prompt)
        raw_text = response.strip()
        
        # Extract JSON block
        json_text = _extract_json_block(raw_text)
        
        # Parse and validate
        payload = json.loads(json_text)
        return ConsultationExtraction.model_validate(payload)
        
    except ValueError as e:
        print(f"JSON extraction failed: {e}")
        print(f"Raw response: {raw_text[:500]}")
        return _rule_based_fallback(transcript)
    except json.JSONDecodeError as e:
        print(f"JSON parsing failed: {e}")
        return _rule_based_fallback(transcript)
    except Exception as e:
        print(f"Ollama extraction failed: {e}")
        return _rule_based_fallback(transcript)