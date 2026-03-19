from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from mcp_client import AppointmentContext
from prescription_extractor import ConsultationExtraction


def generate_prescription_pdf(
    output_path: Path,
    appointment: AppointmentContext,
    extraction: ConsultationExtraction,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(output_path), pagesize=A4)
    width, height = A4
    y = height - 40

    def write_line(text: str, font: str = "Helvetica", size: int = 11, gap: int = 16):
        nonlocal y
        c.setFont(font, size)
        c.drawString(40, y, text[:140])
        y -= gap

    write_line("Hospital Consultation Prescription", "Helvetica-Bold", 16, 26)
    write_line(f"Appointment ID: {appointment.appointment_id}")
    write_line(f"Patient: {appointment.patient_name}")
    write_line(f"Doctor: {appointment.doctor_name}")
    if appointment.appointment_datetime:
        write_line(f"Consultation Date: {appointment.appointment_datetime.isoformat()}")
    write_line("")

    write_line("Symptoms", "Helvetica-Bold", 13, 20)
    symptoms_text = ", ".join(extraction.patient_symptoms) if extraction.patient_symptoms else "Not specified"
    write_line(symptoms_text)
    write_line("")

    write_line("Prescription Summary", "Helvetica-Bold", 13, 20)
    write_line(extraction.doctor_prescription_summary or "Not specified")
    write_line("")

    write_line("Medications", "Helvetica-Bold", 13, 20)
    if extraction.medications:
        for idx, med in enumerate(extraction.medications, start=1):
            write_line(
                f"{idx}. {med.medicine_name} | Dosage: {med.dosage} | "
                f"Frequency: {med.frequency} | Duration: {med.duration}"
            )
            if med.instructions:
                write_line(f"   Instructions: {med.instructions}")
    else:
        write_line("No medication extracted.")

    write_line("")
    write_line("Additional Advice", "Helvetica-Bold", 13, 20)
    if extraction.additional_advice:
        for advice in extraction.additional_advice:
            write_line(f"- {advice}")
    else:
        write_line("No additional advice extracted.")

    c.showPage()
    c.save()
    return output_path
