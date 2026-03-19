class IntentClassifier:
    def classify(self, query: str) -> str:
        q = query.lower()

        # ---------- REGISTER PATIENT ----------
        if any(p in q for p in [
            "register patient", "register a patient", "register new patient",
            "add patient", "new patient", "enroll patient", "sign up patient",
            "create patient", "patient registration", "register a new patient"
        ]):
            return "REGISTER_PATIENT"

        # ---------- BOOK APPOINTMENT ----------
        if any(p in q for p in [
            "book appointment", "schedule appointment", "make appointment",
            "book a appointment", "schedule a visit", "book a visit",
            "book slot", "set appointment", "fix appointment"
        ]):
            return "BOOK_APPOINTMENT"

        # ---------- GET APPOINTMENTS ----------
        if any(p in q for p in [
            "my appointments", "my appointment", "view appointments",
            "show appointments", "list appointments", "check appointments",
            "upcoming appointments", "appointment history"
        ]):
            return "GET_APPOINTMENTS"

        # ---------- SEARCH DOCTORS ----------
        if any(p in q for p in [
            "search doctor", "find doctor", "find all doctor",
            "available doctor", "list doctor", "show doctor",
            "get doctor", "doctors of", "doctor in",
            "cardiologist", "neurologist", "dermatologist",
            "orthopedic", "pediatrician", "gynecologist",
            "psychiatrist", "oncologist", "radiologist",
            "specialist", "physician", "surgeon"
        ]) or (("find" in q or "search" in q or "show" in q or "list" in q or "available" in q) and "doctor" in q):
            return "SEARCH_DOCTORS"

        # ---------- RAG (knowledge questions) ----------
        if any(w in q for w in [
            "what", "when", "where", "how", "why", "who",
            "rights", "facilities", "services",
            "visiting", "policy", "hours", "information", "tell me about"
        ]):
            return "KNOWLEDGE_QUERY"

        return "UNKNOWN"