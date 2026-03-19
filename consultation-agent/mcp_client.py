from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import requests
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient


@dataclass
class AppointmentContext:
    appointment_id: str
    db_appointment_id: str
    patient_id: str
    patient_name: str
    patient_email: str
    doctor_id: str
    doctor_name: str
    appointment_datetime: Optional[datetime]
    reason: Optional[str]
    symptoms: Optional[str]


class MCPClient:
    def __init__(
        self,
        mongodb_uri: str,
        db_name: str,
        mcp_base_url: Optional[str] = None,
    ) -> None:
        self._mcp_base_url = (mcp_base_url or "").rstrip("/")
        self._client = AsyncIOMotorClient(mongodb_uri) if mongodb_uri else None
        self._db = self._client[db_name] if self._client else None

    async def close(self) -> None:
        if self._client:
            self._client.close()

    async def get_appointment_context(
        self, appointment_id: str, db_appointment_id: Optional[str] = None
    ) -> AppointmentContext:
        if self._mcp_base_url:
            context = await self._get_context_from_mcp(appointment_id)
            if context:
                return context

            # Try fallback with mapped DB ObjectId if given.
            if db_appointment_id and db_appointment_id != appointment_id:
                context = await self._get_context_from_mcp(db_appointment_id)
                if context:
                    return context

        if self._db is None:
            raise ValueError("Neither MCP HTTP nor MongoDB client is configured.")

        appointment = await self._find_appointment(db_appointment_id or appointment_id)
        if not appointment:
            raise ValueError(f"Appointment not found for id: {appointment_id}")

        patient_id = str(appointment.get("patient_id", ""))
        doctor_id = str(appointment.get("doctor_id", ""))

        patient_doc = await self._find_by_id("patients", patient_id)
        if not patient_doc:
            raise ValueError(f"Patient not found for id: {patient_id}")

        patient_email = str(patient_doc.get("email", "")).strip()

        return AppointmentContext(
            appointment_id=appointment_id,
            db_appointment_id=str(appointment.get("_id")),
            patient_id=patient_id,
            patient_name=str(appointment.get("patient_name", patient_doc.get("name", "Patient"))),
            patient_email=patient_email,
            doctor_id=doctor_id,
            doctor_name=str(appointment.get("doctor_name", "Doctor")),
            appointment_datetime=appointment.get("appointment_datetime"),
            reason=appointment.get("reason"),
            symptoms=appointment.get("symptoms"),
        )

    async def _get_context_from_mcp(self, appointment_id: str) -> Optional[AppointmentContext]:
        try:
            response = await asyncio.to_thread(
                requests.post,
                f"{self._mcp_base_url}/tool/get_appointment_context",
                json={"appointment_id": appointment_id},
                timeout=30,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception:
            return None

        if not payload.get("success"):
            return None

        context = payload.get("context") or {}
        appointment = context.get("appointment") or {}
        patient = context.get("patient") or {}
        doctor = context.get("doctor") or {}

        patient_id = str(appointment.get("patient_id", ""))
        doctor_id = str(appointment.get("doctor_id", ""))
        patient_email = str(patient.get("email", "")).strip()
        # Allow empty email for non-email workflows.

        appointment_dt = appointment.get("appointment_datetime")
        parsed_dt: Optional[datetime] = None
        if isinstance(appointment_dt, str):
            try:
                parsed_dt = datetime.fromisoformat(appointment_dt)
            except ValueError:
                parsed_dt = None

        return AppointmentContext(
            appointment_id=appointment_id,
            db_appointment_id=str(appointment.get("_id", "")),
            patient_id=patient_id,
            patient_name=str(
                appointment.get("patient_name", patient.get("name", "Patient"))
            ),
            patient_email=patient_email,
            doctor_id=doctor_id,
            doctor_name=str(appointment.get("doctor_name", doctor.get("name", "Doctor"))),
            appointment_datetime=parsed_dt,
            reason=appointment.get("reason"),
            symptoms=appointment.get("symptoms"),
        )

    async def _find_appointment(self, appointment_id: str):
        appointments = self._db.appointments

        object_id_query = self._object_id_query(appointment_id)
        if object_id_query:
            doc = await appointments.find_one(object_id_query)
            if doc:
                return doc

        # Supports future schema where a human-friendly appointment code is stored.
        for field in ("appointment_id", "external_appointment_id", "appointment_code"):
            doc = await appointments.find_one({field: appointment_id})
            if doc:
                return doc

        return None

    async def _find_by_id(self, collection_name: str, raw_id: str):
        collection = self._db[collection_name]
        object_id_query = self._object_id_query(raw_id)
        if object_id_query:
            doc = await collection.find_one(object_id_query)
            if doc:
                return doc
        return await collection.find_one({"_id": raw_id})

    @staticmethod
    def _object_id_query(raw_id: str):
        if ObjectId.is_valid(raw_id):
            return {"_id": ObjectId(raw_id)}
        return None
