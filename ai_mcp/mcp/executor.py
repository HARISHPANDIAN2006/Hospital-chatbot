import json
import os
import re

try:
    from google import genai as google_genai  # New SDK: google-genai
except Exception:
    google_genai = None

try:
    import google.generativeai as google_generativeai  # Legacy SDK: google-generativeai
except Exception:
    google_generativeai = None
from dotenv import load_dotenv

try:
    from mcp.client import MCPClient
except (ModuleNotFoundError, ImportError):
    from client import MCPClient

load_dotenv()


class MCPExecutor:
    def __init__(self):
        self.client = MCPClient()
        self.sdk = None
        try:
            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise RuntimeError("Missing GOOGLE_API_KEY or GEMINI_API_KEY in environment")
            model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
            self.model_name = model_name

            if google_genai is not None:
                self.client_llm = google_genai.Client(api_key=api_key)
                self.sdk = "google-genai"
            elif google_generativeai is not None:
                google_generativeai.configure(api_key=api_key)
                self.client_llm = google_generativeai.GenerativeModel(self.model_name)
                self.sdk = "google-generativeai"
            else:
                raise RuntimeError(
                    "Gemini SDK not installed. Install one of: 'google-genai' or 'google-generativeai'."
                )

            self.llm = True
            print(f"Using Gemini ({model_name}) for NLP extraction via {self.sdk}")
        except Exception as e:
            print(f"Gemini not available: {e}")
            self.llm = None
            self.model_name = ""
            self.client_llm = None

    def _invoke_gemini(self, prompt: str) -> str:
        if not self.llm:
            raise RuntimeError("Gemini not configured")
        try:
            if self.sdk == "google-genai":
                response = self.client_llm.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config={"temperature": 0.1},
                )
                text = (getattr(response, "text", "") or "").strip()
                if text:
                    return text
                if getattr(response, "candidates", None):
                    parts = []
                    for candidate in response.candidates:
                        content = getattr(candidate, "content", None)
                        if not content:
                            continue
                        for part in getattr(content, "parts", []) or []:
                            if getattr(part, "text", ""):
                                parts.append(part.text)
                    return "\n".join(parts).strip()
                return ""

            response = self.client_llm.generate_content(
                prompt,
                generation_config={"temperature": 0.1},
            )
            return (getattr(response, "text", "") or "").strip()
        except Exception as e:
            err = str(e).lower()
            if "429" in err or "quota" in err or "rate limit" in err:
                # Disable Gemini for this process and continue with rule-based parsing.
                self.llm = None
            raise

    def _extract_patient_rule_based(self, query: str) -> dict:
        q = query
        data = {
            "name": None,
            "age": None,
            "gender": None,
            "contact": None,
            "email": None,
            "address": None,
            "blood_group": None,
            "allergies": None,
        }

        name_match = re.search(r"(?:named|name is)\s+([a-zA-Z .'-]{2,60})", q, re.IGNORECASE)
        if name_match:
            data["name"] = name_match.group(1).strip(" ,.")

        age_match = re.search(r"\b(\d{1,3})\s*(?:years?|yrs?)?\s*old\b|\bage\s*(?:is)?\s*(\d{1,3})", q, re.IGNORECASE)
        if age_match:
            data["age"] = int(next(g for g in age_match.groups() if g))

        gender_match = re.search(r"\b(male|female|other)\b", q, re.IGNORECASE)
        if gender_match:
            data["gender"] = gender_match.group(1).capitalize()

        contact_match = re.search(r"(?:contact|phone|mobile)\s*(?:is|:)?\s*(\+?\d[\d -]{7,}\d)", q, re.IGNORECASE)
        if not contact_match:
            contact_match = re.search(r"\b(\+?\d[\d -]{9,}\d)\b", q)
        if contact_match:
            data["contact"] = contact_match.group(1).strip()

        email_match = re.search(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", q)
        if email_match:
            data["email"] = email_match.group(0)

        blood_match = re.search(r"\b(a|b|ab|o)[+-]\b", q, re.IGNORECASE)
        if blood_match:
            data["blood_group"] = blood_match.group(0).upper()

        allergies_match = re.search(r"(?:allerg(?:y|ies)\s*(?:is|are|:)?\s*)([^,.]+)", q, re.IGNORECASE)
        if allergies_match:
            data["allergies"] = allergies_match.group(1).strip()

        address_match = re.search(r"(?:address\s*(?:is|:)?\s*)(.+)", q, re.IGNORECASE)
        if address_match:
            data["address"] = address_match.group(1).strip().rstrip(".")

        return data

    def _extract_appointment_rule_based(self, query: str) -> dict:
        q = query
        data = {
            "patient_id": None,
            "doctor_id": None,
            "doctor_name": None,
            "specialization": None,
            "date": None,
            "time": None,
            "reason": None,
            "symptoms": None,
        }

        pid = re.search(r"(?:patient\s*id|patient)\s*(?:is|:)?\s*([a-fA-F0-9]{24}|\w[\w-]{4,})", q, re.IGNORECASE)
        if pid:
            data["patient_id"] = pid.group(1)

        did = re.search(r"(?:doctor\s*id|dr\s*id)\s*(?:is|:)?\s*([a-fA-F0-9]{24}|\w[\w-]{4,})", q, re.IGNORECASE)
        if did:
            data["doctor_id"] = did.group(1)

        dname = re.search(r"(?:with|doctor|dr\.?)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})", q)
        if dname:
            name = dname.group(1).strip()
            if not name.lower().startswith("id"):
                data["doctor_name"] = f"Dr. {name}" if not name.lower().startswith("dr") else name

        date_match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", q)
        if date_match:
            data["date"] = date_match.group(1)

        time_match = re.search(r"\b([01]\d|2[0-3]):([0-5]\d)\b", q)
        if time_match:
            data["time"] = f"{time_match.group(1)}:{time_match.group(2)}"

        spec_match = re.search(
            r"\b(cardiology|cardiologist|dermatology|dermatologist|neurology|neurologist|pediatrics|pediatrician|orthopedics|orthopedic|gynecology|gynecologist|psychiatry|psychiatrist|general medicine)\b",
            q,
            re.IGNORECASE,
        )
        if spec_match:
            data["specialization"] = spec_match.group(1)

        reason_match = re.search(r"(?:for|reason\s*(?:is|:))\s+([^,.]+)", q, re.IGNORECASE)
        if reason_match:
            data["reason"] = reason_match.group(1).strip()

        symptoms_match = re.search(r"(?:symptoms?\s*(?:are|:))\s+([^,.]+)", q, re.IGNORECASE)
        if symptoms_match:
            data["symptoms"] = symptoms_match.group(1).strip()

        return data

    def generate_human_response(self, result: dict, intent: str) -> str:
        if not self.llm:
            return json.dumps(result, indent=2)

        prompt = f"""You are a friendly hospital chatbot assistant. Convert this technical response into a natural, human-friendly message.

Intent: {intent}
Technical Response: {json.dumps(result)}

Rules:
1. Be warm, professional, and conversational
2. If successful, confirm the action
3. If error, explain the problem clearly and suggest next step
4. Include important IDs, names, dates when present
5. Keep it concise (2-4 sentences)

Human-friendly response:"""

        try:
            text = self._invoke_gemini(prompt)
            return text or json.dumps(result, indent=2)
        except Exception:
            return json.dumps(result, indent=2)

    def _extract_json(self, response: str) -> dict:
        response = response.replace("```json", "").replace("```", "").strip()

        json_match = re.search(r"\{[\s\S]*\}", response)
        if json_match:
            response = json_match.group(0)

        data = json.loads(response)
        for key, value in list(data.items()):
            if value in ("null", "None"):
                data[key] = None
        return data

    def extract_patient_with_gemini(self, query: str) -> dict:
        prompt = f"""Extract patient registration details from this query: \"{query}\"

Return ONLY a valid JSON object with these fields (use null for missing fields):
{{
    "name": "patient full name or null",
    "age": "number or null",
    "gender": "Male/Female/Other or null",
    "contact": "phone number or null",
    "email": "email or null",
    "address": "address or null",
    "blood_group": "blood group or null",
    "allergies": "allergies or null"
}}

Return ONLY the JSON, no other text."""

        response = self._invoke_gemini(prompt)
        data = self._extract_json(response)

        if data.get("age") is not None:
            data["age"] = int(data["age"])
        return data

    def extract_appointment_with_gemini(self, query: str) -> dict:
        prompt = f"""Extract appointment booking details from this query: \"{query}\"

Return ONLY a valid JSON object:
{{
    "patient_id": "patient ID or null",
    "doctor_id": "doctor ID or null",
    "doctor_name": "doctor name or null",
    "specialization": "medical specialization or null",
    "date": "appointment date in YYYY-MM-DD format or null",
    "time": "appointment time in HH:MM format (24-hour) or null",
    "reason": "reason for appointment or null",
    "symptoms": "symptoms or null"
}}

Return ONLY the JSON, no other text."""

        response = self._invoke_gemini(prompt)
        return self._extract_json(response)

    def execute(self, intent: str, query: str):
        if intent == "SEARCH_DOCTORS":
            specialty = query.lower()
            specialty = specialty.replace("search doctors of", "").strip()
            specialty = specialty.replace("search doctors", "").strip()
            specialty = specialty.replace("find doctors", "").strip()

            try:
                result = self.client.call("search_doctors", {"specialization": specialty})
                return {
                    "human_response": self.generate_human_response(result, intent),
                    "raw_data": result,
                }
            except Exception as e:
                error_result = {"error": str(e)}
                return {
                    "human_response": self.generate_human_response(error_result, intent),
                    "raw_data": error_result,
                }

        if intent == "BOOK_APPOINTMENT":
            try:
                if self.llm:
                    print("\nExtracting appointment details...")
                    try:
                        details = self.extract_appointment_with_gemini(query)
                    except Exception:
                        details = self._extract_appointment_rule_based(query)
                else:
                    details = self._extract_appointment_rule_based(query)

                missing_fields = []
                if not details.get("patient_id"):
                    missing_fields.append("patient ID")
                if not details.get("doctor_id") and not details.get("doctor_name") and not details.get("specialization"):
                    missing_fields.append("doctor name or specialization")
                if not details.get("date"):
                    missing_fields.append("appointment date (YYYY-MM-DD)")
                if not details.get("time"):
                    missing_fields.append("appointment time (HH:MM)")
                if not details.get("reason"):
                    missing_fields.append("reason for appointment")

                if missing_fields:
                    missing_info = {
                        "error": f"Missing required information: {', '.join(missing_fields)}",
                        "missing_fields": missing_fields,
                        "example": "Try saying: 'Book appointment for patient ID 67890abc with Dr. Sarah Johnson on 2026-03-20 at 14:00 for chest pain'",
                    }
                    return {
                        "human_response": self.generate_human_response(missing_info, intent),
                        "raw_data": missing_info,
                    }

                if not details.get("doctor_id"):
                    if details.get("doctor_name"):
                        print(f"\nSearching for doctor: {details['doctor_name']}")
                        doctor_result = self.client.call("search_doctors", {"name": details["doctor_name"]})
                        if doctor_result.get("doctors") and len(doctor_result["doctors"]) > 0:
                            details["doctor_id"] = doctor_result["doctors"][0]["_id"]
                            print(f"Found: {doctor_result['doctors'][0]['name']}")
                        else:
                            error_result = {"error": f"No doctor found with name '{details['doctor_name']}'"}
                            return {
                                "human_response": self.generate_human_response(error_result, intent),
                                "raw_data": error_result,
                            }
                    elif details.get("specialization"):
                        print(f"\nSearching for {details['specialization']} doctors...")
                        doctor_result = self.client.call("search_doctors", {"specialization": details["specialization"]})
                        if doctor_result.get("doctors") and len(doctor_result["doctors"]) > 0:
                            details["doctor_id"] = doctor_result["doctors"][0]["_id"]
                            print(f"Found: {doctor_result['doctors'][0]['name']}")
                        else:
                            error_result = {"error": f"No {details['specialization']} doctors found"}
                            return {
                                "human_response": self.generate_human_response(error_result, intent),
                                "raw_data": error_result,
                            }

                appointment_data = {
                    "patient_id": details["patient_id"],
                    "doctor_id": details["doctor_id"],
                    "appointment_date": details["date"],
                    "appointment_time": details["time"],
                    "reason": details["reason"],
                }
                if details.get("symptoms"):
                    appointment_data["symptoms"] = details["symptoms"]

                print("\nBooking appointment...")
                result = self.client.call("book_appointment", appointment_data)
                return {
                    "human_response": self.generate_human_response(result, intent),
                    "raw_data": result,
                }

            except ValueError as e:
                error_result = {"error": f"Invalid input format: {str(e)}"}
                return {
                    "human_response": self.generate_human_response(error_result, intent),
                    "raw_data": error_result,
                }
            except Exception as e:
                error_result = {"error": str(e)}
                return {
                    "human_response": self.generate_human_response(error_result, intent),
                    "raw_data": error_result,
                }

        if intent == "REGISTER_PATIENT":
            try:
                if self.llm:
                    print("\nExtracting patient details...")
                    try:
                        details = self.extract_patient_with_gemini(query)
                    except Exception:
                        details = self._extract_patient_rule_based(query)
                else:
                    details = self._extract_patient_rule_based(query)

                required = ["name", "age", "gender", "contact"]
                missing = [f for f in required if not details.get(f)]

                if missing:
                    missing_info = {
                        "error": f"Missing required information: {', '.join(missing)}",
                        "missing_fields": missing,
                        "example": "Try saying: 'Register patient named Sarah Smith, 28 years old, female, contact 9876543210'",
                    }
                    return {
                        "human_response": self.generate_human_response(missing_info, intent),
                        "raw_data": missing_info,
                    }

                details = {k: v for k, v in details.items() if v is not None}

                print(f"Registering patient: {details.get('name')}...\n")
                result = self.client.call("register_patient", details)
                return {
                    "human_response": self.generate_human_response(result, intent),
                    "raw_data": result,
                }

            except ValueError as e:
                error_result = {
                    "error": f"Invalid input format: {str(e)}. Please make sure age is a number."
                }
                return {
                    "human_response": self.generate_human_response(error_result, intent),
                    "raw_data": error_result,
                }
            except Exception as e:
                error_result = {"error": str(e)}
                return {
                    "human_response": self.generate_human_response(error_result, intent),
                    "raw_data": error_result,
                }

        return {
            "human_response": "I can help with registering patients, searching doctors, and booking appointments.",
            "raw_data": {"error": "Unsupported MCP intent"},
        }
