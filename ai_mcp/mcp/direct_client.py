from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime, timedelta
import os
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
        if doc and "_id" in doc:
            doc["_id"] = str(doc["_id"])
        if doc and "created_at" in doc and isinstance(doc["created_at"], datetime):
            doc["created_at"] = doc["created_at"].isoformat()
        if doc and "updated_at" in doc and isinstance(doc["updated_at"], datetime):
            doc["updated_at"] = doc["updated_at"].isoformat()
        if doc and "appointment_datetime" in doc and isinstance(doc["appointment_datetime"], datetime):
            doc["appointment_datetime"] = doc["appointment_datetime"].isoformat()
        return doc
    
    async def call(self, tool_name: str, payload: dict):
        """Call tool directly without HTTP"""
        
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
        
        elif tool_name == "book_appointment":
            # Verify patient exists
            patient = await self.patients_collection.find_one({"_id": ObjectId(payload["patient_id"])})
            if not patient:
                return {"error": f"Patient with ID {payload['patient_id']} not found"}
            
            # Verify doctor exists
            doctor = await self.doctors_collection.find_one({"_id": ObjectId(payload["doctor_id"])})
            if not doctor:
                return {"error": f"Doctor with ID {payload['doctor_id']} not found"}
            
            # Parse datetime
            appointment_datetime = datetime.strptime(
                f"{payload['appointment_date']} {payload['appointment_time']}", 
                "%Y-%m-%d %H:%M"
            )
            
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
        
        else:
            return {"error": f"Unknown tool: {tool_name}"}