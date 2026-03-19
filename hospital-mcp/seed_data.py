"""
Seed Hospital Management Database with Sample Data
Run this to populate MongoDB Atlas with realistic test data
"""
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import sys

load_dotenv() 

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://username:password@cluster.mongodb.net/")
DB_NAME = os.getenv("DB_NAME", "hospital_db")

async def seed_database():
    """Populate database with sample data"""   
    
    print("Connecting to MongoDB Atlas...", file=sys.stderr)
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DB_NAME]
    
    try:
        print("\n" + "=" * 60, file=sys.stderr)
        print("SEEDING HOSPITAL MANAGEMENT DATABASE", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        
        # Clear existing data (optional - comment out if you want to keep existing data)
        print("\n🗑️  Clearing existing data...", file=sys.stderr)
        await db.patients.delete_many({})
        await db.doctors.delete_many({})
        await db.appointments.delete_many({})
        await db.medical_records.delete_many({})
        await db.prescriptions.delete_many({})
        await db.lab_reports.delete_many({})
        print("✓ Existing data cleared", file=sys.stderr)
        
        # ============================================
        # 1. DOCTORS DATA
        # ============================================
        print("\n👨‍⚕️ Inserting Doctors...", file=sys.stderr)
        
        doctors_data = [
            {
                "name": "Dr. Sarah Johnson",
                "specialization": "Cardiology",
                "qualification": "MD, FACC, Board Certified Cardiologist",
                "contact": "+1-555-0101",
                "email": "sarah.johnson@hospital.com",
                "department": "Cardiology",
                "experience_years": 15,
                "consultation_fee": 150,
                "available_days": ["Monday", "Wednesday", "Friday"],
                "available_hours": "9:00 AM - 5:00 PM",
                "created_at": datetime.utcnow()
            },
            {
                "name": "Dr. Michael Chen",
                "specialization": "Pediatrics",
                "qualification": "MD, FAAP, Pediatric Specialist",
                "contact": "+1-555-0102",
                "email": "michael.chen@hospital.com",
                "department": "Pediatrics",
                "experience_years": 10,
                "consultation_fee": 120,
                "available_days": ["Tuesday", "Thursday", "Saturday"],
                "available_hours": "10:00 AM - 6:00 PM",
                "created_at": datetime.utcnow()
            },
            {
                "name": "Dr. Emily Rodriguez",
                "specialization": "Orthopedics",
                "qualification": "MD, FAAOS, Orthopedic Surgeon",
                "contact": "+1-555-0103",
                "email": "emily.rodriguez@hospital.com",
                "department": "Orthopedics",
                "experience_years": 12,
                "consultation_fee": 180,
                "available_days": ["Monday", "Tuesday", "Thursday"],
                "available_hours": "8:00 AM - 4:00 PM",
                "created_at": datetime.utcnow()
            },
            {
                "name": "Dr. James Wilson",
                "specialization": "General Medicine",
                "qualification": "MD, Internal Medicine",
                "contact": "+1-555-0104",
                "email": "james.wilson@hospital.com",
                "department": "Internal Medicine",
                "experience_years": 8,
                "consultation_fee": 100,
                "available_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                "available_hours": "9:00 AM - 5:00 PM",
                "created_at": datetime.utcnow()
            },
            {
                "name": "Dr. Lisa Anderson",
                "specialization": "Dermatology",
                "qualification": "MD, FAAD, Board Certified Dermatologist",
                "contact": "+1-555-0105",
                "email": "lisa.anderson@hospital.com",
                "department": "Dermatology",
                "experience_years": 11,
                "consultation_fee": 130,
                "available_days": ["Wednesday", "Thursday", "Friday"],
                "available_hours": "10:00 AM - 6:00 PM",
                "created_at": datetime.utcnow()
            },
            {
                "name": "Dr. Robert Martinez",
                "specialization": "Neurology",
                "qualification": "MD, PhD, FAAN, Neurologist",
                "contact": "+1-555-0106",
                "email": "robert.martinez@hospital.com",
                "department": "Neurology",
                "experience_years": 18,
                "consultation_fee": 200,
                "available_days": ["Monday", "Wednesday", "Friday"],
                "available_hours": "9:00 AM - 3:00 PM",
                "created_at": datetime.utcnow()
            },
            {
                "name": "Dr. Priya Sharma",
                "specialization": "Gynecology",
                "qualification": "MD, FACOG, OB-GYN Specialist",
                "contact": "+1-555-0107",
                "email": "priya.sharma@hospital.com",
                "department": "Obstetrics & Gynecology",
                "experience_years": 14,
                "consultation_fee": 140,
                "available_days": ["Tuesday", "Thursday", "Saturday"],
                "available_hours": "9:00 AM - 5:00 PM",
                "created_at": datetime.utcnow()
            },
            {
                "name": "Dr. David Kim",
                "specialization": "Psychiatry",
                "qualification": "MD, Psychiatrist",
                "contact": "+1-555-0108",
                "email": "david.kim@hospital.com",
                "department": "Mental Health",
                "experience_years": 9,
                "consultation_fee": 160,
                "available_days": ["Monday", "Tuesday", "Wednesday", "Thursday"],
                "available_hours": "11:00 AM - 7:00 PM",
                "created_at": datetime.utcnow()
            }
        ]
        
        result = await db.doctors.insert_many(doctors_data)
        doctor_ids = result.inserted_ids
        print(f"✓ Inserted {len(doctor_ids)} doctors", file=sys.stderr)
        
        # ============================================
        # 2. PATIENTS DATA
        # ============================================
        print("\n👤 Inserting Patients...", file=sys.stderr)
        
        patients_data = [
            {
                "name": "John Smith",
                "age": 45,
                "gender": "Male",
                "contact": "+1-555-1001",
                "email": "john.smith@email.com",
                "address": "123 Oak Street, Springfield, IL 62701",
                "blood_group": "O+",
                "emergency_contact": "+1-555-1002",
                "allergies": "Penicillin, Peanuts",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "name": "Emily Davis",
                "age": 32,
                "gender": "Female",
                "contact": "+1-555-1003",
                "email": "emily.davis@email.com",
                "address": "456 Maple Avenue, Chicago, IL 60601",
                "blood_group": "A+",
                "emergency_contact": "+1-555-1004",
                "allergies": "None",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "name": "Michael Brown",
                "age": 28,
                "gender": "Male",
                "contact": "+1-555-1005",
                "email": "michael.brown@email.com",
                "address": "789 Pine Road, Boston, MA 02101",
                "blood_group": "B+",
                "emergency_contact": "+1-555-1006",
                "allergies": "Latex",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "name": "Sarah Johnson",
                "age": 55,
                "gender": "Female",
                "contact": "+1-555-1007",
                "email": "sarah.johnson@email.com",
                "address": "321 Elm Street, New York, NY 10001",
                "blood_group": "AB+",
                "emergency_contact": "+1-555-1008",
                "allergies": "Aspirin, Sulfa drugs",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "name": "David Martinez",
                "age": 38,
                "gender": "Male",
                "contact": "+1-555-1009",
                "email": "david.martinez@email.com",
                "address": "654 Cedar Lane, Los Angeles, CA 90001",
                "blood_group": "O-",
                "emergency_contact": "+1-555-1010",
                "allergies": "None",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "name": "Jennifer Wilson",
                "age": 42,
                "gender": "Female",
                "contact": "+1-555-1011",
                "email": "jennifer.wilson@email.com",
                "address": "987 Birch Court, Miami, FL 33101",
                "blood_group": "A-",
                "emergency_contact": "+1-555-1012",
                "allergies": "Shellfish",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "name": "Robert Taylor",
                "age": 67,
                "gender": "Male",
                "contact": "+1-555-1013",
                "email": "robert.taylor@email.com",
                "address": "159 Willow Street, Seattle, WA 98101",
                "blood_group": "B-",
                "emergency_contact": "+1-555-1014",
                "allergies": "Codeine",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "name": "Lisa Anderson",
                "age": 29,
                "gender": "Female",
                "contact": "+1-555-1015",
                "email": "lisa.anderson@email.com",
                "address": "753 Spruce Avenue, Austin, TX 78701",
                "blood_group": "AB-",
                "emergency_contact": "+1-555-1016",
                "allergies": "None",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        
        result = await db.patients.insert_many(patients_data)
        patient_ids = result.inserted_ids
        print(f"✓ Inserted {len(patient_ids)} patients", file=sys.stderr)
        
        # ============================================
        # 3. APPOINTMENTS DATA
        # ============================================
        print("\n📅 Inserting Appointments...", file=sys.stderr)
        
        appointments_data = [
            # Past appointments (completed)
            {
                "patient_id": str(patient_ids[0]),
                "patient_name": "John Smith",
                "doctor_id": str(doctor_ids[0]),
                "doctor_name": "Dr. Sarah Johnson",
                "appointment_datetime": datetime.utcnow() - timedelta(days=7),
                "reason": "Chest pain and irregular heartbeat",
                "symptoms": "Shortness of breath, chest discomfort",
                "status": "completed",
                "created_at": datetime.utcnow() - timedelta(days=10)
            },
            {
                "patient_id": str(patient_ids[1]),
                "patient_name": "Emily Davis",
                "doctor_id": str(doctor_ids[1]),
                "doctor_name": "Dr. Michael Chen",
                "appointment_datetime": datetime.utcnow() - timedelta(days=3),
                "reason": "Child's fever and cough",
                "symptoms": "High temperature, persistent cough",
                "status": "completed",
                "created_at": datetime.utcnow() - timedelta(days=5)
            },
            # Upcoming appointments (scheduled)
            {
                "patient_id": str(patient_ids[2]),
                "patient_name": "Michael Brown",
                "doctor_id": str(doctor_ids[2]),
                "doctor_name": "Dr. Emily Rodriguez",
                "appointment_datetime": datetime.utcnow() + timedelta(days=2, hours=10),
                "reason": "Knee pain after sports injury",
                "symptoms": "Swelling, difficulty walking",
                "status": "scheduled",
                "created_at": datetime.utcnow()
            },
            {
                "patient_id": str(patient_ids[3]),
                "patient_name": "Sarah Johnson",
                "doctor_id": str(doctor_ids[3]),
                "doctor_name": "Dr. James Wilson",
                "appointment_datetime": datetime.utcnow() + timedelta(days=5, hours=14),
                "reason": "Annual health checkup",
                "symptoms": "None, routine examination",
                "status": "scheduled",
                "created_at": datetime.utcnow()
            },
            {
                "patient_id": str(patient_ids[4]),
                "patient_name": "David Martinez",
                "doctor_id": str(doctor_ids[4]),
                "doctor_name": "Dr. Lisa Anderson",
                "appointment_datetime": datetime.utcnow() + timedelta(days=1, hours=11),
                "reason": "Skin rash and itching",
                "symptoms": "Red patches on arms and legs",
                "status": "confirmed",
                "created_at": datetime.utcnow()
            },
            {
                "patient_id": str(patient_ids[5]),
                "patient_name": "Jennifer Wilson",
                "doctor_id": str(doctor_ids[5]),
                "doctor_name": "Dr. Robert Martinez",
                "appointment_datetime": datetime.utcnow() + timedelta(days=7, hours=9),
                "reason": "Frequent headaches and dizziness",
                "symptoms": "Severe migraines, balance issues",
                "status": "scheduled",
                "created_at": datetime.utcnow()
            }
        ]
        
        result = await db.appointments.insert_many(appointments_data)
        appointment_ids = result.inserted_ids
        print(f"✓ Inserted {len(appointment_ids)} appointments", file=sys.stderr)
        
        # ============================================
        # 4. MEDICAL RECORDS DATA
        # ============================================
        print("\n📋 Inserting Medical Records...", file=sys.stderr)
        
        medical_records_data = [
            {
                "patient_id": str(patient_ids[0]),
                "patient_name": "John Smith",
                "doctor_id": str(doctor_ids[0]),
                "doctor_name": "Dr. Sarah Johnson",
                "visit_date": datetime.utcnow() - timedelta(days=7),
                "diagnosis": "Atrial Fibrillation (AFib)",
                "symptoms": ["Chest pain", "Irregular heartbeat", "Shortness of breath"],
                "treatment": "Prescribed blood thinners and beta-blockers",
                "vital_signs": {
                    "blood_pressure": "145/92 mmHg",
                    "heart_rate": "105 bpm",
                    "temperature": "98.6°F",
                    "oxygen_saturation": "96%"
                },
                "notes": "Patient advised to reduce stress and follow up in 2 weeks. ECG shows irregular rhythm.",
                "created_at": datetime.utcnow() - timedelta(days=7)
            },
            {
                "patient_id": str(patient_ids[1]),
                "patient_name": "Emily Davis",
                "doctor_id": str(doctor_ids[1]),
                "doctor_name": "Dr. Michael Chen",
                "visit_date": datetime.utcnow() - timedelta(days=3),
                "diagnosis": "Acute Bronchitis",
                "symptoms": ["Fever", "Persistent cough", "Fatigue"],
                "treatment": "Antibiotics and cough suppressant prescribed",
                "vital_signs": {
                    "blood_pressure": "118/76 mmHg",
                    "heart_rate": "88 bpm",
                    "temperature": "100.2°F",
                    "oxygen_saturation": "98%"
                },
                "notes": "Rest recommended. Follow up if symptoms persist beyond 1 week.",
                "created_at": datetime.utcnow() - timedelta(days=3)
            },
            {
                "patient_id": str(patient_ids[0]),
                "patient_name": "John Smith",
                "doctor_id": str(doctor_ids[3]),
                "doctor_name": "Dr. James Wilson",
                "visit_date": datetime.utcnow() - timedelta(days=30),
                "diagnosis": "Hypertension",
                "symptoms": ["High blood pressure", "Occasional headaches"],
                "treatment": "Lifestyle modifications and ACE inhibitors",
                "vital_signs": {
                    "blood_pressure": "150/95 mmHg",
                    "heart_rate": "78 bpm",
                    "temperature": "98.4°F",
                    "oxygen_saturation": "97%"
                },
                "notes": "Patient advised on diet and exercise. Monthly monitoring required.",
                "created_at": datetime.utcnow() - timedelta(days=30)
            }
        ]
        
        result = await db.medical_records.insert_many(medical_records_data)
        print(f"✓ Inserted {len(result.inserted_ids)} medical records", file=sys.stderr)
        
        # ============================================
        # 5. PRESCRIPTIONS DATA
        # ============================================
        print("\n💊 Inserting Prescriptions...", file=sys.stderr)
        
        prescriptions_data = [
            {
                "patient_id": str(patient_ids[0]),
                "patient_name": "John Smith",
                "doctor_id": str(doctor_ids[0]),
                "doctor_name": "Dr. Sarah Johnson",
                "prescribed_date": datetime.utcnow() - timedelta(days=7),
                "medications": [
                    {
                        "name": "Warfarin",
                        "dosage": "5mg",
                        "frequency": "Once daily",
                        "duration": "3 months",
                        "instructions": "Take with food"
                    },
                    {
                        "name": "Metoprolol",
                        "dosage": "50mg",
                        "frequency": "Twice daily",
                        "duration": "3 months",
                        "instructions": "Take morning and evening"
                    }
                ],
                "status": "active",
                "notes": "Monitor INR levels weekly",
                "created_at": datetime.utcnow() - timedelta(days=7)
            },
            {
                "patient_id": str(patient_ids[1]),
                "patient_name": "Emily Davis",
                "doctor_id": str(doctor_ids[1]),
                "doctor_name": "Dr. Michael Chen",
                "prescribed_date": datetime.utcnow() - timedelta(days=3),
                "medications": [
                    {
                        "name": "Amoxicillin",
                        "dosage": "500mg",
                        "frequency": "Three times daily",
                        "duration": "7 days",
                        "instructions": "Complete full course"
                    },
                    {
                        "name": "Dextromethorphan",
                        "dosage": "10ml",
                        "frequency": "Every 6 hours",
                        "duration": "5 days",
                        "instructions": "Take as needed for cough"
                    }
                ],
                "status": "active",
                "notes": "Complete antibiotic course even if feeling better",
                "created_at": datetime.utcnow() - timedelta(days=3)
            },
            {
                "patient_id": str(patient_ids[0]),
                "patient_name": "John Smith",
                "doctor_id": str(doctor_ids[3]),
                "doctor_name": "Dr. James Wilson",
                "prescribed_date": datetime.utcnow() - timedelta(days=30),
                "medications": [
                    {
                        "name": "Lisinopril",
                        "dosage": "10mg",
                        "frequency": "Once daily",
                        "duration": "6 months",
                        "instructions": "Take in the morning"
                    }
                ],
                "status": "active",
                "notes": "Monitor blood pressure at home",
                "created_at": datetime.utcnow() - timedelta(days=30)
            }
        ]
        
        result = await db.prescriptions.insert_many(prescriptions_data)
        print(f"✓ Inserted {len(result.inserted_ids)} prescriptions", file=sys.stderr)
        
        # ============================================
        # 6. LAB REPORTS DATA
        # ============================================
        print("\n🔬 Inserting Lab Reports...", file=sys.stderr)
        
        lab_reports_data = [
            {
                "patient_id": str(patient_ids[0]),
                "patient_name": "John Smith",
                "doctor_id": str(doctor_ids[0]),
                "test_name": "Electrocardiogram (ECG)",
                "test_date": datetime.utcnow() - timedelta(days=7),
                "test_type": "Cardiac",
                "results": {
                    "finding": "Atrial Fibrillation detected",
                    "heart_rate": "105 bpm (irregular)",
                    "interpretation": "Abnormal rhythm pattern consistent with AFib"
                },
                "status": "completed",
                "notes": "Urgent cardiology follow-up recommended",
                "created_at": datetime.utcnow() - timedelta(days=7)
            },
            {
                "patient_id": str(patient_ids[0]),
                "patient_name": "John Smith",
                "doctor_id": str(doctor_ids[3]),
                "test_name": "Lipid Panel",
                "test_date": datetime.utcnow() - timedelta(days=30),
                "test_type": "Blood Chemistry",
                "results": {
                    "total_cholesterol": "245 mg/dL (High)",
                    "ldl": "160 mg/dL (High)",
                    "hdl": "45 mg/dL (Low)",
                    "triglycerides": "200 mg/dL (High)"
                },
                "status": "completed",
                "notes": "Lifestyle modifications and possible statin therapy recommended",
                "created_at": datetime.utcnow() - timedelta(days=30)
            },
            {
                "patient_id": str(patient_ids[1]),
                "patient_name": "Emily Davis",
                "doctor_id": str(doctor_ids[1]),
                "test_name": "Chest X-Ray",
                "test_date": datetime.utcnow() - timedelta(days=3),
                "test_type": "Radiology",
                "results": {
                    "finding": "Mild bronchial thickening",
                    "interpretation": "Consistent with acute bronchitis, no pneumonia"
                },
                "status": "completed",
                "notes": "Antibiotic therapy appropriate",
                "created_at": datetime.utcnow() - timedelta(days=3)
            },
            {
                "patient_id": str(patient_ids[3]),
                "patient_name": "Sarah Johnson",
                "doctor_id": str(doctor_ids[3]),
                "test_name": "Complete Blood Count (CBC)",
                "test_date": datetime.utcnow() - timedelta(days=60),
                "test_type": "Blood Test",
                "results": {
                    "wbc": "7,500 cells/mcL (Normal)",
                    "rbc": "4.5 million cells/mcL (Normal)",
                    "hemoglobin": "13.5 g/dL (Normal)",
                    "platelets": "250,000/mcL (Normal)"
                },
                "status": "completed",
                "notes": "All values within normal range",
                "created_at": datetime.utcnow() - timedelta(days=60)
            }
        ]
        
        result = await db.lab_reports.insert_many(lab_reports_data)
        print(f"✓ Inserted {len(result.inserted_ids)} lab reports", file=sys.stderr)
        
        # ============================================
        # Summary
        # ============================================
        print("\n" + "=" * 60, file=sys.stderr)
        print("DATABASE SEEDING COMPLETED SUCCESSFULLY!", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        
        print("\n📊 Summary:", file=sys.stderr)
        print(f"  • Doctors: {len(doctor_ids)}", file=sys.stderr)
        print(f"  • Patients: {len(patient_ids)}", file=sys.stderr)
        print(f"  • Appointments: {len(appointment_ids)}", file=sys.stderr)
        print(f"  • Medical Records: {len(medical_records_data)}", file=sys.stderr)
        print(f"  • Prescriptions: {len(prescriptions_data)}", file=sys.stderr)
        print(f"  • Lab Reports: {len(lab_reports_data)}", file=sys.stderr)
        
        print("\n✅ Your database is ready to use!", file=sys.stderr)
        print("\n💡 Try these test queries in Claude:", file=sys.stderr)
        print("  - Search for cardiologists", file=sys.stderr)
        print(f"  - Get patient profile for: {patient_ids[0]}", file=sys.stderr)
        print("  - View upcoming appointments", file=sys.stderr)
        print("  - Get medical history", file=sys.stderr)
        
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        raise
    finally:
        client.close()
        print("\n✓ Connection closed", file=sys.stderr)

if __name__ == "__main__":
    asyncio.run(seed_database())