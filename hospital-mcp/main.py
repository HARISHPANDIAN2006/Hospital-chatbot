
#============================================
#MCP Hospital Management Server - Python Implementation
#File: main.py
#============================================


from mcp.server.fastmcp import FastMCP
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId
import os
from dotenv import load_dotenv
import sys

load_dotenv()


MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://Harish2006:Harish2006@cluster0.tqoqzv1.mongodb.net/booknest?retryWrites=true&w=majority&appName=Cluster0")
DB_NAME = os.getenv("DB_NAME", "hospital_db")

try:
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DB_NAME]
    print("MongoDB connection established successfully", file=sys.stderr)
except Exception as err:
    print(f"MongoDB connection failed: {err}", file=sys.stderr)
    raise

# Collections
patients_collection = db.patients
doctors_collection = db.doctors
appointments_collection = db.appointments
medical_records_collection = db.medical_records
prescriptions_collection = db.prescriptions
lab_reports_collection = db.lab_reports

# ============================================
# Initialize FastMCP Server
# ============================================

mcp = FastMCP("hospital-management", json_response=True)

# ============================================
# Helper Functions
# ============================================

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
    return doc

# ============================================
# MCP Tools - Patient Registration & Profile
# ============================================

@mcp.tool()
async def register_patient(
    name: str,
    age: int,
    gender: str,
    contact: str,
    email: Optional[str] = None,
    address: Optional[str] = None,
    blood_group: Optional[str] = None,
    emergency_contact: Optional[str] = None,
    allergies: Optional[str] = None
) -> Dict[str, Any]:
    """
    Register a new patient in the hospital system.
    
    Args:
        name: Patient's full name
        age: Patient's age
        gender: Patient's gender (Male/Female/Other)
        contact: Contact phone number
        email: Email address (optional)
        address: Residential address (optional)
        blood_group: Blood group (A+, B+, O+, AB+, etc.) (optional)
        emergency_contact: Emergency contact number (optional)
        allergies: Known allergies (optional)
    
    Returns:
        Dict containing the registered patient information with patient ID
    """
    try:
        patient_data = {
            "name": name,
            "age": age,
            "gender": gender,
            "contact": contact,
            "email": email,
            "address": address,
            "blood_group": blood_group,
            "emergency_contact": emergency_contact,
            "allergies": allergies,
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
        return {"error": str(e)}

@mcp.tool()
async def get_patient_profile(patient_id: str) -> Dict[str, Any]:
    """
    Get complete patient profile information.
    
    Args:
        patient_id: Patient's unique ID
    
    Returns:
        Dict containing patient profile information
    """
    try:
        patient = await patients_collection.find_one({"_id": ObjectId(patient_id)})
        
        if not patient:
            return {"error": f"Patient with ID {patient_id} not found"}
        
        return {
            "success": True,
            "patient": serialize_doc(patient)
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def update_patient_profile(
    patient_id: str,
    email: Optional[str] = None,
    contact: Optional[str] = None,
    address: Optional[str] = None,
    emergency_contact: Optional[str] = None,
    allergies: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update patient profile information.
    
    Args:
        patient_id: Patient's unique ID
        email: New email address (optional)
        contact: New contact number (optional)
        address: New address (optional)
        emergency_contact: New emergency contact (optional)
        allergies: Updated allergies information (optional)
    
    Returns:
        Dict containing updated patient information
    """
    try:
        updates = {"updated_at": datetime.utcnow()}
        
        if email: updates["email"] = email
        if contact: updates["contact"] = contact
        if address: updates["address"] = address
        if emergency_contact: updates["emergency_contact"] = emergency_contact
        if allergies: updates["allergies"] = allergies
        
        if len(updates) == 1:  # Only updated_at
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



@mcp.tool()
async def search_doctors(
    specialization: Optional[str] = None,
    department: Optional[str] = None,
    name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search for doctors by specialization, department, or name.
    
    Args:
        specialization: Medical specialization (Cardiology, Pediatrics, etc.) (optional)
        department: Hospital department (optional)
        name: Doctor's name (optional)
    
    Returns:
        Dict containing list of matching doctors
    """
    try:
        query = {}
        
        if specialization:
            query["specialization"] = {"$regex": specialization, "$options": "i"}
        if department:
            query["department"] = {"$regex": department, "$options": "i"}
        if name:
            query["name"] = {"$regex": name, "$options": "i"}
        
        doctors = await doctors_collection.find(query).to_list(length=100)
        formatted_doctors = [serialize_doc(doc) for doc in doctors]
        
        return {
            "success": True,
            "count": len(formatted_doctors),
            "doctors": formatted_doctors
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def get_doctor_info(doctor_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific doctor.
    
    Args:
        doctor_id: Doctor's unique ID
    
    Returns:
        Dict containing doctor information
    """
    try:
        doctor = await doctors_collection.find_one({"_id": ObjectId(doctor_id)})
        
        if not doctor:
            return {"error": f"Doctor with ID {doctor_id} not found"}
        
        return {
            "success": True,
            "doctor": serialize_doc(doctor)
        }
    except Exception as e:
        return {"error": str(e)}

# ============================================
# MCP Tools - Appointment Management
# ============================================

@mcp.tool()
async def book_appointment(
    patient_id: str,
    doctor_id: str,
    appointment_date: str,
    appointment_time: str,
    reason: str,
    symptoms: Optional[str] = None
) -> Dict[str, Any]:
    """
    Book a new appointment with a doctor.
    
    Args:
        patient_id: Patient's unique ID
        doctor_id: Doctor's unique ID
        appointment_date: Appointment date (YYYY-MM-DD format)
        appointment_time: Appointment time (HH:MM format, 24-hour)
        reason: Reason for appointment
        symptoms: Current symptoms (optional)
    
    Returns:
        Dict containing appointment confirmation details
    """
    try:
        # Verify patient exists
        patient = await patients_collection.find_one({"_id": ObjectId(patient_id)})
        if not patient:
            return {"error": f"Patient with ID {patient_id} not found"}
        
        # Verify doctor exists
        doctor = await doctors_collection.find_one({"_id": ObjectId(doctor_id)})
        if not doctor:
            return {"error": f"Doctor with ID {doctor_id} not found"}
        
        # Parse datetime
        appointment_datetime = datetime.strptime(f"{appointment_date} {appointment_time}", "%Y-%m-%d %H:%M")
        
        # Check if slot is available
        existing = await appointments_collection.find_one({
            "doctor_id": doctor_id,
            "appointment_datetime": appointment_datetime,
            "status": {"$in": ["scheduled", "confirmed"]}
        })
        
        if existing:
            return {"error": "This time slot is already booked. Please choose another time."}
        
        appointment_data = {
            "patient_id": patient_id,
            "patient_name": patient["name"],
            "doctor_id": doctor_id,
            "doctor_name": doctor["name"],
            "appointment_datetime": appointment_datetime,
            "reason": reason,
            "symptoms": symptoms,
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
        return {"error": str(e)}

@mcp.tool()
async def get_my_appointments(
    patient_id: str,
    status: Optional[str] = None,
    upcoming_only: bool = True
) -> Dict[str, Any]:
    """
    Get all appointments for a patient.
    
    Args:
        patient_id: Patient's unique ID
        status: Filter by status (scheduled/confirmed/completed/cancelled) (optional)
        upcoming_only: Show only upcoming appointments (default: True)
    
    Returns:
        Dict containing list of appointments
    """
    try:
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


@mcp.tool()
async def get_appointment_context(appointment_id: str) -> Dict[str, Any]:
    """
    Get appointment + patient + doctor context by appointment_id.

    Args:
        appointment_id: Appointment ObjectId or external appointment code

    Returns:
        Dict containing combined context needed for downstream workflows
    """
    try:
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

@mcp.tool()
async def reschedule_appointment(
    appointment_id: str,
    new_date: str,
    new_time: str
) -> Dict[str, Any]:
    """
    Reschedule an existing appointment.
    
    Args:
        appointment_id: Appointment ID to reschedule
        new_date: New appointment date (YYYY-MM-DD format)
        new_time: New appointment time (HH:MM format, 24-hour)
    
    Returns:
        Dict containing updated appointment details
    """
    try:
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

@mcp.tool()
async def cancel_appointment(appointment_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
    """
    Cancel an appointment.
    
    Args:
        appointment_id: Appointment ID to cancel
        reason: Reason for cancellation (optional)
    
    Returns:
        Dict containing cancellation confirmation
    """
    try:
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

# ============================================
# MCP Tools - Medical Records & History
# ============================================

@mcp.tool()
async def get_medical_history(patient_id: str, limit: int = 10) -> Dict[str, Any]:
    """
    Get patient's medical history and records.
    
    Args:
        patient_id: Patient's unique ID
        limit: Number of records to retrieve (default: 10)
    
    Returns:
        Dict containing medical records
    """
    try:
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

@mcp.tool()
async def get_prescriptions(
    patient_id: str,
    active_only: bool = False
) -> Dict[str, Any]:
    """
    Get patient's prescriptions.
    
    Args:
        patient_id: Patient's unique ID
        active_only: Show only active prescriptions (default: False)
    
    Returns:
        Dict containing prescriptions
    """
    try:
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

@mcp.tool()
async def get_lab_reports(patient_id: str, limit: int = 10) -> Dict[str, Any]:
    """
    Get patient's lab test reports.
    
    Args:
        patient_id: Patient's unique ID
        limit: Number of reports to retrieve (default: 10)
    
    Returns:
        Dict containing lab reports
    """
    try:
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

# ============================================
# MCP Tools - Health Tracking
# ============================================

@mcp.tool()
async def get_appointment_reminders(patient_id: str, days: int = 7) -> Dict[str, Any]:
    """
    Get upcoming appointment reminders for the next N days.
    
    Args:
        patient_id: Patient's unique ID
        days: Number of days to look ahead (default: 7)
    
    Returns:
        Dict containing upcoming appointments
    """
    try:
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

@mcp.tool()
async def get_health_summary(patient_id: str) -> Dict[str, Any]:
    """
    Get comprehensive health summary for a patient.
    
    Args:
        patient_id: Patient's unique ID
    
    Returns:
        Dict containing health summary with stats
    """
    try:
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

# ============================================
# MCP Resources
# ============================================

@mcp.resource("patient://{patient_id}")
async def get_patient_resource(patient_id: str) -> str:
    """
    Get patient information as a resource.
    
    Args:
        patient_id: Patient ID
    
    Returns:
        Patient information as formatted string
    """
    try:
        patient = await patients_collection.find_one({"_id": ObjectId(patient_id)})
        
        if not patient:
            return f"Patient with ID {patient_id} not found"
        
        return f"""
Patient Profile
===============
ID: {patient_id}
Name: {patient['name']}
Age: {patient['age']}
Gender: {patient['gender']}
Contact: {patient['contact']}
Email: {patient.get('email', 'N/A')}
Blood Group: {patient.get('blood_group', 'N/A')}
Allergies: {patient.get('allergies', 'None recorded')}
Emergency Contact: {patient.get('emergency_contact', 'N/A')}
"""
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.resource("appointment://{appointment_id}")
async def get_appointment_resource(appointment_id: str) -> str:
    """
    Get appointment information as a resource.
    
    Args:
        appointment_id: Appointment ID
    
    Returns:
        Appointment information as formatted string
    """
    try:
        appointment = await appointments_collection.find_one({"_id": ObjectId(appointment_id)})
        
        if not appointment:
            return f"Appointment with ID {appointment_id} not found"
        
        return f"""
Appointment Details
==================
ID: {appointment_id}
Patient: {appointment['patient_name']}
Doctor: {appointment['doctor_name']}
Date & Time: {appointment['appointment_datetime']}
Reason: {appointment['reason']}
Status: {appointment['status']}
Symptoms: {appointment.get('symptoms', 'N/A')}
"""
    except Exception as e:
        return f"Error: {str(e)}"

# ============================================
# MCP Prompts
# ============================================

@mcp.prompt()
def health_checkup_reminder_prompt(patient_name: str) -> str:
    """
    Generate a health checkup reminder prompt.
    
    Args:
        patient_name: Patient's name
    
    Returns:
        Formatted reminder prompt
    """
    return f"""
Dear {patient_name},

This is a friendly reminder about maintaining your health:

1. Regular Check-ups: Schedule routine health screenings
2. Medication Adherence: Take prescribed medicines on time
3. Healthy Lifestyle: Maintain proper diet and exercise
4. Follow-up Visits: Don't miss scheduled appointments

Would you like to:
- Book a general health checkup?
- Review your upcoming appointments?
- Check your active prescriptions?

Stay healthy and take care!
"""

@mcp.prompt()
def appointment_preparation_prompt(appointment_type: str = "general") -> str:
    """
    Generate appointment preparation guidelines.
    
    Args:
        appointment_type: Type of appointment (general, lab, specialist)
    
    Returns:
        Formatted preparation prompt
    """
    prompts = {
        "general": """
Preparing for Your Appointment:

1. Bring your ID and insurance card
2. List current medications and allergies
3. Write down symptoms and questions
4. Arrive 15 minutes early
5. Bring previous medical records if available

What to tell your doctor:
- Current symptoms and when they started
- Medications you're taking
- Family medical history
- Lifestyle factors (diet, exercise, stress)
""",
        "lab": """
Preparing for Lab Tests:

1. Fasting: Check if you need to fast (usually 8-12 hours)
2. Medications: Ask if you should take regular meds
3. Hydration: Drink water unless instructed otherwise
4. Clothing: Wear loose, comfortable clothing
5. Documentation: Bring prescription and ID

Remember to collect your reports on time!
""",
        "specialist": """
Preparing for Specialist Visit:

1. Referral letter from primary doctor
2. Complete medical history
3. Previous test results and imaging
4. List of current medications
5. Insurance pre-authorization (if required)

Prepare detailed questions about:
- Diagnosis and treatment options
- Potential side effects
- Expected outcomes
- Follow-up schedule
"""
    }
    
    return prompts.get(appointment_type, prompts["general"])

# ============================================
# Server Startup
# ============================================

if __name__ == "__main__":
    print("=" * 50, file=sys.stderr)
    print("Hospital Management MCP Server", file=sys.stderr)
    print("=" * 50, file=sys.stderr)
    print(f"Database: {DB_NAME}", file=sys.stderr)
    print(f"MongoDB URI: {MONGODB_URI[:30]}...", file=sys.stderr)
    print("=" * 50, file=sys.stderr)
    print("Starting server...", file=sys.stderr)
    print("=" * 50, file=sys.stderr)
    
    # This line keeps the server running!
    mcp.run()
