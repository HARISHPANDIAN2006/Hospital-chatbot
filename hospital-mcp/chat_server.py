from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sys
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

# Add ai_mcp to Python path
AI_MCP_PATH = Path(__file__).parent.parent / "ai_mcp"
sys.path.insert(0, str(AI_MCP_PATH))
AI_MCP_MCP_PATH = AI_MCP_PATH / "mcp"
sys.path.insert(0, str(AI_MCP_MCP_PATH))

app = FastAPI(title="Hospital Chat Server")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB setup
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://Harish2006:Harish2006@cluster0.tqoqzv1.mongodb.net/booknest?retryWrites=true&w=majority&appName=Cluster0")
DB_NAME = os.getenv("DB_NAME", "hospital_db")

mongo_client = AsyncIOMotorClient(MONGODB_URI)
db = mongo_client[DB_NAME]

patients_collection = db.patients
doctors_collection = db.doctors
appointments_collection = db.appointments
medical_records_collection = db.medical_records
prescriptions_collection = db.prescriptions
lab_reports_collection = db.lab_reports

def serialize_doc(doc):
    """Convert MongoDB ObjectId to string"""
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    if doc and "created_at" in doc and isinstance(doc["created_at"], datetime):
        doc["created_at"] = doc["created_at"].isoformat()
    if doc and "updated_at" in doc and isinstance(doc["updated_at"], datetime):
        doc["updated_at"] = doc["updated_at"].isoformat()
    if doc and "appointment_datetime" in doc and isinstance(doc["appointment_datetime"], datetime):
        doc["appointment_datetime"] = doc["appointment_datetime"].isoformat()
    if doc and "visit_date" in doc and isinstance(doc["visit_date"], datetime):
        doc["visit_date"] = doc["visit_date"].isoformat()
    if doc and "test_date" in doc and isinstance(doc["test_date"], datetime):
        doc["test_date"] = doc["test_date"].isoformat()
    if doc and "prescribed_date" in doc and isinstance(doc["prescribed_date"], datetime):
        doc["prescribed_date"] = doc["prescribed_date"].isoformat()
    return doc

# ========== TOOL ENDPOINTS ==========

@app.post("/tool/register_patient")
async def register_patient_endpoint(request: Request):
    try:
        body = await request.json()
        print(f"Register patient - Received: {body}")
        
        patient_data = {
            "name": body["name"],
            "age": body["age"],
            "gender": body["gender"],
            "contact": body["contact"],
            "email": body.get("email"),
            "address": body.get("address"),
            "blood_group": body.get("blood_group"),
            "emergency_contact": body.get("emergency_contact"),
            "allergies": body.get("allergies"),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await patients_collection.insert_one(patient_data)
        patient_data["_id"] = str(result.inserted_id)
        
        return {
            "success": True,
            "message": "Patient registered successfully",
            "patient_id": str(result.inserted_id),
            "patient": serialize_doc(patient_data)
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tool/get_patient_profile")
async def get_patient_profile_endpoint(request: Request):
    try:
        body = await request.json()
        patient_id = body.get("patient_id")
        
        patient = await patients_collection.find_one({"_id": ObjectId(patient_id)})
        
        if not patient:
            return {"error": f"Patient with ID {patient_id} not found"}
        
        return {
            "success": True,
            "patient": serialize_doc(patient)
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/tool/update_patient_profile")
async def update_patient_profile_endpoint(request: Request):
    try:
        body = await request.json()
        patient_id = body.get("patient_id")
        
        updates = {"updated_at": datetime.utcnow()}
        
        if body.get("email"): updates["email"] = body["email"]
        if body.get("contact"): updates["contact"] = body["contact"]
        if body.get("address"): updates["address"] = body["address"]
        if body.get("emergency_contact"): updates["emergency_contact"] = body["emergency_contact"]
        if body.get("allergies"): updates["allergies"] = body["allergies"]
        
        if len(updates) == 1:
            return {"error": "No fields to update"}
        
        result = await patients_collection.update_one(
            {"_id": ObjectId(patient_id)},
            {"$set": updates}
        )
        
        if result.modified_count == 0:
            return {"error": f"Patient with ID {patient_id} not found"}
        
        patient = await patients_collection.find_one({"_id": ObjectId(patient_id)})
        
        return {
            "success": True,
            "message": "Patient profile updated successfully",
            "patient": serialize_doc(patient)
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/tool/search_doctors")
async def search_doctors_endpoint(request: Request):
    try:
        body = await request.json()
        print(f"Search doctors - Received: {body}")
        
        query = {}
        if body.get("specialization"):
            query["specialization"] = {"$regex": body["specialization"], "$options": "i"}
        if body.get("name"):
            query["name"] = {"$regex": body["name"], "$options": "i"}
        if body.get("department"):
            query["department"] = {"$regex": body["department"], "$options": "i"}
        
        doctors = await doctors_collection.find(query).to_list(length=100)
        formatted_doctors = [serialize_doc(doc) for doc in doctors]
        
        result = {
            "success": True,
            "count": len(formatted_doctors),
            "doctors": formatted_doctors
        }
        print(f"Search doctors - Result: {result}")
        return result
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tool/get_doctor_info")
async def get_doctor_info_endpoint(request: Request):
    try:
        body = await request.json()
        doctor_id = body.get("doctor_id")
        
        doctor = await doctors_collection.find_one({"_id": ObjectId(doctor_id)})
        
        if not doctor:
            return {"error": f"Doctor with ID {doctor_id} not found"}
        
        return {
            "success": True,
            "doctor": serialize_doc(doctor)
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/tool/book_appointment")
async def book_appointment_endpoint(request: Request):
    try:
        body = await request.json()
        print(f"Book appointment - Received: {body}")
        
        # Verify patient exists
        patient = await patients_collection.find_one({"_id": ObjectId(body["patient_id"])})
        if not patient:
            return {"error": f"Patient with ID {body['patient_id']} not found"}
        
        # Verify doctor exists
        doctor = await doctors_collection.find_one({"_id": ObjectId(body["doctor_id"])})
        if not doctor:
            return {"error": f"Doctor with ID {body['doctor_id']} not found"}
        
        # Parse datetime
        appointment_datetime = datetime.strptime(
            f"{body['appointment_date']} {body['appointment_time']}", 
            "%Y-%m-%d %H:%M"
        )
        
        # Check if slot is available
        existing = await appointments_collection.find_one({
            "doctor_id": body["doctor_id"],
            "appointment_datetime": appointment_datetime,
            "status": {"$in": ["scheduled", "confirmed"]}
        })
        
        if existing:
            return {"error": "This time slot is already booked. Please choose another time."}
        
        appointment_data = {
            "patient_id": body["patient_id"],
            "patient_name": patient["name"],
            "doctor_id": body["doctor_id"],
            "doctor_name": doctor["name"],
            "appointment_datetime": appointment_datetime,
            "reason": body["reason"],
            "symptoms": body.get("symptoms"),
            "status": "scheduled",
            "created_at": datetime.utcnow()
        }
        
        result = await appointments_collection.insert_one(appointment_data)
        appointment_data["_id"] = str(result.inserted_id)
        
        return {
            "success": True,
            "message": "Appointment booked successfully",
            "appointment_id": str(result.inserted_id),
            "appointment": serialize_doc(appointment_data)
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"error": str(e)}

@app.post("/tool/get_my_appointments")
async def get_my_appointments_endpoint(request: Request):
    try:
        body = await request.json()
        patient_id = body.get("patient_id")
        status = body.get("status")
        upcoming_only = body.get("upcoming_only", True)
        
        query = {"patient_id": patient_id}
        
        if status:
            query["status"] = status
        
        if upcoming_only:
            query["appointment_datetime"] = {"$gte": datetime.utcnow()}
        
        appointments = await appointments_collection.find(query).sort("appointment_datetime", 1).to_list(length=100)
        formatted_appointments = [serialize_doc(doc) for doc in appointments]
        
        return {
            "success": True,
            "count": len(formatted_appointments),
            "appointments": formatted_appointments
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/tool/get_appointment_context")
async def get_appointment_context_endpoint(request: Request):
    try:
        body = await request.json()
        appointment_id = body.get("appointment_id", "").strip()
        if not appointment_id:
            return {"error": "appointment_id is required"}

        appointment = None

        if ObjectId.is_valid(appointment_id):
            appointment = await appointments_collection.find_one({"_id": ObjectId(appointment_id)})

        if not appointment:
            for field in ("appointment_id", "external_appointment_id", "appointment_code"):
                appointment = await appointments_collection.find_one({field: appointment_id})
                if appointment:
                    break

        if not appointment:
            return {"error": f"Appointment with ID {appointment_id} not found"}

        patient_id = str(appointment.get("patient_id", ""))
        doctor_id = str(appointment.get("doctor_id", ""))

        patient = None
        if ObjectId.is_valid(patient_id):
            patient = await patients_collection.find_one({"_id": ObjectId(patient_id)})
        if not patient:
            patient = await patients_collection.find_one({"_id": patient_id})

        doctor = None
        if ObjectId.is_valid(doctor_id):
            doctor = await doctors_collection.find_one({"_id": ObjectId(doctor_id)})
        if not doctor:
            doctor = await doctors_collection.find_one({"_id": doctor_id})

        return {
            "success": True,
            "appointment_id": appointment_id,
            "context": {
                "appointment": serialize_doc(appointment),
                "patient": serialize_doc(patient) if patient else None,
                "doctor": serialize_doc(doctor) if doctor else None,
            },
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/tool/reschedule_appointment")
async def reschedule_appointment_endpoint(request: Request):
    try:
        body = await request.json()
        appointment_id = body.get("appointment_id")
        new_date = body.get("new_date")
        new_time = body.get("new_time")
        
        appointment = await appointments_collection.find_one({"_id": ObjectId(appointment_id)})
        if not appointment:
            return {"error": f"Appointment with ID {appointment_id} not found"}
        
        new_datetime = datetime.strptime(f"{new_date} {new_time}", "%Y-%m-%d %H:%M")
        
        # Check if new slot is available
        existing = await appointments_collection.find_one({
            "doctor_id": appointment["doctor_id"],
            "appointment_datetime": new_datetime,
            "status": {"$in": ["scheduled", "confirmed"]},
            "_id": {"$ne": ObjectId(appointment_id)}
        })
        
        if existing:
            return {"error": "This time slot is already booked. Please choose another time."}
        
        result = await appointments_collection.update_one(
            {"_id": ObjectId(appointment_id)},
            {"$set": {"appointment_datetime": new_datetime, "updated_at": datetime.utcnow()}}
        )
        
        updated = await appointments_collection.find_one({"_id": ObjectId(appointment_id)})
        
        return {
            "success": True,
            "message": "Appointment rescheduled successfully",
            "appointment": serialize_doc(updated)
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/tool/cancel_appointment")
async def cancel_appointment_endpoint(request: Request):
    try:
        body = await request.json()
        appointment_id = body.get("appointment_id")
        reason = body.get("reason")
        
        update_data = {
            "status": "cancelled",
            "cancelled_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        if reason:
            update_data["cancellation_reason"] = reason
        
        result = await appointments_collection.update_one(
            {"_id": ObjectId(appointment_id)},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            return {"error": f"Appointment with ID {appointment_id} not found"}
        
        return {
            "success": True,
            "message": "Appointment cancelled successfully",
            "appointment_id": appointment_id
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/tool/get_medical_history")
async def get_medical_history_endpoint(request: Request):
    try:
        body = await request.json()
        patient_id = body.get("patient_id")
        limit = body.get("limit", 10)
        
        records = await medical_records_collection.find(
            {"patient_id": patient_id}
        ).sort("visit_date", -1).limit(limit).to_list(length=limit)
        
        formatted_records = [serialize_doc(doc) for doc in records]
        
        return {
            "success": True,
            "count": len(formatted_records),
            "medical_records": formatted_records
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/tool/get_prescriptions")
async def get_prescriptions_endpoint(request: Request):
    try:
        body = await request.json()
        patient_id = body.get("patient_id")
        active_only = body.get("active_only", False)
        
        query = {"patient_id": patient_id}
        
        if active_only:
            query["status"] = "active"
        
        prescriptions = await prescriptions_collection.find(query).sort("prescribed_date", -1).to_list(length=100)
        formatted_prescriptions = [serialize_doc(doc) for doc in prescriptions]
        
        return {
            "success": True,
            "count": len(formatted_prescriptions),
            "prescriptions": formatted_prescriptions
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/tool/get_lab_reports")
async def get_lab_reports_endpoint(request: Request):
    try:
        body = await request.json()
        patient_id = body.get("patient_id")
        limit = body.get("limit", 10)
        
        reports = await lab_reports_collection.find(
            {"patient_id": patient_id}
        ).sort("test_date", -1).limit(limit).to_list(length=limit)
        
        formatted_reports = [serialize_doc(doc) for doc in reports]
        
        return {
            "success": True,
            "count": len(formatted_reports),
            "lab_reports": formatted_reports
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/tool/get_appointment_reminders")
async def get_appointment_reminders_endpoint(request: Request):
    try:
        body = await request.json()
        patient_id = body.get("patient_id")
        days = body.get("days", 7)
        
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=days)
        
        appointments = await appointments_collection.find({
            "patient_id": patient_id,
            "appointment_datetime": {"$gte": start_date, "$lte": end_date},
            "status": {"$in": ["scheduled", "confirmed"]}
        }).sort("appointment_datetime", 1).to_list(length=100)
        
        formatted_appointments = [serialize_doc(doc) for doc in appointments]
        
        return {
            "success": True,
            "count": len(formatted_appointments),
            "reminder_period": f"Next {days} days",
            "appointments": formatted_appointments
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/tool/get_health_summary")
async def get_health_summary_endpoint(request: Request):
    try:
        body = await request.json()
        patient_id = body.get("patient_id")
        
        # Get patient info
        patient = await patients_collection.find_one({"_id": ObjectId(patient_id)})
        if not patient:
            return {"error": f"Patient with ID {patient_id} not found"}
        
        # Count records
        total_visits = await medical_records_collection.count_documents({"patient_id": patient_id})
        upcoming_appointments = await appointments_collection.count_documents({
            "patient_id": patient_id,
            "appointment_datetime": {"$gte": datetime.utcnow()},
            "status": {"$in": ["scheduled", "confirmed"]}
        })
        active_prescriptions = await prescriptions_collection.count_documents({
            "patient_id": patient_id,
            "status": "active"
        })
        
        # Get recent visit
        recent_visit = await medical_records_collection.find_one(
            {"patient_id": patient_id},
            sort=[("visit_date", -1)]
        )
        
        return {
            "success": True,
            "patient_name": patient["name"],
            "summary": {
                "total_visits": total_visits,
                "upcoming_appointments": upcoming_appointments,
                "active_prescriptions": active_prescriptions,
                "last_visit": serialize_doc(recent_visit) if recent_visit else None,
                "blood_group": patient.get("blood_group"),
                "allergies": patient.get("allergies")
            }
        }
    except Exception as e:
        return {"error": str(e)}

# ========== CHAT ENDPOINT ==========

@app.post("/chat")
async def chat_endpoint(request: Request):
    try:
        body = await request.json()
        query = body.get("query", "")
        
        print(f"Received query: {query}")
        
        # Import AI MCP modules
        try:
            from mcp.controller import MCPController
            from mcp.executor import MCPExecutor
        except ModuleNotFoundError:
            from controller import MCPController
            from executor import MCPExecutor
        
        mcp = MCPController()
        
        # Create executor
        mcp_executor = MCPExecutor()
        
        action = mcp.decide(query)
        print(f"Action decided: {action}")
        
        if action == "RUN_MCP":
            # ✅ CORRECT - Added await
            result = await mcp_executor.execute(
                intent=mcp.intent_classifier.classify(query),
                query=query
            )
            print(f"MCP Result: {result}")
            return result
        else:
            return {
                "human_response": "I can help you with:\n• Registering new patients\n• Searching for doctors\n• Booking appointments\n\nWhat would you like to do?",
                "raw_data": {"action": action}
            }
            
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"ERROR: {error_trace}")
        return {
            "human_response": f"Sorry, I encountered an error: {str(e)}",
            "raw_data": {"error": str(e)}
        }

@app.get("/")
async def root():
    return {"message": "Hospital Chat Server is running!", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Hospital Chat Server"}

if __name__ == "__main__":
    print("=" * 60)
    print("🏥 Hospital Chat Server - Complete Edition")
    print("=" * 60)
    print("Starting server on http://localhost:3333")
    print("React app should connect to this server")
    print(f"MongoDB: {MONGODB_URI[:50]}...")
    print("=" * 60)
    print("\n📋 Available Tools:")
    print("  • register_patient")
    print("  • get_patient_profile")
    print("  • update_patient_profile")
    print("  • search_doctors")
    print("  • get_doctor_info")
    print("  • book_appointment")
    print("  • get_my_appointments")
    print("  • get_appointment_context")
    print("  • reschedule_appointment")
    print("  • cancel_appointment")
    print("  • get_medical_history")
    print("  • get_prescriptions")
    print("  • get_lab_reports")
    print("  • get_appointment_reminders")
    print("  • get_health_summary")
    print("=" * 60)
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=3333,
        timeout_keep_alive=120  # ← Add this
    )
