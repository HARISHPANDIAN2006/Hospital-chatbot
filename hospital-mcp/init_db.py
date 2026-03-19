"""
Initialize Hospital Management Database
Run this once to set up collections and indexes
"""

from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://username:password@cluster.mongodb.net/")
DB_NAME = os.getenv("DB_NAME", "hospital_db")

async def initialize_database():
    """Create collections and indexes for hospital management system"""
    
    print("Connecting to MongoDB...")
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DB_NAME]
    
    try:
        # Create collections
        collections = [
            "patients",
            "doctors", 
            "appointments",
            "medical_records",
            "prescriptions",
            "lab_reports"
        ]
        
        print("\n=== Creating Collections ===")
        for collection_name in collections:
            # MongoDB creates collection automatically, but we'll ensure it exists
            await db.create_collection(collection_name)
            print(f"✓ Collection '{collection_name}' created")
        
        print("\n=== Creating Indexes ===")
        
        # Patients indexes
        await db.patients.create_index("contact")
        await db.patients.create_index("email")
        print("✓ Patients indexes created")
        
        # Doctors indexes
        await db.doctors.create_index("specialization")
        await db.doctors.create_index("department")
        await db.doctors.create_index("name")
        print("✓ Doctors indexes created")
        
        # Appointments indexes
        await db.appointments.create_index("patient_id")
        await db.appointments.create_index("doctor_id")
        await db.appointments.create_index("appointment_datetime")
        await db.appointments.create_index([("doctor_id", 1), ("appointment_datetime", 1)], unique=True)
        await db.appointments.create_index("status")
        print("✓ Appointments indexes created")
        
        # Medical records indexes
        await db.medical_records.create_index("patient_id")
        await db.medical_records.create_index("doctor_id")
        await db.medical_records.create_index("visit_date")
        print("✓ Medical records indexes created")
        
        # Prescriptions indexes
        await db.prescriptions.create_index("patient_id")
        await db.prescriptions.create_index("status")
        await db.prescriptions.create_index("prescribed_date")
        print("✓ Prescriptions indexes created")
        
        # Lab reports indexes
        await db.lab_reports.create_index("patient_id")
        await db.lab_reports.create_index("test_date")
        print("✓ Lab reports indexes created")
        
        print("\n=== Inserting Sample Data ===")
        
        # Insert sample doctors
        sample_doctors = [
            {
                "name": "Dr. Sarah Johnson",
                "specialization": "Cardiology",
                "qualification": "MD, FACC",
                "contact": "+1-555-0101",
                "email": "sarah.johnson@hospital.com",
                "department": "Cardiology",
                "experience_years": 15
            },
            {
                "name": "Dr. Michael Chen",
                "specialization": "Pediatrics",
                "qualification": "MD, FAAP",
                "contact": "+1-555-0102",
                "email": "michael.chen@hospital.com",
                "department": "Pediatrics",
                "experience_years": 10
            },
            {
                "name": "Dr. Emily Rodriguez",
                "specialization": "Orthopedics",
                "qualification": "MD, FAAOS",
                "contact": "+1-555-0103",
                "email": "emily.rodriguez@hospital.com",
                "department": "Orthopedics",
                "experience_years": 12
            },
            {
                "name": "Dr. James Wilson",
                "specialization": "General Medicine",
                "qualification": "MD",
                "contact": "+1-555-0104",
                "email": "james.wilson@hospital.com",
                "department": "Internal Medicine",
                "experience_years": 8
            },
            {
                "name": "Dr. Lisa Anderson",
                "specialization": "Dermatology",
                "qualification": "MD, FAAD",
                "contact": "+1-555-0105",
                "email": "lisa.anderson@hospital.com",
                "department": "Dermatology",
                "experience_years": 11
            }
        ]
        
        result = await db.doctors.insert_many(sample_doctors)
        print(f"✓ Inserted {len(result.inserted_ids)} sample doctors")
        
        # Insert sample patient
        sample_patient = {
            "name": "John Doe",
            "age": 35,
            "gender": "Male",
            "contact": "+1-555-1001",
            "email": "john.doe@email.com",
            "address": "123 Main St, City, State 12345",
            "blood_group": "O+",
            "emergency_contact": "+1-555-1002",
            "allergies": "Penicillin"
        }
        
        result = await db.patients.insert_one(sample_patient)
        print(f"✓ Inserted sample patient (ID: {result.inserted_id})")
        
        print("\n=== Database Initialization Complete! ===")
        print(f"\nDatabase: {DB_NAME}")
        print(f"Collections created: {len(collections)}")
        print("\nYou can now run the MCP server!")
        
        # List all collections
        print("\n=== Collections in database ===")
        collections_list = await db.list_collection_names()
        for col in collections_list:
            count = await db[col].count_documents({})
            print(f"  • {col}: {count} documents")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise
    finally:
        client.close()
        print("\n✓ Connection closed")

if __name__ == "__main__":
    print("=" * 50)
    print("Hospital Management Database Initialization")
    print("=" * 50)
    asyncio.run(initialize_database())