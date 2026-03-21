class ActionRouter:
    def route(self, intent: str) -> str:
        if intent == "KNOWLEDGE_QUERY":
            return "RUN_RAG"

        # ALL 14 MCP intents
        if intent in {
            "REGISTER_PATIENT",
            "GET_PATIENT_PROFILE",
            "UPDATE_PATIENT_PROFILE",
            "SEARCH_DOCTORS",
            "GET_DOCTOR_INFO",
            "BOOK_APPOINTMENT",
            "GET_MY_APPOINTMENTS",
            "RESCHEDULE_APPOINTMENT",
            "CANCEL_APPOINTMENT",
            "GET_MEDICAL_HISTORY",
            "GET_PRESCRIPTIONS",
            "GET_LAB_REPORTS",
            "GET_APPOINTMENT_REMINDERS",
            "GET_HEALTH_SUMMARY",
            "PROCESS_CONSULTATION"
        }:
            return "RUN_MCP"

        return "UNKNOWN"