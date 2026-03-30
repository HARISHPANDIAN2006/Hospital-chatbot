import asyncpg
import os
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv

load_dotenv()


class DirectMCPClient:
    """MCP Client for PostgreSQL"""
    
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "postgresql://postgres:root@localhost:5432/hospital_db")
        self.pool = None
    
    async def connect(self):
        """Create connection pool"""
        if not self.pool:
            self.pool = await asyncpg.create_pool(self.database_url)
    
    async def close(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
    
    def serialize_record(self, record):
        """Convert asyncpg record to dict"""
        if not record:
            return None
        data = dict(record)
        # Convert datetime to ISO format
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data
    
    async def call(self, tool_name: str, payload: dict):
        """Call tool"""
        await self.connect()
        
        # === SEARCH DOCTORS ===
        if tool_name == "search_doctors":
            query = "SELECT * FROM doctors WHERE 1=1"
            params = []
            
            if payload.get("specialization"):
                query += " AND specialization ILIKE $" + str(len(params) + 1)
                params.append(f"%{payload['specialization']}%")
            
            if payload.get("name"):
                query += " AND name ILIKE $" + str(len(params) + 1)
                params.append(f"%{payload['name']}%")
            
            async with self.pool.acquire() as conn:
                doctors = await conn.fetch(query, *params)
                formatted_doctors = [self.serialize_record(doc) for doc in doctors]
            
            return {
                "success": True,
                "count": len(formatted_doctors),
                "doctors": formatted_doctors
            }
        
        # === REGISTER PATIENT ===
        elif tool_name == "register_patient":
            query = """
                INSERT INTO patients (name, age, gender, contact, email, address, blood_group, emergency_contact, allergies)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING *
            """
            
            async with self.pool.acquire() as conn:
                patient = await conn.fetchrow(
                    query,
                    payload["name"],
                    payload["age"],
                    payload["gender"],
                    payload["contact"],
                    payload.get("email"),
                    payload.get("address"),
                    payload.get("blood_group"),
                    payload.get("emergency_contact"),
                    payload.get("allergies")
                )
            
            return {
                "success": True,
                "message": "Patient registered successfully",
                "patient_id": str(patient["id"]),
                "patient": self.serialize_record(patient)
            }
        
        # === GET PATIENT PROFILE ===
        elif tool_name == "get_patient_profile":
            patient_id = payload.get("patient_id")
            
            async with self.pool.acquire() as conn:
                patient = await conn.fetchrow("SELECT * FROM patients WHERE id = $1", int(patient_id))
            
            if not patient:
                return {"error": f"Patient with ID {patient_id} not found"}
            
            return {
                "success": True,
                "patient": self.serialize_record(patient)
            }
        
        # === UPDATE PATIENT PROFILE ===
        elif tool_name == "update_patient_profile":
            patient_id = int(payload.get("patient_id"))
            updates = payload.get("updates", {})
            
            set_clauses = []
            params = []
            param_count = 1
            
            for key, value in updates.items():
                set_clauses.append(f"{key} = ${param_count}")
                params.append(value)
                param_count += 1
            
            set_clauses.append(f"updated_at = ${param_count}")
            params.append(datetime.utcnow())
            param_count += 1
            
            params.append(patient_id)
            
            query = f"UPDATE patients SET {', '.join(set_clauses)} WHERE id = ${param_count} RETURNING *"
            
            async with self.pool.acquire() as conn:
                patient = await conn.fetchrow(query, *params)
            
            if not patient:
                return {"error": f"Patient with ID {patient_id} not found"}
            
            return {
                "success": True,
                "message": "Patient profile updated successfully",
                "patient": self.serialize_record(patient)
            }
        
        # === GET DOCTOR INFO ===
        elif tool_name == "get_doctor_info":
            doctor_id = int(payload.get("doctor_id"))
            
            async with self.pool.acquire() as conn:
                doctor = await conn.fetchrow("SELECT * FROM doctors WHERE id = $1", doctor_id)
            
            if not doctor:
                return {"error": f"Doctor with ID {doctor_id} not found"}
            
            return {
                "success": True,
                "doctor": self.serialize_record(doctor)
            }
        
        # === BOOK APPOINTMENT ===
        elif tool_name == "book_appointment":
            patient_id = int(payload["patient_id"])
            doctor_id = int(payload["doctor_id"])
            
            async with self.pool.acquire() as conn:
                # Verify patient
                patient = await conn.fetchrow("SELECT * FROM patients WHERE id = $1", patient_id)
                if not patient:
                    return {"error": f"Patient with ID {patient_id} not found"}
                
                # Verify doctor
                doctor = await conn.fetchrow("SELECT * FROM doctors WHERE id = $1", doctor_id)
                if not doctor:
                    return {"error": f"Doctor with ID {doctor_id} not found"}
                
                # Parse datetime
                appointment_datetime = datetime.strptime(
                    f"{payload['appointment_date']} {payload['appointment_time']}", 
                    "%Y-%m-%d %H:%M"
                )
                
                # Check availability
                existing = await conn.fetchrow(
                    "SELECT * FROM appointments WHERE doctor_id = $1 AND appointment_datetime = $2 AND status IN ('scheduled', 'confirmed')",
                    doctor_id, appointment_datetime
                )
                
                if existing:
                    return {"error": "This time slot is already booked. Please choose another time."}
                
                # Book appointment
                appointment = await conn.fetchrow(
                    """
                    INSERT INTO appointments (patient_id, patient_name, doctor_id, doctor_name, appointment_datetime, reason, symptoms, status)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, 'scheduled')
                    RETURNING *
                    """,
                    patient_id, patient["name"], doctor_id, doctor["name"], 
                    appointment_datetime, payload["reason"], payload.get("symptoms")
                )
            
            return {
                "success": True,
                "message": "Appointment booked successfully",
                "appointment_id": str(appointment["id"]),
                "appointment": self.serialize_record(appointment)
            }
        
        # === GET MY APPOINTMENTS ===
        elif tool_name == "get_my_appointments":
            patient_id = int(payload.get("patient_id"))
            
            async with self.pool.acquire() as conn:
                appointments = await conn.fetch(
                    "SELECT * FROM appointments WHERE patient_id = $1 ORDER BY appointment_datetime DESC",
                    patient_id
                )
            
            formatted_appointments = [self.serialize_record(apt) for apt in appointments]
            
            return {
                "success": True,
                "count": len(formatted_appointments),
                "appointments": formatted_appointments
            }
        
        # === RESCHEDULE APPOINTMENT ===
        elif tool_name == "reschedule_appointment":
            appointment_id = int(payload.get("appointment_id"))
            new_datetime = datetime.strptime(
                f"{payload['new_date']} {payload['new_time']}", 
                "%Y-%m-%d %H:%M"
            )
            
            async with self.pool.acquire() as conn:
                appointment = await conn.fetchrow(
                    "UPDATE appointments SET appointment_datetime = $1, updated_at = $2 WHERE id = $3 RETURNING *",
                    new_datetime, datetime.utcnow(), appointment_id
                )
            
            if not appointment:
                return {"error": f"Appointment with ID {appointment_id} not found"}
            
            return {
                "success": True,
                "message": "Appointment rescheduled successfully",
                "appointment": self.serialize_record(appointment)
            }
        
        # === CANCEL APPOINTMENT ===
        elif tool_name == "cancel_appointment":
            appointment_id = int(payload.get("appointment_id"))
            
            async with self.pool.acquire() as conn:
                result = await conn.execute(
                    "UPDATE appointments SET status = 'cancelled', cancelled_at = $1 WHERE id = $2",
                    datetime.utcnow(), appointment_id
                )
            
            if result == "UPDATE 0":
                return {"error": f"Appointment with ID {appointment_id} not found"}
            
            return {
                "success": True,
                "message": "Appointment cancelled successfully"
            }
        
        # === GET MEDICAL HISTORY ===
        elif tool_name == "get_medical_history":
            patient_id = int(payload.get("patient_id"))
            
            async with self.pool.acquire() as conn:
                records = await conn.fetch(
                    "SELECT * FROM medical_records WHERE patient_id = $1 ORDER BY visit_date DESC",
                    patient_id
                )
            
            formatted_records = [self.serialize_record(rec) for rec in records]
            
            return {
                "success": True,
                "count": len(formatted_records),
                "records": formatted_records
            }
        
        # === GET PRESCRIPTIONS ===
        elif tool_name == "get_prescriptions":
            patient_id = int(payload.get("patient_id"))
            
            async with self.pool.acquire() as conn:
                prescriptions = await conn.fetch(
                    "SELECT * FROM prescriptions WHERE patient_id = $1 ORDER BY prescribed_date DESC",
                    patient_id
                )
            
            formatted_prescriptions = [self.serialize_record(pres) for pres in prescriptions]
            
            return {
                "success": True,
                "count": len(formatted_prescriptions),
                "prescriptions": formatted_prescriptions
            }
        
        # === GET LAB REPORTS ===
        elif tool_name == "get_lab_reports":
            patient_id = int(payload.get("patient_id"))
            
            async with self.pool.acquire() as conn:
                reports = await conn.fetch(
                    "SELECT * FROM lab_reports WHERE patient_id = $1 ORDER BY test_date DESC",
                    patient_id
                )
            
            formatted_reports = [self.serialize_record(rep) for rep in reports]
            
            return {
                "success": True,
                "count": len(formatted_reports),
                "reports": formatted_reports
            }
        
        # === GET APPOINTMENT REMINDERS ===
        elif tool_name == "get_appointment_reminders":
            patient_id = int(payload.get("patient_id"))
            now = datetime.utcnow()
            future = now + timedelta(days=30)
            
            async with self.pool.acquire() as conn:
                appointments = await conn.fetch(
                    """SELECT * FROM appointments 
                       WHERE patient_id = $1 
                       AND appointment_datetime BETWEEN $2 AND $3 
                       AND status IN ('scheduled', 'confirmed')
                       ORDER BY appointment_datetime""",
                    patient_id, now, future
                )
            
            formatted_appointments = [self.serialize_record(apt) for apt in appointments]
            
            return {
                "success": True,
                "count": len(formatted_appointments),
                "reminders": formatted_appointments
            }
        
        # === GET HEALTH SUMMARY ===
        elif tool_name == "get_health_summary":
            patient_id = int(payload.get("patient_id"))
            
            async with self.pool.acquire() as conn:
                patient = await conn.fetchrow("SELECT * FROM patients WHERE id = $1", patient_id)
                if not patient:
                    return {"error": f"Patient with ID {patient_id} not found"}
                
                recent_appointments = await conn.fetch(
                    "SELECT * FROM appointments WHERE patient_id = $1 ORDER BY appointment_datetime DESC LIMIT 5",
                    patient_id
                )
                
                recent_prescriptions = await conn.fetch(
                    "SELECT * FROM prescriptions WHERE patient_id = $1 ORDER BY prescribed_date DESC LIMIT 5",
                    patient_id
                )
                
                recent_labs = await conn.fetch(
                    "SELECT * FROM lab_reports WHERE patient_id = $1 ORDER BY test_date DESC LIMIT 5",
                    patient_id
                )
            
            return {
                "success": True,
                "summary": {
                    "patient": self.serialize_record(patient),
                    "recent_appointments": [self.serialize_record(a) for a in recent_appointments],
                    "recent_prescriptions": [self.serialize_record(p) for p in recent_prescriptions],
                    "recent_lab_reports": [self.serialize_record(l) for l in recent_labs]
                }
            }
        
        # === PROCESS CONSULTATION ===
        elif tool_name == "process_consultation":
            consultation_agent_url = os.getenv("CONSULTATION_AGENT_URL", "http://localhost:8001")
            
            try:
                response = requests.post(
                    f"{consultation_agent_url}/consultation/process",
                    json={
                        "appointment_id": payload["appointment_id"],
                        "send_email": payload.get("send_email", True),
                        "audio_filename": payload.get("audio_filename"),
                        "db_appointment_id": payload.get("db_appointment_id")
                    },
                    timeout=300
                )
                response.raise_for_status()
                result = response.json()
                
                return {
                    "success": True,
                    "message": f"Consultation processed for {result['patient_name']}",
                    "prescription_pdf": result["pdf_path"],
                    "email_sent": result["email_sent"],
                    "patient_name": result["patient_name"],
                    "doctor_name": result["doctor_name"],
                    "extraction": result["extraction"]
                }
            except requests.exceptions.Timeout:
                return {"error": "Consultation processing timed out."}
            except requests.exceptions.RequestException as e:
                return {"error": f"Failed to process consultation: {str(e)}"}
        
        else:
            return {"error": f"Unknown tool: {tool_name}"}