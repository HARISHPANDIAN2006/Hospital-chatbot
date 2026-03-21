class IntentClassifier:
    def classify(self, query: str) -> str:
        """Classify user query into intents"""
        query_lower = query.lower()
        
        print(f"🔍 CLASSIFYING: '{query_lower}'")
        
        # Patient registration
        if any(keyword in query_lower for keyword in ['register patient', 'new patient', 'add patient']):
            print("✅ MATCHED: REGISTER_PATIENT")
            return "REGISTER_PATIENT"
        
        # Patient profile
        if any(keyword in query_lower for keyword in [
            'patient profile', 'get patient profile', 'view patient', 
            'show patient profile', 'show patient details', 'patient info',
            'show me patient'
        ]):
            print("✅ MATCHED: GET_PATIENT_PROFILE")
            return "GET_PATIENT_PROFILE"
        
        if any(keyword in query_lower for keyword in ['update patient', 'edit patient', 'modify patient']):
            print("✅ MATCHED: UPDATE_PATIENT_PROFILE")
            return "UPDATE_PATIENT_PROFILE"
        
        # Doctor search
        if any(keyword in query_lower for keyword in ['search doctor', 'find doctor', 'cardiologist', 'pediatric', 'specialist', 'doctor']):
            print("✅ MATCHED: SEARCH_DOCTORS")
            return "SEARCH_DOCTORS"
        
        if any(keyword in query_lower for keyword in ['doctor info', 'doctor details', 'about doctor']):
            print("✅ MATCHED: GET_DOCTOR_INFO")
            return "GET_DOCTOR_INFO"
        
        # Appointments
        if any(keyword in query_lower for keyword in ['book appointment', 'schedule appointment', 'make appointment']):
            print("✅ MATCHED: BOOK_APPOINTMENT")
            return "BOOK_APPOINTMENT"
        
        if any(keyword in query_lower for keyword in ['my appointments', 'view appointments', 'show appointments', 'list appointments']):
            print("✅ MATCHED: GET_MY_APPOINTMENTS")
            return "GET_MY_APPOINTMENTS"
        
        if any(keyword in query_lower for keyword in ['reschedule', 'change appointment', 'move appointment']):
            print("✅ MATCHED: RESCHEDULE_APPOINTMENT")
            return "RESCHEDULE_APPOINTMENT"
        
        if any(keyword in query_lower for keyword in ['cancel appointment', 'delete appointment']):
            print("✅ MATCHED: CANCEL_APPOINTMENT")
            return "CANCEL_APPOINTMENT"
        
        # Medical records
        if any(keyword in query_lower for keyword in ['medical history', 'past visits', 'health records']):
            print("✅ MATCHED: GET_MEDICAL_HISTORY")
            return "GET_MEDICAL_HISTORY"
        
        if any(keyword in query_lower for keyword in ['prescriptions', 'medications', 'medicines']):
            print("✅ MATCHED: GET_PRESCRIPTIONS")
            return "GET_PRESCRIPTIONS"
        
        if any(keyword in query_lower for keyword in ['lab reports', 'test results', 'lab results']):
            print("✅ MATCHED: GET_LAB_REPORTS")
            return "GET_LAB_REPORTS"
        
        if any(keyword in query_lower for keyword in ['appointment reminders', 'upcoming appointments', 'next appointments']):
            print("✅ MATCHED: GET_APPOINTMENT_REMINDERS")
            return "GET_APPOINTMENT_REMINDERS"
        
        if any(keyword in query_lower for keyword in ['health summary', 'health overview', 'medical summary']):
            print("✅ MATCHED: GET_HEALTH_SUMMARY")
            return "GET_HEALTH_SUMMARY"
        
        # Consultation processing
        if any(keyword in query_lower for keyword in [
            'process consultation', 'analyze consultation', 'generate prescription',
            'consultation audio', 'process appointment audio'
        ]):
            print("✅ MATCHED: PROCESS_CONSULTATION")
            return "PROCESS_CONSULTATION"
        
        print("❌ NO MATCH: UNKNOWN")
        return "UNKNOWN"