from __future__ import annotations

import mimetypes
import smtplib
from email.message import EmailMessage
from pathlib import Path


def send_prescription_email(
    smtp_host: str,
    smtp_port: int,
    smtp_username: str,
    smtp_password: str,
    sender_email: str,
    recipient_email: str,
    recipient_name: str,
    doctor_name: str,
    appointment_id: str,
    pdf_path: Path,
    use_tls: bool = True,
) -> None:
    if not pdf_path.exists():
        raise FileNotFoundError(f"Prescription PDF not found: {pdf_path}")

    msg = EmailMessage()
    msg["Subject"] = f"Prescription for Appointment {appointment_id}"
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg.set_content(
        f"Dear {recipient_name},\n\n"
        f"Your prescription from {doctor_name} is attached.\n"
        "Please follow the advice and medication schedule.\n\n"
        "Regards,\nHospital AI Platform"
    )

    ctype, encoding = mimetypes.guess_type(str(pdf_path))
    maintype, subtype = (ctype or "application/pdf").split("/", 1)
    with pdf_path.open("rb") as f:
        msg.add_attachment(
            f.read(),
            maintype=maintype,
            subtype=subtype,
            filename=pdf_path.name,
        )

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        if use_tls:
            server.starttls()
        if smtp_username:
            server.login(smtp_username, smtp_password)
        server.send_message(msg)
