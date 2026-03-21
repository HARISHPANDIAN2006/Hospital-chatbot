from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime, timedelta
import os
import requests
from dotenv import load_dotenv

load_dotenv()


class DirectMCPClient:
    """MCP Client that calls MongoDB directly (no HTTP)"""
    
    def __init__(self):
        MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://Harish2006:Harish2006@cluster0.tqoqzv1.mongodb.net/booknest?retryWrites=true&w=majority&appName=Cluster0")
        DB_NAME = os.getenv("DB_NAME", "hospital_db")
        
        self.mongo_client = AsyncIOMotorClient(MONGODB_URI)
        self.db = self.mongo_client[DB_NAME]
        
        self.patients_collection = self.db.patients
        self.doctors_collection = self.db.doctors
        self.appointments_collection = self.db.appointments
        self.medical_records_collection = self.db.medical_records
        self.prescriptions_collection = self.db.prescriptions
        self.lab_reports_collection = self.db.lab_reports
    
    def serialize_doc(self, doc):
        """Convert MongoDB ObjectId to string"""
        if not doc:
            return doc
            
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])
        if "created_at" in doc and isinstance(doc["created_at"], datetime):
            doc["created_at"] = doc["created_at"].isoformat()
        if "updated_at" in doc and isinstance(doc["updated_at"], datetime):
            doc["updated_at"] = doc["updated_at"].isoformat()
        if "appointment_datetime" in doc and isinstance(doc["appointment_datetime"], datetime):
            doc["appointment_datetime"] = doc["appointment_datetime"].isoformat()
        if "date" in doc and isinstance(doc["date"], datetime):
            doc["date"] = doc["date"].isoformat()
        if "test_date" in doc and isinstance(doc["test_date"], datetime):
            doc["test_date"] = doc["test_date"].isoformat()
        if "visit_date" in doc and isinstance(doc["visit_date"], datetime):
            doc["visit_date"] = doc["visit_date"].isoformat()
        
        return doc
    
    async def call(self, tool_name: str, payload: dict):
        """Call tool directly without HTTP"""
        
        # === SEARCH DOCTORS ===
        if tool_name == "search_doctors":
            query = {}
            if payload.get("specialization"):
                query["specialization"] = {"$regex": payload["specialization"], "$options": "i"}
            if payload.get("name"):
                query["name"] = {"$regex": payload["name"], "$options": "i"}
            if payload.get("department"):
                query["department"] = {"$regex": payload["department"], "$options": "i"}
            
            doctors = await self.doctors_collection.find(query).to_list(length=100)
            formatted_doctors = [self.serialize_doc(doc) for doc in doctors]
            
            return {
                "success": True,
                "count": len(formatted_doctors),
                "doctors": formatted_doctors
            }
        
        # === REGISTER PATIENT ===
        elif tool_name == "register_patient":
            patient_data = {
                "name": payload["name"],
                "age": payload["age"],
                "gender": payload["gender"],
                "contact": payload["contact"],
                "email": payload.get("email"),
                "address": payload.get("address"),
                "blood_group": payload.get("blood_group"),
                "emergency_contact": payload.get("emergency_contact"),
                "allergies": payload.get("allergies"),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await self.patients_collection.insert_one(patient_data)
            patient_data["_id"] = str(result.inserted_id)
            
            return {
                "success": True,
                "message": "Patient registered successfully",
                "patient_id": str(result.inserted_id),
                "patient": self.serialize_doc(patient_data)
            }
        
        # === GET PATIENT PROFILE ===
        elif tool_name == "get_patient_profile":
            patient_id = payload.get("patient_id")
            if not patient_id:
                return {"error": "patient_id is required"}
            
            try:
                patient = await self.patients_collection.find_one({"_id": ObjectId(patient_id)})
                if not patient:
                    return {"error": f"Patient with ID {patient_id} not found"}
                
                return {
                    "success": True,
                    "patient": self.serialize_doc(patient)
                }
            except Exception as e:
                return {"error": f"Invalid patient ID: {str(e)}"}
        
        # === UPDATE PATIENT PROFILE ===
        elif tool_name == "update_patient_profile":
            patient_id = payload.get("patient_id")
            updates = payload.get("updates", {})
            
            if not patient_id:
                return {"error": "patient_id is required"}
            
            try:
                updates["updated_at"] = datetime.utcnow()
                result = await self.patients_collection.update_one(
                    {"_id": ObjectId(patient_id)},
                    {"$set": updates}
                )
                
                if result.matched_count == 0:
                    return {"error": f"Patient with ID {patient_id} not found"}
                
                updated_patient = await self.patients_collection.find_one({"_id": ObjectId(patient_id)})
                
                return {
                    "success": True,
                    "message": "Patient profile updated successfully",
                    "patient": self.serialize_doc(updated_patient)
                }
            except Exception as e:
                return {"error": f"Update failed: {str(e)}"}
        
        # === GET DOCTOR INFO ===
        elif tool_name == "get_doctor_info":
            doctor_id = payload.get("doctor_id")
            if not doctor_id:
                return {"error": "doctor_id is required"}
            
            try:
                doctor = await self.doctors_collection.find_one({"_id": ObjectId(doctor_id)})
                if not doctor:
                    return {"error": f"Doctor with ID {doctor_id} not found"}
                
                return {
                    "success": True,
                    "doctor": self.serialize_doc(doctor)
                }
            except Exception as e:
                return {"error": f"Invalid doctor ID: {str(e)}"}
        
        # === BOOK APPOINTMENT ===
        elif tool_name == "book_appointment":
            # Verify patient exists
            try:
                patient = await self.patients_collection.find_one({"_id": ObjectId(payload["patient_id"])})
            except:
                return {"error": f"Invalid patient ID: {payload['patient_id']}"}
            
            if not patient:
                return {"error": f"Patient with ID {payload['patient_id']} not found"}
            
            # Verify doctor exists
            try:
                doctor = await self.doctors_collection.find_one({"_id": ObjectId(payload["doctor_id"])})
            except:
                return {"error": f"Invalid doctor ID: {payload['doctor_id']}"}
            
            if not doctor:
                return {"error": f"Doctor with ID {payload['doctor_id']} not found"}
            
            # Parse datetime
            try:
                appointment_datetime = datetime.strptime(
                    f"{payload['appointment_date']} {payload['appointment_time']}", 
                    "%Y-%m-%d %H:%M"
                )
            except ValueError as e:
                return {"error": f"Invalid date/time format: {str(e)}"}
            
            # Check if slot is available
            existing = await self.appointments_collection.find_one({
                "doctor_id": payload["doctor_id"],
                "appointment_datetime": appointment_datetime,
                "status": {"$in": ["scheduled", "confirmed"]}
            })
            
            if existing:
                return {"error": "This time slot is already booked. Please choose another time."}
            
            appointment_data = {
                "patient_id": payload["patient_id"],
                "patient_name": patient["name"],
                "doctor_id": payload["doctor_id"],
                "doctor_name": doctor["name"],
                "appointment_datetime": appointment_datetime,
                "reason": payload["reason"],
                "symptoms": payload.get("symptoms"),
                "status": "scheduled",
                "created_at": datetime.utcnow()
            }
            
            result = await self.appointments_collection.insert_one(appointment_data)
            appointment_data["_id"] = str(result.inserted_id)
            
            return {
                "success": True,
                "message": "Appointment booked successfully",
                "appointment_id": str(result.inserted_id),
                "appointment": self.serialize_doc(appointment_data)
            }
        
        # === GET MY APPOINTMENTS ===
        elif tool_name == "get_my_appointments":
            patient_id = payload.get("patient_id")
            if not patient_id:
                return {"error": "patient_id is required"}
            
            appointments = await self.appointments_collection.find({
                "patient_id": patient_id
            }).sort("appointment_datetime", -1).to_list(length=100)
            
            formatted_appointments = [self.serialize_doc(doc) for doc in appointments]
            
            return {
                "success": True,
                "count": len(formatted_appointments),
                "appointments": formatted_appointments
            }
        
        # === RESCHEDULE APPOINTMENT ===
        elif tool_name == "reschedule_appointment":
            appointment_id = payload.get("appointment_id")
            new_date = payload.get("new_date")
            new_time = payload.get("new_time")
            
            if not appointment_id:
                return {"error": "appointment_id is required"}
            if not new_date or not new_time:
                return {"error": "new_date and new_time are required"}
            
            try:
                new_datetime = datetime.strptime(f"{new_date} {new_time}", "%Y-%m-%d %H:%M")
            except ValueError as e:
                return {"error": f"Invalid date/time format: {str(e)}"}
            
            try:
                appointment = await self.appointments_collection.find_one({"_id": ObjectId(appointment_id)})
                if not appointment:
                    return {"error": f"Appointment with ID {appointment_id} not found"}
                
                # Check if new slot is available
                existing = await self.appointments_collection.find_one({
                    "doctor_id": appointment["doctor_id"],
                    "appointment_datetime": new_datetime,
                    "status": {"$in": ["scheduled", "confirmed"]},
                    "_id": {"$ne": ObjectId(appointment_id)}
                })
                
                if existing:
                    return {"error": "This time slot is already booked. Please choose another time."}
                
                result = await self.appointments_collection.update_one(
                    {"_id": ObjectId(appointment_id)},
                    {"$set": {"appointment_datetime": new_datetime}}
                )
                
                updated_appointment = await self.appointments_collection.find_one({"_id": ObjectId(appointment_id)})
                
                return {
                    "success": True,
                    "message": "Appointment rescheduled successfully",
                    "appointment": self.serialize_doc(updated_appointment)
                }
            except Exception as e:
                return {"error": f"Reschedule failed: {str(e)}"}
        
        # === CANCEL APPOINTMENT ===
        elif tool_name == "cancel_appointment":
            appointment_id = payload.get("appointment_id")
            if not appointment_id:
                return {"error": "appointment_id is required"}
            
            try:
                result = await self.appointments_collection.update_one(
                    {"_id": ObjectId(appointment_id)},
                    {"$set": {"status": "cancelled"}}
                )
                
                if result.matched_count == 0:
                    return {"error": f"Appointment with ID {appointment_id} not found"}
                
                return {
                    "success": True,
                    "message": "Appointment cancelled successfully"
                }
            except Exception as e:
                return {"error": f"Cancellation failed: {str(e)}"}
        
        # === GET MEDICAL HISTORY ===
        elif tool_name == "get_medical_history":
            patient_id = payload.get("patient_id")
            if not patient_id:
                return {"error": "patient_id is required"}
            
            records = await self.medical_records_collection.find({
                "patient_id": patient_id
            }).sort("visit_date", -1).to_list(length=100)
            
            formatted_records = [self.serialize_doc(doc) for doc in records]
            
            return {
                "success": True,
                "count": len(formatted_records),
                "records": formatted_records
            }
        
        # === GET PRESCRIPTIONS ===
        elif tool_name == "get_prescriptions":
            patient_id = payload.get("patient_id")
            if not patient_id:
                return {"error": "patient_id is required"}
            
            prescriptions = await self.prescriptions_collection.find({
                "patient_id": patient_id
            }).sort("date", -1).to_list(length=100)
            
            formatted_prescriptions = [self.serialize_doc(doc) for doc in prescriptions]
            
            return {
                "success": True,
                "count": len(formatted_prescriptions),
                "prescriptions": formatted_prescriptions
            }
        
        # === GET LAB REPORTS ===
        elif tool_name == "get_lab_reports":
            patient_id = payload.get("patient_id")
            if not patient_id:
                return {"error": "patient_id is required"}
            
            reports = await self.lab_reports_collection.find({
                "patient_id": patient_id
            }).sort("test_date", -1).to_list(length=100)
            
            formatted_reports = [self.serialize_doc(doc) for doc in reports]
            
            return {
                "success": True,
                "count": len(formatted_reports),
                "reports": formatted_reports
            }
        
        # === GET APPOINTMENT REMINDERS ===
        elif tool_name == "get_appointment_reminders":
            patient_id = payload.get("patient_id")
            if not patient_id:
                return {"error": "patient_id is required"}
            
            # Get upcoming appointments (next 30 days)
            now = datetime.utcnow()
            future = now + timedelta(days=30)
            
            appointments = await self.appointments_collection.find({
                "patient_id": patient_id,
                "appointment_datetime": {"$gte": now, "$lte": future},
                "status": {"$in": ["scheduled", "confirmed"]}
            }).sort("appointment_datetime", 1).to_list(length=100)
            
            formatted_appointments = [self.serialize_doc(doc) for doc in appointments]
            
            return {
                "success": True,
                "count": len(formatted_appointments),
                "reminders": formatted_appointments
            }
        
        # === GET HEALTH SUMMARY ===
        elif tool_name == "get_health_summary":
            patient_id = payload.get("patient_id")
            if not patient_id:
                return {"error": "patient_id is required"}
            
            try:
                # Get patient info
                patient = await self.patients_collection.find_one({"_id": ObjectId(patient_id)})
                if not patient:
                    return {"error": f"Patient with ID {patient_id} not found"}
                
                # Get recent appointments
                recent_appointments = await self.appointments_collection.find({
                    "patient_id": patient_id
                }).sort("appointment_datetime", -1).limit(5).to_list(length=5)
                
                # Get recent prescriptions
                recent_prescriptions = await self.prescriptions_collection.find({
                    "patient_id": patient_id
                }).sort("date", -1).limit(5).to_list(length=5)
                
                # Get recent lab reports
                recent_labs = await self.lab_reports_collection.find({
                    "patient_id": patient_id
                }).sort("test_date", -1).limit(5).to_list(length=5)
                
                summary = {
                    "patient": self.serialize_doc(patient),
                    "recent_appointments": [self.serialize_doc(doc) for doc in recent_appointments],
                    "recent_prescriptions": [self.serialize_doc(doc) for doc in recent_prescriptions],
                    "recent_lab_reports": [self.serialize_doc(doc) for doc in recent_labs],
                    "total_appointments": len(recent_appointments),
                    "total_prescriptions": len(recent_prescriptions),
                    "total_lab_reports": len(recent_labs)
                }
                
                return {
                    "success": True,
                    "summary": summary
                }
            except Exception as e:
                return {"error": f"Failed to generate health summary: {str(e)}"}
        
        # === PROCESS CONSULTATION ===
        elif tool_name == "process_consultation":
            consultation_agent_url = os.getenv("CONSULTATION_AGENT_URL", "http://localhost:8001")
            
            try:
                # Call consultation agent
                response = requests.post(
                    f"{consultation_agent_url}/consultation/process",
                    json={
                        "appointment_id": payload["appointment_id"],
                        "send_email": payload.get("send_email", True),
                        "audio_filename": payload.get("audio_filename"),
                        "db_appointment_id": payload.get("db_appointment_id")
                    },
                    timeout=300  # 5 minutes for audio processing
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
                return {"error": "Consultation processing timed out. Audio may be too long."}
            except requests.exceptions.RequestException as e:
                return {"error": f"Failed to process consultation: {str(e)}"}
        
        # === UNKNOWN TOOL ===
        else:
            return {"error": f"Unknown tool: {tool_name}"}